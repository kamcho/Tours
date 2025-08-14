from django import forms
from .models import TourComment, EventComment, TourBooking, EventBooking, Features, MenuCategory, MenuItem, PlaceRating, AgencyRating, PlaceCategory, Agency, GroupTours, AgencyService

# Comment Forms
class TourCommentForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Share your thoughts about this tour...',
            'rows': 4,
        }),
        max_length=1000
    )

class EventCommentForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none',
            'rows': 3,
            'placeholder': 'Share your thoughts about this event...'
        }),
        max_length=1000
    )

# Booking Forms
class TourBookingForm(forms.ModelForm):
    class Meta:
        model = TourBooking
        fields = ['participants', 'special_requests']
        widgets = {
            'participants': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
                'min': '1',
                'max': '10',
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
                'placeholder': 'Any special requests or requirements?',
                'rows': 3,
            }),
        }

class EventBookingForm(forms.ModelForm):
    class Meta:
        model = EventBooking
        fields = ['participants', 'special_requests']
        widgets = {
            'participants': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
                'min': '1',
                'max': '10',
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
                'placeholder': 'Any special requests or requirements?',
                'rows': 3,
            }),
        }

class EnhancedTourBookingForm(forms.Form):
    BOOKING_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('couple', 'Couple'),
        ('group', 'Group'),
    ]
    
    booking_type = forms.ChoiceField(
        choices=BOOKING_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'w-4 h-4 text-teal-600 focus:ring-teal-500 border-gray-300'
        }),
        initial='individual'
    )
    
    participants = forms.IntegerField(
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Number of participants'
        })
    )
    
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Any special requests, dietary requirements, or accessibility needs?',
            'rows': 4,
        }),
        max_length=1000
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.tour = kwargs.pop('tour', None)
        super().__init__(*args, **kwargs)
        
        if self.tour:
            # Update max participants based on available spots
            max_spots = self.tour.available_spots
            self.fields['participants'].max_value = max_spots
            self.fields['participants'].widget.attrs['max'] = max_spots
            
            # If no couple price, remove couple option
            if not self.tour.couple_price:
                choices = [(k, v) for k, v in self.fields['booking_type'].choices if k != 'couple']
                self.fields['booking_type'].choices = choices
                self.fields['booking_type'].initial = 'individual'
    
    def clean(self):
        cleaned_data = super().clean()
        booking_type = cleaned_data.get('booking_type')
        participants = cleaned_data.get('participants')
        
        if booking_type == 'couple' and participants != 2:
            raise forms.ValidationError("Couple booking must have exactly 2 participants.")
        
        if booking_type == 'individual' and participants != 1:
            raise forms.ValidationError("Individual booking must have exactly 1 participant.")
        
        return cleaned_data
    
    def calculate_total_amount(self):
        """Calculate total amount based on booking type and pricing"""
        if not self.tour:
            return 0
            
        participants = self.cleaned_data.get('participants', 1)
        booking_type = self.cleaned_data.get('booking_type', 'individual')
        
        if booking_type == 'couple' and self.tour.couple_price:
            return self.tour.couple_price
        else:
            return self.tour.price_per_person * participants

class FeatureForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Feature name (e.g., Swimming Pool, Playground)',
        }),
        label='Feature Name'
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'Describe this feature in detail...',
            'rows': 4,
        }),
        label='Description'
    )
    
    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0',
        }),
        label='Price ($)'
    )
    
    duration = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'placeholder': 'e.g., 2 hours, Full day, 30 minutes',
        }),
        label='Duration'
    )
    
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition duration-200',
            'accept': 'image/*',
        }),
        label='Feature Image'
    )
    
    class Meta:
        model = Features
        fields = ['name', 'description', 'price', 'duration', 'image'] 

