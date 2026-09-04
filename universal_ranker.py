import json
import math
import pandas as pd


CATALOG_PATH = "catalog/products_universal.csv"


class UniversalRanker:

    """
    Universal attribute-aware product ranking engine.

    It works with the actual attributes present in
    products_universal.csv, including:

    Headphones:
        battery_hours, noise_cancellation, microphone_quality, wireless

    Smartphones:
        battery_mah, camera_mp, ram_gb, storage_gb, 5g

    Laptops:
        ram_gb, storage_gb, processor, battery_hours

    Smartwatches:
        battery_days, water_resistant, heart_rate, gps

    Running Shoes:
        material, comfort, water_resistant, lightweight

    Backpacks:
        capacity_liters, material, laptop_compartment

    Watches:
        material, water_resistant, style

    Air Fryers:
        capacity_liters, power_watts, digital_controls

    Vacuum Cleaners:
        suction_power, battery_minutes, cordless

    Fitness Equipment:
        resistance, portable, home_use
    """

    IMPORTANCE_WEIGHTS = {
        "critical": 1.60,
        "high": 1.30,
        "medium": 1.00,
        "low": 0.70
    }

    # Attribute aliases allow the intent normalizer and catalog
    # to use slightly different names safely.
    ATTRIBUTE_ALIASES = {
        "battery_hours": [
            "battery_hours",
            "battery_life_hours"
        ],
        "battery_days": [
            "battery_days"
        ],
        "battery_mah": [
            "battery_mah"
        ],
        "camera_mp": [
            "camera_mp"
        ],
        "ram_gb": [
            "ram_gb"
        ],
        "storage_gb": [
            "storage_gb"
        ],
        "noise_cancellation": [
            "noise_cancellation",
            "anc"
        ],
        "wireless": [
            "wireless",
            "bluetooth"
        ],
        "comfort": [
            "comfort",
            "comfort_score"
        ],
        "lightweight": [
            "lightweight"
        ],
        "water_resistant": [
            "water_resistant"
        ],
        "heart_rate": [
            "heart_rate"
        ],
        "gps": [
            "gps"
        ],
        "5g": [
            "5g"
        ],
        "capacity_liters": [
            "capacity_liters"
        ],
        "power_watts": [
            "power_watts"
        ],
        "digital_controls": [
            "digital_controls"
        ],
        "suction_power": [
            "suction_power"
        ],
        "battery_minutes": [
            "battery_minutes"
        ],
        "cordless": [
            "cordless"
        ],
        "portable": [
            "portable"
        ],
        "home_use": [
            "home_use"
        ],
        "laptop_compartment": [
            "laptop_compartment"
        ],
        "material": [
            "material"
        ],
        "style": [
            "style"
        ],
        "resistance": [
            "resistance"
        ],
        "microphone_quality": [
            "microphone_quality"
        ],
        "processor": [
            "processor"
        ]
    }

    MAXIMIZE_KEYS = {
        "battery_hours",
        "battery_days",
        "battery_mah",
        "camera_mp",
        "storage_gb",
        "capacity_liters",
        "power_watts",
        "suction_power",
        "battery_minutes",
        "ram_gb",
        "processor"
    }

    # Used when a qualitative preference such as "good battery"
    # has no numeric target.
    QUALITATIVE_LEVELS = {
        "poor": 0.20,
        "low": 0.35,
        "average": 0.50,
        "medium": 0.60,
        "good": 0.75,
        "high": 0.85,
        "excellent": 1.00,
        "best": 1.00,
        "great": 0.90,
        "long": 0.85,
        "strong": 0.85,
        "better": 0.80,
        "premium": 0.90,
        "top": 1.00
    }

    PROCESSOR_TIERS = {
        "core i9": 4.0,
        "ryzen 9": 4.0,
        "core i7": 3.0,
        "ryzen 7": 3.0,
        "core i5": 2.0,
        "ryzen 5": 2.0,
        "core i3": 1.0,
        "ryzen 3": 1.0
    }

    def __init__(self, catalog=None):
        self.catalog = catalog

        if catalog is not None and hasattr(catalog, "products"):
            self.products = catalog.products
        else:
            self.products = pd.read_csv(CATALOG_PATH)

    # ==================================================
    # SAFE JSON / VALUE HELPERS
    # ==================================================

    @staticmethod
    def parse_attributes(value):
        if isinstance(value, dict):
            return value

        if value is None:
            return {}

        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def parse_use_cases(value):
        if isinstance(value, list):
            return value

        if value is None:
            return []

        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (TypeError, json.JSONDecodeError):
            return []

    @staticmethod
    def number(value):
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if value is None:
            return None

        text = str(value).lower().strip()

        for token in ["hours", "hour", "hrs", "hr", "days", "day", "mp", "gb", "mah", "watts", "w"]:
            text = text.replace(token, "")

        try:
            return float(text.strip())
        except ValueError:
            return None

    @staticmethod
    def importance_weight(importance):
        return UniversalRanker.IMPORTANCE_WEIGHTS.get(
            str(importance).lower(),
            1.0
        )

    @staticmethod
    def clamp(value, low=0.0, high=1.0):
        return max(low, min(high, float(value)))

    # ==================================================
    # ATTRIBUTE LOOKUP
    # ==================================================

    def get_attribute(self, attributes, key):

        aliases = self.ATTRIBUTE_ALIASES.get(
            key,
            [key]
        )

        for alias in aliases:
            if alias in attributes:
                return attributes[alias]

        return None

    # ==================================================
    # NORMALIZED ATTRIBUTE SCORE
    # ==================================================

    def normalized_numeric_score(
        self,
        value,
        candidates,
        key,
        direction
    ):
        """
        Convert a numeric attribute into a 0..1 relative score.

        maximize:
            highest value gets 1.0

        minimize:
            lowest value gets 1.0

        match:
            handled separately by target matching
        """

        numeric_values = []

        for _, product in candidates.iterrows():

            attrs = self.parse_attributes(
                product.get("attributes")
            )

            candidate_value = self.get_attribute(
                attrs,
                key
            )

            number = self.number(candidate_value)

            if number is not None:
                numeric_values.append(number)

        current = self.number(value)

        if current is None or not numeric_values:
            return None

        low = min(numeric_values)
        high = max(numeric_values)

        if math.isclose(low, high):
            return 1.0

        if direction == "minimize":
            return self.clamp(
                (high - current) /
                (high - low)
            )

        return self.clamp(
            (current - low) /
            (high - low)
        )

    # ==================================================
    # TARGET MATCH SCORE
    # ==================================================

    def target_match_score(
        self,
        actual,
        wanted,
        key
    ):

        if wanted is None:
            return None

        if actual is None:
            return None

        # Boolean preference
        if isinstance(wanted, bool):

            if isinstance(actual, bool):
                return 1.0 if actual == wanted else 0.0

            text = str(actual).lower().strip()

            actual_bool = text in {
                "true",
                "yes",
                "available",
                "enabled"
            }

            return 1.0 if actual_bool == wanted else 0.0

        # Numeric target
        wanted_num = self.number(wanted)
        actual_num = self.number(actual)

        if wanted_num is not None and actual_num is not None:

            # For numeric "match", values at or above the target
            # are considered a strong match.
            if key in {
                "ram_gb",
                "storage_gb",
                "battery_hours",
                "battery_days",
                "battery_mah",
                "camera_mp",
                "capacity_liters",
                "power_watts",
                "suction_power",
                "battery_minutes"
            }:

                if actual_num >= wanted_num:
                    return 1.0

                # Partial credit when below target.
                if wanted_num == 0:
                    return 0.0

                return self.clamp(
                    actual_num / wanted_num
                )

            return self.clamp(
                1.0 -
                abs(actual_num - wanted_num) /
                max(abs(wanted_num), 1.0)
            )

        # Text / qualitative matching
        actual_text = str(actual).lower().strip()
        wanted_text = str(wanted).lower().strip()

        if actual_text == wanted_text:
            return 1.0

        # Qualitative levels
        actual_level = self.QUALITATIVE_LEVELS.get(
            actual_text
        )

        wanted_level = self.QUALITATIVE_LEVELS.get(
            wanted_text
        )

        if actual_level is not None and wanted_level is not None:

            if actual_level >= wanted_level:
                return 1.0

            return self.clamp(
                actual_level / wanted_level
            )

        # Substring / semantic-ish simple match
        if (
            wanted_text in actual_text
            or actual_text in wanted_text
        ):
            return 1.0

        return 0.0

    # ==================================================
    # PREFERENCE SCORE
    # ==================================================

    def preference_score(
        self,
        product,
        candidates,
        key,
        requirement
    ):

        if not isinstance(requirement, dict):
            return 0.0, 0.0

        attributes = self.parse_attributes(
            product.get("attributes")
        )

        actual = self.get_attribute(
            attributes,
            key
        )

        if actual is None:
            return 0.0, 0.0

        wanted = requirement.get("value")

        direction = requirement.get(
            "direction",
            "match"
        )

        importance = requirement.get(
            "importance",
            "medium"
        )

        weight = self.importance_weight(
            importance
        )

        # --------------------------------------------------
        # Explicit maximize / minimize
        # --------------------------------------------------

        if direction in {
            "maximize",
            "minimize"
        }:

            if key == "processor":
                actual_tier = 0.5
                actual_str = str(actual).lower().strip()
                for p_key, p_tier in self.PROCESSOR_TIERS.items():
                    if p_key in actual_str:
                        actual_tier = p_tier
                        break
                
                # Normalizing processor tiers across candidates
                candidate_tiers = []
                for _, c in candidates.iterrows():
                    c_attr = self.parse_attributes(c.get("attributes"))
                    c_proc = str(self.get_attribute(c_attr, "processor")).lower().strip()
                    c_tier = 0.5
                    for p_key, p_tier in self.PROCESSOR_TIERS.items():
                        if p_key in c_proc:
                            c_tier = p_tier
                            break
                    candidate_tiers.append(c_tier)
                
                max_tier = max(candidate_tiers) if candidate_tiers else 4.0
                min_tier = min(candidate_tiers) if candidate_tiers else 0.5
                
                if max_tier == min_tier:
                    score = 1.0
                else:
                    if direction == "maximize":
                        score = (actual_tier - min_tier) / (max_tier - min_tier)
                    else:
                        score = (max_tier - actual_tier) / (max_tier - min_tier)
            elif isinstance(actual, str):

                actual_level = self.QUALITATIVE_LEVELS.get(
                    actual.lower().strip()
                )

                if actual_level is not None:

                    score = actual_level

                else:

                    score = 0.5

            else:

                score = self.normalized_numeric_score(
                    actual,
                    candidates,
                    key,
                    direction
                )

                if score is None:
                    score = 0.0

            return (
                self.clamp(score),
                weight
            )

        # --------------------------------------------------
        # Match
        # --------------------------------------------------

        score = self.target_match_score(
            actual,
            wanted,
            key
        )

        if score is None:
            return 0.0, 0.0

        return (
            self.clamp(score),
            weight
        )

    # ==================================================
    # USE CASE SCORE
    # ==================================================

    def use_case_score(
        self,
        product,
        requested_use_cases
    ):

        if not requested_use_cases:
            return 0.0, 0.0

        product_use_cases = self.parse_use_cases(
            product.get("use_cases")
        )

        product_use_cases = {
            str(x).strip().lower()
            for x in product_use_cases
        }

        if not product_use_cases:
            return 0.0, 0.0

        requested = {
            str(x).strip().lower()
            for x in requested_use_cases
        }

        matched = requested.intersection(
            product_use_cases
        )

        if not matched:
            return 0.0, 1.0

        return (
            len(matched) / max(len(requested), 1),
            1.0
        )

    # ==================================================
    # BASE PRODUCT SCORE
    # ==================================================

    def base_score(
        self,
        product,
        max_price=None,
        min_price=None
    ):

        score = 0.0
        weight = 0.0

        # Rating contributes to general product quality.
        rating = self.number(
            product.get("rating")
        )

        if rating is not None:
            rating_score = self.clamp(
                rating / 5.0
            )

            score += rating_score * 1.0
            weight += 1.0

        # Stock gives a small availability signal.
        stock = self.number(
            product.get("stock")
        )

        if stock is not None:
            stock_score = 1.0 if stock > 0 else 0.0
            score += stock_score * 0.30
            weight += 0.30

        # Budget fit is rewarded.
        price = self.number(
            product.get("price")
        )

        if price is not None:

            if max_price is not None:

                max_price_num = self.number(
                    max_price
                )

                if (
                    max_price_num is not None
                    and max_price_num > 0
                ):

                    if price <= max_price_num:
                        budget_score = 1.0

                        # Slight preference for products that
                        # are not unnecessarily expensive.
                        savings_ratio = (
                            max_price_num - price
                        ) / max_price_num

                        budget_score = (
                            0.85 +
                            0.15 *
                            self.clamp(savings_ratio)
                        )

                    else:
                        budget_score = 0.0

                    score += budget_score * 1.2
                    weight += 1.2

            elif min_price is not None:

                min_price_num = self.number(
                    min_price
                )

                if (
                    min_price_num is not None
                    and price >= min_price_num
                ):
                    score += 1.0 * 0.8
                    weight += 0.8

        if weight == 0:
            return 0.0

        return self.clamp(
            score / weight
        )

    # ==================================================
    # RANK PRODUCTS
    # ==================================================

    def rank(
        self,
        candidates,
        max_price=None,
        min_price=None,
        use_cases=None,
        preferences=None,
        top_n=5
    ):

        if candidates is None or candidates.empty:
            return pd.DataFrame()

        use_cases = use_cases or []
        preferences = preferences or {}

        results = candidates.copy()

        scores = []

        for _, product in results.iterrows():

            # ------------------------------------------
            # Base score
            # ------------------------------------------

            base = self.base_score(
                product,
                max_price=max_price,
                min_price=min_price
            )

            total_score = base * 0.20
            total_weight = 0.20

            # ------------------------------------------
            # Use case
            # ------------------------------------------

            uc_score, uc_weight = self.use_case_score(
                product,
                use_cases
            )

            if uc_weight > 0:
                total_score += uc_score * 0.20
                total_weight += 0.20

            # ------------------------------------------
            # User preferences
            # ------------------------------------------

            preference_weight_total = 0.0

            for key, requirement in preferences.items():

                score, weight = self.preference_score(
                    product,
                    results,
                    key,
                    requirement
                )

                if weight > 0:

                    # Preferences dominate generic rating.
                    total_score += score * weight
                    total_weight += weight

                    preference_weight_total += weight

            # ------------------------------------------
            # Final percentage
            # ------------------------------------------

            if total_weight > 0:
                final_score = (
                    total_score /
                    total_weight
                ) * 100
            else:
                final_score = 0.0

            scores.append(
                round(
                    self.clamp(
                        final_score,
                        0,
                        100
                    ),
                    2
                )
            )

        results["match_score"] = scores

        # Higher match first.
        # Rating is the secondary tie-breaker.
        # Price is the tertiary tie-breaker.
        results = results.sort_values(
            by=[
                "match_score",
                "rating",
                "price"
            ],
            ascending=[
                False,
                False,
                True
            ]
        )

        return results.head(
            top_n
        ).reset_index(drop=True)

    # ==================================================
    # DISPLAY
    # ==================================================

    @staticmethod
    def display_results(results):

        if results.empty:
            print("No products found.")
            return

        for index, (_, product) in enumerate(
            results.iterrows(),
            start=1
        ):

            print(
                f"#{index} "
                f"{product['name']} | "
                f"₹{product['price']} | "
                f"Score: {product['match_score']}%"
            )


