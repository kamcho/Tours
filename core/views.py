"""
Core views for TravelsKe platform
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, SubscriptionPlan, VerificationRequest, Payment
from listings.models import Place, Agency, PlaceCategory
import random
from users.models import MyUser
import base64
import requests
from requests.auth import HTTPBasicAuth
import logging
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods


logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def robots_txt(request):
    """Serve robots.txt file"""
    content = """User-agent: *
Allow: /

# Allow all search engines to crawl the site
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Slurp
Allow: /

# Disallow admin and private areas
Disallow: /admin/
Disallow: /accounts/
Disallow: /api/
Disallow: /private/
Disallow: /django-admin/

# Allow important pages
Allow: /tours/
Allow: /events/
Allow: /places/
Allow: /agencies/
Allow: /search/

# Sitemap location
Sitemap: https://tourske.com/sitemap.xml

# Crawl delay (optional - be respectful to server)
Crawl-delay: 1
"""
    return HttpResponse(content, content_type="text/plain")


@require_http_methods(["GET"])
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def sitemap_xml(request):
    """Serve sitemap.xml file"""
    # Generate simple sitemap
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://tourske.com/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://tourske.com/tours/</loc>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://tourske.com/events/</loc>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://tourske.com/places/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://tourske.com/agencies/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://tourske.com/about/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://tourske.com/contact/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    return HttpResponse(content, content_type="application/xml; charset=utf-8")


def about_view(request):
    """About page view"""
    return render(request, 'core/about.html')


def contact_view(request):
    """Contact page view"""
    return render(request, 'core/contact.html')


def privacy_policy_view(request):
    """Privacy policy page view"""
    return render(request, 'core/privacy_policy.html')


def terms_of_service_view(request):
    """Terms of service page view"""
    return render(request, 'core/terms_of_service.html')


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
    user_agencies = Agency.objects.filter(owner=request.user)
    
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
            messages.warning(request, f'You already have an active {plan.get_subscription_type_display()} subscription.')
            return redirect('core:subscription_page')
        
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
        return redirect('core:subscription_payment', subscription_id=subscription.id)
    
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
                return redirect('core:subscription_page')
            else:
                messages.error(request, 'Payment failed. Please try again.')
        else:
            messages.error(request, 'Invalid payment method.')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'core/subscription_payment.html', context)

def verification_request(request):  # Temporarily removed @login_required for debugging
    """Submit verification request with payment"""
    print(f"🔍 DEBUG: ===== verification_request view called =====")
    print(f"🔍 DEBUG: Method: {request.method}")
    print(f"🔍 DEBUG: User: {request.user}")
    print(f"🔍 DEBUG: URL: {request.path}")
    print(f"🔍 DEBUG: Request headers: {dict(request.headers)}")
    
    if request.method == 'POST':
        print(f"🔍 DEBUG: Processing POST request")
        
        # Get form data
        verification_type = request.POST.get('verification_type')
        phone_number = request.POST.get('phone_number', '')
        duration_years = int(request.POST.get('duration_years', 1))
        place_id = request.POST.get('place_id', '')
        agency_id = request.POST.get('agency_id', '')
        
        print(f"🔍 DEBUG: verification_type: {verification_type}")
        print(f"🔍 DEBUG: phone_number: {phone_number}")
        print(f"🔍 DEBUG: duration_years: {duration_years}")
        print(f"🔍 DEBUG: place_id: {place_id}")
        print(f"🔍 DEBUG: agency_id: {agency_id}")
        print(f"🔍 DEBUG: FILES data: {request.FILES}")
        
        # Calculate amount based on years (KES 1000 per year)
        amount = duration_years * 1000
        print(f"🔍 DEBUG: calculated amount: {amount}")
        
        # Validate place/agency selection for business verifications
        if verification_type in ['place', 'agency']:
            if verification_type == 'place' and not place_id:
                messages.error(request, 'Please select a place to verify.')
                return redirect('core:verification_request')
            elif verification_type == 'agency' and not agency_id:
                messages.error(request, 'Please select an agency to verify.')
                return redirect('core:verification_request')
        
        # Check if user already has a pending verification request for the same target
        existing_request = None
        if verification_type == 'place' and place_id:
            existing_request = VerificationRequest.objects.filter(
                user=request.user,
                place_id=place_id,
                status='pending'
            ).first()
        elif verification_type == 'agency' and agency_id:
            existing_request = VerificationRequest.objects.filter(
                user=request.user,
                agency_id=agency_id,
                status='pending'
            ).first()
        elif verification_type == 'user':
            existing_request = VerificationRequest.objects.filter(
            user=request.user,
                verification_type='user',
            status='pending'
        ).first()
        
        if existing_request:
            print(f"🔍 DEBUG: Found existing pending request: {existing_request.id}, updating it...")
            verification = existing_request
            # Update existing request with new data
            verification.verification_type = verification_type
            verification.phone_number = phone_number
            verification.duration_years = duration_years
            if place_id:
                verification.place_id = place_id
            if agency_id:
                verification.agency_id = agency_id
            verification.save()
        else:
            print(f"🔍 DEBUG: Creating new verification request...")
            # Create new verification request
            verification_data = {
                'user': request.user,
                'verification_type': verification_type,
                'phone_number': phone_number,
                'duration_years': duration_years,
            }
            
            if place_id:
                verification_data['place_id'] = place_id
            if agency_id:
                verification_data['agency_id'] = agency_id
                
            verification = VerificationRequest.objects.create(**verification_data)
        
        print(f"🔍 DEBUG: Using verification request ID: {verification.id}")
        
        # Handle ID document upload for individual users
        if verification_type == 'user' and 'id_document' in request.FILES:
            print(f"🔍 DEBUG: Processing ID document upload")
            verification.id_document = request.FILES['id_document']
            verification.save()
        
        print(f"🔍 DEBUG: About to call process_verification_payment...")
        
        # Process M-Pesa payment
        success = process_verification_payment(verification, phone_number, amount)
        
        print(f"🔍 DEBUG: process_verification_payment returned: {success}")
        
        if success:
            messages.success(request, f'Verification request submitted successfully! Payment of KES {amount} initiated via M-Pesa. Please complete the payment on your phone.')
        else:
            messages.warning(request, 'Verification request submitted but payment failed. Please contact support.')
        
        return redirect('core:subscription_page')
    else:
        # No context needed for the selection page
        context = {}
    
    return render(request, 'core/verification_request.html', context)

@login_required
def my_subscriptions(request):
    """User's subscription management page"""
    subscriptions = Subscription.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate total monthly cost for active subscriptions
    total_monthly_cost = sum(
        subscription.amount for subscription in subscriptions 
        if subscription.status == 'active' and subscription.is_active
    )
    
    context = {
        'subscriptions': subscriptions,
        'total_monthly_cost': total_monthly_cost,
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
        return redirect('core:my_subscriptions')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'core/cancel_subscription.html', context)

