#!/usr/bin/env python3
"""
Test script for M-Pesa STK Push functionality
Run this script to test if STK push appears on your phone
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
from django.contrib.auth import get_user_model

User = get_user_model()

def test_stk_push():
    """Test STK push functionality"""
    print("🚀 Testing M-Pesa STK Push...")
    print("=" * 50)
    
    try:
        # Initialize MPesa service
        mpesa_service = MPesaService()
        print(f"✅ MPesaService initialized successfully")
        print(f"📱 Business Shortcode: {mpesa_service.business_shortcode}")
        print(f"🔗 Callback URL: {mpesa_service.callback_url}")
        
        # Get or create a test user
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
        
        # Get or create M-Pesa payment method
        try:
            mpesa_method = PaymentMethod.objects.get(payment_type='mpesa', is_active=True)
            print(f"💳 Found M-Pesa payment method: {mpesa_method.name}")
        except PaymentMethod.DoesNotExist:
            print("❌ M-Pesa payment method not found. Please create one in admin panel.")
            return
        
        # Test parameters
        phone_number = input("📱 Enter your phone number (e.g., 0712345678): ").strip()
        if not phone_number:
            print("❌ Phone number is required!")
            return
        
        amount = Decimal("1.00")  # Test with 1 KES
        reference = f"TEST_{int(django.utils.timezone.now().timestamp())}"
        description = "Test STK Push Payment"
        
        print(f"\n📋 Test Parameters:")
        print(f"   Phone: {phone_number}")
        print(f"   Amount: KES {amount}")
        print(f"   Reference: {reference}")
        print(f"   Description: {description}")
        
        # Confirm before proceeding
        confirm = input("\n❓ Proceed with STK push? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Test cancelled.")
            return
        
        print(f"\n🚀 Initiating STK push...")
        print("   Please check your phone for the M-Pesa prompt...")
        
        # Create payment transaction and initiate STK push
        transaction, mpesa_payment, response = mpesa_service.create_payment_transaction(
            user=test_user,
            amount=amount,
            phone_number=phone_number,
            reference=reference,
            description=description
        )
        
        if transaction and mpesa_payment:
            print(f"\n✅ STK Push initiated successfully!")
            print(f"   Transaction ID: {transaction.transaction_id}")
            print(f"   M-Pesa Payment ID: {mpesa_payment.id}")
            print(f"   Checkout Request ID: {mpesa_payment.checkout_request_id}")
            print(f"   Merchant Request ID: {mpesa_payment.merchant_request_id}")
            
            print(f"\n📱 Check your phone for the M-Pesa prompt!")
            print(f"   You should receive a message asking you to enter your M-Pesa PIN")
            print(f"   Amount: KES {amount}")
            print(f"   Business: {mpesa_service.business_shortcode}")
            
            # Wait for user to complete payment
            input("\n⏳ Press Enter after you've completed or cancelled the payment on your phone...")
            
            # Check transaction status
            transaction.refresh_from_db()
            mpesa_payment.refresh_from_db()
            
            print(f"\n📊 Final Status:")
            print(f"   Transaction Status: {transaction.status}")
            print(f"   M-Pesa Status: {mpesa_payment.mpesa_status}")
            if transaction.completed_at:
                print(f"   Completed At: {transaction.completed_at}")
            if transaction.external_reference:
                print(f"   M-Pesa Receipt: {transaction.external_reference}")
            
        else:
            print(f"\n❌ Failed to initiate STK push:")
            print(f"   Error: {response}")
            
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

def test_access_token():
    """Test access token generation"""
    print("\n🔑 Testing Access Token Generation...")
    print("=" * 50)
    
    try:
        mpesa_service = MPesaService()
        access_token = mpesa_service.generate_access_token()
        
        if access_token:
            print(f"✅ Access token generated successfully!")
            print(f"   Token: {access_token[:50]}...")
        else:
            print(f"❌ Failed to generate access token")
            
    except Exception as e:
        print(f"❌ Error generating access token: {str(e)}")

def test_password_generation():
    """Test password generation"""
    print("\n🔐 Testing Password Generation...")
    print("=" * 50)
    
    try:
        mpesa_service = MPesaService()
        password, timestamp = mpesa_service.generate_password()
        
        print(f"✅ Password generated successfully!")
        print(f"   Password: {password[:20]}...")
        print(f"   Timestamp: {timestamp}")
        
    except Exception as e:
        print(f"❌ Error generating password: {str(e)}")

def main():
    """Main test function"""
    print("🧪 M-Pesa STK Push Test Suite")
    print("=" * 50)
    
    while True:
        print("\n📋 Test Options:")
        print("1. Test STK Push (Full test)")
        print("2. Test Access Token Generation")
        print("3. Test Password Generation")
        print("4. Exit")
        
        choice = input("\n🔢 Select test option (1-4): ").strip()
        
        if choice == '1':
            test_stk_push()
        elif choice == '2':
            test_access_token()
        elif choice == '3':
            test_password_generation()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main() 