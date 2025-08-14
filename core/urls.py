from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('subscription/', views.subscription_page, name='subscription_page'),
    path('subscription/plan/<int:plan_id>/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('subscription/payment/<int:subscription_id>/', views.subscription_payment, name='subscription_payment'),
    path('verification/request/', views.verification_request, name='verification_request'),
    path('subscription/my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscription/cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
] 