@login_required
def admin_verification_dashboard(request):
    """Admin dashboard for managing verification requests"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff only.')
        return redirect('core:subscription_page')
    
    # Get all verification requests
    verification_requests = VerificationRequest.objects.all().order_by('-created_at')
    
    # Get payment statistics
    total_payments = Payment.objects.count()
    completed_payments = Payment.objects.filter(payment_status='completed').count()
    pending_payments = Payment.objects.filter(payment_status='pending').count()
    failed_payments = Payment.objects.filter(payment_status='failed').count()
    
    # Get verification statistics
    total_verifications = verification_requests.count()
    pending_verifications = verification_requests.filter(status='pending').count()
    payment_completed = verification_requests.filter(status='payment_completed').count()
    under_review = verification_requests.filter(status='under_review').count()
    approved_verifications = verification_requests.filter(status='approved').count()
    rejected_verifications = verification_requests.filter(status='rejected').count()
    
    context = {
        'verification_requests': verification_requests,
        'total_payments': total_payments,
        'completed_payments': completed_payments,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        'total_verifications': total_verifications,
        'pending_verifications': pending_verifications,
        'payment_completed': payment_completed,
        'under_review': under_review,
        'approved_verifications': approved_verifications,
        'rejected_verifications': rejected_verifications,
    }
    
    return render(request, 'core/admin_verification_dashboard.html', context)

@login_required
def admin_payment_dashboard(request):
    """Admin dashboard for managing payments"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff only.')
        return redirect('core:subscription_page')
    
    # Get all payments
    payments = Payment.objects.all().order_by('-transaction_date')
    
    # Get payment statistics
    total_amount = sum(payment.amount for payment in payments if payment.payment_status == 'completed')
    mpesa_payments = payments.filter(payment_method='mpesa')
    card_payments = payments.filter(payment_method='card')
    
    # Calculate percentages
    total_payments_count = payments.count()
    mpesa_percentage = (mpesa_payments.count() / total_payments_count * 100) if total_payments_count > 0 else 0
    card_percentage = (card_payments.count() / total_payments_count * 100) if total_payments_count > 0 else 0
    
    # Get payment status counts
    payment_status_counts = {}
    for status_choice in Payment.PAYMENT_STATUS_CHOICES:
        status = status_choice[0]
        count = payments.filter(payment_status=status).count()
        payment_status_counts[status] = count
    
    context = {
        'payments': payments,
        'total_amount': total_amount,
        'mpesa_payments': mpesa_payments,
        'card_payments': card_payments,
        'mpesa_percentage': round(mpesa_percentage, 1),
        'card_percentage': round(card_percentage, 1),
        'payment_status_counts': payment_status_counts,
    }
    
    return render(request, 'core/admin_payment_dashboard.html', context)

def process_mpesa_payment(subscription, phone_number):
    """Process M-Pesa payment for subscription"""
    try:
        # Use the same M-Pesa implementation from your working code
        from core.models import PaymentSettings
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
        import requests
        from requests.auth import HTTPBasicAuth
        
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

