from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
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
    
    # Admin dashboards
    path('admin/verification-dashboard/', views.admin_verification_dashboard, name='admin_verification_dashboard'),
    path('admin/payment-dashboard/', views.admin_payment_dashboard, name='admin_payment_dashboard'),
] 