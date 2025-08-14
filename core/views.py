from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, SubscriptionPlan, VerificationRequest, Payment
from listings.models import Place, Agency
import base64
import requests
from requests.auth import HTTPBasicAuth

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
