"""
RazorGuard AI - Offer Eligibility

Determines whether a merchant offer is eligible to be used
for a purchase recommendation.

IMPORTANT:
An offer being present in the database does NOT automatically
mean that it is safe to recommend for purchase.

Eligibility considers:
- availability
- price
- merchant identity
- source type
- product URL
- verification status
- freshness
"""

from datetime import datetime, timezone
from urllib.parse import urlparse


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MAX_AGE_HOURS = 24


# ============================================================
# URL CHECK
# ============================================================

def has_valid_url(url):
    """
    Check whether the offer contains a valid HTTP/HTTPS URL.
    """

    if not url:
        return False

    try:

        parsed = urlparse(
            str(url).strip()
        )

        return (
            parsed.scheme in {
                "http",
                "https",
            }
            and bool(parsed.netloc)
        )

    except Exception:

        return False


# ============================================================
# TIMESTAMP PARSER
# ============================================================

def parse_timestamp(value):
    """
    Parse an ISO timestamp.

    Returns None when the timestamp cannot be parsed.
    """

    if not value:
        return None

    try:

        text = str(value).strip()

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        parsed = datetime.fromisoformat(
            text
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================
# FRESHNESS
# ============================================================

def get_offer_age_hours(
    last_checked_at,
):
    """
    Return offer age in hours.

    Returns None if the timestamp is invalid.
    """

    timestamp = parse_timestamp(
        last_checked_at
    )

    if timestamp is None:

        return None

    now = datetime.now(
        timezone.utc
    )

    age = (
        now - timestamp
    ).total_seconds() / 3600

    # Protect against future timestamps.
    if age < 0:

        age = 0

    return age


def is_fresh(
    last_checked_at,
    max_age_hours=DEFAULT_MAX_AGE_HOURS,
):
    """
    Determine whether an offer is recent enough.
    """

    age = get_offer_age_hours(
        last_checked_at
    )

    if age is None:

        return False

    return age <= max_age_hours


# ============================================================
# OFFER ELIGIBILITY
# ============================================================

def evaluate_offer(
    offer,
    max_age_hours=DEFAULT_MAX_AGE_HOURS,
):
    """
    Evaluate one offer.

    Returns a structured decision:

        {
            "eligible": True/False,
            "reasons": [...],
            "warnings": [...],
            "age_hours": ...
        }
    """

    reasons = []
    warnings = []

    if not isinstance(
        offer,
        dict,
    ):

        return {
            "eligible": False,
            "reasons": [
                "invalid offer object"
            ],
            "warnings": [],
            "age_hours": None,
        }

    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    product_id = str(
        offer.get(
            "product_id",
            "",
        )
    ).strip()

    if not product_id:

        return {
            "eligible": False,
            "reasons": [
                "missing product ID"
            ],
            "warnings": [],
            "age_hours": None,
        }

    # --------------------------------------------------------
    # MERCHANT
    # --------------------------------------------------------

    merchant_id = str(
        offer.get(
            "merchant_id",
            "",
        )
    ).strip()

    merchant_name = str(
        offer.get(
            "merchant_name",
            "",
        )
    ).strip()

    if not merchant_id:

        reasons.append(
            "missing merchant ID"
        )

    if not merchant_name:

        reasons.append(
            "missing merchant name"
        )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    try:

        price = float(
            offer.get(
                "price",
                0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        price = 0

    if price <= 0:

        reasons.append(
            "invalid product price"
        )

    # --------------------------------------------------------
    # SHIPPING
    # --------------------------------------------------------

    try:

        shipping_fee = float(
            offer.get(
                "shipping_fee",
                0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        shipping_fee = -1

    if shipping_fee < 0:

        reasons.append(
            "invalid shipping fee"
        )

    # --------------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------------

    availability = str(
        offer.get(
            "availability",
            "unknown",
        )
    ).strip().lower()

    if availability != "in_stock":

        reasons.append(
            "offer is not currently in stock"
        )

    else:

        reasons.append(
            "currently in stock"
        )

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    product_url = offer.get(
        "product_url",
        "",
    )

    valid_url = has_valid_url(
        product_url
    )

    if not valid_url:

        warnings.append(
            "merchant product URL is missing or invalid"
        )

    else:

        reasons.append(
            "merchant product URL available"
        )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    source_type = str(
        offer.get(
            "source_type",
            "",
        )
    ).strip().lower()

    if source_type == "demo":

        warnings.append(
            "offer comes from simulated demo data"
        )

    elif source_type:

        reasons.append(
            f"source: {source_type}"
        )

    else:

        warnings.append(
            "offer source is unspecified"
        )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    is_verified = bool(
        offer.get(
            "is_verified",
            False,
        )
    )

    if is_verified:

        if valid_url:

            reasons.append(
                "source marked as verified"
            )

        else:

            warnings.append(
                "verification flag ignored because URL is invalid"
            )

            is_verified = False

    # --------------------------------------------------------
    # FRESHNESS
    # --------------------------------------------------------

    last_checked_at = offer.get(
        "last_checked_at"
    )

    age_hours = get_offer_age_hours(
        last_checked_at
    )

    if age_hours is None:

        warnings.append(
            "offer freshness cannot be verified"
        )

    elif age_hours <= max_age_hours:

        reasons.append(
            "offer price is fresh"
        )

    else:

        warnings.append(
            "offer price is stale"
        )

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    eligible = True

    # Basic requirements.
    if not merchant_id:
        eligible = False

    if not merchant_name:
        eligible = False

    if price <= 0:
        eligible = False

    if shipping_fee < 0:
        eligible = False

    if availability != "in_stock":
        eligible = False

    # Demo offers are NEVER eligible for a real purchase
    # decision.
    if source_type == "demo":
        eligible = False

    # A verified purchase candidate needs a valid URL.
    if is_verified and not valid_url:
        eligible = False

    # Freshness is required for a verified offer.
    if is_verified and age_hours is None:
        eligible = False

    if (
        is_verified
        and age_hours is not None
        and age_hours > max_age_hours
    ):
        eligible = False

    return {
        "eligible": eligible,
        "reasons": reasons,
        "warnings": warnings,
        "age_hours": age_hours,
        "is_verified": is_verified,
        "has_valid_url": valid_url,
        "source_type": source_type,
    }


# ============================================================
# FILTER ELIGIBLE OFFERS
# ============================================================

def filter_eligible_offers(
    offers,
    max_age_hours=DEFAULT_MAX_AGE_HOURS,
):
    """
    Return only offers eligible for a purchase decision.

    Also returns evaluation information for every offer.
    """

    eligible = []
    rejected = []

    if not isinstance(
        offers,
        list,
    ):

        return {
            "eligible": [],
            "rejected": [],
        }

    for offer in offers:

        evaluation = evaluate_offer(
            offer,
            max_age_hours=max_age_hours,
        )

        result = {
            "offer": offer,
            "evaluation": evaluation,
        }

        if evaluation["eligible"]:

            eligible.append(
                result
            )

        else:

            rejected.append(
                result
            )

    return {
        "eligible": eligible,
        "rejected": rejected,
    }


# ============================================================
# LOWEST ELIGIBLE OFFER
# ============================================================

def get_lowest_eligible_offer(
    offers,
    max_age_hours=DEFAULT_MAX_AGE_HOURS,
):
    """
    Find the lowest total-cost eligible offer.

    Total cost:

        product price + shipping fee
    """

    result = filter_eligible_offers(
        offers,
        max_age_hours=max_age_hours,
    )

    eligible = result[
        "eligible"
    ]

    if not eligible:

        return {
            "offer": None,
            "evaluation": None,
            "eligible_count": 0,
            "rejected_count":
                len(result["rejected"]),
        }

    best = min(
        eligible,
        key=lambda item: (
            float(
                item["offer"].get(
                    "price",
                    0,
                )
            )
            +
            float(
                item["offer"].get(
                    "shipping_fee",
                    0,
                )
            )
        ),
    )

    return {
        "offer": best["offer"],
        "evaluation": best["evaluation"],
        "eligible_count":
            len(eligible),
        "rejected_count":
            len(result["rejected"]),
    }