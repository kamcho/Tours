from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import PaymentMethod, PaymentSettings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Set up default payment methods and settings for the payment system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up payment system...')
        
        with transaction.atomic():
            # Create default payment methods
            payment_methods = [
                {
                    'name': 'M-Pesa',
                    'payment_type': 'mpesa',
                    'description': 'Pay using M-Pesa mobile money service',
                    'icon': '📱',
                    'processing_fee_percentage': Decimal('0.00'),
                    'processing_fee_fixed': Decimal('0.00'),
                    'min_amount': Decimal('1.00'),
                    'max_amount': Decimal('70000.00'),
                },
                {
                    'name': 'Visa/Mastercard',
                    'payment_type': 'card',
                    'description': 'Pay using Visa or Mastercard credit/debit cards',
                    'icon': '💳',
                    'processing_fee_percentage': Decimal('2.5'),
                    'processing_fee_fixed': Decimal('0.00'),
                    'min_amount': Decimal('1.00'),
                    'max_amount': Decimal('999999.99'),
                },
                {
                    'name': 'Bank Transfer',
                    'payment_type': 'bank_transfer',
                    'description': 'Pay via bank transfer (manual processing)',
                    'icon': '🏦',
                    'processing_fee_percentage': Decimal('0.00'),
                    'processing_fee_fixed': Decimal('0.00'),
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('999999.99'),
                },
                {
                    'name': 'Cash',
                    'payment_type': 'cash',
                    'description': 'Pay in cash upon arrival or pickup',
                    'icon': '💵',
                    'processing_fee_percentage': Decimal('0.00'),
                    'processing_fee_fixed': Decimal('0.00'),
                    'min_amount': Decimal('1.00'),
                    'max_amount': Decimal('999999.99'),
                },
            ]
            
            for method_data in payment_methods:
                payment_method, created = PaymentMethod.objects.get_or_create(
                    name=method_data['name'],
                    defaults=method_data
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created payment method: {payment_method.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Payment method already exists: {payment_method.name}')
                    )
            
            # Create default payment settings
            settings, created = PaymentSettings.objects.get_or_create(
                defaults={
                    'default_currency': 'KES',
                    'mpesa_environment': 'sandbox',
                    'auto_capture': True,
                    'require_cvv': True,
                    'default_processing_fee_percentage': Decimal('2.5'),
                    'default_processing_fee_fixed': Decimal('0.00'),
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created default payment settings')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Payment settings already exist')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Payment system setup completed successfully!')
        )
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Configure M-Pesa credentials in admin panel')
        self.stdout.write('2. Configure Stripe credentials in admin panel')
        self.stdout.write('3. Set up webhook endpoints for payment providers')
        self.stdout.write('4. Test payment flows in sandbox environment') 