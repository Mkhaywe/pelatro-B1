from django.core.management.base import BaseCommand
from loyalty.models import LoyaltyAccount, LoyaltyTransaction, LoyaltyTier
from django.db.models import Sum
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix loyalty point balances and tier assignments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Fix specific account ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--fix-tiers',
            action='store_true',
            help='Also fix tier assignments',
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        dry_run = options.get('dry_run')
        fix_tiers = options.get('fix_tiers')
        
        if account_id:
            accounts = LoyaltyAccount.objects.filter(id=account_id)
            if not accounts.exists():
                self.stdout.write(
                    self.style.ERROR(f'Account with ID {account_id} not found')
                )
                return
        else:
            accounts = LoyaltyAccount.objects.all()

        self.stdout.write(f'Processing {accounts.count()} loyalty accounts...')
        
        updated_count = 0
        tier_updated_count = 0
        
        with transaction.atomic():
            for account in accounts:
                old_balance = account.points_balance
                old_tier = account.tier
                
                # Recalculate balance from transactions
                new_balance = self.calculate_correct_balance(account)
                
                # Fix tier assignment if requested
                new_tier = None
                if fix_tiers:
                    new_tier = self.calculate_correct_tier(account, new_balance)
                
                # Check if updates needed
                balance_changed = old_balance != new_balance
                tier_changed = fix_tiers and old_tier != new_tier
                
                if balance_changed or tier_changed:
                    self.stdout.write(
                        f'Account {account.id} ({account.customer}):'
                    )
                    
                    if balance_changed:
                        self.stdout.write(
                            f'  Balance: {old_balance} → {new_balance} points'
                        )
                    
                    if tier_changed:
                        old_tier_name = old_tier.name if old_tier else 'None'
                        new_tier_name = new_tier.name if new_tier else 'None'
                        self.stdout.write(
                            f'  Tier: {old_tier_name} → {new_tier_name}'
                        )
                    
                    if not dry_run:
                        if balance_changed:
                            account.points_balance = new_balance
                            updated_count += 1
                        
                        if tier_changed:
                            account.tier = new_tier
                            tier_updated_count += 1
                        
                        account.save()
                
                else:
                    self.stdout.write(
                        f'Account {account.id} ({account.customer}): '
                        f'{old_balance} points (no changes needed)'
                    )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would update {updated_count} balances'
                    + (f' and {tier_updated_count} tiers' if fix_tiers else '')
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} balances'
                    + (f' and {tier_updated_count} tiers' if fix_tiers else '')
                )
            )

    def calculate_correct_balance(self, account):
        """Calculate the correct balance from all transactions"""
        transactions = LoyaltyTransaction.objects.filter(account=account).order_by('created_at')
        
        balance = 0
        for transaction in transactions:
            if transaction.transaction_type in ['earn', 'adjust']:
                balance += transaction.amount
            elif transaction.transaction_type == 'redeem':
                balance -= transaction.amount
        
        # Ensure balance doesn't go negative
        return max(0, balance)
    
    def calculate_correct_tier(self, account, points_balance):
        """Calculate the correct tier based on points balance"""
        tiers = LoyaltyTier.objects.filter(program=account.program).order_by('min_points')
        
        # Find the highest tier the customer qualifies for
        current_tier = None
        for tier in tiers:
            if points_balance >= tier.min_points:
                current_tier = tier
            else:
                break
        
        return current_tier 