from django.contrib import admin
from .models import Contact, PaymentMethod, PaymentTransaction, CardPayment, MPesaPayment, PaymentWebhook, Refund, PaymentSettings, Subscription, SubscriptionPlan, VerificationRequest, Payment, AIChatInteraction, AIInsightsReport, DateBuilderPreference, DateBuilderSuggestion
from django.utils import timezone
from .models import ChatQuestion, ChatResponse

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
                'mpesa_environment', 'mpesa_business_shortcode', 'mpesa_callback_url',
                'mpesa_initiator_name', 'mpesa_security_credential'
            ),
            'classes': ('collapse',),
            'description': 'Configure M-Pesa API credentials. For account balance queries, both initiator_name and security_credential are required.'
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

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'verification_request', 'amount', 'payment_method', 'payment_status', 'transaction_date', 'completed_date']
    list_filter = ['payment_status', 'payment_method', 'transaction_date']
    search_fields = ['verification_request__user__email', 'payment_reference', 'mpesa_checkout_request_id']
    readonly_fields = ['transaction_date', 'completed_date']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('verification_request', 'amount', 'payment_method', 'payment_status')
        }),
        ('M-Pesa Details', {
            'fields': ('mpesa_checkout_request_id', 'mpesa_merchant_request_id', 'mpesa_result_code', 'mpesa_result_desc')
        }),
        ('Timestamps', {
            'fields': ('transaction_date', 'completed_date'),
            'classes': ('collapse',)
        }),
    )

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'verification_type', 'status', 'phone_number', 'created_at', 'reviewed_at']
    list_filter = ['status', 'verification_type', 'created_at', 'reviewed_at']
    search_fields = ['user__email', 'user__username', 'business_name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'verification_type', 'status')
        }),
        ('Contact Details', {
            'fields': ('phone_number', 'email')
        }),
        ('Business Information', {
            'fields': ('business_name', 'business_registration', 'address'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('id_document', 'business_license', 'address_proof'),
            'classes': ('collapse',)
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_verification', 'reject_verification', 'mark_under_review']
    
    def approve_verification(self, request, queryset):
        """Approve selected verification requests"""
        updated = queryset.update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} verification request(s) were successfully approved.')
    approve_verification.short_description = "Approve selected verification requests"
    
    def reject_verification(self, request, queryset):
        """Reject selected verification requests"""
        updated = queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} verification request(s) were successfully rejected.')
    reject_verification.short_description = "Reject selected verification requests"
    
    def mark_under_review(self, request, queryset):
        """Mark selected verification requests as under review"""
        updated = queryset.update(
            status='under_review',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} verification request(s) were marked as under review.')
    mark_under_review.short_description = "Mark selected verification requests as under review"


# AI Insights and Analytics Admin

@admin.register(AIChatInteraction)
class AIChatInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'interaction_type', 'content_type', 'content_id', 'tokens_used', 'ai_model', 'created_at']
    list_filter = ['interaction_type', 'content_type', 'ai_model', 'created_at']
    search_fields = ['user__email', 'user__username', 'question', 'ai_response']
    readonly_fields = ['created_at', 'tokens_used', 'response_time_ms']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'subscription')
        }),
        ('Content Reference', {
            'fields': ('content_type', 'content_id')
        }),
        ('Interaction Details', {
            'fields': ('interaction_type', 'question', 'ai_response', 'user_feedback')
        }),
        ('Technical Details', {
            'fields': ('ai_model', 'tokens_used', 'response_time_ms'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'subscription')


@admin.register(AIInsightsReport)
class AIInsightsReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'report_type', 'status', 'tokens_used', 'generation_started_at', 'generation_completed_at']
    list_filter = ['report_type', 'status', 'generation_started_at']
    search_fields = ['title', 'user__email', 'user__username', 'insights_summary']
    readonly_fields = ['generation_started_at', 'generation_completed_at', 'tokens_used', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'report_type', 'status')
        }),
        ('User and Subscription', {
            'fields': ('user', 'subscription')
        }),
        ('Content Reference', {
            'fields': ('content_type', 'content_id'),
            'classes': ('collapse',)
        }),
        ('Report Content', {
            'fields': ('insights_summary', 'detailed_analysis', 'recommendations')
        }),
        ('Generation Details', {
            'fields': ('generation_started_at', 'generation_completed_at', 'tokens_used', 'ai_model'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['regenerate_report', 'mark_completed']
    
    def regenerate_report(self, request, queryset):
        """Mark selected reports for regeneration"""
        updated = queryset.update(
            status='generating',
            generation_started_at=timezone.now(),
            generation_completed_at=None
        )
        self.message_user(request, f'{updated} report(s) were marked for regeneration.')
    regenerate_report.short_description = "Regenerate selected reports"
    
    def mark_completed(self, request, queryset):
        """Mark selected reports as completed"""
        updated = queryset.update(
            status='completed',
            generation_completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} report(s) were marked as completed.')
    mark_completed.short_description = "Mark selected reports as completed"


# Date Builder Admin

@admin.register(DateBuilderPreference)
class DateBuilderPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_duration', 'group_size', 'budget_range', 'activity_intensity', 'created_at']
    list_filter = ['preferred_duration', 'group_size', 'budget_range', 'activity_intensity', 'created_at']
    search_fields = ['user__email', 'user__username', 'special_requirements']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Activity Preferences', {
            'fields': ('preferred_activities', 'activity_intensity')
        }),
        ('Food Preferences', {
            'fields': ('preferred_food_types', 'dietary_restrictions', 'budget_range')
        }),
        ('Transport Preferences', {
            'fields': ('preferred_transport', 'max_travel_distance')
        }),
        ('Time and Group', {
            'fields': ('preferred_duration', 'group_size')
        }),
        ('Additional Requirements', {
            'fields': ('special_requirements',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(DateBuilderSuggestion)
class DateBuilderSuggestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'estimated_cost', 'estimated_duration', 'confidence_score', 'generated_at']
    list_filter = ['status', 'estimated_duration', 'generated_at']
    search_fields = ['title', 'user__email', 'user__username', 'description']
    readonly_fields = ['generated_at', 'accepted_at', 'completed_at', 'tokens_used']
    
    fieldsets = (
        ('Suggestion Information', {
            'fields': ('title', 'description', 'status')
        }),
        ('User and Preferences', {
            'fields': ('user', 'preferences')
        }),
        ('Cost and Duration', {
            'fields': ('estimated_cost', 'estimated_duration')
        }),
        ('Itinerary', {
            'fields': ('itinerary', 'recommended_places', 'recommended_agencies')
        }),
        ('AI Generation', {
            'fields': ('ai_model', 'confidence_score', 'tokens_used'),
            'classes': ('collapse',)
        }),
        ('User Interaction', {
            'fields': ('user_feedback', 'feedback_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('generated_at', 'accepted_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_accepted', 'mark_completed']
    
    def mark_accepted(self, request, queryset):
        """Mark selected suggestions as accepted"""
        updated = queryset.update(
            status='accepted',
            accepted_at=timezone.now()
        )
        self.message_user(request, f'{updated} suggestion(s) were marked as accepted.')
    mark_accepted.short_description = "Mark selected suggestions as accepted"
    
    def mark_completed(self, request, queryset):
        """Mark selected suggestions as completed"""
        updated = queryset.update(
            status='completed',
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} suggestion(s) were marked as completed.')
    mark_completed.short_description = "Mark selected suggestions as completed"


# Chat Models Admin

@admin.register(ChatQuestion)
class ChatQuestionAdmin(admin.ModelAdmin):
    list_display = ['chat_type', 'get_place_or_agency', 'get_user_info', 'question_preview', 'is_anonymous', 'created_at']
    list_filter = ['chat_type', 'is_anonymous', 'created_at']
    search_fields = ['question', 'user__email', 'user__username', 'session_id']
    readonly_fields = ['created_at', 'is_anonymous']
    list_per_page = 50
    
    fieldsets = (
        ('Chat Information', {
            'fields': ('chat_type', 'place', 'agency')
        }),
        ('User Information', {
            'fields': ('user', 'session_id', 'ip_address', 'user_agent', 'is_anonymous')
        }),
        ('Question Content', {
            'fields': ('question', 'question_tokens')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_place_or_agency(self, obj):
        if obj.place:
            return f"Place: {obj.place.name}"
        elif obj.agency:
            return f"Agency: {obj.agency.name}"
        return "Unknown"
    get_place_or_agency.short_description = "Place/Agency"
    
    def get_user_info(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.email})"
        else:
            return f"Anonymous ({obj.session_id[:20]}...)"
    get_user_info.short_description = "User"
    
    def question_preview(self, obj):
        return obj.question[:100] + "..." if len(obj.question) > 100 else obj.question
    question_preview.short_description = "Question"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'place', 'agency')


@admin.register(ChatResponse)
class ChatResponseAdmin(admin.ModelAdmin):
    list_display = ['get_question_preview', 'get_chat_type', 'ai_model', 'response_tokens', 'response_time_ms', 'cost_usd', 'user_feedback', 'created_at']
    list_filter = ['ai_model', 'user_feedback', 'created_at']
    search_fields = ['response', 'question__question', 'question__user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_tokens']
    list_per_page = 50
    
    fieldsets = (
        ('Question Link', {
            'fields': ('question',)
        }),
        ('Response Content', {
            'fields': ('response', 'response_tokens')
        }),
        ('AI Model Information', {
            'fields': ('ai_model', 'model_version', 'confidence_score')
        }),
        ('Performance Metrics', {
            'fields': ('response_time_ms', 'total_tokens', 'cost_usd')
        }),
        ('User Feedback', {
            'fields': ('user_feedback',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_question_preview(self, obj):
        return obj.question.question[:80] + "..." if len(obj.question.question) > 80 else obj.question.question
    get_question_preview.short_description = "Question"
    
    def get_chat_type(self, obj):
        return obj.question.chat_type
    get_chat_type.short_description = "Chat Type"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question__user', 'question__place', 'question__agency')