def process_verification_payment(verification, phone_number, amount):
    """Process M-Pesa payment for verification request"""
    try:
        print(f"🔍 DEBUG: process_verification_payment called with phone={phone_number}, amount={amount}")
        
        # Use the working implementation from tour booking
        print("🚀 DEBUG: Using working M-Pesa implementation...")
        
        # Process phone number
        if phone_number.startswith('0'):
            phone = '254' + phone_number[1:]
        elif phone_number.startswith('254'):
            phone = phone_number
        else:
            phone = phone_number
        
        print(f"📱 DEBUG: Processed phone number: {phone}")
        
        # Get M-Pesa credentials from database
        try:
            from .models import PaymentSettings
            settings = PaymentSettings.get_settings()
            consumer_key = settings.mpesa_consumer_key
            consumer_secret = settings.mpesa_consumer_secret
            passkey = settings.mpesa_passkey
            business_shortcode = settings.mpesa_business_shortcode
            callback_url = settings.mpesa_callback_url
            print(f"🔑 DEBUG: Using credentials from database - shortcode: {business_shortcode}")
        except Exception as e:
            print(f"❌ DEBUG: Failed to get payment settings: {e}")
            return False
        
        # Generate timestamp and password (working approach from tour booking)
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        concatenated_string = f"{business_shortcode}{passkey}{timestamp}"
        password = base64.b64encode(concatenated_string.encode()).decode('utf-8')
        
        print(f"🔐 DEBUG: Generated password and timestamp: {timestamp}")
        
        # Generate access token
        access_token_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(access_token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        
        if response.status_code != 200:
            print(f"❌ DEBUG: Failed to generate access token: {response.status_code}")
            return False
        
        access_token = response.json()['access_token']
        print(f"🎫 DEBUG: Generated access token: {access_token[:20]}...")
        
        # Prepare STK push request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": int(business_shortcode),
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": int(business_shortcode),
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": f"VER_{verification.id}",
            "TransactionDesc": f"Verification: {verification.get_verification_type_display()}",
        }
        
        print(f"📦 DEBUG: STK push payload prepared")
        print(f"   Amount: KES {amount}")
        print(f"   Phone: {phone}")
        print(f"   Business: {business_shortcode}")
        
        # Make STK push request
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📡 DEBUG: STK push response status: {response.status_code}")
        print(f"📡 DEBUG: STK push response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ DEBUG: STK push successful: {result}")
            
            # Create payment record
            from core.models import Payment
            payment = Payment.objects.create(
                verification_request=verification,
                amount=amount,
                payment_method='mpesa',
                payment_status='processing',
                mpesa_checkout_request_id=result.get('CheckoutRequestID', ''),
                mpesa_merchant_request_id=result.get('MerchantRequestID', ''),
                payment_reference=f"VER_{verification.id}_{timestamp}"
            )
            
            print(f"🔍 DEBUG: Created payment record: {payment.id}")
            
            # Update verification status
            verification.status = 'pending'
            verification.save()
            return True
        else:
            print(f"❌ DEBUG: STK push failed with status {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Error processing verification payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def mpesa_callback(request):
    """Handle M-Pesa STK push callback"""
    if request.method == 'POST':
        try:
            data = request.POST
            print(f"🔍 DEBUG: M-Pesa callback received: {data}")
            
            # Extract callback data
            checkout_request_id = data.get('CheckoutRequestID')
            merchant_request_id = data.get('MerchantRequestID')
            result_code = data.get('ResultCode')
            result_desc = data.get('ResultDesc')
            
            # Find the payment by checkout request ID
            try:
                from core.models import Payment
                payment = Payment.objects.get(mpesa_checkout_request_id=checkout_request_id)
                print(f"🔍 DEBUG: Found payment: {payment.id}")
                
                if result_code == '0':
                    # Payment successful
                    payment.mpesa_result_code = result_code
                    payment.mpesa_result_desc = result_desc
                    payment.mpesa_merchant_request_id = merchant_request_id
                    payment.mark_completed()
                    
                    print(f"✅ Payment {payment.id} completed successfully")
                    return JsonResponse({'status': 'success'})
                else:
                    # Payment failed
                    payment.mpesa_result_code = result_code
                    payment.mpesa_result_desc = result_desc
                    payment.mark_failed(result_desc)
                    
                    print(f"❌ Payment {payment.id} failed: {result_desc}")
                    return JsonResponse({'status': 'failed', 'error': result_desc})
                    
            except Payment.DoesNotExist:
                print(f"❌ Payment not found for checkout request ID: {checkout_request_id}")
                return JsonResponse({'status': 'error', 'error': 'Payment not found'})
                
        except Exception as e:
            print(f"❌ Error processing M-Pesa callback: {str(e)}")
            return JsonResponse({'status': 'error', 'error': str(e)})
    
    return JsonResponse({'status': 'error', 'error': 'Invalid request method'})

@login_required
def verify_user(request):
    """User verification page"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '')
        duration_months = int(request.POST.get('duration_months', 3))
        
        # Calculate amount based on months (KES 100 per 3 months)
        amount = (duration_months // 3) * 100
        
        # Check if user already has a pending verification request
        existing_request = VerificationRequest.objects.filter(
            user=request.user,
            verification_type='user',
            status='pending'
        ).first()
        
        # Convert months to years for storage (round up to nearest year)
        duration_years = (duration_months + 11) // 12  # Round up to nearest year
        
        if existing_request:
            verification = existing_request
            verification.phone_number = phone_number
            verification.duration_years = duration_years
            verification.save()
        else:
            verification = VerificationRequest.objects.create(
                user=request.user,
                verification_type='user',
                phone_number=phone_number,
                duration_years=duration_years,
            )
        
        # Handle ID document upload
        if 'id_document' in request.FILES:
            verification.id_document = request.FILES['id_document']
            verification.save()
        
        # Process M-Pesa payment
        success = process_verification_payment(verification, phone_number, amount)
        
        if success:
            messages.success(request, f'Verification request submitted successfully! Payment of KES {amount} initiated via M-Pesa. Please complete the payment on your phone.')
        else:
            messages.warning(request, 'Verification request submitted but payment failed. Please contact support.')
        
        return redirect('core:subscription_page')
    
    return render(request, 'core/verify_user.html')

@login_required
def verify_place(request):
    """Place verification page"""
    if request.method == 'POST':
        place_id = request.POST.get('place_id')
        phone_number = request.POST.get('phone_number', '')
        duration_years = int(request.POST.get('duration_years', 1))
        
        if not place_id:
            messages.error(request, 'Please select a place to verify.')
            return redirect('core:verify_place')
        
        # Calculate amount based on years (KES 1000 per year)
        amount = duration_years * 1000
        
        # Check if user already has a pending verification request for this place
        existing_request = VerificationRequest.objects.filter(
            user=request.user,
            place_id=place_id,
            status='pending'
        ).first()
        
        if existing_request:
            verification = existing_request
            verification.phone_number = phone_number
            verification.duration_years = duration_years
            verification.save()
        else:
            verification = VerificationRequest.objects.create(
                user=request.user,
                verification_type='place',
                place_id=place_id,
                phone_number=phone_number,
                duration_years=duration_years,
            )
        
        # Process M-Pesa payment
        success = process_verification_payment(verification, phone_number, amount)
        
        if success:
            messages.success(request, f'Verification request submitted successfully! Payment of KES {amount} initiated via M-Pesa. Please complete the payment on your phone.')
        else:
            messages.warning(request, 'Verification request submitted but payment failed. Please contact support.')
        
        return redirect('core:subscription_page')
    
    # Get user's unverified places
    user_places = Place.objects.filter(created_by=request.user, verified=False)
    
    context = {
        'user_places': user_places,
    }
    return render(request, 'core/verify_place.html', context)

@login_required
def verify_agency(request):
    """Agency verification page"""
    if request.method == 'POST':
        agency_id = request.POST.get('agency_id')
        phone_number = request.POST.get('phone_number', '')
        duration_years = int(request.POST.get('duration_years', 1))
        
        if not agency_id:
            messages.error(request, 'Please select an agency to verify.')
            return redirect('core:verify_agency')
        
        # Calculate amount based on years (KES 1000 per year)
        amount = duration_years * 1000
        
        # Check if user already has a pending verification request for this agency
        existing_request = VerificationRequest.objects.filter(
            user=request.user,
            agency_id=agency_id,
            status='pending'
        ).first()
        
        if existing_request:
            verification = existing_request
            verification.phone_number = phone_number
            verification.duration_years = duration_years
            verification.save()
        else:
            verification = VerificationRequest.objects.create(
                user=request.user,
                verification_type='agency',
                agency_id=agency_id,
                phone_number=phone_number,
                duration_years=duration_years,
            )
        
        # Process M-Pesa payment
        success = process_verification_payment(verification, phone_number, amount)
        
        if success:
            messages.success(request, f'Verification request submitted successfully! Payment of KES {amount} initiated via M-Pesa. Please complete the payment on your phone.')
        else:
            messages.warning(request, 'Verification request submitted but payment failed. Please contact support.')
        
        return redirect('core:subscription_page')
    
    # Get user's unverified agencies
    user_agencies = Agency.objects.filter(owner=request.user, verified=False)
    
    context = {
        'user_agencies': user_agencies,
    }
    return render(request, 'core/verify_agency.html', context)


# AI Insights Views

@login_required
def ai_insights_dashboard(request):
    """Dashboard for AI insights and analytics"""
    # Check if user has active AI insights subscription
    ai_insights_subscription = Subscription.objects.filter(
        user=request.user,
        subscription_type='ai_insights',
        status='active'
    ).first()
    
    if not ai_insights_subscription:
        messages.warning(request, 'You need an AI Insights subscription to access this feature.')
        return redirect('core:subscription_page')
    
    # Get user's places and agencies
    user_places = Place.objects.filter(created_by=request.user)
    user_agencies = Agency.objects.filter(owner=request.user)
    
    # Get recent insights reports
    from .models import AIInsightsReport
    recent_reports = AIInsightsReport.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Get chat interaction statistics
    from .models import AIChatInteraction
    from django.db import models
    chat_stats = AIChatInteraction.objects.filter(
        user=request.user
    ).aggregate(
        total_interactions=models.Count('id'),
        total_tokens=models.Sum('tokens_used'),
        avg_response_time=models.Avg('response_time_ms')
    )
    
    context = {
        'ai_insights_subscription': ai_insights_subscription,
        'user_places': user_places,
        'user_agencies': user_agencies,
        'recent_reports': recent_reports,
        'chat_stats': chat_stats,
    }
    
    return render(request, 'core/ai_insights_dashboard.html', context)


@login_required
def generate_ai_insights(request):
    """Generate AI insights report for a specific place/agency"""
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        content_id = request.POST.get('content_id')
        report_type = request.POST.get('report_type')
        
        # Check subscription
        subscription = Subscription.objects.filter(
            user=request.user,
            subscription_type='ai_insights',
            status='active'
        ).first()
        
        if not subscription:
            return JsonResponse({'success': False, 'error': 'No active AI Insights subscription'})
        
        # Check usage limits
        from .models import AIInsightsReport
        monthly_reports = AIInsightsReport.objects.filter(
            user=request.user,
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).count()
        
        if monthly_reports >= subscription.subscription_plan.max_insights_reports:
            return JsonResponse({'success': False, 'error': 'Monthly report limit reached'})
        
        # Create insights report
        report = AIInsightsReport.objects.create(
            user=request.user,
            subscription=subscription,
            report_type=report_type,
            title=f"{report_type.replace('_', ' ').title()} Report",
            content_type=content_type,
            content_id=content_id,
            status='generating'
        )
        
        # TODO: Integrate with OpenAI API to generate actual insights
        # For now, create a placeholder report
        report.insights_summary = "AI insights generation is being implemented. This is a placeholder report."
        report.detailed_analysis = {
            'summary': 'Placeholder analysis data',
            'metrics': {},
            'trends': []
        }
        report.recommendations = [
            'Implement AI insights generation',
            'Connect with OpenAI API',
            'Add more detailed analytics'
        ]
        report.status = 'completed'
        report.generation_completed_at = timezone.now()
        report.save()
        
        return JsonResponse({
            'success': True,
            'report_id': report.id,
            'message': 'Insights report generated successfully'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Date Builder Views

@login_required
def date_builder_dashboard(request):
    """Dashboard for date builder functionality"""
    # Check if user has active date builder subscription
    date_builder_subscription = Subscription.objects.filter(
        user=request.user,
        subscription_type='date_builder',
        status='active'
    ).first()
    
    if not date_builder_subscription:
        messages.warning(request, 'You need a Date Builder subscription to access this feature.')
        return redirect('core:subscription_page')
    
    # Get user's date preferences
    from .models import DateBuilderPreference
    user_preferences = DateBuilderPreference.objects.filter(user=request.user).first()
    
    # Get recent date suggestions
    from .models import DateBuilderSuggestion
    recent_suggestions = DateBuilderSuggestion.objects.filter(
        user=request.user
    ).order_by('-generated_at')[:5]
    
    # Get available places and agencies for suggestions
    available_places = Place.objects.filter(verified=True)
    available_agencies = Agency.objects.filter(verified=True)
    
    context = {
        'date_builder_subscription': date_builder_subscription,
        'user_preferences': user_preferences,
        'recent_suggestions': recent_suggestions,
        'available_places': available_places,
        'available_agencies': available_agencies,
    }
    
    return render(request, 'core/date_builder_dashboard.html', context)


@login_required
def create_date_preferences(request):
    """Create or update date builder preferences"""
    if request.method == 'POST':
        # Get form data
        preferred_activities = request.POST.getlist('preferred_activities')
        activity_intensity = request.POST.get('activity_intensity')
        preferred_food_types = request.POST.getlist('preferred_food_types')
        dietary_restrictions = request.POST.getlist('dietary_restrictions')
        budget_range = request.POST.get('budget_range')
        preferred_transport = request.POST.getlist('preferred_transport')
        max_travel_distance = request.POST.get('max_travel_distance')
        preferred_duration = request.POST.get('preferred_duration')
        group_size = request.POST.get('group_size')
        special_requirements = request.POST.get('special_requirements')
        
        # Create or update preferences
        from .models import DateBuilderPreference
        preferences, created = DateBuilderPreference.objects.get_or_create(
            user=request.user,
            defaults={
                'preferred_activities': preferred_activities,
                'activity_intensity': activity_intensity,
                'preferred_food_types': preferred_food_types,
                'dietary_restrictions': dietary_restrictions,
                'budget_range': budget_range,
                'preferred_transport': preferred_transport,
                'max_travel_distance': max_travel_distance,
                'preferred_duration': preferred_duration,
                'group_size': group_size,
                'special_requirements': special_requirements,
            }
        )
        
        if not created:
            # Update existing preferences
            preferences.preferred_activities = preferred_activities
            preferences.activity_intensity = activity_intensity
            preferences.preferred_food_types = preferred_food_types
            preferences.dietary_restrictions = dietary_restrictions
            preferences.budget_range = budget_range
            preferences.preferred_transport = preferred_transport
            preferences.max_travel_distance = max_travel_distance
            preferences.preferred_duration = preferred_duration
            preferences.group_size = group_size
            preferences.special_requirements = special_requirements
            preferences.save()
        
        messages.success(request, 'Date preferences saved successfully!')
        return redirect('core:date_builder_dashboard')
    
    # Get existing preferences for form
    from .models import DateBuilderPreference
    user_preferences = DateBuilderPreference.objects.filter(user=request.user).first()
    
    context = {
        'user_preferences': user_preferences,
        'activity_types': DateBuilderPreference.ACTIVITY_TYPES,
        'food_preferences': DateBuilderPreference.FOOD_PREFERENCES,
        'transport_preferences': DateBuilderPreference.TRANSPORT_PREFERENCES,
    }
    
    return render(request, 'core/create_date_preferences.html', context)


@login_required
def generate_date_suggestion(request):
    """Generate AI-powered date suggestion based on user preferences"""
    if request.method == 'POST':
        # Check subscription
        subscription = Subscription.objects.filter(
            user=request.user,
            subscription_type='date_builder',
            status='active'
        ).first()
        
        if not subscription:
            return JsonResponse({'success': False, 'error': 'No active Date Builder subscription'})
        
        # Get user preferences
        from .models import DateBuilderPreference
        preferences = DateBuilderPreference.objects.filter(user=request.user).first()
        if not preferences:
            return JsonResponse({'success': False, 'error': 'Please create date preferences first'})
        
        # TODO: Integrate with OpenAI API to generate actual date suggestions
        # For now, create a placeholder suggestion
        
        # Get some verified places and agencies for suggestions
        suggested_places = Place.objects.filter(verified=True)[:3]
        suggested_agencies = Agency.objects.filter(verified=True)[:2]
        
        from .models import DateBuilderSuggestion
        suggestion = DateBuilderSuggestion.objects.create(
            user=request.user,
            preferences=preferences,
            title=f"Perfect {preferences.preferred_duration.replace('_', ' ').title()} for {preferences.group_size.replace('_', ' ').title()}",
            description=f"AI-generated suggestion based on your preferences for {preferences.activity_intensity} activities, {preferences.budget_range} budget, and {preferences.preferred_duration}.",
            estimated_cost=1000.00,  # Placeholder cost
            estimated_duration=preferences.preferred_duration,
            recommended_places=[p.id for p in suggested_places],
            recommended_agencies=[a.id for a in suggested_agencies],
            itinerary=[
                {
                    'time': '09:00 AM',
                    'activity': 'Start your adventure',
                    'location': 'Meeting point',
                    'description': 'Begin your perfect day'
                },
                {
                    'time': '12:00 PM',
                    'activity': 'Lunch break',
                    'location': 'Recommended restaurant',
                    'description': 'Enjoy local cuisine'
                },
                {
                    'time': '03:00 PM',
                    'activity': 'Afternoon activity',
                    'location': 'Activity venue',
                    'description': 'Continue your adventure'
                }
            ],
            ai_model='placeholder',
            confidence_score=0.85,
            status='generated'
        )
        
        return JsonResponse({
            'success': True,
            'suggestion_id': suggestion.id,
            'message': 'Date suggestion generated successfully'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def view_date_suggestion(request, suggestion_id):
    """View a specific date suggestion"""
    from .models import DateBuilderSuggestion
    suggestion = get_object_or_404(DateBuilderSuggestion, id=suggestion_id, user=request.user)
    
    # Get recommended places and agencies
    recommended_places = Place.objects.filter(id__in=suggestion.recommended_places)
    recommended_agencies = Agency.objects.filter(id__in=suggestion.recommended_agencies)
    
    context = {
        'suggestion': suggestion,
        'recommended_places': recommended_places,
        'recommended_agencies': recommended_agencies,
    }
    
    return render(request, 'core/view_date_suggestion.html', context)


@login_required
def accept_date_suggestion(request, suggestion_id):
    """Accept a date suggestion"""
    from .models import DateBuilderSuggestion
    suggestion = get_object_or_404(DateBuilderSuggestion, id=suggestion_id, user=request.user)
    
    if request.method == 'POST':
        suggestion.accept()
        messages.success(request, 'Date suggestion accepted! Start planning your adventure.')
        return redirect('core:date_builder_dashboard')
    
    return redirect('core:view_date_suggestion', suggestion_id=suggestion.id)


@login_required
def complete_date_suggestion(request, suggestion_id):
    """Mark a date suggestion as completed"""
    from .models import DateBuilderSuggestion
    suggestion = get_object_or_404(DateBuilderSuggestion, id=suggestion_id, user=request.user)
    
    if request.method == 'POST':
        suggestion.complete()
        messages.success(request, 'Date completed! How was your experience?')
        return redirect('core:date_builder_dashboard')
    
    return redirect('core:view_date_suggestion', suggestion_id=suggestion.id)


# Enhanced Subscription Management

@login_required
def subscription_analytics(request):
    """Analytics dashboard for subscription usage"""
    # Get all user subscriptions
    user_subscriptions = Subscription.objects.filter(user=request.user)
    
    # Get usage statistics
    from .models import AIChatInteraction, AIInsightsReport, DateBuilderSuggestion
    ai_chat_usage = AIChatInteraction.objects.filter(
        user=request.user,
        created_at__month=timezone.now().month,
        created_at__year=timezone.now().year
    ).count()
    
    insights_reports = AIInsightsReport.objects.filter(
        user=request.user,
        created_at__month=timezone.now().month,
        created_at__year=timezone.now().year
    ).count()
    
    date_suggestions = DateBuilderSuggestion.objects.filter(
        user=request.user,
        created_at__month=timezone.now().month,
        created_at__year=timezone.now().year
    ).count()
    
    # Calculate subscription costs
    total_monthly_cost = sum(sub.amount for sub in user_subscriptions if sub.is_active)
    
    context = {
        'user_subscriptions': user_subscriptions,
        'ai_chat_usage': ai_chat_usage,
        'insights_reports': insights_reports,
        'date_suggestions': date_suggestions,
        'total_monthly_cost': total_monthly_cost,
    }
    
    return render(request, 'core/subscription_analytics.html', context)


@login_required
def upgrade_subscription(request, subscription_id):
    """Upgrade an existing subscription"""
    current_subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        new_plan_id = request.POST.get('new_plan_id')
        new_plan = get_object_or_404(SubscriptionPlan, id=new_plan_id, is_active=True)
        
        # Check if upgrade is valid
        if new_plan.plan_type != current_subscription.subscription_type:
            messages.error(request, 'Cannot upgrade to a different subscription type.')
            return redirect('core:subscription_analytics')
        
        # Calculate prorated amount
        days_remaining = current_subscription.days_remaining
        if days_remaining > 0:
            # Calculate refund for remaining days
            daily_rate = current_subscription.amount / current_subscription.duration_days
            refund_amount = daily_rate * days_remaining
            
            # Calculate cost for new plan
            new_daily_rate = new_plan.price / new_plan.duration_days
            new_cost = new_daily_rate * days_remaining
            
            upgrade_cost = new_cost - refund_amount
        else:
            upgrade_cost = new_plan.price
        
        # Create upgrade subscription
        upgrade_subscription = Subscription.objects.create(
            user=request.user,
            subscription_type=new_plan.plan_type,
            amount=upgrade_cost,
            end_date=timezone.now() + timedelta(days=new_plan.duration_days),
            status='pending',
            target_content_type=current_subscription.target_content_type,
            target_object_id=current_subscription.target_object_id
        )
        
        messages.success(request, f'Subscription upgrade created. Cost: KES {upgrade_cost:.2f}')
        return redirect('core:subscription_payment', subscription_id=upgrade_subscription.id)
    
    # Get available upgrade plans
    upgrade_plans = SubscriptionPlan.objects.filter(
        plan_type=current_subscription.subscription_type,
        target_type='user',  # Assuming user subscriptions
        is_active=True
    ).exclude(price__lte=current_subscription.amount)
    
    context = {
        'current_subscription': current_subscription,
        'upgrade_plans': upgrade_plans,
    }
    
    return render(request, 'core/upgrade_subscription.html', context)


# M-Pesa Account Balance Views

@login_required
def get_mpesa_balance(request):
    """Get M-Pesa account balance for Admin users"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
    
    try:
        from .mpesa_service import MPesaService
        mpesa_service = MPesaService()
        balance_result = mpesa_service.get_account_balance()
        
        # Log the raw response for debugging
        logger.info(f"Raw M-Pesa balance result: {balance_result}")
        
        if balance_result and 'error' not in balance_result:
            # Check if this is the immediate success response from M-Pesa
            if 'ResponseCode' in balance_result and balance_result.get('ResponseCode') == '0':
                # This is the immediate success response - M-Pesa accepted the request
                # For now, we'll simulate the balance data since M-Pesa sends it asynchronously
                # In a production environment, you'd store the ConversationID and check for results
                
                # Simulate balance data (replace with actual M-Pesa balance when available)
                simulated_balance = "0.00"  # This should come from M-Pesa callback
                
                balance_info = {
                    'success': True,
                    'data': {
                        'ResponseCode': balance_result.get('ResponseCode'),
                        'ResponseDescription': balance_result.get('ResponseDescription'),
                        'ConversationID': balance_result.get('ConversationID'),
                        'OriginatorConversationID': balance_result.get('OriginatorConversationID'),
                        'status': 'request_accepted',
                        'message': 'Balance query accepted by M-Pesa. Using simulated balance for now.',
                        'WorkingAccountBalance': simulated_balance,
                        'note': 'Real balance data will come via M-Pesa callback URL'
                    },
                    'timestamp': timezone.now().isoformat()
                }
            elif 'Result' in balance_result:
                # This is the actual result data from the callback
                result = balance_result['Result']
                logger.info(f"M-Pesa Result: {result}")
                
                if result.get('ResultCode') == '0':
                    # Success - extract balance from ResultParameters
                    result_params = result.get('ResultParameters', {}).get('ResultParameter', [])
                    logger.info(f"Result Parameters: {result_params}")
                    
                    # Find AccountBalance parameter
                    balance_info = None
                    for param in result_params:
                        if param.get('Key') == 'AccountBalance':
                            balance_info = param.get('Value', '')
                            break
                    
                    if balance_info:
                        # Parse the balance string: "Working Account|KES|700000.00|700000.00|0.00|0.00&Float Account|KES|0.00|0.00|0.00|0.00..."
                        # Extract Working Account balance (main business account)
                        accounts = balance_info.split('&')
                        working_account = None
                        for account in accounts:
                            if 'Working Account' in account:
                                parts = account.split('|')
                                if len(parts) >= 3:
                                    working_account = parts[2]  # Current balance
                                    break
                        
                        balance_info = {
                            'success': True,
                            'data': {
                                'ResultCode': result.get('ResultCode'),
                                'ResultDesc': result.get('ResultDesc'),
                                'AccountBalance': balance_info,
                                'WorkingAccountBalance': working_account,
                                'ConversationID': result.get('ConversationID'),
                                'TransactionID': result.get('TransactionID'),
                                'status': 'balance_retrieved'
                            },
                            'timestamp': timezone.now().isoformat()
                        }
                    else:
                        balance_info = {
                            'success': False,
                            'error': 'Balance information not found in response',
                            'details': 'Account balance parameter missing from M-Pesa response',
                            'timestamp': timezone.now().isoformat()
                        }
                else:
                    # M-Pesa API error
                    balance_info = {
                        'success': False,
                        'error': f'M-Pesa API Error: {result.get("ResultCode")}',
                        'details': result.get('ResultDesc', 'Unknown error'),
                        'timestamp': timezone.now().isoformat()
                    }
            else:
                # Log the unexpected response structure
                logger.warning(f"Unexpected response structure. Keys: {list(balance_result.keys())}")
                logger.warning(f"Full response: {balance_result}")
                
                # Unexpected response format - return the raw response for debugging
                balance_info = {
                    'success': False,
                    'error': 'Unexpected response format',
                    'details': f'Response keys: {list(balance_result.keys())}. Check logs for full response.',
                    'raw_response': balance_result,
                    'timestamp': timezone.now().isoformat()
                }
        else:
            # Error occurred
            error_msg = balance_result.get('error', 'Failed to retrieve balance information') if balance_result else 'Failed to retrieve balance information'
            details = balance_result.get('details', '') if balance_result else ''
            
            balance_info = {
                'success': False,
                'error': error_msg,
                'details': details,
                'timestamp': timezone.now().isoformat()
            }
        
        return JsonResponse(balance_info)
        
    except Exception as e:
        logger.error(f"Error getting M-Pesa balance: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to retrieve balance information',
            'details': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@login_required
def test_mpesa_balance(request):
    """Test page for M-Pesa balance functionality"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Admin privileges required.'}, status=403)
    
    context = {
        'user': request.user,
    }
    return render(request, 'core/test_mpesa_balance.html', context)


@require_POST
def partnership_form_submit(request):
    """Handle partnership form submissions and send emails"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.http import JsonResponse
        
        # Get form data
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        # Validate required fields
        if not all([email, phone, message]):
            return JsonResponse({
                'success': False,
                'error': 'All fields are required'
            }, status=400)
        
        # Prepare email content
        subject = f'New Partnership Request from {email}'
        email_content = f"""
New Partnership Request

From: {email}
Phone: {phone}

Message:
{message}

---
This email was sent from the ToursKe partnership form.
        """.strip()
        
        # Send email
        recipient_email = getattr(settings, 'PARTNERSHIP_EMAIL_RECIPIENT', 'kevingitundu@gmail.com')
        
        send_mail(
            subject=subject,
            message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Partnership request sent successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to send partnership request: {str(e)}'
        }, status=500)


# -----------------------------
# Sample data seeding (staff only)
# -----------------------------

def _random_kenyan_phone():
    return '07' + ''.join(str(random.randint(0, 9)) for _ in range(8))

def _random_name():
    first_names = [
        'Achieng', 'Wanjiku', 'Njeri', 'Atieno', 'Chebet', 'Akinyi', 'Nyambura', 'Wairimu', 'Wambui', 'Naliaka',
        'Odhiambo', 'Kamau', 'Otieno', 'Kiptoo', 'Mutiso', 'Mwangi', 'Omondi', 'Barasa', 'Kiplagat', 'Juma'
    ]
    last_names = [
        'Omondi', 'Otieno', 'Mwangi', 'Kamau', 'Njoroge', 'Mutiso', 'Barasa', 'Cheruiyot', 'Chebet', 'Wambui',
        'Wekesa', 'Wanjiru', 'Muthoni', 'Were', 'Oketch', 'Karimi', 'Maina', 'Koech', 'Kiptoo', 'Ochieng'
    ]
    return random.choice(first_names), random.choice(last_names)

@login_required
def seed_sample_data(request):
    if not request.user.is_staff:
        messages.error(request, 'Only staff can seed sample data.')
        return redirect('core:subscription_page')

    created_users = 0
    created_places = 0
    created_agencies = 0

    # Ensure a category exists
    category = PlaceCategory.objects.first() or PlaceCategory.objects.create(name='Attractions')

    # Create 100 users (verified)
    for _ in range(10):
        first, last = _random_name()
        username = f"{first.lower()}.{last.lower()}{random.randint(100,999)}"
        email = f"{username}@example.ke"
        if MyUser.objects.filter(email=email).exists():
            continue
        try:
            user = MyUser.objects.create_user(username=username, email=email, password='Pass12345!')
            user.first_name = first
            user.last_name = last
            if hasattr(user, 'phone'):
                setattr(user, 'phone', _random_kenyan_phone())
            if hasattr(user, 'gender'):
                setattr(user, 'gender', random.choice(['male', 'female']))
            if hasattr(user, 'is_verified'):
                user.is_verified = True
            user.save()
            created_users += 1
        except Exception:
            continue

    creators = list(MyUser.objects.order_by('-id')[:10]) or [request.user]
    locations = ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Naivasha', 'Diani', 'Malindi']

    kenyan_places = [
        "Carnivore","Java House","Artcaffe","Mama Oliech","Nyama Mama","Fogo Gaucho","Talisman","Urban Eatery","CJ's","Seven Seafood and Grill",
        "Aero Club Restaurant","Ranalo Foods","Big Square","KFC","Pizza Inn","Galito's","Mambo Italia","About Thyme","Osteria del Chianti","Mezze on the Deck",
        "Mercado","Hemmingways Brasserie","Lord Erroll","360 Degrees Pizza","Urban Burger","Roast by Carnivore","Abyssinia","Wasp and Sprout","Slims Restaurant","Hashmi BBQ",
        "River Cafe","Tamambo","News Cafe","Sankara Rooftop","Copper Ivy","J's Fresh Bar and Kitchen","Captain’s Terrace","Mama Rocks","Village Market Food Court","Westgate Food Court",
        "Two Rivers Food Court","Kempinski Cafe","Nairobi Street Kitchen","Cheka Japanese Restaurant","For You Chinese","Phoenician","Kosewe","Nargis","Kilimanjaro Jamia","Steers",
        "Domino’s Pizza","Chicken Inn","Planet Yogurt","Cold Stone Creamery","Naked Pizza","Subway","Burger King","Magic Planet","Funscapes","Playland",
        "Safari Walk","Paradise Lost","Bomas of Kenya","Uhuru Park","Jungle Gym","Kids City","Rock City","Two Rivers Funscapes","Village Bowl"
    ]

    kenyan_agencies = [
        "Bonfire Adventures","Expeditions Maasai Safaris","Pollman’s Tours and Safaris","Glory Safaris","Let's Go Travel","Bountiful Safaris","Gamewatchers Safaris","JT Safaris",
        "Kenya Walking Survivors Safaris","Apt Holidays","Go Kenya Tours","Sense of Africa","Safarilink","Bestcamp Kenya","Dream Kenya Safaris","Eastern Vacations","African Quest Safaris",
        "Bush and Events Africa","Peony Safaris","Perfect Wilderness Tours"
    ]

    # Create 70 places (verified)
    for i in range(70):
        try:
            creator = random.choice(creators)
            place_name = kenyan_places[i % len(kenyan_places)]
            place = Place.objects.create(
                name=place_name,
                description="A beautiful destination with amazing experiences across Kenya.",
                category=category,
                location=random.choice(locations),
                address="Kenya",
                website=f"https://{place_name}.com",
                contact_email=f"{place_name}@gmail.com",
                contact_phone=_random_kenyan_phone(),
                is_active=True,
                created_by=creator,
            )
            if hasattr(place, 'verified'):
                place.verified = True
                place.save()
            created_places += 1
        except Exception:
            continue

    # Create 20 agencies (verified)
    agency_types = ['travel_tours', 'transport', 'photo_video', 'accommodation', 'events_planners']
    for i in range(20):
        try:
            owner = random.choice(creators)
            agency_name = kenyan_agencies[i % len(kenyan_agencies)]
            agency = Agency.objects.create(
                name=agency_name,
                description="Professional services for travel and events across Kenya.",
                agency_type=random.choice(agency_types),
                email=f"{agency_name}@gmail.com",
                phone=_random_kenyan_phone(),
                website=f"https://{agency_name}.com",
                address="Kenya",
                city=random.choice(locations),
                country="Kenya",
                owner=owner,
                status='active',
            )
            if hasattr(agency, 'verified'):
                agency.verified = True
                agency.save()
            created_agencies += 1
        except Exception:
            continue

    return render(request, 'core/seed_result.html', {
        'created_users': created_users,
        'created_places': created_places,
        'created_agencies': created_agencies,
    })
from django.shortcuts import render
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
import json
from .models import PageVisit

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_admin)
def analytics_dashboard(request):
    # Total users
    total_users = MyUser.objects.count()
    
    # Total visits
    total_visits = PageVisit.objects.count()

    # Unique visitors - count distinct sessions (now all visits should have sessions)
    unique_visitors = PageVisit.objects.values("session_key").distinct().count()
    ip = PageVisit.objects.values('ip_address').distinct().count()
    # Average load time
    avg_load_time = PageVisit.objects.aggregate(avg_time=Avg('load_time'))['avg_time'] or 0

    # Top pages
    top_pages = (
        PageVisit.objects.values("path")
        .annotate(visits=Count("id"))
        .order_by("-visits")[:10]
    )

    # Entry pages (first page per session)
    entry_pages = (
        PageVisit.objects.values("path")
        .annotate(entries=Count("session_key", distinct=True))
        .order_by("-entries")[:5]
    )

    # Exit pages (last page per session) — simplified
    exit_pages = top_pages

    # Real visits trend data - last 7 days
    today = timezone.now().date()
    visits_by_day = []
    day_labels = []
    
    for i in range(6, -1, -1):  # Last 7 days
        day = today - timedelta(days=i)
        day_visits = PageVisit.objects.filter(
            timestamp__date=day
        ).count()
        visits_by_day.append(day_visits)
        day_labels.append(day.strftime('%a'))  # Mon, Tue, etc.

    # Hourly visits for today
    hourly_visits = []
    hourly_labels = []
    for hour in range(24):
        hour_visits = PageVisit.objects.filter(
            timestamp__date=today,
            timestamp__hour=hour
        ).count()
        hourly_visits.append(hour_visits)
        hourly_labels.append(f"{hour:02d}:00")

    # Browser/Device analytics - group by parsed browser name
    browser_stats = {}
    all_visits = PageVisit.objects.values("user_agent").annotate(count=Count("id"))
    
    for visit in all_visits:
        browser_name = parse_user_agent(visit['user_agent'])
        if browser_name in browser_stats:
            browser_stats[browser_name] += visit['count']
        else:
            browser_stats[browser_name] = visit['count']
    
    # Convert to list format for charts
    browser_data = [
        {'browser': browser, 'count': count} 
        for browser, count in sorted(browser_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Prepare data for charts (JSON safe)
    chart_data = {
        'top_pages_labels': [page['path'][:30] for page in top_pages],
        'top_pages_data': [page['visits'] for page in top_pages],
        'visits_trend_labels': day_labels,
        'visits_trend_data': visits_by_day,
        'hourly_labels': hourly_labels,
        'hourly_data': hourly_visits,
        'browser_labels': [browser['browser'][:20] for browser in browser_data],
        'browser_data': [browser['count'] for browser in browser_data]
    }

    context = {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "avg_load_time": avg_load_time,
        "top_pages": top_pages,
        "entry_pages": entry_pages,
        "exit_pages": exit_pages,
        "chart_data_json": json.dumps(chart_data),
        "browser_data": browser_data,
        "total_users": total_users,'ip':ip,
    }
    return render(request, "core/analytics_dashboard.html", context)

def parse_user_agent(user_agent):
    """Simple user agent parsing to extract browser name"""
    if not user_agent:
        return "Unknown"
    
    user_agent = user_agent.lower()
    if 'chrome' in user_agent and 'edg' not in user_agent:
        return "Chrome"
    elif 'firefox' in user_agent:
        return "Firefox"
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        return "Safari"
    elif 'edg' in user_agent:
        return "Edge"
    elif 'opera' in user_agent:
        return "Opera"
    else:
        return "Other"
