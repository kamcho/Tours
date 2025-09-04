#!/usr/bin/env python
"""
Test script for Business Chat functionality

This script runs comprehensive tests to verify that the business chat system
is working correctly.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelske.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from listings.models import Business, UserBusinessInquiry, BusinessAIIquiryResponse
from listings.views import web_chat_assistant
import json

def test_models():
    """Test that all models are working correctly"""
    print("🧪 Testing Models...")
    
    # Test Business model
    business = Business.objects.create(
        name="Test Business",
        description="A test business for testing purposes",
        industry="Testing",
        company_size="1-10 employees",
        location="Test City",
        phone="+1234567890",
        email="test@business.com"
    )
    assert business.id is not None
    assert str(business) == "Test Business"
    print("✅ Business model test passed")
    
    # Test User model
    User = get_user_model()
    import time
    unique_email = f"test{int(time.time())}@example.com"
    user = User.objects.create_user(
        email=unique_email,
        password="testpass123"
    )
    assert user.id is not None
    print("✅ User model test passed")
    
    # Test UserBusinessInquiry model
    inquiry = UserBusinessInquiry.objects.create(
        business=business,
        user=user,
        message="Test inquiry message",
        status="new"
    )
    assert inquiry.id is not None
    assert inquiry.status == "new"
    print("✅ UserBusinessInquiry model test passed")
    
    # Test BusinessAIIquiryResponse model
    response = BusinessAIIquiryResponse.objects.create(
        inquiry=inquiry,
        response="Test AI response"
    )
    assert response.id is not None
    assert response.inquiry == inquiry
    print("✅ BusinessAIIquiryResponse model test passed")
    
    return business, user

def test_chat_function(business, user):
    """Test the web_chat_assistant function"""
    print("\n💬 Testing Chat Function...")
    
    # Test basic functionality
    print(f"   Testing with business ID: {business.id}, user ID: {user.id}")
    response = web_chat_assistant(business.id, user, "Hello, what services do you offer?")
    assert response is not None
    assert len(response) > 0
    print("✅ Chat function returns response")
    print(f"   Response: {response[:100]}...")
    
    # Verify inquiry was saved
    all_inquiries = UserBusinessInquiry.objects.all()
    print(f"   Total inquiries in DB: {all_inquiries.count()}")
    for inq in all_inquiries:
        print(f"   - Business: {inq.business_id}, User: {inq.user_id}, Message: {inq.message[:50]}...")
    
    inquiry = UserBusinessInquiry.objects.filter(
        business=business, 
        user=user, 
        message="Hello, what services do you offer?"
    ).first()
    print(f"   Found specific inquiry: {inquiry}")
    assert inquiry is not None, f"No inquiry found with the expected message for business {business.id} and user {user.id}"
    print("✅ Inquiry saved to database")
    
    # Verify AI response was saved
    ai_response = BusinessAIIquiryResponse.objects.filter(inquiry=inquiry).first()
    assert ai_response is not None, "No AI response found for inquiry"
    assert ai_response.response == response
    print("✅ AI response saved to database")
    
    # Test conversation history
    print("   Testing conversation history...")
    response2 = web_chat_assistant(business.id, user, "What's your location?")
    inquiries = UserBusinessInquiry.objects.filter(business=business, user=user).count()
    print(f"   Expected 2 inquiries, found: {inquiries}")
    # Note: We created one inquiry in the model test and two in the chat function test
    assert inquiries == 3, f"Expected 3 inquiries (1 from model test + 2 from chat test), got {inquiries}"
    print("✅ Conversation history maintained")

def test_views():
    """Test the Django views"""
    print("\n🌐 Testing Views...")
    
    client = Client()
    
    # Create test data
    business = Business.objects.create(
        name="View Test Business",
        description="Testing views",
        industry="Testing",
        company_size="1-10 employees",
        location="Test City",
        phone="+1234567890",
        email="viewtest@business.com"
    )
    
    User = get_user_model()
    import time
    unique_email = f"viewtest{int(time.time())}@example.com"
    user = User.objects.create_user(
        email=unique_email,
        password="testpass123"
    )
    
    # Test BusinessChatService view (requires login)
    client.login(email=unique_email, password="testpass123")
    
    response = client.get(f'/business/{business.id}/chat/')
    print(f"   Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Response content: {response.content}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert business.name.encode() in response.content
    print("✅ BusinessChatService view works")
    
    # Test AJAX endpoint
    ajax_response = client.post(
        f'/business/{business.id}/chat/ajax/',
        data=json.dumps({'message': 'Test AJAX message'}),
        content_type='application/json'
    )
    assert ajax_response.status_code == 200
    ajax_data = json.loads(ajax_response.content)
    assert ajax_data['success'] == True
    assert 'response' in ajax_data
    print("✅ AJAX endpoint works")

def test_admin_integration():
    """Test admin interface integration"""
    print("\n⚙️ Testing Admin Integration...")
    
    from django.contrib import admin
    from listings.admin import BusinessAdmin, UserBusinessInquiryAdmin, BusinessAIIquiryResponseAdmin
    
    # Check if models are registered
    assert Business in admin.site._registry
    assert UserBusinessInquiry in admin.site._registry
    assert BusinessAIIquiryResponse in admin.site._registry
    print("✅ All models registered in admin")
    
    # Test admin classes exist
    assert BusinessAdmin is not None
    assert UserBusinessInquiryAdmin is not None
    assert BusinessAIIquiryResponseAdmin is not None
    print("✅ Admin classes defined")

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Business Chat Tests")
    print("=" * 50)
    
    try:
        # Test models
        business, user = test_models()
        
        # Test chat function
        test_chat_function(business, user)
        
        # Test views
        test_views()
        
        # Test admin integration
        test_admin_integration()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("✅ Business Chat system is working correctly")
        
        # Show summary
        total_businesses = Business.objects.count()
        total_inquiries = UserBusinessInquiry.objects.count()
        total_responses = BusinessAIIquiryResponse.objects.count()
        
        print(f"\n📊 Database Summary:")
        print(f"   Businesses: {total_businesses}")
        print(f"   Inquiries: {total_inquiries}")
        print(f"   Responses: {total_responses}")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()