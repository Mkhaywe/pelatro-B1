from django.core.management.base import BaseCommand
from loyalty.models import LoyaltyAccount, LoyaltyTransaction
from django.db.models import Sum


class Command(BaseCommand):
    help = 'Recalculate loyalty account balances based on transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Recalculate balance for specific account ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        dry_run = options.get('dry_run')
        
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
        for account in accounts:
            old_balance = account.points_balance
            new_balance = self.calculate_balance_from_transactions(account)
            
            if old_balance != new_balance:
                self.stdout.write(
                    f'Account {account.id} ({account.customer}): '
                    f'{old_balance} → {new_balance} points'
                )
                
                if not dry_run:
                    account.points_balance = new_balance
                    account.save(update_fields=['points_balance'])
                
                updated_count += 1
            else:
                self.stdout.write(
                    f'Account {account.id} ({account.customer}): '
                    f'{old_balance} points (no change needed)'
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would update {updated_count} accounts'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} accounts'
                )
            )

    def calculate_balance_from_transactions(self, account):
        """Calculate the correct balance from all transactions"""
        # Get all transactions for this account
        transactions = LoyaltyTransaction.objects.filter(account=account)
        
        balance = 0
        for transaction in transactions:
            if transaction.transaction_type in ['earn', 'adjust']:
                balance += transaction.amount
            elif transaction.transaction_type == 'redeem':
                balance -= transaction.amount
        
        # Ensure balance doesn't go negative
        return max(0, balance) 