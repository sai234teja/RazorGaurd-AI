"""
RazorGuard AI - Razorpay API Integration

Server-side Razorpay Test Mode integration.

IMPORTANT:
- Razorpay Key Secret is loaded only from environment variables.
- The secret is never returned to the frontend.
- This module creates/fetches Razorpay orders.
- Payment signatures are verified server-side.
- Payment verification never exposes the Key Secret.
"""

import os
import uuid

import razorpay
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID"
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET"
)


# ============================================================
# CLIENT
# ============================================================

_client = None


def get_client():
    """
    Return a configured Razorpay client.

    The client is created lazily so importing this module
    does not immediately fail when credentials are missing.
    """

    global _client

    if _client is not None:
        return _client

    if not RAZORPAY_KEY_ID:
        raise RuntimeError(
            "RAZORPAY_KEY_ID is not configured."
        )

    if not RAZORPAY_KEY_SECRET:
        raise RuntimeError(
            "RAZORPAY_KEY_SECRET is not configured."
        )

    _client = razorpay.Client(
        auth=(
            RAZORPAY_KEY_ID,
            RAZORPAY_KEY_SECRET,
        )
    )

    return _client


# ============================================================
# CONFIGURATION CHECK
# ============================================================

def is_configured():
    """
    Return True when both Razorpay credentials exist.

    This does not make an API request.
    """

    return bool(
        RAZORPAY_KEY_ID
        and RAZORPAY_KEY_SECRET
    )


# ============================================================
# RUPEES → PAISE
# ============================================================

def amount_to_paise(amount):
    """
    Convert an INR amount into paise.

    Example:
        ₹2499.00 → 249900
    """

    try:
        amount = float(amount)

    except (TypeError, ValueError):

        raise ValueError(
            "Amount must be numeric."
        )

    if amount <= 0:

        raise ValueError(
            "Amount must be greater than zero."
        )

    paise = round(
        amount * 100
    )

    if paise <= 0:

        raise ValueError(
            "Amount must be greater than zero."
        )

    return int(paise)


# ============================================================
# PAISE → RUPEES
# ============================================================

def paise_to_amount(amount):
    """
    Convert paise into a rupee amount.

    Example:
        249900 → 2499.00
    """

    try:
        amount = int(amount)

    except (TypeError, ValueError):

        raise ValueError(
            "Paise amount must be an integer."
        )

    return round(
        amount / 100,
        2,
    )


# ============================================================
# RECEIPT
# ============================================================

def generate_receipt():
    """
    Generate a short unique receipt identifier.

    Razorpay receipts have a maximum length of 40 characters.
    """

    suffix = uuid.uuid4().hex[:12]

    return (
        f"rzg_{suffix}"
    )


# ============================================================
# CREATE RAZORPAY ORDER
# ============================================================

def create_razorpay_order(
    amount,
    currency="INR",
    receipt=None,
    notes=None,
):
    """
    Create a Razorpay order in Test Mode.

    Parameters:
        amount:
            Human-readable amount in rupees.

        currency:
            ISO currency code. Defaults to INR.

        receipt:
            Optional internal receipt identifier.

        notes:
            Optional metadata dictionary.

    Returns:
        Safe Razorpay order information.

    IMPORTANT:
        The Key Secret is never included in the result.
    """

    if not is_configured():

        raise RuntimeError(
            "Razorpay credentials are not configured."
        )

    currency = str(
        currency or "INR"
    ).upper().strip()

    if len(currency) != 3:

        raise ValueError(
            "Currency must be a valid 3-letter ISO code."
        )

    amount_paise = amount_to_paise(
        amount
    )

    if receipt is None:

        receipt = generate_receipt()

    receipt = str(
        receipt
    ).strip()

    if not receipt:

        receipt = generate_receipt()

    if len(receipt) > 40:

        raise ValueError(
            "Receipt must be 40 characters or fewer."
        )

    if notes is None:

        notes = {}

    if not isinstance(
        notes,
        dict,
    ):

        raise ValueError(
            "Notes must be a dictionary."
        )

    # Razorpay allows a maximum of 15 notes.
    if len(notes) > 15:

        raise ValueError(
            "Razorpay notes cannot contain more than 15 entries."
        )

    client = get_client()

    data = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt,
        "notes": notes,
    }

    response = client.order.create(
        data=data
    )

    # ========================================================
    # SAFE RESPONSE
    # ========================================================

    return {
        "success": True,

        "id": response.get(
            "id"
        ),

        "entity": response.get(
            "entity",
            "order",
        ),

        "amount": response.get(
            "amount",
            amount_paise,
        ),

        "amount_rupees": paise_to_amount(
            response.get(
                "amount",
                amount_paise,
            )
        ),

        "amount_paid": response.get(
            "amount_paid",
            0,
        ),

        "amount_due": response.get(
            "amount_due",
            amount_paise,
        ),

        "currency": response.get(
            "currency",
            currency,
        ),

        "receipt": response.get(
            "receipt",
            receipt,
        ),

        "status": response.get(
            "status",
            "created",
        ),

        "attempts": response.get(
            "attempts",
            0,
        ),

        "notes": response.get(
            "notes",
            notes,
        ),

        "test_mode": True,
    }


