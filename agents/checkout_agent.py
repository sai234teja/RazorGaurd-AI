"""
RazorGuard AI - Checkout Agent

Coordinates the application checkout flow.

Flow:

    Order
      ↓
    Validate
      ↓
    Verify Total
      ↓
    User Confirmation
      ↓
    Purchase Guard
      ↓
    Razorpay Test Order
      ↓
    Audit Trail

IMPORTANT:
This agent does not capture/charge a payment.
It only creates a Razorpay Order after explicit confirmation
AND successful Purchase Guard authorization.
"""

import os

from dotenv import load_dotenv

from services.checkout_service import (
    verify_order_total,
    confirm_order,
)

from backend.razorpay_api import (
    create_razorpay_order,
)

from agents.purchase_guard import (
    evaluate_purchase,
)

from audit.audit_service import (
    record_checkout_prepared,
    record_user_confirmed,
    record_order_total_verification_failed,
    record_purchase_guard_allowed,
    record_purchase_guard_blocked,
    record_razorpay_order_created,
    record_payment_failed,
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CHECKOUT AGENT
# ============================================================

class CheckoutAgent:
    """
    Coordinates safe checkout preparation.

    The agent separates:

        order calculation
        order verification
        user confirmation
        purchase authorization
        payment-provider order creation
        audit logging

    The Purchase Guard is an independent deterministic
    safety boundary before Razorpay.
    """

    def __init__(self):
        self.provider = "razorpay"
        self.test_mode = True

    # ========================================================
    # PREPARE CHECKOUT
    # ========================================================

    def prepare_checkout(self, order):
        """
        Validate and prepare an order for user confirmation.

        This method DOES NOT create a Razorpay order.
        """

        if not isinstance(order, dict):
            return {
                "success": False,
                "status": "invalid",
                "error": "Order must be an object.",
            }

        # ----------------------------------------------------
        # Verify calculated total
        # ----------------------------------------------------

        verification = verify_order_total(order)

        if not verification["valid"]:

            try:
                audit_event = record_order_total_verification_failed(
                    order,
                    verification,
                )

            except Exception as exc:

                audit_event = {
                    "event": "ORDER_TOTAL_VERIFICATION_FAILED",
                    "status": "audit_failed",
                    "error": str(exc),
                }

            return {
                "success": False,
                "status": "rejected",
                "error": "Order total verification failed.",
                "verification": verification,
                "audit": audit_event,
            }

        # ----------------------------------------------------
        # AUDIT: CHECKOUT PREPARED
        # ----------------------------------------------------

        try:
            audit_event = record_checkout_prepared(
                order
            )

        except Exception as exc:

            audit_event = {
                "event": "CHECKOUT_PREPARED",
                "status": "audit_failed",
                "error": str(exc),
            }

        # ----------------------------------------------------
        # Checkout is ready for confirmation
        # ----------------------------------------------------

        return {
            "success": True,
            "status": "awaiting_confirmation",
            "order": order,
            "verification": verification,
            "payment_provider": self.provider,
            "test_mode": self.test_mode,
            "requires_user_confirmation": True,
            "audit": audit_event,
        }

    # ========================================================
    # CONFIRM CHECKOUT
    # ========================================================

    def confirm_checkout(self, order):
        """
        Confirm an order after explicit user approval.

        This method marks the order as confirmed.

        It does NOT create a Razorpay order yet.
        """

        if not isinstance(order, dict):
            return {
                "success": False,
                "status": "invalid",
                "error": "Order must be an object.",
            }

        try:
            confirmed_order = confirm_order(
                order
            )

        except ValueError as exc:

            return {
                "success": False,
                "status": "rejected",
                "error": str(exc),
            }

        # ----------------------------------------------------
        # AUDIT: USER CONFIRMED
        # ----------------------------------------------------

        try:
            audit_event = record_user_confirmed(
                confirmed_order
            )

        except Exception as exc:

            audit_event = {
                "event": "USER_CONFIRMED",
                "status": "audit_failed",
                "error": str(exc),
            }

        return {
            "success": True,
            "status": "confirmed",
            "order": confirmed_order,
            "payment_provider": self.provider,
            "test_mode": self.test_mode,
            "audit": audit_event,
        }

    # ========================================================
    # CREATE PAYMENT ORDER
    # ========================================================

    def create_payment_order(self, order):
        """
        Create a Razorpay Order after:

            1. Explicit user confirmation
            2. Total verification
            3. Purchase Guard authorization

        Razorpay is never called before these checks.
        """

        # ----------------------------------------------------
        # Basic order validation
        # ----------------------------------------------------

        if not isinstance(order, dict):
            return {
                "success": False,
                "status": "invalid",
                "error": "Order must be an object.",
            }

        # ----------------------------------------------------
        # Explicit confirmation check
        # ----------------------------------------------------

        if not order.get(
            "user_confirmed",
            False,
        ):

            return {
                "success": False,
                "status": "confirmation_required",
                "error": (
                    "Explicit user confirmation "
                    "is required before payment."
                ),
                "requires_user_confirmation": True,
            }

        # ----------------------------------------------------
        # Verify total again
        # ----------------------------------------------------

        verification = verify_order_total(
            order
        )

        if not verification["valid"]:

            try:

                audit_event = (
                    record_order_total_verification_failed(
                        order,
                        verification,
                    )
                )

            except Exception as exc:

                audit_event = {
                    "event": (
                        "ORDER_TOTAL_VERIFICATION_FAILED"
                    ),
                    "status": "audit_failed",
                    "error": str(exc),
                }

            return {
                "success": False,
                "status": "rejected",
                "error": (
                    "Order total verification failed "
                    "before payment."
                ),
                "verification": verification,
                "audit": audit_event,
            }

        # ----------------------------------------------------
        # PURCHASE GUARD
        # ----------------------------------------------------

        guard_result = evaluate_purchase(
            order
        )

        # ----------------------------------------------------
        # Guard BLOCKED
        # ----------------------------------------------------

        if not guard_result.get(
            "allowed",
            False,
        ):

            try:

                audit_event = record_purchase_guard_blocked(
                    order,
                    guard_result,
                )

            except Exception as exc:

                audit_event = {
                    "event": "PURCHASE_GUARD_BLOCKED",
                    "status": "audit_failed",
                    "error": str(exc),
                }

            return {
                "success": False,
                "status": "purchase_blocked",
                "error": (
                    "Purchase Guard blocked "
                    "the transaction."
                ),
                "guard": guard_result,
                "verification": verification,
                "audit": audit_event,
            }

        # ----------------------------------------------------
        # Guard ALLOWED
        # ----------------------------------------------------

        try:

            audit_guard_event = (
                record_purchase_guard_allowed(
                    order,
                    guard_result,
                )
            )

        except Exception as exc:

            audit_guard_event = {
                "event": "PURCHASE_GUARD_ALLOWED",
                "status": "audit_failed",
                "error": str(exc),
            }

        # ----------------------------------------------------
        # Read order amount
        # ----------------------------------------------------

        amount = order.get(
            "total"
        )

        if amount is None:

            return {
                "success": False,
                "status": "invalid",
                "error": (
                    "Order total is required."
                ),
            }

        currency = (
            order.get(
                "currency",
                "INR",
            )
            or "INR"
        )

        # ----------------------------------------------------
        # Build safe Razorpay notes
        # ----------------------------------------------------

        notes = {
            "source": "RazorGuard AI",
            "order_status": str(
                order.get(
                    "status",
                    "confirmed",
                )
            ),
            "purchase_guard": "allowed",
        }

        # ----------------------------------------------------
        # Add first product information
        # ----------------------------------------------------

        items = order.get(
            "items",
            [],
        )

        if items:

            first_item = items[0]

            if isinstance(
                first_item,
                dict,
            ):

                product_id = first_item.get(
                    "product_id"
                )

                if product_id:

                    notes[
                        "product_id"
                    ] = str(
                        product_id
                    )

        # ----------------------------------------------------
        # Create Razorpay Test Order
        # ----------------------------------------------------

        try:

            razorpay_order = create_razorpay_order(
                amount=amount,
                currency=currency,
                notes=notes,
            )

        except Exception as exc:

            try:

                audit_event = record_payment_failed(
                    order,
                    exc,
                )

            except Exception as audit_exc:

                audit_event = {
                    "event": "PAYMENT_FAILED",
                    "status": "audit_failed",
                    "error": str(audit_exc),
                }

            return {
                "success": False,
                "status": "payment_provider_error",
                "error": str(exc),
                "guard": guard_result,
                "audit": audit_event,
            }

        # ----------------------------------------------------
        # Update application order
        # ----------------------------------------------------

        updated_order = dict(
            order
        )

        updated_order[
            "order_id"
        ] = razorpay_order.get(
            "id"
        )

        updated_order[
            "status"
        ] = "payment_pending"

        updated_order[
            "payment_status"
        ] = "payment_pending"

        # ----------------------------------------------------
        # AUDIT: RAZORPAY ORDER CREATED
        # ----------------------------------------------------

        try:

            audit_payment_event = (
                record_razorpay_order_created(
                    updated_order,
                    razorpay_order,
                )
            )

        except Exception as exc:

            audit_payment_event = {
                "event": "RAZORPAY_ORDER_CREATED",
                "status": "audit_failed",
                "error": str(exc),
            }

        # ----------------------------------------------------
        # PUBLIC RAZORPAY KEY ID
        # ----------------------------------------------------

        razorpay_key_id = os.getenv(
            "RAZORPAY_KEY_ID",
            "",
        ).strip()

        # ----------------------------------------------------
        # Return safe checkout response
        #
        # IMPORTANT:
        # Only the PUBLIC Key ID is returned.
        # NEVER return RAZORPAY_KEY_SECRET.
        # ----------------------------------------------------

        return {
            "success": True,
            "status": "payment_pending",
            "order": updated_order,
            "razorpay_order": razorpay_order,
            "razorpay_key_id": razorpay_key_id,
            "purchase_guard": guard_result,
            "audit": {
                "purchase_guard": audit_guard_event,
                "razorpay_order": audit_payment_event,
            },
            "test_mode": True,
        }


# ============================================================
# MODULE-LEVEL AGENT
# ============================================================

checkout_agent = CheckoutAgent()


# ============================================================
# BACKWARD-COMPATIBLE FUNCTION
# ============================================================

def prepare_checkout(
    order,
):
    """
    Backward-compatible wrapper for existing imports.
    """

    return checkout_agent.prepare_checkout(
        order
    )


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def confirm_checkout(
    order,
):
    """
    Confirm an order through the shared checkout agent.
    """

    return checkout_agent.confirm_checkout(
        order
    )


def create_payment_order(
    order,
):
    """
    Create a Razorpay Test Order after:

        confirmation
        ↓
        total verification
        ↓
        Purchase Guard authorization
        ↓
        audit logging
    """

    return checkout_agent.create_payment_order(
        order
    )


__all__ = [
    "CheckoutAgent",
    "checkout_agent",
    "prepare_checkout",
    "confirm_checkout",
    "create_payment_order",
]