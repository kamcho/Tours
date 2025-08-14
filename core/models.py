from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone

User = get_user_model()

# Create your models here.

class Contact(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('tour_booking', 'Tour Booking'),
        ('group_travel', 'Group Travel'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ]
    
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.full_name} - {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"


# Payment System Models

class PaymentMethod(models.Model):
    """Available payment methods in the system"""
    PAYMENT_TYPE_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('mobile_money', 'Other Mobile Money'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")
    processing_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    processing_fee_fixed = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('999999.99'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"
    
    def calculate_processing_fee(self, amount):
        """Calculate total processing fee for a given amount"""
        percentage_fee = (amount * self.processing_fee_percentage) / Decimal('100.00')
        return percentage_fee + self.processing_fee_fixed


class PaymentTransaction(models.Model):
    """Main payment transaction model"""
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('partial_refund', 'Partial Refund'),
        ('chargeback', 'Chargeback'),
    ]
    
    # Basic transaction info
    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    reference_number = models.CharField(max_length=100, unique=True, blank=True)
    external_reference = models.CharField(max_length=200, blank=True, help_text="External payment provider reference")
    
    # User and amount info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='KES', help_text="ISO 4217 currency code")
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Payment method and status
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name='transactions')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='payment')
    
    # Related content (polymorphic relationship)
    content_type = models.CharField(max_length=100, blank=True, help_text="Type of content being paid for")
    object_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of the content object")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Additional metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional transaction metadata")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['external_reference']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.email} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"TXN{self.created_at.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        if not self.total_amount:
            self.total_amount = self.amount + self.processing_fee
        super().save(*args, **kwargs)
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'cancelled']


class CardPayment(models.Model):
    """Credit/Debit card payment details"""
    CARD_TYPE_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
        ('other', 'Other'),
    ]
    
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='card_payment')
    
    # Card details (encrypted in production)
    card_last_four = models.CharField(max_length=4)
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES)
    card_brand = models.CharField(max_length=50, blank=True)
    expiry_month = models.PositiveIntegerField()
    expiry_year = models.PositiveIntegerField()
    
    # Payment processor info
    processor = models.CharField(max_length=50, blank=True, help_text="Payment processor (Stripe, PayPal, etc.)")
    processor_transaction_id = models.CharField(max_length=200, blank=True)
    
    # Security
    is_saved = models.BooleanField(default=False, help_text="Whether this card is saved for future use")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Card Payment'
        verbose_name_plural = 'Card Payments'
    
    def __str__(self):
        return f"{self.card_type} ending in {self.card_last_four}"


class MPesaPayment(models.Model):
    """M-Pesa payment details"""
    MPESA_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('reversed', 'Reversed'),
    ]
    
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='mpesa_payment')
    
    # M-Pesa specific fields
    phone_number = models.CharField(max_length=15, help_text="Customer phone number")
    mpesa_request_id = models.CharField(max_length=100, unique=True, help_text="M-Pesa request ID")
    checkout_request_id = models.CharField(max_length=100, blank=True, help_text="M-Pesa checkout request ID")
    merchant_request_id = models.CharField(max_length=100, blank=True, help_text="M-Pesa merchant request ID")
    
    # Status and response
    mpesa_status = models.CharField(max_length=20, choices=MPESA_STATUS_CHOICES, default='initiated')
    result_code = models.CharField(max_length=10, blank=True, help_text="M-Pesa result code")
    result_description = models.TextField(blank=True, help_text="M-Pesa result description")
    
    # Amount details
    mpesa_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Additional M-Pesa data
    mpesa_metadata = models.JSONField(default=dict, blank=True, help_text="Additional M-Pesa response data")
    
    class Meta:
        verbose_name = 'M-Pesa Payment'
        verbose_name_plural = 'M-Pesa Payments'
        indexes = [
            models.Index(fields=['mpesa_request_id']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['mpesa_status']),
        ]
    
    def __str__(self):
        return f"M-Pesa {self.mpesa_request_id} - {self.phone_number} - {self.mpesa_amount}"
    
    @property
    def is_successful(self):
        return self.mpesa_status == 'successful'
    
    @property
    def is_pending(self):
        return self.mpesa_status in ['initiated', 'pending']


class PaymentWebhook(models.Model):
    """Webhook events from payment providers"""
    WEBHOOK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    # Webhook identification
    provider = models.CharField(max_length=50, help_text="Payment provider (Stripe, M-Pesa, etc.)")
    event_type = models.CharField(max_length=100, help_text="Type of webhook event")
    webhook_id = models.CharField(max_length=200, unique=True, help_text="Provider's webhook ID")
    
    # Event data
    payload = models.JSONField(help_text="Raw webhook payload")
    processed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=WEBHOOK_STATUS_CHOICES, default='pending')
    
    # Processing info
    processed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Payment Webhook'
        verbose_name_plural = 'Payment Webhooks'
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['status']),
            models.Index(fields=['received_at']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.webhook_id}"


