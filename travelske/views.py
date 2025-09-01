from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from core.models import Contact
from listings.models import Place

def home_view(request):
    places = Place.objects.order_by("?")[:6]

    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            
            # Validate required fields
            if not all([full_name, email, phone, subject, message]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('home')
            
            # Create contact record
            Contact.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
            return redirect('home')
    
    return render(request, 'home.html', context={'places': places})

def tours_view(request):
    return render(request, 'tours.html')

def destinations_view(request):
    return render(request, 'destinations.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html') 