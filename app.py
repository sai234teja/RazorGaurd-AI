"""
RazorGuard AI - Flask Web Application

Main web server for:

    AI product recommendations
    Catalog access
    Checkout preparation
    User confirmation
    Purchase Guard authorization
    Razorpay Test Mode order creation
    Razorpay payment signature verification

The frontend is served from:

    frontend/

The application deliberately keeps payment creation behind
explicit confirmation and the Purchase Guard.
"""

from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
)

from flask_cors import CORS

from agent_pipeline import (
    RazorPayCommerceAgent,
)

from backend.catalog_api import (
    catalog_api,
)

from agents.checkout_agent import (
    CheckoutAgent,
)

from backend.razorpay_api import (
    verify_razorpay_payment,
    fetch_razorpay_order,
)

from audit.audit_service import (
    record_event,
)


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# EXISTING AI COMMERCE AGENT
# ============================================================

agent = RazorPayCommerceAgent()


# ============================================================
# CHECKOUT AGENT
# ============================================================

checkout_agent = CheckoutAgent()


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app.config[
    "CATALOG_SERVICE"
] = None


# ============================================================
# BLUEPRINTS
# ============================================================

app.register_blueprint(
    catalog_api
)


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def home():
    """
    Serve the main RazorGuard frontend.
    """

    return send_from_directory(
        "frontend",
        "index.html",
    )


# ============================================================
# AGENTIC COMMERCE (B2A) MANIFEST
# ============================================================

@app.route("/.well-known/agentic-commerce.json", methods=["GET"])
def agentic_commerce_manifest():
    """
    Agent-readable commerce discovery layer.
    Exposes catalog for external AI buyers while keeping
    financial authorization securely bounded and server-controlled.
    """
    from services.catalog_service import CatalogService
    service = CatalogService()
    products = service.search_products()

    manifest = {
        "merchant": "RazorGuard AI Merchant",
        "capabilities": {
            "product_discovery": "allowed",
            "product_selection": "allowed",
            "checkout_authorization": "gated",
            "razorpay_order_creation": "server_controlled",
            "security": "Purchase_Guard_Mandatory"
        },
        "description": "Catalog discovery is agent-readable. Financial authorization is NOT agent-readable and requires server-side validation and explicit confirmation via RazorGuard.",
        "currency": "INR",
        "catalog": []
    }

    for p in products:
        manifest["catalog"].append({
            "product_id": p.get("product_id"),
            "name": p.get("name"),
            "category": p.get("category"),
            "price": p.get("price"),
            "stock": p.get("stock", 0),
            "attributes": p.get("attributes", {})
        })
        
    return jsonify(manifest), 200


@app.route(
    "/<path:filename>"
)
def frontend_files(
    filename,
):
    """
    Serve frontend assets such as:

        script.js
        style.css
        images
    """

    return send_from_directory(
        "frontend",
        filename,
    )


# ============================================================
# AI RECOMMENDATION API
# ============================================================

