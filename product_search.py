import pandas as pd


CATALOG_PATH = "catalog/products.csv"


class ProductSearch:

    def __init__(self, catalog_path=CATALOG_PATH):

        self.catalog_path = catalog_path
        self.products = pd.read_csv(catalog_path)

        # ==================================================
        # DATA TYPE NORMALIZATION
        # ==================================================

        self.products["price"] = pd.to_numeric(
            self.products["price"],
            errors="coerce"
        )

        self.products["rating"] = pd.to_numeric(
            self.products["rating"],
            errors="coerce"
        )

        self.products["stock"] = pd.to_numeric(
            self.products["stock"],
            errors="coerce"
        ).fillna(0)

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
        required=None,
        preferences=None
    ):

        results = self.products.copy()

        # --------------------------------------------------
        # CATEGORY FILTER
        # --------------------------------------------------

        if category:

            category = str(
                category
            ).strip().lower()

            results = results[
                results["category"]
                .astype(str)
                .str.lower()
                .str.contains(
                    category,
                    na=False
                )
            ]

        # --------------------------------------------------
        # MAXIMUM PRICE FILTER
        # --------------------------------------------------

        if max_price is not None:

            results = results[
                results["price"]
                <= float(max_price)
            ]

        # --------------------------------------------------
        # MINIMUM PRICE FILTER
        # --------------------------------------------------

        if min_price is not None:

            results = results[
                results["price"]
                >= float(min_price)
            ]

        # --------------------------------------------------
        # MINIMUM RATING FILTER
        # --------------------------------------------------

        if min_rating is not None:

            results = results[
                results["rating"]
                >= float(min_rating)
            ]

        # --------------------------------------------------
        # USE CASE FILTER
        # --------------------------------------------------

        if use_cases:

            if isinstance(
                use_cases,
                str
            ):

                use_cases = [
                    use_cases
                ]

            for use_case in use_cases:

                use_case = str(
                    use_case
                ).strip().lower()

                results = results[
                    results["use_case"]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        use_case,
                        na=False
                    )
                ]

        # --------------------------------------------------
        # TEXT SEARCH
        # --------------------------------------------------

        if query:

            query = str(
                query
            ).strip().lower()

            mask = (

                results["name"]
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    na=False
                )

                |

                results["description"]
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    na=False
                )

                |

                results["category"]
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    na=False
                )
            )

            results = results[
                mask
            ]

        # --------------------------------------------------
        # PREFERENCE FILTERS
        # --------------------------------------------------

        if preferences and isinstance(preferences, dict):
            for pref_name, pref_data in preferences.items():
                if not isinstance(pref_data, dict):
                    continue
                value = pref_data.get("value")
                if value is not True or pref_name not in results.columns:
                    continue
                results = results[results[pref_name].astype(str).str.lower().isin(["true", "yes", "1", "y", "on"])]

        # --------------------------------------------------
        # REQUIRED CONSTRAINTS
        # --------------------------------------------------

        if required and isinstance(required, dict):
            for req_name, req_data in required.items():
                if not isinstance(req_data, dict):
                    continue
                
                # Check if attribute exists in dataframe
                if req_name not in results.columns:
                    continue

                value = req_data.get("value")
                operator = req_data.get("operator", "==")

                if value is None:
                    continue

                try:
                    val_float = float(value)
                    col_numeric = pd.to_numeric(results[req_name], errors='coerce')
                    
                    if operator == ">=":
                        results = results[col_numeric >= val_float]
                    elif operator == "<=":
                        results = results[col_numeric <= val_float]
                    elif operator == "==":
                        results = results[col_numeric == val_float]
                except ValueError:
                    # Fallback to string comparison if not numeric
                    col_str = results[req_name].astype(str).str.lower()
                    val_str = str(value).lower()
                    if operator == "==":
                        results = results[col_str == val_str]

        # --------------------------------------------------
        # ONLY PRODUCTS IN STOCK
        # --------------------------------------------------

        results = results[
            results["stock"] > 0
        ]

        return results.reset_index(
            drop=True
        )

    # ==================================================
    # SEARCH USING AI INTENT
    # ==================================================

    def search_from_intent(
        self,
        intent
    ):

        if not isinstance(
            intent,
            dict
        ):

            return pd.DataFrame()

        return self.search_products(

            category=intent.get(
                "subcategory"
            ) or intent.get(
                "category"
            ),

            max_price=intent.get(
                "max_price"
            ),

            min_price=intent.get(
                "min_price"
            ),

            use_cases=intent.get(
                "use_cases",
                []
            ),
            required=intent.get(
                "required",
                {}
            ),
            preferences=intent.get(
                "preferences",
                {}
            )
        )

    # ==================================================
    # CONVERT PRODUCT TO STANDARD FORMAT
    # ==================================================

    @staticmethod
    def to_product_dict(
        product
    ):

        return {

            # --------------------------------------------------
            # BASIC PRODUCT INFORMATION
            # --------------------------------------------------

            "product_id": str(
                product.get(
                    "product_id",
                    ""
                )
            ),

            "name": str(
                product.get(
                    "name",
                    ""
                )
            ),

            "brand": str(
                product.get(
                    "brand",
                    "Merchant Brand"
                )
            ),

            "category": str(
                product.get(
                    "category",
                    ""
                )
            ),

            "subcategory": str(
                product.get(
                    "category",
                    ""
                )
            ),

            # --------------------------------------------------
            # PRICE
            # --------------------------------------------------

            "price": float(
                product.get(
                    "price",
                    0
                )
            ),

            "currency": str(
                product.get(
                    "currency",
                    "INR"
                )
            ),

            # --------------------------------------------------
            # PRODUCT INFORMATION
            # --------------------------------------------------

            "description": str(
                product.get(
                    "description",
                    ""
                )
            ),

            "rating": float(
                product.get(
                    "rating",
                    0
                )
            ),

            "stock": int(
                product.get(
                    "stock",
                    0
                )
            ),

            # --------------------------------------------------
            # ORIGINAL MERCHANT ATTRIBUTES
            # --------------------------------------------------

            "battery_hours": product.get(
                "battery_hours"
            ),

            "noise_cancellation": product.get(
                "noise_cancellation"
            ),

            "microphone_quality": product.get(
                "microphone_quality"
            ),

            # The merchant catalog currently does not
            # have a dedicated wireless column.
            # Wireless is derived in build_attributes().
            "wireless": product.get(
                "wireless"
            ),

            "use_case": str(
                product.get(
                    "use_case",
                    ""
                )
            ),

            # --------------------------------------------------
            # COMMERCE MEDIA
            # --------------------------------------------------

            "image_url": str(
                product.get(
                    "image_url",
                    ""
                )
            ),

            "product_url": str(
                product.get(
                    "product_url",
                    ""
                )
            )
        }

    # ==================================================
    # BUILD UNIVERSAL ATTRIBUTES
    # ==================================================

    @staticmethod
    def build_attributes(
        product
    ):

        attributes = {}

        # --------------------------------------------------
        # BATTERY HOURS
        # --------------------------------------------------

        battery_hours = product.get(
            "battery_hours"
        )

        if pd.notna(
            battery_hours
        ):

            try:

                attributes[
                    "battery_hours"
                ] = float(
                    battery_hours
                )

            except (
                TypeError,
                ValueError
            ):

                pass

        # --------------------------------------------------
        # NOISE CANCELLATION
        # --------------------------------------------------

        noise = product.get(
            "noise_cancellation"
        )

        if pd.notna(
            noise
        ):

            attributes[
                "noise_cancellation"
            ] = (
                str(noise)
                .strip()
                .lower()
                in [
                    "yes",
                    "true",
                    "1"
                ]
            )

        # --------------------------------------------------
        # MICROPHONE QUALITY
        # --------------------------------------------------

        microphone = product.get(
            "microphone_quality"
        )

        if pd.notna(
            microphone
        ):

            attributes[
                "microphone_quality"
            ] = str(
                microphone
            )

        # --------------------------------------------------
        # WIRELESS
        #
        # The merchant catalog does not have a dedicated
        # "wireless" column.
        #
        # Therefore:
        #
        # 1. If a wireless column exists, use it.
        # 2. Otherwise derive wireless from category
        #    and description.
        #
        # Example:
        #
        # category:
        # "wireless headphones"
        #
        # description:
        # "Wireless headphones with long battery life"
        #
        # Result:
        #
        # wireless = True
        # --------------------------------------------------

        wireless = product.get(
            "wireless"
        )

        if pd.notna(
            wireless
        ):

            if isinstance(
                wireless,
                bool
            ):

                attributes[
                    "wireless"
                ] = wireless

            else:

                attributes[
                    "wireless"
                ] = (
                    str(wireless)
                    .strip()
                    .lower()
                    in [
                        "yes",
                        "true",
                        "1",
                        "wireless"
                    ]
                )

        else:

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

            attributes[
                "wireless"
            ] = (
                "wireless" in category
                or "wireless" in description
            )

        return attributes

    # ==================================================
    # BUILD USE CASE LIST
    # ==================================================

    @staticmethod
    def build_use_cases(
        product
    ):

        use_cases = []

        raw_use_cases = product.get(
            "use_case",
            ""
        )

        if pd.isna(
            raw_use_cases
        ):

            return use_cases

        for item in str(
            raw_use_cases
        ).split(","):

            item = item.strip()

            if item:

                use_cases.append(
                    item
                )

        return use_cases

    # ==================================================
    # CONVERT ONE PRODUCT TO UNIVERSAL FORMAT
    # ==================================================

    def to_universal_product(
        self,
        product
    ):

        data = self.to_product_dict(
            product
        )

        # --------------------------------------------------
        # Universal attributes
        # --------------------------------------------------

        data["attributes"] = (
            self.build_attributes(
                product
            )
        )

        # --------------------------------------------------
        # Universal use cases
        # --------------------------------------------------

        data["use_cases"] = (
            self.build_use_cases(
                product
            )
        )

        return data

    # ==================================================
    # CONVERT SEARCH RESULTS TO UNIVERSAL DATAFRAME
    # ==================================================

    def to_universal_dataframe(
        self,
        results
    ):

        if (
            results is None
            or results.empty
        ):

            return pd.DataFrame()

        products = []

        for _, product in results.iterrows():

            universal_product = (
                self.to_universal_product(
                    product
                )
            )

            products.append(
                universal_product
            )

        return pd.DataFrame(
            products
        )

    # ==================================================
    # GET PRODUCT BY ID
    # ==================================================

    def get_product(
        self,
        product_id
    ):

        result = self.products[
            self.products[
                "product_id"
            ].astype(str)
            == str(product_id)
        ]

        if result.empty:

            return None

        return result.iloc[0]

    # ==================================================
    # GET ALL CATEGORIES
    # ==================================================

    def get_categories(
        self
    ):

        return sorted(
            self.products[
                "category"
            ]
            .dropna()
            .unique()
            .tolist()
        )

    # ==================================================
    # GET PRODUCT COUNT
    # ==================================================

    def get_product_count(
        self
    ):

        return len(
            self.products
        )


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    search = ProductSearch()

    print("=" * 70)
    print(
        "       RAZORPAY AI COMMERCE AGENT"
    )
    print(
        "              MERCHANT SEARCH"
    )
    print("=" * 70)

    # ==================================================
    # TEST 1 — HEADPHONES
    # ==================================================

    print(
        "\nTEST 1 — Wireless headphones "
        "under ₹3,000"
    )

    print("-" * 70)

    results = search.search_products(

        category="wireless headphones",

        max_price=3000,

        use_cases=[
            "travel"
        ]
    )

    if results.empty:

        print(
            "No matching products found."
        )

    else:

        for _, product in results.iterrows():

            data = search.to_product_dict(
                product
            )

            print(
                f"{data['product_id']} | "
                f"{data['name']} | "
                f"₹{data['price']} | "
                f"Rating: {data['rating']} | "
                f"Stock: {data['stock']}"
            )

    # ==================================================
    # TEST 2 — PRICE
    # ==================================================

    print(
        "\nTEST 2 — Products under ₹2,000"
    )

    print("-" * 70)

    results = search.search_products(
        max_price=2000
    )

    print(
        f"Products found: "
        f"{len(results)}"
    )

    # ==================================================
    # TEST 3 — UNKNOWN PRODUCT
    # ==================================================

    print(
        "\nTEST 3 — Unknown product"
    )

    print("-" * 70)

    results = search.search_products(
        category="televisions"
    )

    print(
        f"Products found: "
        f"{len(results)}"
    )

    # ==================================================
    # TEST 4 — UNIVERSAL ADAPTER
    # ==================================================

    print(
        "\nTEST 4 — Universal Product Adapter"
    )

    print("-" * 70)

    results = search.search_products(

        category="wireless headphones",

        max_price=3000,

        use_cases=[
            "travel"
        ]
    )

    universal = (
        search.to_universal_dataframe(
            results
        )
    )

    if universal.empty:

        print(
            "No products available."
        )

    else:

        print(
            f"Universal products: "
            f"{len(universal)}"
        )

        for _, product in universal.iterrows():

            print(
                f"\nProduct ID: "
                f"{product['product_id']}"
            )

            print(
                f"Name: "
                f"{product['name']}"
            )

            print(
                f"Price: "
                f"₹{product['price']}"
            )

            print(
                f"Rating: "
                f"{product['rating']}"
            )

            print(
                f"Attributes: "
                f"{product['attributes']}"
            )

            print(
                f"Use Cases: "
                f"{product['use_cases']}"
            )

            print(
                f"Image URL: "
                f"{product['image_url']}"
            )

            print(
                f"Product URL: "
                f"{product['product_url']}"
            )

    # ==================================================
    # TEST 5 — AI INTENT
    # ==================================================

    print(
        "\nTEST 5 — AI Intent Search"
    )

    print("-" * 70)

    test_intent = {

        "category": "Electronics",

        "subcategory": "wireless headphones",

        "max_price": 3000,

        "min_price": None,

        "use_cases": [
            "travel",
            "online classes"
        ],

        "preferences": {

            "battery_hours": {

                "value": None,

                "importance": "high",

                "direction": "maximize"
            },

            "wireless": {

                "value": True,

                "importance": "high",

                "direction": "match"
            }
        }
    }

    results = search.search_from_intent(
        test_intent
    )

    print(
        f"Products found: "
        f"{len(results)}"
    )

    if not results.empty:

        universal = (
            search.to_universal_dataframe(
                results
            )
        )

        for _, product in universal.iterrows():

            print(
                f"{product['product_id']} | "
                f"{product['name']} | "
                f"₹{product['price']}"
            )

    # ==================================================
    # TEST 6 — PRODUCT BY ID
    # ==================================================

    print(
        "\nTEST 6 — Product Lookup"
    )

    print("-" * 70)

    product = search.get_product(
        "P001"
    )

    if product is None:

        print(
            "Product P001 not found."
        )

    else:

        data = search.to_universal_product(
            product
        )

        print(
            f"Product: "
            f"{data['name']}"
        )

        print(
            f"Price: "
            f"₹{data['price']}"
        )

        print(
            f"Attributes: "
            f"{data['attributes']}"
        )

    # ==================================================
    # TEST 7 — CATALOG INFORMATION
    # ==================================================

    print(
        "\nTEST 7 — Catalog Information"
    )

    print("-" * 70)

    print(
        f"Total merchant products: "
        f"{search.get_product_count()}"
    )

    print(
        "\nCategories:"
    )

    for category in search.get_categories():

        print(
            f"• {category}"
        )

    # ==================================================
    # FINISH
    # ==================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "Merchant product search "
        "and universal adapter "
        "completed successfully!"
    )

    print(
        "=" * 70
    )