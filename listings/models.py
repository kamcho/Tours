from django.db import models
from django.utils import timezone
from users.models import MyUser
import os
from decimal import Decimal
from django.core.validators import MinValueValidator
import uuid
from datetime import datetime, date, timedelta

class Agency(models.Model):
    AGENCY_TYPE_CHOICES = [
        ('tour_operator', 'Tour Operator'),
        ('travel_agent', 'Travel Agent'),
        ('destination_management', 'Destination Management'),
        ('adventure_company', 'Adventure Company'),
        ('luxury_travel', 'Luxury Travel'),
        ('budget_travel', 'Budget Travel'),
        ('corporate_travel', 'Corporate Travel'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    agency_type = models.CharField(max_length=50, choices=AGENCY_TYPE_CHOICES, default='tour_operator')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    website = models.URLField(blank=True, null=True)
    
    # Address Information
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Kenya')
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Business Information
    license_number = models.CharField(max_length=100, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    year_established = models.PositiveIntegerField(blank=True, null=True)
    legal_documents = models.FileField(upload_to='agencies/legal_documents/', blank=True, null=True)
    
    # Enhanced Search Fields
    price_range = models.CharField(
        max_length=20,
        choices=[
            ('budget', 'Budget'),
            ('mid_range', 'Mid-Range'),
            ('premium', 'Premium'),
            ('luxury', 'Luxury'),
        ],
        default='mid_range',
        help_text="Price range of services offered"
    )
    
    specialties = models.JSONField(
        default=list,
        blank=True,
        help_text="List of specialties (e.g., ['adventure', 'cultural', 'wildlife', 'beach'])"
    )
    
    languages_spoken = models.JSONField(
        default=list,
        blank=True,
        help_text="Languages spoken by staff"
    )
    
    group_size_range = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Group size range (e.g., '1-10', '10-50', '50+')"
    )
    
    operating_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Operating hours for each day of the week"
    )
    
    # Location Details
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text="GPS latitude coordinate"
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text="GPS longitude coordinate"
    )
    
    # Certifications & Awards
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of certifications and awards"
    )
    
    # Social Media
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    
    # Media
    logo = models.ImageField(upload_to='agencies/logos/', blank=True, null=True)
    profile_picture = models.ImageField(upload_to='agencies/profiles/', blank=True, null=True)
    
    # Relationships
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='agencies_owned')
    
    # Verification
    verified = models.BooleanField(default=False, help_text="Agency verification status")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Agencies"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_verified(self):
        return self.verified
    
    @property
    def average_rating(self):
        """Calculate average rating from all ratings"""
        ratings = self.ratings.filter(rating__isnull=False)
        if ratings.exists():
            total = sum(rating.rating for rating in ratings)
            return round(total / ratings.count(), 1)
        return 0
    
    @property
    def total_ratings(self):
        """Get total number of ratings"""
        return self.ratings.count()
    
    @property
    def rating_distribution(self):
        """Get distribution of ratings (1-5 stars)"""
        distribution = {}
        for i in range(1, 6):
            count = self.ratings.filter(rating=i).count()
            distribution[i] = count
        return distribution
    
    @property
    def top_rating(self):
        """Get the most common rating"""
        from django.db.models import Count
        rating_counts = self.ratings.values('rating').annotate(count=Count('rating')).order_by('-count')
        if rating_counts.exists():
            return rating_counts.first()['rating']
        return 0
    
    def get_user_rating(self, user):
        """Get rating given by a specific user"""
        if user.is_authenticated:
            try:
                return self.ratings.get(user=user)
            except AgencyRating.DoesNotExist:
                return None
        return None