@app.route(
    "/api/recommend",
    methods=["POST"],
)
def recommend():
    """
    Run the existing AI commerce recommendation pipeline.
    """

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": (
                    "Request body is empty."
                ),
            }), 400

        user_message = (
            data.get(
                "message",
                "",
            )
            .strip()
        )

        if not user_message:

            return jsonify({
                "success": False,
                "error": (
                    "Please enter a product request."
                ),
            }), 400

        # ----------------------------------------------------
        # Existing AI commerce pipeline
        # ----------------------------------------------------

        result = agent.recommend_for_api(
            user_message
        )

        return jsonify({
            "success": True,
            "data": result,
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# API RECOMMENDATION STREAM
# ============================================================

@app.route(
    "/api/recommend/stream",
    methods=["POST"],
)
def recommend_stream_endpoint():
    """
    Agent Pipeline Visualization.
    Uses Server-Sent Events (SSE) to stream the real execution
    stages of the AI commerce pipeline.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is empty."
            }), 400

        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({
                "success": False,
                "error": "Please enter a product request."
            }), 400

        def generate():
            try:
                for chunk in agent.recommend_stream(user_message):
                    yield chunk
            except Exception as e:
                import json
                yield f"data: {json.dumps({'type': 'result', 'success': False, 'error': str(e)})}\n\n"

        from flask import Response
        return Response(generate(), mimetype="text/event-stream")

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# CHECKOUT - PREPARE
# ============================================================

@app.route(
    "/api/checkout/prepare",
    methods=["POST"],
)
def prepare_checkout():
    """
    Prepare a cart for checkout.

    This endpoint does NOT create a Razorpay order.

    It verifies the order total and returns an
    awaiting-confirmation state.
    """

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": (
                    "Request body is empty."
                ),
            }), 400

        items = data.get(
            "items",
            [],
        )

        if not isinstance(
            items,
            list,
        ) or not items:

            return jsonify({
                "success": False,
                "error": (
                    "Checkout requires at least "
                    "one cart item."
                ),
            }), 400

        # ----------------------------------------------------
        # Create application order
        # ----------------------------------------------------

        from services.checkout_service import (
            create_order,
        )

        customer_details = data.get("customer_details", {})

        order = create_order(
            items=items,
            customer_details=customer_details
        )

        # ----------------------------------------------------
        # Prepare checkout
        # ----------------------------------------------------

        result = checkout_agent.prepare_checkout(
            order
        )

        status_code = (
            200
            if result.get(
                "success",
                False,
            )
            else 400
        )

        return jsonify(
            result
        ), status_code

    except Exception as exc:

        return jsonify({
            "success": False,
            "status": "error",
            "error": str(exc),
        }), 500


# ============================================================
# CHECKOUT - CONFIRM
# ============================================================

@app.route(
    "/api/checkout/confirm",
    methods=["POST"],
)
def confirm_checkout():
    """
    Confirm an order after explicit user approval.

    This endpoint marks the order as confirmed.

    It does NOT create a Razorpay order.
    """

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": (
                    "Request body is empty."
                ),
            }), 400

        order = data.get(
            "order"
        )

        if not isinstance(
            order,
            dict,
        ):

            return jsonify({
                "success": False,
                "error": (
                    "A valid order is required."
                ),
            }), 400

        result = checkout_agent.confirm_checkout(
            order
        )

        status_code = (
            200
            if result.get(
                "success",
                False,
            )
            else 400
        )

        return jsonify(
            result
        ), status_code

    except Exception as exc:

        return jsonify({
            "success": False,
            "status": "error",
            "error": str(exc),
        }), 500


# ============================================================
# CHECKOUT - CREATE PAYMENT ORDER
# ============================================================

@app.route(
    "/api/checkout/payment-order",
    methods=["POST"],
)
def create_payment_order():
    """
    Create a Razorpay Test Mode order.

    Security sequence:

        explicit confirmation
                ↓
        total verification
                ↓
        Purchase Guard
                ↓
        Razorpay order

    No payment-provider order is created if any
    safety check fails.
    """

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": (
                    "Request body is empty."
                ),
            }), 400

        order = data.get(
            "order"
        )

        if not isinstance(
            order,
            dict,
        ):

            return jsonify({
                "success": False,
                "error": (
                    "A valid order is required."
                ),
            }), 400

        result = checkout_agent.create_payment_order(
            order
        )

        status = result.get(
            "status",
            "error",
        )

        # ----------------------------------------------------
        # Successful payment-order creation
        # ----------------------------------------------------

        if result.get(
            "success",
            False,
        ):
            # Save the pending order to the database
            from services.order_service import save_pending_order
            save_pending_order(
                internal_order_id=order.get("order_id"),
                razorpay_order_id=result.get("razorpay_order", {}).get("id"),
                order_data=order,
                purchase_guard_data=result.get("purchase_guard", {})
            )

            return jsonify(
                result
            ), 200

        # ----------------------------------------------------
        # Client-side confirmation required
        # ----------------------------------------------------

        if status == "confirmation_required":

            return jsonify(
                result
            ), 400

        # ----------------------------------------------------
        # Purchase blocked
        # ----------------------------------------------------

        if status == "purchase_blocked":

            return jsonify(
                result
            ), 403

        # ----------------------------------------------------
        # Total/order validation failure
        # ----------------------------------------------------

        if status in (
            "rejected",
            "invalid",
        ):

            return jsonify(
                result
            ), 400

        # ----------------------------------------------------
        # Payment provider failure
        # ----------------------------------------------------

        if status == "payment_provider_error":

            return jsonify(
                result
            ), 502

        return jsonify(
            result
        ), 400

    except Exception as exc:

        return jsonify({
            "success": False,
            "status": "error",
            "error": str(exc),
        }), 500


# ============================================================
# CHECKOUT - VERIFY PAYMENT
# ============================================================

@app.route(
    "/api/checkout/verify-payment",
    methods=["POST"],
)
def verify_payment():
    """
    Verify a Razorpay Checkout payment server-side.

    Expected request:

        {
            "order": {
                ...
                "order_id": "Razorpay order ID",
                "total": 2499,
                "currency": "INR"
            },

            "razorpay_payment_id":
                "...",

            "razorpay_order_id":
                "...",

            "razorpay_signature":
                "..."
        }

    Security sequence:

        browser payment response
                ↓
        validate required fields
                ↓
        compare Razorpay order ID
        with the application order
                ↓
        verify Razorpay signature
                ↓
        fetch Razorpay order
                ↓
        verify amount/currency
                ↓
        return verified result
                ↓
        audit event

    IMPORTANT:

        The Razorpay Key Secret remains on the server.
        It is never returned to the frontend.
    """

    try:

        # ====================================================
        # STEP 1 — READ REQUEST
        # ====================================================

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "status": "invalid_request",
                "error": (
                    "Request body is empty."
                ),
            }), 400

        order = data.get(
            "order"
        )

        razorpay_payment_id = str(
            data.get(
                "razorpay_payment_id",
                "",
            )
            or ""
        ).strip()

        razorpay_order_id = str(
            data.get(
                "razorpay_order_id",
                "",
            )
            or ""
        ).strip()

        razorpay_signature = str(
            data.get(
                "razorpay_signature",
                "",
            )
            or ""
        ).strip()

        # ====================================================
        # STEP 2 — VALIDATE APPLICATION ORDER
        # ====================================================

        if not isinstance(
            order,
            dict,
        ):

            return jsonify({
                "success": False,
                "status": "invalid_request",
                "error": (
                    "A valid application order is required."
                ),
            }), 400

        # ====================================================
        # STEP 3 — VALIDATE PAYMENT FIELDS
        # ====================================================

        if not razorpay_payment_id:

            return jsonify({
                "success": False,
                "status": "invalid_request",
                "error": (
                    "Razorpay payment ID is required."
                ),
            }), 400

        if not razorpay_order_id:

            return jsonify({
                "success": False,
                "status": "invalid_request",
                "error": (
                    "Razorpay order ID is required."
                ),
            }), 400

        if not razorpay_signature:

            return jsonify({
                "success": False,
                "status": "invalid_request",
                "error": (
                    "Razorpay payment signature is required."
                ),
            }), 400

        # ====================================================
        # STEP 4 — VERIFY ORDER ID ASSOCIATION
        # ====================================================

        application_order_id = str(
            order.get(
                "order_id",
                "",
            )
            or ""
        ).strip()

        if not application_order_id:

            return jsonify({
                "success": False,
                "status": "invalid_order",
                "error": (
                    "Application order does not contain "
                    "a Razorpay order ID."
                ),
            }), 400

        if (
            razorpay_order_id
            != application_order_id
        ):

            audit = record_event(
                event=(
                    "PAYMENT_VERIFICATION_FAILED"
                ),
                status="blocked",
                order_id=application_order_id,
                amount=order.get(
                    "total"
                ),
                currency=order.get(
                    "currency",
                    "INR",
                ),
                details={
                    "reason": (
                        "Razorpay order ID does not "
                        "match the application order."
                    ),
                },
            )

            return jsonify({
                "success": False,
                "status": "payment_rejected",
                "error": (
                    "Razorpay order ID does not "
                    "match the application order."
                ),
                "audit": audit,
            }), 400

        # ====================================================
        # STEP 5 — VERIFY SIGNATURE
        # ====================================================

        verification = (
            verify_razorpay_payment(
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature,
            )
        )

        if not verification.get(
            "verified",
            False,
        ):

            audit = record_event(
                event=(
                    "PAYMENT_VERIFICATION_FAILED"
                ),
                status="blocked",
                order_id=razorpay_order_id,
                amount=order.get(
                    "total"
                ),
                currency=order.get(
                    "currency",
                    "INR",
                ),
                details={
                    "reason": (
                        "Razorpay payment signature "
                        "verification failed."
                    ),
                    "payment_id_present": True,
                },
            )

            return jsonify({
                "success": False,
                "status": "payment_rejected",
                "error": (
                    "Razorpay payment signature "
                    "verification failed."
                ),
                "audit": audit,
            }), 400

        # ====================================================
        # STEP 6 — FETCH RAZORPAY ORDER
        # ====================================================

        razorpay_order = (
            fetch_razorpay_order(
                razorpay_order_id
            )
        )

        # ====================================================
        # STEP 7 — VERIFY AMOUNT
        # ====================================================

        application_total = float(
            order.get(
                "total",
                0,
            )
            or 0
        )

        application_amount_paise = int(round(application_total * 100))
        razorpay_amount_paise = int(
            razorpay_order.get(
                "amount",
                0,
            )
            or 0
        )
        
        razorpay_total = float(razorpay_amount_paise) / 100.0

        amount_matches = (
            application_amount_paise == razorpay_amount_paise
        )

        if not amount_matches:

            audit = record_event(
                event=(
                    "PAYMENT_VERIFICATION_FAILED"
                ),
                status="blocked",
                order_id=razorpay_order_id,
                amount=application_total,
                currency=order.get(
                    "currency",
                    "INR",
                ),
                details={
                    "reason": (
                        "Payment amount does not "
                        "match the application order."
                    ),
                    "application_amount":
                        application_total,
                    "razorpay_amount":
                        razorpay_total,
                },
            )

            return jsonify({
                "success": False,
                "status": "payment_rejected",
                "error": (
                    "Payment amount does not "
                    "match the order total."
                ),
                "verification": {
                    "signature_valid": True,
                    "amount_valid": False,
                    "application_amount":
                        application_total,
                    "razorpay_amount":
                        razorpay_total,
                },
                "audit": audit,
            }), 400

        # ====================================================
        # STEP 8 — VERIFY CURRENCY
        # ====================================================

        application_currency = str(
            order.get(
                "currency",
                "INR",
            )
            or "INR"
        ).upper().strip()

        razorpay_currency = str(
            razorpay_order.get(
                "currency",
                "INR",
            )
            or "INR"
        ).upper().strip()

        currency_matches = (
            application_currency
            == razorpay_currency
        )

        if not currency_matches:

            audit = record_event(
                event=(
                    "PAYMENT_VERIFICATION_FAILED"
                ),
                status="blocked",
                order_id=razorpay_order_id,
                amount=application_total,
                currency=application_currency,
                details={
                    "reason": (
                        "Payment currency does not "
                        "match the application order."
                    ),
                    "application_currency":
                        application_currency,
                    "razorpay_currency":
                        razorpay_currency,
                },
            )

            return jsonify({
                "success": False,
                "status": "payment_rejected",
                "error": (
                    "Payment currency does not "
                    "match the order currency."
                ),
                "verification": {
                    "signature_valid": True,
                    "amount_valid": True,
                    "currency_valid": False,
                    "application_currency":
                        application_currency,
                    "razorpay_currency":
                        razorpay_currency,
                },
                "audit": audit,
            }), 400

        # ====================================================
        # STEP 9 — VERIFY RAZORPAY ORDER STATUS
        # ====================================================

        razorpay_status = str(
            razorpay_order.get(
                "status",
                "",
            )
            or ""
        ).lower().strip()

        # At this stage the Razorpay order itself may still
        # be "created" because payment capture/settlement can
        # be represented separately.
        #
        # Signature verification is the authenticity check.
        # We therefore don't reject a valid Test Mode order
        # merely because the order status is not "paid".

        # ====================================================
        # STEP 10 — AUDIT SUCCESS
        # ====================================================

        audit = record_event(
            event=(
                "PAYMENT_VERIFIED"
            ),
            status="success",
            order_id=razorpay_order_id,
            amount=application_total,
            currency=application_currency,
            details={
                "payment_id_present": True,
                "signature_verified": True,
                "amount_verified": True,
                "currency_verified": True,
                "razorpay_status":
                    razorpay_status,
                "test_mode": True,
            },
        )

        # ====================================================
        # STEP 11 — SAVE ORDER AS PAID
        # ====================================================

        from services.order_service import mark_order_paid
        
        mark_order_paid(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id
        )

        # ====================================================
        # STEP 12 — SAFE RESPONSE
        # ====================================================

        return jsonify({
            "success": True,
            "status": "payment_verified",

            "payment": {
                "razorpay_payment_id":
                    razorpay_payment_id,

                "razorpay_order_id":
                    razorpay_order_id,

                "verified":
                    True,
            },

            "order": {
                "order_id":
                    razorpay_order_id,

                "total":
                    application_total,

                "currency":
                    application_currency,

                "payment_status":
                    "verified",
            },

            "verification": {
                "signature_valid":
                    True,

                "amount_valid":
                    True,

                "currency_valid":
                    True,

                "application_amount":
                    application_total,

                "razorpay_amount":
                    razorpay_total,

                "razorpay_status":
                    razorpay_status,
            },

            "razorpay_order": {
                "id":
                    razorpay_order.get(
                        "id"
                    ),

                "status":
                    razorpay_order.get(
                        "status"
                    ),

                "amount_rupees":
                    razorpay_order.get(
                        "amount_rupees"
                    ),

                "currency":
                    razorpay_order.get(
                        "currency"
                    ),

                "test_mode":
                    True,
            },

            "audit":
                audit,

            "test_mode":
                True,
        }), 200

    except Exception as exc:

        # ----------------------------------------------------
        # Do not expose credentials or sensitive SDK data.
        # ----------------------------------------------------

        try:

            audit = record_event(
                event=(
                    "PAYMENT_VERIFICATION_ERROR"
                ),
                status="failed",
                details={
                    "error":
                        str(exc),
                },
            )

        except Exception:

            audit = None

        return jsonify({
            "success": False,
            "status": "verification_error",
            "error": str(exc),
            "audit": audit,
        }), 500


# ============================================================
# ORDERS API
# ============================================================

@app.route(
    "/api/orders",
    methods=["GET"],
)
def get_orders_api():
    """
    Retrieve all paid orders for the user.
    """
    try:
        from services.order_service import get_orders
        orders = get_orders()
        
        return jsonify({
            "success": True,
            "data": orders
        }), 200
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@app.route(
    "/api/orders/<order_id>",
    methods=["GET"],
)
def get_order_api(order_id):
    """
    Retrieve a specific order by its internal order ID.
    """
    try:
        from services.order_service import get_order
        order = get_order(order_id)
        
        if not order:
            return jsonify({
                "success": False,
                "error": "Order not found",
            }), 404
            
        return jsonify({
            "success": True,
            "data": order
        }), 200
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"],
)
def health():
    """
    Basic application health endpoint.

    Useful for checking that Flask is running before
    testing the frontend.
    """

    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "RazorGuard AI",
        "payment_provider": "razorpay",
        "test_mode": True,
    })


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "        RAZORPAY AI COMMERCE AGENT"
    )

    print(
        "              WEB SERVER"
    )

    print("=" * 70)

    print(
        "\nServer starting..."
    )

    print(
        "Open: http://127.0.0.1:5000"
    )

    print(
        "Health: http://127.0.0.1:5000/api/health"
    )

    print(
        "Payment mode: RAZORPAY TEST MODE"
    )

    print(
        "Payment verification: ENABLED"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )