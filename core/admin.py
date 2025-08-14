from django.contrib import admin
from .models import Contact, PaymentMethod, PaymentTransaction, CardPayment, MPesaPayment, PaymentWebhook, Refund, PaymentSettings

# Register your models here.

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['subject', 'is_read', 'created_at']
    search_fields = ['full_name', 'email', 'message']
    list_editable = ['is_read']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


# Payment System Admin

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'is_active', 'processing_fee_percentage', 'processing_fee_fixed', 'min_amount', 'max_amount']
    list_filter = ['payment_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'processing_fee_percentage', 'processing_fee_fixed', 'min_amount', 'max_amount']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'payment_type', 'is_active', 'description', 'icon')
        }),
        ('Fee Configuration', {
            'fields': ('processing_fee_percentage', 'processing_fee_fixed')
        }),
        ('Amount Limits', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'amount', 'currency', 'payment_method', 'status', 'transaction_type', 'created_at']
    list_filter = ['status', 'transaction_type', 'payment_method', 'currency', 'created_at']
    search_fields = ['transaction_id', 'reference_number', 'external_reference', 'user__email', 'description']
    readonly_fields = ['transaction_id', 'reference_number', 'total_amount', 'created_at', 'updated_at', 'completed_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'reference_number', 'external_reference', 'status', 'transaction_type')
        }),
        ('User and Amount', {
            'fields': ('user', 'amount', 'currency', 'processing_fee', 'total_amount')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'description')
        }),
        ('Content Reference', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'payment_method')


@admin.register(CardPayment)
class CardPaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'card_last_four', 'card_type', 'card_brand', 'processor', 'is_saved', 'created_at']
    list_filter = ['card_type', 'card_brand', 'processor', 'is_saved', 'created_at']
    search_fields = ['transaction__transaction_id', 'card_last_four', 'processor_transaction_id']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Transaction', {
            'fields': ('transaction',)
        }),
        ('Card Information', {
            'fields': ('card_last_four', 'card_type', 'card_brand', 'expiry_month', 'expiry_year')
        }),
        ('Processor Information', {
            'fields': ('processor', 'processor_transaction_id')
        }),
        ('Security', {
            'fields': ('is_saved',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('transaction')


@admin.register(MPesaPayment)
class MPesaPaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'phone_number', 'mpesa_status', 'mpesa_amount', 'mpesa_request_id', 'initiated_at']
    list_filter = ['mpesa_status', 'initiated_at', 'completed_at']
    search_fields = ['mpesa_request_id', 'checkout_request_id', 'merchant_request_id', 'phone_number', 'transaction__transaction_id']
    readonly_fields = ['mpesa_request_id', 'initiated_at', 'completed_at']
    list_editable = ['mpesa_status']
    
    fieldsets = (
        ('Transaction', {
            'fields': ('transaction',)
        }),
        ('M-Pesa Details', {
            'fields': ('phone_number', 'mpesa_amount', 'mpesa_status')
        }),
        ('M-Pesa References', {
            'fields': ('mpesa_request_id', 'checkout_request_id', 'merchant_request_id')
        }),
        ('Response Information', {
            'fields': ('result_code', 'result_description')
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('mpesa_metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('transaction')


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ['provider', 'event_type', 'webhook_id', 'status', 'processed', 'received_at']
    list_filter = ['provider', 'event_type', 'status', 'processed', 'received_at']
    search_fields = ['webhook_id', 'provider', 'event_type']
    readonly_fields = ['received_at', 'processed_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Webhook Information', {
            'fields': ('provider', 'event_type', 'webhook_id', 'status', 'processed')
        }),
        ('Event Data', {
            'fields': ('payload',)
        }),
        ('Processing Information', {
            'fields': ('processed_at', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('received_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id', 'original_transaction', 'amount', 'status', 'reason', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['refund_id', 'external_refund_id', 'original_transaction__transaction_id']
    readonly_fields = ['refund_id', 'created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Refund Information', {
            'fields': ('refund_id', 'external_refund_id', 'status')
        }),
        ('Transaction Details', {
            'fields': ('original_transaction', 'amount', 'reason', 'description')
        }),
        ('Processing', {
            'fields': ('processed_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('original_transaction')


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ['default_currency', 'mpesa_environment', 'auto_capture', 'require_cvv', 'updated_at']
    list_editable = ['mpesa_environment', 'auto_capture', 'require_cvv']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('M-Pesa Configuration', {
            'fields': (
                'mpesa_consumer_key', 'mpesa_consumer_secret', 'mpesa_passkey', 
                'mpesa_environment', 'mpesa_business_shortcode', 'mpesa_callback_url'
            ),
            'classes': ('collapse',)
        }),
        ('Stripe Configuration', {
            'fields': (
                'stripe_publishable_key', 'stripe_secret_key', 'stripe_webhook_secret'
            ),
            'classes': ('collapse',)
        }),
        ('General Settings', {
            'fields': ('default_currency', 'auto_capture', 'require_cvv')
        }),
        ('Fee Settings', {
            'fields': ('default_processing_fee_percentage', 'default_processing_fee_fixed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not PaymentSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of payment settings
        return False