class AgencyService(models.Model):
    """Services offered by agencies"""
    SERVICE_TYPE_CHOICES = [
        ('transport', 'Transport Services'),
        ('tour_guide', 'Tour Guide Services'),
        ('accommodation', 'Accommodation Services'),
        ('booking', 'Booking Services'),
        ('custom_tours', 'Custom Tours'),
        ('adventure', 'Adventure Activities'),
        ('cultural', 'Cultural Experiences'),
        ('wildlife', 'Wildlife Safaris'),
        ('beach', 'Beach & Coastal Tours'),
        ('mountain', 'Mountain & Hiking Tours'),
        ('city_tours', 'City Tours'),
        ('food_tours', 'Food & Culinary Tours'),
        ('photography', 'Photography Tours'),
        ('luxury', 'Luxury Travel Services'),
        ('budget', 'Budget Travel Services'),
        ('corporate', 'Corporate Travel Services'),
        ('events', 'Event Planning'),
        ('transportation', 'Transportation & Logistics'),
        ('insurance', 'Travel Insurance'),
        ('visa', 'Visa & Documentation'),
        ('other', 'Other Services'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('limited', 'Limited Availability'),
        ('unavailable', 'Currently Unavailable'),
        ('seasonal', 'Seasonal Service'),
    ]
    
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    name = models.CharField(max_length=200, help_text="Specific name for this service")
    description = models.TextField(help_text="Detailed description of the service")
    
    # Service Details
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    is_featured = models.BooleanField(default=False, help_text="Mark as featured service")
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Base price for this service")
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Minimum price range")
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Maximum price range")
    pricing_model = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Per Person, Per Day, Fixed Rate")
    
    # Service Features
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 2 hours, Full day, 3 days")
    group_size_min = models.PositiveIntegerField(blank=True, null=True, help_text="Minimum group size")
    group_size_max = models.PositiveIntegerField(blank=True, null=True, help_text="Maximum group size")
    
    # Media
    service_image = models.ImageField(upload_to='agencies/services/', blank=True, null=True, help_text="Image representing this service")
    
    # Additional Information
    requirements = models.TextField(blank=True, null=True, help_text="Requirements for customers")
    included_items = models.TextField(blank=True, null=True, help_text="What's included in the service")
    excluded_items = models.TextField(blank=True, null=True, help_text="What's not included")
    cancellation_policy = models.TextField(blank=True, null=True, help_text="Cancellation and refund policy")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Agency Services"
        ordering = ['-is_featured', 'service_type', 'name']
        unique_together = ['agency', 'service_type', 'name']
    
    def __str__(self):
        return f"{self.agency.name} - {self.get_service_type_display()}: {self.name}"
    
    @property
    def display_price(self):
        """Display price information"""
        if self.base_price:
            return f"${self.base_price}"
        elif self.price_range_min and self.price_range_max:
            return f"${self.price_range_min} - ${self.price_range_max}"
        elif self.price_range_min:
            return f"From ${self.price_range_min}"
        else:
            return "Contact for pricing"
    
    @property
    def group_size_display(self):
        """Display group size information"""
        if self.group_size_min and self.group_size_max:
            return f"{self.group_size_min}-{self.group_size_max} people"
        elif self.group_size_min:
            return f"Min {self.group_size_min} people"
        elif self.group_size_max:
            return f"Max {self.group_size_max} people"
        else:
            return "Flexible group size"
    
    @property
    def is_popular(self):
        """Determine if service is popular based on featured status"""
        return self.is_featured
    
    def clean(self):
        """Validate price ranges"""
        from django.core.exceptions import ValidationError
        
        if self.price_range_min and self.price_range_max:
            if self.price_range_min > self.price_range_max:
                raise ValidationError("Minimum price cannot be greater than maximum price")
        
        if self.group_size_min and self.group_size_max:
            if self.group_size_min > self.group_size_max:
                raise ValidationError("Minimum group size cannot be greater than maximum group size")

def place_image_path(instance, filename):
    """Generate file path for place images"""
    return f'places/{instance.place.id}/{filename}'

def place_profile_picture_path(instance, filename):
    """Generate file path for place profile pictures"""
    return f'places/{instance.id}/profile/{filename}'

class PlaceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True, help_text="Optional icon name or URL.")

    def __str__(self):
        return self.name

class Place(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(PlaceCategory, on_delete=models.CASCADE, related_name='places')
    location = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=30, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=place_profile_picture_path, blank=True, null=True, help_text="Main profile picture for the place")
    created_by = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, related_name='places_created')
    
    # Enhanced Search Fields
    price_range = models.CharField(
        max_length=20, 
        choices=[
            ('free', 'Free'),
            ('low', 'Low (Under KES 500)'),
            ('medium', 'Medium (KES 500 - 2000)'),
            ('high', 'High (KES 2000 - 5000)'),
            ('luxury', 'Luxury (Over KES 5000)'),
        ],
        default='free',
        help_text="Price range for visiting this place"
    )
    
    best_time_to_visit = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Best time of year to visit (e.g., 'June-August', 'Year-round')"
    )
    
    average_visit_duration = models.PositiveIntegerField(
        default=2,
        help_text="Average time spent at this place (in hours)"
    )
    
    peak_season = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Peak tourist season (e.g., 'December-March', 'July-September')"
    )
    
    accessibility_features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of accessibility features (e.g., ['wheelchair_accessible', 'braille_signs'])"
    )
    
    family_friendly = models.BooleanField(
        default=False,
        help_text="Whether this place is suitable for families with children"
    )
    
    pet_friendly = models.BooleanField(
        default=False,
        help_text="Whether pets are allowed at this place"
    )
    
    # Location Details
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True,
        help_text="GPS latitude coordinate"
    )
    
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True,
        help_text="GPS longitude coordinate"
    )
    
    # Operating Hours
    opening_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Operating hours for each day of the week"
    )
    
    # Amenities
    amenities = models.JSONField(
        default=list,
        blank=True,
        help_text="List of available amenities (e.g., ['parking', 'restrooms', 'wifi'])"
    )
    
    # Verification
    verified = models.BooleanField(default=False, help_text="Place verification status")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        """Calculate average rating from all ratings"""
        ratings = self.ratings.filter(rating__isnull=False)
        if ratings.exists():
            total = sum(rating.rating for rating in ratings)
            return round(total / ratings.count(), 1)
        return 0
    
    @property
    def total_ratings(self):
        """Get total number of ratings"""
        return self.ratings.count()
    
    @property
    def rating_distribution(self):
        """Get distribution of ratings (1-5 stars)"""
        distribution = {}
        for i in range(1, 6):
            count = self.ratings.filter(rating=i).count()
            distribution[i] = count
        return distribution
    
    @property
    def top_rating(self):
        """Get the most common rating"""
        from django.db.models import Count
        rating_counts = self.ratings.values('rating').annotate(count=Count('rating')).order_by('-count')
        if rating_counts.exists():
            return rating_counts.first()['rating']
        return 0
    
    def get_user_rating(self, user):
        """Get rating given by a specific user"""
        if user.is_authenticated:
            try:
                return self.ratings.get(user=user)
            except PlaceRating.DoesNotExist:
                return None
        return None

