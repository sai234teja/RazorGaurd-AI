"""SQLite-backed catalog service for the commerce agent."""

import json

from database.database import (
    DEFAULT_DB_PATH,
    get_connection,
)

try:
    from offer_sources.offer_eligibility import get_lowest_eligible_offer
except ImportError:
    get_lowest_eligible_offer = None


class CatalogService:
    """
    Service layer that abstracts database access
    for catalog operations.

    The catalog is designed to be AI-readable and
    merchant-aware for agentic commerce.
    """

    def __init__(
        self,
        db_path=DEFAULT_DB_PATH
    ):
        self.db_path = db_path

    # ==================================================
    # DESERIALIZE DATABASE VALUES
    # ==================================================

    @staticmethod
    def _deserialize(
        value,
        default=None
    ):
        if value in (
            None,
            ""
        ):
            return default

        if isinstance(
            value,
            (
                dict,
                list
            )
        ):
            return value

        try:
            return json.loads(
                value
            )

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError
        ):
            return default

    # ==================================================
    # NORMALIZE RELATED PRODUCTS
    # ==================================================

    @staticmethod
    def _normalize_related_products(
        value
    ):
        """
        Convert related_products into a clean list
        of product IDs.
        """

        if value in (
            None,
            ""
        ):
            return []

        if isinstance(
            value,
            list
        ):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        if isinstance(
            value,
            str
        ):

            parsed = CatalogService._deserialize(
                value,
                None
            )

            if isinstance(
                parsed,
                list
            ):
                return [
                    str(item).strip()
                    for item in parsed
                    if str(item).strip()
                ]

            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]

        return []

    # ==================================================
    # PREPARE PRODUCT
    # ==================================================

    @staticmethod
    def _prepare_product(
        product
    ):

        if product is None:

            raise ValueError(
                "Product data is required"
            )


        payload = dict(
            product
        )


        product_id = str(
            payload.get(
                "product_id",
                ""
            )
        ).strip()


        if not product_id:

            raise ValueError(
                "product_id is required"
            )


        # --------------------------------------------------
        # MERCHANT
        # --------------------------------------------------

        merchant_id = str(
            payload.get(
                "merchant_id",
                "MERCHANT_DEMO"
            )
            or "MERCHANT_DEMO"
        ).strip()


        # --------------------------------------------------
        # ATTRIBUTES
        # --------------------------------------------------

        attributes = payload.get(
            "attributes"
        ) or {}


        if isinstance(
            attributes,
            str
        ):

            try:

                attributes = json.loads(
                    attributes
                )

            except (
                TypeError,
                ValueError,
                json.JSONDecodeError
            ):

                attributes = {}


        if not isinstance(
            attributes,
            dict
        ):

            attributes = {}


        # --------------------------------------------------
        # USE CASES
        # --------------------------------------------------

        use_cases = payload.get(
            "use_cases"
        ) or []


        if isinstance(
            use_cases,
            str
        ):

            try:

                use_cases = json.loads(
                    use_cases
                )

            except (
                TypeError,
                ValueError,
                json.JSONDecodeError
            ):

                use_cases = [
                    part.strip()
                    for part in use_cases.split(",")
                    if part.strip()
                ]


        if not isinstance(
            use_cases,
            list
        ):

            use_cases = [
                str(use_cases)
            ]


        # --------------------------------------------------
        # RELATED PRODUCTS
        # --------------------------------------------------

        related_products = (
            CatalogService
            ._normalize_related_products(
                payload.get(
                    "related_products"
                )
            )
        )


        # --------------------------------------------------
        # UNIVERSAL ATTRIBUTE DERIVATION
        # --------------------------------------------------

        category = str(
            payload.get(
                "category",
                ""
            )
        ).strip().lower()


        description = str(
            payload.get(
                "description",
                ""
            )
        ).strip().lower()


        # --------------------------------------------------
        # WIRELESS
        # --------------------------------------------------

        if "wireless" not in attributes:

            attributes["wireless"] = (
                "wireless" in category
                or
                "wireless" in description
            )


        # --------------------------------------------------
        # BUILD DATABASE ROW
        # --------------------------------------------------

        row = {

            "product_id":
                product_id,

            "merchant_id":
                merchant_id,

            "brand":
                str(
                    payload.get(
                        "brand"
                    )
                    or "Merchant Brand"
                ),

            "name":
                str(
                    payload.get(
                        "name"
                    )
                    or ""
                ),

            "category":
                str(
                    payload.get(
                        "category"
                    )
                    or ""
                ),

            "price":
                float(
                    payload.get(
                        "price"
                    )
                    or 0
                ),

            "currency":
                str(
                    payload.get(
                        "currency"
                    )
                    or "INR"
                ),

            "description":
                str(
                    payload.get(
                        "description"
                    )
                    or ""
                ),

            "rating":
                float(
                    payload.get(
                        "rating"
                    )
                    or 0
                ),

            "stock":
                int(
                    payload.get(
                        "stock"
                    )
                    or 0
                ),

            "image_url":
                str(
                    payload.get(
                        "image_url"
                    )
                    or ""
                ),

            "product_url":
                str(
                    payload.get(
                        "product_url"
                    )
                    or ""
                ),

            "attributes":
                json.dumps(
                    attributes,
                    ensure_ascii=False
                ),

            "use_cases":
                json.dumps(
                    [
                        str(item).strip()
                        for item in use_cases
                        if str(item).strip()
                    ],
                    ensure_ascii=False
                ),

            "related_products":
                json.dumps(
                    related_products,
                    ensure_ascii=False
                ),
        }


        return row

    # ==================================================
    # ADD PRODUCT
    # ==================================================

    def add_product(
        self,
        product
    ):

        row = self._prepare_product(
            product
        )


        conn = get_connection(
            self.db_path
        )


        try:

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
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    datetime('now'),
                    datetime('now')
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
                        datetime('now')
                """,

                (
                    row["product_id"],
                    row["merchant_id"],
                    row["brand"],
                    row["name"],
                    row["category"],
                    row["price"],
                    row["currency"],
                    row["description"],
                    row["rating"],
                    row["stock"],
                    row["image_url"],
                    row["product_url"],
                    row["attributes"],
                    row["use_cases"],
                    row["related_products"],
                ),
            )


            conn.commit()


            return self.get_product(
                row["product_id"]
            )


        finally:

            conn.close()

    # ==================================================
    # GET PRODUCT
    # ==================================================

    def get_product(
        self,
        product_id
    ):

        conn = get_connection(
            self.db_path
        )


        try:

            product = conn.execute(
                """
                SELECT *
                FROM products
                WHERE product_id = ?
                """,
                (
                    str(product_id),
                ),
            ).fetchone()


            if product is None:

                return None


            return self._row_to_product(
                dict(product)
            )


        finally:

            conn.close()

    # ==================================================
    # GET ALL PRODUCTS
    # ==================================================

    def get_all_products(
        self
    ):

        conn = get_connection(
            self.db_path
        )


        try:

            rows = conn.execute(
                """
                SELECT *
                FROM products
                ORDER BY name
                """
            ).fetchall()


            return [
                self._row_to_product(
                    dict(row)
                )
                for row in rows
            ]


        finally:

            conn.close()

    # ==================================================
    # UPDATE PRODUCT
    # ==================================================

    def update_product(
        self,
        product_id,
        product
    ):

        existing = self.get_product(
            product_id
        )


        if existing is None:

            return self.add_product(
                product
            )


        payload = self._prepare_product(
            product
        )


        conn = get_connection(
            self.db_path
        )


        try:

            conn.execute(
                """
                UPDATE products SET

                    merchant_id = ?,

                    brand = ?,

                    name = ?,

                    category = ?,

                    price = ?,

                    currency = ?,

                    description = ?,

                    rating = ?,

                    stock = ?,

                    image_url = ?,

                    product_url = ?,

                    attributes = ?,

                    use_cases = ?,

                    related_products = ?,

                    updated_at = datetime('now')

                WHERE product_id = ?
                """,

                (
                    payload["merchant_id"],
                    payload["brand"],
                    payload["name"],
                    payload["category"],
                    payload["price"],
                    payload["currency"],
                    payload["description"],
                    payload["rating"],
                    payload["stock"],
                    payload["image_url"],
                    payload["product_url"],
                    payload["attributes"],
                    payload["use_cases"],
                    payload["related_products"],
                    str(product_id),
                ),
            )


            conn.commit()


            return self.get_product(
                product_id
            )


        finally:

            conn.close()

    # ==================================================
    # DELETE PRODUCT
    # ==================================================

    def delete_product(
        self,
        product_id
    ):

        conn = get_connection(
            self.db_path
        )


        try:

            cursor = conn.execute(
                """
                DELETE FROM products
                WHERE product_id = ?
                """,
                (
                    str(product_id),
                )
            )


            conn.commit()


            return cursor.rowcount > 0


        finally:

            conn.close()

    # ==================================================
    # SEARCH PRODUCTS
    # ==================================================

    def search_products(
        self,
        category=None,
        max_price=None,
        min_price=None,
        use_cases=None,
        min_rating=None,
        query=None,
        in_stock=None
    ):

        clauses = []

        params = []


        # --------------------------------------------------
        # CATEGORY
        # --------------------------------------------------

        if category:

            clauses.append(
                "LOWER(category) LIKE ?"
            )

            params.append(
                f"%{str(category).lower()}%"
            )


        # --------------------------------------------------
        # MAX PRICE
        # --------------------------------------------------

        if max_price is not None:

            clauses.append(
                "price <= ?"
            )

            params.append(
                float(max_price)
            )


        # --------------------------------------------------
        # MIN PRICE
        # --------------------------------------------------

        if min_price is not None:

            clauses.append(
                "price >= ?"
            )

            params.append(
                float(min_price)
            )


        # --------------------------------------------------
        # MIN RATING
        # --------------------------------------------------

        if min_rating is not None:

            clauses.append(
                "rating >= ?"
            )

            params.append(
                float(min_rating)
            )


        # --------------------------------------------------
        # STOCK
        # --------------------------------------------------

        if in_stock is not None:

            if bool(in_stock):

                clauses.append(
                    "stock > 0"
                )

            else:

                clauses.append(
                    "stock >= 0"
                )


        # --------------------------------------------------
        # USE CASES (MOVED TO SOFT RANKING)
        # --------------------------------------------------
        # We no longer apply use_cases as a strict SQL LIKE filter 
        # to avoid eliminating valid candidates for broad terms like "best phone".

        # --------------------------------------------------
        # TEXT QUERY
        # --------------------------------------------------

        if query:

            clauses.append(
                """
                (
                    LOWER(name) LIKE ?
                    OR LOWER(description) LIKE ?
                    OR LOWER(category) LIKE ?
                )
                """
            )


            q = (
                f"%{str(query).lower()}%"
            )


            params.extend(
                [
                    q,
                    q,
                    q
                ]
            )


        # --------------------------------------------------
        # SQL
        # --------------------------------------------------

        sql = """
            SELECT *
            FROM products
        """


        if clauses:

            sql += (
                " WHERE "
                + " AND ".join(
                    clauses
                )
            )


        sql += """
            ORDER BY price ASC
        """


        conn = get_connection(
            self.db_path
        )


        try:

            rows = conn.execute(
                sql,
                params
            ).fetchall()


            return [
                self._row_to_product(
                    dict(row)
                )
                for row in rows
            ]


        finally:

            conn.close()

    # ==================================================
    # SEARCH FROM AI INTENT
    # ==================================================

    def search_for_intent(
        self,
        intent
    ):
        """
        Search products using normalized AI intent.

        Preferences remain product attributes and are
        not converted into use cases.
        """

        if not isinstance(
            intent,
            dict
        ):

            return []


        # --------------------------------------------------
        # INTENT VALUES
        # --------------------------------------------------

        category = intent.get(
            "category"
        )


        subcategory = intent.get(
            "subcategory"
        )


        use_cases = (
            intent.get(
                "use_cases"
            )
            or []
        )


        preferences = (
            intent.get(
                "preferences"
            )
            or {}
        )


        max_price = intent.get(
            "max_price"
        )


        min_price = intent.get(
            "min_price"
        )


        # --------------------------------------------------
        # PRIMARY SEARCH
        # --------------------------------------------------

        results = []


        if subcategory:

            results = self.search_products(

                category=subcategory,

                max_price=max_price,

                min_price=min_price,

                use_cases=use_cases,

                in_stock=True
            )


        # --------------------------------------------------
        # FALLBACK TO CATEGORY
        # --------------------------------------------------

        if not results and category:

            results = self.search_products(

                category=category,

                max_price=max_price,

                min_price=min_price,

                use_cases=use_cases,

                in_stock=True
            )

        # PATCH: Fallback for required constraints (e.g., form_factor=foldable)
        required = intent.get("required", {})
        if not results and isinstance(required, dict) and required:
            results = self.search_products(
                category=None,
                max_price=max_price,
                min_price=min_price,
                use_cases=use_cases,
                in_stock=True
            )


        # --------------------------------------------------
        # PREFERENCE FILTERING
        # --------------------------------------------------

        required = intent.get("required", {})
        
        if (
            (isinstance(preferences, dict) and preferences) or 
            (isinstance(required, dict) and required)
        ):

            filtered = []


            for product in results:

                attributes = (
                    product.get(
                        "attributes"
                    )
                    or {}
                )


                if isinstance(
                    attributes,
                    str
                ):

                    try:

                        attributes = json.loads(
                            attributes
                        )

                    except (
                        TypeError,
                        ValueError,
                        json.JSONDecodeError
                    ):

                        attributes = {}


                if not isinstance(
                    attributes,
                    dict
                ):

                    attributes = {}


                # --------------------------------------------------
                # DERIVE WIRELESS
                # --------------------------------------------------

                category_text = str(
                    product.get(
                        "category",
                        ""
                    )
                ).strip().lower()


                description_text = str(
                    product.get(
                        "description",
                        ""
                    )
                ).strip().lower()


                if "wireless" not in attributes:

                    attributes["wireless"] = (
                        "wireless" in category_text
                        or
                        "wireless" in description_text
                    )


                keeps_product = True

                # --------------------------------------------------
                # CHECK REQUIRED CONSTRAINTS
                # --------------------------------------------------
                
                required_constraints = intent.get("required", {})
                for key, req_data in required_constraints.items():
                    if not isinstance(req_data, dict):
                        continue
                    
                    expected = req_data.get("value")
                    operator = req_data.get("operator", "==")
                    
                    if expected is None:
                        continue
                        
                    actual = attributes.get(key)
                    if actual is None:
                        keeps_product = False
                        break
                        
                    try:
                        expected_num = float(expected)
                        actual_num = float(actual)
                        if operator == "==" and actual_num != expected_num:
                            keeps_product = False
                            break
                        elif operator == ">=" and actual_num < expected_num:
                            keeps_product = False
                            break
                        elif operator == "<=" and actual_num > expected_num:
                            keeps_product = False
                            break
                    except (TypeError, ValueError):
                        if operator == "==" and str(actual).lower() != str(expected).lower():
                            keeps_product = False
                            break
                            
                if not keeps_product:
                    continue

                # --------------------------------------------------
                # CHECK EACH PREFERENCE
                # --------------------------------------------------

                for key, requirement in (
                    preferences.items()
                ):

                    if not isinstance(
                        requirement,
                        dict
                    ):

                        continue


                    actual = attributes.get(
                        key
                    )


                    expected = requirement.get(
                        "value"
                    )


                    importance = str(
                        requirement.get(
                            "importance",
                            "medium"
                        )
                    ).lower()


                    direction = str(
                        requirement.get(
                            "direction",
                            "match"
                        )
                    ).lower()


                    # --------------------------------------------------
                    # UNKNOWN ATTRIBUTE
                    # --------------------------------------------------

                    if actual is None:

                        if (
                            direction == "match"
                            and
                            importance in {
                                "critical",
                                "high"
                            }
                        ):

                            keeps_product = False

                            break


                        continue


                    # --------------------------------------------------
                    # EXACT MATCH
                    # --------------------------------------------------

                    if (
                        direction == "match"
                        and
                        expected is not None
                    ):

                        # Boolean
                        if isinstance(
                            expected,
                            bool
                        ):

                            actual_bool = (
                                actual is True
                                or
                                str(
                                    actual
                                ).lower()
                                in {
                                    "true",
                                    "yes",
                                    "1"
                                }
                            )


                            if (
                                actual_bool
                                != expected
                            ):

                                if importance in {
                                    "critical",
                                    "high"
                                }:

                                    keeps_product = False

                                    break


                        # Numeric
                        elif isinstance(
                            expected,
                            (
                                int,
                                float
                            )
                        ):

                            try:

                                actual_number = float(
                                    actual
                                )

                                expected_number = float(
                                    expected
                                )


                                if (
                                    actual_number
                                    !=
                                    expected_number
                                ):

                                    if importance in {
                                        "critical",
                                        "high"
                                    }:

                                        keeps_product = False

                                        break


                            except (
                                TypeError,
                                ValueError
                            ):

                                pass


                        # Text
                        else:

                            if (
                                str(actual).lower()
                                !=
                                str(expected).lower()
                            ):

                                if importance in {
                                    "critical",
                                    "high"
                                }:

                                    keeps_product = False

                                    break


                if keeps_product:

                    product[
                        "attributes"
                    ] = attributes

                    filtered.append(
                        product
                    )


            # --------------------------------------------------
            # HARD MATCH LOGIC
            # --------------------------------------------------

            has_hard_match = any(

                isinstance(
                    requirement,
                    dict
                )

                and

                str(
                    requirement.get(
                        "direction",
                        "match"
                    )
                ).lower()
                == "match"

                and

                str(
                    requirement.get(
                        "importance",
                        "medium"
                    )
                ).lower()
                in {
                    "critical",
                    "high"
                }

                and

                requirement.get(
                    "value"
                ) is not None

                for requirement
                in preferences.values()
            )


            has_required = isinstance(required, dict) and len(required) > 0

            if filtered:

                results = filtered

            elif has_hard_match or has_required:

                results = []


        # --------------------------------------------------
        # NORMALIZE FOR UNIVERSAL RANKER
        # --------------------------------------------------

        normalized = []


        for product in results:

            # --------------------------------------------------
            # ATTRIBUTES
            # --------------------------------------------------

            attributes = (
                product.get(
                    "attributes"
                )
                or {}
            )


            if isinstance(
                attributes,
                str
            ):

                try:

                    attributes = json.loads(
                        attributes
                    )

                except (
                    TypeError,
                    ValueError,
                    json.JSONDecodeError
                ):

                    attributes = {}


            if not isinstance(
                attributes,
                dict
            ):

                attributes = {}


            # --------------------------------------------------
            # DERIVE WIRELESS
            # --------------------------------------------------

            category_text = str(
                product.get(
                    "category",
                    ""
                )
            ).strip().lower()


            description_text = str(
                product.get(
                    "description",
                    ""
                )
            ).strip().lower()


            if "wireless" not in attributes:

                attributes["wireless"] = (
                    "wireless" in category_text
                    or
                    "wireless" in description_text
                )


            # --------------------------------------------------
            # USE CASES
            # --------------------------------------------------

            use_case_list = (
                product.get(
                    "use_cases"
                )
                or []
            )


            if isinstance(
                use_case_list,
                str
            ):

                try:

                    use_case_list = json.loads(
                        use_case_list
                    )

                except (
                    TypeError,
                    ValueError,
                    json.JSONDecodeError
                ):

                    use_case_list = [
                        item.strip()
                        for item in use_case_list.split(",")
                        if item.strip()
                    ]


            if not isinstance(
                use_case_list,
                list
            ):

                use_case_list = []


            # --------------------------------------------------
            # RELATED PRODUCTS
            # --------------------------------------------------

            related_products = (
                self._normalize_related_products(
                    product.get(
                        "related_products"
                    )
                )
            )


            # --------------------------------------------------
            # NORMALIZED PRODUCT
            # --------------------------------------------------

            normalized_item = {

                "product_id":
                    product.get(
                        "product_id"
                    ),

                "merchant_id":
                    product.get(
                        "merchant_id",
                        "MERCHANT_DEMO"
                    ),

                "brand":
                    product.get(
                        "brand",
                        "Merchant Brand"
                    ),

                "name":
                    product.get(
                        "name"
                    ),

                "category":
                    product.get(
                        "category"
                    ),

                "subcategory":
                    product.get(
                        "subcategory"
                    )
                    or
                    product.get(
                        "category"
                    ),

                "price":
                    float(
                        product.get(
                            "price"
                        )
                        or 0
                    ),

                "currency":
                    product.get(
                        "currency",
                        "INR"
                    ),

                "description":
                    product.get(
                        "description",
                        ""
                    ),

                "rating":
                    float(
                        product.get(
                            "rating"
                        )
                        or 0
                    ),

                "stock":
                    int(
                        product.get(
                            "stock"
                        )
                        or 0
                    ),

                "attributes":
                    attributes,

                "use_cases":
                    use_case_list,

                "use_case":
                    ", ".join(
                        str(item)
                        for item in use_case_list
                    ),

                "image_url":
                    product.get(
                        "image_url",
                        ""
                    ),

                "product_url":
                    product.get(
                        "product_url",
                        ""
                    ),

                "related_products":
                    related_products,
            }


            # --------------------------------------------------
            # EXPOSE COMMON ATTRIBUTES
            # --------------------------------------------------

            for key in (

                "battery_hours",

                "battery_days",

                "battery_mah",

                "noise_cancellation",

                "microphone_quality",

                "wireless",

                "ram_gb",

                "storage_gb",

                "camera_mp",

                "processor",

                "capacity_liters",

                "power_watts",

                "suction_power",

                "resistance",

                "comfort",

                "lightweight"

            ):

                if key in attributes:

                    normalized_item[
                        key
                    ] = attributes[
                        key
                    ]


            normalized.append(
                normalized_item
            )


        return normalized

    # ==================================================
    # COUNT PRODUCTS
    # ==================================================

    def count_products(
        self
    ):

        conn = get_connection(
            self.db_path
        )


        try:

            return conn.execute(
                """
                SELECT COUNT(*)
                FROM products
                """
            ).fetchone()[0]


        finally:

            conn.close()

    # ==================================================
    # DATABASE ROW → PRODUCT
    # ==================================================

    def _row_to_product(
        self,
        row
    ):

        product = dict(
            row
        )


        # --------------------------------------------------
        # ATTRIBUTES
        # --------------------------------------------------

        product[
            "attributes"
        ] = CatalogService._deserialize(
            product.get(
                "attributes"
            ),
            {}
        )


        # --------------------------------------------------
        # USE CASES
        # --------------------------------------------------

        product[
            "use_cases"
        ] = CatalogService._deserialize(
            product.get(
                "use_cases"
            ),
            []
        )


        # --------------------------------------------------
        # RELATED PRODUCTS
        # --------------------------------------------------

        product[
            "related_products"
        ] = CatalogService._normalize_related_products(
            product.get(
                "related_products"
            )
        )


        # --------------------------------------------------
        # MERCHANT
        # --------------------------------------------------

        if not product.get(
            "merchant_id"
        ):

            product[
                "merchant_id"
            ] = "MERCHANT_DEMO"


        # --------------------------------------------------
        # DERIVE WIRELESS AT READ TIME
        # --------------------------------------------------

        attributes = product.get(
            "attributes"
        )


        if not isinstance(
            attributes,
            dict
        ):

            attributes = {}


        category = str(
            product.get(
                "category",
                ""
            )
        ).strip().lower()


        description = str(
            product.get(
                "description",
                ""
            )
        ).strip().lower()


        if "wireless" not in attributes:

            attributes[
                "wireless"
            ] = (
                "wireless" in category
                or
                "wireless" in description
            )


        product[
            "attributes"
        ] = attributes

        # --------------------------------------------------
        # PRICE COMPARISON
        # --------------------------------------------------

        product[
            "price_comparison"
        ] = self.get_price_comparison(
            product.get("product_id")
        )

        return product

    # ==================================================
    # MERCHANT OFFERS / PRICE COMPARISON
    # ==================================================

    def get_product_offers(
        self,
        product_id,
        in_stock_only=True,
    ):
        """
        Return merchant offers for a product.

        Offers are stored separately from the product catalog so
        the same product can be compared across merchants.
        """
        conn = get_connection(self.db_path)

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

            params = [str(product_id)]

            if in_stock_only:
                sql += """
                    AND LOWER(COALESCE(availability, 'in_stock'))
                    = 'in_stock'
                """

            sql += """
                ORDER BY
                    (price + COALESCE(shipping_fee, 0)) ASC,
                    price ASC
            """

            rows = conn.execute(
                sql,
                params,
            ).fetchall()

            offers = []

            for row in rows:
                offer = dict(row)

                price = float(
                    offer.get("price") or 0
                )

                shipping_fee = float(
                    offer.get("shipping_fee") or 0
                )

                offer["price"] = price
                offer["shipping_fee"] = shipping_fee
                offer["total_price"] = round(
                    price + shipping_fee,
                    2,
                )
                offer["is_verified"] = bool(
                    offer.get("is_verified")
                )

                offers.append(offer)

            return offers

        except Exception:
            # The catalog must continue working even if the
            # optional offers table is unavailable.
            return []

        finally:
            conn.close()

    def get_price_comparison(
        self,
        product_id,
    ):
        """
        Build a safe price-comparison payload.

        Eligible, in-stock offers are preferred for the trusted
        lowest-price decision. No external price is invented.
        """
        offers = self.get_product_offers(
            product_id,
            in_stock_only=True,
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

        # --------------------------------------------------
        # ELIGIBILITY
        # --------------------------------------------------
        # Use the eligibility layer when available. It is responsible
        # for checks such as stock, URL validity, source and freshness.
        # Keep a safe fallback so the catalog never crashes if the
        # optional eligibility module is unavailable.
        eligible_offers = []

        if get_lowest_eligible_offer is not None:
            try:
                eligibility_result = get_lowest_eligible_offer(offers)
                if isinstance(eligibility_result, dict):
                    selected = eligibility_result.get("offer")
                    eligible_count = int(
                        eligibility_result.get("eligible_count") or 0
                    )
                    if selected is not None and eligible_count > 0:
                        selected_id = selected.get("offer_id")
                        eligible_offers = [
                            offer
                            for offer in offers
                            if offer.get("offer_id") == selected_id
                        ]
            except Exception:
                eligible_offers = []

        # Safe fallback to verified offers, then all in-stock offers.
        if not eligible_offers:
            verified_offers = [
                offer for offer in offers if offer.get("is_verified")
            ]
            eligible_offers = verified_offers or offers

        comparison_offers = sorted(
            eligible_offers,
            key=lambda offer: (
                float(offer.get("total_price") or 0),
                float(offer.get("price") or 0),
            ),
        )

        if not comparison_offers:
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

        lowest = comparison_offers[0]
        lowest_total = float(lowest.get("total_price") or 0)
        highest_total = max(
            float(offer.get("total_price") or 0)
            for offer in comparison_offers
        )

        normalized_offers = []
        for offer in comparison_offers:
            item = dict(offer)
            item["is_lowest"] = (
                offer.get("offer_id") == lowest.get("offer_id")
            )
            normalized_offers.append(item)

        return {
            "has_offers": True,
            "offer_count": len(normalized_offers),
            "lowest_price": float(lowest.get("price") or 0),
            "lowest_total": round(lowest_total, 2),
            "lowest_merchant": lowest.get("merchant_name"),
            "lowest_merchant_id": lowest.get("merchant_id"),
            "savings": round(max(0, highest_total - lowest_total), 2),
            "currency": lowest.get("currency", "INR"),
            "offers": normalized_offers,
        }

    # ==================================================
    # RELATED / COMPLEMENTARY PRODUCTS
    # ==================================================

    def get_related_products(
        self,
        product_id,
        limit=3
    ):
        """
        Find complementary products for a primary product.

        Related products are selected using:
        - same merchant
        - different product
        - shared use cases
        - complementary categories
        - price suitability
        """

        primary = self.get_product(
            product_id
        )

        if primary is None:

            return []


        all_products = self.get_all_products()


        primary_category = str(
            primary.get(
                "category",
                ""
            )
        ).strip().lower()


        primary_use_cases = set(

            str(item).strip().lower()

            for item in (
                primary.get(
                    "use_cases"
                )
                or []
            )

            if str(item).strip()

        )


        primary_price = float(
            primary.get(
                "price"
            )
            or 0
        )


        merchant_id = (
            primary.get(
                "merchant_id"
            )
            or "MERCHANT_DEMO"
        )


        # --------------------------------------------------
        # Category relationship map
        # --------------------------------------------------

        complementary_categories = {

            "wireless headphones": {
                "backpacks",
                "smartwatches",
                "watches",
            },

            "gaming headphones": {
                "laptops",
                "smartphones",
                "backpacks",
            },

            "smartphones": {
                "smartwatches",
                "backpacks",
                "headphones",
                "wireless headphones",
                "watches",
            },

            "laptops": {
                "backpacks",
                "wireless headphones",
                "headphones",
            },

            "running shoes": {
                "fitness equipment",
                "smartwatches",
                "backpacks",
            },

            "smartwatches": {
                "running shoes",
                "fitness equipment",
                "smartphones",
                "wireless headphones",
            },

            "backpacks": {
                "laptops",
                "smartphones",
                "running shoes",
                "wireless headphones",
            },

            "fitness equipment": {
                "running shoes",
                "smartwatches",
                "backpacks",
            },

            "air fryers": {
                "vacuum cleaners",
            },

            "vacuum cleaners": {
                "air fryers",
            },

            "watches": {
                "backpacks",
                "smartphones",
            },
        }


        allowed_categories = (
            complementary_categories.get(
                primary_category,
                set()
            )
        )


        scored = []


        # --------------------------------------------------
        # Score every possible product
        # --------------------------------------------------

        for candidate in all_products:

            candidate_id = str(
                candidate.get(
                    "product_id",
                    ""
                )
            )


            # ----------------------------------------------
            # Don't recommend itself
            # ----------------------------------------------

            if candidate_id == str(
                product_id
            ):

                continue


            # ----------------------------------------------
            # Same merchant only
            # ----------------------------------------------

            candidate_merchant = (
                candidate.get(
                    "merchant_id"
                )
                or "MERCHANT_DEMO"
            )


            if candidate_merchant != merchant_id:

                continue


            candidate_category = str(
                candidate.get(
                    "category",
                    ""
                )
            ).strip().lower()


            candidate_use_cases = set(

                str(item).strip().lower()

                for item in (
                    candidate.get(
                        "use_cases"
                    )
                    or []
                )

                if str(item).strip()

            )


            candidate_price = float(
                candidate.get(
                    "price"
                )
                or 0
            )


            # ----------------------------------------------
            # Must be in stock
            # ----------------------------------------------

            if int(
                candidate.get(
                    "stock"
                )
                or 0
            ) <= 0:

                continue


            score = 0


            reasons = []


            # ----------------------------------------------
            # Complementary category
            # ----------------------------------------------

            if candidate_category in allowed_categories:

                score += 50

                reasons.append(
                    "complements the selected product"
                )


            # ----------------------------------------------
            # Shared use case
            # ----------------------------------------------

            shared_use_cases = (
                primary_use_cases
                &
                candidate_use_cases
            )


            if shared_use_cases:

                score += (
                    15
                    *
                    min(
                        len(shared_use_cases),
                        3
                    )
                )

                reasons.append(
                    "matches your use case"
                )


            # ----------------------------------------------
            # Price suitability
            # ----------------------------------------------

            # ----------------------------------------------
# Price suitability
# ----------------------------------------------

            if primary_price > 0:
    
                price_ratio = (
                    candidate_price
                    /
                    primary_price
                )

                if (
                    candidate_price <= 1500
                    or
                    price_ratio <= 0.50
                ):

                    score += 20

                    reasons.append(
                        "affordable add-on"
                    )

                elif price_ratio <= 0.60:

                    score += 5

                else:

                    continue


            # ----------------------------------------------
            # Rating
            # ----------------------------------------------

            rating = float(
                candidate.get(
                    "rating"
                )
                or 0
            )


            if rating >= 4.5:

                score += 10

            elif rating >= 4.0:

                score += 5


            # ----------------------------------------------
            # Stock availability
            # ----------------------------------------------

            stock = int(
                candidate.get(
                    "stock"
                )
                or 0
            )


            if stock >= 10:

                score += 5


            # ----------------------------------------------
            # Only accept meaningful relationships
            # ----------------------------------------------

            if score < 30:

                continue


            scored.append(
                (
                    score,
                    candidate,
                    reasons
                )
            )


        # --------------------------------------------------
        # Sort best first
        # --------------------------------------------------

        scored.sort(
            key=lambda item: (
                -item[0],
                -float(
                    item[1].get(
                        "rating"
                    )
                    or 0
                ),
                float(
                    item[1].get(
                        "price"
                    )
                    or 0
                )
            )
        )


        # --------------------------------------------------
        # Return top recommendations
        # --------------------------------------------------

        results = []


        for score, candidate, reasons in scored:

            item = dict(
                candidate
            )


            item[
                "relation_score"
            ] = round(
                score,
                2
            )


            item[
                "why"
            ] = reasons


            results.append(
                item
            )


            if len(
                results
            ) >= int(limit):

                break


        return results

# ======================================================
# COMPATIBILITY WRAPPER
# ======================================================

def get_catalog_items():
    """
    Compatibility wrapper for older code
    expecting a list of items.
    """

    return (
        CatalogService()
        .get_all_products()
    )