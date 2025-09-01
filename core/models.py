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
    mpesa_initiator_name = models.CharField(max_length=100, blank=True, help_text="M-Pesa initiator name for API calls")
    mpesa_security_credential = models.CharField(max_length=500, blank=True, help_text="M-Pesa security credential for API calls")
    
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
        ('ai_insights', 'AI Insights & Analytics'),
        ('date_builder', 'Date Builder Inclusion'),
        ('whatsapp_api', 'WhatsApp API Support'),
        ('feature_ads', 'Feature Advertising'),
        ('premium', 'Premium Package'),
        ('custom', 'Custom Package'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Service-specific fields - using JSON for flexibility
    service_features = models.JSONField(default=dict, help_text="Features and settings for this subscription")
    
    # Legacy boolean fields for backward compatibility
    is_verified = models.BooleanField(default=False)
    ai_chat_enabled = models.BooleanField(default=False)
    whatsapp_api_enabled = models.BooleanField(default=False)
    feature_ads_enabled = models.BooleanField(default=False)
    
    # New fields for enhanced services
    ai_insights_enabled = models.BooleanField(default=False)
    date_builder_enabled = models.BooleanField(default=False)
    
    # Target entity (for place/agency specific subscriptions)
    target_content_type = models.CharField(max_length=100, blank=True, help_text="Type of content (place, agency, user)")
    target_object_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of the target object")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['subscription_type', 'status']),
            models.Index(fields=['target_content_type', 'target_object_id']),
        ]
    
    def __str__(self):
        target_info = ""
        if self.target_content_type and self.target_object_id:
            target_info = f" for {self.target_content_type} #{self.target_object_id}"
        return f"{self.user.username} - {self.get_subscription_type_display()}{target_info}"
    
    @property
    def is_active(self):
        return self.status == 'active' and timezone.now() < self.end_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if self.end_date:
            remaining = self.end_date - timezone.now()
            return max(0, remaining.days)
        return 0
    
    def activate_services(self):
        """Activate services based on subscription type"""
        # Reset all services first
        self.is_verified = False
        self.ai_chat_enabled = False
        self.whatsapp_api_enabled = False
        self.feature_ads_enabled = False
        self.ai_insights_enabled = False
        self.date_builder_enabled = False
        
        # Activate based on subscription type
        if self.subscription_type == 'verification':
            self.is_verified = True
        elif self.subscription_type == 'ai_chat':
            self.ai_chat_enabled = True
        elif self.subscription_type == 'ai_insights':
            self.ai_insights_enabled = True
        elif self.subscription_type == 'date_builder':
            self.date_builder_enabled = True
        elif self.subscription_type == 'whatsapp_api':
            self.whatsapp_api_enabled = True
        elif self.subscription_type == 'feature_ads':
            self.feature_ads_enabled = True
        elif self.subscription_type == 'premium':
            # Premium includes all services
            self.is_verified = True
            self.ai_chat_enabled = True
            self.ai_insights_enabled = True
            self.date_builder_enabled = True
            self.whatsapp_api_enabled = True
            self.feature_ads_enabled = True
        elif self.subscription_type == 'custom':
            # Custom packages use service_features JSON
            custom_features = self.service_features.get('enabled_features', [])
            if 'verification' in custom_features:
                self.is_verified = True
            if 'ai_chat' in custom_features:
                self.ai_chat_enabled = True
            if 'ai_insights' in custom_features:
                self.ai_insights_enabled = True
            if 'date_builder' in custom_features:
                self.date_builder_enabled = True
            if 'whatsapp_api' in custom_features:
                self.whatsapp_api_enabled = True
            if 'feature_ads' in custom_features:
                self.feature_ads_enabled = True
        
        self.status = 'active'
        self.save()
    
    def get_service_status(self, service_name):
        """Get status of a specific service"""
        service_map = {
            'verification': self.is_verified,
            'ai_chat': self.ai_chat_enabled,
            'ai_insights': self.ai_insights_enabled,
            'date_builder': self.date_builder_enabled,
            'whatsapp_api': self.whatsapp_api_enabled,
            'feature_ads': self.feature_ads_enabled,
        }
        return service_map.get(service_name, False)
    
    def has_access_to_service(self, service_name):
        """Check if user has access to a specific service"""
        if not self.is_active:
            return False
        return self.get_service_status(service_name)

