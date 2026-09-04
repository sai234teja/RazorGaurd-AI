"""
RazorGuard AI - Merchant Offer Normalizer

Converts offers from different merchant/feed formats
into one safe internal format.

IMPORTANT:
This module does NOT invent prices or URLs.
It only normalizes data supplied by a legitimate source.
"""

from datetime import datetime, timezone
from urllib.parse import urlparse


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_AVAILABILITY = {
    "in_stock",
    "out_of_stock",
    "preorder",
    "unknown",
}


# ============================================================
# URL VALIDATION
# ============================================================

def normalize_url(value):
    """
    Return a valid HTTP/HTTPS URL or an empty string.

    We never manufacture a merchant URL.
    """

    if value is None:
        return ""

    value = str(value).strip()

    if not value:
        return ""

    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"}:
        return ""

    if not parsed.netloc:
        return ""

    return value


# ============================================================
# AVAILABILITY
# ============================================================

def normalize_availability(value):
    """
    Normalize merchant availability values.
    """

    if value is None:
        return "unknown"

    value = str(value).strip().lower()

    mapping = {
        "available": "in_stock",
        "in stock": "in_stock",
        "instock": "in_stock",
        "yes": "in_stock",
        "true": "in_stock",

        "out of stock": "out_of_stock",
        "outofstock": "out_of_stock",
        "unavailable": "out_of_stock",
        "no": "out_of_stock",
        "false": "out_of_stock",

        "pre-order": "preorder",
        "pre order": "preorder",
    }

    value = mapping.get(
        value,
        value,
    )

    if value not in ALLOWED_AVAILABILITY:
        return "unknown"

    return value


# ============================================================
# NUMBER HELPERS
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:

        if value is None:
            return default

        if isinstance(value, str):

            value = (
                value
                .replace(",", "")
                .replace("₹", "")
                .strip()
            )

            if not value:
                return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


def safe_int(value, default=None):
    """
    Safely convert a value to int.
    """

    try:

        if value is None:
            return default

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return default

        return int(float(value))

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# OFFER VALIDATION
# ============================================================

def validate_offer(offer):
    """
    Validate the minimum information required for an offer.

    Returns:

        (True, [])

    or:

        (False, ["reason"])
    """

    errors = []

    if not isinstance(
        offer,
        dict,
    ):

        return (
            False,
            ["offer must be a dictionary"],
        )

    product_id = str(
        offer.get(
            "product_id",
            "",
        )
    ).strip()

    if not product_id:

        errors.append(
            "missing product_id"
        )

    merchant_id = str(
        offer.get(
            "merchant_id",
            "",
        )
    ).strip()

    if not merchant_id:

        errors.append(
            "missing merchant_id"
        )

    merchant_name = str(
        offer.get(
            "merchant_name",
            "",
        )
    ).strip()

    if not merchant_name:

        errors.append(
            "missing merchant_name"
        )

    price = safe_float(
        offer.get(
            "price"
        ),
        default=-1,
    )

    if price <= 0:

        errors.append(
            "price must be greater than zero"
        )

    shipping_fee = safe_float(
        offer.get(
            "shipping_fee",
            0,
        ),
        default=-1,
    )

    if shipping_fee < 0:

        errors.append(
            "shipping_fee cannot be negative"
        )

    product_url = normalize_url(
        offer.get(
            "product_url",
            "",
        )
    )

    # A real external offer should normally have a URL.
    # We do not reject it here because internal merchant
    # feeds may temporarily omit it.
    #
    # The source verification layer decides whether an
    # offer without a URL can be considered verified.

    availability = normalize_availability(
        offer.get(
            "availability",
            "unknown",
        )
    )

    if availability not in ALLOWED_AVAILABILITY:

        errors.append(
            "invalid availability"
        )

    return (
        len(errors) == 0,
        errors,
    )


# ============================================================
# NORMALIZE OFFER
# ============================================================

def normalize_offer(
    raw_offer,
    source_type="merchant_feed",
    default_currency="INR",
):
    """
    Normalize one merchant offer.

    No price, URL, or merchant information is invented.

    Returns:

        {
            "product_id": ...,
            "merchant_id": ...,
            "merchant_name": ...,
            "price": ...,
            ...
        }

    Raises ValueError for invalid offers.
    """

    if not isinstance(
        raw_offer,
        dict,
    ):

        raise ValueError(
            "Offer must be a dictionary."
        )

    normalized = {

        "product_id": str(
            raw_offer.get(
                "product_id",
                "",
            )
        ).strip(),

        "merchant_id": str(
            raw_offer.get(
                "merchant_id",
                "",
            )
        ).strip(),

        "merchant_name": str(
            raw_offer.get(
                "merchant_name",
                "",
            )
        ).strip(),

        "price": safe_float(
            raw_offer.get(
                "price"
            ),
            default=0,
        ),

        "currency": str(
            raw_offer.get(
                "currency"
            )
            or default_currency
        ).strip().upper(),

        "product_url": normalize_url(
            raw_offer.get(
                "product_url",
                "",
            )
        ),

        "availability":
            normalize_availability(
                raw_offer.get(
                    "availability",
                    "unknown",
                )
            ),

        "shipping_fee": safe_float(
            raw_offer.get(
                "shipping_fee",
                0,
            ),
            default=0,
        ),

        "delivery_days": safe_int(
            raw_offer.get(
                "delivery_days"
            ),
            default=None,
        ),

        "is_verified": bool(
            raw_offer.get(
                "is_verified",
                False,
            )
        ),

        "source_type": str(
            raw_offer.get(
                "source_type"
            )
            or source_type
        ).strip(),

    }

    valid, errors = validate_offer(
        normalized
    )

    if not valid:

        raise ValueError(
            "Invalid offer: "
            + "; ".join(errors)
        )

    # --------------------------------------------------------
    # SAFETY RULES
    # --------------------------------------------------------

    if normalized["shipping_fee"] < 0:

        raise ValueError(
            "Shipping fee cannot be negative."
        )

    if (
        normalized["delivery_days"]
        is not None
        and normalized["delivery_days"] < 0
    ):

        raise ValueError(
            "Delivery days cannot be negative."
        )

    # A verified offer must have a real URL.
    if (
        normalized["is_verified"]
        and not normalized["product_url"]
    ):

        normalized["is_verified"] = False

    return normalized


# ============================================================
# NORMALIZE MANY OFFERS
# ============================================================

def normalize_offers(
    raw_offers,
    source_type="merchant_feed",
    default_currency="INR",
):
    """
    Normalize a list of merchant offers.

    Invalid offers are skipped instead of crashing the
    entire ingestion process.

    Returns:

        {
            "offers": [...],
            "rejected": [...]
        }
    """

    if raw_offers is None:

        return {
            "offers": [],
            "rejected": [],
        }

    if not isinstance(
        raw_offers,
        list,
    ):

        raise ValueError(
            "raw_offers must be a list."
        )

    normalized_offers = []
    rejected = []

    for index, raw_offer in enumerate(
        raw_offers
    ):

        try:

            offer = normalize_offer(
                raw_offer,
                source_type=source_type,
                default_currency=default_currency,
            )

            normalized_offers.append(
                offer
            )

        except ValueError as exc:

            rejected.append(
                {
                    "index": index,
                    "reason": str(exc),
                    "offer": raw_offer,
                }
            )

    return {
        "offers": normalized_offers,
        "rejected": rejected,
    }


# ============================================================
# FRESHNESS
# ============================================================

def current_utc_timestamp():
    """
    Return an ISO-8601 UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()