"""
Stripe Payment Service using emergentintegrations
Handles: Course payments, Fee payments
"""
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

# Course pricing packages (server-side only - never accept amounts from frontend)
COURSE_PACKAGES = {
    "free": 0.0,
    "3_day_course": 29.99,
    "certificate": 99.99,
    "certification": 199.99,
    "diploma": 499.99
}

# Initialize Stripe checkout
stripe_checkout = None

def get_stripe_checkout(webhook_url: str):
    """Get or create Stripe checkout instance"""
    global stripe_checkout
    try:
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout,
            CheckoutSessionRequest,
            CheckoutSessionResponse,
            CheckoutStatusResponse
        )
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        return stripe_checkout
    except ImportError as e:
        logger.error(f"Failed to import emergentintegrations: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Stripe: {e}")
        return None


async def create_payment_session(
    amount: float,
    currency: str,
    success_url: str,
    cancel_url: str,
    metadata: dict,
    webhook_url: str
) -> dict:
    """
    Create a Stripe checkout session
    Returns: {"url": str, "session_id": str} or {"error": str}
    """
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
        
        return {
            "url": session.url,
            "session_id": session.session_id
        }
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        return {"error": str(e)}


async def get_payment_status(session_id: str, webhook_url: str) -> dict:
    """
    Get payment status for a checkout session
    Returns: {"status": str, "payment_status": str, "amount_total": int, "currency": str, "metadata": dict}
    """
    try:
        checkout = get_stripe_checkout(webhook_url)
        if not checkout:
            return {"error": "Stripe not configured"}
        
        status = await checkout.get_checkout_status(session_id)
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "metadata": status.metadata
        }
    except Exception as e:
        logger.error(f"Stripe status error: {e}")
        return {"error": str(e)}


def get_course_price(course_type: str) -> float:
    """Get server-defined price for course type"""
    return COURSE_PACKAGES.get(course_type, 0.0)
