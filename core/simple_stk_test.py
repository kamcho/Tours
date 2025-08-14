#!/usr/bin/env python3
"""
Simple M-Pesa STK Push Test Script
This script tests the core STK push functionality without full Django setup
"""

import requests
import base64
import json
import uuid
from datetime import datetime
from requests.auth import HTTPBasicAuth

def generate_mpesa_password(business_shortcode, passkey, timestamp):
    """Generate M-Pesa password for STK push"""
    data_to_encode = business_shortcode + passkey + timestamp
    encoded_string = base64.b64encode(data_to_encode.encode()).decode()
    return encoded_string

def generate_access_token(consumer_key, consumer_secret, base_url):
    """Generate M-Pesa access token"""
    access_token_url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'
    
    try:
        response = requests.get(
            access_token_url, 
            auth=HTTPBasicAuth(consumer_key, consumer_secret),
            timeout=30
        )
        
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            print(f"✅ Access token generated successfully")
            return access_token
        else:
            print(f"❌ Access token failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating access token: {str(e)}")
        return None

def test_stk_push():
    """Test STK push functionality"""
    print("🚀 Testing M-Pesa STK Push...")
    print("=" * 50)
    
    # M-Pesa credentials - Your actual credentials
    consumer_key = "aSG8gGG7GWSGapToKz8ySyALUx9zIdbBr1CHldVhyOLjJsCz"
    consumer_secret = "o8qwdbzapgcvOd1lsBOkKGCL4JwMQyG9ZmKlKC7uaLIc4FsRJFbzfV10EAoL0P6u"
    passkey = "fa0e41448ce844d1a7a37553cee8bf22b61fec894e1ce3e9c0e32b1c6953b6d9"
    business_shortcode = "4161900"
    base_url = "https://api.safaricom.co.ke"
    # Using your production callback URL
    callback_url = "https://mwalimuprivate.pythonanywhere.com/core/mpesa/webhook/"
    print(f"🔗 Using production callback URL: {callback_url}")
    
    print(f"🔑 Using credentials:")
    print(f"   Consumer Key: {consumer_key}")
    print(f"   Business Shortcode: {business_shortcode}")
    print(f"   Base URL: {base_url}")
    print(f"   Callback URL: {callback_url}")
    
    # Check if credentials are set
    if consumer_key == "your_consumer_key_here":
        print("\n❌ Please update the credentials in this script with your actual M-Pesa API credentials!")
        print("   You can find these in your M-Pesa developer account or update the PaymentSettings in Django admin.")
        return
    
    # Get phone number
    phone_number = input("\n📱 Enter your phone number (e.g., 0712345678): ").strip()
    if not phone_number:
        print("❌ Phone number is required!")
        return
    
    # Process phone number to 254 format
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    print(f"📱 Processed phone number: {phone_number}")
    
    # Generate timestamp and password
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = generate_mpesa_password(business_shortcode, passkey, timestamp)
    
    print(f"🔐 Generated password and timestamp:")
    print(f"   Timestamp: {timestamp}")
    print(f"   Password: {password[:20]}...")
    
    # Generate access token
    print(f"\n🎫 Generating access token...")
    access_token = generate_access_token(consumer_key, consumer_secret, base_url)
    
    if not access_token:
        print("❌ Failed to generate access token. Check your credentials.")
        return
    
    # Prepare STK push request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "BusinessShortCode": int(business_shortcode),
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": 1,  # Test with 1 KES
        "PartyA": phone_number,
        "PartyB": int(business_shortcode),
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": f"TEST_{int(datetime.now().timestamp())}",
        "TransactionDesc": "Test STK Push Payment",
    }
    
    print(f"\n📦 STK Push payload:")
    print(json.dumps(payload, indent=2))
    
    # Confirm before proceeding
    confirm = input("\n❓ Proceed with STK push? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Test cancelled.")
        return
    
    # Make STK push request
    print(f"\n🚀 Making STK push request...")
    url = f"{base_url}/mpesa/stkpush/v1/processrequest"
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ STK Push successful!")
            print(f"   Checkout Request ID: {result.get('CheckoutRequestID', 'N/A')}")
            print(f"   Merchant Request ID: {result.get('MerchantRequestID', 'N/A')}")
            print(f"   Response Code: {result.get('ResponseCode', 'N/A')}")
            print(f"   Response Description: {result.get('ResponseDescription', 'N/A')}")
            
            print(f"\n📱 Check your phone for the M-Pesa prompt!")
            print(f"   You should receive a message asking you to enter your M-Pesa PIN")
            print(f"   Amount: KES 1")
            print(f"   Business: {business_shortcode}")
            
            # Wait for user to complete payment
            input("\n⏳ Press Enter after you've completed or cancelled the payment on your phone...")
            print("✅ Test completed!")
            
        else:
            print(f"\n❌ STK Push failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error during STK push: {str(e)}")

def main():
    """Main function"""
    print("🧪 Simple M-Pesa STK Push Test")
    print("=" * 50)
    
    while True:
        print("\n📋 Options:")
        print("1. Test STK Push")
        print("2. Exit")
        
        choice = input("\n🔢 Select option (1-2): ").strip()
        
        if choice == '1':
            test_stk_push()
        elif choice == '2':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-2.")

if __name__ == "__main__":
    main() 