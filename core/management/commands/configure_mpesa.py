from django.core.management.base import BaseCommand
from core.models import PaymentSettings


class Command(BaseCommand):
    help = 'Configure M-Pesa settings for account balance queries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--initiator-name',
            type=str,
            help='M-Pesa initiator name'
        )
        parser.add_argument(
            '--security-credential',
            type=str,
            help='M-Pesa security credential'
        )
        parser.add_argument(
            '--show-current',
            action='store_true',
            help='Show current M-Pesa configuration'
        )

    def handle(self, *args, **options):
        try:
            settings = PaymentSettings.get_settings()
            
            if options['show_current']:
                self.stdout.write(
                    self.style.SUCCESS('Current M-Pesa Configuration:')
                )
                self.stdout.write(f"Consumer Key: {settings.mpesa_consumer_key[:20] if settings.mpesa_consumer_key else 'Not set'}...")
                self.stdout.write(f"Business Shortcode: {settings.mpesa_business_shortcode or 'Not set'}")
                self.stdout.write(f"Initiator Name: {settings.mpesa_initiator_name or 'Not set'}")
                self.stdout.write(f"Security Credential: {settings.mpesa_security_credential[:20] if settings.mpesa_security_credential else 'Not set'}...")
                self.stdout.write(f"Callback URL: {settings.mpesa_callback_url or 'Not set'}")
                return
            
            # Update initiator name
            if options['initiator_name']:
                settings.mpesa_initiator_name = options['initiator_name']
                self.stdout.write(
                    self.style.SUCCESS(f'Updated initiator name to: {options["initiator_name"]}')
                )
            
            # Update security credential
            if options['security_credential']:
                settings.mpesa_security_credential = options['security_credential']
                self.stdout.write(
                    self.style.SUCCESS(f'Updated security credential to: {options["security_credential"][:20]}...')
                )
            
            # Save changes
            if options['initiator_name'] or options['security_credential']:
                settings.save()
                self.stdout.write(
                    self.style.SUCCESS('M-Pesa configuration updated successfully!')
                )
            
            # Show what's still missing
            missing_fields = []
            if not settings.mpesa_initiator_name:
                missing_fields.append('initiator_name')
            if not settings.mpesa_security_credential:
                missing_fields.append('security_credential')
            
            if missing_fields:
                self.stdout.write(
                    self.style.WARNING(f'Missing required fields: {", ".join(missing_fields)}')
                )
                self.stdout.write(
                    self.style.WARNING('Use --initiator-name and --security-credential to set these values')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('All required M-Pesa fields are configured!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
