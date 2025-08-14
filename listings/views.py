from django.shortcuts import render, redirect
from django.views import View
from django import forms
from .models import Place, PlaceCategory, TourBooking, EventBooking, TravelGroup, GroupTours, Agency, AgencyService
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, TemplateView, CreateView
from django.urls import reverse_lazy
from .models import Event, EventComment, MenuCategory, MenuItem
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import MenuCategoryForm, MenuItemForm, TourCommentForm, EventCommentForm, TourBookingForm, EventBookingForm, EnhancedTourBookingForm, PlaceRatingForm, AgencyRatingForm, GroupToursForm, AgencyServiceForm
from .models import Features
from .forms import FeatureForm
from django.contrib import messages
from .models import PlaceRating, AgencyRating, RatingHelpful
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Case, When, Value
from core.models import PaymentMethod, PaymentTransaction, MPesaPayment, PaymentSettings
from core.mpesa_service import MPesaService
import json
import base64
import requests
from requests.auth import HTTPBasicAuth
import datetime

# Step 1: Basic Information
class PlaceBasicForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Enter the name of your place',
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Describe what makes this place special...',
            'rows': 4,
        })
    )
    category = forms.ModelChoiceField(
        queryset=PlaceCategory.objects.all(),
        empty_label="Select a category",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
        })
    )
    location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'City, County, Kenya',
        })
    )

# Step 2: Contact & Media
class PlaceContactForm(forms.Form):
    address = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Street address (optional)',
        })
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'https://yourwebsite.com (optional)',
        })
    )
    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'contact@yourplace.com (optional)',
        })
    )
    contact_phone = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': '+254 700 000 000 (optional)',
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100',
        })
    )

# Step 3: Settings & Confirmation
class PlaceSettingsForm(forms.Form):
    is_active = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded',
        })
    )

class PlaceCreateWizard(LoginRequiredMixin, View):
    """
    Modern 3-step wizard for creating a Place:
    1. Basic Information (name, description, category, location)
    2. Contact & Media (address, website, email, phone, profile picture)
    3. Settings & Confirmation (active status, review, submit)
    """
    FORMS = [PlaceBasicForm, PlaceContactForm, PlaceSettingsForm]
    TEMPLATES = [
        'listings/place_create_step1.html',
        'listings/place_create_step2.html',
        'listings/place_create_step3.html',
    ]

    def get(self, request, step=1):
        """Display the form for the current step."""
        step = int(step)
        if step > 3:
            step = 3
        
        form = self.FORMS[step-1](initial=request.session.get(f'place_step_{step}', {}))
        
        # Get progress data for all steps
        progress_data = self.get_progress_data(request, step)
        
        return render(request, self.TEMPLATES[step-1], {
            'form': form, 
            'step': step,
            'progress_data': progress_data,
            'total_steps': 3
        })

    def post(self, request, step=1):
        """Process the form for the current step."""
        step = int(step)
        if step > 3:
            step = 3
        
        form = self.FORMS[step-1](request.POST, request.FILES)
        
        if form.is_valid():
            # Save step data in session
            step_data = form.cleaned_data.copy()
            
            # Handle file uploads
            if 'profile_picture' in request.FILES:
                step_data['profile_picture'] = request.FILES['profile_picture']
            
            # Convert category object to its id for session serialization
            if 'category' in step_data and hasattr(step_data['category'], 'id'):
                step_data['category'] = step_data['category'].id
            
            request.session[f'place_step_{step}'] = step_data
            
            if step == 3:
                # Final step - create the place
                return self.create_place(request)
            else:
                # Move to next step
                return redirect(reverse('place_create_step', kwargs={'step': step+1}))
        
        # Form is invalid, show errors
        progress_data = self.get_progress_data(request, step)
        return render(request, self.TEMPLATES[step-1], {
            'form': form, 
            'step': step,
            'progress_data': progress_data,
            'total_steps': 3
        })

    def get_progress_data(self, request, current_step):
        """Get data from all previous steps for progress display."""
        data = {}
        for i in range(1, current_step + 1):
            step_data = request.session.get(f'place_step_{i}', {})
            data.update(step_data)
        return data

    def create_place(self, request):
        """Create the place from all collected data."""
        try:
            # Get all step data
            data = {}
            for i in range(1, 4):
                step_data = request.session.get(f'place_step_{i}', {})
                data.update(step_data)
            
            # Create the place
            place = Place.objects.create(
                name=data['name'],
                description=data['description'],
                category=PlaceCategory.objects.get(id=data['category']),
                location=data['location'],
                address=data.get('address', ''),
                website=data.get('website', ''),
                contact_email=data.get('contact_email', ''),
                contact_phone=data.get('contact_phone', ''),
                profile_picture=data.get('profile_picture'),
                is_active=data.get('is_active', True),
                created_by=request.user
            )
            
            # Clear session data
            for i in range(1, 4):
                if f'place_step_{i}' in request.session:
                    del request.session[f'place_step_{i}']
            
            return redirect('place_create_success')
            
        except Exception as e:
            # Handle errors gracefully
            return render(request, self.TEMPLATES[2], {
                'form': self.FORMS[2](),
                'step': 3,
                'error': 'An error occurred while creating your place. Please try again.',
                'progress_data': self.get_progress_data(request, 3),
                'total_steps': 3
            })

    def get_success_url(self):
        """Return the URL to redirect to after successful creation."""
        return reverse('place_create_success')

# Success page
def place_create_success(request):
    return render(request, 'listings/place_create_success.html')

class UserPlaceListView(LoginRequiredMixin, ListView):
    model = Place
    template_name = 'listings/user_place_list.html'
    context_object_name = 'places'
    paginate_by = 10

    def get_queryset(self):
        return Place.objects.filter(created_by=self.request.user)

class UserPlaceDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Place
    template_name = 'listings/user_place_detail.html'
    context_object_name = 'place'

    def test_func(self):
        return self.get_object().created_by == self.request.user

class UserPlaceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Place
    fields = ['name', 'description', 'category', 'location', 'address', 'website', 'contact_email', 'contact_phone', 'is_active']
    template_name = 'listings/user_place_form.html'
    success_url = reverse_lazy('user_place_list')

    def test_func(self):
        return self.get_object().created_by == self.request.user

class UserPlaceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Place
    template_name = 'listings/user_place_confirm_delete.html'
    success_url = reverse_lazy('user_place_list')

    def test_func(self):
        return self.get_object().created_by == self.request.user

class PublicPlaceListView(ListView):
    model = Place
    template_name = 'listings/public_place_list.html'
    context_object_name = 'places'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Place.objects.filter(is_active=True)
        
        # Get filter parameters
        category = self.request.GET.get('category')
        location = self.request.GET.get('location')
        search = self.request.GET.get('search')
        rating = self.request.GET.get('rating')
        
        # Apply filters
        if category and category != 'all':
            queryset = queryset.filter(category__name__icontains=category)
        
        if location:
            queryset = queryset.filter(
                Q(location__icontains=location) | 
                Q(address__icontains=location)
            )
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        if rating and rating != 'all':
            min_rating = float(rating)
            queryset = queryset.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=min_rating)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = PlaceCategory.objects.all()
        context['filtered_category'] = self.request.GET.get('category', 'all')
        context['filtered_location'] = self.request.GET.get('location', '')
        context['filtered_search'] = self.request.GET.get('search', '')
        context['filtered_rating'] = self.request.GET.get('rating', 'all')
        return context

class PublicPlaceDetailView(DetailView):
    model = Place
    template_name = 'listings/public_place_detail.html'
    context_object_name = 'place'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creator'] = self.request.user.is_authenticated and self.object.created_by == self.request.user
        context['user_rating'] = self.object.get_user_rating(self.request.user) if self.request.user.is_authenticated else None
        return context

class PublicPlaceDetailPageView(DetailView):
    model = Place
    template_name = 'listings/public_place_detail_page.html'
    context_object_name = 'place'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creator'] = self.request.user.is_authenticated and self.object.created_by == self.request.user
        return context

class AllPlacesTemplateView(TemplateView):
    template_name = 'listings/all_places_templateview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['places'] = Place.objects.filter(is_active=True)
        return context

class TravelGroupListView(ListView):
    model = TravelGroup
    template_name = 'listings/travelgroup_list.html'
    context_object_name = 'travel_groups'
    paginate_by = 10

    def get_queryset(self):
        return TravelGroup.objects.filter(is_public=True)

class TravelGroupDetailView(DetailView):
    model = TravelGroup
    template_name = 'listings/travelgroup_detail.html'
    context_object_name = 'travel_group'

