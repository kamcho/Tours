from django.contrib import admin
from .models import MyUser, PersonalProfile, UserPreferences

@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)

@admin.register(PersonalProfile)
class PersonalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'phone', 'location', 'gender', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('user__email', 'first_name', 'last_name', 'phone', 'location')
    ordering = ('-created_at',)

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'budget_range', 'travel_style', 'travel_frequency', 'created_at')
    list_filter = ('budget_range', 'travel_style', 'travel_frequency', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Travel Preferences', {
            'fields': ('interests', 'budget_range', 'travel_style', 'preferred_destinations')
        }),
        ('Transportation & Activities', {
            'fields': ('transportation_preferences', 'activity_preferences')
        }),
        ('Travel Patterns', {
            'fields': ('travel_frequency', 'preferred_group_size')
        }),
        ('Communication', {
            'fields': ('notification_preferences',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )