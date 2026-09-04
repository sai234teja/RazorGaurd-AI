"""
RazorGuard AI - Checkout Service

Responsible for building and validating an application-level
checkout order before any payment provider is called.

This module does NOT create a Razorpay order yet.

Flow:

    Recommended Product
            ↓
       Checkout Service
            ↓
       Order Calculation
            ↓
       Purchase Guard
            ↓
       Razorpay
"""


from datetime import datetime, timezone


# ============================================================
# CHECKOUT CONSTANTS
# ============================================================

DEFAULT_CURRENCY = "INR"

DEFAULT_SHIPPING_FEE = 0.0

MAX_ORDER_ITEMS = 20

MAX_SINGLE_ITEM_QUANTITY = 10


# ============================================================
# VALIDATION HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    """
    Convert a value to float safely.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value, default=0):
    """
    Convert a value to integer safely.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _clean_string(value, default=""):
    """
    Return a clean string.
    """

    if value is None:
        return default

    return str(value).strip()


# ============================================================
# ITEM VALIDATION
# ============================================================

def validate_item(item):
    """
    Validate one checkout item.

    Required:
        product_id
        name
        price
        quantity

    Returns:

        {
            "valid": True/False,
            "errors": [...]
        }
    """

    errors = []

    if not isinstance(item, dict):

        return {
            "valid": False,
            "errors": [
                "Checkout item must be an object."
            ],
        }

    product_id = _clean_string(
        item.get("product_id")
    )

    name = _clean_string(
        item.get("name")
    )

    price = _safe_float(
        item.get("price"),
        -1,
    )

    quantity = _safe_int(
        item.get("quantity"),
        0,
    )

    # --------------------------------------------------------
    # PRODUCT ID
    # --------------------------------------------------------

    if not product_id:

        errors.append(
            "Product ID is required."
        )

    # --------------------------------------------------------
    # PRODUCT NAME
    # --------------------------------------------------------

    if not name:

        errors.append(
            "Product name is required."
        )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    if price < 0:

        errors.append(
            "Product price must be zero or greater."
        )

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    if quantity <= 0:

        errors.append(
            "Quantity must be greater than zero."
        )

    elif quantity > MAX_SINGLE_ITEM_QUANTITY:

        errors.append(
            "Quantity exceeds the allowed limit."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


# ============================================================
# NORMALIZE ITEM
# ============================================================

def normalize_item(item):
    """
    Normalize one checkout item into a predictable structure.
    """

    validation = validate_item(
        item
    )

    if not validation["valid"]:

        raise ValueError(
            "; ".join(
                validation["errors"]
            )
        )

    product_id = _clean_string(item.get("product_id"))
    
    from services.catalog_service import CatalogService
    catalog = CatalogService()
    db_product = catalog.get_product(product_id)
    
    if not db_product:
        raise ValueError(f"Product {product_id} not found in catalog.")
        
    authoritative_price = round(_safe_float(db_product.get("price")), 2)
    client_price = round(_safe_float(item.get("price")), 2)
    
    if client_price != authoritative_price:
        try:
            from audit.audit_service import record_event
            record_event(
                event="PRICE_TAMPERING_DETECTED",
                status="blocked",
                details={
                    "product_id": product_id,
                    "client_price": client_price,
                    "authoritative_price": authoritative_price
                }
            )
        except Exception:
            pass
        raise ValueError(f"Price mismatch for product {product_id}.")

    price = authoritative_price

    quantity = _safe_int(
        item.get("quantity"),
        1,
    )

    line_total = round(
        price * quantity,
        2,
    )

    return {
        "product_id": _clean_string(
            item.get("product_id")
        ),

        "name": _clean_string(
            item.get("name")
        ),

        "brand": _clean_string(
            item.get("brand")
        ),

        "price": price,

        "quantity": quantity,

        "line_total": line_total,

        "currency": _clean_string(
            item.get(
                "currency",
                DEFAULT_CURRENCY,
            ),
            DEFAULT_CURRENCY,
        ),

        "product_url": _clean_string(
            item.get("product_url")
        ),

        "merchant_id": _clean_string(
            item.get("merchant_id")
        ),

        "merchant_name": _clean_string(
            item.get("merchant_name")
        ),
    }


# ============================================================
# CREATE ORDER
# ============================================================

def create_order(
    items,
    shipping_fee=DEFAULT_SHIPPING_FEE,
    customer_details=None,
):
    """
    Build an application-level checkout order.

    IMPORTANT:
        This function does NOT call Razorpay.

    It only calculates the order that will later be passed
    through the Purchase Guard and payment layer.
    """

    if not isinstance(
        items,
        list,
    ):

        raise ValueError(
            "items must be a list."
        )

    if not items:

        raise ValueError(
            "At least one checkout item is required."
        )

    if len(items) > MAX_ORDER_ITEMS:

        raise ValueError(
            "Order contains too many items."
        )

    normalized_items = []

    for item in items:

        normalized_items.append(
            normalize_item(
                item
            )
        )

    subtotal = round(
        sum(
            item["line_total"]
            for item in normalized_items
        ),
        2,
    )

    shipping = round(
        max(
            0,
            _safe_float(
                shipping_fee
            ),
        ),
        2,
    )

    total = round(
        subtotal + shipping,
        2,
    )

    currency = (
        normalized_items[0].get(
            "currency",
            DEFAULT_CURRENCY,
        )
        or DEFAULT_CURRENCY
    )

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    import uuid
    internal_order_id = "RG_" + uuid.uuid4().hex[:12].upper()

    return {
        "order_id": internal_order_id,

        "status": "pending",

        "items": normalized_items,

        "item_count": len(
            normalized_items
        ),

        "subtotal": subtotal,

        "shipping_fee": shipping,

        "discount": 0.0,

        "total": total,

        "currency": currency,

        "created_at": created_at,

        "payment_provider": "razorpay",

        "payment_status": "not_started",

        "user_confirmed": False,

        "customer_details": customer_details or {},
    }


# ============================================================
# ORDER TOTAL
# ============================================================

def calculate_order_total(
    order,
):
    """
    Recalculate the order total from its line items.

    This is intentionally deterministic so the Purchase Guard
    can independently verify the amount before payment.
    """

    if not isinstance(
        order,
        dict,
    ):

        raise ValueError(
            "Order must be an object."
        )

    items = order.get(
        "items",
        [],
    )

    if not isinstance(
        items,
        list,
    ):

        raise ValueError(
            "Order items must be a list."
        )

    subtotal = round(
        sum(
            round(
                _safe_float(
                    item.get("price")
                )
                *
                _safe_int(
                    item.get(
                        "quantity",
                        1,
                    ),
                    1,
                ),
                2,
            )
            for item in items
        ),
        2,
    )

    shipping_fee = round(
        max(
            0,
            _safe_float(
                order.get(
                    "shipping_fee",
                    0,
                )
            ),
        ),
        2,
    )

    discount = round(
        max(
            0,
            _safe_float(
                order.get(
                    "discount",
                    0,
                )
            ),
        ),
        2,
    )

    total = round(
        subtotal
        + shipping_fee
        - discount,
        2,
    )

    return total


# ============================================================
# VERIFY ORDER TOTAL
# ============================================================

def verify_order_total(
    order,
):
    """
    Verify that the stored order total matches a fresh
    calculation.

    This will later be used by Purchase Guard.
    """

    if not isinstance(
        order,
        dict,
    ):

        return {
            "valid": False,
            "calculated_total": 0.0,
            "declared_total": 0.0,
            "difference": 0.0,
        }

    calculated_total = calculate_order_total(
        order
    )

    declared_total = round(
        _safe_float(
            order.get(
                "total",
                0,
            )
        ),
        2,
    )

    difference = round(
        abs(
            calculated_total
            - declared_total
        ),
        2,
    )

    return {
        "valid": difference == 0,
        "calculated_total": calculated_total,
        "declared_total": declared_total,
        "difference": difference,
    }


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

def update_order_status(
    order,
    status,
):
    """
    Return a copy of the order with an updated status.
    """

    if not isinstance(
        order,
        dict,
    ):

        raise ValueError(
            "Order must be an object."
        )

    allowed_statuses = {
        "pending",
        "confirmed",
        "payment_pending",
        "paid",
        "failed",
        "cancelled",
    }

    status = _clean_string(
        status
    ).lower()

    if status not in allowed_statuses:

        raise ValueError(
            f"Invalid order status: {status}"
        )

    updated = dict(
        order
    )

    updated["status"] = status

    return updated


# ============================================================
# CONFIRM ORDER
# ============================================================

def confirm_order(
    order,
):
    """
    Mark an order as user-confirmed.

    This does NOT initiate payment.

    The Purchase Guard will later require this flag before
    a Razorpay order can be created.
    """

    if not isinstance(
        order,
        dict,
    ):

        raise ValueError(
            "Order must be an object."
        )

    verified = verify_order_total(
        order
    )

    if not verified["valid"]:

        raise ValueError(
            "Order total verification failed."
        )

    updated = dict(
        order
    )

    updated["user_confirmed"] = True

    updated["status"] = "confirmed"

    return updated


# ============================================================
# CHECKOUT SUMMARY
# ============================================================

def get_checkout_summary(
    order,
):
    """
    Return a frontend-safe checkout summary.
    """

    if not isinstance(
        order,
        dict,
    ):

        raise ValueError(
            "Order must be an object."
        )

    return {
        "item_count": int(
            order.get(
                "item_count",
                len(
                    order.get(
                        "items",
                        [],
                    )
                ),
            )
        ),

        "subtotal": round(
            _safe_float(
                order.get(
                    "subtotal",
                    0,
                )
            ),
            2,
        ),

        "shipping_fee": round(
            _safe_float(
                order.get(
                    "shipping_fee",
                    0,
                )
            ),
            2,
        ),

        "discount": round(
            _safe_float(
                order.get(
                    "discount",
                    0,
                )
            ),
            2,
        ),

        "total": round(
            _safe_float(
                order.get(
                    "total",
                    0,
                )
            ),
            2,
        ),

        "currency": _clean_string(
            order.get(
                "currency",
                DEFAULT_CURRENCY,
            ),
            DEFAULT_CURRENCY,
        ),

        "status": _clean_string(
            order.get(
                "status",
                "pending",
            ),
            "pending",
        ),

        "payment_status": _clean_string(
            order.get(
                "payment_status",
                "not_started",
            ),
            "not_started",
        ),

        "user_confirmed": bool(
            order.get(
                "user_confirmed",
                False,
            )
        ),
    }


__all__ = [
    "create_order",
    "validate_item",
    "normalize_item",
    "calculate_order_total",
    "verify_order_total",
    "update_order_status",
    "confirm_order",
    "get_checkout_summary",
]