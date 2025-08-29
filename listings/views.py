from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django import forms
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, TemplateView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q, Avg, Count, Case, When, Value, F, IntegerField
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.core.mail import send_mail
import logging

# Local imports
from .models import (
    Place, PlaceCategory, TourBooking, EventBooking, TravelGroup, GroupTours, 
    Agency, AgencyService, TourComment, TourBookingPayment, Event, EventComment, 
    MenuCategory, MenuItem, Features, PlaceRating, AgencyRating, RatingHelpful,
    PlaceGallery, AgencyGallery, DatePlan, DateActivity, DatePlanPreference, DatePlanSuggestion,
    PlaceStaff, PlaceOrder, PlaceOrderItem
)
from .forms import (
    MenuCategoryForm, MenuItemForm, TourCommentForm, EventCommentForm, 
    TourBookingForm, EventBookingForm, EnhancedTourBookingForm, PlaceRatingForm, 
    AgencyRatingForm, GroupToursForm, TourVideoUploadForm, AgencyServiceForm, AdvancedSearchForm, FeatureForm,
    PlaceGalleryForm, AgencyGalleryForm, PlaceSearchForm, AgencySearchForm,
    DatePlanForm, DateActivityForm, DatePlanPreferenceForm, DatePlanSuggestionForm,
    PlaceStaffForm, PlaceOrderForm
)
from users.models import MyUser
from core.models import PaymentMethod, PaymentTransaction, MPesaPayment, PaymentSettings
from core.mpesa_service import MPesaService

# Third-party imports
import json
import base64
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, date
from decimal import Decimal
import uuid

# AI imports (optional) - will be imported lazily when needed
OPENAI_AVAILABLE = False

# Custom form for intro video upload
class PlaceIntroVideoForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ['place_intro_video']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['place_intro_video'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition duration-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100',
            'accept': 'video/*',
        })
        self.fields['place_intro_video'].required = False
        self.fields['place_intro_video'].help_text = "Upload a short video introducing your place (MP4, MOV, AVI - max 100MB)"

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
    place_intro_video = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100',
            'accept': 'video/*',
        }),
        help_text="Upload a short video introducing your place (MP4, MOV, AVI - max 100MB)"
    )

# Step 3: Settings & Confirmation
class PlaceSettingsForm(forms.Form):
    is_active = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded',
        })
    )

import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files import File

class PlaceCreateWizard(LoginRequiredMixin, View):
    FORMS = [PlaceBasicForm, PlaceContactForm, PlaceSettingsForm]
    TEMPLATES = [
        'listings/place_create_step1.html',
        'listings/place_create_step2.html',
        'listings/place_create_step3.html',
    ]

    def get(self, request, step=1):
        step = int(step)
        if step > 3:
            step = 3
        form = self.FORMS[step-1](initial=request.session.get(f'place_step_{step}', {}))
        progress_data = self.get_progress_data(request, step)
        return render(request, self.TEMPLATES[step-1], {
            'form': form,
            'step': step,
            'progress_data': progress_data,
            'total_steps': 3
        })

    def post(self, request, step=1):
        step = int(step)
        if step > 3:
            step = 3

        form = self.FORMS[step-1](request.POST, request.FILES)

        if form.is_valid():
            step_data = form.cleaned_data.copy()

            # ✅ Save uploaded file temporarily
            if 'profile_picture' in request.FILES:
                uploaded_file = request.FILES['profile_picture']
                path = default_storage.save(
                    f"temp_uploads/{uploaded_file.name}",
                    ContentFile(uploaded_file.read())
                )
                step_data['profile_picture'] = path  # save file path, not file object

            if 'category' in step_data and hasattr(step_data['category'], 'id'):
                step_data['category'] = step_data['category'].id

            request.session[f'place_step_{step}'] = step_data

            if step == 3:
                return self.create_place(request)
            else:
                return redirect(reverse('place_create_step', kwargs={'step': step+1}))

        progress_data = self.get_progress_data(request, step)
        return render(request, self.TEMPLATES[step-1], {
            'form': form,
            'step': step,
            'progress_data': progress_data,
            'total_steps': 3
        })

    def get_progress_data(self, request, current_step):
        data = {}
        for i in range(1, current_step + 1):
            step_data = request.session.get(f'place_step_{i}', {})
            data.update(step_data)
        return data

    def create_place(self, request):
        try:
            data = {}
            for i in range(1, 4):
                step_data = request.session.get(f'place_step_{i}', {})
                data.update(step_data)

            profile_picture_path = data.get('profile_picture')
            final_profile_picture = None

            # ✅ Move file from temp to permanent location
            if profile_picture_path and default_storage.exists(profile_picture_path):
                with default_storage.open(profile_picture_path, 'rb') as f:
                    file_name = os.path.basename(profile_picture_path)
                    final_path = default_storage.save(f"places/{file_name}", File(f))
                    final_profile_picture = final_path

                # delete temp file
                default_storage.delete(profile_picture_path)

            place = Place.objects.create(
                name=data['name'],
                description=data['description'],
                category=PlaceCategory.objects.get(id=data['category']),
                location=data['location'],
                address=data.get('address', ''),
                website=data.get('website', ''),
                contact_email=data.get('contact_email', ''),
                contact_phone=data.get('contact_phone', ''),
                profile_picture=final_profile_picture,  # now permanent path
                place_intro_video=data.get('place_intro_video'),
                is_active=data.get('is_active', True),
                created_by=request.user
            )

            # Clear session data
            for i in range(1, 4):
                if f'place_step_{i}' in request.session:
                    del request.session[f'place_step_{i}']

            return redirect('place_create_success')

        except Exception as e:
            return render(request, self.TEMPLATES[2], {
                'form': self.FORMS[2](),
                'step': 3,
                'error': f'An error occurred while creating your place: {e}',
                'progress_data': self.get_progress_data(request, 3),
                'total_steps': 3
            })

    def get_success_url(self):
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
    fields = ['name', 'description', 'category', 'location', 'address', 'website', 'contact_email', 'contact_phone', 'profile_picture', 'place_intro_video', 'is_active']
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
    paginate_by = 30
    
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

    def get_queryset(self):
        return Place.objects.prefetch_related('place_gallery_images').select_related('category', 'created_by')

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add membership information for each group
        if self.request.user.is_authenticated:
            for group in context['travel_groups']:
                group.is_member = self.request.user in group.members.all()
                group.is_creator = self.request.user == group.creator
                group.can_join = (
                    group.is_public and 
                    not group.is_member and 
                    not group.is_creator
                )
        else:
            for group in context['travel_groups']:
                group.is_member = False
                group.is_creator = False
                group.can_join = False
        
        return context

class TravelGroupDetailView(DetailView):
    model = TravelGroup
    template_name = 'listings/travelgroup_detail.html'
    context_object_name = 'travel_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prefetch related personal profiles to avoid N+1 queries in templates
        context['members'] = self.object.members.select_related('personalprofile').all()
        
        # Add membership information for the current user
        if self.request.user.is_authenticated:
            context['is_member'] = self.request.user in self.object.members.all()
            context['is_creator'] = self.request.user == self.object.creator
            context['can_join'] = (
                self.object.is_public and 
                not context['is_member'] and 
                not context['is_creator']
            )
            context['can_leave'] = context['is_member'] and not context['is_creator']
        else:
            context['is_member'] = False
            context['is_creator'] = False
            context['can_join'] = False
            context['can_leave'] = False
        
        return context

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
        # Include groups the user created or is a member of
        return TravelGroup.objects.filter(models.Q(creator=self.request.user) | models.Q(members=self.request.user)).distinct()


@login_required
@require_POST
def add_travel_group_member(request, group_id):
    """Add a member to a travel group by email or user ID"""
    try:
        group = TravelGroup.objects.get(id=group_id)
        
        # Check if user is the creator of the group
        if request.user != group.creator:
            messages.error(request, 'Only the group creator can add members')
            return redirect('travelgroup_detail', pk=group_id)
        
        email = request.POST.get('email', '').strip()
        user_id = request.POST.get('user_id', '').strip()
        
        if not email or not user_id:
            messages.error(request, 'Both email and user ID are required')
            return redirect('travelgroup_detail', pk=group_id)
        
        user_to_add = None
        
        # Find user by both email and user ID for verification
        try:
            user_to_add = MyUser.objects.get(email=email, id=user_id)
        except MyUser.DoesNotExist:
            messages.error(request, f'No user found with email: {email} and ID: {user_id}. Please verify both fields are correct.')
            return redirect('travelgroup_detail', pk=group_id)
        except ValueError:
            messages.error(request, f'Invalid user ID format: {user_id}')
            return redirect('travelgroup_detail', pk=group_id)
        
        if not user_to_add:
            messages.error(request, 'User not found')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Check if user is already a member
        if user_to_add in group.members.all():
            messages.error(request, f'{user_to_add.email} is already a member of this group')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Check if user is the creator
        if user_to_add == group.creator:
            messages.error(request, 'The creator is automatically a member')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Add user to group
        group.members.add(user_to_add)

        # If the group has an admission fee (> 0), notify admin via email
        try:
            if hasattr(group, 'admissionfee') and float(group.admissionfee) > 0:
                admin_email = getattr(settings, 'ADMIN_EMAIL', 'kevingitundu@gmail.com')
                subject = f"New TravelGroup Admission (Fee) - Group {group.id}"
                message = (
                    f"A member has been added to a TravelGroup that charges admission.\n\n"
                    f"Group ID: {group.id}\n"
                    f"Group Name: {group.name}\n"
                    f"Creator ID: {group.creator.id}\n"
                    f"Creator Email: {group.creator.email}\n"
                    f"Member Added ID: {user_to_add.id}\n"
                    f"Member Added Email: {user_to_add.email}\n"
                    f"Admission Fee: KES {group.admissionfee}"
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
        except Exception:
            pass
        
        messages.success(request, f'{user_to_add.email} has been added to the group successfully')
        return redirect('travelgroup_detail', pk=group_id)
        
    except TravelGroup.DoesNotExist:
        messages.error(request, 'Travel group not found')
        return redirect('travelgroup_list')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('travelgroup_detail', pk=group_id)

@login_required
@require_POST
def join_travel_group(request, group_id):
    """Allow a user to join a travel group"""
    try:
        group = TravelGroup.objects.get(id=group_id)
        
        # Check if group is public
        if not group.is_public:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'This group is private and requires an invitation to join.'})
            messages.error(request, 'This group is private and requires an invitation to join.')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Check if user is already a member
        if request.user in group.members.all():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'You are already a member of this group.'})
            messages.warning(request, 'You are already a member of this group.')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Check if user is the creator
        if request.user == group.creator:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'You are the creator of this group.'})
            messages.info(request, 'You are the creator of this group.')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Add user to group
        group.members.add(request.user)

        # If the group has an admission fee (> 0), notify admin via email
        try:
            if hasattr(group, 'admissionfee') and float(group.admissionfee) > 0:
                admin_email = getattr(settings, 'ADMIN_EMAIL', 'kevingitundu@gmail.com')
                subject = f"New TravelGroup Admission (Fee) - Group {group.id}"
                message = (
                    f"A member has joined a TravelGroup that charges admission.\n\n"
                    f"Group ID: {group.id}\n"
                    f"Group Name: {group.name}\n"
                    f"Creator ID: {group.creator.id}\n"
                    f"Creator Email: {group.creator.email}\n"
                    f"Member Added ID: {request.user.id}\n"
                    f"Member Added Email: {request.user.email}\n"
                    f"Admission Fee: KES {group.admissionfee}"
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
        except Exception:
            pass
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'You have successfully joined {group.name}!'})
        
        messages.success(request, f'You have successfully joined {group.name}!')
        return redirect('travelgroup_detail', pk=group_id)
        
    except TravelGroup.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Travel group not found'})
        messages.error(request, 'Travel group not found')
        return redirect('travelgroup_list')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('travelgroup_detail', pk=group_id)

@login_required
@require_POST
def leave_travel_group(request, group_id):
    """Allow a user to leave a travel group"""
    try:
        group = TravelGroup.objects.get(id=group_id)
        
        # Check if user is a member
        if request.user not in group.members.all():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'You are not a member of this group.'})
            messages.warning(request, 'You are not a member of this group.')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Check if user is the creator
        if request.user == group.creator:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Group creators cannot leave their own group. Please delete the group instead.'})
            messages.error(request, 'Group creators cannot leave their own group. Please delete the group instead.')
            return redirect('travelgroup_detail', pk=group_id)
        
        # Remove user from group
        group.members.remove(request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'You have left {group.name}.'})
        
        messages.success(request, f'You have left {group.name}.')
        return redirect('travelgroup_list')
        
    except TravelGroup.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Travel group not found'})
        messages.error(request, 'Travel group not found')
        return redirect('travelgroup_list')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('travelgroup_detail', pk=group_id)

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
                start_date = datetime.now().replace(day=1)
                queryset = queryset.filter(start_date__gte=start_date)
                print(f"Debug - Applied this_month filter, queryset count: {queryset.count()}")
            elif date_range == 'next_month':
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