class PlaceImage(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to=place_image_path)
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text="Mark as featured image")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0, help_text="Order for display")

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"{self.place.name} - {self.caption or 'Image'}"

class TravelGroup(models.Model):
 
    GROUP_TYPE_CHOICES = [
        ('permanent', 'Permanent'),
        ('temporary', 'Temporary'),
        ('one-time', 'One-time'),
        
    ]
    OBJECTIVE_CHOICES = [
        ('explore', 'Explore'),
        ('connect', 'Connect'),
        ('experience', 'Experience'),
    ]
    objective = models.CharField(max_length=100, choices=OBJECTIVE_CHOICES)
    group_type = models.CharField(max_length=100, choices=GROUP_TYPE_CHOICES)
    name = models.CharField(max_length=150)
    description = models.TextField()
    creator = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='travel_groups_created')
    members = models.ManyToManyField(MyUser, related_name='travel_groups', blank=True)
    
    is_public = models.BooleanField(default=True, help_text="If true, anyone can request to join.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class GroupTours(models.Model):
    TOUR_STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    GENDERS_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('both', 'Both'),
    ]
    min_age = models.PositiveIntegerField(default=0)
    max_age = models.PositiveIntegerField(default=100)
    gender = models.CharField(max_length=20, choices=GENDERS_CHOICES, default='both')
    min_participants = models.PositiveIntegerField(default=1)
    max_participants = models.PositiveIntegerField(default=10)
    status = models.CharField(max_length=20, choices=TOUR_STATUS_CHOICES, default='planning')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='group_tours_created')
    to = models.CharField(max_length=200, null=True, blank=True)
    destination = models.ManyToManyField(Place, related_name='destinations', null=True, blank=True)
    travel_group = models.ForeignKey(TravelGroup, on_delete=models.CASCADE, related_name='group_tours', blank=True, null=True)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, null=True, blank=True   )
    
    # Display Picture
    display_picture = models.ImageField(
        upload_to='tours/display_pictures/',
        blank=True,
        null=True,
        help_text="Main photo for the tour (recommended size: 800x600px)"
    )
    
    # Tour Details
    start_date = models.DateField()
    end_date = models.DateField()
    max_participants = models.PositiveIntegerField(default=10)
    current_participants = models.PositiveIntegerField(default=0)
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    couple_price = models.DecimalField(max_digits=10, null=True, decimal_places=2, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Additional Details
    itinerary = models.TextField(blank=True, null=True)
    included_services = models.TextField(blank=True, null=True, help_text="What's included in the tour price")
    excluded_services = models.TextField(blank=True, null=True, help_text="What's not included in the tour price")
    requirements = models.TextField(blank=True, null=True, help_text="Requirements for participants")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.to:
            return f"{self.name} - To: {self.to}"
        elif self.destination.exists():
            return f"{self.name} - {self.destination.first().name}"
        else:
            return f"{self.name}"
    
    @property
    def available_spots(self):
        return self.max_participants - self.current_participants
    
    @property
    def is_full(self):
        return self.current_participants >= self.max_participants
    
    @property
    def duration_days(self):
        """Calculate actual duration in days between start and end dates"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def actual_current_participants(self):
        """Calculate current participants from confirmed bookings"""
        confirmed_bookings = self.bookings.filter(status='confirmed')
        return sum(booking.participants for booking in confirmed_bookings)
    
    @property
    def actual_available_spots(self):
        """Calculate available spots based on actual confirmed bookings"""
        return self.max_participants - self.actual_current_participants
    
    @property
    def is_actually_full(self):
        """Check if tour is actually full based on confirmed bookings"""
        return self.actual_current_participants >= self.max_participants

    # Add new fields for enhanced functionality
    likes = models.ManyToManyField(MyUser, related_name='liked_tours', blank=True)
    bookmarks = models.ManyToManyField(MyUser, related_name='bookmarked_tours', blank=True)
    
    def total_likes(self):
        return self.likes.count()
    
    def total_bookmarks(self):
        return self.bookmarks.count()


class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('tour', 'Tour'),
        ('activity', 'Activity'),
        ('workshop', 'Workshop'),
        ('conference', 'Conference'),
        ('other', 'Other'),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='other')

    name = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='events_created')
    # destination = models.ManyToManyField(Place, related_name='destinations')
    travel_group = models.ForeignKey(TravelGroup, null=True, on_delete=models.CASCADE, related_name='events', blank=True)
    
    # Display Picture
    display_picture = models.ImageField(
        upload_to='events/display_pictures/',
        blank=True,
        null=True,
        help_text="Main photo for the event (recommended size: 800x600px)"
    )
    
    # Event Details
    start_date = models.DateField()
    end_date = models.DateField()
    max_participants = models.PositiveIntegerField(default=10)
    current_participants = models.PositiveIntegerField(default=0)
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.BooleanField(default=True)
    
    # Additional Details
    itinerary = models.TextField(blank=True, null=True)
    included_services = models.TextField(blank=True, null=True, help_text="What's included in the tour price")

    # Add new fields for enhanced functionality
    likes = models.ManyToManyField(MyUser, related_name='liked_events', blank=True)
    bookmarks = models.ManyToManyField(MyUser, related_name='bookmarked_events', blank=True)
    
    def total_likes(self):
        return self.likes.count()
    
    def total_bookmarks(self):
        return self.bookmarks.count()

# New models for enhanced functionality

class TourComment(models.Model):
    tour = models.ForeignKey(GroupTours, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='tour_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Comment by {self.user.email} on {self.tour.name}'

class EventComment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='event_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Comment by {self.user.email} on {self.event.name}'

class TourBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    tour = models.ForeignKey(GroupTours, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='tour_bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    participants = models.PositiveIntegerField(default=1)
    special_requests = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-booking_date']
        unique_together = ['user', 'tour']  # One booking per user per tour
    
    def __str__(self):
        return f'Booking by {self.user.email} for {self.tour.name}'
    
    @property
    def is_paid(self):
        """Check if booking is fully paid"""
        return self.payment_status == 'completed'
    
    @property
    def can_cancel(self):
        """Check if booking can be cancelled"""
        return self.status in ['pending', 'payment_pending'] and self.payment_status != 'completed'
    
    @property
    def total_paid_amount(self):
        """Get total amount paid through all payment transactions"""
        return self.payment_transactions.filter(payment_status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    @property
    def remaining_amount(self):
        """Get remaining amount to be paid"""
        return self.total_amount - self.total_paid_amount
    
    @property
    def payment_progress_percentage(self):
        """Get payment progress as percentage"""
        if self.total_amount == 0:
            return 100
        return min(100, (self.total_paid_amount / self.total_amount) * 100)
    
    @property
    def is_fully_paid(self):
        """Check if the full amount has been paid"""
        return self.total_paid_amount >= self.total_amount


class TourBookingPayment(models.Model):
    """Model to store individual payment transactions for tour bookings (Lipa Mdogo Mdogo)"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        
    ]
    
    # Basic payment info
    booking = models.ForeignKey(TourBooking, on_delete=models.CASCADE, related_name='payment_transactions')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='tour_booking_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Link to core payment models
    payment_transaction = models.ForeignKey('core.PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='tour_booking_payments')
    mpesa_payment = models.ForeignKey('core.MPesaPayment', on_delete=models.SET_NULL, null=True, blank=True, related_name='tour_booking_payments')
    card_payment = models.ForeignKey('core.CardPayment', on_delete=models.SET_NULL, null=True, blank=True, related_name='tour_booking_payments')
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Transaction references
    payment_reference = models.CharField(max_length=100, unique=True, blank=True, help_text="Unique payment reference")
    external_reference = models.CharField(max_length=200, blank=True, help_text="External payment provider reference")
    
    # Additional info
    description = models.TextField(blank=True, help_text="Payment description")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional payment metadata")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True, help_text="When payment was completed")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tour Booking Payment'
        verbose_name_plural = 'Tour Booking Payments'
        indexes = [
            models.Index(fields=['payment_reference']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['booking', 'created_at']),
            models.Index(fields=['payment_transaction']),
            models.Index(fields=['mpesa_payment']),
            models.Index(fields=['card_payment']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_reference} - {self.user.email} - KES {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"TBP{self.created_at.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def is_successful(self):
        return self.payment_status == 'completed'
    
    @property
    def is_pending(self):
        return self.payment_status in ['pending', 'processing']
    
    @property
    def is_failed(self):
        return self.payment_status in ['failed', 'cancelled']
    
    def mark_completed(self):
        """Mark payment as completed"""
        self.payment_status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update booking payment status if this completes the full payment
        if self.booking.is_fully_paid:
            self.booking.payment_status = 'completed'
            self.booking.payment_date = timezone.now()
            self.booking.save()
    
    def mark_failed(self, error_message=""):
        """Mark payment as failed"""
        self.payment_status = 'failed'
        self.metadata['error_message'] = error_message
        self.save()


class EventBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='event_bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    participants = models.PositiveIntegerField(default=1)
    special_requests = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment fields
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Payment transaction reference")
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="Payment method used")
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    payment_date = models.DateTimeField(blank=True, null=True, help_text="Date when payment was completed")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-booking_date']
    
    def __str__(self):
        return f'Booking by {self.user.email} for {self.event.name}'
    
    @property
    def is_paid(self):
        """Check if booking is fully paid"""
        return self.payment_status == 'completed'
    
    @property
    def can_cancel(self):
        """Check if booking can be cancelled"""
        return self.status in ['pending', 'payment_pending'] and self.payment_status != 'completed'

class Features(models.Model):
    name = models.CharField(max_length=200, help_text="Feature name (e.g., Swimming Pool, Playground)")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the feature")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for this feature")
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="Duration (e.g., 2 hours, Full day)")
    image = models.ImageField(upload_to='features/', blank=True, null=True, help_text="Feature image")
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='features')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Features"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.place.name}"
    
    @property
    def display_price(self):
        return f"${self.price}"
    
    @property
    def display_duration(self):
        return self.duration if self.duration else "Varies"

