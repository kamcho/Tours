#!/usr/bin/env python3
"""
Simple M-Pesa STK Push Test using working implementation
"""

import requests
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth

def generate_access_token():
    """Generate M-Pesa access token"""
    access_token_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    consumer_key = "aSG8gGG7GWSGapToKz8ySyALUx9zIdbBr1CHldVhyOLjJsCz"
    consumer_secret = "o8qwdbzapgcvOd1lsBOkKGCL4JwMQyG9ZmKlKC7uaLIc4FsRJFbzfV10EAoL0P6u"

    response = requests.get(access_token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    
    if response.status_code == 200:
        access_token = response.json()['access_token']        
        return access_token
    else:
        return None

def process_number(input_str):
    """Process phone number to 254 format"""
    if input_str.startswith('0'):
        return '254' + input_str[1:]
    elif input_str.startswith('254'):
        return input_str
    else:
        return input_str

def test_stk_push():
    """Test STK push using working implementation"""
    print("🚀 Testing M-Pesa STK Push (Working Implementation)...")
    print("=" * 60)
    
    # Configuration
    paybill = "4161900"
    passkey = "fa0e41448ce844d1a7a37553cee8bf22b61fec894e1ce3e9c0e32b1c6953b6d9"
    callback_url = "https://mwalimuprivate.pythonanywhere.com/core/mpesa/webhook/"
    
    print(f"🔑 Configuration:")
    print(f"   Paybill: {paybill}")
    print(f"   Callback URL: {callback_url}")
    
    # Get phone number
    phone_number = input("\n📱 Enter your phone number (e.g., 0712344431): ").strip()
    if not phone_number:
        print("❌ Phone number is required!")
        return
    
    # Process phone number
    phone = process_number(phone_number)
    print(f"📱 Processed phone number: {phone}")
    
    # Get amount
    try:
        amount = int(input("💰 Enter amount in KES (e.g., 1): ").strip())
        if amount < 1:
            print("❌ Amount must be at least KES 1")
            return
    except ValueError:
        print("❌ Invalid amount. Please enter a number.")
        return
    
    # Generate timestamp and password
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    concatenated_string = f"{paybill}{passkey}{timestamp}"
    password = base64.b64encode(concatenated_string.encode()).decode('utf-8')
    
    print(f"\n🔐 Generated credentials:")
    print(f"   Timestamp: {timestamp}")
    print(f"   Password: {password[:30]}...")
    
    # Generate access token
    print(f"\n🎫 Generating access token...")
    access_token = generate_access_token()
    
    if not access_token:
        print("❌ Failed to generate access token")
        return
    
    print(f"✅ Access token generated: {access_token[:30]}...")
    
    # Prepare STK push request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "BusinessShortCode": int(paybill),
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": int(paybill),
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": f"TEST_{int(datetime.now().timestamp())}",
        "TransactionDesc": "Test STK Push Payment",
    }
    
    print(f"\n📦 STK Push payload:")
    print(f"   Amount: KES {amount}")
    print(f"   Phone: {phone}")
    print(f"   Business: {paybill}")
    print(f"   Callback: {callback_url}")
    
    # Confirm before proceeding
    confirm = input("\n❓ Proceed with STK push? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Test cancelled.")
        return
    
    # Make STK push request
    print(f"\n🚀 Making STK push request...")
    url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
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
            print(f"   Amount: KES {amount}")
            print(f"   Business: {paybill}")
            
            # Wait for user to complete payment
            input("\n⏳ Press Enter after you've completed or cancelled the payment on your phone...")
            print("✅ Test completed!")
            
        else:
            print(f"\n❌ STK Push failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error during STK push: {str(e)}")

def test_access_token():
    """Test access token generation"""
    print("\n🔑 Testing Access Token Generation...")
    print("=" * 60)
    
    access_token = generate_access_token()
    
    if access_token:
        print(f"✅ Access token generated successfully!")
        print(f"   Token: {access_token[:50]}...")
    else:
        print(f"❌ Failed to generate access token")

def main():
    """Main function"""
    print("🧪 M-Pesa STK Push Test (Working Implementation)")
    print("=" * 60)
    
    while True:
        print("\n📋 Test Options:")
        print("1. Test STK Push")
        print("2. Test Access Token Generation")
        print("3. Exit")
        
        choice = input("\n🔢 Select option (1-3): ").strip()
        
        if choice == '1':
            test_stk_push()
        elif choice == '2':
            test_access_token()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    main() 