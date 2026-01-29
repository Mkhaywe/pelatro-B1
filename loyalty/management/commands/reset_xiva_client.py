"""
Django management command to reset Xiva client singleton
"""
from django.core.management.base import BaseCommand
from loyalty.integration.xiva_client import reset_xiva_client, get_xiva_client
from django.conf import settings


class Command(BaseCommand):
    help = 'Reset Xiva client singleton to reload credentials'

    def handle(self, *args, **options):
        self.stdout.write('Resetting Xiva client singleton...')
        
        # Show current config
        self.stdout.write(f'  XIVA_API_BASE_URL: {settings.XIVA_API_BASE_URL}')
        self.stdout.write(f'  XIVA_API_AUTH_TYPE: {settings.XIVA_API_AUTH_TYPE}')
        self.stdout.write(f'  XIVA_API_USERNAME: {settings.XIVA_API_USERNAME}')
        self.stdout.write(f'  XIVA_API_PASSWORD: {"SET" if settings.XIVA_API_PASSWORD else "NOT SET"}')
        
        # Reset singleton
        reset_xiva_client()
        self.stdout.write(self.style.SUCCESS('  Singleton reset'))
        
        # Create new client
        client = get_xiva_client()
        self.stdout.write(f'  New client created')
        self.stdout.write(f'  Base URL: {client.base_url}')
        self.stdout.write(f'  Auth Type: {client.auth_type}')
        
        if client.auth_type == 'JWT':
            if client.access_token:
                self.stdout.write(self.style.SUCCESS('  Access token: Present'))
            else:
                self.stdout.write(self.style.WARNING('  Access token: Not yet obtained'))
        
        self.stdout.write(self.style.SUCCESS('\nXiva client reset successfully!'))