class MenuCategory(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('food', 'Food'),
        ('beverage', 'Beverage'),
        ('dessert', 'Dessert'),
        ('appetizer', 'Appetizer'),
        ('main_course', 'Main Course'),
        ('side_dish', 'Side Dish'),
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('alcoholic', 'Alcoholic'),
        ('non_alcoholic', 'Non-Alcoholic'),
        ('hot_drinks', 'Hot Drinks'),
        ('cold_drinks', 'Cold Drinks'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, help_text="Category name (e.g., Main Dishes, Beverages)")
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default='food')
    description = models.TextField(blank=True, null=True, help_text="Category description")
    icon = models.CharField(max_length=100, blank=True, null=True, help_text="Icon name or emoji for the category")
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='menu_categories')
    order = models.PositiveIntegerField(default=0, help_text="Order for display")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Menu Categories"
        ordering = ['order', 'name']
        unique_together = ['place', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.place.name}"
    
    @property
    def display_icon(self):
        return self.icon if self.icon else "🍽️"

class MenuItem(models.Model):
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('limited', 'Limited'),
        ('out_of_stock', 'Out of Stock'),
        ('seasonal', 'Seasonal'),
        ('daily_special', 'Daily Special'),
    ]
    
    SPICE_LEVEL_CHOICES = [
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('hot', 'Hot'),
        ('extra_hot', 'Extra Hot'),
        ('customizable', 'Customizable'),
    ]
    
    name = models.CharField(max_length=200, help_text="Menu item name")
    description = models.TextField(help_text="Detailed description of the menu item")
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='menu_items')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='menu_items')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price")
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Discounted price if applicable")
    is_discounted = models.BooleanField(default=False, help_text="Whether this item is currently discounted")
    
    # Item Details
    ingredients = models.TextField(blank=True, null=True, help_text="List of ingredients")
    allergens = models.TextField(blank=True, null=True, help_text="Allergen information")
    spice_level = models.CharField(max_length=20, choices=SPICE_LEVEL_CHOICES, blank=True, null=True)
    preparation_time = models.PositiveIntegerField(blank=True, null=True, help_text="Preparation time in minutes")
    serving_size = models.CharField(max_length=100, blank=True, null=True, help_text="Serving size (e.g., 250g, 1 cup)")
    
    # Availability
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_halal = models.BooleanField(default=False)
    is_kosher = models.BooleanField(default=False)
    
    # Media
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True, help_text="Menu item image")
    is_featured = models.BooleanField(default=False, help_text="Mark as featured item")
    
    # Status
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order within category")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Menu Items"
        ordering = ['category__order', 'order', 'name']
        unique_together = ['place', 'category', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.place.name}"
    
    @property
    def display_price(self):
        if self.is_discounted and self.discounted_price:
            return f"${self.discounted_price}"
        return f"${self.price}"
    
    @property
    def original_price(self):
        return f"${self.price}"
    
    @property
    def discount_percentage(self):
        if self.is_discounted and self.discounted_price and self.price > 0:
            discount = ((self.price - self.discounted_price) / self.price) * 100
            return int(discount)
        return 0
    
    @property
    def is_popular(self):
        # You can implement popularity logic here based on orders, views, etc.
        return self.is_featured
    
    @property
    def dietary_icons(self):
        icons = []
        if self.is_vegetarian:
            icons.append("🥬")
        if self.is_vegan:
            icons.append("🌱")
        if self.is_gluten_free:
            icons.append("🌾")
        if self.is_halal:
            icons.append("☪️")
        if self.is_kosher:
            icons.append("✡️")
        return icons

