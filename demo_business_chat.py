#!/usr/bin/env python
"""
Demo script for Business Chat functionality

This script demonstrates how to use the business chat system that integrates
with OpenAI to provide intelligent responses about businesses.

Features:
1. Business model with company information
2. User inquiry tracking
3. AI-powered responses using OpenAI GPT-4o-mini
4. Chat history management
5. Beautiful web interface with Tailwind CSS
6. AJAX-powered real-time chat

Usage:
1. Run the Django server: python manage.py runserver
2. Visit: http://localhost:8000/business/1/chat/
3. Log in with: admin@example.com / admin123
4. Start chatting with the business assistant!

The chat interface will:
- Show business information in a side panel
- Provide an interactive chat interface
- Store conversation history
- Use OpenAI for intelligent responses
- Fall back to basic responses if OpenAI is unavailable
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelske.settings')
django.setup()

from django.contrib.auth import get_user_model
from listings.models import Business, UserBusinessInquiry, BusinessAIIquiryResponse
from listings.views import web_chat_assistant

def demo_chat_functionality():
    """Demonstrate the business chat functionality"""
    print("🚀 Business Chat Demo")
    print("=" * 50)
    
    # Get or create a business
    business, created = Business.objects.get_or_create(
        name="TechCorp Solutions",
        defaults={
            'description': 'A leading technology company providing innovative software solutions for businesses worldwide.',
            'industry': 'Technology',
            'company_size': '50-100 employees',
            'website': 'https://techcorp.example.com',
            'location': 'Nairobi, Kenya',
            'phone': '+254712345678',
            'email': 'info@techcorp.example.com',
            'whatsapp_number': '+254712345678'
        }
    )
    
    if created:
        print(f"✅ Created new business: {business.name}")
    else:
        print(f"📋 Using existing business: {business.name}")
    
    # Get or create a user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        email="demo@example.com",
        defaults={
            'first_name': 'Demo',
            'last_name': 'User',
            'is_active': True
        }
    )
    
    if created:
        user.set_password('demo123')
        user.save()
        print(f"✅ Created demo user: {user.email}")
    else:
        print(f"👤 Using existing user: {user.email}")
    
    print(f"\n🏢 Business Information:")
    print(f"   Name: {business.name}")
    print(f"   Industry: {business.industry}")
    print(f"   Location: {business.location}")
    print(f"   Email: {business.email}")
    print(f"   Phone: {business.phone}")
    
    # Simulate some chat interactions
    sample_queries = [
        "What services do you offer?",
        "Where are you located?",
        "How can I contact you?",
        "What's your company size?",
        "Do you have a website?"
    ]
    
    print(f"\n💬 Simulating Chat Interactions:")
    print("-" * 40)
    
    for query in sample_queries:
        print(f"\n👤 User: {query}")
        response = web_chat_assistant(business.id, user, query)
        print(f"🤖 Assistant: {response}")
    
    # Show statistics
    total_inquiries = UserBusinessInquiry.objects.filter(business=business, user=user).count()
    total_responses = BusinessAIIquiryResponse.objects.filter(inquiry__business=business, inquiry__user=user).count()
    
    print(f"\n📊 Chat Statistics:")
    print(f"   Total inquiries: {total_inquiries}")
    print(f"   Total responses: {total_responses}")
    
    print(f"\n🌐 Access the web interface at:")
    print(f"   http://localhost:8000/business/{business.id}/chat/")
    print(f"   Login with: admin@example.com / admin123")
    
    print(f"\n🔧 Admin interface:")
    print(f"   http://localhost:8000/admin/")
    print(f"   Manage businesses, inquiries, and responses")

if __name__ == "__main__":
    demo_chat_functionality()