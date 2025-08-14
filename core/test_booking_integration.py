#!/usr/bin/env python3
"""
Test tour booking payment integration
"""

import os
import sys
import django
from decimal import Decimal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelske.settings')
django.setup()

from core.mpesa_service import MPesaService
from core.models import PaymentMethod, PaymentSettings
from listings.models import GroupTours, TourBooking
from django.contrib.auth import get_user_model

User = get_user_model()

def test_mpesa_service():
    """Test MPesaService initialization and basic functionality"""
    print("🧪 Testing MPesaService Integration...")
    print("=" * 50)
    
    try:
        # Test MPesaService initialization
        print("🔧 Testing MPesaService initialization...")
        mpesa_service = MPesaService()
        print("✅ MPesaService initialized successfully")
        
        # Test access token generation
        print("\n🎫 Testing access token generation...")
        access_token = mpesa_service.generate_access_token()
        if access_token:
            print(f"✅ Access token generated: {access_token[:30]}...")
        else:
            print("❌ Failed to generate access token")
            return False
        
        # Test password generation
        print("\n🔐 Testing password generation...")
        password, timestamp = mpesa_service.generate_password()
        print(f"✅ Password generated: {password[:30]}...")
        print(f"✅ Timestamp: {timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing MPesaService: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_tour_booking_creation():
    """Test tour booking creation with payment"""
    print("\n🧪 Testing Tour Booking Creation...")
    print("=" * 50)
    
    try:
        # Initialize MPesaService
        mpesa_service = MPesaService()
        # Get or create test user
        try:
            test_user = User.objects.get(username='testuser')
            print(f"👤 Using existing test user: {test_user.username}")
        except User.DoesNotExist:
            test_user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            print(f"👤 Created test user: {test_user.username}")
        
        # Get first available tour
        try:
            tour = GroupTours.objects.first()
            if not tour:
                print("❌ No tours available for testing")
                return False
            print(f"🎯 Found tour: {tour.name}")
        except Exception as e:
            print(f"❌ Error getting tour: {e}")
            return False
        
        # Test phone number processing
        print("\n📱 Testing phone number processing...")
        test_phone = "0742134431"
        processed_phone = mpesa_service.process_number(test_phone)
        print(f"   Original: {test_phone}")
        print(f"   Processed: {processed_phone}")
        
        # Test payment transaction creation
        print("\n💰 Testing payment transaction creation...")
        amount = Decimal("100.00")
        reference = f"TEST_BOOKING_{int(django.utils.timezone.now().timestamp())}"
        description = f"Test payment for {tour.name}"
        
        print(f"   Amount: {amount}")
        print(f"   Phone: {processed_phone}")
        print(f"   Reference: {reference}")
        print(f"   Description: {description}")
        
        # Create payment transaction
        transaction, mpesa_payment, response = mpesa_service.create_payment_transaction(
            user=test_user,
            amount=amount,
            phone_number=processed_phone,
            reference=reference,
            description=description
        )
        
        if transaction and mpesa_payment:
            print(f"\n✅ Payment transaction created successfully!")
            print(f"   Transaction ID: {transaction.transaction_id}")
            print(f"   M-Pesa Payment ID: {mpesa_payment.id}")
            print(f"   Checkout Request ID: {mpesa_payment.checkout_request_id}")
            print(f"   Status: {transaction.status}")
            
            # Clean up test data
            transaction.delete()
            print("🧹 Test data cleaned up")
            return True
        else:
            print(f"\n❌ Payment transaction creation failed:")
            print(f"   Response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing tour booking: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Tour Booking Payment Integration Test")
    print("=" * 50)
    
    # Test 1: MPesaService
    if not test_mpesa_service():
        print("\n❌ MPesaService test failed. Cannot proceed.")
        return
    
    # Test 2: Tour Booking
    if not test_tour_booking_creation():
        print("\n❌ Tour booking test failed.")
        return
    
    print("\n🎉 All tests passed! Tour booking payment integration is working.")

if __name__ == "__main__":
    main() 