class PlaceRating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='place_ratings')
    rating = models.IntegerField(choices=RATING_CHOICES, help_text="Rating from 1 to 5")
    comment = models.TextField(help_text="Your review and experience")
    is_verified_visit = models.BooleanField(default=False, help_text="Verified that user visited this place")
    is_helpful = models.BooleanField(default=False, help_text="Marked as helpful by other users")
    helpful_count = models.PositiveIntegerField(default=0, help_text="Number of users who found this helpful")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Place Ratings"
        unique_together = ['place', 'user']  # One rating per user per place
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} rated {self.place.name} - {self.rating}/5"
    
    def save(self, *args, **kwargs):
        # Update helpful count if is_helpful changed
        if self.pk:
            old_instance = PlaceRating.objects.get(pk=self.pk)
            if old_instance.is_helpful != self.is_helpful:
                if self.is_helpful:
                    self.helpful_count += 1
                else:
                    self.helpful_count = max(0, self.helpful_count - 1)
        super().save(*args, **kwargs)

class AgencyRating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='agency_ratings')
    rating = models.IntegerField(choices=RATING_CHOICES, help_text="Rating from 1 to 5")
    comment = models.TextField(help_text="Your review and experience")
    service_type = models.CharField(max_length=50, blank=True, help_text="Type of service used (e.g., Tour, Booking, Consultation)")
    is_verified_customer = models.BooleanField(default=False, help_text="Verified that user used this agency's services")
    is_helpful = models.BooleanField(default=False, help_text="Marked as helpful by other users")
    helpful_count = models.PositiveIntegerField(default=0, help_text="Number of users who found this helpful")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Agency Ratings"
        unique_together = ['agency', 'user']  # One rating per user per agency
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} rated {self.agency.name} - {self.rating}/5"

