"""
Seed demo merchant offers for RazorGuard AI.

IMPORTANT:
These offers are DEMO/SIMULATED data.
They are NOT live Amazon, Flipkart, Croma, Reliance, etc. prices.

Use this file only to test:
    Product
        ↓
    Multiple merchant offers
        ↓
    Lowest price
        ↓
    Savings
        ↓
    Frontend price comparison
"""

from database.database import (
    initialize_database,
    add_product_offer,
    get_connection,
)


# ============================================================
# DEMO MERCHANTS
# ============================================================

MERCHANTS = {
    "MERCHANT_RAZOR": {
        "id": "MERCHANT_RAZOR",
        "name": "Razor Demo Store",
    },
    "MERCHANT_TECH": {
        "id": "MERCHANT_TECH",
        "name": "Tech Demo Store",
    },
    "MERCHANT_DIGITAL": {
        "id": "MERCHANT_DIGITAL",
        "name": "Digital Demo Store",
    },
}


# ============================================================
# DEMO OFFER GENERATOR
# ============================================================

def build_demo_offers(product):
    """
    Create three simulated offers for a product.

    The prices are generated from the catalog price.
    They are DEMO values only.
    """

    product_id = product["product_id"]
    base_price = float(product.get("price") or 0)
    currency = product.get("currency") or "INR"
    product_url = product.get("product_url") or ""

    if base_price <= 0:
        return []

    # --------------------------------------------------------
    # Create realistic-looking demo price variations.
    #
    # These are intentionally marked as demo data.
    # --------------------------------------------------------

    razor_price = round(base_price, 2)

    tech_price = round(
        base_price * 0.96,
        2,
    )

    digital_price = round(
        base_price * 0.92,
        2,
    )

    return [
        {
            "product_id": product_id,
            "merchant_id": MERCHANTS["MERCHANT_RAZOR"]["id"],
            "merchant_name": MERCHANTS["MERCHANT_RAZOR"]["name"],
            "price": razor_price,
            "currency": currency,
            "product_url": product_url,
            "availability": "in_stock",
            "shipping_fee": 0,
            "delivery_days": 3,
            "is_verified": False,
            "source_type": "demo",
        },
        {
            "product_id": product_id,
            "merchant_id": MERCHANTS["MERCHANT_TECH"]["id"],
            "merchant_name": MERCHANTS["MERCHANT_TECH"]["name"],
            "price": tech_price,
            "currency": currency,
            "product_url": product_url,
            "availability": "in_stock",
            "shipping_fee": 0,
            "delivery_days": 4,
            "is_verified": False,
            "source_type": "demo",
        },
        {
            "product_id": product_id,
            "merchant_id": MERCHANTS["MERCHANT_DIGITAL"]["id"],
            "merchant_name": MERCHANTS["MERCHANT_DIGITAL"]["name"],
            "price": digital_price,
            "currency": currency,
            "product_url": product_url,
            "availability": "in_stock",
            "shipping_fee": 0,
            "delivery_days": 5,
            "is_verified": False,
            "source_type": "demo",
        },
    ]


# ============================================================
# CLEAR EXISTING DEMO OFFERS
# ============================================================

def clear_demo_offers():
    """
    Remove previously generated demo offers.

    This prevents duplicate offers every time
    the seed script is executed.
    """

    conn = get_connection()

    try:

        deleted = conn.execute(
            """
            DELETE FROM product_offers
            WHERE source_type = 'demo'
            """
        ).rowcount

        conn.commit()

        return deleted

    finally:

        conn.close()


# ============================================================
# SEED ALL PRODUCTS
# ============================================================

def seed_demo_offers():
    """
    Add demo offers for every product
    currently stored in the database.
    """

    initialize_database()

    conn = get_connection()

    try:

        products = conn.execute(
            """
            SELECT
                product_id,
                name,
                price,
                currency,
                product_url
            FROM products
            ORDER BY product_id
            """
        ).fetchall()

        products = [
            dict(product)
            for product in products
        ]

    finally:

        conn.close()

    if not products:

        print("❌ No products found in database.")

        return 0

    # --------------------------------------------------------
    # Remove old demo offers first
    # --------------------------------------------------------

    deleted = clear_demo_offers()

    print("=" * 70)
    print("RAZORGUARD AI - DEMO OFFER SEEDER")
    print("=" * 70)

    print()
    print(
        f"Removed existing demo offers: {deleted}"
    )

    print(
        f"Products found: {len(products)}"
    )

    print()

    # --------------------------------------------------------
    # Add new offers
    # --------------------------------------------------------

    total_offers = 0

    for product in products:

        offers = build_demo_offers(
            product
        )

        for offer in offers:

            add_product_offer(
                product_id=offer["product_id"],
                merchant_id=offer["merchant_id"],
                merchant_name=offer["merchant_name"],
                price=offer["price"],
                currency=offer["currency"],
                product_url=offer["product_url"],
                availability=offer["availability"],
                shipping_fee=offer["shipping_fee"],
                delivery_days=offer["delivery_days"],
                is_verified=offer["is_verified"],
                source_type=offer["source_type"],
            )

            total_offers += 1

    print(
        f"Demo offers inserted: {total_offers}"
    )

    print()
    print("=" * 70)
    print("DEMO OFFERS READY")
    print("=" * 70)

    return total_offers


# ============================================================
# SHOW P001 COMPARISON
# ============================================================

def show_p001_test():
    """
    Verify the price comparison for SoundMax Air Pro.
    """

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT
                product_id,
                name,
                price,
                currency
            FROM products
            WHERE product_id = 'P001'
            """
        ).fetchall()

        if not rows:

            print()
            print(
                "⚠️ P001 was not found."
            )

            return

        product = dict(
            rows[0]
        )

    finally:

        conn.close()

    from database.database import (
        get_price_comparison,
    )

    comparison = get_price_comparison(
        product_id="P001"
    )

    print()
    print("=" * 70)
    print("PRICE COMPARISON TEST")
    print("=" * 70)

    print()
    print(
        f"Product: {product['name']}"
    )

    print(
        f"Catalog price: ₹{product['price']:.2f}"
    )

    print(
        f"Offers: {comparison['offer_count']}"
    )

    print(
        f"Lowest price: ₹{comparison['lowest_price']:.2f}"
    )

    print(
        f"Lowest merchant: "
        f"{comparison['lowest_merchant']}"
    )

    print(
        f"Savings: ₹{comparison['savings']:.2f}"
    )

    print()
    print("OFFERS")
    print("-" * 70)

    for offer in comparison["offers"]:

        marker = (
            "🏆 LOWEST"
            if offer["is_lowest"]
            else ""
        )

        print(
            f"{offer['merchant_name']}"
            f" | ₹{offer['price']:.2f}"
            f" | Delivery: "
            f"{offer['delivery_days']} days"
            f" | {offer['source_type']}"
            f" {marker}"
        )

    print()
    print(
        "⚠️ These are DEMO/SIMULATED offers."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        seed_demo_offers()

        show_p001_test()

        print()
        print(
            "✅ Seed process completed successfully."
        )

    except Exception as exc:

        print()
        print(
            "❌ Seed process failed."
        )

        print(
            f"Reason: {exc}"
        )

        raisevvvvvv