from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import MyUserCreationForm, MyAuthenticationForm, ProfileEditForm, CustomPasswordChangeForm
from .models import PersonalProfile
from .models import UserPreferences # Added import for UserPreferences

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        # Check if user is staff and redirect accordingly
        from listings.models import PlaceStaff
        staff_places = PlaceStaff.objects.filter(user=request.user)
        if staff_places.exists():
            # Redirect to first staff dashboard
            first_staff_place = staff_places.first().place
            return redirect('staff_dashboard', place_id=first_staff_place.id)
        return redirect('home')
    
    if request.method == 'POST':
        form = MyAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                
                # Check if user is staff and redirect accordingly
                from listings.models import PlaceStaff
                staff_places = PlaceStaff.objects.filter(user=user)
                if staff_places.exists():
                    # Redirect to first staff dashboard
                    first_staff_place = staff_places.first().place
                    return redirect('staff_dashboard', place_id=first_staff_place.id)
                
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MyAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Clear any existing messages and show only this one
            messages.get_messages(request)
            messages.success(request, f'Account created successfully! Let\'s complete your profile.')
            return redirect('profile_completion')  # Redirect to profile completion instead of home
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MyUserCreationForm()
    
    return render(request, 'users/signup.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html')

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})

@login_required
def profile_completion_view(request):
    if request.method == 'POST':
        # Handle profile completion form submission
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        location = request.POST.get('location')
        date_of_birth = request.POST.get('date_of_birth')
        
        # Update user model
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        # Create or update personal profile
        profile, created = PersonalProfile.objects.get_or_create(user=user)
        profile.first_name = first_name
        profile.last_name = last_name
        profile.phone = phone
        profile.location = location
        if date_of_birth:
            profile.date_of_birth = date_of_birth
        profile.save()
        
        # Clear any existing messages and show only this one
        messages.get_messages(request)
        messages.success(request, 'Profile completed successfully! Now let\'s set your preferences.')
        return redirect('preferences_setup')
    
    return render(request, 'users/profile_completion.html')

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'users/password_change.html', {'form': form})

@login_required
def preferences_setup_view(request):
    if request.method == 'POST':
        # Handle preferences form submission
        user = request.user
        
        # Get or create preferences object
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        
        # Get form data
        interests = request.POST.getlist('interests')
        budget = request.POST.get('budget')
        travel_style = request.POST.get('travel_style')
        travel_frequency = request.POST.get('travel_frequency')
        preferred_group_size = request.POST.get('preferred_group_size')
        transportation_preferences = request.POST.getlist('transportation_preferences')
        activity_preferences = request.POST.getlist('activity_preferences')
        preferred_destinations = request.POST.getlist('preferred_destinations')
        notifications = request.POST.getlist('notifications')
        
        # Update preferences
        if interests:
            preferences.interests = interests
        if budget:
            preferences.budget_range = budget
        if travel_style:
            preferences.travel_style = travel_style
        if travel_frequency:
            preferences.travel_frequency = travel_frequency
        if preferred_group_size:
            preferences.preferred_group_size = preferred_group_size
        if transportation_preferences:
            preferences.transportation_preferences = transportation_preferences
        if activity_preferences:
            preferences.activity_preferences = activity_preferences
        if preferred_destinations:
            preferences.preferred_destinations = preferred_destinations
        if notifications:
            preferences.notification_preferences = {
                'email': 'email' in notifications,
                'sms': 'sms' in notifications,
                'push': 'push' in notifications
            }
        
        preferences.save()
        
        # Clear any existing messages and show only this one
        messages.get_messages(request)
        messages.success(request, 'Welcome to TravelsKe! Your account setup is complete.')
        return redirect('home')
    
    return render(request, 'users/preferences_setup.html')

@login_required
def dashboard(request):
    """User dashboard with overview of places, agencies, and activities"""
    user = request.user
    
    # Get user's places and agencies
    user_places = user.places_created.all()[:3]  # Get first 3
    user_agencies = user.agencies_owned.all()[:3]  # Get first 3
    
    # Get counts
    user_places_count = user.places_created.count()
    user_agencies_count = user.agencies_owned.count()
    
    # Get date plans count (if the model exists)
    try:
        from listings.models import DatePlan
        date_plans_count = DatePlan.objects.filter(creator=user).count()
    except:
        date_plans_count = 0
    
    # Get active bookings count (placeholder for now)
    active_bookings_count = 0
    
    context = {
        'user_places': user_places,
        'user_agencies': user_agencies,
        'user_places_count': user_places_count,
        'user_agencies_count': user_agencies_count,
        'date_plans_count': date_plans_count,
        'active_bookings_count': active_bookings_count,
    }
    
    return render(request, 'users/dashboard.html', context)