class RatingHelpful(models.Model):
    """Track which users found which ratings helpful"""
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='helpful_votes')
    place_rating = models.ForeignKey(PlaceRating, on_delete=models.CASCADE, related_name='helpful_votes', null=True, blank=True)
    agency_rating = models.ForeignKey(AgencyRating, on_delete=models.CASCADE, related_name='helpful_votes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Rating Helpful Votes"
        unique_together = [
            ['user', 'place_rating'],
            ['user', 'agency_rating']
        ]
    
    def __str__(self):
        if self.place_rating:
            return f"{self.user.email} found {self.place_rating} helpful"
        else:
            return f"{self.user.email} found {self.agency_rating} helpful"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.place_rating and not self.agency_rating:
            raise ValidationError("Must specify either place_rating or agency_rating")
        if self.place_rating and self.agency_rating:
            raise ValidationError("Cannot specify both place_rating and agency_rating")

class PlaceGallery(models.Model):
    """Gallery images for places"""
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='place_gallery_images')
    image = models.ImageField(upload_to='places/gallery/')
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption for the image")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    is_featured = models.BooleanField(default=False, help_text="Mark as featured image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Place Gallery Image'
        verbose_name_plural = 'Place Gallery Images'
    
    def __str__(self):
        return f"{self.place.name} - {self.caption or 'Image'}"
    
    def get_image_url(self):
        """Get the URL for the image"""
        if self.image:
            return self.image.url
        return None
    
    def save(self, *args, **kwargs):
        # Auto-generate alt text if not provided
        if not self.alt_text:
            self.alt_text = f"{self.place.name} - {self.caption or 'Gallery image'}"
        super().save(*args, **kwargs)