class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['name', 'category_type', 'description', 'icon', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Enter category name (e.g., Main Dishes, Beverages)'
            }),
            'category_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none',
                'rows': 3,
                'placeholder': 'Describe this category...'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Enter emoji or icon name (e.g., 🍽️, 🍕, 🥤)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            })
        }

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'name', 'description', 'category', 'price', 'discounted_price', 'is_discounted',
            'ingredients', 'allergens', 'spice_level', 'preparation_time', 'serving_size',
            'availability', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_halal', 'is_kosher',
            'image', 'is_featured', 'is_active', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Enter menu item name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none',
                'rows': 3,
                'placeholder': 'Describe this menu item...'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'discounted_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'is_discounted': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none',
                'rows': 3,
                'placeholder': 'List the ingredients...'
            }),
            'allergens': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none',
                'rows': 2,
                'placeholder': 'List any allergens...'
            }),
            'spice_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'preparation_time': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'min': '0',
                'placeholder': 'Time in minutes'
            }),
            'serving_size': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., 250g, 1 cup, 1 portion'
            }),
            'availability': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'is_vegetarian': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'is_vegan': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'is_gluten_free': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'is_halal': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'is_kosher': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'min': '0'
            })
        }
    
    def __init__(self, *args, **kwargs):
        place = kwargs.pop('place', None)
        super().__init__(*args, **kwargs)
        if place:
            self.fields['category'].queryset = MenuCategory.objects.filter(place=place, is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discounted_price = cleaned_data.get('discounted_price')
        is_discounted = cleaned_data.get('is_discounted')
        
        if is_discounted and discounted_price and price:
            if discounted_price >= price:
                raise forms.ValidationError("Discounted price must be less than the original price.")
        
        return cleaned_data 

# Rating Forms
class PlaceRatingForm(forms.ModelForm):
    class Meta:
        model = PlaceRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none',
                'rows': 4,
                'placeholder': 'Share your experience...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize rating choices with star emojis
        self.fields['rating'].choices = [
            (1, '⭐ Poor'),
            (2, '⭐⭐ Fair'),
            (3, '⭐⭐⭐ Good'),
            (4, '⭐⭐⭐⭐ Very Good'),
            (5, '⭐⭐⭐⭐⭐ Excellent'),
        ]

class AgencyRatingForm(forms.ModelForm):
    class Meta:
        model = AgencyRating
        fields = ['rating', 'comment', 'service_type']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none',
                'rows': 4,
                'placeholder': 'Share your experience...'
            }),
            'service_type': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., Tour, Booking, Consultation'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize rating choices with star emojis
        self.fields['rating'].choices = [
            (1, '⭐ Poor'),
            (2, '⭐⭐ Fair'),
            (3, '⭐⭐⭐ Good'),
            (4, '⭐⭐⭐⭐ Very Good'),
            (5, '⭐⭐⭐⭐⭐ Excellent'),
        ] 

