# Lipa Mdogo Mdogo - Tour Payment in Installments

## Overview

The "Lipa Mdogo Mdogo" (Pay Little by Little) feature allows users to pay for tour bookings in multiple installments of any amount they choose. This makes travel more accessible by removing the barrier of paying the full amount upfront.

## Features

- **Flexible Payment Amounts**: Users can pay any amount from KES 100 up to the total tour cost
- **Multiple Payment Methods**: Supports M-Pesa, Credit/Debit Cards, Bank Transfer, and Cash
- **Payment Progress Tracking**: Shows total paid, remaining amount, and payment progress percentage
- **Payment History**: Complete record of all payment transactions
- **Additional Payments**: Users can make additional payments anytime before the tour starts
- **Real-time Status Updates**: Payment status updates in real-time

## How It Works

### 1. Initial Booking
- User selects a tour and number of participants
- User enters the amount they want to pay today (minimum KES 100)
- System calculates remaining amount and shows payment progress
- User completes payment through their chosen payment method

### 2. Additional Payments
- Users can make additional payments anytime before departure
- Each payment is tracked separately with its own reference
- Payment progress is updated in real-time
- Full payment must be completed before the tour starts

### 3. Payment Tracking
- Real-time payment status updates
- Payment progress bar showing completion percentage
- Detailed payment history for each booking
- Automatic booking confirmation when fully paid

## Technical Implementation

### Models

#### TourBookingPayment
```python
class TourBookingPayment(models.Model):
    booking = models.ForeignKey(TourBooking, on_delete=models.CASCADE)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    payment_reference = models.CharField(max_length=100, unique=True)
    external_reference = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
```

#### Enhanced TourBooking
The existing TourBooking model has been enhanced with new properties:
- `total_paid_amount`: Total amount paid through all transactions
- `remaining_amount`: Amount still to be paid
- `payment_progress_percentage`: Payment completion percentage
- `is_fully_paid`: Boolean indicating if full payment is complete

### Views

#### TourBookingWithPaymentView
- Handles initial tour booking with installment payment
- Creates TourBooking and TourBookingPayment records
- Processes M-Pesa and other payment methods
- Validates payment amounts and participant limits

#### AdditionalPaymentView
- Handles additional payments for existing bookings
- Validates payment amounts against remaining balance
- Creates new TourBookingPayment records
- Updates payment progress

#### PaymentStatusView
- Shows payment status for both new and legacy payment models
- Displays payment progress and remaining amounts
- Provides links to make additional payments

### Templates

#### tour_booking_payment.html
- Enhanced booking form with payment amount input
- Real-time calculation of remaining amounts
- Payment progress visualization
- Lipa Mdogo Mdogo feature explanation

#### additional_payment.html
- Additional payment form for existing bookings
- Payment history display
- Payment progress tracking
- Action buttons for different payment statuses

#### payment_status.html
- Unified payment status display
- Support for both new and legacy payment models
- Payment progress visualization
- Action buttons based on payment status

## Payment Flow

### 1. Initial Booking Flow
```
User selects tour → Enters payment amount → Chooses payment method → 
Payment processed → TourBookingPayment created → Redirect to payment status
```

### 2. Additional Payment Flow
```
User views booking → Clicks "Make Additional Payment" → 
Enters payment amount → Payment processed → New TourBookingPayment created
```

### 3. Payment Status Flow
```
Payment initiated → Status: Pending → Payment processing → 
Status: Processing → Payment completed → Status: Completed
```

## Configuration

### M-Pesa Integration
- Business shortcode: Configure in view or environment variables
- Passkey: Configure in view or environment variables
- Consumer key/secret: Configure in view or environment variables

### Payment Limits
- Minimum payment: KES 100
- Maximum payment: Total tour cost
- Payment increments: KES 100

## Admin Interface

### TourBookingPayment Admin
- List view with payment details
- Filter by payment method, status, and date
- Search by reference, user, or tour
- Edit payment status
- View payment metadata

## Security Features

- User authentication required for all payment operations
- Payment amount validation against tour cost
- User ownership verification for all operations
- Secure payment reference generation
- Audit trail for all payment transactions

## Future Enhancements

- Payment reminders for incomplete payments
- Automatic payment scheduling
- Payment plan templates
- Late payment fees
- Payment analytics and reporting
- Integration with more payment providers

## Usage Examples

### Making Initial Payment
```python
# User books tour with KES 1,000 payment
booking = TourBooking.objects.create(
    tour=tour,
    user=user,
    participants=2,
    total_amount=5000  # KES 2,500 per person
)

payment = TourBookingPayment.objects.create(
    booking=booking,
    user=user,
    amount=1000,
    payment_method='mpesa',
    payment_status='pending'
)
```

### Making Additional Payment
```python
# User makes additional KES 2,000 payment
additional_payment = TourBookingPayment.objects.create(
    booking=booking,
    user=user,
    amount=2000,
    payment_method='mpesa',
    payment_status='pending'
)
```

### Checking Payment Progress
```python
# Get payment progress
total_paid = booking.total_paid_amount  # KES 3,000
remaining = booking.remaining_amount    # KES 2,000
progress = booking.payment_progress_percentage  # 60%
is_complete = booking.is_fully_paid    # False
```

## Support

For technical support or questions about the Lipa Mdogo Mdogo feature, please contact the development team or refer to the codebase documentation. 