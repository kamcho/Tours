from django.urls import path
from . import views
from . import subscription_views as sub_views

app_name = 'core'

urlpatterns = [
    # Static pages
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    
    # Existing URLs
    path('subscription/', sub_views.subscription_page, name='subscription_page'),
    path('subscription/plan/<int:plan_id>/', sub_views.subscribe_to_plan, name='subscribe_to_plan'),
    path('subscription/payment/<int:subscription_id>/', sub_views.subscription_payment, name='subscription_payment'),
    path('subscription/choose/<str:tier>/', sub_views.subscription_choose_target, name='subscription_choose_target'),
    path('verification/request/', views.verification_request, name='verification_request'),
    path('verification/user/', views.verify_user, name='verify_user'),
    path('verification/place/', views.verify_place, name='verify_place'),
    path('verification/agency/', views.verify_agency, name='verify_agency'),
    path('verification/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('subscription/my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscription/cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
    
    # AI Insights URLs
    path('ai-insights/dashboard/', sub_views.ai_insights_dashboard, name='ai_insights_dashboard'),
    path('ai-insights/generate/', sub_views.generate_ai_insights, name='generate_ai_insights'),
    
    # Date Builder URLs
    path('date-builder/dashboard/', sub_views.date_builder_dashboard, name='date_builder_dashboard'),
    path('date-builder/preferences/', sub_views.create_date_preferences, name='create_date_preferences'),
    path('date-builder/generate-suggestion/', sub_views.generate_date_suggestion, name='generate_date_suggestion'),
    path('date-builder/suggestion/<int:suggestion_id>/', sub_views.view_date_suggestion, name='view_date_suggestion'),
    path('date-builder/suggestion/<int:suggestion_id>/accept/', sub_views.accept_date_suggestion, name='accept_date_suggestion'),
    path('date-builder/suggestion/<int:suggestion_id>/complete/', sub_views.complete_date_suggestion, name='complete_date_suggestion'),
    
    # Enhanced Subscription Management
    path('subscription/analytics/', sub_views.subscription_analytics, name='subscription_analytics'),
    path('subscription/upgrade/<int:subscription_id>/', sub_views.upgrade_subscription, name='upgrade_subscription'),
    
    # M-Pesa Account Balance
    path('mpesa/balance/', views.get_mpesa_balance, name='get_mpesa_balance'),
    path('mpesa/test/', views.test_mpesa_balance, name='test_mpesa_balance'),
    
    # Partnership form
    path('partnership/submit/', views.partnership_form_submit, name='partnership_form_submit'),
    
    # Admin dashboards
    path('admin/verification-dashboard/', views.admin_verification_dashboard, name='admin_verification_dashboard'),
    path('admin/payment-dashboard/', views.admin_payment_dashboard, name='admin_payment_dashboard'),
    
    # Seeding sample data (staff only)
    path('seed/sample-data/', views.seed_sample_data, name='seed_sample_data'),
] 