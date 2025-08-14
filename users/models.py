from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class MyUser(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Optional. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_('email address'), max_length=50, unique=True)
    
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Supervisor', 'Supervisor'),
        ('Manager', 'Manager'),
        ('Staff', 'Staff'),
        ('Member', 'Member'),
    ]
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='Member',  
        help_text=_('User role in the system')
    )
    
    # Profile Picture
    profile_picture = models.ImageField(
        _('Profile Picture'),
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text=_('Upload a profile picture (optional)')
    )
    
    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text=_('User verification status')
    )
    
    # Fix related_name clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='myuser_set',
        related_query_name='myuser'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='myuser_set',
        related_query_name='myuser'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MyUserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Generate username from email if not provided
        if not self.username:
            self.username = self.email.split('@')[0]
            # Ensure username uniqueness
            counter = 1
            original_username = self.username
            while MyUser.objects.filter(username=self.username).exclude(pk=self.pk).exists():
                self.username = f"{original_username}{counter}"
                counter += 1
        super().save(*args, **kwargs)

class PersonalProfile(models.Model):
    user = models.OneToOneField(
        MyUser, 
        on_delete=models.CASCADE, 
        related_name='profile',
        error_messages={
            'unique': 'A profile already exists for this user.',
            'invalid': 'Invalid user ID.',
        }
    )
    first_name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    county = models.TextField(blank=True, null=True)
    subcounty = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        default='O'
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"

    def save(self, *args, **kwargs):
        # Verify user exists
        if not self.user_id or not MyUser.objects.filter(id=self.user_id).exists():
            raise ValueError("Invalid user ID. The user must exist in the database.")
            
        # If first_name and last_name are not set, copy from user
        if not self.first_name and self.user.first_name:
            self.first_name = self.user.first_name
        if not self.last_name and self.user.last_name:
            self.last_name = self.user.last_name
            
        # Check if profile already exists for this user
        if not self.pk and PersonalProfile.objects.filter(user=self.user).exists():
            raise ValueError("A profile already exists for this user.")
            
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class UserPreferences(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='preferences')
    
    # Travel Interests (Multiple choice)
    INTEREST_CHOICES = [
        ('adventure', 'Adventure'),
        ('culture', 'Culture & Heritage'),
        ('relaxation', 'Relaxation & Wellness'),
        ('food', 'Food & Dining'),
        ('nature', 'Nature & Wildlife'),
        ('shopping', 'Shopping'),
        ('beach', 'Beach & Water'),
        ('mountain', 'Mountain & Hiking'),
        ('historical', 'Historical Sites'),
    ]
    
    interests = models.JSONField(
        default=list,
        blank=True,
        help_text='List of travel interests'
    )
    
    # Budget Range
    BUDGET_CHOICES = [
        ('budget', 'Budget-friendly'),
        ('moderate', 'Moderate'),
        ('luxury', 'Luxury'),
        ('premium', 'Premium'),
    ]
    budget_range = models.CharField(
        max_length=20,
        choices=BUDGET_CHOICES,
        blank=True,
        null=True,
        help_text='Preferred budget range for travel'
    )
    
    # Travel Style
    TRAVEL_STYLE_CHOICES = [
        ('solo', 'Solo Travel'),
        ('couple', 'Couple Travel'),
        ('family', 'Family Travel'),
        ('group', 'Group Travel'),
    ]
    travel_style = models.CharField(
        max_length=20,
        choices=TRAVEL_STYLE_CHOICES,
        blank=True,
        null=True,
        help_text='Preferred travel style'
    )
    
    # Preferred Destinations
    DESTINATION_CHOICES = [
        ('beach', 'Beach Destinations'),
        ('mountain', 'Mountain Destinations'),
        ('city', 'City Destinations'),
        ('rural', 'Rural Destinations'),
        ('historical', 'Historical Destinations'),
        ('wildlife', 'Wildlife Destinations'),
    ]
    preferred_destinations = models.JSONField(
        default=list,
        blank=True,
        help_text='List of preferred destinations or regions'
    )
    
    # Transportation Preferences
    TRANSPORT_CHOICES = [
        ('flight', 'Flight'),
        ('bus', 'Bus'),
        ('train', 'Train'),
        ('car', 'Car Rental'),
        ('motorcycle', 'Motorcycle'),
        ('bicycle', 'Bicycle'),
        ('walking', 'Walking'),
        ('boat', 'Boat'),
    ]
    transportation_preferences = models.JSONField(
        default=list,
        blank=True,
        help_text='Preferred transportation methods'
    )
    
    # Activity Preferences
    ACTIVITY_CHOICES = [
        ('sightseeing', 'Sightseeing'),
        ('photography', 'Photography'),
        ('hiking', 'Hiking'),
        ('swimming', 'Swimming'),
        ('fishing', 'Fishing'),
        ('bird_watching', 'Bird Watching'),
        ('cultural_events', 'Cultural Events'),
        ('sports', 'Sports'),
        ('spa', 'Spa & Wellness'),
        ('nightlife', 'Nightlife'),
    ]
    activity_preferences = models.JSONField(
        default=list,
        blank=True,
        help_text='Preferred activities during travel'
    )
    
    # Travel Frequency
    TRAVEL_FREQUENCY_CHOICES = [
        ('never', 'Never traveled'),
        ('rarely', 'Rarely (1-2 times per year)'),
        ('occasionally', 'Occasionally (3-5 times per year)'),
        ('frequently', 'Frequently (6-10 times per year)'),
        ('very_frequently', 'Very frequently (10+ times per year)'),
    ]
    travel_frequency = models.CharField(
        max_length=20,
        choices=TRAVEL_FREQUENCY_CHOICES,
        blank=True,
        null=True,
        help_text='How often do you travel'
    )
    
    # Group Size Preferences
    GROUP_SIZE_CHOICES = [
        ('1', 'Solo (1 person)'),
        ('2', 'Couple (2 people)'),
        ('3-5', 'Small group (3-5 people)'),
        ('6-10', 'Medium group (6-10 people)'),
        ('10+', 'Large group (10+ people)'),
    ]
    preferred_group_size = models.CharField(
        max_length=10,
        choices=GROUP_SIZE_CHOICES,
        blank=True,
        null=True,
        help_text='Preferred group size for travel'
    )
    
    # Notification Preferences
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text='Notification preferences (email, sms, push)'
    )
    
    # Created and Updated timestamps
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        return f"{self.user.email}'s Preferences"
    
    def get_interests_display(self):
        """Return human-readable interests"""
        if not self.interests:
            return "No interests specified"
        return ", ".join([dict(self.INTEREST_CHOICES).get(interest, interest) for interest in self.interests])
    
    def get_budget_display(self):
        """Return human-readable budget range"""
        return dict(self.BUDGET_CHOICES).get(self.budget_range, "Not specified")
    
    def get_travel_style_display(self):
        """Return human-readable travel style"""
        return dict(self.TRAVEL_STYLE_CHOICES).get(self.travel_style, "Not specified")
    
    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs) 