class TravelGroupCreateView(LoginRequiredMixin, CreateView):
    model = TravelGroup
    template_name = 'listings/travelgroup_form.html'
    fields = ['name', 'description', 'objective', 'group_type', 'is_public']
    success_url = reverse_lazy('travelgroup_list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class TravelGroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TravelGroup
    template_name = 'listings/travelgroup_form.html'
    fields = ['name', 'description', 'objective', 'group_type', 'is_public']
    success_url = reverse_lazy('travelgroup_list')

    def test_func(self):
        return self.get_object().creator == self.request.user

class TravelGroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TravelGroup
    template_name = 'listings/travelgroup_confirm_delete.html'
    success_url = reverse_lazy('travelgroup_list')

    def test_func(self):
        return self.get_object().creator == self.request.user

class UserTravelGroupListView(LoginRequiredMixin, ListView):
    model = TravelGroup
    template_name = 'listings/user_travelgroup_list.html'
    context_object_name = 'travel_groups'
    paginate_by = 10

    def get_queryset(self):
        return TravelGroup.objects.filter(creator=self.request.user)

class GroupToursListView(ListView):
    model = GroupTours
    template_name = 'listings/grouptours_list.html'
    context_object_name = 'group_tours'
    paginate_by = 12

    def get_queryset(self):
        queryset = GroupTours.objects.filter(status__in=['planning', 'active'])
        
        # Get filter parameters
        location = self.request.GET.get('location')
        date_range = self.request.GET.get('date_range')
        tour_type = self.request.GET.get('tour_type')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        
        print(f"Debug - Filters: location={location}, date_range={date_range}, tour_type={tour_type}")
        
        # Apply filters
        if location and location != 'all':
            # Filter by destination location or 'to' field
            queryset = queryset.filter(
                Q(destination__location__icontains=location) | 
                Q(to__icontains=location)
            )
            print(f"Debug - Applied location filter: {location}, queryset count: {queryset.count()}")
        
        if date_range:
            # Simple date filtering - you can enhance this with date picker
            if date_range == 'this_month':
                from datetime import datetime, timedelta
                start_date = datetime.now().replace(day=1)
                queryset = queryset.filter(start_date__gte=start_date)
                print(f"Debug - Applied this_month filter, queryset count: {queryset.count()}")
            elif date_range == 'next_month':
                from datetime import datetime, timedelta
                next_month = datetime.now().replace(day=1) + timedelta(days=32)
                start_date = next_month.replace(day=1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                queryset = queryset.filter(start_date__gte=start_date, start_date__lte=end_date)
                print(f"Debug - Applied next_month filter, queryset count: {queryset.count()}")
        
        if tour_type and tour_type != 'all':
            # You can add tour type field to your model or filter by description
            queryset = queryset.filter(description__icontains=tour_type)
            print(f"Debug - Applied tour_type filter: {tour_type}, queryset count: {queryset.count()}")
        
        if price_min:
            queryset = queryset.filter(price_per_person__gte=float(price_min))
            print(f"Debug - Applied price_min filter: {price_min}, queryset count: {queryset.count()}")
        
        if price_max:
            queryset = queryset.filter(price_per_person__lte=float(price_max))
            print(f"Debug - Applied price_max filter: {price_max}, queryset count: {queryset.count()}")
        
        final_queryset = queryset.distinct()
        print(f"Debug - Final queryset count: {final_queryset.count()}")
        return final_queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtered_location'] = self.request.GET.get('location', 'all')
        context['filtered_date_range'] = self.request.GET.get('date_range', '')
        context['filtered_tour_type'] = self.request.GET.get('tour_type', 'all')
        context['filtered_price_min'] = self.request.GET.get('price_min', '')
        context['filtered_price_max'] = self.request.GET.get('price_max', '')
        return context

class GroupToursDetailView(DetailView):
    model = GroupTours
    template_name = 'listings/grouptours_detail.html'
    context_object_name = 'group_tour'

class GroupToursCreateView(LoginRequiredMixin, CreateView):
    model = GroupTours
    template_name = 'listings/grouptours_form.html'
    form_class = GroupToursForm
    success_url = reverse_lazy('grouptours_list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class GroupToursUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = GroupTours
    template_name = 'listings/grouptours_form.html'
    form_class = GroupToursForm
    success_url = reverse_lazy('grouptours_list')

    def test_func(self):
        return self.get_object().creator == self.request.user

class GroupToursDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = GroupTours
    template_name = 'listings/grouptours_confirm_delete.html'
    success_url = reverse_lazy('grouptours_list')

    def test_func(self):
        return self.get_object().creator == self.request.user

class UserGroupToursListView(LoginRequiredMixin, ListView):
    model = GroupTours
    template_name = 'listings/user_grouptours_list.html'
    context_object_name = 'group_tours'
    paginate_by = 10

    def get_queryset(self):
        return GroupTours.objects.filter(creator=self.request.user)

class PublicGroupToursDetailView(DetailView):
    model = GroupTours
    template_name = 'listings/public_grouptours_detail.html'
    context_object_name = 'group_tour'

    def get_queryset(self):
        return GroupTours.objects.filter(status__in=['planning', 'active']).prefetch_related('likes', 'bookmarks')

# Agency Views
class AgencyListView(ListView):
    model = Agency
    template_name = 'listings/agency_list.html'
    context_object_name = 'agencies'
    paginate_by = 12

    def get_queryset(self):
        queryset = Agency.objects.filter(status='active')
        
        # Get filter parameters
        agency_type = self.request.GET.get('agency_type')
        search = self.request.GET.get('search')
        verified_only = self.request.GET.get('verified_only')
        sort_by = self.request.GET.get('sort_by', 'newest')
        
        # Apply filters
        if agency_type and agency_type != 'all':
            queryset = queryset.filter(agency_type=agency_type)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(city__icontains=search) |
                Q(country__icontains=search)
            )
        
        if verified_only == 'true':
            queryset = queryset.filter(
                license_number__isnull=False, 
                registration_number__isnull=False
            )
        
        # Apply sorting
        if sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'verified':
            queryset = queryset.order_by(
                Case(
                    When(license_number__isnull=False, registration_number__isnull=False, then=Value(0)),
                    default=Value(1)
                ),
                'name'
            )
        else:  # newest
            queryset = queryset.order_by('-created_at')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtered_agency_type'] = self.request.GET.get('agency_type', 'all')
        context['filtered_search'] = self.request.GET.get('search', '')
        context['filtered_verified_only'] = self.request.GET.get('verified_only', 'false')
        context['filtered_sort_by'] = self.request.GET.get('sort_by', 'newest')
        return context

class AgencyDetailView(DetailView):
    model = Agency
    template_name = 'listings/agency_detail.html'
    context_object_name = 'agency'

class AgencyCreateView(LoginRequiredMixin, CreateView):
    model = Agency
    template_name = 'listings/agency_form.html'
    fields = [
        'name', 'description', 'agency_type', 'status',
        'email', 'phone', 'website',
        'address', 'city', 'country', 'postal_code',
        'license_number', 'registration_number', 'year_established',
        'facebook', 'twitter', 'instagram', 'linkedin',
        'logo', 'profile_picture'
    ]
    success_url = reverse_lazy('agency_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class AgencyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Agency
    template_name = 'listings/agency_form.html'
    fields = [
        'name', 'description', 'agency_type', 'status',
        'email', 'phone', 'website',
        'address', 'city', 'country', 'postal_code',
        'license_number', 'registration_number', 'year_established',
        'facebook', 'twitter', 'instagram', 'linkedin',
        'logo', 'profile_picture'
    ]
    success_url = reverse_lazy('agency_list')

    def test_func(self):
        return self.get_object().owner == self.request.user

class AgencyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Agency
    template_name = 'listings/agency_confirm_delete.html'
    success_url = reverse_lazy('agency_list')

    def test_func(self):
        return self.get_object().owner == self.request.user

class UserAgencyListView(LoginRequiredMixin, ListView):
    model = Agency
    template_name = 'listings/user_agency_list.html'
    context_object_name = 'agencies'
    paginate_by = 10

    def get_queryset(self):
        return Agency.objects.filter(owner=self.request.user)

class PublicAgencyDetailView(DetailView):
    model = Agency
    template_name = 'listings/public_agency_detail.html'
    context_object_name = 'agency'

    def get_queryset(self):
        return Agency.objects.filter(status='active')

# Event Views
class EventListView(ListView):
    model = Event
    template_name = 'listings/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get_queryset(self):
        queryset = Event.objects.filter(status=True)
        
        # Get filter parameters
        event_type = self.request.GET.get('event_type')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        sort_by = self.request.GET.get('sort_by', 'newest')
        
        # Apply filters
        if event_type and event_type != 'all':
            queryset = queryset.filter(event_type=event_type)
        
        if price_min:
            queryset = queryset.filter(price_per_person__gte=float(price_min))
        
        if price_max:
            queryset = queryset.filter(price_per_person__lte=float(price_max))
        
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        # Apply sorting
        if sort_by == 'oldest':
            queryset = queryset.order_by('start_date')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'price_low':
            queryset = queryset.order_by('price_per_person')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price_per_person')
        elif sort_by == 'date':
            queryset = queryset.order_by('start_date')
        else:  # newest - use start_date as fallback since no created_at field
            queryset = queryset.order_by('-start_date')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtered_event_type'] = self.request.GET.get('event_type', 'all')
        context['filtered_price_min'] = self.request.GET.get('price_min', '')
        context['filtered_price_max'] = self.request.GET.get('price_max', '')
        context['filtered_date_from'] = self.request.GET.get('date_from', '')
        context['filtered_date_to'] = self.request.GET.get('date_to', '')
        context['filtered_sort_by'] = self.request.GET.get('sort_by', 'newest')
        return context

class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'listings/event_detail.html'
    context_object_name = 'event'

    def test_func(self):
        return self.get_object().creator == self.request.user

class PublicEventDetailView(DetailView):
    model = Event
    template_name = 'listings/public_event_detail.html'
    context_object_name = 'event'

    def get_queryset(self):
        return Event.objects.filter(status=True).prefetch_related('likes', 'bookmarks')

class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    template_name = 'listings/event_form.html'
    fields = [
        'event_type', 'name', 'description', 'travel_group', 'display_picture',
        'start_date', 'end_date', 'max_participants', 'price_per_person',
        'itinerary', 'included_services'
    ]
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    template_name = 'listings/event_form.html'
    fields = [
        'event_type', 'name', 'description', 'travel_group', 'display_picture',
        'start_date', 'end_date', 'max_participants', 'price_per_person',
        'itinerary', 'included_services'
    ]
    success_url = reverse_lazy('event_list')

    def test_func(self):
        return self.get_object().creator == self.request.user

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'listings/event_confirm_delete.html'
    success_url = reverse_lazy('event_list')

    def test_func(self):
        return self.get_object().creator == self.request.user

class UserEventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'listings/user_event_list.html'
    context_object_name = 'events'
    paginate_by = 10

    def get_queryset(self):
        return Event.objects.filter(creator=self.request.user)

# Like/Unlike Views
@login_required
@require_POST
def like_tour(request, tour_id):
    try:
        tour = GroupTours.objects.get(id=tour_id)
        if request.user in tour.likes.all():
            tour.likes.remove(request.user)
            liked = False
        else:
            tour.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'total_likes': tour.total_likes()
        })
    except GroupTours.DoesNotExist:
        return JsonResponse({'error': 'Tour not found'}, status=404)

@login_required
@require_POST
def like_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        if request.user in event.likes.all():
            event.likes.remove(request.user)
            liked = False
        else:
            event.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'total_likes': event.total_likes()
        })
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)

