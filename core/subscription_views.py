from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
import base64
import requests
from requests.auth import HTTPBasicAuth
from .models import Subscription, SubscriptionPlan, VerificationRequest, AIChatInteraction, AIInsightsReport, DateBuilderPreference, DateBuilderSuggestion
from listings.models import Place, Agency
import json
from django.db import models

@login_required
def subscription_page(request):
    """Main subscription page showing all available plans"""
    # Plans are rendered statically in the template; model was simplified
    user_plans = []
    place_plans = []
    agency_plans = []

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
            messages.warning(request, f'You already have an active {plan.get_plan_type_display()} subscription.')
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
                messages.success(request, 'Payment initiated. You will receive a confirmation shortly.')
                return redirect('core:subscription_page')
            else:
                messages.error(request, 'Payment failed. Please try again.')
        else:
            messages.error(request, 'Invalid payment method.')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'core/subscription_payment.html', context)


@login_required
def subscription_choose_target(request, tier):
    """Selection page to pick a Place or Agency and enter phone number to pay via STK"""
    # Normalize tier
    tier = tier.lower()
    if tier not in ['free', 'basic', 'gold', 'premium']:
        messages.error(request, 'Invalid plan tier selected.')
        return redirect('subscription_page')

    # Fetch plan by name (simplified model)
    plan = SubscriptionPlan.objects.filter(name__iexact=tier).first()

    # User content to choose from
    user_places = Place.objects.filter(created_by=request.user)
    user_agencies = Agency.objects.filter(owner=request.user)

    if request.method == 'POST':
        target_value = request.POST.get('target_id')  # encoded like 'place:12' or 'agency:7'
        phone_number = request.POST.get('phone_number')

        # Validate
        if not target_value or not phone_number:
            messages.error(request, 'Please select a target and enter your phone number.')
            return redirect('core:subscription_choose_target', tier=tier)

        # Parse target
        try:
            parts = target_value.split(':', 1)
            target_type = parts[0]
            target_id = int(parts[1])
        except Exception:
            messages.error(request, 'Invalid selection. Please try again.')
            return redirect('core:subscription_choose_target', tier=tier)

        # Resolve plan based on selection (same plan for all targets)
        selected_plan = plan
        if not selected_plan:
            messages.error(request, 'No subscription plan found for the selected tier and target.')
            return redirect('core:subscription_page')

        # Resolve target object
        if target_type == 'place':
            target_obj = get_object_or_404(Place, id=target_id, created_by=request.user)
        else:
            target_obj = get_object_or_404(Agency, id=target_id, owner=request.user)

        # Create subscription (pending)
        end_date = timezone.now() + timedelta(days=selected_plan.duration_days)
        # Map tier to subscription_type on simplified model
        tier_to_type = {
            'basic': 'ai_chat',
            'gold': 'premium',
            'premium': 'premium',
            'free': 'verification',
        }
        subscription = Subscription.objects.create(
            user=request.user,
            subscription_type=tier_to_type.get(tier, 'premium'),
            amount=selected_plan.price,
            end_date=end_date,
            status='pending',
        )

        # Attach generic target (store type label as string)
        subscription.target_content_type = 'place' if target_type == 'place' else 'agency'
        subscription.target_object_id = target_obj.id
        subscription.save()

        # Trigger STK push
        if process_mpesa_payment(subscription, phone_number):
            messages.success(request, 'Payment initiated. You will receive a confirmation shortly.')
            return redirect('core:subscription_page')
        else:
            messages.error(request, 'Payment failed. Please try again.')
            return redirect('core:subscription_choose_target', tier=tier)

    context = {
        'tier': tier,
        'plan': plan,
        'user_places': user_places,
        'user_agencies': user_agencies,
    }
    return render(request, 'core/subscription_choose_target.html', context)

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
            return redirect('core:subscription_page')
        
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
        return redirect('subscription_page')
    
    # Get user's places and agencies
    user_places = Place.objects.filter(created_by=request.user)
    user_agencies = Agency.objects.filter(created_by=request.user)
    
    # Get recent insights reports
    recent_reports = AIInsightsReport.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Get chat interaction statistics
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
        return redirect('subscription_page')
    
    # Get user's date preferences
    user_preferences = DateBuilderPreference.objects.filter(user=request.user).first()
    
    # Get recent date suggestions
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
        return redirect('date_builder_dashboard')
    
    # Get existing preferences for form
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
        preferences = DateBuilderPreference.objects.filter(user=request.user).first()
        if not preferences:
            return JsonResponse({'success': False, 'error': 'Please create date preferences first'})
        
        # TODO: Integrate with OpenAI API to generate actual date suggestions
        # For now, create a placeholder suggestion
        
        # Get some verified places and agencies for suggestions
        suggested_places = Place.objects.filter(verified=True)[:3]
        suggested_agencies = Agency.objects.filter(verified=True)[:2]
        
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
    suggestion = get_object_or_404(DateBuilderSuggestion, id=suggestion_id, user=request.user)
    
    if request.method == 'POST':
        suggestion.accept()
        messages.success(request, 'Date suggestion accepted! Start planning your adventure.')
        return redirect('date_builder_dashboard')
    
    return redirect('view_date_suggestion', suggestion_id=suggestion.id)


@login_required
def complete_date_suggestion(request, suggestion_id):
    """Mark a date suggestion as completed"""
    suggestion = get_object_or_404(DateBuilderSuggestion, id=suggestion_id, user=request.user)
    
    if request.method == 'POST':
        suggestion.complete()
        messages.success(request, 'Date completed! How was your experience?')
        return redirect('date_builder_dashboard')
    
    return redirect('view_date_suggestion', suggestion_id=suggestion.id)


# Enhanced Subscription Management

@login_required
def subscription_analytics(request):
    """Analytics dashboard for subscription usage"""
    # Get all user subscriptions
    user_subscriptions = Subscription.objects.filter(user=request.user)
    
    # Get usage statistics
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
            return redirect('subscription_analytics')
        
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
        return redirect('subscription_payment', subscription_id=upgrade_subscription.id)
    
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