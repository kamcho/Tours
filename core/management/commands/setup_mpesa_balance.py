from django.core.management.base import BaseCommand
from core.models import PaymentSettings


class Command(BaseCommand):
    help = 'Set up M-Pesa balance query configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--security-credential',
            type=str,
            help='M-Pesa security credential (Base64 encoded)'
        )
        parser.add_argument(
            '--show-status',
            action='store_true',
            help='Show current M-Pesa balance configuration status'
        )

    def handle(self, *args, **options):
        try:
            settings = PaymentSettings.get_settings()
            
            # Set initiator name to "KG" if not already set
            if not settings.mpesa_initiator_name:
                settings.mpesa_initiator_name = "KG"
                settings.save()
                self.stdout.write(
                    self.style.SUCCESS('✅ Set M-Pesa initiator name to: KG')
                )
            
            # Set security credential if provided
            if options['security_credential']:
                settings.mpesa_security_credential = options['security_credential']
                settings.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Set M-Pesa security credential to: {options["security_credential"][:20]}...')
                )
            
            # Show current status
            if options['show_status'] or not options['security_credential']:
                self.stdout.write(
                    self.style.SUCCESS('\n📊 Current M-Pesa Balance Configuration Status:')
                )
                self.stdout.write(f"📱 Business Shortcode: {settings.mpesa_business_shortcode}")
                self.stdout.write(f"🔑 Consumer Key: {settings.mpesa_consumer_key[:20] if settings.mpesa_consumer_key else 'Not set'}...")
                self.stdout.write(f"👤 Initiator Name: {settings.mpesa_initiator_name}")
                self.stdout.write(f"🔐 Security Credential: {'Set' if settings.mpesa_security_credential else 'Not set'}")
                self.stdout.write(f"🔗 Callback URL: {settings.mpesa_callback_url}")
                
                # Check what's missing
                missing_fields = []
                if not settings.mpesa_initiator_name:
                    missing_fields.append('initiator_name')
                if not settings.mpesa_security_credential:
                    missing_fields.append('security_credential')
                
                if missing_fields:
                    self.stdout.write(
                        self.style.WARNING(f'\n⚠️  Missing required fields: {", ".join(missing_fields)}')
                    )
                    if 'security_credential' in missing_fields:
                        self.stdout.write(
                            self.style.WARNING('   To set the security credential, use:')
                        )
                        self.stdout.write(
                            self.style.WARNING('   python manage.py setup_mpesa_balance --security-credential "YOUR_ENCRYPTED_CREDENTIAL"')
                        )
                        self.stdout.write(
                            self.style.WARNING('   Note: This should be the Base64 encoded credential from M-Pesa')
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('\n✅ All required fields are configured!')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('   M-Pesa balance query should now work.')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('   Check the Admin dropdown in the navbar to see your balance.')
                    )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
