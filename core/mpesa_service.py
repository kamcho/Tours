import base64
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from requests.auth import HTTPBasicAuth
from django.utils import timezone
import requests
import pytz

from .models import PaymentTransaction, MPesaPayment, PaymentMethod, PaymentSettings
from .services import generate_access_token, parse_date, generate_mpesa_password, process_number

logger = logging.getLogger(__name__)


class MPesaService:
    """M-Pesa payment service integration"""
    
    def __init__(self):
        print("🔧 DEBUG: MPesaService initialized")
        # Get settings from database
        try:
            self.settings = PaymentSettings.get_settings()
            print(f"⚙️ DEBUG: Loaded payment settings: {self.settings}")
            print(f"🔑 DEBUG: Consumer key: {self.settings.mpesa_consumer_key[:20] if self.settings.mpesa_consumer_key else 'None'}...")
            print(f"📱 DEBUG: Business shortcode: {self.settings.mpesa_business_shortcode if self.settings.mpesa_business_shortcode else 'None'}")
            print(f"🔗 DEBUG: Callback URL: {self.settings.mpesa_callback_url if self.settings.mpesa_callback_url else 'None'}")
        except Exception as e:
            print(f"❌ DEBUG: Failed to load payment settings: {e}")
            # Fallback to hardcoded values
            self.settings = None
        
        # Use settings from database
        if self.settings and self.settings.mpesa_consumer_key:
            self.consumer_key = self.settings.mpesa_consumer_key
            self.consumer_secret = self.settings.mpesa_consumer_secret
            self.passkey = self.settings.mpesa_passkey
            self.business_shortcode = self.settings.mpesa_business_shortcode
            print(f"🔑 DEBUG: Using settings from database - shortcode: {self.business_shortcode}")
        else:
            # No settings found - raise error
            raise Exception("M-Pesa credentials not configured. Please run 'python manage.py setup_mpesa' to configure.")
        
        # Get callback URL from settings
        if self.settings and self.settings.mpesa_callback_url:
            self.callback_url = self.settings.mpesa_callback_url
            print(f"🔗 DEBUG: Callback URL from settings: {self.callback_url}")
        else:
            # No callback URL configured - raise error
            raise Exception("M-Pesa callback URL not configured. Please run 'python manage.py setup_mpesa' to configure.")
        
        # API URLs - using production URLs
        self.base_url = "https://api.safaricom.co.ke"
        print(f"🌐 DEBUG: Base URL: {self.base_url}")
    
    def generate_access_token(self):
        """Generate M-Pesa access token for API authentication"""
        access_token_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        
        try:
            response = requests.get(
                access_token_url, 
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            
            if response.status_code == 200:
                access_token = response.json().get('access_token')
                logger.info("M-Pesa access token generated successfully")
                return access_token
            else:
                logger.error(f"M-Pesa access token failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating M-Pesa access token: {str(e)}")
            return None
    
    def generate_password(self):
        """Generate M-Pesa password for STK push"""
        print("🔐 DEBUG: generate_password called")
        try:
            # Use the working implementation from tests.py - avoid datetime conflict
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            print(f"🔍 DEBUG: timestamp generated: {timestamp}")
            
            # Use the working implementation from user's code
            concatenated_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(concatenated_string.encode()).decode('utf-8')
            
            print(f"🔐 DEBUG: Password generated successfully, timestamp: {timestamp}")
            return password, timestamp
        except Exception as e:
            print(f"❌ DEBUG: Failed to generate password: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_account_balance(self):
        """Query M-Pesa account balance for the business shortcode"""
        try:
            # Check if required fields are configured
            if not hasattr(self.settings, 'mpesa_initiator_name') or not self.settings.mpesa_initiator_name:
                logger.error("M-Pesa initiator name not configured")
                return {
                    'error': 'M-Pesa initiator name not configured',
                    'details': 'Please configure the initiator name in Payment Settings'
                }
            
            if not hasattr(self.settings, 'mpesa_security_credential') or not self.settings.mpesa_security_credential:
                logger.error("M-Pesa security credential not configured")
                return {
                    'error': 'M-Pesa security credential not configured',
                    'details': 'Please configure the security credential in Payment Settings'
                }
            
            # Generate access token
            access_token = self.generate_access_token()
            if not access_token:
                logger.error("Failed to generate access token for account balance query")
                return {
                    'error': 'Failed to generate access token',
                    'details': 'Check your M-Pesa consumer key and secret'
                }
            
            # Account balance endpoint
            balance_url = f"{self.base_url}/mpesa/accountbalance/v1/query"
            
            # Prepare payload according to M-Pesa API documentation
            payload = {
                "CommandID": "AccountBalance",
                "PartyA": int(self.business_shortcode),
                "IdentifierType": "4",  # 4 for business shortcode
                "Remarks": "Account balance query",
                "Initiator": self.settings.mpesa_initiator_name,
                "SecurityCredential": self.settings.mpesa_security_credential,
                "QueueTimeOutURL": f"{self.callback_url}/timeout/",
                "ResultURL": f"{self.callback_url}/balance/"
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Querying account balance for shortcode: {self.business_shortcode}")
            logger.info(f"Payload: {payload}")
            logger.info(f"Headers: {headers}")
            
            response = requests.post(balance_url, headers=headers, json=payload, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Account balance query successful: {result}")
                return result
            else:
                logger.error(f"Account balance query failed: {response.status_code} - {response.text}")
                return {
                    'error': f'API request failed: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"Error querying account balance: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'error': 'Exception occurred',
                'details': str(e)
            }
    
    def initiate_stk_push(self, phone_number, amount, reference, description="Payment"):
        """
        Initiate M-Pesa STK push payment
        
        Args:
            phone_number (str): Customer phone number
            amount (Decimal): Payment amount
            reference (str): Payment reference/account reference
            description (str): Payment description
            
        Returns:
            dict: Response from M-Pesa API
        """
        print(f"🔍 DEBUG: initiate_stk_push called with phone={phone_number}, amount={amount}, reference={reference}")
        try:
            phone = self.process_number(phone_number)
            print(f"📱 DEBUG: Processed phone number: {phone}")
            password, timestamp = self.generate_password()
            print(f"🔐 DEBUG: Generated password: {password[:20]}..., timestamp: {timestamp}")
            access_token = self.generate_access_token()
            print(f"🎫 DEBUG: Generated access token: {access_token[:20]}...")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            print(f"📋 DEBUG: Headers prepared: Authorization Bearer {access_token[:20]}...")
            
            payload = {
                "BusinessShortCode": int(self.business_shortcode),
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),  # Convert to int as per M-Pesa API requirement
                "PartyA": phone,
                "PartyB": int(self.business_shortcode),
                "PhoneNumber": phone,
                "CallBackURL": self.callback_url,
                "AccountReference": reference,
                "TransactionDesc": description,
            }
            print(f"📦 DEBUG: Payload prepared: {json.dumps(payload, indent=2)}")
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            print(f"🌐 DEBUG: Making request to: {url}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"📡 DEBUG: Response status: {response.status_code}")
            print(f"📡 DEBUG: Response content: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ DEBUG: STK push successful: {result}")
                return result
            else:
                print(f"❌ DEBUG: STK push failed with status {response.status_code}: {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            print(f"❌ DEBUG: Exception in initiate_stk_push: {e}")
            return {"error": str(e)}
    
    def create_payment_transaction(self, user, amount, phone_number, reference, description="Payment"):
        """
        Create a payment transaction and initiate M-Pesa payment
        
        Args:
            user: User making the payment
            amount (Decimal): Payment amount
            phone_number (str): Customer phone number
            reference (str): Payment reference
            description (str): Payment description
            
        Returns:
            tuple: (PaymentTransaction, MPesaPayment, dict) or (None, None, dict) on error
        """
        print(f"💰 DEBUG: create_payment_transaction called for user={user}, amount={amount}, phone={phone_number}")
        print(f"🔍 DEBUG: About to get payment method...")
        try:
            # Get M-Pesa payment method
            mpesa_method = PaymentMethod.objects.get(payment_type='mpesa', is_active=True)
            
            # Calculate processing fee
            processing_fee = mpesa_method.calculate_processing_fee(amount)
            
            # Create payment transaction
            transaction = PaymentTransaction.objects.create(
                user=user,
                amount=amount,
                processing_fee=processing_fee,
                payment_method=mpesa_method,
                description=description,
                content_type='mpesa_payment',
                object_id=reference,
                status='pending'
            )
            print(f"📝 DEBUG: Created PaymentTransaction: {transaction.transaction_id}")
            
            # Initiate M-Pesa payment
            print("🚀 DEBUG: Initiating STK push...")
            payment_response = self.initiate_stk_push(
                phone_number=phone_number,
                amount=amount,
                reference=reference,
                description=description
            )
            print(f"📡 DEBUG: STK push response: {payment_response}")
            
            if 'error' not in payment_response:
                # Create M-Pesa payment record
                mpesa_payment = MPesaPayment.objects.create(
                    transaction=transaction,
                    phone_number=phone_number,
                    mpesa_request_id=f"MPESA_{reference}_{int(timezone.now().timestamp())}",
                    checkout_request_id=payment_response.get('CheckoutRequestID', ''),
                    merchant_request_id=payment_response.get('MerchantRequestID', ''),
                    mpesa_status='initiated',
                    mpesa_amount=amount
                )
                print(f"📱 DEBUG: Created MPesaPayment: {mpesa_payment.id}")
                
                logger.info(f"M-Pesa payment transaction created: {transaction.transaction_id}")
                return transaction, mpesa_payment, payment_response
            else:
                # Update transaction status to failed
                transaction.status = 'failed'
                transaction.save()
                
                logger.error(f"Failed to create M-Pesa payment: {payment_response['error']}")
                return None, None, payment_response
                
        except PaymentMethod.DoesNotExist:
            error_msg = "M-Pesa payment method not found or inactive"
            logger.error(error_msg)
            return None, None, {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"Error creating M-Pesa payment transaction: {str(e)}")
            return None, None, {'success': False, 'error': str(e)}
    
    def process_callback(self, callback_data):
        """
        Process M-Pesa callback data
        
        Args:
            callback_data (dict): Callback data from M-Pesa
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        print(f"📞 DEBUG: process_callback called with data: {callback_data}")
        try:
            # Extract relevant data
            checkout_request_id = callback_data.get('CheckoutRequestID')
            print(f"🔍 DEBUG: Looking for checkout request ID: {checkout_request_id}")
            
            if not checkout_request_id:
                print("❌ DEBUG: No CheckoutRequestID found in callback data")
                return False
            
            # Find the M-Pesa payment record
            try:
                mpesa_payment = MPesaPayment.objects.get(
                    checkout_request_id=checkout_request_id,
                    merchant_request_id=callback_data.get('MerchantRequestID') # Use MerchantRequestID from callback
                )
                print(f"📱 DEBUG: Found MPesaPayment: {mpesa_payment.id}")
            except MPesaPayment.DoesNotExist:
                print(f"❌ DEBUG: No MPesaPayment found for checkout request ID: {checkout_request_id}")
                return False
            
            # Update M-Pesa payment status
            result_code = callback_data.get('ResultCode')
            print(f"📊 DEBUG: Result code: {result_code}")
            
            if result_code == '0':  # Success
                mpesa_payment.mpesa_status = 'successful'
                mpesa_payment.result_code = result_code
                mpesa_payment.result_description = callback_data.get('ResultDesc', 'Success')
                mpesa_payment.completed_at = timezone.now()
                mpesa_payment.mpesa_metadata = callback_data
                mpesa_payment.save()
                
                # Update main transaction status
                transaction = mpesa_payment.transaction
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.external_reference = callback_data.get('MpesaReceiptNumber', '')
                transaction.metadata = {
                    'mpesa_receipt_number': transaction.external_reference,
                    'transaction_date': callback_data.get('TransactionDate'),
                    'callback_data': callback_data
                }
                transaction.save()
                
                logger.info(f"M-Pesa payment completed successfully: {transaction.transaction_id}")
                return True
                
            else:  # Failed
                mpesa_payment.mpesa_status = 'failed'
                mpesa_payment.result_code = result_code
                mpesa_payment.result_description = callback_data.get('ResultDesc', 'Failed')
                mpesa_payment.mpesa_metadata = callback_data
                mpesa_payment.save()
                
                # Update main transaction status
                transaction = mpesa_payment.transaction
                transaction.status = 'failed'
                transaction.metadata = {
                    'mpesa_error': transaction.result_description,
                    'callback_data': callback_data
                }
                transaction.save()
                
                logger.error(f"M-Pesa payment failed: {transaction.result_description}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}")
            return False
    
    def process_number(self, input_str):
        """Process phone number to ensure proper format (254XXXXXXXXX)"""
        if input_str.startswith('0'):
            # Remove the leading '0' and replace it with '254'
            return '254' + input_str[1:]
        elif input_str.startswith('254'):
            # If it starts with '254', return the original string
            return input_str
        else:
            # If it doesn't start with either '0' or '254', return the original string
            return input_str
    
    def pull_transactions(self, start_date=None, end_date=None):
        """
        Pull M-Pesa transactions from the API
        
        Args:
            start_date (str): Start date in YYYY-MM-DD HH:MM:SS format
            end_date (str): End date in YYYY-MM-DD HH:MM:SS format
            
        Returns:
            dict: Transactions data or error information
        """
        print(f"📊 DEBUG: pull_transactions called")
        try:
            # Use provided dates or default to last 5 hours
            if not start_date or not end_date:
                start_date, end_date = self._parse_date()
            
            url = f"{self.base_url}/pulltransactions/v1/query"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.generate_access_token()}'
            }
            
            payload = {
                'ShortCode': self.business_shortcode,
                'StartDate': start_date,
                'EndDate': end_date,
                'OffSetValue': '0'
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"📡 DEBUG: Pull response status: {response.status_code}")
            print(f"📡 DEBUG: Pull response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ResponseCode') == '1000':
                    transactions = data.get('Response', [])
                    logger.info(f"Successfully pulled {len(transactions)} M-Pesa transactions")
                    return {
                        'success': True,
                        'transactions': transactions
                    }
                else:
                    logger.error(f"M-Pesa pull transactions failed: {data}")
                    return {
                        'success': False,
                        'error': data.get('ResponseDescription', 'Unknown error')
                    }
            else:
                logger.error(f"M-Pesa pull transactions HTTP error: {response.status_code}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Error pulling M-Pesa transactions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_date(self):
        """Parse dates for M-Pesa transaction queries"""
        print(f"🔍 DEBUG: _parse_date called")
        try:
            # Define the Kenyan timezone
            kenya_timezone = pytz.timezone("Africa/Nairobi")
            print(f"🔍 DEBUG: kenya_timezone: {kenya_timezone}")
            
            # Get the current time in the Kenyan timezone
            now_kenya = datetime.now(pytz.utc).astimezone(kenya_timezone)
            print(f"🔍 DEBUG: now_kenya: {now_kenya}")
            
            # Calculate time 5 hours (300 minutes) earlier
            five_hours_ago = now_kenya - timedelta(minutes=300)
            print(f"🔍 DEBUG: five_hours_ago: {five_hours_ago}")
            
            # Format the dates
            start = five_hours_ago.strftime("%Y-%m-%d %H:%M:%S")
            now = now_kenya.strftime("%Y-%m-%d %H:%M:%S")
            print(f"🔍 DEBUG: start: {start}, now: {now}")
            
            return start, now
        except Exception as e:
            print(f"❌ DEBUG: Error in _parse_date: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def register_callback_url(self, callback_url=None):
        """
        Register callback URL for M-Pesa transactions
        
        Args:
            callback_url (str): URL to receive M-Pesa callbacks (optional, uses default if not provided)
            
        Returns:
            dict: Registration response
        """
        print(f"🔗 DEBUG: register_callback_url called")
        try:
            url = f"{self.base_url}/pulltransactions/v1/register"
            access_token = self.generate_access_token()
            print(f"🎫 DEBUG: Generated access token for registration: {access_token[:20]}...")
            
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to generate access token'
                }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept-Encoding': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            # Use provided callback URL or default from settings
            callback_url = callback_url or self.callback_url
            
            payload = {
                "ShortCode": self.business_shortcode,
                "RequestType": "Pull",
                "NominatedNumber": "254742134431",  # This should be configurable
                "CallBackURL": callback_url
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"📡 DEBUG: Registration response status: {response.status_code}")
            print(f"📡 DEBUG: Registration response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Callback URL registered successfully: {data}")
                return {
                    'success': True,
                    'data': data
                }
            else:
                logger.error(f"Failed to register callback URL: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Error registering callback URL: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 


