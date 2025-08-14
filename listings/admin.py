from django.contrib import admin
from .models import PlaceCategory, Place, TravelGroup, PlaceImage, GroupTours, Agency, AgencyService
from .models import * 
# Register your models here.

def verify_places(modeladmin, request, queryset):
    queryset.update(verified=True)
verify_places.short_description = "Mark selected places as verified"

def unverify_places(modeladmin, request, queryset):
    queryset.update(verified=False)
unverify_places.short_description = "Mark selected places as unverified"

def verify_agencies(modeladmin, request, queryset):
    queryset.update(verified=True)
verify_agencies.short_description = "Mark selected agencies as verified"

def unverify_agencies(modeladmin, request, queryset):
    queryset.update(verified=False)
unverify_agencies.short_description = "Mark selected agencies as unverified"

admin.site.register(PlaceCategory)
@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'location', 'verified', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'verified', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'location', 'address']
    list_editable = ['verified', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    actions = [verify_places, unverify_places]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'verified')
        }),
        ('Location', {
            'fields': ('location', 'address')
        }),
        ('Contact Information', {
            'fields': ('website', 'contact_email', 'contact_phone')
        }),
        ('Media', {
            'fields': ('profile_picture',)
        }),
        ('Relationships', {
            'fields': ('created_by',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
admin.site.register(TravelGroup)
admin.site.register(PlaceImage)
admin.site.register(GroupTours)
@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'agency_type', 'status', 'verified', 'city', 'country', 'owner', 'created_at']
    list_filter = ['agency_type', 'status', 'verified', 'country', 'created_at']
    search_fields = ['name', 'description', 'city', 'country', 'owner__email']
    list_editable = ['status', 'verified']
    readonly_fields = ['created_at', 'updated_at']
    actions = [verify_agencies, unverify_agencies]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'agency_type', 'status', 'verified')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'country', 'postal_code')
        }),
        ('Business Information', {
            'fields': ('license_number', 'registration_number', 'year_established', 'legal_documents')
        }),
        ('Social Media', {
            'fields': ('facebook', 'twitter', 'instagram', 'linkedin')
        }),
        ('Media', {
            'fields': ('logo', 'profile_picture')
        }),
        ('Relationships', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
admin.site.register(Event)

@admin.register(AgencyService)
class AgencyServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'agency', 'service_type', 'availability', 'is_featured', 'is_active', 'created_at']
    list_filter = ['service_type', 'availability', 'is_featured', 'is_active', 'created_at', 'agency']
    search_fields = ['name', 'description', 'agency__name']
    list_editable = ['is_featured', 'is_active', 'availability']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('agency', 'service_type', 'name', 'description')
        }),
        ('Service Details', {
            'fields': ('availability', 'is_featured', 'duration')
        }),
        ('Pricing', {
            'fields': ('base_price', 'price_range_min', 'price_range_max', 'pricing_model')
        }),
        ('Group Size', {
            'fields': ('group_size_min', 'group_size_max')
        }),
        ('Media', {
            'fields': ('service_image',)
        }),
        ('Additional Information', {
            'fields': ('requirements', 'included_items', 'excluded_items', 'cancellation_policy'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Features)
class FeaturesAdmin(admin.ModelAdmin):
    list_display = ['name', 'place', 'price', 'duration', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'place']
    search_fields = ['name', 'description', 'place__name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'place')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