# ======================================================
# TEST SUITE
# ======================================================

if __name__ == "__main__":

    from catalog_engine import CatalogEngine

    catalog = CatalogEngine()

    ranker = UniversalRanker(
        catalog
    )

    tests = [

        # --------------------------------------------------
        # TEST 1 — HEADPHONES
        # --------------------------------------------------

        {
            "name": "Headphones",
            "subcategory": "Headphones",
            "max_price": 3000,
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
                    "importance": "critical",
                    "direction": "match"
                }
            }
        },

        # --------------------------------------------------
        # TEST 2 — LAPTOPS
        # --------------------------------------------------

        {
            "name": "Laptops",
            "subcategory": "Laptops",
            "max_price": 60000,
            "use_cases": [
                "coding"
            ],
            "preferences": {
                "ram_gb": {
                    "value": 16,
                    "importance": "high",
                    "direction": "match"
                },
                "battery_hours": {
                    "value": None,
                    "importance": "medium",
                    "direction": "maximize"
                }
            }
        },

        # --------------------------------------------------
        # TEST 3 — RUNNING SHOES
        # --------------------------------------------------

        {
            "name": "Running Shoes",
            "subcategory": "Running Shoes",
            "max_price": 4000,
            "use_cases": [
                "running"
            ],
            "preferences": {
                "comfort": {
                    "value": "high",
                    "importance": "high",
                    "direction": "match"
                }
            }
        },

        # --------------------------------------------------
        # TEST 4 — SMARTPHONES
        # --------------------------------------------------

        {
            "name": "Smartphones",
            "subcategory": "Smartphones",
            "max_price": 20000,
            "use_cases": [],
            "preferences": {
                "camera_mp": {
                    "value": None,
                    "importance": "critical",
                    "direction": "maximize"
                }
            }
        },

        # --------------------------------------------------
        # TEST 5 — SMARTWATCHES
        # --------------------------------------------------

        {
            "name": "Smartwatches",
            "subcategory": "Smartwatches",
            "max_price": 5000,
            "use_cases": [],
            "preferences": {
                "battery_days": {
                    "value": None,
                    "importance": "high",
                    "direction": "maximize"
                }
            }
        },

        # --------------------------------------------------
        # TEST 6 — BACKPACKS
        # --------------------------------------------------

        {
            "name": "Backpacks",
            "subcategory": "Backpacks",
            "max_price": 2000,
            "use_cases": [
                "college"
            ],
            "preferences": {
                "capacity_liters": {
                    "value": 25,
                    "importance": "medium",
                    "direction": "match"
                },
                "laptop_compartment": {
                    "value": True,
                    "importance": "high",
                    "direction": "match"
                }
            }
        },

        # --------------------------------------------------
        # TEST 7 — WATCHES
        # --------------------------------------------------

        {
            "name": "Watches",
            "subcategory": "Watches",
            "max_price": 5000,
            "use_cases": [],
            "preferences": {
                "water_resistant": {
                    "value": True,
                    "importance": "medium",
                    "direction": "match"
                }
            }
        },

        # --------------------------------------------------
        # TEST 8 — AIR FRYERS
        # --------------------------------------------------

        {
            "name": "Air Fryers",
            "subcategory": "Air Fryers",
            "max_price": 7000,
            "use_cases": [],
            "preferences": {
                "capacity_liters": {
                    "value": 5,
                    "importance": "high",
                    "direction": "match"
                },
                "power_watts": {
                    "value": None,
                    "importance": "medium",
                    "direction": "maximize"
                }
            }
        },

        # --------------------------------------------------
        # TEST 9 — VACUUM CLEANERS
        # --------------------------------------------------

        {
            "name": "Vacuum Cleaners",
            "subcategory": "Vacuum Cleaners",
            "max_price": 8000,
            "use_cases": [],
            "preferences": {
                "suction_power": {
                    "value": None,
                    "importance": "high",
                    "direction": "maximize"
                },
                "cordless": {
                    "value": True,
                    "importance": "medium",
                    "direction": "match"
                }
            }
        },

        # --------------------------------------------------
        # TEST 10 — FITNESS EQUIPMENT
        # --------------------------------------------------

        {
            "name": "Fitness Equipment",
            "subcategory": "Fitness Equipment",
            "max_price": 3000,
            "use_cases": [
                "fitness"
            ],
            "preferences": {
                "portable": {
                    "value": True,
                    "importance": "high",
                    "direction": "match"
                },
                "resistance": {
                    "value": "high",
                    "importance": "medium",
                    "direction": "match"
                }
            }
        }
    ]

    print("=" * 75)
    print(
        "          RAZORPAY AI COMMERCE AGENT"
    )
    print(
        "          UNIVERSAL RANKER V6"
    )
    print("=" * 75)

    for test in tests:

        print(
            f"\n\nTEST — {test['name']}"
        )

        print("-" * 75)

        candidates = catalog.search(
            subcategory=test["subcategory"],
            max_price=test["max_price"]
        )

        ranked = ranker.rank(
            candidates,
            max_price=test["max_price"],
            use_cases=test["use_cases"],
            preferences=test["preferences"],
            top_n=5
        )

        UniversalRanker.display_results(
            ranked
        )

    print("\n" + "=" * 75)
    print(
        "Universal ranking V6 completed!"
    )
    print("=" * 75)