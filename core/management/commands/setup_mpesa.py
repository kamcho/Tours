from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import PaymentSettings, PaymentMethod
from decimal import Decimal

class Command(BaseCommand):
    help = 'Setup M-Pesa credentials and payment method in the database'
    
    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up M-Pesa configuration...')
        
        try:
            with transaction.atomic():
                # Update or create PaymentSettings
                settings, created = PaymentSettings.objects.get_or_create()
                
                # Update M-Pesa credentials
                settings.mpesa_consumer_key = "aSG8gGG7GWSGapToKz8ySyALUx9zIdbBr1CHldVhyOLjJsCz"
                settings.mpesa_consumer_secret = "o8qwdbzapgcvOd1lsBOkKGCL4JwMQyG9ZmKlKC7uaLIc4FsRJFbzfV10EAoL0P6u"
                settings.mpesa_passkey = "fa0e41448ce844d1a7a37553cee8bf22b61fec894e1ce3e9c0e32b1c6953b6d9"
                settings.mpesa_business_shortcode = "4161900"
                settings.mpesa_environment = "production"
                settings.mpesa_callback_url = "https://mwalimuprivate.pythonanywhere.com/core/mpesa/webhook/"
                
                settings.save()
                
                if created:
                    self.stdout.write(self.style.SUCCESS('✅ Created new PaymentSettings'))
                else:
                    self.stdout.write(self.style.SUCCESS('✅ Updated existing PaymentSettings'))
                
                # Create or update M-Pesa payment method
                mpesa_method, created = PaymentMethod.objects.get_or_create(
                    payment_type='mpesa',
                    defaults={
                        'name': 'M-Pesa Mobile Money',
                        'is_active': True,
                        'description': 'Pay using M-Pesa mobile money service',
                        'icon': '📱',
                        'processing_fee_percentage': Decimal('0.00'),
                        'processing_fee_fixed': Decimal('0.00'),
                        'min_amount': Decimal('1.00'),
                        'max_amount': Decimal('70000.00'),
                    }
                )
                
                if not created:
                    # Update existing method
                    mpesa_method.name = 'M-Pesa Mobile Money'
                    mpesa_method.is_active = True
                    mpesa_method.description = 'Pay using M-Pesa mobile money service'
                    mpesa_method.icon = '📱'
                    mpesa_method.processing_fee_percentage = Decimal('0.00')
                    mpesa_method.processing_fee_fixed = Decimal('0.00')
                    mpesa_method.min_amount = Decimal('1.00')
                    mpesa_method.max_amount = Decimal('70000.00')
                    mpesa_method.save()
                    self.stdout.write(self.style.SUCCESS('✅ Updated existing M-Pesa payment method'))
                else:
                    self.stdout.write(self.style.SUCCESS('✅ Created new M-Pesa payment method'))
                
                # Display current settings
                self.stdout.write('\n📋 Current M-Pesa Configuration:')
                self.stdout.write(f'   Consumer Key: {settings.mpesa_consumer_key[:20]}...')
                self.stdout.write(f'   Business Shortcode: {settings.mpesa_business_shortcode}')
                self.stdout.write(f'   Environment: {settings.mpesa_environment}')
                self.stdout.write(f'   Callback URL: {settings.mpesa_callback_url}')
                
                self.stdout.write('\n💳 M-Pesa Payment Method:')
                self.stdout.write(f'   Name: {mpesa_method.name}')
                self.stdout.write(f'   Active: {mpesa_method.is_active}')
                self.stdout.write(f'   Min Amount: KES {mpesa_method.min_amount}')
                self.stdout.write(f'   Max Amount: KES {mpesa_method.max_amount}')
                self.stdout.write(f'   Processing Fee: {mpesa_method.processing_fee_percentage}% + KES {mpesa_method.processing_fee_fixed}')
                
                self.stdout.write(self.style.SUCCESS('\n🎉 M-Pesa setup completed successfully!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error setting up M-Pesa: {str(e)}'))
            raise 