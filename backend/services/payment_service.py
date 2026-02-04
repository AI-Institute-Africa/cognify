"""
Payment Services for Cognify - Supports Stripe and Paynow Zimbabwe
"""
import os
import logging
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ====================  PRICING PACKAGES (Server-side only) ====================
COURSE_PACKAGES = {
    "free": {"usd": 0.0, "zwl": 0.0},
    "3_day_course": {"usd": 29.99, "zwl": 7500.0},
    "certificate": {"usd": 99.99, "zwl": 25000.0},
    "certification": {"usd": 199.99, "zwl": 50000.0},
    "diploma": {"usd": 499.99, "zwl": 125000.0},
    "custom_basic": {"usd": 49.99, "zwl": 12500.0},
    "custom_advanced": {"usd": 149.99, "zwl": 37500.0},
    "custom_enterprise": {"usd": 999.99, "zwl": 250000.0},
}

# ====================  STRIPE INTEGRATION ====================
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')
stripe_checkout = None

def get_stripe_checkout(webhook_url: str):
    """Get or create Stripe checkout instance"""
    global stripe_checkout
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        return stripe_checkout
    except Exception as e:
        logger.error(f"Failed to initialize Stripe: {e}")
        return None

async def create_stripe_session(
    amount: float,
    currency: str,
    success_url: str,
    cancel_url: str,
    metadata: dict,
    webhook_url: str
) -> dict:
    """Create a Stripe checkout session"""
    try:
        from emergentintegrations.payments.stripe.checkout import CheckoutSessionRequest
        
        checkout = get_stripe_checkout(webhook_url)
        if not checkout:
            return {"error": "Stripe not configured"}
        
        request = CheckoutSessionRequest(
            amount=float(amount),
            currency=currency,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        session = await checkout.create_checkout_session(request)
        return {"url": session.url, "session_id": session.session_id}
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        return {"error": str(e)}


# ====================  PAYNOW ZIMBABWE INTEGRATION ====================
PAYNOW_INTEGRATION_ID = os.environ.get('PAYNOW_INTEGRATION_ID', 'test_integration_id')
PAYNOW_INTEGRATION_KEY = os.environ.get('PAYNOW_INTEGRATION_KEY', 'test_integration_key')

class PaynowService:
    """Paynow Zimbabwe Payment Gateway Service"""
    
    def __init__(self, result_url: str, return_url: str):
        self.integration_id = PAYNOW_INTEGRATION_ID
        self.integration_key = PAYNOW_INTEGRATION_KEY
        self.result_url = result_url
        self.return_url = return_url
        self.base_url = "https://www.paynow.co.zw/interface"
    
    def generate_hash(self, values: Dict[str, str]) -> str:
        """Generate SHA512 hash for Paynow message authentication"""
        # Concatenate all values in order
        concatenated = ''.join(str(v) for k, v in sorted(values.items()) if k.upper() != 'HASH')
        concatenated += self.integration_key
        return hashlib.sha512(concatenated.encode('utf-8')).hexdigest().upper()
    
    def verify_hash(self, values: Dict[str, str], provided_hash: str) -> bool:
        """Verify that a message hash matches the expected hash"""
        calculated_hash = self.generate_hash(values)
        return calculated_hash == provided_hash
    
    async def initiate_web_payment(
        self,
        reference: str,
        email: str,
        amount: float,
        item_description: str
    ) -> Dict[str, Any]:
        """Initiate a web-based payment (redirects to Paynow)"""
        import httpx
        
        values = {
            "id": self.integration_id,
            "reference": reference,
            "amount": str(amount),
            "additionalinfo": item_description,
            "returnurl": self.return_url,
            "resulturl": self.result_url,
            "authemail": email,
            "status": "Message"
        }
        values["hash"] = self.generate_hash(values)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/initiatetransaction",
                    data=values,
                    timeout=30
                )
                
                # Parse response (URL-encoded format)
                result = dict(x.split('=') for x in response.text.split('&') if '=' in x)
                
                if result.get('status', '').lower() in ['ok', 'created']:
                    return {
                        "success": True,
                        "paymentUrl": result.get('browserurl', ''),
                        "pollUrl": result.get('pollurl', ''),
                        "reference": reference,
                        "paynow_reference": result.get('paynowreference', '')
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get('error', 'Payment initiation failed')
                    }
        except Exception as e:
            logger.error(f"Paynow web payment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def initiate_mobile_payment(
        self,
        reference: str,
        email: str,
        phone: str,
        method: str,  # 'ecocash' or 'onemoney'
        amount: float,
        item_description: str
    ) -> Dict[str, Any]:
        """Initiate a mobile money payment (EcoCash or OneMoney)"""
        import httpx
        
        values = {
            "id": self.integration_id,
            "reference": reference,
            "amount": str(amount),
            "additionalinfo": item_description,
            "returnurl": self.return_url,
            "resulturl": self.result_url,
            "authemail": email,
            "phone": phone,
            "method": method,
            "status": "Message"
        }
        values["hash"] = self.generate_hash(values)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/remotetransaction",
                    data=values,
                    timeout=30
                )
                
                # Parse response
                result = dict(x.split('=') for x in response.text.split('&') if '=' in x)
                
                if result.get('status', '').lower() in ['ok', 'sent']:
                    instructions = "Check your phone for payment prompt"
                    if method.lower() == 'ecocash':
                        instructions = "Dial *151*2*7# to approve payment or check your EcoCash app"
                    elif method.lower() == 'onemoney':
                        instructions = "Dial *111# to approve payment or check your OneMoney app"
                    
                    return {
                        "success": True,
                        "instructions": instructions,
                        "pollUrl": result.get('pollurl', ''),
                        "reference": reference,
                        "paynow_reference": result.get('paynowreference', '')
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get('error', 'Mobile payment initiation failed')
                    }
        except Exception as e:
            logger.error(f"Paynow mobile payment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_payment_status(self, poll_url: str) -> Dict[str, Any]:
        """Poll Paynow to check the current status of a payment"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(poll_url, timeout=15)
                
                # Parse response
                result = dict(x.split('=') for x in response.text.split('&') if '=' in x)
                
                status = result.get('status', 'unknown').lower()
                
                return {
                    "status": status,
                    "reference": result.get('reference'),
                    "paynow_reference": result.get('paynowreference'),
                    "amount": result.get('amount'),
                    "paid": status in ['paid', 'awaiting delivery', 'delivered']
                }
        except Exception as e:
            logger.error(f"Paynow status check error: {e}")
            return {"status": "error", "error": str(e)}


# ====================  UTILITY FUNCTIONS ====================

def get_course_price(course_type: str, currency: str = "usd") -> float:
    """Get server-defined price for course type"""
    package = COURSE_PACKAGES.get(course_type, {"usd": 0.0, "zwl": 0.0})
    return package.get(currency.lower(), 0.0)

def generate_payment_reference(course_id: str, user_id: str) -> str:
    """Generate unique payment reference"""
    timestamp = int(datetime.now(timezone.utc).timestamp())
    return f"COG-{course_id[:8]}-{user_id[:8]}-{timestamp}"
