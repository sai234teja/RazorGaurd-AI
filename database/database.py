"""SQLite database helpers for the commerce catalog."""

import csv
import json
import os
import sqlite3
from datetime import datetime, timezone


# ============================================================
# PATHS
# ============================================================

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "commerce.db",
)

DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "catalog",
    "products.csv",
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection(db_path=DEFAULT_DB_PATH):
    """Create and return a SQLite connection."""

    os.makedirs(
        os.path.dirname(db_path) or ".",
        exist_ok=True,
    )

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    # Enable foreign-key support.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables(conn=None, db_path=DEFAULT_DB_PATH):
    """
    Create all commerce database tables.

    Tables:
        products
        product_offers
    """

    if conn is None:
        conn = get_connection(db_path)
        close_conn = True
    else:
        close_conn = False

    try:

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,

                merchant_id TEXT NOT NULL
                    DEFAULT 'MERCHANT_DEMO',

                brand TEXT,

                name TEXT,

                category TEXT,

                price REAL,

                currency TEXT,

                description TEXT,

                rating REAL,

                stock INTEGER,

                image_url TEXT,

                product_url TEXT,

                attributes TEXT,

                use_cases TEXT,

                related_products TEXT
                    DEFAULT '[]',

                created_at TEXT,

                updated_at TEXT
            )
            """
        )

        # ----------------------------------------------------
        # PRODUCT OFFERS
        #
        # One product can have multiple merchant offers.
        # This is the foundation for price comparison.
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_offers (
                offer_id INTEGER PRIMARY KEY AUTOINCREMENT,

                product_id TEXT NOT NULL,

                merchant_id TEXT NOT NULL,

                merchant_name TEXT NOT NULL,

                price REAL NOT NULL,

                currency TEXT NOT NULL
                    DEFAULT 'INR',

                product_url TEXT,

                availability TEXT NOT NULL
                    DEFAULT 'in_stock',

                shipping_fee REAL NOT NULL
                    DEFAULT 0,

                delivery_days INTEGER,

                is_verified INTEGER NOT NULL
                    DEFAULT 0,

                source_type TEXT NOT NULL
                    DEFAULT 'demo',

                last_checked_at TEXT,

                created_at TEXT,

                updated_at TEXT,

                FOREIGN KEY (product_id)
                    REFERENCES products(product_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                internal_order_id TEXT PRIMARY KEY,
                razorpay_order_id TEXT,
                razorpay_payment_id TEXT,
                status TEXT NOT NULL,
                currency TEXT NOT NULL,
                total REAL NOT NULL,
                payment_provider TEXT NOT NULL,
                purchase_guard_risk_score REAL,
                purchase_guard_risk_level TEXT,
                purchase_guard_decision TEXT,
                purchase_guard_checks TEXT,
                customer_id TEXT,
                shipping_address_id TEXT,
                created_at TEXT,
                paid_at TEXT
            )
            """
        )

        # ----------------------------------------------------
        # CUSTOMERS & ADDRESSES
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS addresses (
                address_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                line1 TEXT NOT NULL,
                line2 TEXT,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                postal_code TEXT NOT NULL,
                country TEXT NOT NULL DEFAULT 'IN',
                created_at TEXT,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # ORDER ITEMS
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                internal_order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (internal_order_id)
                    REFERENCES orders(internal_order_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # INDEXES
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_product_offers_product_id
            ON product_offers(product_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_product_offers_merchant_id
            ON product_offers(merchant_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_product_offers_price
            ON product_offers(price)
            """
        )

        conn.commit()

        return True

    finally:

        if close_conn:
            conn.close()


# ============================================================
# SCHEMA MIGRATION
# ============================================================

def migrate_schema(db_path=DEFAULT_DB_PATH):
    """
    Safely upgrade an existing database.

    Existing products are preserved.

    Adds:
        merchant_id
        related_products
        product_offers table
    """

    conn = get_connection(db_path)

    try:

        # ----------------------------------------------------
        # Check whether products table exists
        # ----------------------------------------------------

        table_exists = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'products'
            """
        ).fetchone()

        if not table_exists:

            create_tables(
                conn=conn,
            )

            conn.commit()

            return True

        # ----------------------------------------------------
        # Existing products columns
        # ----------------------------------------------------

        columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(products)"
            ).fetchall()
        }

        # ----------------------------------------------------
        # merchant_id
        # ----------------------------------------------------

        if "merchant_id" not in columns:

            conn.execute(
                """
                ALTER TABLE products
                ADD COLUMN merchant_id TEXT
                DEFAULT 'MERCHANT_DEMO'
                """
            )

        # ----------------------------------------------------
        # related_products
        # ----------------------------------------------------

        if "related_products" not in columns:

            conn.execute(
                """
                ALTER TABLE products
                ADD COLUMN related_products TEXT
                DEFAULT '[]'
                """
            )

        # ----------------------------------------------------
        # Repair existing merchant IDs
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE products
            SET merchant_id = 'MERCHANT_DEMO'
            WHERE merchant_id IS NULL
               OR TRIM(merchant_id) = ''
            """
        )

        # ----------------------------------------------------
        # Repair existing related products
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE products
            SET related_products = '[]'
            WHERE related_products IS NULL
               OR TRIM(related_products) = ''
            """
        )

        # ----------------------------------------------------
        # Create product_offers if missing
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_offers (
                offer_id INTEGER PRIMARY KEY AUTOINCREMENT,

                product_id TEXT NOT NULL,

                merchant_id TEXT NOT NULL,

                merchant_name TEXT NOT NULL,

                price REAL NOT NULL,

                currency TEXT NOT NULL
                    DEFAULT 'INR',

                product_url TEXT,

                availability TEXT NOT NULL
                    DEFAULT 'in_stock',

                shipping_fee REAL NOT NULL
                    DEFAULT 0,

                delivery_days INTEGER,

                is_verified INTEGER NOT NULL
                    DEFAULT 0,

                source_type TEXT NOT NULL
                    DEFAULT 'demo',

                last_checked_at TEXT,

                created_at TEXT,

                updated_at TEXT,

                FOREIGN KEY (product_id)
                    REFERENCES products(product_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # Create orders and order_items if missing
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                internal_order_id TEXT PRIMARY KEY,
                razorpay_order_id TEXT,
                razorpay_payment_id TEXT,
                status TEXT NOT NULL,
                currency TEXT NOT NULL,
                total REAL NOT NULL,
                payment_provider TEXT NOT NULL,
                purchase_guard_risk_score REAL,
                purchase_guard_risk_level TEXT,
                purchase_guard_decision TEXT,
                purchase_guard_checks TEXT,
                created_at TEXT,
                paid_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS addresses (
                address_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                line1 TEXT NOT NULL,
                line2 TEXT,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                postal_code TEXT NOT NULL,
                country TEXT NOT NULL DEFAULT 'IN',
                created_at TEXT,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # Alter orders table
        # ----------------------------------------------------

        order_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(orders)"
            ).fetchall()
        }

        if "customer_id" not in order_columns:
            conn.execute(
                """
                ALTER TABLE orders
                ADD COLUMN customer_id TEXT
                """
            )

        if "shipping_address_id" not in order_columns:
            conn.execute(
                """
                ALTER TABLE orders
                ADD COLUMN shipping_address_id TEXT
                """
            )

        # ----------------------------------------------------
        # Create order_items if missing
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                internal_order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (internal_order_id)
                    REFERENCES orders(internal_order_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # Indexes
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_product_offers_product_id
            ON product_offers(product_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_product_offers_merchant_id
            ON product_offers(merchant_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_product_offers_price
            ON product_offers(price)
            """
        )

        conn.commit()

        return True

    finally:

        conn.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database(db_path=DEFAULT_DB_PATH):
    """
    Ensure the database exists and schema is upgraded.
    """

    create_tables(
        db_path=db_path,
    )

    migrate_schema(
        db_path=db_path,
    )

    return db_path


# ============================================================
# ATTRIBUTE NORMALIZATION
# ============================================================

def _normalize_attributes(raw_attributes, raw_row):
    """
    Convert merchant-specific attributes into
    a JSON-safe dictionary.
    """

    attributes = {}

    # --------------------------------------------------------
    # Existing JSON attributes
    # --------------------------------------------------------

    if isinstance(
        raw_attributes,
        str,
    ):

        try:

            attributes = json.loads(
                raw_attributes
            )

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):

            attributes = {}

    elif isinstance(
        raw_attributes,
        dict,
    ):

        attributes = raw_attributes.copy()

    # --------------------------------------------------------
    # Normalize known CSV attributes
    # --------------------------------------------------------

    for key in (
        "battery_hours",
        "noise_cancellation",
        "microphone_quality",
    ):

        value = raw_row.get(key)

        if value is None or value == "":
            continue

        # ----------------------------------------------------
        # Noise cancellation
        # ----------------------------------------------------

        if key == "noise_cancellation":

            normalized = str(
                value
            ).strip().lower()

            attributes[key] = (
                normalized
                in {
                    "yes",
                    "true",
                    "1",
                    "y",
                }
            )

        # ----------------------------------------------------
        # Battery
        # ----------------------------------------------------

        elif key == "battery_hours":

            try:

                attributes[key] = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                attributes[key] = value

        # ----------------------------------------------------
        # Other attributes
        # ----------------------------------------------------

        else:

            attributes[key] = str(
                value
            )

    return attributes


# ============================================================
# USE CASE NORMALIZATION
# ============================================================

def _normalize_use_cases(
    raw_use_cases,
    raw_row,
):
    """
    Convert use_case CSV text into
    a JSON-safe list.
    """

    if isinstance(
        raw_use_cases,
        list,
    ):

        return [
            str(item).strip()
            for item in raw_use_cases
            if str(item).strip()
        ]

    if isinstance(
        raw_use_cases,
        str,
    ):

        parsed = raw_use_cases.strip()

        if parsed:

            return [
                item.strip()
                for item in parsed.split(",")
                if item.strip()
            ]

    # --------------------------------------------------------
    # Legacy CSV field
    # --------------------------------------------------------

    legacy = raw_row.get(
        "use_case",
        "",
    )

    if (
        isinstance(
            legacy,
            str,
        )
        and legacy.strip()
    ):

        return [
            item.strip()
            for item in legacy.split(",")
            if item.strip()
        ]

    return []


# ============================================================
# RELATED PRODUCT NORMALIZATION
# ============================================================

def _normalize_related_products(
    raw_related_products,
):
    """
    Convert related-product information into
    a JSON-safe list.
    """

    if isinstance(
        raw_related_products,
        list,
    ):

        return [
            str(item).strip()
            for item in raw_related_products
            if str(item).strip()
        ]

    if isinstance(
        raw_related_products,
        str,
    ):

        value = raw_related_products.strip()

        if not value:
            return []

        # ----------------------------------------------------
        # Try JSON first
        # ----------------------------------------------------

        try:

            parsed = json.loads(
                value
            )

            if isinstance(
                parsed,
                list,
            ):

                return [
                    str(item).strip()
                    for item in parsed
                    if str(item).strip()
                ]

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):

            pass

        # ----------------------------------------------------
        # Comma-separated fallback
        # ----------------------------------------------------

        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    return []


# ============================================================
# CSV ROW NORMALIZATION
# ============================================================

def _normalize_row(raw_row):
    """
    Normalize a CSV row to a database-ready
    product dictionary.
    """

    if not raw_row:
        return None

    # --------------------------------------------------------
    # Product ID
    # --------------------------------------------------------

    product_id = str(
        raw_row.get(
            "product_id",
            "",
        )
    ).strip()

    if not product_id:
        return None

    # --------------------------------------------------------
    # Attributes
    # --------------------------------------------------------

    attributes = _normalize_attributes(
        raw_row.get(
            "attributes",
        ),
        raw_row,
    )

    # --------------------------------------------------------
    # Use cases
    # --------------------------------------------------------

    use_cases = _normalize_use_cases(
        raw_row.get(
            "use_cases",
        ),
        raw_row,
    )

    # --------------------------------------------------------
    # Related products
    # --------------------------------------------------------

    related_products = _normalize_related_products(
        raw_row.get(
            "related_products",
        )
    )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    now = datetime.now(
        timezone.utc
    ).isoformat()

    # --------------------------------------------------------
    # Product object
    # --------------------------------------------------------

    product = {

        "product_id":
            product_id,

        "merchant_id":
            str(
                raw_row.get(
                    "merchant_id",
                )
                or "MERCHANT_DEMO"
            ).strip(),

        "brand":
            str(
                raw_row.get(
                    "brand",
                )
                or "Merchant Brand"
            ).strip(),

        "name":
            str(
                raw_row.get(
                    "name",
                )
                or ""
            ).strip(),

        "category":
            str(
                raw_row.get(
                    "category",
                )
                or ""
            ).strip(),

        "price":
            float(
                raw_row.get(
                    "price",
                )
                or 0
            ),

        "currency":
            str(
                raw_row.get(
                    "currency",
                )
                or "INR"
            ).strip(),

        "description":
            str(
                raw_row.get(
                    "description",
                )
                or ""
            ).strip(),

        "rating":
            float(
                raw_row.get(
                    "rating",
                )
                or 0
            ),

        "stock":
            int(
                raw_row.get(
                    "stock",
                )
                or 0
            ),

        "image_url":
            str(
                raw_row.get(
                    "image_url",
                )
                or ""
            ).strip(),

        "product_url":
            str(
                raw_row.get(
                    "product_url",
                )
                or ""
            ).strip(),

        "attributes":
            json.dumps(
                attributes,
                ensure_ascii=False,
            ),

        "use_cases":
            json.dumps(
                use_cases,
                ensure_ascii=False,
            ),

        "related_products":
            json.dumps(
                related_products,
                ensure_ascii=False,
            ),

        "created_at":
            raw_row.get(
                "created_at",
            )
            or now,

        "updated_at":
            raw_row.get(
                "updated_at",
            )
            or now,
    }

    return product


# ============================================================
# CSV → DATABASE
# ============================================================

def migrate_csv_to_database(
    csv_path=DEFAULT_CSV_PATH,
    db_path=DEFAULT_DB_PATH,
):
    """
    Import or update the merchant catalog
    from CSV into SQLite.
    """

    initialize_database(
        db_path
    )

    conn = get_connection(
        db_path
    )

    try:

        imported_or_updated = 0

        # ----------------------------------------------------
        # Validate CSV
        # ----------------------------------------------------

        if not os.path.exists(
            csv_path
        ):

            raise FileNotFoundError(
                f"CSV catalog not found: {csv_path}"
            )

        # ----------------------------------------------------
        # Read CSV
        # ----------------------------------------------------

        with open(
            csv_path,
            "r",
            encoding="utf-8",
            newline="",
        ) as csv_file:

            reader = csv.DictReader(
                csv_file
            )

            for raw_row in reader:

                product = _normalize_row(
                    raw_row
                )

                if product is None:
                    continue

                # ------------------------------------------------
                # Insert / update product
                # ------------------------------------------------

                conn.execute(
                    """
                    INSERT INTO products (
                        product_id,
                        merchant_id,
                        brand,
                        name,
                        category,
                        price,
                        currency,
                        description,
                        rating,
                        stock,
                        image_url,
                        product_url,
                        attributes,
                        use_cases,
                        related_products,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?
                    )
                    ON CONFLICT(product_id)
                    DO UPDATE SET

                        merchant_id =
                            excluded.merchant_id,

                        brand =
                            excluded.brand,

                        name =
                            excluded.name,

                        category =
                            excluded.category,

                        price =
                            excluded.price,

                        currency =
                            excluded.currency,

                        description =
                            excluded.description,

                        rating =
                            excluded.rating,

                        stock =
                            excluded.stock,

                        image_url =
                            excluded.image_url,

                        product_url =
                            excluded.product_url,

                        attributes =
                            excluded.attributes,

                        use_cases =
                            excluded.use_cases,

                        related_products =
                            excluded.related_products,

                        updated_at =
                            excluded.updated_at
                    """,
                    (
                        product["product_id"],
                        product["merchant_id"],
                        product["brand"],
                        product["name"],
                        product["category"],
                        product["price"],
                        product["currency"],
                        product["description"],
                        product["rating"],
                        product["stock"],
                        product["image_url"],
                        product["product_url"],
                        product["attributes"],
                        product["use_cases"],
                        product["related_products"],
                        product["created_at"],
                        product["updated_at"],
                    ),
                )

                imported_or_updated += 1

        # ----------------------------------------------------
        # Commit
        # ----------------------------------------------------

        conn.commit()

        # ----------------------------------------------------
        # Count products
        # ----------------------------------------------------

        total_products = conn.execute(
            """
            SELECT COUNT(*)
            FROM products
            """
        ).fetchone()[0]

        return (
            imported_or_updated,
            total_products,
        )

    finally:

        conn.close()


# ============================================================
# PRODUCT OFFER HELPERS
# ============================================================

def add_product_offer(
    product_id,
    merchant_id,
    merchant_name,
    price,
    currency="INR",
    product_url="",
    availability="in_stock",
    shipping_fee=0,
    delivery_days=None,
    is_verified=False,
    source_type="demo",
    db_path=DEFAULT_DB_PATH,
):
    """
    Add a merchant offer for an existing product.

    This is the foundation for multi-merchant
    price comparison.
    """

    now = datetime.now(
        timezone.utc
    ).isoformat()

    conn = get_connection(
        db_path
    )

    try:

        # ----------------------------------------------------
        # Validate product
        # ----------------------------------------------------

        exists = conn.execute(
            """
            SELECT 1
            FROM products
            WHERE product_id = ?
            """,
            (
                str(product_id),
            ),
        ).fetchone()

        if exists is None:

            raise ValueError(
                f"Product not found: {product_id}"
            )

        # ----------------------------------------------------
        # Insert offer
        # ----------------------------------------------------

        cursor = conn.execute(
            """
            INSERT INTO product_offers (
                product_id,
                merchant_id,
                merchant_name,
                price,
                currency,
                product_url,
                availability,
                shipping_fee,
                delivery_days,
                is_verified,
                source_type,
                last_checked_at,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                str(product_id),
                str(merchant_id),
                str(merchant_name),
                float(price),
                str(currency or "INR"),
                str(product_url or ""),
                str(availability or "in_stock"),
                float(shipping_fee or 0),
                (
                    int(delivery_days)
                    if delivery_days is not None
                    else None
                ),
                1 if is_verified else 0,
                str(source_type or "demo"),
                now,
                now,
                now,
            ),
        )

        conn.commit()

        return cursor.lastrowid

    finally:

        conn.close()


def get_product_offers(
    product_id,
    in_stock_only=False,
    db_path=DEFAULT_DB_PATH,
):
    """
    Return all merchant offers for a product.
    """

    conn = get_connection(
        db_path
    )

    try:

        sql = """
            SELECT
                offer_id,
                product_id,
                merchant_id,
                merchant_name,
                price,
                currency,
                product_url,
                availability,
                shipping_fee,
                delivery_days,
                is_verified,
                source_type,
                last_checked_at,
                created_at,
                updated_at
            FROM product_offers
            WHERE product_id = ?
        """

        params = [
            str(product_id)
        ]

        if in_stock_only:

            sql += """
                AND availability = 'in_stock'
            """

        sql += """
            ORDER BY
                (price + shipping_fee) ASC,
                price ASC
        """

        rows = conn.execute(
            sql,
            params,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


def get_lowest_product_offer(
    product_id,
    in_stock_only=True,
    db_path=DEFAULT_DB_PATH,
):
    """
    Return the lowest-cost merchant offer.

    Total cost =
        product price + shipping fee
    """

    offers = get_product_offers(
        product_id=product_id,
        in_stock_only=in_stock_only,
        db_path=db_path,
    )

    if not offers:
        return None

    return min(
        offers,
        key=lambda offer: (
            float(
                offer.get("price")
                or 0
            )
            +
            float(
                offer.get("shipping_fee")
                or 0
            )
        ),
    )


def get_price_comparison(
    product_id,
    db_path=DEFAULT_DB_PATH,
):
    """
    Build a clean price-comparison object
    for the frontend/API.
    """

    offers = get_product_offers(
        product_id=product_id,
        in_stock_only=True,
        db_path=db_path,
    )

    if not offers:

        return {
            "has_offers": False,
            "offer_count": 0,
            "lowest_price": None,
            "lowest_total": None,
            "lowest_merchant": None,
            "lowest_merchant_id": None,
            "savings": 0,
            "currency": "INR",
            "offers": [],
        }

    # --------------------------------------------------------
    # Sort by total payable amount
    # --------------------------------------------------------

    offers = sorted(
        offers,
        key=lambda offer: (
            float(
                offer.get("price")
                or 0
            )
            +
            float(
                offer.get("shipping_fee")
                or 0
            )
        ),
    )

    cheapest = offers[0]

    cheapest_total = (
        float(
            cheapest.get("price")
            or 0
        )
        +
        float(
            cheapest.get("shipping_fee")
            or 0
        )
    )

    highest_total = max(
        (
            float(
                offer.get("price")
                or 0
            )
            +
            float(
                offer.get("shipping_fee")
                or 0
            )
        )
        for offer in offers
    )

    savings = max(
        0,
        highest_total - cheapest_total,
    )

    # --------------------------------------------------------
    # Mark lowest-price offer
    # --------------------------------------------------------

    normalized_offers = []

    for offer in offers:

        price = float(
            offer.get("price")
            or 0
        )

        shipping = float(
            offer.get("shipping_fee")
            or 0
        )

        total = price + shipping

        item = dict(
            offer
        )

        item["total_price"] = round(
            total,
            2,
        )

        item["is_lowest"] = (
            offer["offer_id"]
            == cheapest["offer_id"]
        )

        normalized_offers.append(
            item
        )

    return {
        "has_offers": True,
        "offer_count": len(
            normalized_offers
        ),
        "lowest_price": float(
            cheapest.get("price")
            or 0
        ),
        "lowest_total": round(
            cheapest_total,
            2,
        ),
        "lowest_merchant": cheapest.get(
            "merchant_name"
        ),
        "lowest_merchant_id": cheapest.get(
            "merchant_id"
        ),
        "savings": round(
            savings,
            2,
        ),
        "currency": cheapest.get(
            "currency",
            "INR",
        ),
        "offers": normalized_offers,
    }


# ============================================================
# TEST / ENTRY POINT
# ============================================================

if __name__ == "__main__":

    db_path = initialize_database()

    print(
        "DATABASE READY"
    )

    conn = get_connection(
        db_path
    )

    try:

        tables = [
            row["name"]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()
        ]

        print(
            "TABLES:",
            tables,
        )

        product_columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(products)"
            ).fetchall()
        ]

        offer_columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(product_offers)"
            ).fetchall()
        ]

        print(
            "PRODUCT COLUMNS:",
            product_columns,
        )

        print(
            "OFFER COLUMNS:",
            offer_columns,
        )

    finally:

        conn.close()