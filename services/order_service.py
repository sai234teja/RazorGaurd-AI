"""
Service for persisting orders securely on the server-side.
"""
import json
import uuid
from datetime import datetime, timezone
from database.database import get_connection

def save_pending_order(internal_order_id, razorpay_order_id, order_data, purchase_guard_data):
    """
    Save a pending order after Purchase Guard succeeds and a Razorpay order is created.
    """
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        customer_details = order_data.get("customer_details", {})
        customer_id = None
        shipping_address_id = None
        
        if customer_details.get("name") and customer_details.get("email"):
            customer_id = "CUST_" + uuid.uuid4().hex[:12].upper()
            shipping_address_id = "ADDR_" + uuid.uuid4().hex[:12].upper()
            
            # Save customer
            conn.execute(
                """
                INSERT INTO customers (customer_id, name, email, phone, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    customer_details.get("name"),
                    customer_details.get("email"),
                    customer_details.get("phone", ""),
                    now,
                    now
                )
            )
            
            # Save address
            conn.execute(
                """
                INSERT INTO addresses (address_id, customer_id, line1, line2, city, state, postal_code, country, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    shipping_address_id,
                    customer_id,
                    customer_details.get("address", ""),
                    "",
                    customer_details.get("city", ""),
                    customer_details.get("state", ""),
                    customer_details.get("pin", ""),
                    "IN",
                    now
                )
            )
        
        # Save main order
        conn.execute(
            """
            INSERT INTO orders (
                internal_order_id, razorpay_order_id, razorpay_payment_id, status, currency, total, payment_provider, 
                purchase_guard_risk_score, purchase_guard_risk_level, purchase_guard_decision, purchase_guard_checks,
                customer_id, shipping_address_id,
                created_at, paid_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                internal_order_id,
                razorpay_order_id,
                None,
                "pending",
                order_data.get("currency", "INR"),
                float(order_data.get("total", 0)),
                "razorpay",
                purchase_guard_data.get("risk_score"),
                purchase_guard_data.get("risk_level"),
                purchase_guard_data.get("decision"),
                json.dumps(purchase_guard_data.get("checks", {})),
                customer_id,
                shipping_address_id,
                now,
                None
            )
        )
        
        # Save order items
        items = order_data.get("items", [])
        for item in items:
            conn.execute(
                """
                INSERT INTO order_items (
                    internal_order_id, product_id, name, quantity, price
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    internal_order_id,
                    item.get("product_id"),
                    item.get("name"),
                    int(item.get("quantity", 1)),
                    float(item.get("price", 0))
                )
            )
            
        conn.commit()
        return internal_order_id
    finally:
        conn.close()

def mark_order_paid(razorpay_order_id, razorpay_payment_id):
    """
    Mark an existing pending order as paid.
    This must ONLY be called after server-side payment signature and amount verification.
    """
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """
            UPDATE orders 
            SET status = 'paid', razorpay_payment_id = ?, paid_at = ?
            WHERE razorpay_order_id = ? AND status != 'paid'
            """,
            (razorpay_payment_id, now, razorpay_order_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_orders():
    """
    Retrieve all paid orders for the user.
    (Currently returns all paid orders as there is no auth system)
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT internal_order_id, razorpay_order_id, status, total, currency, paid_at
            FROM orders
            WHERE status = 'paid'
            ORDER BY paid_at DESC
            """
        ).fetchall()
        
        orders = []
        for row in rows:
            # Fetch simple item summaries
            items = conn.execute(
                "SELECT name, quantity FROM order_items WHERE internal_order_id = ?",
                (row["internal_order_id"],)
            ).fetchall()
            
            orders.append({
                "internal_order_id": row["internal_order_id"],
                "razorpay_order_id": row["razorpay_order_id"],
                "status": row["status"],
                "total": row["total"],
                "currency": row["currency"],
                "paid_at": row["paid_at"],
                "items": [{"name": i["name"], "quantity": i["quantity"]} for i in items]
            })
            
        return orders
    finally:
        conn.close()

def get_order(internal_order_id):
    """
    Retrieve full details for a specific order.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT * FROM orders WHERE internal_order_id = ?
            """,
            (internal_order_id,)
        ).fetchone()
        
        if not row:
            return None
            
        items = conn.execute(
            "SELECT * FROM order_items WHERE internal_order_id = ?",
            (internal_order_id,)
        ).fetchall()
        
        order = dict(row)
        order["purchase_guard_checks"] = json.loads(order["purchase_guard_checks"] or "{}")
        order["items"] = [dict(i) for i in items]
        
        if order.get("customer_id"):
            cust_row = conn.execute(
                "SELECT * FROM customers WHERE customer_id = ?", 
                (order["customer_id"],)
            ).fetchone()
            if cust_row:
                order["customer"] = dict(cust_row)
                
        if order.get("shipping_address_id"):
            addr_row = conn.execute(
                "SELECT * FROM addresses WHERE address_id = ?", 
                (order["shipping_address_id"],)
            ).fetchone()
            if addr_row:
                order["delivery_address"] = dict(addr_row)
        
        return order
    finally:
        conn.close()
