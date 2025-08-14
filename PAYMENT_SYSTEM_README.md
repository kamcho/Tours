# Payment System Implementation

## Overview

This document describes the comprehensive payment system implemented in the TravelsKe platform, supporting both card payments (via Stripe) and M-Pesa mobile money payments.

## Features

- **Multiple Payment Methods**: Credit/Debit cards, M-Pesa, Bank Transfer, Cash
- **Flexible Fee Structure**: Configurable percentage and fixed processing fees
- **Transaction Tracking**: Complete audit trail of all payment activities
- **Webhook Support**: Real-time payment status updates
- **Refund Management**: Comprehensive refund processing
- **Admin Interface**: Full administrative control over payment operations

## Models Architecture

### 1. PaymentMethod
Defines available payment methods with configurable fees and limits.

**Key Fields:**
- `name`: Display name for the payment method
- `payment_type`: Type of payment (card, mpesa, bank_transfer, cash)
- `processing_fee_percentage`: Percentage-based processing fee
- `processing_fee_fixed`: Fixed amount processing fee
- `min_amount`/`max_amount`: Payment amount limits
- `is_active`: Whether the payment method is available

**Usage:**
```python
# Get available payment methods
methods = PaymentMethod.objects.filter(is_active=True)

# Calculate processing fee
fee = method.calculate_processing_fee(amount)
```

### 2. PaymentTransaction
Core transaction model that tracks all payment activities.

**Key Fields:**
- `transaction_id`: Unique transaction identifier
- `user`: User making the payment
- `amount`: Payment amount
- `currency`: Payment currency (default: KES)
- `payment_method`: Selected payment method
- `status`: Transaction status (pending, processing, completed, failed, etc.)
- `content_type`/`object_id`: Polymorphic relationship to paid content

**Usage:**
```python
# Create a new transaction
transaction = PaymentTransaction.objects.create(
    user=user,
    amount=Decimal('1000.00'),
    payment_method=mpesa_method,
    description='Tour booking payment',
    content_type='tour_booking',
    object_id=booking_id
)
```

### 3. CardPayment
Handles credit/debit card payment details.

**Key Fields:**
- `transaction`: Link to PaymentTransaction
- `card_last_four`: Last 4 digits of card
- `card_type`: Card type (visa, mastercard, amex, discover)
- `processor`: Payment processor (Stripe, PayPal, etc.)
- `is_saved`: Whether card is saved for future use

### 4. MPesaPayment
Manages M-Pesa mobile money payments.

**Key Fields:**
- `transaction`: Link to PaymentTransaction
- `phone_number`: Customer's phone number
- `mpesa_request_id`: M-Pesa request identifier
- `mpesa_status`: M-Pesa payment status
- `result_code`/`result_description`: M-Pesa response details

### 5. PaymentWebhook
Tracks webhook events from payment providers.

**Key Fields:**
- `provider`: Payment provider name
- `event_type`: Type of webhook event
- `payload`: Raw webhook data
- `status`: Processing status

### 6. Refund
Manages payment refunds.

**Key Fields:**
- `original_transaction`: Link to original payment
- `amount`: Refund amount
- `reason`: Refund reason
- `status`: Refund processing status

### 7. PaymentSettings
Global configuration for the payment system.

**Key Fields:**
- M-Pesa credentials and environment
- Stripe API keys
- Default fees and currency
- General payment settings

## Admin Interface

The payment system includes comprehensive admin interfaces:

- **PaymentMethodAdmin**: Manage payment methods and fees
- **PaymentTransactionAdmin**: View and manage all transactions
- **CardPaymentAdmin**: Handle card payment details
- **MPesaPaymentAdmin**: Manage M-Pesa payments
- **PaymentWebhookAdmin**: Monitor webhook events
- **RefundAdmin**: Process refunds
- **PaymentSettingsAdmin**: Configure global settings

## Setup Instructions

### 1. Initial Setup
```bash
# Run migrations
python manage.py migrate

# Set up default payment methods
python manage.py setup_payment_system
```

### 2. Configure Payment Providers

#### M-Pesa Configuration
1. Go to Admin → Payment Settings
2. Enter your M-Pesa credentials:
   - Consumer Key
   - Consumer Secret
   - Passkey
   - Business Shortcode