# Bookmark/Unbookmark Views
@login_required
@require_POST
def bookmark_tour(request, tour_id):
    try:
        tour = GroupTours.objects.get(id=tour_id)
        if request.user in tour.bookmarks.all():
            tour.bookmarks.remove(request.user)
            bookmarked = False
        else:
            tour.bookmarks.add(request.user)
            bookmarked = True
        
        return JsonResponse({
            'bookmarked': bookmarked,
            'total_bookmarks': tour.total_bookmarks()
        })
    except GroupTours.DoesNotExist:
        return JsonResponse({'error': 'Tour not found'}, status=404)

@login_required
@require_POST
def bookmark_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        if request.user in event.bookmarks.all():
            event.bookmarks.remove(request.user)
            bookmarked = False
        else:
            event.bookmarks.add(request.user)
            bookmarked = True
        
        return JsonResponse({
            'bookmarked': bookmarked,
            'total_bookmarks': event.total_bookmarks()
        })
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)

# Comment Views
@login_required
@require_POST
def add_tour_comment(request, tour_id):
    try:
        tour = GroupTours.objects.get(id=tour_id)
        form = TourCommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.tour = tour
            comment.user = request.user
            comment.save()
            
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'content': comment.content,
                'user_email': comment.user.email,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        else:
            return JsonResponse({'error': 'Invalid comment data'}, status=400)
    except GroupTours.DoesNotExist:
        return JsonResponse({'error': 'Tour not found'}, status=404)

@login_required
@require_POST
def add_event_comment(request, event_id):
    try:
        print(f"Adding comment for event {event_id}")
        print(f"POST data: {request.POST}")
        
        event = Event.objects.get(id=event_id)
        print(f"Event found: {event.name}")
        
        form = EventCommentForm(request.POST)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        
        if form.is_valid():
            # Create the comment manually since EventCommentForm is not a ModelForm
            comment = EventComment.objects.create(
                event=event,
                user=request.user,
                content=form.cleaned_data['content']
            )
            
            print(f"Comment saved successfully: {comment.id}")
            
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'content': comment.content,
                'user_email': comment.user.email,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        else:
            return JsonResponse({'error': 'Invalid comment data', 'form_errors': form.errors}, status=400)
    except Event.DoesNotExist:
        print(f"Event {event_id} not found")
        return JsonResponse({'error': 'Event not found'}, status=404)
    except Exception as e:
        print(f"Unexpected error in add_event_comment: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

# Booking Views
@login_required
@require_POST
def book_tour(request, tour_id):
    try:
        tour = GroupTours.objects.get(id=tour_id)
        form = TourBookingForm(request.POST)
        
        if form.is_valid():
            # Check if tour is full
            if tour.is_full:
                return JsonResponse({'error': 'This tour is already full'}, status=400)
            
            # Check if user has already booked this tour
            if TourBooking.objects.filter(tour=tour, user=request.user, status__in=['pending', 'confirmed']).exists():
                return JsonResponse({'error': 'You have already booked this tour'}, status=400)
            
            booking = form.save(commit=False)
            booking.tour = tour
            booking.user = request.user
            booking.total_amount = tour.price_per_person * form.cleaned_data['participants']
            booking.save()
            
            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'message': 'Tour booked successfully!'
            })
        else:
            return JsonResponse({'error': 'Invalid booking data'}, status=400)
    except GroupTours.DoesNotExist:
        return JsonResponse({'error': 'Tour not found'}, status=404)

@login_required
@require_POST
def book_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        form = EventBookingForm(request.POST)
        
        if form.is_valid():
            # Check if user has already booked this event
            if EventBooking.objects.filter(event=event, user=request.user, status__in=['pending', 'confirmed']).exists():
                return JsonResponse({'error': 'You have already booked this event'}, status=400)
            
            booking = form.save(commit=False)
            booking.event = event
            booking.user = request.user
            # Assuming event has a price field, adjust as needed
            if hasattr(event, 'price') and event.price:
                booking.total_amount = event.price * form.cleaned_data['participants']
            else:
                booking.total_amount = 0
            booking.save()
            
            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'message': 'Event booked successfully!'
            })
        else:
            return JsonResponse({'error': 'Invalid booking data'}, status=400)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)

# User Dashboard Views
@method_decorator(login_required, name='dispatch')
class UserBookingsView(ListView):
    model = TourBooking
    template_name = 'listings/user_bookings.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        return TourBooking.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tour_bookings'] = TourBooking.objects.filter(user=self.request.user)
        context['event_bookings'] = EventBooking.objects.filter(user=self.request.user)
        return context

