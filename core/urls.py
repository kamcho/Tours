from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Static pages
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    
    # Existing URLs
    path('subscription/', views.subscription_page, name='subscription_page'),
    path('subscription/plan/<int:plan_id>/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('subscription/payment/<int:subscription_id>/', views.subscription_payment, name='subscription_payment'),
    path('verification/request/', views.verification_request, name='verification_request'),
    path('verification/user/', views.verify_user, name='verify_user'),
    path('verification/place/', views.verify_place, name='verify_place'),
    path('verification/agency/', views.verify_agency, name='verify_agency'),
    path('verification/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('subscription/my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscription/cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
    
    # AI Insights URLs
    path('ai-insights/dashboard/', views.ai_insights_dashboard, name='ai_insights_dashboard'),
    path('ai-insights/generate/', views.generate_ai_insights, name='generate_ai_insights'),
    
    # Date Builder URLs
    path('date-builder/dashboard/', views.date_builder_dashboard, name='date_builder_dashboard'),
    path('date-builder/preferences/', views.create_date_preferences, name='create_date_preferences'),
    path('date-builder/generate-suggestion/', views.generate_date_suggestion, name='generate_date_suggestion'),
    path('date-builder/suggestion/<int:suggestion_id>/', views.view_date_suggestion, name='view_date_suggestion'),
    path('date-builder/suggestion/<int:suggestion_id>/accept/', views.accept_date_suggestion, name='accept_date_suggestion'),
    path('date-builder/suggestion/<int:suggestion_id>/complete/', views.complete_date_suggestion, name='complete_date_suggestion'),
    
    # Enhanced Subscription Management
    path('subscription/analytics/', views.subscription_analytics, name='subscription_analytics'),
    path('subscription/upgrade/<int:subscription_id>/', views.upgrade_subscription, name='upgrade_subscription'),
    
    # M-Pesa Account Balance
    path('mpesa/balance/', views.get_mpesa_balance, name='get_mpesa_balance'),
    path('mpesa/test/', views.test_mpesa_balance, name='test_mpesa_balance'),
    
    # Admin dashboards
    path('admin/verification-dashboard/', views.admin_verification_dashboard, name='admin_verification_dashboard'),
    path('admin/payment-dashboard/', views.admin_payment_dashboard, name='admin_payment_dashboard'),
] 