# ============================================================
# FETCH RAZORPAY ORDER
# ============================================================

def fetch_razorpay_order(
    order_id,
):
    """
    Fetch an existing Razorpay order.

    Used by the payment verification layer.
    """

    if not is_configured():

        raise RuntimeError(
            "Razorpay credentials are not configured."
        )

    order_id = str(
        order_id or ""
    ).strip()

    if not order_id:

        raise ValueError(
            "Razorpay order ID is required."
        )

    client = get_client()

    response = client.order.fetch(
        order_id
    )

    return {
        "success": True,

        "id": response.get(
            "id"
        ),

        "amount": response.get(
            "amount"
        ),

        "amount_rupees": paise_to_amount(
            response.get(
                "amount",
                0,
            )
        ),

        "amount_paid": response.get(
            "amount_paid",
            0,
        ),

        "amount_due": response.get(
            "amount_due",
            0,
        ),

        "currency": response.get(
            "currency",
            "INR",
        ),

        "receipt": response.get(
            "receipt"
        ),

        "status": response.get(
            "status"
        ),

        "attempts": response.get(
            "attempts",
            0,
        ),

        "notes": response.get(
            "notes",
            {},
        ),

        "test_mode": True,
    }


# ============================================================
# VERIFY RAZORPAY PAYMENT SIGNATURE
# ============================================================

def verify_razorpay_payment(
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature,
):
    """
    Verify a Razorpay Checkout payment signature.

    Razorpay verification is based on:

        razorpay_order_id
        +
        "|"
        +
        razorpay_payment_id

    signed using the Razorpay Key Secret.

    The Razorpay Python SDK performs the HMAC-SHA256
    verification internally.

    IMPORTANT:
        This function must run on the server.

        The Key Secret is never returned to the frontend.

    Returns:

        Valid signature:

            {
                "success": True,
                "verified": True,
                ...
            }

        Invalid signature:

            {
                "success": False,
                "verified": False,
                ...
            }
    """

    if not is_configured():

        raise RuntimeError(
            "Razorpay credentials are not configured."
        )

    razorpay_order_id = str(
        razorpay_order_id or ""
    ).strip()

    razorpay_payment_id = str(
        razorpay_payment_id or ""
    ).strip()

    razorpay_signature = str(
        razorpay_signature or ""
    ).strip()

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if not razorpay_order_id:

        raise ValueError(
            "Razorpay order ID is required."
        )

    if not razorpay_payment_id:

        raise ValueError(
            "Razorpay payment ID is required."
        )

    if not razorpay_signature:

        raise ValueError(
            "Razorpay payment signature is required."
        )

    client = get_client()

    parameters = {
        "razorpay_order_id":
            razorpay_order_id,

        "razorpay_payment_id":
            razorpay_payment_id,

        "razorpay_signature":
            razorpay_signature,
    }

    # ========================================================
    # SERVER-SIDE SIGNATURE VERIFICATION
    # ========================================================

    try:

        verified = (
            client.utility.verify_payment_signature(
                parameters
            )
        )

    except Exception:

        # Never expose the Razorpay Key Secret.
        # Never return the raw SDK exception to the frontend.

        return {
            "success": False,

            "verified": False,

            "error":
                "Razorpay payment signature verification failed.",

            "razorpay_order_id":
                razorpay_order_id,

            "razorpay_payment_id":
                razorpay_payment_id,

            "test_mode":
                True,
        }

    # ========================================================
    # SUCCESS
    # ========================================================

    return {
        "success": True,

        "verified": bool(
            verified
        ),

        "razorpay_order_id":
            razorpay_order_id,

        "razorpay_payment_id":
            razorpay_payment_id,

        "test_mode":
            True,
    }


# ============================================================
# LEGACY COMPATIBILITY
# ============================================================

def init_payment():
    """
    Backward-compatible payment initialization helper.

    This does not create an order.

    It only reports whether the Razorpay integration is
    configured.
    """

    return {
        "status": (
            "configured"
            if is_configured()
            else "not_configured"
        ),

        "provider":
            "razorpay",

        "test_mode":
            True,

        "key_id_configured":
            bool(
                RAZORPAY_KEY_ID
            ),

        "key_secret_configured":
            bool(
                RAZORPAY_KEY_SECRET
            ),
    }


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [

    "is_configured",

    "get_client",

    "amount_to_paise",

    "paise_to_amount",

    "generate_receipt",

    "create_razorpay_order",

    "fetch_razorpay_order",

    "verify_razorpay_payment",

    "init_payment",
]