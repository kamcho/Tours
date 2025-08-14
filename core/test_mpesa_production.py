#!/usr/bin/env python3
"""
Production M-Pesa STK Push Test Script
This script tests the M-Pesa integration using database settings
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

def test_mpesa_integration():
    """Test complete M-Pesa integration"""
    print("🚀 Testing M-Pesa Production Integration...")
    print("=" * 60)
    
    try:
        # Check if M-Pesa is configured
        try:
            settings = PaymentSettings.get_settings()
            if not settings.mpesa_consumer_key:
                print("❌ M-Pesa not configured. Please run 'python manage.py setup_mpesa' first.")
                return
            print(f"✅ M-Pesa configuration found")
        except Exception as e:
            print(f"❌ Error checking M-Pesa configuration: {e}")
            return
        
        # Initialize MPesa service
        mpesa_service = MPesaService()
        print(f"✅ MPesaService initialized successfully")
        print(f"📱 Business Shortcode: {mpesa_service.business_shortcode}")
        print(f"🔗 Callback URL: {mpesa_service.callback_url}")
        
        # Check M-Pesa payment method
        try:
            mpesa_method = PaymentMethod.objects.get(payment_type='mpesa', is_active=True)
            print(f"✅ M-Pesa payment method found: {mpesa_method.name}")
        except PaymentMethod.DoesNotExist:
            print("❌ M-Pesa payment method not found. Please run 'python manage.py setup_mpesa' first.")
            return
        
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
        
        # Test parameters
        phone_number = input("\n📱 Enter your phone number (e.g., 0712345678): ").strip()
        if not phone_number:
            print("❌ Phone number is required!")
            return
        
        amount = Decimal("1.00")  # Test with 1 KES
        reference = f"PROD_TEST_{int(django.utils.timezone.now().timestamp())}"
        description = "Production M-Pesa Test Payment"
        
        print(f"\n📋 Test Parameters:")
        print(f"   Phone: {phone_number}")
        print(f"   Amount: KES {amount}")
        print(f"   Reference: {reference}")
        print(f"   Description: {description}")
        print(f"   Payment Method: {mpesa_method.name}")
        
        # Confirm before proceeding
        confirm = input("\n❓ Proceed with production STK push? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Test cancelled.")
            return
        
        print(f"\n🚀 Initiating production STK push...")
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
            print(f"\n✅ Production STK Push initiated successfully!")
            print(f"   Transaction ID: {transaction.transaction_id}")
            print(f"   M-Pesa Payment ID: {mpesa_payment.id}")
            print(f"   Checkout Request ID: {mpesa_payment.checkout_request_id}")
            print(f"   Merchant Request ID: {mpesa_payment.merchant_request_id}")
            print(f"   Status: {mpesa_payment.mpesa_status}")
            
            print(f"\n📱 Check your phone for the M-Pesa prompt!")
            print(f"   You should receive a message asking you to enter your M-Pesa PIN")
            print(f"   Amount: KES {amount}")
            print(f"   Business: {mpesa_service.business_shortcode}")
            print(f"   Reference: {reference}")
            
            # Wait for user to complete payment
            input("\n⏳ Press Enter after you've completed or cancelled the payment on your phone...")
            
            # Check transaction status
            transaction.refresh_from_db()
            mpesa_payment.refresh_from_db()
            
            print(f"\n📊 Final Transaction Status:")
            print(f"   Transaction Status: {transaction.status}")
            print(f"   M-Pesa Status: {mpesa_payment.mpesa_status}")
            if transaction.completed_at:
                print(f"   Completed At: {transaction.completed_at}")
            if transaction.external_reference:
                print(f"   M-Pesa Receipt: {transaction.external_reference}")
            
            # Show transaction details
            print(f"\n💰 Transaction Details:")
            print(f"   Amount: KES {transaction.amount}")
            print(f"   Processing Fee: KES {transaction.processing_fee}")
            print(f"   Total: KES {transaction.amount + transaction.processing_fee}")
            print(f"   Payment Method: {transaction.payment_method.name}")
            
            if transaction.metadata:
                print(f"   Metadata: {transaction.metadata}")
            
        else:
            print(f"\n❌ Failed to initiate production STK push:")
            print(f"   Error: {response}")
            
    except Exception as e:
        print(f"\n❌ Error during production test: {str(e)}")
        import traceback
        traceback.print_exc()

def show_mpesa_config():
    """Show current M-Pesa configuration"""
    print("\n🔧 Current M-Pesa Configuration:")
    print("=" * 60)
    
    try:
        settings = PaymentSettings.get_settings()
        print(f"📱 Consumer Key: {settings.mpesa_consumer_key[:20]}...")
        print(f"🔑 Business Shortcode: {settings.mpesa_business_shortcode}")
        print(f"🌍 Environment: {settings.mpesa_environment}")
        print(f"🔗 Callback URL: {settings.mpesa_callback_url}")
        
        # Check payment method
        try:
            mpesa_method = PaymentMethod.objects.get(payment_type='mpesa', is_active=True)
            print(f"💳 Payment Method: {mpesa_method.name} (Active: {mpesa_method.is_active})")
            print(f"💰 Min Amount: KES {mpesa_method.min_amount}")
            print(f"💰 Max Amount: KES {mpesa_method.max_amount}")
        except PaymentMethod.DoesNotExist:
            print("❌ M-Pesa payment method not found")
            
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")

def main():
    """Main function"""
    print("🧪 M-Pesa Production Integration Test Suite")
    print("=" * 60)
    
    while True:
        print("\n📋 Test Options:")
        print("1. Test Production M-Pesa Integration")
        print("2. Show Current M-Pesa Configuration")
        print("3. Exit")
        
        choice = input("\n🔢 Select option (1-3): ").strip()
        
        if choice == '1':
            test_mpesa_integration()
        elif choice == '2':
            show_mpesa_config()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    main() 