class TourVideoUploadView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Separate view for tour video uploads - only for verified creators"""
    model = GroupTours
    template_name = 'listings/tour_video_upload.html'
    context_object_name = 'group_tour'
    
    def test_func(self):
        """Only tour creator can upload videos"""
        return self.get_object().creator == self.request.user
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is verified before allowing video upload"""
        if not request.user.is_verified:
            messages.error(request, 'Only verified creators can upload tour videos. Please get verified first.')
            return redirect('core:subscription_page')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add form to context for video upload"""
        context = super().get_context_data(**kwargs)
        context['form'] = TourVideoUploadForm(instance=self.get_object())
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle video upload"""
        tour = self.get_object()
        form = TourVideoUploadForm(request.POST, request.FILES, instance=tour)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Tour video uploaded successfully!')
            return redirect('grouptours_list')
        else:
            # If form is invalid, re-render with errors
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)
    
    def delete_video(self, request, *args, **kwargs):
        """Handle video deletion via AJAX"""
        if request.method == 'POST':
            tour = self.get_object()
            
            # Check if user has permission to delete
            if tour.creator != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            # Check if user is verified
            if not request.user.is_verified:
                return JsonResponse({'success': False, 'error': 'Only verified creators can delete videos'})
            
            try:
                # Delete the video file
                if tour.tour_video:
                    # Remove the file from storage
                    tour.tour_video.delete(save=False)
                    # Clear the field
                    tour.tour_video = None
                    tour.save()
                    
                    return JsonResponse({'success': True, 'message': 'Video deleted successfully'})
                else:
                    return JsonResponse({'success': False, 'error': 'No video found to delete'})
                    
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error deleting video: {str(e)}'})
        
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

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
            # Create the comment manually since TourCommentForm is not a ModelForm
            comment = TourComment.objects.create(
                tour=tour,
                user=request.user,
                content=form.cleaned_data['content']
            )
            
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'content': comment.content,
                'user_email': comment.user.email,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        else:
            return JsonResponse({'error': 'Invalid comment data', 'form_errors': form.errors}, status=400)
    except GroupTours.DoesNotExist:
        return JsonResponse({'error': 'Tour not found'}, status=404)
    except Exception as e:
        print(f"Unexpected error in add_tour_comment: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

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
    """Tour booking view with payment integration and Lipa Mdogo Mdogo feature"""
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
            
            # existing_booking will be passed to template to show balance and allow additional payments
            
            # Get user's phone number from profile if available
            user_phone = request.user.phone if hasattr(request.user, 'phone') else ''
            
            context = {
                'tour': tour,
                'user_phone': user_phone,
                'available_spots': tour.available_spots,
                'existing_booking': existing_booking,
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
            
            # Get form data (M-Pesa only)
            participants = int(request.POST.get('participants', 1))
            special_requests = request.POST.get('special_requests', '')
            phone_number = request.POST.get('phone_number', '')
            payment_amount = Decimal(request.POST.get('payment_amount', '0'))
            
            print(f"📋 DEBUG: Form data - participants: {participants}, phone: {phone_number}, payment_amount: {payment_amount}")
            
            # Check if user has already booked this tour (any status)
            existing_booking = TourBooking.objects.filter(
                tour=tour, 
                user=request.user
            ).first()
            
            if existing_booking:
                # Use existing booking
                print(f"💰 DEBUG: Using existing booking {existing_booking.id}")
                booking = existing_booking
            else:
                # Create new booking
                print(f"🎯 DEBUG: Creating new booking")
                
                # Validate participants
                if participants < 1 or participants > tour.available_spots:
                    messages.error(request, 'Invalid number of participants.')
                    return redirect('tour_booking_payment', pk=pk)
                
                # Calculate total amount
                total_amount = tour.price_per_person * participants
                
                # Create the booking
                booking = TourBooking.objects.create(
                    tour=tour,
                    user=request.user,
                    participants=participants,
                    special_requests=special_requests,
                    total_amount=total_amount,
                    status='pending'
                )
            
            # Validate payment amount (flexible for M-Pesa)
            if payment_amount < 1:
                messages.error(request, 'Payment amount must be at least KES 1.')
                return redirect('tour_booking_payment', pk=pk)
            
            # For existing bookings, check remaining amount
            if existing_booking:
                remaining_amount = existing_booking.remaining_amount
                if payment_amount > remaining_amount:
                    messages.error(request, f'Payment amount cannot exceed the remaining balance of KES {remaining_amount}.')
                    return redirect('tour_booking_payment', pk=pk)
            else:
                # For new bookings, check total amount
                if payment_amount > booking.total_amount:
                    messages.error(request, 'Payment amount cannot exceed the total tour cost.')
                    return redirect('tour_booking_payment', pk=pk)
            
            # Create the payment transaction record (M-Pesa only)
            tour_payment = TourBookingPayment.objects.create(
                booking=booking,
                user=request.user,
                amount=payment_amount,
                payment_method='mpesa',
                payment_status='pending',
                description=f"{'Additional' if existing_booking else 'Initial'} payment for {tour.name} - {booking.participants} participant(s)"
            )
            
            # Initialize M-Pesa STK push
            from core.tests import initiate_tour_payment
            print(f"🔍 DEBUG: Initiating M-Pesa payment for phone: {phone_number}, account: {f'Tour_{booking.id}_{tour_payment.id}'}, total: {payment_amount}")
            
            # Call the function with required arguments
            response = initiate_tour_payment(
                phone=phone_number,
                account=f"Tour_{booking.id}_{tour_payment.id}",
                total=payment_amount
            )
            
            if response.status_code == 200:
                result = response.json()
                tour_payment.external_reference = result.get('CheckoutRequestID', '')
                tour_payment.payment_status = 'processing'
                tour_payment.metadata = {
                    'mpesa_request_id': result.get('MerchantRequestID', ''),
                    'checkout_request_id': result.get('CheckoutRequestID', ''),
                    'response_code': result.get('ResponseCode', ''),
                    'response_description': result.get('ResponseDescription', ''),
                    'customer_message': result.get('CustomerMessage', ''),
                                            'timestamp': datetime.now().strftime("%Y%m%d%H%M%S")
                }
                tour_payment.save()
                
                # Update booking status to confirmed since payment is processing
                booking.status = 'confirmed'
                booking.save()
                
                messages.success(request, f'✅ Tour booking {"updated" if existing_booking else "created"}! M-Pesa STK push sent to {phone_number}. Please complete the payment on your phone.')
                return redirect('payment_status', transaction_id=tour_payment.payment_reference)
            else:
                messages.warning(request, f'{"Additional payment" if existing_booking else "Tour booking"} {"failed" if existing_booking else "created but payment failed"}. Please contact support.')
                return redirect('tour_booking_payment', pk=booking.tour.pk)
                
        except GroupTours.DoesNotExist:
            messages.error(request, 'Tour not found.')
            return redirect('grouptours_list')
        except Exception as e:
            print(f"❌ DEBUG: Error in TourBookingWithPaymentView.post: {str(e)}")
            messages.error(request, f'An error occurred while processing your booking: {str(e)}')
            return redirect('tour_booking_payment', pk=pk)
    


class PaymentStatusView(LoginRequiredMixin, View):
    """View to show payment status and instructions"""
    template_name = 'listings/payment_status.html'
    
    def get(self, request, transaction_id):
        try:
            # First try to find a TourBookingPayment
            try:
                tour_payment = TourBookingPayment.objects.get(
                    payment_reference=transaction_id,
                    user=request.user
                )
                
                # Get tour details
                tour = tour_payment.booking.tour
                
                context = {
                    'tour_payment': tour_payment,
                    'tour': tour,
                    'booking': tour_payment.booking,
                    'is_tour_booking': True,
                }
                
                return render(request, self.template_name, context)
                
            except TourBookingPayment.DoesNotExist:
                # Fall back to old PaymentTransaction model
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
                        'is_tour_booking': False,
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
            
        except Exception as e:
            print(f"❌ DEBUG: Error in PaymentStatusView: {str(e)}")
            messages.error(request, 'An error occurred while loading payment status.')
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
            
            # Get user's phone number from profile if available
            user_phone = request.user.phone if hasattr(request.user, 'phone') else ''
            
            context = {
                'event': event,
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
            
            # Get form data (M-Pesa only)
            participants = int(request.POST.get('participants', 1))
            special_requests = request.POST.get('special_requests', '')
            phone_number = request.POST.get('phone_number', '')
            
            print(f"📋 DEBUG: Form data - participants: {participants}, phone: {phone_number}")
            
            # Validate phone number
            if not phone_number:
                messages.error(request, 'Phone number is required for M-Pesa payment.')
                return redirect('event_booking_payment', pk=pk)
            
            # Calculate total amount
            total_amount = event.price_per_person * participants if event.price_per_person else 0
            
            # Create booking record
            booking = EventBooking.objects.create(
                event=event,
                user=request.user,
                participants=participants,
                special_requests=special_requests,
                total_amount=total_amount,
                status='pending'
            )
            
            # Initialize M-Pesa STK push
            from core.tests import initiate_tour_payment
            print(f"🔍 DEBUG: Initiating M-Pesa payment for phone: {phone_number}, account: {f'Event_{booking.id}'}, total: {total_amount}")
            
            # Call the function with required arguments
            response = initiate_tour_payment(
                phone=phone_number,
                account=f"Event_{booking.id}",
                total=total_amount
            )
            
            if response.status_code == 200:
                result = response.json()
                booking.payment_reference = result.get('CheckoutRequestID', '')
                booking.payment_method = 'mpesa'
                booking.metadata = {
                    'mpesa_request_id': result.get('MerchantRequestID', ''),
                    'checkout_request_id': result.get('CheckoutRequestID', ''),
                    'response_code': result.get('ResponseCode', ''),
                    'response_description': result.get('ResponseDescription', ''),
                    'customer_message': result.get('CustomerMessage', ''),
                    'timestamp': datetime.now().strftime("%Y%m%d%H%M%S")
                }
                booking.save()
                
                # Update booking status to confirmed since payment is processing
                booking.status = 'confirmed'
                booking.save()
                
                messages.success(request, f'✅ Event booking created! M-Pesa STK push sent to {phone_number}. Please complete the payment on your phone.')
                return redirect('event_receipt', transaction_id=booking.payment_reference)
            else:
                messages.warning(request, f'Event booking created but payment failed. Please contact support.')
                return redirect('event_booking_payment', pk=event.pk)
            
        except Event.DoesNotExist:
            messages.error(request, 'Event not found.')
            return redirect('event_list')
        except Exception as e:
            print(f"❌ DEBUG: Error in EventBookingWithPaymentView.post: {str(e)}")
            messages.error(request, f'An error occurred while processing your booking: {str(e)}')
            return redirect('event_booking_payment', pk=pk)
    



class MPesaWebhookView(View):
    """Handle M-Pesa payment callbacks and update booking status"""
    
    def post(self, request):
        print(f"📞 DEBUG: M-Pesa webhook received: {request.body}")
        
        try:
            # Parse the callback data
            callback_data = json.loads(request.body)
            print(f"📋 DEBUG: Parsed callback data: {callback_data}")
            
            # Check if this is an event booking or tour booking
            account_reference = callback_data.get('AccountReference', '')
            
            if account_reference.startswith('Event_'):
                # Handle event booking
                return self._handle_event_booking(callback_data)
            else:
                # Handle tour booking (existing logic)
                return self._handle_tour_booking(callback_data)
                
        except json.JSONDecodeError as e:
            print(f"❌ DEBUG: Invalid JSON in webhook: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"❌ DEBUG: Error processing webhook: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    def _handle_event_booking(self, callback_data):
        """Handle M-Pesa callback for event bookings"""
        try:
            print(f"🎯 DEBUG: Processing event booking webhook")
            
            # Extract event booking ID from account reference
            account_ref = callback_data.get('AccountReference', '')
            event_booking_id = account_ref.replace('Event_', '')
            
            # Get the event booking
            from .models import EventBooking
            try:
                booking = EventBooking.objects.get(id=event_booking_id)
                print(f"✅ DEBUG: Found event booking {booking.id} for event {booking.event.name}")
            except EventBooking.DoesNotExist:
                print(f"❌ DEBUG: Event booking {event_booking_id} not found")
                return JsonResponse({'status': 'error', 'message': 'Event booking not found'}, status=404)
            
            # Check payment result
            result_code = callback_data.get('ResultCode', '')
            result_desc = callback_data.get('ResultDesc', '')
            
            print(f"💰 DEBUG: Event payment result - Code: {result_code}, Description: {result_desc}")
            
            if result_code == '0':
                # Payment successful
                booking.payment_status = 'completed'
                booking.status = 'confirmed'
                booking.payment_date = datetime.now()
                
                # Safely update metadata
                current_metadata = booking.metadata or {}
                current_metadata.update({
                    'webhook_data': callback_data,
                    'payment_completed_at': datetime.now().isoformat(),
                    'mpesa_transaction_id': callback_data.get('TransactionID', ''),
                })
                booking.metadata = current_metadata
                booking.save()
                
                # Create payment transaction record
                self._create_payment_transaction(booking, callback_data)
                
                print(f"✅ DEBUG: Event booking {booking.id} payment completed successfully")
                
                # Send email notification
                self._send_event_booking_email(booking)
                
                return JsonResponse({'status': 'success', 'message': 'Event payment processed'}, status=200)
            else:
                # Payment failed
                booking.payment_status = 'failed'
                booking.status = 'cancelled'
                
                # Safely update metadata
                current_metadata = booking.metadata or {}
                current_metadata.update({
                    'webhook_data': callback_data,
                    'payment_failed_at': datetime.now().isoformat(),
                    'failure_reason': result_desc,
                })
                booking.metadata = current_metadata
                booking.save()
                
                print(f"❌ DEBUG: Event booking {booking.id} payment failed: {result_desc}")
                return JsonResponse({'status': 'failed', 'message': 'Event payment failed'}, status=200)
                
        except Exception as e:
            print(f"❌ DEBUG: Error handling event booking webhook: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    def _handle_tour_booking(self, callback_data):
        """Handle M-Pesa callback for tour bookings (existing logic)"""
        try:
            # Initialize M-Pesa service
            mpesa_service = MPesaService()
            
            # Process the callback
            success = mpesa_service.process_callback(callback_data)
            
            if success:
                print("✅ DEBUG: Tour booking M-Pesa callback processed successfully")
                return JsonResponse({'status': 'success'}, status=200)
            else:
                print("❌ DEBUG: Tour booking M-Pesa callback processing failed")
                return JsonResponse({'status': 'failed'}, status=400)
                
        except Exception as e:
            print(f"❌ DEBUG: Error processing tour booking webhook: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    def get(self, request):
        """Handle GET requests (for testing)"""
        return JsonResponse({'status': 'webhook_endpoint_active'}, status=200)
    
    def _send_event_booking_email(self, booking):
        """Send confirmation email for successful event booking"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f"✅ Event Booking Confirmed: {booking.event.name}"
            
            message = f"""
Dear {booking.user.get_full_name() or booking.user.username},

Your event booking has been confirmed! 🎉

Event Details:
- Event: {booking.event.name}
- Date: {booking.event.date}
- Time: {booking.event.time}
- Location: {booking.event.place.name}
- Participants: {booking.participants}
- Total Amount: KES {booking.total_amount}

Payment Status: ✅ Confirmed
Booking ID: {booking.id}

We look forward to seeing you at the event!

Best regards,
TravelsKe Team
            """.strip()
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.user.email],
                fail_silently=True,  # Don't fail if email sending fails
            )
            
            print(f"📧 DEBUG: Event booking confirmation email sent to {booking.user.email}")
            
        except Exception as e:
            print(f"❌ DEBUG: Failed to send event booking email: {str(e)}")
            # Don't fail the webhook if email fails
    
    def _create_payment_transaction(self, booking, callback_data):
        """Create payment transaction record for event booking"""
        try:
            from core.models import PaymentTransaction, PaymentMethod
            from decimal import Decimal
            
            # Get or create M-Pesa payment method
            payment_method, created = PaymentMethod.objects.get_or_create(
                name='mpesa',
                defaults={
                    'display_name': 'M-Pesa',
                    'description': 'Mobile money payment via M-Pesa',
                    'is_active': True,
                    'icon': 'mobile',
                    'sort_order': 1
                }
            )
            
            # Create payment transaction
            transaction = PaymentTransaction.objects.create(
                user=booking.user,
                amount=booking.total_amount,
                currency='KES',
                processing_fee=Decimal('0.00'),
                total_amount=booking.total_amount,
                payment_method=payment_method,
                status='completed',
                transaction_type='payment',
                content_type='event_booking',
                object_id=booking.id,
                description=f"Payment for {booking.event.name} event - {booking.participants} participant(s)",
                metadata={
                    'event_id': booking.event.id,
                    'event_name': booking.event.name,
                    'participants': booking.participants,
                    'mpesa_transaction_id': callback_data.get('TransactionID', ''),
                    'mpesa_request_id': callback_data.get('MerchantRequestID', ''),
                    'mpesa_checkout_request_id': callback_data.get('CheckoutRequestID', ''),
                    'webhook_data': callback_data,
                }
            )
            
            print(f"💳 DEBUG: Payment transaction {transaction.transaction_id} created for event booking {booking.id}")
            
        except Exception as e:
            print(f"❌ DEBUG: Failed to create payment transaction: {str(e)}")
            # Don't fail the webhook if transaction creation fails

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
                return redirect('event_receipt', transaction_id=booking.payment_reference)
            else:
                print(f"❌ DEBUG: STK push failed with status {response.status_code}")
                messages.warning(request, f'⚠️ Booking created but M-Pesa STK push failed. Please try again or contact support.')
                return redirect('event_receipt', transaction_id=booking.payment_reference)
                
        except Exception as e:
            print(f"❌ DEBUG: Error in M-Pesa payment: {str(e)}")
            messages.error(request, f'❌ Error processing M-Pesa payment: {str(e)}')
            return redirect('event_receipt', transaction_id=booking.payment_reference)


class EventReceiptView(LoginRequiredMixin, View):
    """View to display event payment receipt and check payment status"""
    template_name = 'listings/event_receipt.html'
    
    def get(self, request, transaction_id):
        try:
            # Try to find the event booking by transaction ID
            from .models import EventBooking
            booking = EventBooking.objects.filter(
                payment_reference__icontains=transaction_id
            ).first()
            
            if not booking:
                # If no booking found, try to find by other means
                messages.error(request, 'Event booking not found.')
                return redirect('event_list')
            
            # Get the event
            event = booking.event
            
            # Calculate total amount
            total_amount = event.price_per_person * booking.participants if event.price_per_person else 0
            
            context = {
                'event': event,
                'booking': booking,
                'transaction_id': transaction_id,
                'total_amount': total_amount,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            print(f"❌ DEBUG: Error in EventReceiptView.get: {str(e)}")
            messages.error(request, 'An error occurred while loading the receipt.')
            return redirect('event_list')


class EventPaymentStatusView(View):
    """API view to check event payment status"""
    
    def get(self, request, transaction_id):
        try:
            from .models import EventBooking
            
            # Try to find the event booking by transaction ID
            booking = EventBooking.objects.filter(
                payment_reference__icontains=transaction_id
            ).first()
            
            if not booking:
                return JsonResponse({
                    'success': False,
                    'error': 'Event booking not found'
                })
            
            # Get payment status from the booking
            payment_status = booking.payment_status or 'pending'
            
            # Map status to user-friendly values
            status_mapping = {
                'pending': 'processing',
                'processing': 'processing',
                'completed': 'completed',
                'successful': 'completed',
                'failed': 'failed',
                'cancelled': 'cancelled',
            }
            
            mapped_status = status_mapping.get(payment_status, payment_status)
            
            return JsonResponse({
                'success': True,
                'payment_status': mapped_status,
                'booking_id': booking.id,
                'event_name': booking.event.name,
                'amount': float(booking.total_amount) if booking.total_amount else 0,
                'participants': booking.participants,
            })
            
        except Exception as e:
            print(f"❌ DEBUG: Error in EventPaymentStatusView.get: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class AdditionalPaymentView(LoginRequiredMixin, View):
    """View to handle additional payments for existing tour bookings (Lipa Mdogo Mdogo)"""
    template_name = 'listings/additional_payment.html'
    
    def get(self, request, booking_id):
        try:
            booking = TourBooking.objects.get(id=booking_id, user=request.user)
            
            # Check if booking is still active
            if booking.status not in ['pending', 'confirmed']:
                messages.error(request, 'This booking is no longer active.')
                return redirect('user_bookings')
            
            # Get available payment methods
            payment_methods = PaymentMethod.objects.filter(is_active=True)
            
            # Get user's phone number from profile if available
            user_phone = request.user.phone if hasattr(request.user, 'phone') else ''
            
            # Get payment history
            payment_history = booking.payment_transactions.all().order_by('-created_at')
            
            context = {
                'booking': booking,
                'payment_methods': payment_methods,
                'user_phone': user_phone,
                'payment_history': payment_history,
            }
            
            return render(request, self.template_name, context)
            
        except TourBooking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('user_bookings')
    
    def post(self, request, booking_id):
        try:
            booking = TourBooking.objects.get(id=booking_id, user=request.user)
            
            # Get form data
            payment_amount = Decimal(request.POST.get('payment_amount', '0'))
            payment_method_id = request.POST.get('payment_method')
            phone_number = request.POST.get('phone_number', '')
            
            # Validate payment amount
            if payment_amount < 100:
                messages.error(request, 'Minimum payment amount is KES 100.')
                return redirect('additional_payment', booking_id=booking_id)
            
            remaining_amount = booking.remaining_amount
            if payment_amount > remaining_amount:
                messages.error(request, f'Payment amount cannot exceed the remaining amount of KES {remaining_amount}.')
                return redirect('additional_payment', booking_id=booking_id)
            
            # Get payment method
            try:
                payment_method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
            except PaymentMethod.DoesNotExist:
                messages.error(request, 'Invalid payment method selected.')
                return redirect('additional_payment', booking_id=booking_id)
            
            # Create the payment transaction record
            tour_payment = TourBookingPayment.objects.create(
                booking=booking,
                user=request.user,
                amount=payment_amount,
                payment_method=payment_method.name.lower(),
                payment_status='pending',
                description=f"Additional payment for {booking.tour.name} - {booking.participants} participant(s)"
            )
            
            # Process payment based on method
            if payment_method.name.lower() == 'mpesa':
                return self._process_mpesa_payment(request, booking, tour_payment, phone_number, payment_amount)
            else:
                # For other payment methods, redirect to payment status
                messages.success(request, f'Additional payment of KES {payment_amount} is pending.')
                return redirect('payment_status', transaction_id=tour_payment.payment_reference)
                
        except TourBooking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('user_bookings')
        except Exception as e:
            print(f"❌ DEBUG: Error in AdditionalPaymentView.post: {str(e)}")
            messages.error(request, f'An error occurred while processing your payment: {str(e)}')
            return redirect('additional_payment', booking_id=booking_id)
    
    def _process_mpesa_payment(self, request, booking, tour_payment, phone_number, payment_amount):
        """Process M-Pesa payment for additional payment using working implementation"""
        try:
            print(f"🔍 DEBUG: _process_mpesa_payment called for additional payment {tour_payment.id}, phone: {phone_number}, amount: {payment_amount}")
            
            # Use the working implementation from verification
            print("🚀 DEBUG: Using working M-Pesa implementation from verification...")
            
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
                return redirect('additional_payment', booking_id=booking.id)
            
            # Generate timestamp and password (working approach from verification)
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
                return redirect('additional_payment', booking_id=booking.id)
            
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
                "Amount": int(payment_amount),
                "PartyA": phone,
                "PartyB": int(business_shortcode),
                "PhoneNumber": phone,
                "CallBackURL": callback_url,
                "AccountReference": f"Tour_{booking.id}_{tour_payment.id}",
                "TransactionDesc": f"Additional payment - {booking.tour.name}",
            }
            
            print(f"📦 DEBUG: STK push payload prepared")
            print(f"   Amount: KES {payment_amount}")
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
                
                # Update payment record with M-Pesa details
                tour_payment.external_reference = result.get('CheckoutRequestID', '')
                tour_payment.payment_status = 'processing'
                tour_payment.metadata = {
                    'mpesa_request_id': result.get('MerchantRequestID', ''),
                    'checkout_request_id': result.get('CheckoutRequestID', ''),
                    'response_code': result.get('ResponseCode', ''),
                    'response_description': result.get('ResponseDescription', ''),
                    'customer_message': result.get('CustomerMessage', ''),
                    'timestamp': timestamp
                }
                tour_payment.save()
                
                messages.success(request, f'✅ Additional payment initiated! M-Pesa STK push sent to {phone}. Please complete the payment on your phone.')
                return redirect('payment_status', transaction_id=tour_payment.payment_reference)
            else:
                print(f"❌ DEBUG: STK push failed with status {response.status_code}")
                messages.warning(request, 'Additional payment created but payment failed. Please contact support.')
                return redirect('additional_payment', booking_id=booking.id)
                
        except Exception as e:
            print(f"❌ Error processing additional payment: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, 'Error processing payment. Please contact support.')
            return redirect('additional_payment', booking_id=booking.id)
    
class PaymentStatusView(LoginRequiredMixin, View):
    """View to show payment status and instructions"""
    template_name = 'listings/payment_status.html'
    
    def get(self, request, transaction_id):
        try:
            # First try to find a TourBookingPayment
            try:
                tour_payment = TourBookingPayment.objects.get(
                    payment_reference=transaction_id,
                    user=request.user
                )
                
                # Get tour details
                tour = tour_payment.booking.tour
                
                context = {
                    'tour_payment': tour_payment,
                    'tour': tour,
                    'booking': tour_payment.booking,
                    'is_tour_booking': True,
                }
                
                return render(request, self.template_name, context)
                
            except TourBookingPayment.DoesNotExist:
                # Fall back to old PaymentTransaction model
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
                        'is_tour_booking': False,
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
            
        except Exception as e:
            print(f"❌ DEBUG: Error in PaymentStatusView: {str(e)}")
            messages.error(request, 'An error occurred while loading payment status.')
            return redirect('user_bookings')

@csrf_exempt
@require_http_methods(["POST"])
def agency_chat(request, agency_id):
    """AI chat endpoint for agencies with comprehensive context"""
    start_time = timezone.now()
    
    try:
        # Debug logging
        print(f"Agency chat called for agency_id: {agency_id}")
        
        # Parse JSON data
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        print(f"Question received: {question}")
        
        if not question:
            return JsonResponse({'success': False, 'error': 'Question is required'}, status=400)
        
        # Get agency information
        try:
            agency = Agency.objects.get(pk=agency_id)
            print(f"Agency found: {agency.name}")
        except Agency.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Agency not found'}, status=404)
        
        # Get user information and session data
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key or f"anon_{uuid.uuid4().hex[:16]}"
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create ChatQuestion record
        try:
            from core.models import ChatQuestion, ChatResponse
            
            chat_question = ChatQuestion.objects.create(
                chat_type='agency',
                agency=agency,
                user=user,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                question=question,
                question_tokens=len(question.split())  # Rough token estimation
            )
            print(f"Chat question saved with ID: {chat_question.id}")
        except Exception as e:
            print(f"Error saving chat question: {e}")
            # Continue without saving if there's an error
        
        # Import openai when needed
        try:
            import openai
            print("OpenAI imported successfully!")
        except Exception as e:
            print(f"OpenAI import failed: {e}")
            fallback_response = f"I'm sorry, but I'm currently offline. However, I can tell you about {agency.name} based on the information I have: {agency.description[:200]}..."
            
            # Save fallback response if question was saved
            if 'chat_question' in locals():
                try:
                    ChatResponse.objects.create(
                        question=chat_question,
                        response=fallback_response,
                        response_tokens=len(fallback_response.split()),
                        ai_model='fallback',
                        response_time_ms=0,
                        total_tokens=chat_question.question_tokens,
                        cost_usd=0
                    )
                except Exception as save_error:
                    print(f"Error saving fallback response: {save_error}")
            
            return JsonResponse({
                'success': True, 
                'response': fallback_response
            })
        
        print("OpenAI is available, proceeding with API call")
        
        # Gather comprehensive agency data
        try:
            agency_data = {
                'basic_info': {
                    'name': agency.name,
                    'agency_type': agency.get_agency_type_display(),
                    'status': agency.get_status_display(),
                    'description': agency.description,
                    'city': agency.city,
                    'country': agency.country,
                    'address': agency.address,
                    'phone': agency.phone,
                    'email': agency.email,
                    'website': agency.website if agency.website else 'Not provided',
                    'postal_code': agency.postal_code if agency.postal_code else 'Not specified',
                    'license_number': agency.license_number if agency.license_number else 'Not specified',
                    'registration_number': agency.registration_number if agency.registration_number else 'Not specified',
                    'year_established': agency.year_established if agency.year_established else 'Not specified',
                    'price_range': agency.get_price_range_display(),
                    'verified': 'Yes' if agency.verified else 'No',
                    'is_active': 'Yes' if agency.status == 'active' else 'No'
                },
                'location_details': {
                    'latitude': str(agency.latitude) if agency.latitude else 'Not specified',
                    'longitude': str(agency.longitude) if agency.longitude else 'Not specified'
                },
                'features': {
                    'specialties': ', '.join(agency.specialties) if agency.specialties else 'None specified',
                    'languages_spoken': ', '.join(agency.languages_spoken) if agency.languages_spoken else 'Not specified',
                    'group_size_range': agency.group_size_range if agency.group_size_range else 'Not specified',
                    'operating_hours': agency.operating_hours if agency.operating_hours else 'Not specified'
                },
                'ratings': {
                    'average_rating': agency.average_rating,
                    'total_ratings': agency.total_ratings,
                    'rating_distribution': agency.rating_distribution
                },
                'social_media': {
                    'facebook': agency.facebook if agency.facebook else 'Not available',
                    'twitter': agency.twitter if agency.twitter else 'Not available',
                    'instagram': agency.instagram if agency.instagram else 'Not available',
                    'linkedin': agency.linkedin if agency.linkedin else 'Not available'
                },
                'certifications': {
                    'certifications': ', '.join(agency.certifications) if agency.certifications else 'None specified'
                }
            }
            print("Agency data gathered successfully")
        except Exception as e:
            print(f"Error gathering agency data: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error processing agency data: {str(e)}'
            }, status=500)
        
        # Get agency services
        try:
            services = agency.services.filter(is_active=True)
            services_data = []
            for service in services:
                service_data = {
                    'name': service.name,
                    'service_type': service.get_service_type_display(),
                    'description': service.description,
                    'availability': service.get_availability_display(),
                    'is_featured': service.is_featured,
                    'base_price': str(service.base_price) if service.base_price else 'Price on request',
                    'price_range_min': str(service.price_range_min) if service.price_range_min else 'Not specified',
                    'price_range_max': str(service.price_range_max) if service.price_range_max else 'Not specified',
                    'pricing_model': service.pricing_model if service.pricing_model else 'Not specified',
                    'duration': service.duration if service.duration else 'Not specified',
                    'group_size_min': service.group_size_min if service.group_size_min else 'Not specified',
                    'group_size_max': service.group_size_max if service.group_size_max else 'Not specified',
                    'requirements': service.requirements if service.requirements else 'None specified',
                    'included_items': service.included_items if service.included_items else 'Not specified',
                    'excluded_items': service.excluded_items if service.excluded_items else 'Not specified',
                    'cancellation_policy': service.cancellation_policy if service.cancellation_policy else 'Not specified'
                }
                services_data.append(service_data)
            print("Services data gathered successfully")
        except Exception as e:
            print(f"Error gathering services data: {e}")
            services_data = []
        
        # Get gallery images
        try:
            gallery_images = agency.gallery_images.all()
            gallery_data = []
            for image in gallery_images:
                gallery_data.append({
                    'caption': image.caption if image.caption else 'Gallery image',
                    'is_featured': image.is_featured
                })
            print("Gallery data gathered successfully")
        except Exception as e:
            print(f"Error gathering gallery data: {e}")
            gallery_data = []
        
        # Create comprehensive context
        try:
            context = f"""
            AGENCY INFORMATION:
            ===================
            Basic Details:
            - Name: {agency_data['basic_info']['name']}
            - Agency Type: {agency_data['basic_info']['agency_type']}
            - Status: {agency_data['basic_info']['status']}
            - Description: {agency_data['basic_info']['description']}
            - Location: {agency_data['basic_info']['city']}, {agency_data['basic_info']['country']}
            - Address: {agency_data['basic_info']['address']}
            - Phone: {agency_data['basic_info']['phone']}
            - Email: {agency_data['basic_info']['email']}
            - Website: {agency_data['basic_info']['website']}
            - Postal Code: {agency_data['basic_info']['postal_code']}
            - License Number: {agency_data['basic_info']['license_number']}
            - Registration Number: {agency_data['basic_info']['registration_number']}
            - Year Established: {agency_data['basic_info']['year_established']}
            - Price Range: {agency_data['basic_info']['price_range']}
            - Verified: {agency_data['basic_info']['verified']}
            - Active Status: {agency_data['basic_info']['is_active']}
            
            Location & Coordinates:
            - Latitude: {agency_data['location_details']['latitude']}
            - Longitude: {agency_data['location_details']['longitude']}
            
            Features & Capabilities:
            - Specialties: {agency_data['features']['specialties']}
            - Languages Spoken: {agency_data['features']['languages_spoken']}
            - Group Size Range: {agency_data['features']['group_size_range']}
            - Operating Hours: {agency_data['features']['operating_hours']}
            
            Ratings & Reviews:
            - Average Rating: {agency_data['ratings']['average_rating']}/5
            - Total Ratings: {agency_data['ratings']['total_ratings']}
            
            Social Media:
            - Facebook: {agency_data['social_media']['facebook']}
            - Twitter: {agency_data['social_media']['twitter']}
            - Instagram: {agency_data['social_media']['instagram']}
            - LinkedIn: {agency_data['social_media']['linkedin']}
            
            Certifications:
            - Certifications: {agency_data['certifications']['certifications']}
            
            SERVICES OFFERED:
            =================
            """
            
            if services_data:
                context += f"Number of Services: {len(services_data)}\n"
                for service in services_data:
                    context += f"\nService: {service['name']} ({service['service_type']})\n"
                    context += f"Description: {service['description']}\n"
                    context += f"Availability: {service['availability']}\n"
                    context += f"Featured: {'Yes' if service['is_featured'] else 'No'}\n"
                    context += f"Base Price: {service['base_price']}\n"
                    if service['price_range_min'] != 'Not specified' and service['price_range_max'] != 'Not specified':
                        context += f"Price Range: Ksh {service['price_range_min']} - {service['price_range_max']}\n"
                    context += f"Pricing Model: {service['pricing_model']}\n"
                    context += f"Duration: {service['duration']}\n"
                    context += f"Group Size: {service['group_size_min']} - {service['group_size_max']}\n"
                    context += f"Requirements: {service['requirements']}\n"
                    context += f"Included: {service['included_items']}\n"
                    context += f"Excluded: {service['excluded_items']}\n"
                    context += f"Cancellation Policy: {service['cancellation_policy']}\n"
            else:
                context += "No services information available.\n"
            
            context += f"""
            
            GALLERY & MEDIA:
            ================
            Number of Gallery Images: {len(gallery_data)}
            Featured Images: {sum(1 for img in gallery_data if img['is_featured'])}
            
            OWNER INFORMATION:
            ==================
            Owner: {agency.owner.username if agency.owner else 'Not specified'}
            """
            
            print("Context created successfully")
        except Exception as e:
            print(f"Error creating context: {e}")
            return JsonResponse({
                'success': False, 
                'error': f'Error creating context: {str(e)}'
            }, status=500)
        
        # Create the enhanced prompt for OpenAI
        prompt = f"""
        You are a knowledgeable AI travel assistant for {agency.name}, a {agency.get_agency_type_display()} located in {agency.city}, {agency.country}.
        
        You have access to comprehensive information about this agency including:
        - Basic details and description
        - Services offered with pricing, duration, and policies
        - Operating hours and specialties
        - Languages spoken and group size capabilities
        - Ratings and reviews
        - Social media presence
        - Certifications and verification status
        
        Here is the complete information:
        {context}
        
        A visitor is asking: "{question}"
        
        Please provide a helpful, informative, and accurate response based on the information above. 
        - If the information is available, provide detailed and helpful answers
        - If the information is not available, politely say so and suggest they contact the agency directly
        - For service questions, mention pricing in Kenyan Shillings (Ksh) when available
        - For pricing questions, include both base price and price ranges if available
        - Keep your response friendly, helpful, and under 250 words
        - Focus on being informative about the agency's services, capabilities, policies, and contact information
        - If asked about pricing, always mention the currency (Ksh)
        - Highlight the agency's specialties and unique offerings
        """
        
        # Configure OpenAI API key
        print(f"Setting OpenAI API key: {settings.OPENAI_API_KEY[:20]}...")
        openai.api_key = settings.OPENAI_API_KEY
            
        # Get response from OpenAI
        try:
            print("Making OpenAI API call...")
            # Use the new OpenAI API (v1.0.0+)
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI travel assistant that provides accurate information about travel agencies and their services. You have access to comprehensive data about the agency including services, pricing, policies, and capabilities. Always be helpful, accurate, and informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            response_time = (timezone.now() - start_time).total_seconds() * 1000  # Convert to milliseconds
            print("OpenAI API call successful")
            
            # Calculate tokens and cost (rough estimates)
            response_tokens = len(ai_response.split())
            total_tokens = chat_question.question_tokens + response_tokens
            cost_usd = (total_tokens / 1000) * 0.002  # Rough cost estimate for GPT-3.5-turbo
            
            # Save the AI response
            try:
                ChatResponse.objects.create(
                    question=chat_question,
                    response=ai_response,
                    response_tokens=response_tokens,
                    ai_model='gpt-3.5-turbo',
                    model_version='3.5',
                    response_time_ms=int(response_time),
                    total_tokens=total_tokens,
                    cost_usd=cost_usd
                )
                print(f"Chat response saved successfully")
            except Exception as save_error:
                print(f"Error saving chat response: {save_error}")
            
            return JsonResponse({
                'success': True,
                'response': ai_response
            })
            
        except Exception as openai_error:
            print(f"OpenAI API error: {openai_error}")
            print(f"Error type: {type(openai_error)}")
            print(f"Error details: {str(openai_error)}")
            # Enhanced fallback response with available data
            fallback_response = f"I'm sorry, I'm having trouble processing your question right now. However, I can tell you that {agency.name} is a {agency.get_agency_type_display()} located in {agency.city}, {agency.country}. "
            
            if services_data:
                fallback_response += f"They offer {len(services_data)} services including various travel and tour options. "
            
            fallback_response += f"For specific information about '{question}', I recommend contacting them directly at {agency.phone} or {agency.email}."
            
            # Save fallback response if question was saved
            if 'chat_question' in locals():
                try:
                    ChatResponse.objects.create(
                        question=chat_question,
                        response=fallback_response,
                        response_tokens=len(fallback_response.split()),
                        ai_model='fallback',
                        response_time_ms=0,
                        total_tokens=chat_question.question_tokens,
                        cost_usd=0
                    )
                except Exception as save_error:
                    print(f"Error saving fallback response: {save_error}")
            
            return JsonResponse({
                'success': True,
                'response': fallback_response
            })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Agency chat error: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

def generate_fallback_response(question, agency):
    """
    Generate a fallback response when OpenAI is not available
    """
    question_lower = question.lower()
    
    # Basic keyword matching for common questions
    if any(word in question_lower for word in ['service', 'offer', 'provide']):
        if agency.services.exists():
            services_list = ", ".join([service.name for service in agency.services.all()])
            return f"{agency.name} offers the following services: {services_list}. For more detailed information about each service, please contact them directly."
        else:
            return f"{agency.name} is a travel agency, but I don't have specific information about their current services. Please contact them directly for the most up-to-date service offerings."
    
    elif any(word in question_lower for word in ['price', 'cost', 'fee', 'rate']):
        return f"I don't have specific pricing information for {agency.name}'s services. Pricing can vary based on the service, season, and other factors. Please contact them directly for accurate pricing quotes."
    
    elif any(word in question_lower for word in ['location', 'where', 'address']):
        return f"{agency.name} is located at {agency.address}, {agency.city}, {agency.country}. You can contact them at {agency.phone} or {agency.email} for directions or to schedule a visit."
    
    elif any(word in question_lower for word in ['contact', 'phone', 'email', 'reach']):
        return f"You can contact {agency.name} at {agency.phone} or {agency.email}. They're located at {agency.address}, {agency.city}, {agency.country}."
    
    elif any(word in question_lower for word in ['policy', 'cancellation', 'refund']):
        return f"I don't have specific information about {agency.name}'s policies regarding cancellations, refunds, or other terms. Please contact them directly for their current policies and terms of service."
    
    elif any(word in question_lower for word in ['hour', 'time', 'open', 'available']):
        return f"I don't have specific information about {agency.name}'s business hours. Please contact them directly at {agency.phone} or {agency.email} to confirm their current operating hours."
    
    else:
        return f"Thank you for your question about {agency.name}. While I don't have specific information about that, I can tell you they're a {agency.get_agency_type_display()} located in {agency.city}, {agency.country}. For detailed information, please contact them directly at {agency.phone} or {agency.email}."

@login_required
@require_POST
def upload_place_gallery_image(request, place_id):
    """Upload a new image to place gallery"""
    try:
        place = get_object_or_404(Place, pk=place_id)
        
        # Check if user owns the place
        if place.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        form = PlaceGalleryForm(request.POST, request.FILES)
        if form.is_valid():
            gallery_image = form.save(commit=False)
            gallery_image.place = place
            gallery_image.save()
            
            return JsonResponse({
                'success': True,
                'image_id': gallery_image.id,
                'image_url': gallery_image.get_image_url(),
                'caption': gallery_image.caption,
                'message': 'Image uploaded successfully'
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_place_gallery_image(request, place_id, image_id):
    """Delete an image from place gallery"""
    try:
        place = get_object_or_404(Place, pk=place_id)
        gallery_image = get_object_or_404(PlaceGallery, pk=image_id, place=place)
        
        # Check if user owns the place
        if place.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        gallery_image.delete()
        return JsonResponse({'success': True, 'message': 'Image deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def reorder_place_gallery(request, place_id):
    """Reorder place gallery images"""
    try:
        place = get_object_or_404(Place, pk=place_id)
        
        # Check if user owns the place
        if place.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        image_orders = data.get('image_orders', [])
        
        for item in image_orders:
            image_id = item.get('id')
            new_order = item.get('order')
            if image_id and new_order is not None:
                PlaceGallery.objects.filter(id=image_id, place=place).update(order=new_order)
        
        return JsonResponse({'success': True, 'message': 'Gallery reordered successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def upload_agency_gallery_image(request, agency_id):
    """Upload a new image to agency gallery"""
    try:
        agency = get_object_or_404(Agency, pk=agency_id)
        
        # Check if user owns the agency
        if agency.owner != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        form = AgencyGalleryForm(request.POST, request.FILES)
        if form.is_valid():
            gallery_image = form.save(commit=False)
            gallery_image.agency = agency
            gallery_image.save()
            
            return JsonResponse({
                'success': True,
                'image_id': gallery_image.id,
                'image_url': gallery_image.get_image_url(),
                'caption': gallery_image.caption,
                'message': 'Image uploaded successfully'
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_agency_gallery_image(request, agency_id, image_id):
    """Delete an image from agency gallery"""
    try:
        agency = get_object_or_404(Agency, pk=agency_id)
        gallery_image = get_object_or_404(AgencyGallery, pk=image_id, agency=agency)
        
        # Check if user owns the agency
        if agency.owner != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        gallery_image.delete()
        return JsonResponse({'success': True, 'message': 'Image deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def reorder_agency_gallery(request, agency_id):
    """Reorder agency gallery images"""
    try:
        agency = get_object_or_404(Agency, pk=agency_id)
        
        # Check if user owns the agency
        if agency.owner != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        image_orders = data.get('image_orders', [])
        
        for item in image_orders:
            image_id = item.get('id')
            new_order = item.get('order')
            if image_id and new_order is not None:
                AgencyGallery.objects.filter(id=image_id, agency=agency).update(order=new_order)
        
        return JsonResponse({'success': True, 'message': 'Gallery reordered successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def enhanced_place_search(request):
    """Enhanced search view for places with multiple filters"""
    
    # Get search form
    search_form = PlaceSearchForm(request.GET)
    
    # Start with all places
    places = Place.objects.filter(is_active=True)
    
    if search_form.is_valid():
        # Basic search query
        search_query = search_form.cleaned_data.get('search_query')
        if search_query:
            places = places.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        
        # Category filter
        category = search_form.cleaned_data.get('category')
        if category:
            places = places.filter(category=category)
        
        # Price range filter
        price_range = search_form.cleaned_data.get('price_range')
        if price_range:
            places = places.filter(price_range=price_range)
        
        # Duration filter
        max_duration = search_form.cleaned_data.get('max_duration')
        if max_duration:
            places = places.filter(average_visit_duration__lte=int(max_duration))
        
        # Location filter
        location = search_form.cleaned_data.get('location')
        if location:
            places = places.filter(
                Q(location__icontains=location) |
                Q(address__icontains=location)
            )
        
        # Family friendly filter
        family_friendly = search_form.cleaned_data.get('family_friendly')
        if family_friendly:
            places = places.filter(family_friendly=True)
        
        # Pet friendly filter
        pet_friendly = search_form.cleaned_data.get('pet_friendly')
        if pet_friendly:
            places = places.filter(pet_friendly=True)
        
        # Accessibility features filter
        accessibility_features = search_form.cleaned_data.get('accessibility_features')
        if accessibility_features:
            for feature in accessibility_features:
                places = places.filter(accessibility_features__contains=[feature])
        
        # Amenities filter
        amenities = search_form.cleaned_data.get('amenities')
        if amenities:
            for amenity in amenities:
                places = places.filter(amenities__contains=[amenity])
        
        # Rating filter
        min_rating = search_form.cleaned_data.get('min_rating')
        if min_rating:
            min_rating_int = int(min_rating)
            places = places.annotate(
                avg_rating=Avg('ratings__rating')
            ).filter(avg_rating__gte=min_rating_int)
        
        # Sort results
        sort_by = search_form.cleaned_data.get('sort_by', '-created_at')
        
        # Debug logging
        print(f"DEBUG: sort_by value: '{sort_by}' (type: {type(sort_by)})")
        
        # Validate sort_by is not empty and is a valid field
        if sort_by and str(sort_by).strip():
            sort_by = str(sort_by).strip()
            
            if sort_by == 'average_rating':
                places = places.annotate(
                    avg_rating=Avg('ratings__rating')
                ).order_by('-avg_rating')
            elif sort_by == '-average_rating':
                places = places.annotate(
                    avg_rating=Avg('ratings__rating')
                ).order_by('avg_rating')
            elif sort_by == 'price_range':
                # Custom ordering for price ranges
                places = places.annotate(
                    price_order=Case(
                        When(price_range='free', then=Value(1)),
                        When(price_range='low', then=Value(2)),
                        When(price_range='medium', then=Value(3)),
                        When(price_range='high', then=Value(4)),
                        When(price_range='luxury', then=Value(5)),
                        default=Value(6),
                        output_field=IntegerField(),
                    )
                ).order_by('price_order')
            elif sort_by == '-price_range':
                places = places.annotate(
                    price_order=Case(
                        When(price_range='free', then=Value(1)),
                        When(price_range='low', then=Value(2)),
                        When(price_range='medium', then=Value(3)),
                        When(price_range='high', then=Value(4)),
                        When(price_range='luxury', then=Value(5)),
                        default=Value(6),
                        output_field=IntegerField(),
                    )
                ).order_by('-price_order')
            else:
                # Validate that the field exists before ordering
                try:
                    # Check if the field exists in the model
                    if hasattr(Place._meta, 'get_field'):
                        field_name = sort_by.lstrip('-')  # Remove minus sign for field validation
                        Place._meta.get_field(field_name)
                        places = places.order_by(sort_by)
                    else:
                        places = places.order_by('-created_at')
                except Exception as e:
                    print(f"DEBUG: Error ordering by {sort_by}: {e}")
                    # Fallback to default ordering if field doesn't exist
                    places = places.order_by('-created_at')
        else:
            print(f"DEBUG: Using default ordering, sort_by was: '{sort_by}'")
            # Default ordering if no sort specified
            places = places.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(places, 12)  # Show 12 places per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for the filter
    categories = PlaceCategory.objects.all()
    
    # Get filter counts for active filters
    active_filters = {}
    if search_form.is_valid():
        for field_name, value in search_form.cleaned_data.items():
            if value and value != '' and value != []:
                active_filters[field_name] = value
    
    context = {
        'search_form': search_form,
        'page_obj': page_obj,
        'categories': categories,
        'active_filters': active_filters,
        'total_results': places.count(),
        'search_performed': bool(request.GET),
    }
    
    return render(request, 'listings/enhanced_place_search.html', context)

@require_http_methods(["POST"])
def place_chat(request, place_id):
    """AI chat endpoint for places with comprehensive context"""
    start_time = timezone.now()
    
    try:
        # Debug logging
        print(f"Place chat called for place_id: {place_id}")
        
        # Get the place with all related data
        place = get_object_or_404(Place, pk=place_id)
        print(f"Place found: {place.name}")
        
        # Parse the request data
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        print(f"Question received: {question}")
        
        if not question:
            return JsonResponse({'success': False, 'error': 'Question is required'}, status=400)
        
        # Get user information and session data
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key or f"anon_{uuid.uuid4().hex[:16]}"
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create ChatQuestion record
        try:
            from core.models import ChatQuestion, ChatResponse
            
            chat_question = ChatQuestion.objects.create(
                chat_type='place',
                place=place,
                user=user,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                question=question,
                question_tokens=len(question.split())  # Rough token estimation
            )
            print(f"Chat question saved with ID: {chat_question.id}")
        except Exception as e:
            print(f"Error saving chat question: {e}")
            # Continue without saving if there's an error
        
        # Import openai when needed
        try:
            import openai
            print("OpenAI imported successfully!")
        except Exception as e:
            print(f"OpenAI import failed: {e}")
            fallback_response = f"I'm sorry, but I'm currently offline. However, I can tell you about {place.name} based on the information I have: {place.description[:200]}..."
            
            # Save fallback response if question was saved
            if 'chat_question' in locals():
                try:
                    ChatResponse.objects.create(
                        question=chat_question,
                        response=fallback_response,
                        response_tokens=len(fallback_response.split()),
                        ai_model='fallback',
                        response_time_ms=0,
                        total_tokens=chat_question.question_tokens,
                        cost_usd=0
                    )
                except Exception as save_error:
                    print(f"Error saving fallback response: {save_error}")
            
            return JsonResponse({
                'success': True, 
                'response': fallback_response
            })
        
        print("OpenAI is available, proceeding with API call")
        
        # Gather comprehensive place data
        try:
            place_data = {
                'basic_info': {
                    'name': place.name,
                    'category': place.category.name if place.category else 'Not specified',
                    'description': place.description,
                    'location': place.location,
                    'address': place.address if place.address else 'Not specified',
                    'contact_email': place.contact_email if place.contact_email else 'Not specified',
                    'contact_phone': place.contact_phone if place.contact_phone else 'Not specified',
                    'website': place.website if place.website else 'Not specified',
                    'price_range': place.get_price_range_display() if place.price_range else 'Not specified',
                    'best_time_to_visit': place.best_time_to_visit if place.best_time_to_visit else 'Not specified',
                    'average_visit_duration': f"{place.average_visit_duration} hours" if place.average_visit_duration else 'Not specified',
                    'peak_season': place.peak_season if place.peak_season else 'Not specified',
                    'family_friendly': 'Yes' if place.family_friendly else 'No',
                    'pet_friendly': 'Yes' if place.pet_friendly else 'No',
                    'verified': 'Yes' if place.verified else 'No',
                    'is_active': 'Yes' if place.is_active else 'No'
                },
                'location_details': {
                    'latitude': str(place.latitude) if place.latitude else 'Not specified',
                    'longitude': str(place.longitude) if place.longitude else 'Not specified'
                },
                'features': {
                    'accessibility_features': ', '.join(place.accessibility_features) if place.accessibility_features else 'None available',
                    'amenities': ', '.join(place.amenities) if place.amenities else 'None available',
                    'opening_hours': place.opening_hours if place.opening_hours else 'Not specified'
                },
                'ratings': {
                    'average_rating': place.average_rating,
                    'total_ratings': place.total_ratings,
                    'rating_distribution': place.rating_distribution
                }
            }
            print("Place data gathered successfully")
        except Exception as e:
            print(f"Error gathering place data: {e}")
            return JsonResponse({
                'success': False, 
                'error': f'Error processing place data: {str(e)}'
            }, status=500)
        
        # Get menu categories and items
        try:
            menu_categories = place.menu_categories.filter(is_active=True).prefetch_related('menu_items')
            menu_data = []
            for category in menu_categories:
                category_items = []
                for item in category.menu_items.filter(is_active=True):
                    item_data = {
                        'name': item.name,
                        'description': item.description,
                        'price': str(item.price),
                        'discounted_price': str(item.discounted_price) if item.discounted_price else None,
                        'is_discounted': item.is_discounted,
                        'ingredients': item.ingredients if item.ingredients else 'Not specified',
                        'allergens': item.allergens if item.allergens else 'None',
                        'spice_level': item.get_spice_level_display() if item.spice_level else 'Not specified',
                        'preparation_time': f"{item.preparation_time} minutes" if item.preparation_time else 'Not specified',
                        'serving_size': item.serving_size if item.serving_size else 'Not specified',
                        'availability': item.get_availability_display(),
                        'dietary_info': {
                            'is_vegetarian': item.is_vegetarian,
                            'is_vegan': item.is_vegan,
                            'is_gluten_free': item.is_gluten_free,
                            'is_halal': item.is_halal,
                            'is_kosher': item.is_kosher
                        }
                    }
                    category_items.append(item_data)
                
                menu_data.append({
                    'category_name': category.name,
                    'category_type': category.get_category_type_display(),
                    'category_description': category.description if category.description else 'No description',
                    'items': category_items
                })
            print("Menu data gathered successfully")
        except Exception as e:
            print(f"Error gathering menu data: {e}")
            menu_data = []
        
        # Get features
        try:
            features = place.features.filter(is_active=True)
            features_data = []
            for feature in features:
                feature_data = {
                    'name': feature.name,
                    'description': feature.description if feature.description else 'No description',
                    'price': str(feature.price),
                    'duration': feature.display_duration
                }
                features_data.append(feature_data)
            print("Features data gathered successfully")
        except Exception as e:
            print(f"Error gathering features data: {e}")
            features_data = []
        
        # Get gallery images
        try:
            gallery_images = place.place_gallery_images.all()
            gallery_data = []
            for image in gallery_images:
                gallery_data.append({
                    'caption': image.caption if image.caption else 'Gallery image',
                    'is_featured': image.is_featured
                })
            print("Gallery data gathered successfully")
        except Exception as e:
            print(f"Error gathering gallery data: {e}")
            gallery_data = []
        
        # Get staff information
        try:
            staff = place.staff_members.filter(is_active=True)
            staff_data = []
            for member in staff:
                staff_data.append({
                    'name': member.user.username,
                    'role': member.role,
                    'bio': member.notes if member.notes else 'No bio available'
                })
            print("Staff data gathered successfully")
        except Exception as e:
            print(f"Error gathering staff data: {e}")
            staff_data = []
        
        # Create comprehensive context
        try:
            context = f"""
            PLACE INFORMATION:
            ==================
            Basic Details:
            - Name: {place_data['basic_info']['name']}
            - Category: {place_data['basic_info']['category']}
            - Description: {place_data['basic_info']['description']}
            - Location: {place_data['basic_info']['location']}
            - Address: {place_data['basic_info']['address']}
            - Contact Email: {place_data['basic_info']['contact_email']}
            - Contact Phone: {place_data['basic_info']['contact_phone']}
            - Website: {place_data['basic_info']['website']}
            - Price Range: {place_data['basic_info']['price_range']}
            - Best Time to Visit: {place_data['basic_info']['best_time_to_visit']}
            - Average Visit Duration: {place_data['basic_info']['average_visit_duration']}
            - Peak Season: {place_data['basic_info']['peak_season']}
            - Family Friendly: {place_data['basic_info']['family_friendly']}
            - Pet Friendly: {place_data['basic_info']['pet_friendly']}
            - Verified: {place_data['basic_info']['verified']}
            - Status: {place_data['basic_info']['is_active']}
            
            Location & Coordinates:
            - Latitude: {place_data['location_details']['latitude']}
            - Longitude: {place_data['location_details']['longitude']}
            
            Features & Amenities:
            - Accessibility Features: {place_data['features']['accessibility_features']}
            - Amenities: {place_data['features']['amenities']}
            - Opening Hours: {place_data['features']['opening_hours']}
            
            Ratings & Reviews:
            - Average Rating: {place_data['ratings']['average_rating']}/5
            - Total Ratings: {place_data['ratings']['total_ratings']}
            
            MENU INFORMATION:
            =================
            """
            
            if menu_data:
                context += f"Number of Menu Categories: {len(menu_data)}\n"
                for category in menu_data:
                    context += f"\nCategory: {category['category_name']} ({category['category_type']})\n"
                    context += f"Description: {category['category_description']}\n"
                    context += f"Number of Items: {len(category['items'])}\n"
                    
                    for item in category['items']:
                        context += f"  - {item['name']}: Ksh {item['price']}"
                        if item['is_discounted'] and item['discounted_price']:
                            context += f" (Discounted: Ksh {item['discounted_price']})"
                        context += f"\n    Description: {item['description']}\n"
                        context += f"    Preparation Time: {item['preparation_time']}\n"
                        context += f"    Serving Size: {item['serving_size']}\n"
                        context += f"    Availability: {item['availability']}\n"
                        context += f"    Dietary: Vegetarian: {item['dietary_info']['is_vegetarian']}, Vegan: {item['dietary_info']['is_vegan']}, Gluten-Free: {item['dietary_info']['is_gluten_free']}\n"
            else:
                context += "No menu information available.\n"
            
            context += f"""
            
            FEATURES & SERVICES:
            ====================
            """
            
            if features_data:
                context += f"Number of Features: {len(features_data)}\n"
                for feature in features_data:
                    context += f"- {feature['name']}: Ksh {feature['price']} ({feature['duration']})\n"
                    context += f"  Description: {feature['description']}\n"
            else:
                context += "No additional features available.\n"
            
            context += f"""
            
            GALLERY & MEDIA:
            ================
            Number of Gallery Images: {len(gallery_data)}
            Featured Images: {sum(1 for img in gallery_data if img['is_featured'])}
            
            STAFF INFORMATION:
            ==================
            """
            
            if staff_data:
                context += f"Number of Staff Members: {len(staff_data)}\n"
                for member in staff_data:
                    context += f"- {member['name']} ({member['role']}): {member['bio']}\n"
            else:
                context += "No staff information available.\n"
            
            print("Context created successfully")
        except Exception as e:
            print(f"Error creating context: {e}")
            return JsonResponse({
                'success': False, 
                'error': f'Error creating context: {str(e)}'
            }, status=500)
        
        # Create the prompt for OpenAI
        prompt = f"""
        {context}
        
        USER QUESTION: {question}
        
        Please provide a helpful, informative response about {place.name} based on the information above. 
        Focus on answering the specific question asked and provide relevant details from the available data.
        If the question is about pricing, always mention prices in Kenyan Shillings (Ksh).
        Be conversational but professional, and encourage the user to visit or contact {place.name}.
        """
        
        # Get response from OpenAI
        try:
            print("Making OpenAI API call...")
            # Set OpenAI API key
            openai.api_key = settings.OPENAI_API_KEY
            # Use the new OpenAI API (v1.0.0+)
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI travel assistant that provides accurate information about travel destinations and places. You have access to comprehensive data about the place including menu items, features, pricing, and policies. Always be helpful, accurate, and informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            response_time = (timezone.now() - start_time).total_seconds() * 1000  # Convert to milliseconds
            
            # Calculate tokens and cost (rough estimates)
            response_tokens = len(ai_response.split())
            total_tokens = chat_question.question_tokens + response_tokens
            cost_usd = (total_tokens / 1000) * 0.002  # Rough cost estimate for GPT-3.5-turbo
            
            # Save the AI response
            try:
                ChatResponse.objects.create(
                    question=chat_question,
                    response=ai_response,
                    response_tokens=response_tokens,
                    ai_model='gpt-3.5-turbo',
                    model_version='3.5',
                    response_time_ms=int(response_time),
                    total_tokens=total_tokens,
                    cost_usd=cost_usd
                )
                print(f"Chat response saved successfully")
            except Exception as save_error:
                print(f"Error saving chat response: {save_error}")
            
            return JsonResponse({
                'success': True,
                'response': ai_response
            })
            
        except Exception as openai_error:
            print(f"OpenAI API error: {openai_error}")
            print(f"Error type: {type(openai_error)}")
            print(f"Error details: {str(openai_error)}")
            # Enhanced fallback response with available data
            fallback_response = f"I'm sorry, I'm having trouble processing your question right now. However, I can tell you that {place.name} is a {place.category.name if place.category else 'travel destination'} located in {place.location}. "
            
            if menu_data:
                fallback_response += f"They offer {len(menu_data)} menu categories with various food and beverage options. "
            
            if features_data:
                fallback_response += f"They also provide {len(features_data)} additional features and services. "
            
            fallback_response += f"For specific information about '{question}', I recommend contacting them directly at {place.contact_phone if place.contact_phone else place.contact_email if place.contact_email else 'their website'}."
            
            # Save fallback response if question was saved
            if 'chat_question' in locals():
                try:
                    ChatResponse.objects.create(
                        question=chat_question,
                        response=fallback_response,
                        response_tokens=len(fallback_response.split()),
                        ai_model='fallback',
                        response_time_ms=0,
                        total_tokens=chat_question.question_tokens,
                        cost_usd=0
                    )
                except Exception as save_error:
                    print(f"Error saving fallback response: {save_error}")
            
            return JsonResponse({
                'success': True,
                'response': fallback_response
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Place chat error: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

# Date Planner Views
class DatePlannerDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for date planning"""
    template_name = 'listings/date_planner_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's date plans
        context['date_plans'] = DatePlan.objects.filter(creator=user).order_by('-created_at')
        context['active_plans'] = context['date_plans'].filter(status='active')
        context['upcoming_plans'] = context['date_plans'].filter(
            planned_date__gte=date.today(),
            status__in=['draft', 'active']
        ).order_by('planned_date')
        
        # Get user preferences
        context['preferences'], created = DatePlanPreference.objects.get_or_create(user=user)
        
        # Get AI suggestions
        context['ai_suggestions'] = DatePlanSuggestion.objects.filter(
            user=user, 
            status='pending'
        ).order_by('-created_at')[:5]
        
        return context


class DatePlanCreateView(LoginRequiredMixin, CreateView):
    """View for creating new date plans"""
    model = DatePlan
    form_class = DatePlanForm
    template_name = 'listings/date_plan_form.html'
    success_url = reverse_lazy('date_planner_dashboard')
    
    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.success(self.request, 'Date plan created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Date Plan'
        context['submit_text'] = 'Create Plan'
        return context


class DatePlanUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for editing existing date plans"""
    model = DatePlan
    form_class = DatePlanForm
    template_name = 'listings/date_plan_form.html'
    
    def test_func(self):
        date_plan = self.get_object()
        return date_plan.creator == self.request.user
    
    def get_success_url(self):
        return reverse('date_plan_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Date plan updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Date Plan'
        context['submit_text'] = 'Update Plan'
        return context


class DatePlanDetailView(LoginRequiredMixin, DetailView):
    """View for displaying date plan details"""
    model = DatePlan
    template_name = 'listings/date_plan_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_plan = self.get_object()
        
        # Check if user can edit this plan
        context['can_edit'] = date_plan.creator == self.request.user
        
        # Get activities ordered by time
        context['activities'] = date_plan.activities.all().order_by('order', 'start_time')
        
        # Get collaborators
        context['collaborators'] = date_plan.collaborators.all()
        
        return context


class DatePlanDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting date plans"""
    model = DatePlan
    template_name = 'listings/date_plan_confirm_delete.html'
    success_url = reverse_lazy('date_planner_dashboard')
    
    def test_func(self):
        date_plan = self.get_object()
        return date_plan.creator == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Date plan deleted successfully!')
        return super().delete(request, *args, **kwargs)


class DateActivityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for adding activities to date plans"""
    model = DateActivity
    form_class = DateActivityForm
    template_name = 'listings/date_activity_form.html'
    
    def test_func(self):
        date_plan = DatePlan.objects.get(pk=self.kwargs['plan_pk'])
        return date_plan.creator == self.request.user
    
    def form_valid(self, form):
        form.instance.date_plan_id = self.kwargs['plan_pk']
        
        # Set order if not provided
        if not form.instance.order:
            last_activity = DateActivity.objects.filter(
                date_plan_id=self.kwargs['plan_pk']
            ).order_by('-order').first()
            form.instance.order = (last_activity.order + 1) if last_activity else 0
        
        messages.success(self.request, 'Activity added successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('date_plan_detail', kwargs={'pk': self.kwargs['plan_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_plan'] = DatePlan.objects.get(pk=self.kwargs['plan_pk'])
        context['title'] = 'Add Activity'
        context['submit_text'] = 'Add Activity'
        return context


class DateActivityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for editing date activities"""
    model = DateActivity
    form_class = DateActivityForm
    template_name = 'listings/date_activity_form.html'
    
    def test_func(self):
        activity = self.get_object()
        return activity.date_plan.creator == self.request.user
    
    def get_success_url(self):
        return reverse('date_plan_detail', kwargs={'pk': self.object.date_plan.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Activity updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_plan'] = self.object.date_plan
        context['title'] = 'Edit Activity'
        context['submit_text'] = 'Update Activity'
        return context


class DateActivityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting date activities"""
    model = DateActivity
    template_name = 'listings/date_activity_confirm_delete.html'
    
    def test_func(self):
        activity = self.get_object()
        return activity.date_plan.creator == self.request.user
    
    def get_success_url(self):
        return reverse('date_plan_detail', kwargs={'pk': self.object.date_plan.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Activity deleted successfully!')
        return super().delete(request, *args, **kwargs)


class DatePlanPreferenceView(LoginRequiredMixin, UpdateView):
    """View for managing date planning preferences"""
    model = DatePlanPreference
    form_class = DatePlanPreferenceForm
    template_name = 'listings/date_plan_preferences.html'
    success_url = reverse_lazy('date_planner_dashboard')
    
    def get_object(self, queryset=None):
        obj, created = DatePlanPreference.objects.get_or_create(user=self.request.user)
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Preferences updated successfully!')
        return super().form_valid(form)


class DatePlanSuggestionView(LoginRequiredMixin, TemplateView):
    """View for requesting AI-generated date plan suggestions"""
    template_name = 'listings/date_plan_suggestion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suggestion_form'] = DatePlanSuggestionForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = DatePlanSuggestionForm(request.POST)
        if form.is_valid():
            # Generate AI suggestion
            suggestion = self.generate_ai_suggestion(form.cleaned_data, request.user)
            if suggestion:
                messages.success(request, 'AI suggestion generated successfully!')
                return redirect('date_plan_suggestion_detail', pk=suggestion.pk)
            else:
                messages.error(request, 'Failed to generate AI suggestion. Please try again.')
        
        context = self.get_context_data()
        context['suggestion_form'] = form
        return self.render_to_response(context)
    
    def generate_ai_suggestion(self, data, user):
        """Generate AI suggestion for date plan"""
        try:
            # Create the suggestion record
            suggestion = DatePlanSuggestion.objects.create(
                user=user,
                title=f"AI Suggested {data['suggestion_type'].title()} Plan",
                description=self.create_ai_description(data),
                suggested_date=data['date'],
                estimated_duration=data['duration'],
                estimated_cost=data.get('budget'),
                suggested_activities=self.generate_activity_suggestions(data),
                ai_prompt=self.create_ai_prompt(data)
            )
            return suggestion
        except Exception as e:
            print(f"Error generating AI suggestion: {e}")
            return None
    
    def create_ai_description(self, data):
        """Create description for AI suggestion"""
        return f"AI-generated {data['suggestion_type']} plan for {data['date']} in {data['location']}. " \
               f"Duration: {data['duration']} hours, Group size: {data['group_size']} people."
    
    def create_ai_prompt(self, data):
        """Create the AI prompt used for generation"""
        return f"Create a {data['suggestion_type']} plan for {data['date']} in {data['location']}. " \
               f"Duration: {data['duration']} hours, Group size: {data['group_size']} people. " \
               f"Preferences: {data.get('preferences', 'None')}"
    
    def generate_activity_suggestions(self, data):
        """Generate suggested activities based on plan type and preferences"""
        # This would typically call an AI service
        # For now, return basic suggestions
        suggestions = []
        
        if data['suggestion_type'] == 'romantic':
            suggestions = ['Romantic dinner', 'Sunset walk', 'Couple massage']
        elif data['suggestion_type'] == 'family':
            suggestions = ['Family lunch', 'Park visit', 'Museum tour']
        elif data['suggestion_type'] == 'food':
            suggestions = ['Breakfast', 'Lunch', 'Dinner', 'Dessert']
        else:
            suggestions = ['Morning activity', 'Afternoon activity', 'Evening activity']
        
        return suggestions


class DatePlanSuggestionDetailView(LoginRequiredMixin, DetailView):
    """View for displaying AI-generated date plan suggestions"""
    model = DatePlanSuggestion
    template_name = 'listings/date_plan_suggestion_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suggestion = self.get_object()
        
        # Check if user can edit this suggestion
        context['can_edit'] = suggestion.user == self.request.user
        
        return context


@login_required
def accept_date_plan_suggestion(request, pk):
    """Accept an AI-generated date plan suggestion"""
    suggestion = get_object_or_404(DatePlanSuggestion, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Create a new date plan from the suggestion
        date_plan = DatePlan.objects.create(
            creator=request.user,
            title=suggestion.title,
            description=suggestion.description,
            planned_date=suggestion.suggested_date,
            plan_type='other',  # Default type
            group_size=2,  # Default group size
            location='',  # Will be filled by user
            budget=suggestion.estimated_cost
        )
        
        # Update suggestion status
        suggestion.status = 'accepted'
        suggestion.save()
        
        messages.success(request, 'Suggestion accepted! Date plan created successfully.')
        return redirect('date_plan_detail', pk=date_plan.pk)
    
    return redirect('date_plan_suggestion_detail', pk=pk)


@login_required
def reject_date_plan_suggestion(request, pk):
    """Reject an AI-generated date plan suggestion"""
    suggestion = get_object_or_404(DatePlanSuggestion, pk=pk, user=request.user)
    
    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        suggestion.status = 'rejected'
        suggestion.user_feedback = feedback
        suggestion.save()
        
        messages.success(request, 'Suggestion rejected successfully.')
        return redirect('date_planner_dashboard')
    
    return redirect('date_plan_suggestion_detail', pk=pk)


@login_required
def toggle_activity_completion(request, pk):
    """Toggle completion status of a date activity"""
    activity = get_object_or_404(DateActivity, pk=pk)
    
    # Check if user can modify this activity
    if activity.date_plan.creator != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    if request.method == 'POST':
        activity.is_completed = not activity.is_completed
        activity.save()
        
        return JsonResponse({
            'success': True,
            'is_completed': activity.is_completed,
            'message': 'Activity marked as completed' if activity.is_completed else 'Activity marked as incomplete'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def reorder_activities(request, plan_pk):
    """Reorder activities within a date plan"""
    date_plan = get_object_or_404(DatePlan, pk=plan_pk, creator=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            activity_orders = data.get('activity_orders', [])
            
            for item in activity_orders:
                activity_id = item.get('id')
                new_order = item.get('order')
                if activity_id and new_order is not None:
                    DateActivity.objects.filter(
                        id=activity_id, 
                        date_plan=date_plan
                    ).update(order=new_order)
            
            return JsonResponse({'success': True, 'message': 'Activities reordered successfully'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


class PublicDatePlansView(ListView):
    """View for browsing public date plans"""
    model = DatePlan
    template_name = 'listings/public_date_plans.html'
    context_object_name = 'date_plans'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = DatePlan.objects.filter(
            is_public=True,
            status='active',
            planned_date__gte=date.today()
        ).select_related('creator').prefetch_related('activities')
        
        # Filter by plan type
        plan_type = self.request.GET.get('plan_type')
        if plan_type:
            queryset = queryset.filter(plan_type=plan_type)
        
        # Filter by location
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(planned_date__gte=date_from)
            except ValueError:
                pass
        
        return queryset.order_by('planned_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plan_types'] = DatePlan.PLAN_TYPE_CHOICES
        return context

# Staff Management Views
@login_required
def add_place_staff(request, place_id):
    """Add a new staff member to a place"""
    place = get_object_or_404(Place, pk=place_id)
    
    # Check if user is the place owner
    if place.created_by != request.user:
        messages.error(request, 'You do not have permission to manage this place.')
        return redirect('user_place_detail', pk=place_id)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')
        notes = request.POST.get('notes', '')
        
        if not email or not role:
            messages.error(request, 'Email and role are required.')
            return redirect('user_place_detail', pk=place_id)
        
        # Check if user exists
        try:
            user = MyUser.objects.get(email=email)
        except MyUser.DoesNotExist:
            messages.error(request, f'No user found with email: {email}')
            return redirect('user_place_detail', pk=place_id)
        
        # Check if user is already staff at this place
        if PlaceStaff.objects.filter(place=place, user=user).exists():
            messages.error(request, f'{user.username} is already a staff member at this place.')
            return redirect('user_place_detail', pk=place_id)
        
        # Create staff member
        staff_member = PlaceStaff.objects.create(
            place=place,
            user=user,
            role=role,
            notes=notes,
            # Handle checkbox fields
            can_view_orders='can_view_orders' in request.POST,
            can_create_orders='can_create_orders' in request.POST,
            can_edit_orders='can_edit_orders' in request.POST,
            can_delete_orders='can_delete_orders' in request.POST,
            can_view_customers='can_view_customers' in request.POST,
            can_edit_menu='can_edit_menu' in request.POST,
            can_manage_staff='can_manage_staff' in request.POST,
            can_view_analytics='can_view_analytics' in request.POST,
            can_manage_settings='can_manage_settings' in request.POST
        )
        
        messages.success(request, f'{user.username} has been added as staff.')
        return redirect('user_place_detail', pk=place_id)
    
    return redirect('user_place_detail', pk=place_id)


@login_required
def edit_place_staff(request, place_id, staff_id):
    """Edit a staff member's permissions"""
    place = get_object_or_404(Place, pk=place_id)
    staff_member = get_object_or_404(PlaceStaff, pk=staff_id, place=place)
    
    # Check if user is the place owner
    if place.created_by != request.user:
        messages.error(request, 'You do not have permission to manage this place.')
        return redirect('public_place_detail', pk=place.pk)
    
    if request.method == 'POST':
        form = PlaceStaffForm(request.POST, instance=staff_member, place=place)
        if form.is_valid():
            staff_member = form.save(commit=False)
            
            # Handle checkbox fields
            staff_member.can_view_orders = 'can_view_orders' in request.POST
            staff_member.can_create_orders = 'can_create_orders' in request.POST
            staff_member.can_edit_orders = 'can_edit_orders' in request.POST
            staff_member.can_delete_orders = 'can_delete_orders' in request.POST
            staff_member.can_view_customers = 'can_view_customers' in request.POST
            staff_member.can_edit_menu = 'can_edit_menu' in request.POST
            staff_member.can_manage_staff = 'can_manage_staff' in request.POST
            staff_member.can_view_analytics = 'can_view_analytics' in request.POST
            staff_member.can_manage_settings = 'can_manage_settings' in request.POST
            
            staff_member.save()
            messages.success(request, f'{staff_member.user.username}\'s permissions have been updated.')
            return redirect('user_place_detail', pk=place.pk)
    
    # For now, redirect back to user place detail since we're not using a separate edit form
    return redirect('user_place_detail', pk=place.pk)


@login_required
def remove_place_staff(request, place_id, staff_id):
    """Remove a staff member from a place"""
    place = get_object_or_404(Place, pk=place_id)
    staff_member = get_object_or_404(PlaceStaff, pk=staff_id, place=place)
    
    # Check if user is the place owner
    if place.created_by != request.user:
        messages.error(request, 'You do not have permission to manage this place.')
        return redirect('user_place_detail', pk=place.pk)
    
    if request.method == 'POST':
        username = staff_member.user.username
        staff_member.delete()
        messages.success(request, f'{username} has been removed from staff.')
        return redirect('user_place_detail', pk=place_id)
    
    # For now, redirect back to user place detail since we're not using a separate remove form
    return redirect('user_place_detail', pk=place_id)


@login_required
def staff_dashboard(request, place_id):
    """Staff dashboard for managing orders at a place"""
    place = get_object_or_404(Place, pk=place_id)
    
    # Check if user is staff member or place owner
    if request.user != place.created_by:
        staff_member = PlaceStaff.objects.filter(place=place, user=request.user).first()
        if not staff_member:
            messages.error(request, 'You do not have access to this staff dashboard.')
            return redirect('public_place_detail', pk=place_id)
    
    # Get order statistics
    from datetime import date
    today = date.today()
    
    pending_orders_count = PlaceOrder.objects.filter(place=place, status='pending').count()
    in_progress_orders_count = PlaceOrder.objects.filter(
        place=place, 
        status__in=['confirmed', 'preparing']
    ).count()
    completed_today_count = PlaceOrder.objects.filter(
        place=place, 
        status__in=['completed', 'delivered'], 
        order_date__date=today
    ).count()
    
    # Calculate today's revenue
    from django.db.models import Sum
    today_revenue = PlaceOrder.objects.filter(
        place=place, 
        status__in=['completed', 'delivered'], 
        order_date__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get recent orders
    recent_orders = PlaceOrder.objects.filter(place=place).order_by('-order_date')[:5]
    
    context = {
        'place': place,
        'pending_orders_count': pending_orders_count,
        'in_progress_orders_count': in_progress_orders_count,
        'completed_today_count': completed_today_count,
        'today_revenue': today_revenue,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'listings/staff_dashboard.html', context)


@login_required
def place_orders_dashboard(request, place_id):
    """Dashboard for managing place orders"""
    place = get_object_or_404(Place, pk=place_id)
    
    # Check if user is the place owner or staff member
    if place.created_by != request.user:
        # Check if user is staff member
        try:
            staff_member = place.staff_members.get(user=request.user)
            if not staff_member.can_view_orders:
                messages.error(request, 'You do not have permission to view orders.')
                return redirect('public_place_detail', pk=place_id)
        except PlaceStaff.DoesNotExist:
            messages.error(request, 'You do not have permission to access this dashboard.')
            return redirect('public_place_detail', pk=place_id)
    
    # Get orders
    orders = place.orders.all().order_by('-order_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'place': place,
        'page_obj': page_obj,
        'orders': orders,
        'status_choices': PlaceOrder.ORDER_STATUS_CHOICES,
        'status_filter': status_filter,
    }
    
    return render(request, 'listings/place_orders_dashboard.html', context)


@login_required
def create_place_order(request, place_id):
    """Create a new order for a place"""
    place = get_object_or_404(Place, pk=place_id)
    
    # Check if user is the place owner or staff member with permission
    if place.created_by != request.user:
        try:
            staff_member = place.staff_members.get(user=request.user)
            if not staff_member.can_create_orders:
                messages.error(request, 'You do not have permission to create orders.')
                return redirect('staff_dashboard', place_id=place_id)
        except PlaceStaff.DoesNotExist:
            messages.error(request, 'You do not have permission to create orders.')
            return redirect('public_place_detail', pk=place_id)
    
    if request.method == 'POST':
        # Get form data
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        menu_items = request.POST.getlist('menu_items')
        quantities = request.POST.getlist('quantities')
        instructions = request.POST.getlist('instructions')
        
        print(f"DEBUG: customer_name={customer_name}")
        print(f"DEBUG: customer_phone={customer_phone}")
        print(f"DEBUG: menu_items={menu_items}")
        print(f"DEBUG: quantities={quantities}")
        print(f"DEBUG: instructions={instructions}")
        
        if not menu_items:
            messages.error(request, 'Please add at least one menu item to the order.')
            return redirect('create_place_order', place_id=place_id)
        
        try:
            # Create the order
            order = PlaceOrder.objects.create(
                place=place,
                customer=request.user,  # Use the staff member as customer for now
                customer_name=customer_name,
                customer_phone=customer_phone,
                status='pending',
                order_type='dine_in',  # Default to dine in
                subtotal=0,  # Will be calculated
                tax_amount=0,  # No tax for now
                delivery_fee=0,  # No delivery fee for now
                total_amount=0,  # Will be calculated
                party_size=1  # Default party size
            )
            
            print(f"DEBUG: Order created with ID: {order.id}")
            
            # Set staff member if user is staff
            if place.created_by != request.user:
                try:
                    staff_member = place.staff_members.get(user=request.user)
                    order.staff_member = staff_member
                    print(f"DEBUG: Staff member set: {staff_member}")
                except PlaceStaff.DoesNotExist:
                    print("DEBUG: No staff member found")
                    pass
            
            # Create order items
            total_amount = 0
            for i, item_id in enumerate(menu_items):
                try:
                    menu_item = MenuItem.objects.get(pk=item_id, place=place)
                    quantity = int(quantities[i]) if i < len(quantities) else 1
                    instruction = instructions[i] if i < len(instructions) else ""
                    
                    order_item = PlaceOrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        special_instructions=instruction,
                        total_price=menu_item.price * quantity
                    )
                    
                    print(f"DEBUG: Order item created: {order_item.menu_item.name} x {quantity}")
                    total_amount += order_item.total_price
                except (MenuItem.DoesNotExist, ValueError, IndexError) as e:
                    print(f"DEBUG: Error creating order item: {e}")
                    continue
            
            # Update order total and subtotal
            order.subtotal = total_amount
            order.total_amount = total_amount
            order.save()
            
            print(f"DEBUG: Order updated with total: {total_amount}")
            print(f"DEBUG: Final order status: {order.status}")
            
            messages.success(request, f'Order #{order.id} created successfully!')
            return redirect('staff_dashboard', place_id=place_id)
            
        except Exception as e:
            print(f"DEBUG: Error creating order: {e}")
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('create_place_order', place_id=place_id)
    
    # Get menu categories and items for the form
    from listings.models import MenuCategory
    menu_categories = MenuCategory.objects.filter(place=place).prefetch_related('menu_items')
    
    context = {
        'place': place,
        'menu_categories': menu_categories,
    }
    
    return render(request, 'listings/create_place_order.html', context)


@login_required
def edit_place_order(request, place_id, order_id):
    """Edit an existing order"""
    order = get_object_or_404(PlaceOrder, pk=order_id)
    place = get_object_or_404(Place, pk=place_id)
    
    # Verify the order belongs to the specified place
    if order.place != place:
        messages.error(request, 'Order does not belong to this place.')
        return redirect('place_orders_dashboard', place_id=place_id)
    
    # Check if user is the place owner or staff member with permission
    if place.created_by != request.user:
        try:
            staff_member = place.staff_members.get(user=request.user)
            if not staff_member.can_edit_orders:
                messages.error(request, 'You do not have permission to edit orders.')
                return redirect('place_orders_dashboard', place_id=place.pk)
        except PlaceStaff.DoesNotExist:
            messages.error(request, 'You do not have permission to edit orders.')
            return redirect('public_place_detail', pk=place.pk)
    
    if request.method == 'POST':
        form = PlaceOrderForm(request.POST, instance=order, place=place)
        if form.is_valid():
            form.save()
            messages.success(request, 'Order updated successfully!')
            return redirect('place_orders_dashboard', place_id=place.pk)
    else:
        form = PlaceOrderForm(instance=order, place=place)
    
    return render(request, 'listings/edit_place_order.html', {
        'form': form,
        'order': order,
        'place': place
    })


@login_required
def delete_place_order(request, place_id, order_id):
    """Delete an order"""
    order = get_object_or_404(PlaceOrder, pk=order_id)
    place = get_object_or_404(Place, pk=place_id)
    
    # Check if user is the place owner or staff member with permission
    if place.created_by != request.user:
        try:
            staff_member = place.staff_members.get(user=request.user)
            if not staff_member.can_delete_orders:
                messages.error(request, 'You do not have permission to delete orders.')
                return redirect('place_orders_dashboard', place_id=place.pk)
        except PlaceStaff.DoesNotExist:
            messages.error(request, 'You do not have permission to access this dashboard.')
            return redirect('public_place_detail', pk=place.pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Order {order_number} has been deleted.')
        return redirect('place_orders_dashboard', place_id=place.pk)
    
    return render(request, 'listings/delete_place_order.html', {
        'order': order,
        'place': place
    })


@login_required
def add_items_to_order(request, place_id, order_id):
    """Add more items to an existing order"""
    order = get_object_or_404(PlaceOrder, pk=order_id)
    place = get_object_or_404(Place, pk=place_id)
    
    # Verify the order belongs to the specified place
    if order.place != place:
        messages.error(request, 'Order does not belong to this place.')
        return redirect('place_orders_dashboard', place_id=place_id)
    
    # Check if user is the place owner or staff member with permission
    if place.created_by != request.user:
        try:
            staff_member = place.staff_members.get(user=request.user)
            if not staff_member.can_edit_orders:
                messages.error(request, 'You do not have permission to edit orders.')
                return redirect('place_orders_dashboard', place_id=place.pk)
        except PlaceStaff.DoesNotExist:
            messages.error(request, 'You do not have permission to edit orders.')
            return redirect('public_place_detail', pk=place.pk)
    
    if request.method == 'POST':
        # Get form data
        menu_items = request.POST.getlist('menu_items')
        quantities = request.POST.getlist('quantities')
        instructions = request.POST.getlist('instructions')
        
        if not menu_items:
            messages.error(request, 'Please add at least one menu item to the order.')
            return redirect('add_items_to_order', place_id=place_id, order_id=order_id)
        
        try:
            # Add new order items
            total_amount = 0
            for i, item_id in enumerate(menu_items):
                try:
                    menu_item = MenuItem.objects.get(pk=item_id, place=place)
                    quantity = int(quantities[i]) if i < len(quantities) else 1
                    instruction = instructions[i] if i < len(instructions) else ""
                    
                    order_item = PlaceOrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        special_instructions=instruction,
                        total_price=menu_item.price * quantity
                    )
                    
                    total_amount += order_item.total_price
                except (MenuItem.DoesNotExist, ValueError, IndexError) as e:
                    continue
            
            # Update order total and subtotal
            order.subtotal += total_amount
            order.total_amount += total_amount
            order.save()
            
            messages.success(request, f'Added {len(menu_items)} items to Order #{order.id}')
            return redirect('place_orders_dashboard', place_id=place.pk)
            
        except Exception as e:
            messages.error(request, f'Error adding items to order: {str(e)}')
            return redirect('add_items_to_order', place_id=place_id, order_id=order_id)
    
    # Get menu categories and items for the form
    from listings.models import MenuCategory
    menu_categories = MenuCategory.objects.filter(place=place).prefetch_related('menu_items')
    
    # Get existing order items to show current order
    existing_items = order.items.all()
    
    context = {
        'place': place,
        'order': order,
        'menu_categories': menu_categories,
        'existing_items': existing_items,
    }
    
    return render(request, 'listings/add_items_to_order.html', context)

class TourVideoDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View for deleting tour videos via AJAX"""
    
    def test_func(self):
        """Only tour creator can delete videos"""
        return self.get_object().creator == self.request.user
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is verified before allowing video deletion"""
        if not request.user.is_verified:
            return JsonResponse({'success': False, 'error': 'Only verified creators can delete videos'})
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self):
        """Get the tour object"""
        return get_object_or_404(GroupTours, pk=self.kwargs['pk'])
    
    def post(self, request, *args, **kwargs):
        """Handle video deletion"""
        tour = self.get_object()
        
        try:
            # Delete the video file
            if tour.tour_video:
                # Remove the file from storage
                tour.tour_video.delete(save=False)
                # Clear the field
                tour.tour_video = None
                tour.save()
                
                return JsonResponse({'success': True, 'message': 'Video deleted successfully'})
            else:
                return JsonResponse({'success': False, 'error': 'No video found to delete'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error deleting video: {str(e)}'})

class PlaceIntroVideoUploadView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Dedicated view for uploading/updating place intro videos"""
    model = Place
    template_name = 'listings/place_intro_video_upload.html'
    form_class = PlaceIntroVideoForm
    
    def test_func(self):
        return self.get_object().created_by == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('user_place_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Handle file upload
        if 'place_intro_video' in self.request.FILES:
            # Store reference to old video before saving
            old_video = self.object.place_intro_video
            
            # Save the form first to get the new video
            response = super().form_valid(form)
            
            # Now delete the old video file if it exists and is different
            if old_video and old_video != self.object.place_intro_video:
                try:
                    old_video.delete(save=False)
                except Exception as e:
                    # Log the error but don't fail the upload
                    print(f"Warning: Could not delete old video file: {e}")
            
            messages.success(self.request, 'Intro video updated successfully!')
            return response
        else:
            # No new file uploaded, just save the form
            messages.success(self.request, 'Intro video updated successfully!')
            return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.object
        return context
