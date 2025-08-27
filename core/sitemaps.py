"""
Sitemap generation for TravelsKe platform
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from listings.models import GroupTours, Event, Place, Agency
from django.utils import timezone


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 1.0
    changefreq = 'weekly'
    
    def items(self):
        return [
            'home',
            'grouptours_list',
            'event_list',
            'agency_list',
            'public_place_list',
            'travelgroup_list',
            'trending',
            'advanced_search',
            'about',
            'contact'
        ]
    
    def location(self, item):
        try:
            return reverse(item)
        except:
            return f'/{item}/'


class GroupToursSitemap(Sitemap):
    """Sitemap for group tours"""
    changefreq = 'daily'
    priority = 0.8
    
    def items(self):
        return GroupTours.objects.filter(is_active=True, status='active')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/tour/{obj.pk}/'


class EventSitemap(Sitemap):
    """Sitemap for events"""
    changefreq = 'daily'
    priority = 0.8
    
    def items(self):
        return Event.objects.filter(status=True)
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()
    
    def location(self, obj):
        return f'/event/{obj.pk}/'


class PlaceSitemap(Sitemap):
    """Sitemap for places"""
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Place.objects.filter(is_active=True, verified=True)
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()
    
    def location(self, obj):
        return f'/place/{obj.pk}/'


class AgencySitemap(Sitemap):
    """Sitemap for agencies"""
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Agency.objects.filter(status='active', verified=True)
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else timezone.now()
    
    def location(self, obj):
        return f'/agency/{obj.pk}/'


# Dictionary of sitemaps
sitemaps = {
    'static': StaticViewSitemap,
}