class Refund(models.Model):
    """Payment refunds"""
    REFUND_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REFUND_REASON_CHOICES = [
        ('duplicate', 'Duplicate charge'),
        ('fraudulent', 'Fraudulent charge'),
        ('requested_by_customer', 'Requested by customer'),
        ('defective_product', 'Defective product'),
        ('not_as_described', 'Not as described'),
        ('other', 'Other'),
    ]
    
    # Refund details
    original_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='refunds')
    refund_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    external_refund_id = models.CharField(max_length=200, blank=True, help_text="External payment provider refund ID")
    
    # Amount and reason
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reason = models.CharField(max_length=30, choices=REFUND_REASON_CHOICES, blank=True)
    description = models.TextField(blank=True)
    
    # Status and processing
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        indexes = [
            models.Index(fields=['refund_id']),
            models.Index(fields=['external_refund_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Refund {self.refund_id} - {self.amount} from {self.original_transaction.transaction_id}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']


class PaymentSettings(models.Model):
    """Global payment system settings"""
    # M-Pesa Configuration
    mpesa_consumer_key = models.CharField(max_length=200, blank=True, help_text="M-Pesa consumer key")
    mpesa_consumer_secret = models.CharField(max_length=200, blank=True, help_text="M-Pesa consumer secret")
    mpesa_passkey = models.CharField(max_length=200, blank=True, help_text="M-Pesa passkey")
    mpesa_environment = models.CharField(
        max_length=20, 
        choices=[('sandbox', 'Sandbox'), ('production', 'Production')],
        default='sandbox'
    )
    mpesa_business_shortcode = models.CharField(max_length=10, blank=True, help_text="M-Pesa business shortcode")
    mpesa_callback_url = models.URLField(blank=True, help_text="M-Pesa callback URL for webhooks")
    
    # Card Payment Configuration
    stripe_publishable_key = models.CharField(max_length=200, blank=True, help_text="Stripe publishable key")
    stripe_secret_key = models.CharField(max_length=200, blank=True, help_text="Stripe secret key")
    stripe_webhook_secret = models.CharField(max_length=200, blank=True, help_text="Stripe webhook secret")
    
    # General Settings
    default_currency = models.CharField(max_length=3, default='KES', help_text="Default currency for payments")
    auto_capture = models.BooleanField(default=True, help_text="Automatically capture payments when authorized")
    require_cvv = models.BooleanField(default=True, help_text="Require CVV for card payments")
    
    # Fee Settings
    default_processing_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('2.5'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    default_processing_fee_fixed = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Setting'
        verbose_name_plural = 'Payment Settings'
    
    def __str__(self):
        return f"Payment Settings - {self.default_currency}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and PaymentSettings.objects.exists():
            return
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create payment settings instance"""
        settings, created = cls.objects.get_or_create()
        return settings

class Subscription(models.Model):
    """Subscription model for premium services"""
    SUBSCRIPTION_TYPES = [
        ('verification', 'Verification'),
        ('ai_chat', 'AI Chat Assistant'),
        ('whatsapp_api', 'WhatsApp API Support'),
        ('feature_ads', 'Feature Advertising'),
        ('premium', 'Premium Package'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Service-specific fields
    is_verified = models.BooleanField(default=False)
    ai_chat_enabled = models.BooleanField(default=False)
    whatsapp_api_enabled = models.BooleanField(default=False)
    feature_ads_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_subscription_type_display()}"
    
    @property
    def is_active(self):
        return self.status == 'active' and timezone.now() < self.end_date
    
    def activate_services(self):
        """Activate services based on subscription type"""
        if self.subscription_type == 'verification':
            self.is_verified = True
        elif self.subscription_type == 'ai_chat':
            self.ai_chat_enabled = True
        elif self.subscription_type == 'whatsapp_api':
            self.whatsapp_api_enabled = True
        elif self.subscription_type == 'feature_ads':
            self.feature_ads_enabled = True
        elif self.subscription_type == 'premium':
            self.is_verified = True
            self.ai_chat_enabled = True
            self.whatsapp_api_enabled = True
            self.feature_ads_enabled = True
        
        self.status = 'active'
        self.save()

class SubscriptionPlan(models.Model):
    """Subscription plans and pricing"""
    PLAN_TYPES = [
        ('verification', 'Verification'),
        ('ai_chat', 'AI Chat Assistant'),
        ('whatsapp_api', 'WhatsApp API Support'),
        ('feature_ads', 'Feature Advertising'),
        ('premium', 'Premium Package'),
    ]
    
    TARGET_TYPES = [
        ('user', 'User'),
        ('place', 'Place'),
        ('agency', 'Agency'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    features = models.JSONField(default=list)  # List of features included
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - {self.get_target_type_display()}"
    
    @property
    def monthly_price(self):
        """Calculate monthly equivalent price"""
        if self.duration_days == 30:
            return self.price
        elif self.duration_days == 90:
            return self.price / 3
        elif self.duration_days == 365:
            return self.price / 12
        return self.price

class VerificationRequest(models.Model):
    """Verification requests for users, places, and agencies"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_info', 'Requires More Information'),
    ]
    
    VERIFICATION_TYPES = [
        ('user', 'User'),
        ('place', 'Place'),
        ('agency', 'Agency'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Verification details
    business_name = models.CharField(max_length=200, blank=True, null=True)
    business_registration = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Documents
    id_document = models.FileField(upload_to='verification/id_docs/', blank=True, null=True)
    business_license = models.FileField(upload_to='verification/business_licenses/', blank=True, null=True)
    address_proof = models.FileField(upload_to='verification/address_proofs/', blank=True, null=True)
    
    # Review details
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_verifications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_verification_type_display()} Verification"
    
    def approve(self, reviewer):
        """Approve verification request"""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        
        # Mark user as verified
        self.user.is_verified = True
        self.user.save()
    
    def reject(self, reviewer, notes):
        """Reject verification request"""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
