import json
import pandas as pd


CATALOG_PATH = "catalog/products_universal.csv"


class CatalogEngine:

    # ==================================================
    # ALIASES
    # ==================================================

    CATEGORY_ALIASES = {

        "electronics": "Electronics",
        "electronic": "Electronics",
        "tech": "Electronics",

        "fashion": "Fashion",

        "home": "Home",

        "sports": "Sports",
    }

    SUBCATEGORY_ALIASES = {

        # Headphones
        "headphone": "Headphones",
        "headphones": "Headphones",
        "wireless headphone": "Headphones",
        "wireless headphones": "Headphones",
        "hp": "Headphones",

        # Smartphones
        "phone": "Smartphones",
        "phones": "Smartphones",
        "mobile": "Smartphones",
        "mobiles": "Smartphones",
        "mobile phone": "Smartphones",
        "mobile phones": "Smartphones",
        "smartphone": "Smartphones",
        "smartphones": "Smartphones",

        # Laptops
        "laptop": "Laptops",
        "laptops": "Laptops",
        "notebook": "Laptops",
        "notebooks": "Laptops",

        # Smartwatches
        "smartwatch": "Smartwatches",
        "smartwatches": "Smartwatches",
        "smart watch": "Smartwatches",
        "smart watches": "Smartwatches",

        # Running shoes
        "shoe": "Running Shoes",
        "shoes": "Running Shoes",
        "running shoe": "Running Shoes",
        "running shoes": "Running Shoes",

        # Backpacks
        "bag": "Backpacks",
        "bags": "Backpacks",
        "backpack": "Backpacks",
        "backpacks": "Backpacks",

        # Watches
        "watch": "Watches",
        "watches": "Watches",

        # Air fryers
        "air fryer": "Air Fryers",
        "air fryers": "Air Fryers",
        "airfryer": "Air Fryers",

        # Vacuum cleaners
        "vacuum": "Vacuum Cleaners",
        "vacuum cleaner": "Vacuum Cleaners",
        "vacuum cleaners": "Vacuum Cleaners",

        # Fitness
        "fitness": "Fitness Equipment",
        "fitness equipment": "Fitness Equipment",
        "gym equipment": "Fitness Equipment",
    }

    # ==================================================
    # INIT
    # ==================================================

    def __init__(
        self,
        catalog_path=CATALOG_PATH
    ):

        self.catalog_path = catalog_path

        self.products = pd.read_csv(
            catalog_path
        )

        self.products["attributes"] = (
            self.products["attributes"]
            .apply(self._parse_json)
        )

        self.products["use_cases"] = (
            self.products["use_cases"]
            .apply(self._parse_json)
        )

    # ==================================================
    # JSON PARSER
    # ==================================================

    @staticmethod
    def _parse_json(value):

        if isinstance(value, (dict, list)):
            return value

        try:
            return json.loads(value)

        except (
            TypeError,
            json.JSONDecodeError
        ):
            return {}

    # ==================================================
    # NORMALIZE CATEGORY
    # ==================================================

    @classmethod
    def normalize_category(
        cls,
        value
    ):

        if not value:
            return None

        text = str(
            value
        ).strip().lower()

        return cls.CATEGORY_ALIASES.get(
            text,
            value
        )

    # ==================================================
    # NORMALIZE SUBCATEGORY
    # ==================================================

    @classmethod
    def normalize_subcategory(
        cls,
        value
    ):

        if not value:
            return None

        text = str(
            value
        ).strip().lower()

        return cls.SUBCATEGORY_ALIASES.get(
            text,
            value
        )

    # ==================================================
    # GET CATEGORIES
    # ==================================================

    def get_categories(self):

        return sorted(
            self.products["category"]
            .dropna()
            .unique()
            .tolist()
        )

    # ==================================================
    # GET SUBCATEGORIES
    # ==================================================

    def get_subcategories(self):

        return sorted(
            self.products["subcategory"]
            .dropna()
            .unique()
            .tolist()
        )

    # ==================================================
    # SEARCH
    # ==================================================

    def search(
        self,
        query=None,
        category=None,
        subcategory=None,
        max_price=None,
        min_price=None,
        min_rating=None
    ):

        results = self.products.copy()

        # ==================================================
        # NORMALIZE SEARCH TERMS
        # ==================================================

        category = self.normalize_category(
            category
        )

        subcategory = self.normalize_subcategory(
            subcategory
        )

        # ==================================================
        # SUBCATEGORY
        # ==================================================

        if subcategory:

            results = results[
                results["subcategory"]
                .astype(str)
                .str.strip()
                .str.lower()
                ==
                str(subcategory)
                .strip()
                .lower()
            ]

        # ==================================================
        # CATEGORY
        # ==================================================

        elif category:

            results = results[
                results["category"]
                .astype(str)
                .str.strip()
                .str.lower()
                ==
                str(category)
                .strip()
                .lower()
            ]

        # ==================================================
        # MAX PRICE
        # ==================================================

        if max_price is not None:

            results = results[
                pd.to_numeric(
                    results["price"],
                    errors="coerce"
                )
                <= float(max_price)
            ]

        # ==================================================
        # MIN PRICE
        # ==================================================

        if min_price is not None:

            results = results[
                pd.to_numeric(
                    results["price"],
                    errors="coerce"
                )
                >= float(min_price)
            ]

        # ==================================================
        # RATING
        # ==================================================

        if min_rating is not None:

            results = results[
                pd.to_numeric(
                    results["rating"],
                    errors="coerce"
                )
                >= float(min_rating)
            ]

        # ==================================================
        # TEXT SEARCH
        # ==================================================

        if query:

            query = str(
                query
            ).lower().strip()

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

                results["subcategory"]
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    na=False
                )

                |

                results["brand"]
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    na=False
                )
            )

            results = results[mask]

        # ==================================================
        # ONLY IN-STOCK PRODUCTS
        # ==================================================

        results = results[
            pd.to_numeric(
                results["stock"],
                errors="coerce"
            )
            > 0
        ]

        return results.reset_index(
            drop=True
        )

    # ==================================================
    # GET PRODUCT
    # ==================================================

    def get_product(
        self,
        product_id
    ):

        result = self.products[
            self.products["product_id"]
            == product_id
        ]

        if result.empty:

            return None

        return result.iloc[0]

    # ==================================================
    # DISPLAY
    # ==================================================

    @staticmethod
    def display_products(
        results
    ):

        if results.empty:

            print(
                "No products found."
            )

            return

        for _, product in results.iterrows():

            print(
                f"{product['product_id']} | "
                f"{product['name']} | "
                f"{product['subcategory']} | "
                f"₹{product['price']} | "
                f"Rating: {product['rating']} | "
                f"Stock: {product['stock']}"
            )


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    catalog = CatalogEngine()

    print("=" * 70)
    print(
        "       RAZORPAY AI COMMERCE AGENT"
    )
    print(
        "              UNIVERSAL CATALOG V2"
    )
    print("=" * 70)

    print("\nCategories")
    print("-" * 70)

    for category in catalog.get_categories():

        print(
            f"• {category}"
        )

    print("\nSubcategories")
    print("-" * 70)

    for subcategory in catalog.get_subcategories():

        print(
            f"• {subcategory}"
        )

    # ==================================================
    # TEST 1
    # ==================================================

    print(
        "\n\nTEST 1 — Headphones under ₹3,000"
    )

    print("-" * 70)

    results = catalog.search(
        subcategory="headphones",
        max_price=3000
    )

    catalog.display_products(
        results
    )

    # ==================================================
    # TEST 2
    # ==================================================

    print(
        "\n\nTEST 2 — Laptop under ₹60,000"
    )

    print("-" * 70)

    results = catalog.search(
        subcategory="laptop",
        max_price=60000
    )

    catalog.display_products(
        results
    )

    # ==================================================
    # TEST 3
    # ==================================================

    print(
        "\n\nTEST 3 — Shoes under ₹4,000"
    )

    print("-" * 70)

    results = catalog.search(
        subcategory="shoes",
        max_price=4000
    )

    catalog.display_products(
        results
    )

    # ==================================================
    # TEST 4
    # ==================================================

    print(
        "\n\nTEST 4 — Phone under ₹20,000"
    )

    print("-" * 70)

    results = catalog.search(
        subcategory="phone",
        max_price=20000
    )

    catalog.display_products(
        results
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "Universal catalog V2 test completed!"
    )

    print(
        "=" * 70
    )