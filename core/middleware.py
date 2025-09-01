from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user
from django.utils.deprecation import MiddlewareMixin
from listings.models import PlaceStaff

class StaffNavigationMiddleware(MiddlewareMixin):
    """
    Middleware to handle staff navigation and redirects
    """
    
    def process_request(self, request):
        # Skip for non-authenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip for superusers
        if request.user.is_superuser:
            return None
            
        # Check if user is staff at any place
        staff_places = PlaceStaff.objects.filter(user=request.user)
        
        if staff_places.exists():
            # User is staff at one or more places
            current_path = request.path
            
            # Allow access to staff-specific URLs
            allowed_staff_urls = [
                '/users/logout/',
                '/users/profile/',
                '/users/profile/edit/',
                '/users/password/change/',
            ]
            
            # Allow access to staff dashboard and order management
            if any(place_id in current_path for place_id in [str(sp.place.id) for sp in staff_places]):
                if '/staff/' in current_path or '/orders/' in current_path:
                    return None
            
            # If user is trying to access restricted areas, redirect to first staff dashboard
            if not any(allowed_url in current_path for allowed_url in allowed_staff_urls):
                if not any(place_id in current_path for place_id in [str(sp.place.id) for sp in staff_places]):
                    # Redirect to first staff dashboard
                    first_staff_place = staff_places.first().place
                    return redirect('staff_dashboard', place_id=first_staff_place.id)
            
            # Also redirect home page access for staff members
            if current_path == '/':
                first_staff_place = staff_places.first().place
                return redirect('staff_dashboard', place_id=first_staff_place.id)
        
        return None
import time
from .models import PageVisit

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timing request load time
        start_time = time.time()

        response = self.get_response(request)

        # Skip admin and static files
        if request.path.startswith("/admin") or request.path.startswith("/static"):
            return response

        try:
            load_time = time.time() - start_time
            ip = self.get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            referrer = request.META.get("HTTP_REFERER", "")
            session_key = request.session.session_key or None

            PageVisit.objects.create(
                path=request.path,
                ip_address=ip,
                user_agent=user_agent,
                referrer=referrer,
                session_key=session_key,
                load_time=load_time,
                status_code=response.status_code,
            )
        except Exception as e:
            print("Analytics error:", e)

        return response

    def get_client_ip(self, request):
        """Get client IP address safely"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "")