class AgencyGallery(models.Model):
    """Gallery images for agencies"""
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='agencies/gallery/')
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption for the image")
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    is_featured = models.BooleanField(default=False, help_text="Mark as featured image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Agency Gallery Image'
        verbose_name_plural = 'Agency Gallery Images'
    
    def __str__(self):
        return f"{self.agency.name} - {self.caption or 'Image'}"
    
    def get_image_url(self):
        """Get the URL for the image"""
        if self.image:
            return self.image.url
        return None
    
    def save(self, *args, **kwargs):
        # Auto-generate alt text if not provided
        if not self.alt_text:
            self.alt_text = f"{self.agency.name} - {self.caption or 'Gallery image'}"
        super().save(*args, **kwargs)

# Date Planner Models
class DatePlan(models.Model):
    """Model for storing date/activity plans created by users"""
    
    PLAN_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PLAN_TYPE_CHOICES = [
        ('romantic', 'Romantic Date'),
        ('family', 'Family Day Out'),
        ('friends', 'Friends Hangout'),
        ('solo', 'Solo Adventure'),
        ('business', 'Business Meeting'),
        ('cultural', 'Cultural Experience'),
        ('adventure', 'Adventure/Outdoor'),
        ('relaxation', 'Relaxation/Wellness'),
        ('food', 'Food & Dining'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping Trip'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='date_plans')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=PLAN_STATUS_CHOICES, default='draft')
    
    # Date and Time
    planned_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # Location and Budget
    location = models.CharField(max_length=200, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_currency = models.CharField(max_length=3, default='KES')
    
    # Preferences
    group_size = models.PositiveIntegerField(default=2)
    is_public = models.BooleanField(default=False, help_text="Make this plan visible to others")
    allow_suggestions = models.BooleanField(default=True, help_text="Allow AI to suggest activities")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Date Plan'
        verbose_name_plural = 'Date Plans'
    
    def __str__(self):
        return f"{self.title} - {self.creator.email} ({self.planned_date})"
    
    @property
    def total_cost(self):
        """Calculate total cost of all activities"""
        return sum(activity.estimated_cost or 0 for activity in self.activities.all())
    
    @property
    def duration_hours(self):
        """Calculate total duration in hours"""
        if self.start_time and self.end_time:
            start = datetime.combine(self.planned_date, self.start_time)
            end = datetime.combine(self.planned_date, self.end_time)
            if end < start:  # If end time is next day
                end += timedelta(days=1)
            return (end - start).total_seconds() / 3600
        return 0


class DateActivity(models.Model):
    """Model for individual activities within a date plan"""
    
    ACTIVITY_CATEGORY_CHOICES = [
        ('food', 'Food & Dining'),
        ('entertainment', 'Entertainment'),
        ('outdoor', 'Outdoor Activities'),
        ('cultural', 'Cultural'),
        ('shopping', 'Shopping'),
        ('wellness', 'Wellness & Spa'),
        ('adventure', 'Adventure'),
        ('relaxation', 'Relaxation'),
        ('education', 'Education & Learning'),
        ('social', 'Social'),
        ('other', 'Other'),
    ]
    
    date_plan = models.ForeignKey(DatePlan, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=ACTIVITY_CATEGORY_CHOICES, default='other')
    
    # Timing
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveIntegerField(default=0)
    
    # Location and Details
    location = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Related Place/Agency (optional)
    related_place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name='date_activities')
    related_agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True, related_name='date_activities')
    
    # Status
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'start_time']
        verbose_name = 'Date Activity'
        verbose_name_plural = 'Date Activities'
    
    def __str__(self):
        return f"{self.title} - {self.date_plan.title}"
    
    @property
    def duration_hours(self):
        """Calculate activity duration in hours"""
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        if end < start:  # If end time is next day
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600


class DatePlanPreference(models.Model):
    """Model for storing user preferences for date planning"""
    
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='date_preferences')
    
    # General Preferences
    preferred_plan_types = models.JSONField(default=list, blank=True)
    preferred_activities = models.JSONField(default=list, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    
    # Budget Preferences
    budget_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_currency = models.CharField(max_length=3, default='KES')
    
    # Activity Preferences
    preferred_duration = models.PositiveIntegerField(default=4, help_text="Preferred duration in hours")
    group_size_preference = models.PositiveIntegerField(default=2)
    
    # Dietary and Accessibility
    dietary_restrictions = models.JSONField(default=list, blank=True)
    accessibility_needs = models.JSONField(default=list, blank=True)
    
    # AI Suggestions
    allow_ai_suggestions = models.BooleanField(default=True)
    ai_suggestion_frequency = models.CharField(max_length=20, choices=[
        ('always', 'Always'),
        ('sometimes', 'Sometimes'),
        ('never', 'Never')
    ], default='sometimes')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Date Plan Preference'
        verbose_name_plural = 'Date Plan Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


class DatePlanSuggestion(models.Model):
    """Model for AI-generated date plan suggestions"""
    
    SUGGESTION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('modified', 'Modified'),
    ]
    
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='date_suggestions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Plan Details
    suggested_date = models.DateField()
    estimated_duration = models.PositiveIntegerField(help_text="Duration in hours")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Activities
    suggested_activities = models.JSONField(default=list, help_text="List of suggested activities")
    
    # AI Generation
    ai_prompt = models.TextField(help_text="Original prompt used to generate suggestion")
    ai_model = models.CharField(max_length=50, default='gpt-3.5-turbo')
    generation_timestamp = models.DateTimeField(auto_now_add=True)
    
    # User Response
    status = models.CharField(max_length=20, choices=SUGGESTION_STATUS_CHOICES, default='pending')
    user_feedback = models.TextField(blank=True)
    rating = models.PositiveIntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Date Plan Suggestion'
        verbose_name_plural = 'Date Plan Suggestions'
    
    def __str__(self):
        return f"AI Suggestion: {self.title} for {self.user.email}"


