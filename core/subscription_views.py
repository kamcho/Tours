from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
import base64
import requests
from requests.auth import HTTPBasicAuth
from .models import Subscription, SubscriptionPlan, VerificationRequest
from listings.models import Place, Agency

@login_required
def subscription_page(request):
    """Main subscription page showing all available plans"""
    # Get active subscription plans
    user_plans = SubscriptionPlan.objects.filter(target_type='user', is_active=True)
    place_plans = SubscriptionPlan.objects.filter(target_type='place', is_active=True)
    agency_plans = SubscriptionPlan.objects.filter(target_type='agency', is_active=True)
    
    # Get user's current subscriptions
    user_subscriptions = Subscription.objects.filter(user=request.user, status='active')
    
    # Check if user has places or agencies
    user_places = Place.objects.filter(created_by=request.user)
    user_agencies = Agency.objects.filter(created_by=request.user)
    
    context = {
        'user_plans': user_plans,
        'place_plans': place_plans,
        'agency_plans': agency_plans,
        'user_subscriptions': user_subscriptions,
        'user_places': user_places,
        'user_agencies': user_agencies,
    }
    
    return render(request, 'core/subscription_page.html', context)

@login_required
def subscribe_to_plan(request, plan_id):
    """Subscribe to a specific plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    
    if request.method == 'POST':
        # Check if user already has an active subscription of this type
        existing_subscription = Subscription.objects.filter(
            user=request.user,
            subscription_type=plan.plan_type,
            status='active'
        ).first()
        
        if existing_subscription:
            messages.warning(request, f'You already have an active {plan.get_plan_type_display()} subscription.')
            return redirect('subscription_page')
        
        # Create subscription
        end_date = timezone.now() + timedelta(days=plan.duration_days)
        subscription = Subscription.objects.create(
            user=request.user,
            subscription_type=plan.plan_type,
            amount=plan.price,
            end_date=end_date,
            status='pending'
        )
        
        # Redirect to payment page
        return redirect('subscription_payment', subscription_id=subscription.id)
    
    context = {
        'plan': plan,
    }
    return render(request, 'core/subscribe_to_plan.html', context)

@login_required
def subscription_payment(request, subscription_id):
    """Payment page for subscription"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        phone_number = request.POST.get('phone_number')
        
        if payment_method == 'mpesa':
            # Process M-Pesa payment
            success = process_mpesa_payment(subscription, phone_number)
            if success:
                messages.success(request, 'Payment successful! Your subscription is now active.')
                return redirect('subscription_page')
            else:
                messages.error(request, 'Payment failed. Please try again.')
        else:
            messages.error(request, 'Invalid payment method.')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'core/subscription_payment.html', context)

@login_required
def verification_request(request):
    """Submit verification request"""
    if request.method == 'POST':
        verification_type = request.POST.get('verification_type')
        business_name = request.POST.get('business_name', '')
        business_registration = request.POST.get('business_registration', '')
        address = request.POST.get('address', '')
        phone_number = request.POST.get('phone_number', '')
        email = request.POST.get('email', '')
        
        # Check if user already has a pending verification request
        existing_request = VerificationRequest.objects.filter(
            user=request.user,
            status='pending'
        ).first()
        
        if existing_request:
            messages.warning(request, 'You already have a pending verification request.')
            return redirect('subscription_page')
        
        # Create verification request
        verification = VerificationRequest.objects.create(
            user=request.user,
            verification_type=verification_type,
            business_name=business_name,
            business_registration=business_registration,
            address=address,
            phone_number=phone_number,
            email=email,
        )
        
        # Handle file uploads
        if 'id_document' in request.FILES:
            verification.id_document = request.FILES['id_document']
        if 'business_license' in request.FILES:
            verification.business_license = request.FILES['business_license']
        if 'address_proof' in request.FILES:
            verification.address_proof = request.FILES['address_proof']
        
        verification.save()
        
        messages.success(request, 'Verification request submitted successfully! We will review it within 24-48 hours.')
        return redirect('subscription_page')
    
    return render(request, 'core/verification_request.html')

@login_required
def my_subscriptions(request):
    """User's subscription management page"""
    subscriptions = Subscription.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'subscriptions': subscriptions,
    }
    return render(request, 'core/my_subscriptions.html', context)

@login_required
def cancel_subscription(request, subscription_id):
    """Cancel a subscription"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.save()
        messages.success(request, 'Subscription cancelled successfully.')
        return redirect('my_subscriptions')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'core/cancel_subscription.html', context)

def process_mpesa_payment(subscription, phone_number):
    """Process M-Pesa payment for subscription"""
    try:
        # Use the same M-Pesa implementation from your working code
        from .models import PaymentSettings
        settings = PaymentSettings.get_settings()
        
        # Process phone number
        if phone_number.startswith('0'):
            phone = '254' + phone_number[1:]
        elif phone_number.startswith('254'):
            phone = phone_number
        else:
            phone = phone_number
        
        # Generate timestamp and password
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        concatenated_string = f"{settings.mpesa_business_shortcode}{settings.mpesa_passkey}{timestamp}"
        password = base64.b64encode(concatenated_string.encode()).decode('utf-8')
        
        # Generate access token
        access_token_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(access_token_url, auth=HTTPBasicAuth(settings.mpesa_consumer_key, settings.mpesa_consumer_secret))
        
        if response.status_code != 200:
            return False
        
        access_token = response.json()['access_token']
        
        # Prepare STK push request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": int(settings.mpesa_business_shortcode),
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(subscription.amount),
            "PartyA": phone,
            "PartyB": int(settings.mpesa_business_shortcode),
            "PhoneNumber": phone,
            "CallBackURL": settings.mpesa_callback_url,
            "AccountReference": f"SUB_{subscription.id}",
            "TransactionDesc": f"Subscription: {subscription.get_subscription_type_display()}",
        }
        
        # Make STK push request
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ResponseCode') == '0':
                # Update subscription with payment details
                subscription.payment_reference = f"MPESA_{subscription.id}_{timestamp}"
                subscription.payment_method = 'mpesa'
                subscription.status = 'active'
                subscription.activate_services()
                subscription.save()
                return True
        
        return False
        
    except Exception as e:
        print(f"Error processing M-Pesa payment: {str(e)}")
        return False 