class SubscriptionPlan(models.Model):
    """Simplified subscription plan: name, duration, price"""
    DURATION_CHOICES = [
        (30, '1 Month'),
        (90, '3 Months'),
        (180, '6 Months'),
        (365, '1 Year'),
        (730, '2 Years'),
    ]

    name = models.CharField(max_length=100, unique=True)
    duration_days = models.IntegerField(choices=DURATION_CHOICES, default=365)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"

    @property
    def monthly_price(self):
        if self.duration_days == 0:
            return self.price
        if self.duration_days == 365:
            return self.price / 12
        if self.duration_days == 180:
            return self.price / 6
        if self.duration_days == 90:
            return self.price / 3
        if self.duration_days == 30:
            return self.price
        return self.price

    @property
    def yearly_price(self):
        if self.duration_days == 365:
            return self.price
        if self.duration_days == 30:
            return self.price * 12
        if self.duration_days == 90:
            return self.price * 4
        if self.duration_days == 180:
            return self.price * 2
        if self.duration_days == 730:
            return self.price / 2
        return self.price

class VerificationRequest(models.Model):
    """Verification requests for users, places, and agencies"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('payment_completed', 'Payment Completed'),
        ('under_review', 'Under Review'),
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
    
    # Link to specific place or agency being verified
    place = models.ForeignKey('listings.Place', on_delete=models.CASCADE, null=True, blank=True, related_name='verification_requests')
    agency = models.ForeignKey('listings.Agency', on_delete=models.CASCADE, null=True, blank=True, related_name='verification_requests')
    
    # Verification duration in years
    duration_years = models.PositiveIntegerField(default=1, help_text="Number of years for verification")
    
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
        if self.place:
            return f"{self.user.username} - {self.place.name} Verification"
        elif self.agency:
            return f"{self.user.username} - {self.agency.name} Verification"
        else:
            return f"{self.user.username} - {self.get_verification_type_display()} Verification"
    
    def get_verification_target(self):
        """Get the place or agency being verified"""
        if self.place:
            return self.place
        elif self.agency:
            return self.agency
        return None
    
    def get_verification_target_name(self):
        """Get the name of the place or agency being verified"""
        target = self.get_verification_target()
        if target:
            return target.name
        return "N/A"
    
    def calculate_amount(self):
        """Calculate verification fee based on years"""
        return self.duration_years * 1000  # KES 1000 per year
    
    def approve(self, reviewer):
        """Approve verification request"""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        
        # Mark the specific place or agency as verified
        if self.place:
            self.place.verified = True
            self.place.save()
        elif self.agency:
            self.agency.verified = True
            self.agency.save()
        else:
            # Mark user as verified for individual verification
            self.user.is_verified = True
            self.user.save()
        
    def reject(self, reviewer, notes):
        """Reject verification request"""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

class Payment(models.Model):
    """Track payments for verification requests"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
    ]
    
    verification_request = models.OneToOneField(VerificationRequest, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='mpesa')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    mpesa_merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    mpesa_result_code = models.CharField(max_length=10, blank=True, null=True)
    mpesa_result_desc = models.TextField(blank=True, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"Payment {self.id} - {self.verification_request.user.email} - KES {self.amount}"
    
    def mark_completed(self):
        """Mark payment as completed and update verification status"""
        self.payment_status = 'completed'
        self.completed_date = timezone.now()
        self.save()
        
        # Update verification request status
        self.verification_request.status = 'payment_completed'
        self.verification_request.save()
    
    def mark_failed(self, error_message=""):
        """Mark payment as failed"""
        self.payment_status = 'failed'
        self.mpesa_result_desc = error_message
        self.save()


# AI Insights and Analytics Models

class OpenAIAPIKey(models.Model):
    """Store OpenAI API key for the chat feature"""
    api_key = models.CharField(max_length=200, help_text="OpenAI API key")
    data = models.CharField(max_length=100, null=True, blank=True)
    class Meta:
        verbose_name = 'OpenAI API Key'
        verbose_name_plural = 'OpenAI API Keys'
    
    def __str__(self):
        return f"OpenAI API Key (***{self.api_key[-4:] if len(self.api_key) > 4 else '****'})"
    
    @classmethod
    def get_api_key(cls):
        """Get the API key from database"""
        instance = cls.objects.first()
        return instance.api_key if instance else None

class AIChatInteraction(models.Model):
    """Track AI chat interactions for analytics and insights"""
    INTERACTION_TYPE_CHOICES = [
        ('question', 'Question Asked'),
        ('response', 'AI Response'),
        ('feedback', 'User Feedback'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_chat_interactions')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='ai_chat_interactions', null=True, blank=True)
    
    # Content being discussed
    content_type = models.CharField(max_length=100, blank=True, help_text="Type of content (place, agency, user)")
    content_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of the content object")
    
    # Interaction details
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPE_CHOICES, default='question')
    question = models.TextField(blank=True, help_text="User's question")
    ai_response = models.TextField(blank=True, help_text="AI's response")
    user_feedback = models.CharField(max_length=20, blank=True, help_text="User feedback (positive, negative, neutral)")
    
    # Metadata
    tokens_used = models.PositiveIntegerField(default=0, help_text="Number of tokens used in this interaction")
    response_time_ms = models.PositiveIntegerField(default=0, help_text="Response time in milliseconds")
    ai_model = models.CharField(max_length=50, blank=True, help_text="AI model used for response")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['interaction_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"AI Chat: {self.user.username} - {self.get_interaction_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class AIInsightsReport(models.Model):
    """AI-generated insights reports for businesses"""
    REPORT_TYPE_CHOICES = [
        ('chat_analytics', 'Chat Analytics'),
        ('customer_questions', 'Customer Questions Analysis'),
        ('trending_topics', 'Trending Topics'),
        ('improvement_suggestions', 'Improvement Suggestions'),
        ('competitor_analysis', 'Competitor Analysis'),
        ('custom', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_insights_reports')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='ai_insights_reports')
    
    # Report details
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Content being analyzed
    content_type = models.CharField(max_length=100, blank=True, help_text="Type of content (place, agency, user)")
    content_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of the content object")
    
    # Report content
    insights_summary = models.TextField(blank=True, help_text="AI-generated insights summary")
    detailed_analysis = models.JSONField(default=dict, help_text="Detailed analysis data")
    recommendations = models.JSONField(default=list, help_text="List of recommendations")
    
    # Report metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    generation_started_at = models.DateTimeField(auto_now_add=True)
    generation_completed_at = models.DateTimeField(blank=True, null=True)
    
    # Usage tracking
    tokens_used = models.PositiveIntegerField(default=0, help_text="Total tokens used for this report")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'report_type']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"AI Insights: {self.title} - {self.user.username} ({self.get_report_type_display()})"
    
    @property
    def generation_time(self):
        """Calculate report generation time"""
        if self.generation_completed_at and self.generation_started_at:
            return self.generation_completed_at - self.generation_started_at
        return None


# Date Builder Models

class DateBuilderPreference(models.Model):
    """User preferences for date planning"""
    ACTIVITY_TYPES = [
        ('outdoor', 'Outdoor Activities'),
        ('indoor', 'Indoor Activities'),
        ('adventure', 'Adventure & Sports'),
        ('cultural', 'Cultural & Arts'),
        ('food', 'Food & Dining'),
        ('entertainment', 'Entertainment'),
        ('relaxation', 'Relaxation & Wellness'),
        ('shopping', 'Shopping & Markets'),
        ('nature', 'Nature & Wildlife'),
        ('urban', 'Urban Exploration'),
    ]
    
    FOOD_PREFERENCES = [
        ('local', 'Local Cuisine'),
        ('international', 'International Cuisine'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('seafood', 'Seafood'),
        ('meat', 'Meat & Poultry'),
        ('street_food', 'Street Food'),
        ('fine_dining', 'Fine Dining'),
        ('casual', 'Casual Dining'),
        ('fast_food', 'Fast Food'),
    ]
    
    TRANSPORT_PREFERENCES = [
        ('walking', 'Walking'),
        ('cycling', 'Cycling'),
        ('public_transport', 'Public Transport'),
        ('taxi', 'Taxi/Ride Share'),
        ('car', 'Private Car'),
        ('boat', 'Boat/Ferry'),
        ('train', 'Train'),
        ('bus', 'Bus'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='date_builder_preferences')
    
    # Activity preferences
    preferred_activities = models.JSONField(default=list, help_text="List of preferred activity types")
    activity_intensity = models.CharField(max_length=20, choices=[
        ('low', 'Low - Relaxed'),
        ('medium', 'Medium - Balanced'),
        ('high', 'High - Active'),
    ], default='medium')
    
    # Food preferences
    preferred_food_types = models.JSONField(default=list, help_text="List of preferred food types")
    dietary_restrictions = models.JSONField(default=list, help_text="List of dietary restrictions")
    budget_range = models.CharField(max_length=20, choices=[
        ('budget', 'Budget Friendly'),
        ('moderate', 'Moderate'),
        ('premium', 'Premium'),
        ('luxury', 'Luxury'),
    ], default='moderate')
    
    # Transport preferences
    preferred_transport = models.JSONField(default=list, help_text="List of preferred transport methods")
    max_travel_distance = models.PositiveIntegerField(default=50, help_text="Maximum travel distance in km")
    
    # Time preferences
    preferred_duration = models.CharField(max_length=20, choices=[
        ('half_day', 'Half Day (2-4 hours)'),
        ('full_day', 'Full Day (6-8 hours)'),
        ('weekend', 'Weekend (2-3 days)'),
        ('week', 'Week (5-7 days)'),
    ], default='full_day')
    
    # Group preferences
    group_size = models.CharField(max_length=20, choices=[
        ('couple', 'Couple (2 people)'),
        ('small_group', 'Small Group (3-5 people)'),
        ('medium_group', 'Medium Group (6-10 people)'),
        ('large_group', 'Large Group (10+ people)'),
    ], default='couple')
    
    # Additional preferences
    special_requirements = models.TextField(blank=True, help_text="Any special requirements or preferences")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Date Builder Preference'
        verbose_name_plural = 'Date Builder Preferences'
    
    def __str__(self):
        return f"Date Preferences: {self.user.username} - {self.get_preferred_duration_display()}"


class DateBuilderSuggestion(models.Model):
    """AI-generated date suggestions based on user preferences"""
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='date_builder_suggestions')
    preferences = models.ForeignKey(DateBuilderPreference, on_delete=models.CASCADE, related_name='suggestions')
    
    # Suggestion details
    title = models.CharField(max_length=200)
    description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_duration = models.CharField(max_length=50, blank=True)
    
    # Suggested itinerary
    itinerary = models.JSONField(default=list, help_text="List of suggested activities and locations")
    recommended_places = models.JSONField(default=list, help_text="List of recommended place IDs")
    recommended_agencies = models.JSONField(default=list, help_text="List of recommended agency IDs")
    
    # AI generation details
    ai_model = models.CharField(max_length=50, blank=True, help_text="AI model used for suggestion")
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, help_text="AI confidence score (0-1)")
    tokens_used = models.PositiveIntegerField(default=0, help_text="Tokens used for this suggestion")
    
    # User interaction
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    user_feedback = models.CharField(max_length=20, blank=True, choices=[
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ])
    feedback_notes = models.TextField(blank=True)
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'generated_at']),
        ]
    
    def __str__(self):
        return f"Date Suggestion: {self.title} - {self.user.username} ({self.get_status_display()})"
    
    def accept(self):
        """Mark suggestion as accepted"""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
    
    def complete(self):
        """Mark suggestion as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def get_total_cost(self):
        """Calculate total estimated cost including subscriptions"""
        total_cost = self.estimated_cost or Decimal('0.00')
        
        # Add subscription costs for recommended places/agencies
        for place_id in self.recommended_places:
            try:
                place = Place.objects.get(id=place_id)
                if hasattr(place, 'subscription') and place.subscription:
                    # Add a small fee for premium suggestions
                    total_cost += Decimal('100.00')
            except Place.DoesNotExist:
                pass
        
        for agency_id in self.recommended_agencies:
            try:
                agency = Agency.objects.get(id=agency_id)
                if hasattr(agency, 'subscription') and agency.subscription:
                    # Add a small fee for premium suggestions
                    total_cost += Decimal('150.00')
            except Agency.DoesNotExist:
                pass
        
        return total_cost


# Chat Models for Analytics

class ChatQuestion(models.Model):
    """Model to store user questions in place/agency chats"""
    CHAT_TYPE_CHOICES = [
        ('place', 'Place Chat'),
        ('agency', 'Agency Chat'),
    ]
    
    # Chat identification
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPE_CHOICES)
    place = models.ForeignKey('listings.Place', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_questions')
    agency = models.ForeignKey('listings.Agency', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_questions')
    
    # User information (can be anonymous)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_questions')
    session_id = models.CharField(max_length=100, blank=True, help_text="Session ID for anonymous users")
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP address for analytics")
    user_agent = models.TextField(blank=True, help_text="User agent string for analytics")
    
    # Question content
    question = models.TextField()
    question_tokens = models.PositiveIntegerField(default=0, help_text="Number of tokens in the question")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False, help_text="Whether the user was anonymous")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat_type', 'created_at']),
            models.Index(fields=['place', 'created_at']),
            models.Index(fields=['agency', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_id', 'created_at']),
        ]
        verbose_name = 'Chat Question'
        verbose_name_plural = 'Chat Questions'
    
    def __str__(self):
        if self.place:
            return f"Place Chat: {self.place.name} - {self.question[:50]}..."
        elif self.agency:
            return f"Agency Chat: {self.agency.name} - {self.question[:50]}..."
        else:
            return f"Chat: {self.question[:50]}..."
    
    def save(self, *args, **kwargs):
        # Set anonymous flag if no user
        if not self.user:
            self.is_anonymous = True
        super().save(*args, **kwargs)


class ChatResponse(models.Model):
    """Model to store AI responses to chat questions"""
    # Link to the question
    question = models.OneToOneField(ChatQuestion, on_delete=models.CASCADE, related_name='response')
    
    # Response content
    response = models.TextField()
    response_tokens = models.PositiveIntegerField(default=0, help_text="Number of tokens in the response")
    
    # AI model information
    ai_model = models.CharField(max_length=50, default='gpt-3.5-turbo', help_text="AI model used for response")
    model_version = models.CharField(max_length=20, blank=True, help_text="Specific model version")
    
    # Performance metrics
    response_time_ms = models.PositiveIntegerField(default=0, help_text="Response time in milliseconds")
    total_tokens = models.PositiveIntegerField(default=0, help_text="Total tokens used (question + response)")
    
    # Cost tracking
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0, help_text="Cost in USD for this response")
    
    # Quality metrics
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, help_text="AI confidence score (0-1)")
    user_feedback = models.CharField(max_length=20, blank=True, choices=[
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('not_rated', 'Not Rated'),
    ], default='not_rated')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ai_model', 'created_at']),
            models.Index(fields=['user_feedback', 'created_at']),
            models.Index(fields=['response_time_ms', 'created_at']),
        ]
        verbose_name = 'Chat Response'
        verbose_name_plural = 'Chat Responses'
    
    def __str__(self):
        return f"Response to: {self.question.question[:50]}..."
    
    def get_total_cost_kes(self):
        """Get cost in Kenyan Shillings (approximate conversion)"""
        # Rough conversion rate (you can make this dynamic)
        return self.cost_usd * 150  # 1 USD ≈ 150 KES
    
    def get_chat_type(self):
        """Get the chat type from the linked question"""
        return self.question.chat_type
    
    def get_place_or_agency(self):
        """Get the place or agency from the linked question"""
        if self.question.place:
            return self.question.place
        elif self.question.agency:
            return self.question.agency
        return None




class PageVisit(models.Model):
    path = models.CharField(max_length=255)   # The page URL or route
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)  # Browser/device info
    referrer = models.TextField(blank=True, null=True)  # Source (Google, social, direct)
    timestamp = models.DateTimeField(default=timezone.now)
    session_key = models.CharField(max_length=40, blank=True, null=True)

    # Extra metrics
    load_time = models.FloatField(blank=True, null=True)  # In seconds
    status_code = models.IntegerField(blank=True, null=True)  # e.g., 200, 404, 500

    def __str__(self):
        return f"{self.path} - {self.ip_address} @ {self.timestamp}"