class DatePlanCollaboration(models.Model):
    """Model for collaborative date planning between users"""
    
    COLLABORATION_ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
        ('contributor', 'Contributor'),
    ]
    
    date_plan = models.ForeignKey(DatePlan, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='date_collaborations')
    role = models.CharField(max_length=20, choices=COLLABORATION_ROLE_CHOICES, default='viewer')
    
    # Permissions
    can_edit = models.BooleanField(default=False)
    can_add_activities = models.BooleanField(default=False)
    can_remove_activities = models.BooleanField(default=False)
    can_invite_others = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['date_plan', 'user']
        verbose_name = 'Date Plan Collaboration'
        verbose_name_plural = 'Date Plan Collaborations'
    
    def __str__(self):
        return f"{self.user.email} - {self.role} on {self.date_plan.title}"




class PlaceStaff(models.Model):
    """Staff members assigned to places with specific permissions"""
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('waiter', 'Waiter'),
        ('chef', 'Chef'),
        ('cashier', 'Cashier'),
        ('host', 'Host'),
        ('bartender', 'Bartender'),
        ('kitchen_staff', 'Kitchen Staff'),
        ('cleaning_staff', 'Cleaning Staff'),
        ('other', 'Other'),
    ]
    
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='staff_members')
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='place_staff_roles')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
    
    # Permissions
    can_view_orders = models.BooleanField(default=True)
    can_create_orders = models.BooleanField(default=False)
    can_edit_orders = models.BooleanField(default=False)
    can_delete_orders = models.BooleanField(default=False)
    can_view_customers = models.BooleanField(default=True)
    can_edit_menu = models.BooleanField(default=False)
    can_manage_staff = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    # Additional info
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['place', 'user']
        verbose_name = 'Place Staff'
        verbose_name_plural = 'Place Staff'
    
    def __str__(self):
        return f"{self.user.username} - {self.role} at {self.place.name}"
    
    def has_permission(self, permission):
        """Check if staff member has a specific permission"""
        return getattr(self, permission, False)
    
    def get_permissions_display(self):
        """Get a list of all permissions this staff member has"""
        permissions = []
        if self.can_view_orders:
            permissions.append('View Orders')
        if self.can_create_orders:
            permissions.append('Create Orders')
        if self.can_edit_orders:
            permissions.append('Edit Orders')
        if self.can_delete_orders:
            permissions.append('Delete Orders')
        if self.can_view_customers:
            permissions.append('View Customers')
        if self.can_edit_menu:
            permissions.append('Edit Menu')
        if self.can_manage_staff:
            permissions.append('Manage Staff')
        if self.can_view_analytics:
            permissions.append('View Analytics')
        if self.can_manage_settings:
            permissions.append('Manage Settings')
        return permissions


class PlaceOrder(models.Model):
    """Orders for places (restaurants, etc.)"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('dine_in', 'Dine In'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Delivery'),
        ('reservation', 'Reservation'),
    ]
    
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='place_orders')
    staff_member = models.ForeignKey(PlaceStaff, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_handled')
    
    # Order details
    order_number = models.CharField(max_length=50, unique=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='dine_in')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Timing
    order_date = models.DateTimeField(auto_now_add=True)
    estimated_ready_time = models.DateTimeField(null=True, blank=True)
    actual_ready_time = models.DateTimeField(null=True, blank=True)
    completed_time = models.DateTimeField(null=True, blank=True)
    
    # Customer details
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    
    # Delivery/Reservation details
    delivery_address = models.TextField(blank=True, null=True)
    delivery_instructions = models.TextField(blank=True, null=True)
    reservation_time = models.DateTimeField(null=True, blank=True)
    party_size = models.PositiveIntegerField(default=1)
    
    # Financial
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Notes
    special_instructions = models.TextField(blank=True, null=True)
    staff_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Place Order'
        verbose_name_plural = 'Place Orders'
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.place.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_status_color(self):
        """Get color class for status display"""
        status_colors = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-blue-100 text-blue-800',
            'preparing': 'bg-orange-100 text-orange-800',
            'ready': 'bg-green-100 text-green-800',
            'delivered': 'bg-purple-100 text-purple-800',
            'completed': 'bg-gray-100 text-gray-800',
            'cancelled': 'bg-red-100 text-red-800',
        }
        return status_colors.get(self.status, 'bg-gray-100 text-gray-800')


class PlaceOrderItem(models.Model):
    """Individual items in a place order"""
    order = models.ForeignKey(PlaceOrder, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='place_order_items')
    
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customizations
    special_instructions = models.TextField(blank=True, null=True)
    customizations = models.JSONField(default=dict, blank=True)  # For add-ons, modifications, etc.
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} - Order #{self.order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.quantity * self.menu_item.price
        super().save(*args, **kwargs)