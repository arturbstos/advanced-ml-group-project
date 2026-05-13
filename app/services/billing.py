"""Stripe billing — checkout session creation and webhook parsing."""
import logging
import os
from typing import Optional

import stripe

logger = logging.getLogger("veritas.billing")

_PRICE_IDS = {
    "pro":  os.getenv("STRIPE_PRICE_PRO",  ""),
    "team": os.getenv("STRIPE_PRICE_TEAM", ""),
}

_SUCCESS_URL = "https://veritas-demo.web.app/dashboard.html?upgrade=success"
_CANCEL_URL  = "https://veritas-demo.web.app/dashboard.html?upgrade=cancelled"


def _secret_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured.")
    return key


def create_checkout_url(firebase_uid: str, email: Optional[str], tier: str) -> str:
    """Create a Stripe Checkout session and return the hosted payment URL."""
    price_id = _PRICE_IDS.get(tier)
    if not price_id:
        raise ValueError(
            f"STRIPE_PRICE_{tier.upper()} is not configured — "
            "add the price ID from your Stripe dashboard to the environment."
        )

    stripe.api_key = _secret_key()
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=_SUCCESS_URL,
        cancel_url=_CANCEL_URL,
        customer_email=email,
        metadata={"firebase_uid": firebase_uid, "tier": tier},
        subscription_data={"metadata": {"firebase_uid": firebase_uid, "tier": tier}},
    )
    return session.url


def parse_webhook_event(payload: bytes, sig_header: str) -> dict:
    """Verify Stripe signature and return the parsed event dict."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured.")
    return stripe.Webhook.construct_event(payload, sig_header, secret)
