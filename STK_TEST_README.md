# M-Pesa STK Push Test Scripts

This directory contains test scripts to test the M-Pesa STK push functionality and see if you receive the payment prompt on your phone.

## 📱 What is STK Push?

STK Push (Sim Tool Kit Push) is a feature that allows businesses to send payment requests directly to a customer's phone. When initiated, the customer receives an M-Pesa prompt asking them to enter their PIN to complete the payment.

## 🚀 Test Scripts Available

### 1. Full Django Test Script (`core/test_stk_push.py`)
- **Use this if**: You want to test the complete Django integration
- **Features**: Creates test users, payment methods, and full transaction records
- **Requirements**: Django server running, database configured

### 2. Simple Standalone Test Script (`core/simple_stk_test.py`)
- **Use this if**: You want to test just the core STK push functionality
- **Features**: Tests the M-Pesa API directly without Django overhead
- **Requirements**: Only Python and requests library

## 🔧 Prerequisites

### For Full Django Test:
1. Django server running (`python manage.py runserver`)
2. Database migrations applied
3. M-Pesa payment method created in admin panel
4. Payment settings configured

### For Simple Test:
1. Python 3.6+
2. Required packages installed
3. Valid M-Pesa API credentials

## 📦 Installation

1. **Install dependencies:**
   ```bash
   pip install -r test_requirements.txt
   ```

2. **Update credentials** (for simple test):
   - Edit `core/simple_stk_test.py`
   - Replace `your_consumer_key_here` with your actual consumer key
   - Replace `your_consumer_secret_here` with your actual consumer secret

## 🧪 Running the Tests

### Option 1: Full Django Test
```bash
cd core
python test_stk_push.py
```

### Option 2: Simple Standalone Test
```bash
cd core
python simple_stk_test.py
```

## 📋 Test Process

1. **Enter your phone number** (e.g., 0712345678)
2. **Confirm the test parameters**
3. **Wait for STK push initiation**
4. **Check your phone** for the M-Pesa prompt
5. **Enter your M-Pesa PIN** (or cancel if testing)
6. **Check the test results**

## 🔑 Required M-Pesa Credentials

You need these credentials from your M-Pesa developer account:
- **Consumer Key**: Your app's consumer key
- **Consumer Secret**: Your app's consumer secret  
- **Passkey**: Your app's passkey
- **Business Shortcode**: Your business shortcode

## 📱 What to Expect on Your Phone

When the test is successful, you should receive:
1. **M-Pesa SMS** with payment details
2. **Payment prompt** asking for your PIN
3. **Amount**: KES 1 (test amount)
4. **Business**: Your business shortcode
5. **Reference**: Test transaction reference

## ❌ Common Issues & Solutions

### Issue: "Access token failed"
- **Solution**: Check your consumer key and secret
- **Check**: Verify credentials in M-Pesa developer portal

### Issue: "STK Push failed"
- **Solution**: Check business shortcode and passkey
- **Check**: Verify shortcode is active and passkey is correct

### Issue: No prompt on phone
- **Solution**: Check phone number format (should be 254XXXXXXXXX)
- **Check**: Ensure phone has M-Pesa app installed and active

### Issue: Django import errors
- **Solution**: Run Django server first (`python manage.py runserver`)
- **Check**: Ensure you're in the correct directory

## 🔍 Debug Information

Both scripts provide detailed debug output:
- ✅ Success indicators
- ❌ Error messages
- 📡 API responses
- 🔐 Generated credentials
- 📱 Phone number processing

## 🚨 Important Notes

1. **Test Amount**: Scripts use KES 1 for testing (minimal charge)
2. **Phone Number**: Must be registered with M-Pesa
3. **Network**: Requires internet connection
4. **Credentials**: Never commit real credentials to version control
5. **Testing**: Use test credentials in development environment

## 📞 Support

If you encounter issues:
1. Check the debug output for error messages
2. Verify your M-Pesa credentials
3. Ensure your phone number is correct
4. Check internet connectivity
5. Verify M-Pesa app is active on your phone

## 🎯 Next Steps

After successful testing:
1. Integrate the working code into your main application
2. Set up proper error handling and logging
3. Implement callback URL handling
4. Add transaction status tracking
5. Set up production credentials

---

**Happy Testing! 🚀📱** 