class AgencyServiceForm(forms.ModelForm):
    class Meta:
        model = AgencyService
        fields = [
            'service_type', 'name', 'description', 'availability', 'is_featured',
            'base_price', 'price_range_min', 'price_range_max', 'pricing_model',
            'duration', 'group_size_min', 'group_size_max', 'service_image',
            'requirements', 'included_items', 'excluded_items', 'cancellation_policy'
        ]
        widgets = {
            'service_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'placeholder': 'Enter service name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 4,
                'placeholder': 'Describe this service in detail'
            }),
            'availability': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'base_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Base price (optional)'
            }),
            'price_range_min': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Minimum price (optional)'
            }),
            'price_range_max': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Maximum price (optional)'
            }),
            'pricing_model': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'placeholder': 'e.g., Per Person, Per Day, Fixed Rate'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'placeholder': 'e.g., 2 hours, Full day, 3 days'
            }),
            'group_size_min': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'min': '1',
                'placeholder': 'Minimum group size (optional)'
            }),
            'group_size_max': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'min': '1',
                'placeholder': 'Maximum group size (optional)'
            }),
            'service_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'accept': 'image/*'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 3,
                'placeholder': 'Requirements for customers (optional)'
            }),
            'included_items': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 3,
                'placeholder': 'What\'s included in the service (optional)'
            }),
            'excluded_items': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 3,
                'placeholder': 'What\'s not included (optional)'
            }),
            'cancellation_policy': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 3,
                'placeholder': 'Cancellation and refund policy (optional)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        price_range_min = cleaned_data.get('price_range_min')
        price_range_max = cleaned_data.get('price_range_max')
        group_size_min = cleaned_data.get('group_size_min')
        group_size_max = cleaned_data.get('group_size_max')
        
        # Validate price ranges
        if price_range_min and price_range_max and price_range_min > price_range_max:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price")
        
        # Validate group sizes
        if group_size_min and group_size_max and group_size_min > group_size_max:
            raise forms.ValidationError("Minimum group size cannot be greater than maximum group size")
        
        return cleaned_data

class AdvancedSearchForm(forms.Form):
    """Advanced search form for places, tours, and agencies"""
    
    # Basic search
    query = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'placeholder': 'Search for places, tours, or agencies...',
        })
    )
    
    # Search type
    search_type = forms.ChoiceField(
        choices=[
            ('all', 'All'),
            ('places', 'Places'),
            ('tours', 'Tours'),
            ('agencies', 'Agencies'),
            ('events', 'Events'),
        ],
        initial='all',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
        })
    )
    
    # Location filters
    location = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'placeholder': 'City, County, or Region',
        })
    )
    
    # Category filters
    place_category = forms.ModelChoiceField(
        queryset=PlaceCategory.objects.all(),
        required=False,
        empty_label="Any Category",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
        })
    )
    
    agency_type = forms.ChoiceField(
        choices=[('', 'Any Type')] + Agency.AGENCY_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
        })
    )
    
    # Price filters
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'placeholder': 'Min Price',
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'placeholder': 'Max Price',
        })
    )
    
    # Rating filters
    min_rating = forms.ChoiceField(
        choices=[
            ('', 'Any Rating'),
            ('4.5', '4.5+ Stars'),
            (4.0, '4.0+ Stars'),
            (3.5, '3.5+ Stars'),
            (3.0, '3.0+ Stars'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
        })
    )
    
    # Date filters for tours/events
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'type': 'date',
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'type': 'date',
        })
    )
    
    # Additional filters
    is_verified = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded',
        })
    )
    
    has_photos = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded',
        })
    )
    
    # Sort options
    sort_by = forms.ChoiceField(
        choices=[
            ('relevance', 'Relevance'),
            ('rating', 'Highest Rated'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('newest', 'Newest First'),
            ('popular', 'Most Popular'),
        ],
        initial='relevance',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price")
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date")
        
        return cleaned_data


# GroupTours Form
class GroupToursForm(forms.ModelForm):
    class Meta:
        model = GroupTours
        fields = ['name', 'description', 'to', 'destination', 'travel_group', 'start_date', 'end_date', 
                  'max_participants', 'price_per_person', 'couple_price', 'status', 
                  'itinerary', 'included_services', 'excluded_services', 'requirements', 'display_picture']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'placeholder': 'Enter tour name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 4,
                'placeholder': 'Describe your tour'
            }),
            'to': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'placeholder': 'Enter destination (e.g., Nairobi, Mombasa, etc.)'
            }),
            'destination': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
            }),
            'travel_group': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'type': 'date'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'min': '1',
                'max': '100'
            }),
            'price_per_person': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'step': '0.01',
                'min': '0'
            }),
            'couple_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'step': '0.01',
                'min': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
            }),
            'itinerary': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 4,
                'placeholder': 'Describe the tour itinerary'
            }),
            'included_services': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 3,
                'placeholder': 'What\'s included in the tour price'
            }),
            'excluded_services': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 3,
                'placeholder': 'What\'s not included in the tour price'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900 resize-none',
                'rows': 3,
                'placeholder': 'Requirements for participants'
            }),
            'display_picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 bg-white text-gray-900',
                'accept': 'image/*'
            }),
        }

    def clean_destination(self):
        """Handle empty destination field properly"""
        destination = self.cleaned_data.get('destination')
        if destination == [''] or destination == []:
            return []
        return destination

    def clean_to(self):
        """Clean the to field"""
        to = self.cleaned_data.get('to')
        if to and to.strip() == '':
            return None
        return to

    def clean_description(self):
        """Clean the description field"""
        description = self.cleaned_data.get('description')
        if description and description.strip() == '':
            return None
        return description 