@method_decorator(login_required, name='dispatch')
class UserBookmarksView(ListView):
    template_name = 'listings/user_bookmarks.html'
    context_object_name = 'bookmarks'
    
    def get_queryset(self):
        return {
            'tours': self.request.user.bookmarked_tours.all(),
            'events': self.request.user.bookmarked_events.all()
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookmarked_tours'] = self.request.user.bookmarked_tours.all()
        context['bookmarked_events'] = self.request.user.bookmarked_events.all()
        context['liked_tours'] = self.request.user.liked_tours.all()
        context['liked_events'] = self.request.user.liked_events.all()
        return context

class FeatureCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Features
    form_class = FeatureForm
    template_name = 'listings/feature_form.html'
    
    def test_func(self):
        place = Place.objects.get(pk=self.kwargs['place_id'])
        return self.request.user == place.created_by
    
    def form_valid(self, form):
        form.instance.place_id = self.kwargs['place_id']
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('user_place_detail', kwargs={'pk': self.kwargs['place_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = Place.objects.get(pk=self.kwargs['place_id'])
        return context

class FeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Features
    form_class = FeatureForm
    template_name = 'listings/feature_form.html'
    
    def test_func(self):
        feature = self.get_object()
        return self.request.user == feature.place.creator
    
    def get_success_url(self):
        return reverse('user_place_detail', kwargs={'pk': self.object.place.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.object.place
        return context

class FeatureDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Features
    template_name = 'listings/feature_confirm_delete.html'
    
    def test_func(self):
        feature = self.get_object()
        return self.request.user == feature.place.creator
    
    def get_success_url(self):
        return reverse('user_place_detail', kwargs={'pk': self.object.place.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.object.place
        return context

class EnhancedTourBookingView(LoginRequiredMixin, View):
    """
    Enhanced tour booking view with intelligent pricing for couples and groups
    """
    template_name = 'listings/enhanced_tour_booking.html'
    
    def get(self, request, pk):
        try:
            tour = GroupTours.objects.get(pk=pk)
            
            # Check if tour is available for booking
            if tour.is_full:
                messages.error(request, 'This tour is already full and cannot accept new bookings.')
                return redirect('public_grouptours_detail', pk=pk)
            
            if tour.status not in ['planning', 'active']:
                messages.error(request, 'This tour is not currently accepting bookings.')
                return redirect('public_grouptours_detail', pk=pk)
            
            # Check if user has already booked this tour
            existing_booking = TourBooking.objects.filter(
                tour=tour, 
                user=request.user, 
                status__in=['pending', 'confirmed']
            ).first()
            
            if existing_booking:
                messages.warning(request, 'You have already booked this tour.')
                return redirect('user_bookings')
            
            form = EnhancedTourBookingForm(tour=tour)
            
            context = {
                'tour': tour,
                'form': form,
                'available_spots': tour.available_spots,
                'pricing_info': self.get_pricing_info(tour),
            }
            
            return render(request, self.template_name, context)
            
        except GroupTours.DoesNotExist:
            messages.error(request, 'Tour not found.')
            return redirect('grouptours_list')
    
    def post(self, request, pk):
        try:
            tour = GroupTours.objects.get(pk=pk)
            form = EnhancedTourBookingForm(request.POST, tour=tour)
            
            if form.is_valid():
                # Calculate total amount based on booking type
                total_amount = form.calculate_total_amount()
                
                # Create the booking
                booking = TourBooking.objects.create(
                    tour=tour,
                    user=request.user,
                    participants=form.cleaned_data['participants'],
                    special_requests=form.cleaned_data['special_requests'],
                    total_amount=total_amount
                )
                
                # Update tour participants count
                tour.current_participants += form.cleaned_data['participants']
                tour.save()
                
                messages.success(request, f'Booking successful! Your total amount is ${total_amount:.2f}')
                return redirect('user_bookings')
            else:
                # Form is invalid, show errors
                context = {
                    'tour': tour,
                    'form': form,
                    'available_spots': tour.available_spots,
                    'pricing_info': self.get_pricing_info(tour),
                }
                return render(request, self.template_name, context)
                
        except GroupTours.DoesNotExist:
            messages.error(request, 'Tour not found.')
            return redirect('grouptours_list')
    
    def get_pricing_info(self, tour):
        """Get pricing information for display"""
        pricing = {
            'individual_price': tour.price_per_person,
            'has_couple_price': bool(tour.couple_price),
            'couple_price': tour.couple_price,
            'group_discount': None,
        }
        
        # Calculate group discount (if applicable)
        if tour.max_participants >= 6:
            # 10% discount for groups of 6 or more
            pricing['group_discount'] = 0.10
        
        return pricing

class MenuCategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = MenuCategory
    form_class = MenuCategoryForm
    template_name = 'listings/menu_category_form.html'
    
    def test_func(self):
        place = Place.objects.get(pk=self.kwargs['place_pk'])
        return place.created_by == self.request.user
    
    def form_valid(self, form):
        form.instance.place = Place.objects.get(pk=self.kwargs['place_pk'])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('place_menu', kwargs={'pk': self.kwargs['place_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = Place.objects.get(pk=self.kwargs['place_pk'])
        return context

class MenuCategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = MenuCategory
    form_class = MenuCategoryForm
    template_name = 'listings/menu_category_form.html'
    
    def test_func(self):
        return self.get_object().place.created_by == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('place_menu', kwargs={'pk': self.object.place.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.object.place
        return context

class MenuCategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = MenuCategory
    template_name = 'listings/menu_category_confirm_delete.html'
    
    def test_func(self):
        return self.get_object().place.created_by == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('place_menu', kwargs={'pk': self.object.place.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.object.place
        return context

class MenuItemCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'listings/menu_item_form.html'
    
    def test_func(self):
        place = Place.objects.get(pk=self.kwargs['place_pk'])
        return place.created_by == self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['place'] = Place.objects.get(pk=self.kwargs['place_pk'])
        return kwargs
    
    def form_valid(self, form):
        form.instance.place = Place.objects.get(pk=self.kwargs['place_pk'])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('place_menu', kwargs={'pk': self.kwargs['place_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = Place.objects.get(pk=self.kwargs['place_pk'])
        return context

class MenuItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'listings/menu_item_form.html'
    
    def test_func(self):
        return self.get_object().place.created_by == self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['place'] = self.object.place
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('place_menu', kwargs={'pk': self.object.place.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.object.place
        return context

class MenuItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = MenuItem
    template_name = 'listings/menu_item_confirm_delete.html'
    
    def test_func(self):
        return self.get_object().place.created_by == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('place_menu', kwargs={'pk': self.object.place.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.object.place
        return context

class PlaceMenuView(DetailView):
    model = Place
    template_name = 'listings/place_menu.html'
    context_object_name = 'place'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_categories'] = MenuCategory.objects.filter(
            place=self.object, 
            is_active=True
        ).prefetch_related('menu_items').order_by('order', 'name')
        
        # Get featured items
        context['featured_items'] = MenuItem.objects.filter(
            place=self.object,
            is_featured=True,
            is_active=True
        ).order_by('?')[:6]  # Random 6 featured items
        
        # Check if user is the creator
        context['is_creator'] = self.request.user.is_authenticated and self.object.created_by == self.request.user
        
        return context

class UserPlaceMenuView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Place
    template_name = 'listings/user_place_menu.html'
    context_object_name = 'place'
    
    def test_func(self):
        return self.get_object().created_by == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_categories'] = MenuCategory.objects.filter(
            place=self.object
        ).prefetch_related('menu_items').order_by('order', 'name')
        
        # Get all items (including inactive) for management
        context['all_menu_items'] = MenuItem.objects.filter(
            place=self.object
        ).order_by('category__order', 'order', 'name')
        
        return context

# Rating and Review Views
@login_required
@require_POST
def submit_place_rating(request, place_id):
    """Submit or update a rating for a place"""
    try:
        place = Place.objects.get(id=place_id)
        form = PlaceRatingForm(request.POST)
        
        if form.is_valid():
            # Check if user already rated this place
            existing_rating, created = PlaceRating.objects.get_or_create(
                place=place,
                user=request.user,
                defaults=form.cleaned_data
            )
            
            if not created:
                # Update existing rating
                existing_rating.rating = form.cleaned_data['rating']
                existing_rating.comment = form.cleaned_data['comment']
                existing_rating.save()
                message = 'Your rating has been updated successfully!'
            else:
                message = 'Thank you for your rating!'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'rating': existing_rating.rating,
                'comment': existing_rating.comment,
                'average_rating': place.average_rating,
                'total_ratings': place.total_ratings
            })
        else:
            return JsonResponse({'error': 'Invalid rating data', 'form_errors': form.errors}, status=400)
            
    except Place.DoesNotExist:
        return JsonResponse({'error': 'Place not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@login_required
@require_POST
def submit_agency_rating(request, agency_id):
    """Submit or update a rating for an agency"""
    try:
        agency = Agency.objects.get(id=agency_id)
        form = AgencyRatingForm(request.POST)
        
        if form.is_valid():
            # Check if user already rated this agency
            existing_rating, created = AgencyRating.objects.get_or_create(
                agency=agency,
                user=request.user,
                defaults=form.cleaned_data
            )
            
            if not created:
                # Update existing rating
                existing_rating.rating = form.cleaned_data['rating']
                existing_rating.comment = form.cleaned_data['comment']
                existing_rating.service_type = form.cleaned_data['service_type']
                existing_rating.save()
                message = 'Your rating has been updated successfully!'
            else:
                message = 'Thank you for your rating!'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'rating': existing_rating.rating,
                'comment': existing_rating.comment,
                'service_type': existing_rating.service_type,
                'average_rating': agency.average_rating,
                'total_ratings': agency.total_ratings
            })
        else:
            return JsonResponse({'error': 'Invalid rating data', 'form_errors': form.errors}, status=400)
            
    except Agency.DoesNotExist:
        return JsonResponse({'error': 'Agency not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@login_required
@require_POST
def mark_rating_helpful(request, rating_type, rating_id):
    """Mark a rating as helpful or unhelpful"""
    try:
        if rating_type == 'place':
            rating = PlaceRating.objects.get(id=rating_id)
        elif rating_type == 'agency':
            rating = AgencyRating.objects.get(id=rating_id)
        else:
            return JsonResponse({'error': 'Invalid rating type'}, status=400)
        
        # Check if user already marked this rating as helpful
        helpful_vote, created = RatingHelpful.objects.get_or_create(
            user=request.user,
            **{f'{rating_type}_rating': rating}
        )
        
        if created:
            # Mark as helpful
            rating.is_helpful = True
            rating.helpful_count += 1
            rating.save()
            is_helpful = True
            message = 'Rating marked as helpful!'
        else:
            # Remove helpful mark
            helpful_vote.delete()
            rating.is_helpful = False
            rating.helpful_count = max(0, rating.helpful_count - 1)
            rating.save()
            is_helpful = False
            message = 'Helpful mark removed.'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'is_helpful': is_helpful,
            'helpful_count': rating.helpful_count
        })
        
    except (PlaceRating.DoesNotExist, AgencyRating.DoesNotExist):
        return JsonResponse({'error': 'Rating not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@login_required
@require_POST
def delete_rating(request, rating_type, rating_id):
    """Delete a user's own rating"""
    try:
        if rating_type == 'place':
            rating = PlaceRating.objects.get(id=rating_id, user=request.user)
            redirect_url = reverse('public_place_detail', kwargs={'pk': rating.place.pk})
        elif rating_type == 'agency':
            rating = AgencyRating.objects.get(id=rating_id, user=request.user)
            redirect_url = reverse('public_agency_detail', kwargs={'pk': rating.agency.pk})
        else:
            return JsonResponse({'error': 'Invalid rating type'}, status=400)
        
        rating.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Rating deleted successfully!',
            'redirect_url': redirect_url
        })
        
    except (PlaceRating.DoesNotExist, AgencyRating.DoesNotExist):
        return JsonResponse({'error': 'Rating not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

class PlaceRatingListView(ListView):
    """Display all ratings for a specific place"""
    model = PlaceRating
    template_name = 'listings/place_ratings.html'
    context_object_name = 'ratings'
    paginate_by = 10
    
    def get_queryset(self):
        self.place = get_object_or_404(Place, pk=self.kwargs['place_id'])
        return PlaceRating.objects.filter(place=self.place).select_related('user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.place
        context['user_rating'] = self.place.get_user_rating(self.request.user) if self.request.user.is_authenticated else None
        return context

class AgencyRatingListView(ListView):
    """Display all ratings for a specific agency"""
    model = AgencyRating
    template_name = 'listings/agency_ratings.html'
    context_object_name = 'ratings'
    paginate_by = 10
    
    def get_queryset(self):
        self.agency = get_object_or_404(Agency, pk=self.kwargs['agency_id'])
        return AgencyRating.objects.filter(agency=self.agency).select_related('user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = self.agency
        context['user_rating'] = self.agency.get_user_rating(self.request.user) if self.request.user.is_authenticated else None
        return context

# Search and Discovery Views
from django.db.models import Q, Avg, Count, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

class AdvancedSearchView(View):
    """Advanced search view for places, tours, agencies, and events"""
    
    def get(self, request):
        form = AdvancedSearchForm(request.GET)
        results = {}
        total_results = 0
        
        if form.is_valid():
            results = self.perform_search(form.cleaned_data)
            total_results = sum(len(result_list) for result_list in results.values())
        
        # Pagination
        page = request.GET.get('page', 1)
        items_per_page = 12
        
        # Paginate each result type
        paginated_results = {}
        for result_type, result_list in results.items():
            paginator = Paginator(result_list, items_per_page)
            try:
                paginated_results[result_type] = paginator.page(page)
            except:
                paginated_results[result_type] = paginator.page(1)
        
        context = {
            'form': form,
            'results': paginated_results,
            'total_results': total_results,
            'search_performed': form.is_bound and form.is_valid(),
        }
        
        return render(request, 'listings/advanced_search.html', context)
    
    def perform_search(self, data):
        """Perform the actual search based on form data"""
        results = {
            'places': [],
            'tours': [],
            'agencies': [],
            'events': [],
        }
        
        search_type = data.get('search_type', 'all')
        query = data.get('query', '').strip()
        location = data.get('location', '').strip()
        
        # Search places
        if search_type in ['all', 'places']:
            results['places'] = self.search_places(data)
        
        # Search tours
        if search_type in ['all', 'tours']:
            results['tours'] = self.search_tours(data)
        
        # Search agencies
        if search_type in ['all', 'agencies']:
            results['agencies'] = self.search_agencies(data)
        
        # Search events
        if search_type in ['all', 'events']:
            results['events'] = self.search_events(data)
        
        return results
    
    def search_places(self, data):
        """Search places based on criteria"""
        queryset = Place.objects.filter(is_active=True)
        
        # Text search
        if data.get('query'):
            query = data['query']
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query) |
                Q(address__icontains=query)
            )
        
        # Location filter
        if data.get('location'):
            location = data['location']
            queryset = queryset.filter(
                Q(location__icontains=location) |
                Q(address__icontains=location)
            )
        
        # Category filter
        if data.get('place_category'):
            queryset = queryset.filter(category=data['place_category'])
        
        # Rating filter
        if data.get('min_rating'):
            min_rating = float(data['min_rating'])
            queryset = queryset.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=min_rating)
        
        # Additional filters
        if data.get('has_photos'):
            queryset = queryset.filter(gallery_images__isnull=False).distinct()
        
        # Sort results
        queryset = self.sort_places(queryset, data.get('sort_by', 'relevance'))
        
        return queryset.distinct()
    
    def search_tours(self, data):
        """Search tours based on criteria"""
        queryset = GroupTours.objects.filter(is_active=True)
        
        # Text search
        if data.get('query'):
            query = data['query']
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(itinerary__icontains=query)
            )
        
        # Location filter
        if data.get('location'):
            location = data['location']
            queryset = queryset.filter(
                Q(destination__location__icontains=location) |
                Q(destination__address__icontains=location)
            )
        
        # Price filters
        if data.get('min_price'):
            queryset = queryset.filter(price_per_person__gte=data['min_price'])
        if data.get('max_price'):
            queryset = queryset.filter(price_per_person__lte=data['max_price'])
        
        # Date filters
        if data.get('start_date'):
            queryset = queryset.filter(start_date__gte=data['start_date'])
        if data.get('end_date'):
            queryset = queryset.filter(end_date__lte=data['end_date'])
        
        # Rating filter
        if data.get('min_rating'):
            min_rating = float(data['min_rating'])
            queryset = queryset.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=min_rating)
        
        # Sort results
        queryset = self.sort_tours(queryset, data.get('sort_by', 'relevance'))
        
        return queryset.distinct()
    
    def search_agencies(self, data):
        """Search agencies based on criteria"""
        queryset = Agency.objects.filter(status='active')
        
        # Text search
        if data.get('query'):
            query = data['query']
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(city__icontains=query) |
                Q(country__icontains=query)
            )
        
        # Location filter
        if data.get('location'):
            location = data['location']
            queryset = queryset.filter(
                Q(city__icontains=location) |
                Q(country__icontains=location) |
                Q(address__icontains=location)
            )
        
        # Agency type filter
        if data.get('agency_type'):
            queryset = queryset.filter(agency_type=data['agency_type'])
        
        # Rating filter
        if data.get('min_rating'):
            min_rating = float(data['min_rating'])
            queryset = queryset.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=min_rating)
        
        # Verification filter
        if data.get('is_verified'):
            queryset = queryset.filter(license_number__isnull=False, registration_number__isnull=False)
        
        # Sort results
        queryset = self.sort_agencies(queryset, data.get('sort_by', 'relevance'))
        
        return queryset.distinct()
    
    def search_events(self, data):
        """Search events based on criteria"""
        queryset = Event.objects.filter(status=True)
        
        # Text search
        if data.get('query'):
            query = data['query']
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(itinerary__icontains=query)
            )
        
        # Price filters
        if data.get('min_price'):
            queryset = queryset.filter(price_per_person__gte=data['min_price'])
        if data.get('max_price'):
            queryset = queryset.filter(price_per_person__lte=data['max_price'])
        
        # Date filters
        if data.get('start_date'):
            queryset = queryset.filter(start_date__gte=data['start_date'])
        if data.get('end_date'):
            queryset = queryset.filter(end_date__lte=data['end_date'])
        
        # Sort results
        queryset = self.sort_events(queryset, data.get('sort_by', 'relevance'))
        
        return queryset.distinct()
    
    def sort_places(self, queryset, sort_by):
        """Sort places based on criteria"""
        if sort_by == 'rating':
            return queryset.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'popular':
            return queryset.annotate(rating_count=Count('ratings')).order_by('-rating_count')
        else:  # relevance
            return queryset.order_by('-created_at')
    
    def sort_tours(self, queryset, sort_by):
        """Sort tours based on criteria"""
        if sort_by == 'rating':
            return queryset.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
        elif sort_by == 'price_low':
            return queryset.order_by('price_per_person')
        elif sort_by == 'price_high':
            return queryset.order_by('-price_per_person')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'popular':
            return queryset.annotate(like_count=Count('likes')).order_by('-like_count')
        else:  # relevance
            return queryset.order_by('-created_at')
    
    def sort_agencies(self, queryset, sort_by):
        """Sort agencies based on criteria"""
        if sort_by == 'rating':
            return queryset.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'popular':
            return queryset.annotate(rating_count=Count('ratings')).order_by('-rating_count')
        else:  # relevance
            return queryset.order_by('-created_at')
    
    def sort_events(self, queryset, sort_by):
        """Sort events based on criteria"""
        if sort_by == 'price_low':
            return queryset.order_by('price_per_person')
        elif sort_by == 'price_high':
            return queryset.order_by('-price_per_person')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'popular':
            return queryset.annotate(like_count=Count('likes')).order_by('-like_count')
        else:  # relevance
            return queryset.order_by('-created_at')

class QuickSearchView(View):
    """Quick search view for simple text-based search"""
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        search_type = request.GET.get('type', 'all')
        
        if not query:
            return redirect('advanced_search')
        
        # Perform quick search
        results = self.quick_search(query, search_type)
        
        context = {
            'query': query,
            'search_type': search_type,
            'results': results,
            'total_results': sum(len(result_list) for result_list in results.values()),
        }
        
        return render(request, 'listings/quick_search_results.html', context)
    
    def quick_search(self, query, search_type):
        """Perform quick search across all types"""
        results = {
            'places': [],
            'tours': [],
            'agencies': [],
            'events': [],
        }
        
        if search_type in ['all', 'places']:
            results['places'] = Place.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query),
                is_active=True
            )[:5]
        
        if search_type in ['all', 'tours']:
            results['tours'] = GroupTours.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query),
                is_active=True
            )[:5]
        
        if search_type in ['all', 'agencies']:
            results['agencies'] = Agency.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(city__icontains=query),
                status='active'
            )[:5]
        
        if search_type in ['all', 'events']:
            results['events'] = Event.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query),
                status=True
            )[:5]
        
        return results

class TrendingView(View):
    """View for trending/popular destinations and tours"""
    
    def get(self, request):
        # Get trending places (most rated in last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        trending_places = Place.objects.filter(
            ratings__created_at__gte=thirty_days_ago,
            is_active=True
        ).annotate(
            recent_rating_count=Count('ratings'),
            avg_rating=Avg('ratings__rating')
        ).filter(
            recent_rating_count__gte=1
        ).order_by('-recent_rating_count', '-avg_rating')[:6]
        
        # Get popular tours (most liked/bookmarked)
        popular_tours = GroupTours.objects.filter(
            is_active=True
        ).annotate(
            like_count=Count('likes'),
            bookmark_count=Count('bookmarks'),
            total_engagement=F('like_count') + F('bookmark_count')
        ).filter(
            total_engagement__gte=1
        ).order_by('-total_engagement')[:6]
        
        # Get top-rated agencies
        top_agencies = Agency.objects.filter(
            status='active'
        ).annotate(
            avg_rating=Avg('ratings__rating'),
            rating_count=Count('ratings')
        ).filter(
            rating_count__gte=3
        ).order_by('-avg_rating', '-rating_count')[:6]
        
        context = {
            'trending_places': trending_places,
            'popular_tours': popular_tours,
            'top_agencies': top_agencies,
        }
        
        return render(request, 'listings/trending.html', context)

class RecommendationView(View):
    """View for personalized recommendations"""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user = request.user
        
        # Get user's preferences based on their activity
        user_ratings = PlaceRating.objects.filter(user=user).values_list('place__category', flat=True)
        user_liked_tours = user.liked_tours.values_list('destination__category', flat=True)
        
        # Combine preferences
        preferred_categories = list(user_ratings) + list(user_liked_tours)
        
        # Get recommendations based on preferences
        recommended_places = []
        if preferred_categories:
            recommended_places = Place.objects.filter(
                category__in=preferred_categories,
                is_active=True
            ).exclude(
                ratings__user=user  # Exclude already rated places
            ).annotate(
                avg_rating=Avg('ratings__rating')
            ).order_by('-avg_rating')[:6]
        
        # Get tours similar to user's interests
        recommended_tours = []
        if preferred_categories:
            recommended_tours = GroupTours.objects.filter(
                destination__category__in=preferred_categories,
                is_active=True
            ).exclude(
                likes=user  # Exclude already liked tours
            ).annotate(
                like_count=Count('likes')
            ).order_by('-like_count')[:6]
        
        # Get agencies in user's preferred locations
        user_locations = PlaceRating.objects.filter(user=user).values_list('place__location', flat=True)
        recommended_agencies = []
        if user_locations:
            recommended_agencies = Agency.objects.filter(
                Q(city__in=user_locations) | Q(country__in=user_locations),
                status='active'
            ).exclude(
                ratings__user=user  # Exclude already rated agencies
            ).annotate(
                avg_rating=Avg('ratings__rating')
            ).order_by('-avg_rating')[:6]
        
        context = {
            'recommended_places': recommended_places,
            'recommended_tours': recommended_tours,
            'recommended_agencies': recommended_agencies,
        }
        
        return render(request, 'listings/recommendations.html', context)


# Agency Service Views
class AgencyServiceListView(ListView):
    """List all services for a specific agency"""
    model = AgencyService
    template_name = 'listings/agency_services_list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        agency_id = self.kwargs.get('agency_id')
        if agency_id:
            return AgencyService.objects.filter(
                agency_id=agency_id,
                is_active=True
            ).select_related('agency')
        return AgencyService.objects.filter(is_active=True).select_related('agency')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agency_id = self.kwargs.get('agency_id')
        if agency_id:
            context['agency'] = get_object_or_404(Agency, id=agency_id)
        return context


class AgencyServiceDetailView(DetailView):
    """Detail view for a specific agency service"""
    model = AgencyService
    template_name = 'listings/agency_service_detail.html'
    context_object_name = 'service'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = self.object.agency
        return context


class AgencyServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new service for an agency"""
    model = AgencyService
    form_class = AgencyServiceForm
    template_name = 'listings/agency_service_form.html'
    
    def test_func(self):
        """Check if user owns the agency"""
        agency_id = self.kwargs.get('agency_id')
        if agency_id:
            agency = get_object_or_404(Agency, id=agency_id)
            return agency.owner == self.request.user
        return False
    
    def form_valid(self, form):
        form.instance.agency_id = self.kwargs.get('agency_id')
        messages.success(self.request, 'Service created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('agency_service_list', kwargs={'agency_id': self.kwargs.get('agency_id')})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = get_object_or_404(Agency, id=self.kwargs.get('agency_id'))
        context['action'] = 'Create'
        return context


class AgencyServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing agency service"""
    model = AgencyService
    form_class = AgencyServiceForm
    template_name = 'listings/agency_service_form.html'
    
    def test_func(self):
        """Check if user owns the agency"""
        return self.get_object().agency.owner == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Service updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('agency_service_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = self.object.agency
        context['action'] = 'Update'
        return context


class AgencyServiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an agency service"""
    model = AgencyService
    template_name = 'listings/agency_service_confirm_delete.html'
    
    def test_func(self):
        """Check if user owns the agency"""
        return self.get_object().agency.owner == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('agency_service_list', kwargs={'agency_id': self.object.agency.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = self.object.agency
        return context


@login_required
def agency_service_toggle_featured(request, pk):
    """Toggle featured status of an agency service"""
    service = get_object_or_404(AgencyService, pk=pk)
    
    # Check if user owns the agency
    if service.agency.owner != request.user:
        messages.error(request, 'You do not have permission to modify this service.')
        return redirect('agency_service_detail', pk=pk)
    
    service.is_featured = not service.is_featured
    service.save()
    
    status = "featured" if service.is_featured else "unfeatured"
    messages.success(request, f'Service {status} successfully!')
    
    return redirect('agency_service_detail', pk=pk)


@login_required
def agency_service_toggle_active(request, pk):
    """Toggle active status of an agency service"""
    service = get_object_or_404(AgencyService, pk=pk)
    
    # Check if user owns the agency
    if service.agency.owner != request.user:
        messages.error(request, 'You do not have permission to modify this service.')
        return redirect('agency_service_detail', pk=pk)
    
    service.is_active = not service.is_active
    service.save()
    
    status = "activated" if service.is_active else "unfeatured"
    messages.success(request, f'Service {status} successfully!')
    
    return redirect('agency_service_detail', pk=pk)


class TourBookingWithPaymentView(LoginRequiredMixin, View):
    """Tour booking view with payment integration"""
    template_name = 'listings/tour_booking_payment.html'
    
    def get(self, request, pk):
        try:
            tour = GroupTours.objects.get(pk=pk)
            
            # Check if tour is available for booking
            if tour.is_full:
                messages.error(request, 'This tour is already full and cannot accept new bookings.')
                return redirect('public_grouptours_detail', pk=pk)
            
            if tour.status not in ['planning', 'active']:
                messages.error(request, 'This tour is not currently accepting bookings.')
                return redirect('public_grouptours_detail', pk=pk)
            
            # Check if user has already booked this tour
            existing_booking = TourBooking.objects.filter(
                tour=tour, 
                user=request.user, 
                status__in=['pending', 'confirmed']
            ).first()
            
            if existing_booking:
                messages.warning(request, 'You have already booked this tour.')
                return redirect('user_bookings')
            
            # Get available payment methods
            payment_methods = PaymentMethod.objects.filter(is_active=True)
            
            # Get user's phone number from profile if available
            user_phone = request.user.phone if hasattr(request.user, 'phone') else ''
            
            context = {
                'tour': tour,
                'payment_methods': payment_methods,
                'user_phone': user_phone,
                'available_spots': tour.available_spots,
            }
            
            return render(request, self.template_name, context)
            
        except GroupTours.DoesNotExist:
            messages.error(request, 'Tour not found.')
            return redirect('grouptours_list')
    
    def post(self, request, pk):
        print(f"🔍 DEBUG: TourBookingWithPaymentView.post called for tour {pk}")
        print(f"📋 DEBUG: POST data: {request.POST}")
        try:
            tour = GroupTours.objects.get(pk=pk)
            print(f"🎯 DEBUG: Found tour: {tour.name}")
            
            # Get form data
            participants = int(request.POST.get('participants', 1))
            special_requests = request.POST.get('special_requests', '')
            payment_method_id = request.POST.get('payment_method')
            phone_number = request.POST.get('phone_number', '')
            
            print(f"📋 DEBUG: Form data - participants: {participants}, payment_method: {payment_method_id}, phone: {phone_number}")
            
            # Validate participants
            if participants < 1 or participants > tour.available_spots:
                messages.error(request, 'Invalid number of participants.')
                return redirect('tour_booking_payment', pk=pk)
            
            # Calculate total amount
            total_amount = tour.price_per_person * participants
            
            # Get payment method
            try:
                payment_method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
            except PaymentMethod.DoesNotExist:
                messages.error(request, 'Invalid payment method selected.')
                return redirect('tour_booking_payment', pk=pk)
            
            # Create the booking
            booking = TourBooking.objects.create(
                tour=tour,
                user=request.user,
                participants=participants,
                special_requests=special_requests,
                total_amount=total_amount,
                status='pending'
            )
            
            # Process payment based on method
            if payment_method.payment_type == 'mpesa':
                return self._process_mpesa_payment(request, booking, phone_number, total_amount)
            elif payment_method.payment_type == 'card':
                # Redirect to card payment page or process card payment
                messages.info(request, 'Card payment will be processed separately.')
                return redirect('user_bookings')
            else:
                # Other payment methods (cash, bank transfer)
                messages.success(request, f'Booking created successfully! Please complete payment via {payment_method.name}.')
                return redirect('user_bookings')
                
        except GroupTours.DoesNotExist:
            messages.error(request, 'Tour not found.')
            return redirect('grouptours_list')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('tour_booking_payment', pk=pk)
    
    def _process_mpesa_payment(self, request, booking, phone_number, total_amount):
        """Process M-Pesa payment for the booking using working implementation from tests.py"""
        print(f"💰 DEBUG: _process_mpesa_payment called for booking {booking.id}, phone: {phone_number}, amount: {total_amount}")
        try:
            if not phone_number or phone_number.strip() == '':
                print("❌ DEBUG: No phone number provided")
                messages.error(request, 'Phone number is required for M-Pesa payment.')
                return redirect('tour_booking_payment', pk=booking.tour.pk)
            
            # Use the working implementation from tests.py
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
                settings = PaymentSettings.get_settings()
                consumer_key = settings.mpesa_consumer_key
                consumer_secret = settings.mpesa_consumer_secret
                passkey = settings.mpesa_passkey
                business_shortcode = settings.mpesa_business_shortcode
                callback_url = settings.mpesa_callback_url
                print(f"🔑 DEBUG: Using credentials from database - shortcode: {business_shortcode}")
            except Exception as e:
                print(f"❌ DEBUG: Failed to get payment settings: {e}")
                messages.error(request, 'Payment settings not configured.')
                return redirect('tour_booking_payment', pk=booking.tour.pk)
            
            # Generate timestamp and password (working approach from tests.py)
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
                messages.error(request, 'Failed to authenticate with M-Pesa.')
                return redirect('tour_booking_payment', pk=booking.tour.pk)
            
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
                "Amount": int(total_amount),
                "PartyA": phone,
                "PartyB": int(business_shortcode),
                "PhoneNumber": phone,
                "CallBackURL": callback_url,
                "AccountReference": str(booking.id),
                "TransactionDesc": f"Payment for {booking.tour.name} tour",
            }
            
            print(f"📦 DEBUG: STK push payload prepared")
            print(f"   Amount: KES {total_amount}")
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
                
                # Update booking with payment details
                booking.payment_reference = f"MPESA_{booking.id}_{timestamp}"
                booking.payment_method = 'mpesa'
                booking.payment_status = 'processing'
                booking.status = 'payment_pending'
                booking.save()
                
                messages.success(request, 'M-Pesa payment initiated! Please check your phone for the STK push notification.')
                return redirect('payment_status', transaction_id=booking.payment_reference)
            else:
                # Payment initiation failed
                print(f"❌ DEBUG: STK push failed with status {response.status_code}")
                messages.error(request, f'M-Pesa payment failed: {response.text}')
                # Delete the failed booking
                booking.delete()
                return redirect('tour_booking_payment', pk=booking.tour.pk)
                
        except Exception as e:
            messages.error(request, f'Error processing M-Pesa payment: {str(e)}')
            # Delete the failed booking
            booking.delete()
            return redirect('tour_booking_payment', pk=booking.tour.pk)


class PaymentStatusView(LoginRequiredMixin, View):
    """View to show payment status and instructions"""
    template_name = 'listings/payment_status.html'
    
    def get(self, request, transaction_id):
        try:
            transaction = PaymentTransaction.objects.get(
                transaction_id=transaction_id,
                user=request.user
            )
            
            # Get M-Pesa payment details if available
            try:
                mpesa_payment = MPesaPayment.objects.get(transaction=transaction)
            except MPesaPayment.DoesNotExist:
                mpesa_payment = None
            
            context = {
                'transaction': transaction,
                'mpesa_payment': mpesa_payment,
                'tour': None,
            }
            
            # Get tour details if this is a tour booking
            if transaction.content_type == 'mpesa_payment':
                try:
                    booking = TourBooking.objects.get(id=transaction.object_id)
                    context['tour'] = booking.tour
                except TourBooking.DoesNotExist:
                    pass
            
            return render(request, self.template_name, context)
            
        except PaymentTransaction.DoesNotExist:
            messages.error(request, 'Payment transaction not found.')
            return redirect('user_bookings')

class EventBookingWithPaymentView(LoginRequiredMixin, View):
    """Event booking view with payment integration"""
    template_name = 'listings/event_booking_payment.html'
    
    def get(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
            
            # Check if event is available for booking
            if event.status not in ['active', 'upcoming']:
                messages.error(request, 'This event is not currently accepting bookings.')
                return redirect('public_event_detail', pk=pk)
            
            # Check if user has already booked this event
            existing_booking = EventBooking.objects.filter(
                event=event, 
                user=request.user, 
                status__in=['pending', 'confirmed']
            ).first()
            
            if existing_booking:
                messages.warning(request, 'You have already booked this event.')
                return redirect('user_bookings')
            
            # Get available payment methods
            payment_methods = PaymentMethod.objects.filter(is_active=True)
            
            # Get user's phone number from profile if available
            user_phone = request.user.phone if hasattr(request.user, 'phone') else ''
            
            context = {
                'event': event,
                'payment_methods': payment_methods,
                'user_phone': user_phone,
            }
            
            return render(request, self.template_name, context)
            
        except Event.DoesNotExist:
            messages.error(request, 'Event not found.')
            return redirect('event_list')
    
    def post(self, request, pk):
        print(f"🔍 DEBUG: EventBookingWithPaymentView.post called for event {pk}")
        print(f"📋 DEBUG: POST data: {request.POST}")
        try:
            event = Event.objects.get(pk=pk)
            print(f"🎯 DEBUG: Found event: {event.name}")
            
            # Get form data
            participants = int(request.POST.get('participants', 1))
            special_requests = request.POST.get('special_requests', '')
            payment_method = request.POST.get('payment_method', 'mpesa')
            phone = request.POST.get('phone', '').strip()
            
            # Validate phone number
            if not phone:
                messages.error(request, 'Phone number is required for booking.')
                return redirect('simple_event_booking', pk=pk)
            
            # Calculate total amount
            total_amount = event.price_per_person * participants if event.price_per_person else 0
            
            # Get user info based on authentication status
            if request.user.is_authenticated:
                name = request.user.get_full_name() or request.user.username
                email = request.user.email
                
                # Create booking record
                booking = EventBooking.objects.create(
                    event=event,
                    user=request.user,
                    participants=participants,
                    special_requests=special_requests,
                    total_amount=total_amount,
                    status='pending'
                )
                
                # Handle payment method
                if payment_method == 'mpesa':
                    # Initiate M-Pesa STK push
                    print(f"🔍 DEBUG: Initiating M-Pesa payment for phone: {phone}, user: {name}, amount: {total_amount}")
                    response, error = initiate_mpesa_payment(phone, name, total_amount)
                    
                    if response and response.status_code == 200:
                        response_data = response.json()
                        print(f"🔍 DEBUG: M-Pesa response: {response_data}")
                        if response_data.get('ResponseCode') == '0':
                            # STK push successful
                            checkout_request_id = response_data.get('CheckoutRequestID')
                            messages.success(request, f'✅ Booking created! M-Pesa STK push sent to {phone}. Please check your phone and enter M-Pesa PIN to complete payment.')
                            
                            # Store checkout request ID for tracking
                            booking.payment_reference = checkout_request_id
                            booking.payment_method = 'mpesa'
                            booking.save()
                        else:
                            messages.warning(request, f'⚠️ Booking created but M-Pesa STK push failed: {response_data.get("ResponseDescription", "Unknown error")}')
                    else:
                        print(f"🔍 DEBUG: M-Pesa error: {error}")
                        messages.warning(request, f'⚠️ Booking created but M-Pesa STK push failed: {error or "Network error"}')
                elif payment_method == 'card':
                    booking.payment_method = 'card'
                    booking.save()
                    messages.success(request, f'✅ Booking created successfully! Your booking ID is {booking.id}. Please complete card payment.')
                else:
                    messages.success(request, f'✅ Booking created successfully! Your booking ID is {booking.id}.')
                    
            else:
                # For unauthenticated users, get form data
                name = request.POST.get('name', '')
                email = request.POST.get('email', '')
                
                # Create a temporary booking record or just show success message
                messages.success(request, f'✅ Booking request received for {participants} participant(s)! Please log in to complete your booking.')
            
            return redirect('public_event_detail', pk=pk)
            
        except Event.DoesNotExist:
            messages.error(request, 'Event not found.')
            return redirect('event_list')
        except Exception as e:
            messages.error(request, f'❌ An error occurred: {str(e)}')
            return redirect('public_event_detail', pk=pk)
    
    def _process_mpesa_payment(self, request, booking, phone_number, total_amount):
        """Process M-Pesa payment for the event booking using working implementation from tests.py"""
        print(f"💰 DEBUG: _process_mpesa_payment called for event booking {booking.id}, phone: {phone_number}, amount: {total_amount}")
        try:
            if not phone_number or phone_number.strip() == '':
                print("❌ DEBUG: No phone number provided")
                messages.error(request, 'Phone number is required for M-Pesa payment.')
                return redirect('event_booking_payment', pk=booking.event.pk)
            
            # Use the working implementation from tests.py
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
                settings = PaymentSettings.get_settings()
                consumer_key = settings.mpesa_consumer_key
                consumer_secret = settings.mpesa_consumer_secret
                passkey = settings.mpesa_passkey
                business_shortcode = settings.mpesa_business_shortcode
                callback_url = settings.mpesa_callback_url
                print(f"🔑 DEBUG: Using credentials from database - shortcode: {business_shortcode}")
            except Exception as e:
                print(f"❌ DEBUG: Failed to get payment settings: {e}")
                messages.error(request, 'Payment settings not configured.')
                return redirect('event_booking_payment', pk=booking.event.pk)
            
            # Generate timestamp and password (working approach from tests.py)
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
                messages.error(request, 'Failed to authenticate with M-Pesa.')
                return redirect('event_booking_payment', pk=booking.event.pk)
            
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
                "Amount": int(total_amount),
                "PartyA": phone,
                "PartyB": int(business_shortcode),
                "PhoneNumber": phone,
                "CallBackURL": callback_url,
                "AccountReference": str(booking.id),
                "TransactionDesc": f"Payment for {booking.event.name} event",
            }
            
            print(f"📦 DEBUG: STK push payload prepared")
            print(f"   Amount: KES {total_amount}")
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
                
                # Update booking with payment details
                booking.payment_reference = f"MPESA_{booking.id}_{timestamp}"
                booking.payment_method = 'mpesa'
                booking.payment_status = 'processing'
                booking.status = 'payment_pending'
                booking.save()
                
                messages.success(request, 'M-Pesa payment initiated! Please check your phone for the STK push notification.')
                return redirect('payment_status', transaction_id=booking.payment_reference)
            else:
                # Payment initiation failed
                print(f"❌ DEBUG: STK push failed with status {response.status_code}")
                messages.error(request, f'M-Pesa payment failed: {response.text}')
                # Delete the failed booking
                booking.delete()
                return redirect('event_booking_payment', pk=booking.event.pk)
                
        except Exception as e:
            print(f"❌ DEBUG: Exception in _process_mpesa_payment: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error processing M-Pesa payment: {str(e)}')
            # Delete the failed booking
            booking.delete()
            return redirect('event_booking_payment', pk=booking.event.pk)


class MPesaWebhookView(View):
    """Handle M-Pesa payment callbacks and update booking status"""
    
    def post(self, request):
        print(f"📞 DEBUG: M-Pesa webhook received: {request.body}")
        
        try:
            # Parse the callback data
            callback_data = json.loads(request.body)
            print(f"📋 DEBUG: Parsed callback data: {callback_data}")
            
            # Initialize M-Pesa service
            mpesa_service = MPesaService()
            
            # Process the callback
            success = mpesa_service.process_callback(callback_data)
            
            if success:
                print("✅ DEBUG: M-Pesa callback processed successfully")
                return JsonResponse({'status': 'success'}, status=200)
            else:
                print("❌ DEBUG: M-Pesa callback processing failed")
                return JsonResponse({'status': 'failed'}, status=400)
                
        except json.JSONDecodeError as e:
            print(f"❌ DEBUG: Invalid JSON in webhook: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"❌ DEBUG: Error processing webhook: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    def get(self, request):
        """Handle GET requests (for testing)"""
        return JsonResponse({'status': 'webhook_endpoint_active'}, status=200)

def generate_access_token():
    """Generate M-Pesa access token"""
    access_token_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    consumer_key = "aSG8gGG7GWSGapToKz8ySyALUx9zIdbBr1CHldVhyOLjJsCz"
    consumer_secret = "o8qwdbzapgcvOd1lsBOkKGCL4JwMQyG9ZmKlKC7uaLIc4FsRJFbzfV10EAoL0P6u"

    response = requests.get(access_token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    
    if response.status_code == 200:
        access_token = response.json()['access_token']        
        return access_token
    else:
        return None

def process_phone_number(input_str):
    """Process phone number to M-Pesa format"""
    if input_str.startswith('0'):
        return '254' + input_str[1:]
    elif input_str.startswith('254'):
        return input_str
    else:
        return input_str

def initiate_mpesa_payment(phone, user, total):
    """Initiate M-Pesa STK push"""
    phone = process_phone_number(phone)
    paybill = "4161900"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    consumer_key = 'fa0e41448ce844d1a7a37553cee8bf22b61fec894e1ce3e9c0e32b1c6953b6d9'
    concatenated_string = f"{paybill}{consumer_key}{timestamp}"
    base64_encoded = base64.b64encode(concatenated_string.encode()).decode('utf-8')
    password = str(base64_encoded)
    
    access_token = generate_access_token()
    if not access_token:
        return None, "Failed to generate access token"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "BusinessShortCode": 4161900,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(total),
        "PartyA": phone,
        "PartyB": 4161900,
        "PhoneNumber": phone,
        "CallBackURL": "https://knowedge.online/Subscription/callback/",
        "AccountReference": user,
        "TransactionDesc": "Event Booking",
    }

    try:
        response = requests.post('https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest', 
                               headers=headers, json=payload)
        return response, None
    except Exception as e:
        return None, str(e)

def test_mpesa_connection():
    """Test M-Pesa API connection"""
    try:
        consumer_key = "fa0e41448ce844d1a7a37553cee8bf22b61fec894e1ce3e9c0e32b1c6953b6d9"
        consumer_secret = "o8qwdbzapgcvOd1lsBOkKGCL4JwMQyG9ZmKlKC7uaLIc4FsRJFbzfV10EAoL0P6u"
        
        auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth_response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret), timeout=10)
        
        print(f"🔍 M-Pesa Auth Test: Status {auth_response.status_code}")
        if auth_response.status_code == 200:
            token = auth_response.json().get('access_token')
            print(f"✅ Access token received: {token[:20]}..." if token else "❌ No token in response")
            return True
        else:
            print(f"❌ Auth failed: {auth_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ M-Pesa test error: {str(e)}")
        return False

def simple_mpesa_stk_push(phone_number, amount, reference):
    """Simple M-Pesa STK push that actually works"""
    try:
        # M-Pesa API credentials
        consumer_key = "fa0e41448ce844d1a7a37553cee8bf22b61fec894e1ce3e9c0e32b1c6953b6d9"
        consumer_secret = "o8qwdbzapgcvOd1lsBOkKGCL4JwMQyG9ZmKlKC7uaLIc4FsRJFbzfV10EAoL0P6u"
        
        # Generate access token
        auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth_response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        
        if auth_response.status_code != 200:
            return False, "Failed to get access token"
        
        access_token = auth_response.json().get('access_token')
        if not access_token:
            return False, "No access token received"
        
        # Process phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        # Generate password
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        business_shortcode = "4161900"
        password_string = f"{business_shortcode}{consumer_key}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        
        # STK Push payload
        stk_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": business_shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": "https://knowedge.online/Subscription/callback/",
            "AccountReference": reference,
            "TransactionDesc": "Event Booking"
        }
        
        # Send STK push request
        response = requests.post(stk_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('ResponseCode') == '0':
                return True, response_data.get('CheckoutRequestID', '')
            else:
                return False, response_data.get('ResponseDescription', 'STK push failed')
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

class SimpleEventBookingView(View):
    """Simple event booking view with working M-Pesa integration"""
    template_name = 'listings/simple_event_booking.html'
    
    def get(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
            context = {
                'event': event,
            }
            return render(request, self.template_name, context)
        except Event.DoesNotExist:
            messages.error(request, 'Event not found.')
            return redirect('event_list')
    
    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
            
            # Get form data
            participants = int(request.POST.get('participants', 1))
            special_requests = request.POST.get('special_requests', '')
            payment_method = request.POST.get('payment_method', 'mpesa')
            phone = request.POST.get('phone', '').strip()
            
            # Validate phone number
            if not phone:
                messages.error(request, 'Phone number is required for booking.')
                return redirect('simple_event_booking', pk=pk)
            
            # Calculate total amount
            total_amount = event.price_per_person * participants if event.price_per_person else 0
            
            # Get user info based on authentication status
            if request.user.is_authenticated:
                name = request.user.get_full_name() or request.user.username
                email = request.user.email
                
                # Create booking record
                booking = EventBooking.objects.create(
                    event=event,
                    user=request.user,
                    participants=participants,
                    special_requests=special_requests,
                    total_amount=total_amount,
                    status='pending'
                )
                
                # Handle payment method
                if payment_method == 'mpesa':
                    # Use the same working M-Pesa implementation from tour booking
                    return self._process_mpesa_payment(request, booking, phone, total_amount)
                        
                elif payment_method == 'card':
                    booking.payment_method = 'card'
                    booking.save()
                    messages.success(request, f'✅ Booking created successfully! Your booking ID is {booking.id}. Please complete card payment.')
                else:
                    messages.success(request, f'✅ Booking created successfully! Your booking ID is {booking.id}.')
                    
            else:
                # For unauthenticated users, get form data
                name = request.POST.get('name', '')
                email = request.POST.get('email', '')
                
                # Create a temporary booking record or just show success message
                messages.success(request, f'✅ Booking request received for {participants} participant(s)! Please log in to complete your booking.')
            
            return redirect('public_event_detail', pk=pk)
            
        except Event.DoesNotExist:
            messages.error(request, 'Event not found.')
            return redirect('event_list')
        except Exception as e:
            messages.error(request, f'❌ An error occurred: {str(e)}')
            print(f"❌ ERROR in booking: {str(e)}")
            return redirect('public_event_detail', pk=pk)
    
    def _process_mpesa_payment(self, request, booking, phone_number, total_amount):
        """Process M-Pesa payment for the event booking using working implementation from tour booking"""
        print(f"💰 DEBUG: _process_mpesa_payment called for event booking {booking.id}, phone: {phone_number}, amount: {total_amount}")
        try:
            if not phone_number or phone_number.strip() == '':
                print("❌ DEBUG: No phone number provided")
                messages.error(request, 'Phone number is required for M-Pesa payment.')
                return redirect('simple_event_booking', pk=booking.event.pk)
            
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
                from core.models import PaymentSettings
                settings = PaymentSettings.get_settings()
                consumer_key = settings.mpesa_consumer_key
                consumer_secret = settings.mpesa_consumer_secret
                passkey = settings.mpesa_passkey
                business_shortcode = settings.mpesa_business_shortcode
                callback_url = settings.mpesa_callback_url
                print(f"🔑 DEBUG: Using credentials from database - shortcode: {business_shortcode}")
            except Exception as e:
                print(f"❌ DEBUG: Failed to get payment settings: {e}")
                messages.error(request, 'Payment settings not configured.')
                return redirect('simple_event_booking', pk=booking.event.pk)
            
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
                messages.error(request, 'Failed to authenticate with M-Pesa.')
                return redirect('simple_event_booking', pk=booking.event.pk)
            
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
                "Amount": int(total_amount),
                "PartyA": phone,
                "PartyB": int(business_shortcode),
                "PhoneNumber": phone,
                "CallBackURL": callback_url,
                "AccountReference": str(booking.id),
                "TransactionDesc": f"Payment for {booking.event.name} event",
            }
            
            print(f"📦 DEBUG: STK push payload prepared")
            print(f"   Amount: KES {total_amount}")
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
                
                # Update booking with payment details
                booking.payment_reference = f"MPESA_{booking.id}_{timestamp}"
                booking.payment_method = 'mpesa'
                booking.payment_status = 'processing'
                booking.status = 'pending'
                booking.save()
                
                messages.success(request, f'✅ Booking created! M-Pesa STK push sent to {phone}. Please check your phone and enter M-Pesa PIN to complete payment.')
                return redirect('public_event_detail', pk=booking.event.pk)
            else:
                print(f"❌ DEBUG: STK push failed with status {response.status_code}")
                messages.warning(request, f'⚠️ Booking created but M-Pesa STK push failed. Please try again or contact support.')
                return redirect('public_event_detail', pk=booking.event.pk)
                
        except Exception as e:
            print(f"❌ DEBUG: Error in M-Pesa payment: {str(e)}")
            messages.error(request, f'❌ Error processing M-Pesa payment: {str(e)}')
            return redirect('public_event_detail', pk=booking.event.pk)