3. Set environment (sandbox/production)

#### Stripe Configuration
1. Go to Admin → Payment Settings
2. Enter your Stripe credentials:
   - Publishable Key
   - Secret Key
   - Webhook Secret

### 3. Webhook Setup

#### M-Pesa Webhook
- Endpoint: `/api/payments/mpesa/webhook/`
- Events: Payment confirmation, reversal

#### Stripe Webhook
- Endpoint: `/api/payments/stripe/webhook/`
- Events: Payment success, failure, refund

## Usage Examples

### Creating a Payment Transaction

```python
from core.models import PaymentMethod, PaymentTransaction
from decimal import Decimal

def create_tour_payment(user, tour, amount):
    # Get M-Pesa payment method
    mpesa_method = PaymentMethod.objects.get(payment_type='mpesa')
    
    # Calculate processing fee
    processing_fee = mpesa_method.calculate_processing_fee(amount)
    
    # Create transaction
    transaction = PaymentTransaction.objects.create(
        user=user,
        amount=amount,
        processing_fee=processing_fee,
        payment_method=mpesa_method,
        description=f'Payment for {tour.name}',
        content_type='tour_booking',
        object_id=tour.id
    )
    
    return transaction
```

### Processing M-Pesa Payment

```python
from core.models import MPesaPayment

def process_mpesa_payment(transaction, phone_number, mpesa_request_id):
    mpesa_payment = MPesaPayment.objects.create(
        transaction=transaction,
        phone_number=phone_number,
        mpesa_request_id=mpesa_request_id,
        mpesa_amount=transaction.amount
    )
    
    # Initiate M-Pesa STK push
    # This would integrate with M-Pesa API
    
    return mpesa_payment
```

### Handling Webhooks

```python
from core.models import PaymentWebhook, PaymentTransaction

def process_payment_webhook(provider, event_type, payload):
    # Create webhook record
    webhook = PaymentWebhook.objects.create(
        provider=provider,
        event_type=event_type,
        payload=payload
    )
    
    try:
        if provider == 'mpesa' and event_type == 'payment_success':
            # Process M-Pesa payment confirmation
            process_mpesa_confirmation(payload)
        elif provider == 'stripe' and event_type == 'payment_intent.succeeded':
            # Process Stripe payment confirmation
            process_stripe_confirmation(payload)
        
        webhook.status = 'processed'
        webhook.processed = True
        webhook.processed_at = timezone.now()
        
    except Exception as e:
        webhook.status = 'failed'
        webhook.error_message = str(e)
    
    webhook.save()
```

## Security Considerations

1. **Card Data**: Never store full card details. Only store last 4 digits and expiry.
2. **API Keys**: Store sensitive credentials in environment variables.
3. **Webhook Verification**: Verify webhook signatures from payment providers.
4. **HTTPS**: Always use HTTPS for payment endpoints.
5. **Input Validation**: Validate all payment data before processing.

## Testing

### Sandbox Environment
1. Use M-Pesa sandbox credentials for testing
2. Use Stripe test keys for card payments
3. Test webhook endpoints with provider test tools

### Test Data
- M-Pesa test phone numbers: 254708374149, 254708374150
- Stripe test cards: 4242424242424242 (Visa), 5555555555554444 (Mastercard)

## Monitoring and Analytics

The admin interface provides:
- Transaction status overview
- Payment method usage statistics
- Failed transaction analysis
- Webhook processing status
- Refund tracking

## Future Enhancements

1. **Multi-currency Support**: Add support for USD, EUR, etc.
2. **Recurring Payments**: Subscription and installment payment support
3. **Advanced Analytics**: Payment trends and business intelligence
4. **Mobile SDK**: Native mobile payment integration
5. **Fraud Detection**: AI-powered fraud prevention
6. **Payment Links**: Shareable payment URLs

## Support

For technical support or questions about the payment system:
1. Check the admin interface for transaction details
2. Review webhook logs for payment provider issues
3. Verify payment method configurations
4. Test with sandbox credentials before going live

## Compliance

- **PCI DSS**: Follow PCI compliance guidelines for card payments
- **GDPR**: Ensure proper data handling for EU customers
- **Local Regulations**: Comply with Kenyan financial regulations
- **Audit Trail**: Maintain complete transaction records for compliance 