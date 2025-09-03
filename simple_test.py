#!/usr/bin/env python
"""
Simple test for Business Chat functionality - Core features only
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
import time

def run_simple_test():
    print("🚀 Simple Business Chat Test")
    print("=" * 40)
    
    # Create unique test data
    timestamp = int(time.time())
    
    # Create business
    business = Business.objects.create(
        name=f"Test Business {timestamp}",
        description="A test business for testing purposes",
        industry="Testing",
        company_size="1-10 employees",
        location="Test City",
        phone="+1234567890",
        email=f"test{timestamp}@business.com"
    )
    print(f"✅ Created business: {business.name}")
    
    # Create user
    User = get_user_model()
    user = User.objects.create_user(
        email=f"test{timestamp}@example.com",
        password="testpass123"
    )
    print(f"✅ Created user: {user.email}")
    
    # Test chat functionality
    print("\n💬 Testing chat functionality...")
    response = web_chat_assistant(business.id, user, "What services do you offer?")
    print(f"   Response: {response[:100]}...")
    
    # Verify data was saved
    inquiry = UserBusinessInquiry.objects.filter(
        business=business,
        user=user,
        message="What services do you offer?"
    ).first()
    
    if inquiry:
        print("✅ Inquiry saved correctly")
        
        ai_response = BusinessAIIquiryResponse.objects.filter(inquiry=inquiry).first()
        if ai_response:
            print("✅ AI response saved correctly")
        else:
            print("❌ AI response not saved")
            return False
    else:
        print("❌ Inquiry not saved")
        return False
    
    # Test conversation history
    response2 = web_chat_assistant(business.id, user, "Where are you located?")
    total_inquiries = UserBusinessInquiry.objects.filter(business=business, user=user).count()
    
    if total_inquiries == 2:
        print("✅ Conversation history working")
    else:
        print(f"❌ Expected 2 inquiries, got {total_inquiries}")
        return False
    
    print("\n📊 Test Summary:")
    print(f"   Business: {business.name}")
    print(f"   User: {user.email}")
    print(f"   Total inquiries: {total_inquiries}")
    print(f"   Total responses: {BusinessAIIquiryResponse.objects.filter(inquiry__business=business).count()}")
    
    print("\n🎉 All core tests passed!")
    print("\n🌐 To test the web interface:")
    print(f"   1. Start server: python manage.py runserver")
    print(f"   2. Visit: http://localhost:8000/business/{business.id}/chat/")
    print(f"   3. Login with: admin@example.com / admin123")
    
    return True

if __name__ == "__main__":
    if run_simple_test():
        sys.exit(0)
    else:
        sys.exit(1)