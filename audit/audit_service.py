"""
RazorGuard AI - Audit Service

Centralized audit logging for checkout and payment events.

The audit trail records important state transitions without
storing sensitive payment credentials or secrets.

Example events:

    CHECKOUT_PREPARED
    USER_CONFIRMED
    ORDER_TOTAL_VERIFICATION_FAILED
    PURCHASE_GUARD_ALLOWED
    PURCHASE_GUARD_BLOCKED
    RAZORPAY_ORDER_CREATED
    PAYMENT_FAILED
"""

import json
import os
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

AUDIT_DIRECTORY = "audit"

AUDIT_LOG_FILE = os.path.join(
    AUDIT_DIRECTORY,
    "audit.log",
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _ensure_audit_directory():
    """
    Ensure that the audit directory exists.
    """

    os.makedirs(
        AUDIT_DIRECTORY,
        exist_ok=True,
    )


def _timestamp():
    """
    Return a UTC ISO-8601 timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# BASIC LOG WRITER
# ============================================================

def write_audit_log(
    message: str,
):
    """
    Write a plain audit message.

    This preserves the original audit service API so existing
    code using write_audit_log() continues to work.
    """

    _ensure_audit_directory()

    with open(
        AUDIT_LOG_FILE,
        "a",
        encoding="utf-8",
    ) as log_file:

        log_file.write(
            str(message) + "\n"
        )

    return True


# ============================================================
# STRUCTURED AUDIT EVENT
# ============================================================

def record_event(
    event,
    status="info",
    order_id=None,
    product_id=None,
    amount=None,
    currency="INR",
    details=None,
):
    """
    Record a structured audit event.

    Parameters
    ----------
    event:
        Event name such as PURCHASE_GUARD_ALLOWED.

    status:
        Event status such as info, success, blocked, or failed.

    order_id:
        Application/Razorpay order identifier when available.

    product_id:
        Product identifier when available.

    amount:
        Monetary amount in human-readable currency units.

    currency:
        Currency code. Defaults to INR.

    details:
        Additional non-sensitive event information.

    IMPORTANT:
    Never pass API keys, API secrets, passwords, tokens,
    payment signatures, or other credentials to this function.
    """

    if details is None:
        details = {}

    if not isinstance(
        details,
        dict,
    ):
        details = {
            "message": str(details)
        }

    event_record = {
        "timestamp": _timestamp(),

        "event": str(
            event
        ),

        "status": str(
            status
        ),

        "order_id": (
            str(order_id)
            if order_id is not None
            else None
        ),

        "product_id": (
            str(product_id)
            if product_id is not None
            else None
        ),

        "amount": (
            round(
                float(amount),
                2,
            )
            if amount is not None
            else None
        ),

        "currency": str(
            currency or "INR"
        ).upper(),

        "details": details,
    }

    # --------------------------------------------------------
    # JSON Lines format
    # --------------------------------------------------------

    write_audit_log(
        json.dumps(
            event_record,
            ensure_ascii=False,
        )
    )

    return event_record


# ============================================================
# CHECKOUT EVENTS
# ============================================================

def record_checkout_prepared(
    order,
):
    """
    Record that checkout preparation completed.
    """

    if not isinstance(
        order,
        dict,
    ):
        return record_event(
            event="CHECKOUT_PREPARED",
            status="failed",
            details={
                "error": "invalid order"
            },
        )

    items = order.get(
        "items",
        [],
    )

    product_id = None

    if items and isinstance(
        items[0],
        dict,
    ):
        product_id = items[0].get(
            "product_id"
        )

    return record_event(
        event="CHECKOUT_PREPARED",
        status="success",
        order_id=order.get(
            "order_id"
        ),
        product_id=product_id,
        amount=order.get(
            "total"
        ),
        currency=order.get(
            "currency",
            "INR",
        ),
        details={
            "item_count": order.get(
                "item_count",
                len(items),
            ),
        },
    )


def record_user_confirmed(
    order,
):
    """
    Record explicit user confirmation.
    """

    if not isinstance(
        order,
        dict,
    ):
        return record_event(
            event="USER_CONFIRMED",
            status="failed",
            details={
                "error": "invalid order"
            },
        )

    items = order.get(
        "items",
        [],
    )

    product_id = None

    if items and isinstance(
        items[0],
        dict,
    ):
        product_id = items[0].get(
            "product_id"
        )

    return record_event(
        event="USER_CONFIRMED",
        status="success",
        order_id=order.get(
            "order_id"
        ),
        product_id=product_id,
        amount=order.get(
            "total"
        ),
        currency=order.get(
            "currency",
            "INR",
        ),
        details={
            "user_confirmed": True,
        },
    )


# ============================================================
# TOTAL VERIFICATION EVENTS
# ============================================================

def record_order_total_verification_failed(
    order,
    verification=None,
):
    """
    Record a failed monetary-total verification.

    This event is used when the declared order total does not
    match the total independently calculated from the order
    items.

    No payment-provider call should occur after this failure.
    """

    if not isinstance(
        order,
        dict,
    ):
        order = {}

    items = order.get(
        "items",
        [],
    )

    product_id = None

    if items and isinstance(
        items[0],
        dict,
    ):
        product_id = items[0].get(
            "product_id"
        )

    details = {
        "reason": (
            "order total verification failed"
        ),
    }

    if isinstance(
        verification,
        dict,
    ):

        details[
            "calculated_total"
        ] = verification.get(
            "calculated_total"
        )

        details[
            "declared_total"
        ] = verification.get(
            "declared_total"
        )

        details[
            "difference"
        ] = verification.get(
            "difference"
        )

        details[
            "valid"
        ] = verification.get(
            "valid"
        )

    return record_event(
        event="ORDER_TOTAL_VERIFICATION_FAILED",
        status="blocked",
        order_id=order.get(
            "order_id"
        ),
        product_id=product_id,
        amount=order.get(
            "total"
        ),
        currency=order.get(
            "currency",
            "INR",
        ),
        details=details,
    )


# ============================================================
# PURCHASE GUARD EVENTS
# ============================================================

def record_purchase_guard_allowed(
    order,
    guard_result=None,
):
    """
    Record a successful Purchase Guard authorization.

    The audit event records deterministic safety checks and,
    when available, RazorGuard risk information.
    """

    if not isinstance(
        order,
        dict,
    ):
        return record_event(
            event="PURCHASE_GUARD_ALLOWED",
            status="failed",
            details={
                "error": "invalid order"
            },
        )

    items = order.get(
        "items",
        [],
    )

    product_id = None

    if items and isinstance(
        items[0],
        dict,
    ):
        product_id = items[0].get(
            "product_id"
        )

    details = {
        "decision": "allowed",
    }

    if isinstance(
        guard_result,
        dict,
    ):

        # ----------------------------------------------------
        # Existing deterministic checks
        # ----------------------------------------------------

        details[
            "checks"
        ] = guard_result.get(
            "checks",
            {},
        )

        # ----------------------------------------------------
        # RazorGuard risk information
        #
        # These fields are optional for now.
        # They will automatically appear once the
        # Purchase Guard starts calculating them.
        # ----------------------------------------------------

        if "risk_score" in guard_result:

            details[
                "risk_score"
            ] = guard_result.get(
                "risk_score"
            )

        if "risk_level" in guard_result:

            details[
                "risk_level"
            ] = guard_result.get(
                "risk_level"
            )

        if "risk_factors" in guard_result:

            details[
                "risk_factors"
            ] = guard_result.get(
                "risk_factors",
                [],
            )

    return record_event(
        event="PURCHASE_GUARD_ALLOWED",
        status="success",
        order_id=order.get(
            "order_id"
        ),
        product_id=product_id,
        amount=order.get(
            "total"
        ),
        currency=order.get(
            "currency",
            "INR",
        ),
        details=details,
    )


def record_purchase_guard_blocked(
    order,
    guard_result=None,
):
    """
    Record a Purchase Guard rejection.

    The audit event records blocking reasons,
    deterministic safety checks, and RazorGuard
    risk information when available.
    """

    if not isinstance(
        order,
        dict,
    ):
        return record_event(
            event="PURCHASE_GUARD_BLOCKED",
            status="blocked",
            details={
                "error": "invalid order"
            },
        )

    items = order.get(
        "items",
        [],
    )

    product_id = None

    if items and isinstance(
        items[0],
        dict,
    ):
        product_id = items[0].get(
            "product_id"
        )

    details = {
        "decision": "blocked",
    }

    if isinstance(
        guard_result,
        dict,
    ):

        # ----------------------------------------------------
        # Blocking reasons
        # ----------------------------------------------------

        details[
            "reasons"
        ] = guard_result.get(
            "reasons",
            [],
        )

        # ----------------------------------------------------
        # Existing deterministic checks
        # ----------------------------------------------------

        details[
            "checks"
        ] = guard_result.get(
            "checks",
            {},
        )

        # ----------------------------------------------------
        # RazorGuard risk information
        # ----------------------------------------------------

        if "risk_score" in guard_result:

            details[
                "risk_score"
            ] = guard_result.get(
                "risk_score"
            )

        if "risk_level" in guard_result:

            details[
                "risk_level"
            ] = guard_result.get(
                "risk_level"
            )

        if "risk_factors" in guard_result:

            details[
                "risk_factors"
            ] = guard_result.get(
                "risk_factors",
                [],
            )

    return record_event(
        event="PURCHASE_GUARD_BLOCKED",
        status="blocked",
        order_id=order.get(
            "order_id"
        ),
        product_id=product_id,
        amount=order.get(
            "total"
        ),
        currency=order.get(
            "currency",
            "INR",
        ),
        details=details,
    )


# ============================================================
# RAZORPAY EVENTS
# ============================================================

def record_razorpay_order_created(
    order,
    razorpay_order,
):
    """
    Record successful Razorpay Order creation.

    Only non-sensitive order information is recorded.
    """

    if not isinstance(
        order,
        dict,
    ):
        order = {}

    if not isinstance(
        razorpay_order,
        dict,
    ):
        razorpay_order = {}

    items = order.get(
        "items",
        [],
    )

    product_id = None

    if items and isinstance(
        items[0],
        dict,
    ):
        product_id = items[0].get(
            "product_id"
        )

    razorpay_order_id = (
        razorpay_order.get(
            "id"
        )
    )

    return record_event(
        event="RAZORPAY_ORDER_CREATED",
        status="success",
        order_id=razorpay_order_id,
        product_id=product_id,
        amount=razorpay_order.get(
            "amount_rupees",
            order.get(
                "total"
            ),
        ),
        currency=razorpay_order.get(
            "currency",
            order.get(
                "currency",
                "INR",
            ),
        ),
        details={
            "razorpay_status": razorpay_order.get(
                "status"
            ),

            "test_mode": razorpay_order.get(
                "test_mode",
                True,
            ),
        },
    )


def record_payment_failed(
    order,
    error=None,
):
    """
    Record a payment-provider failure.

    Sensitive credentials must never be passed as error
    details.
    """

    if not isinstance(
        order,
        dict,
    ):
        order = {}

    items = order.get(
        "items",
        [],
    )

    product_id = None

    if items and isinstance(
        items[0],
        dict,
    ):
        product_id = items[0].get(
            "product_id"
        )

    details = {}

    if error:
        details[
            "error"
        ] = str(error)

    return record_event(
        event="PAYMENT_FAILED",
        status="failed",
        order_id=order.get(
            "order_id"
        ),
        product_id=product_id,
        amount=order.get(
            "total"
        ),
        currency=order.get(
            "currency",
            "INR",
        ),
        details=details,
    )


# ============================================================
# READ AUDIT LOG
# ============================================================

def read_audit_log():
    """
    Read all audit events.

    Returns a list of parsed JSON events.

    Legacy/plain-text lines are returned as raw records.
    """

    _ensure_audit_directory()

    if not os.path.exists(
        AUDIT_LOG_FILE
    ):
        return []

    events = []

    with open(
        AUDIT_LOG_FILE,
        "r",
        encoding="utf-8",
    ) as log_file:

        for line in log_file:

            line = line.strip()

            if not line:
                continue

            try:

                events.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:

                events.append({
                    "timestamp": None,
                    "event": "LEGACY_LOG",
                    "status": "info",
                    "message": line,
                })

    return events


# ============================================================
# CLEAR AUDIT LOG
# ============================================================

def clear_audit_log():
    """
    Clear the audit log.

    Intended for local development/testing only.
    """

    _ensure_audit_directory()

    with open(
        AUDIT_LOG_FILE,
        "w",
        encoding="utf-8",
    ) as log_file:

        log_file.write(
            "# Audit log\n"
        )

    return True


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "write_audit_log",
    "record_event",
    "record_checkout_prepared",
    "record_user_confirmed",
    "record_order_total_verification_failed",
    "record_purchase_guard_allowed",
    "record_purchase_guard_blocked",
    "record_razorpay_order_created",
    "record_payment_failed",
    "read_audit_log",
    "clear_audit_log",
]