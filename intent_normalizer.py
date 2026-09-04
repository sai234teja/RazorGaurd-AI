class IntentNormalizer:
    
    # ==================================================
    # CATEGORY NORMALIZATION
    # ==================================================

    CATEGORY_MAP = {
        # Main categories
        "electronics": "Electronics",
        "electronic": "Electronics",
        "audio": "Electronics",
        "tech": "Electronics",

        "fashion": "Fashion",
        "home": "Home",
        "sports": "Sports",

        # Headphones
        "headphone": "Headphones",
        "headphones": "Headphones",
        "wireless headphone": "Headphones",
        "wireless headphones": "Headphones",
        "hp": "Headphones",

        # Laptops
        "laptop": "Laptops",
        "laptops": "Laptops",
        "notebook": "Laptops",
        "notebooks": "Laptops",

        # Smartphones
        "phone": "Smartphones",
        "phones": "Smartphones",
        "smartphone": "Smartphones",
        "smartphones": "Smartphones",
        "mobile": "Smartphones",
        "mobiles": "Smartphones",
        "mobile phone": "Smartphones",
        "mobile phones": "Smartphones",
        "cell phone": "Smartphones",
        "cell phones": "Smartphones",

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
        "backpack": "Backpacks",
        "backpacks": "Backpacks",
        "bag": "Backpacks",
        "bags": "Backpacks",

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
        "gym equipment": "Fitness Equipment"
    }

    # ==================================================
    # ATTRIBUTE NORMALIZATION
    # ==================================================

    ATTRIBUTE_MAP = {
        # Battery
        "battery": "battery_hours",
        "battery life": "battery_hours",
        "battery_life": "battery_hours",
        "battery hours": "battery_hours",
        "battery_hours": "battery_hours",
        "long battery": "battery_hours",
        "long battery life": "battery_hours",

        # RAM
        "ram": "ram_gb",
        "ram gb": "ram_gb",
        "ram_gb": "ram_gb",
        "memory": "ram_gb",

        # Storage
        "storage": "storage_gb",
        "storage gb": "storage_gb",
        "storage_gb": "storage_gb",

        # Camera
        "camera": "camera_mp",
        "camera mp": "camera_mp",
        "camera_mp": "camera_mp",
        "camera quality": "camera_mp",
        "camera_quality": "camera_mp",

        # Wireless
        "wireless": "wireless",
        "connectivity": "wireless",
        "connectivity_type": "wireless",

        # Noise cancellation
        "noise cancellation": "noise_cancellation",
        "noise cancelation": "noise_cancellation",
        "noise_cancellation": "noise_cancellation",
        "anc": "noise_cancellation",

        # Shoes
        "comfort": "comfort",
        "comfortable": "comfort",
        "lightweight": "lightweight",
        "light weight": "lightweight",

        # Processor
        "processor": "processor",
        "cpu": "processor",

        # Smartphone
        "5g": "5g",

        # Backpack
        "capacity": "capacity_liters",
        "capacity liters": "capacity_liters",
        "capacity_liters": "capacity_liters",

        # Air fryer
        "power": "power_watts",
        "power watts": "power_watts",
        "power_watts": "power_watts",

        # Vacuum
        "suction": "suction_power",
        "suction power": "suction_power",
        "suction_power": "suction_power",

        # Fitness
        "resistance": "resistance"
    }

    # ==================================================
    # USE CASE NORMALIZATION
    # ==================================================

    USE_CASE_MAP = {
        "travel": "travel",
        "travelling": "travel",
        "traveling": "travel",

        "online class": "online classes",
        "online classes": "online classes",
        "classes": "online classes",
        "study": "online classes",

        "coding": "coding",
        "programming": "coding",
        "development": "coding",
        "software development": "coding",

        "gaming": "gaming",
        "game": "gaming",

        "running": "running",
        "run": "running",

        "fitness": "fitness",
        "gym": "gym",
        "workout": "home workout",
        "home workout": "home workout",

        "college": "college",
        "student": "college",

        "office": "office",
        "work": "office",

        "photography": "photography",
        "photos": "photography",

        "daily use": "daily use",
        "everyday": "daily use"
    }

    # ==================================================
    # NORMALIZE CATEGORY
    # ==================================================

    @classmethod
    def normalize_category(cls, value):
        if not value:
            return None

        text = str(value).strip().lower()

        return cls.CATEGORY_MAP.get(text, value)

    # ==================================================
    # NORMALIZE USE CASES
    # ==================================================

    @classmethod
    def normalize_use_cases(cls, use_cases):
        if not isinstance(use_cases, list):
            return []

        normalized = []

        for use_case in use_cases:
            text = str(use_case).strip().lower()

            mapped = cls.USE_CASE_MAP.get(text, text)

            if mapped not in normalized:
                normalized.append(mapped)

        return normalized

    # ==================================================
    # NORMALIZE VALUE
    # ==================================================

    @staticmethod
    def normalize_value(key, value):

        if value is None:
            return None

        # ------------------------------------------------
        # RAM
        # ------------------------------------------------

        if key == "ram_gb":
            if isinstance(value, (int, float)):
                return value

            text = str(value).lower()
            text = text.replace("gb", "").strip()

            try:
                return float(text)
            except ValueError:
                return value

        # ------------------------------------------------
        # STORAGE
        # ------------------------------------------------

        if key == "storage_gb":
            if isinstance(value, (int, float)):
                return value

            text = str(value).lower()
            text = text.replace("gb", "").strip()

            try:
                return float(text)
            except ValueError:
                return value

        # ------------------------------------------------
        # CAMERA
        # ------------------------------------------------

        if key == "camera_mp":
            if isinstance(value, (int, float)):
                return value

            text = str(value).lower().strip()

            text_without_unit = (
                text
                .replace("mp", "")
                .strip()
            )

            qualitative_camera = {
                "best",
                "excellent",
                "high",
                "good",
                "great",
                "top",
                "highest",
                "maximum",
                "max",
                "premium",
                "superior",
                "better"
            }

            if text in qualitative_camera:
                return text

            try:
                return float(text_without_unit)
            except ValueError:
                return value

        # ------------------------------------------------
        # BATTERY
        # ------------------------------------------------

        if key == "battery_hours":
            if isinstance(value, (int, float)):
                return value

            text = str(value).lower().strip()

            qualitative_battery = {
                "long",
                "good",
                "excellent",
                "great",
                "high",
                "best",
                "strong",
                "better",
                "maximum",
                "max",
                "top"
            }

            if text in qualitative_battery:
                return text

            text = (
                text
                .replace("hours", "")
                .replace("hour", "")
                .replace("hrs", "")
                .replace("hr", "")
                .strip()
            )

            try:
                return float(text)
            except ValueError:
                return value

        # ------------------------------------------------
        # BOOLEAN
        # ------------------------------------------------

        boolean_keys = {
            "wireless",
            "noise_cancellation",
            "lightweight",
            "5g",
            "water_resistant",
            "laptop_compartment",
            "cordless",
            "portable",
            "home_use",
            "digital_controls",
            "gps",
            "heart_rate"
        }

        if key in boolean_keys:
            if isinstance(value, bool):
                return value

            text = str(value).strip().lower()

            if text in {
                "yes",
                "true",
                "required",
                "available",
                "wireless",
                "enabled"
            }:
                return True

            if text in {
                "no",
                "false",
                "not required",
                "wired",
                "disabled"
            }:
                return False

        return value

    # ==================================================
    # NORMALIZE PREFERENCES
    # ==================================================

    @classmethod
    def normalize_preferences(cls, preferences):

        if not isinstance(preferences, dict):
            return {}

        normalized = {}

        for raw_key, raw_requirement in preferences.items():

            key = str(raw_key).strip().lower()

            canonical_key = cls.ATTRIBUTE_MAP.get(key)

            if not canonical_key:
                continue

            # ------------------------------------------------
            # Read Gemini structured preference
            # ------------------------------------------------

            if isinstance(raw_requirement, dict):

                value = raw_requirement.get("value")

                importance = raw_requirement.get(
                    "importance",
                    "medium"
                )

                # THIS IS THE IMPORTANT FIX:
                # Preserve Gemini's explicit direction.
                incoming_direction = raw_requirement.get(
                    "direction"
                )

            else:

                value = raw_requirement
                importance = "medium"
                incoming_direction = None

            # ------------------------------------------------
            # Normalize value
            # ------------------------------------------------

            value = cls.normalize_value(
                canonical_key,
                value
            )

            # ------------------------------------------------
            # Determine direction
            # ------------------------------------------------

            valid_directions = {
                "match",
                "maximize",
                "minimize"
            }

            if incoming_direction in valid_directions:

                # Preserve explicit direction from Gemini
                direction = incoming_direction

            else:

                # Default
                direction = "match"

                # Infer maximize from qualitative language
                if isinstance(value, str):

                    text = value.strip().lower()

                    maximize_words = {
                        "best",
                        "excellent",
                        "high",
                        "highest",
                        "top",
                        "maximum",
                        "max",
                        "great",
                        "greatest",
                        "premium",
                        "superior",
                        "long",
                        "better"
                    }

                    if text in maximize_words:

                        value = None
                        direction = "maximize"

            # ------------------------------------------------
            # Special handling:
            # qualitative camera/battery requests
            # ------------------------------------------------

            if canonical_key in {
                "camera_mp",
                "battery_hours"
            }:

                if isinstance(value, str):

                    text = value.strip().lower()

                    maximize_words = {
                        "best",
                        "excellent",
                        "high",
                        "highest",
                        "top",
                        "maximum",
                        "max",
                        "great",
                        "greatest",
                        "premium",
                        "superior",
                        "long",
                        "better",
                        "good"
                    }

                    if (
                        text in maximize_words
                        and direction == "match"
                    ):
                        value = None
                        direction = "maximize"

            normalized[canonical_key] = {
                "value": value,
                "importance": importance,
                "direction": direction
            }

        return normalized

    # ==================================================
    # COMPLETE NORMALIZATION
    # ==================================================

    @classmethod
    def normalize(cls, intent):

        if not isinstance(intent, dict):
            return {}

        return {
            "category": cls.normalize_category(
                intent.get("category")
            ),

            "subcategory": cls.normalize_category(
                intent.get("subcategory")
            ),

            "max_price": intent.get("max_price"),

            "min_price": intent.get("min_price"),

            "use_cases": cls.normalize_use_cases(
                intent.get("use_cases", [])
            ),

            "preferences": cls.normalize_preferences(
                intent.get("preferences", {})
            ),
            
            "required": intent.get("required", {})
        }

    @classmethod
    def recover_constraints(cls, raw_query, intent, fallback_parser):
        """
        Recover missing required numeric constraints by
        running the deterministic fallback parser on the raw query.
        """
        if not raw_query or not intent:
            return intent
            
        try:
            fallback_intent = fallback_parser(raw_query)
        except Exception:
            return intent
            
        # 1. Recover price bounds
        if intent.get("max_price") is None and fallback_intent.get("max_price") is not None:
            intent["max_price"] = fallback_intent.get("max_price")
            
        if intent.get("min_price") is None and fallback_intent.get("min_price") is not None:
            intent["min_price"] = fallback_intent.get("min_price")
            
        # 2. Recover Category/Subcategory
        if not intent.get("category") and fallback_intent.get("category"):
            intent["category"] = fallback_intent.get("category")
        if not intent.get("subcategory") and fallback_intent.get("subcategory"):
            intent["subcategory"] = fallback_intent.get("subcategory")
            
        # 3. Recover Required RAM and Storage
        req = intent.setdefault("required", {})
        fallback_req = fallback_intent.get("required", {})
        
        for key in ["ram_gb", "storage_gb"]:
            if key in fallback_req and key not in req:
                req[key] = fallback_req[key]
                
                # If it was erroneously put in preferences by the LLM, remove it
                if key in intent.get("preferences", {}):
                    del intent["preferences"][key]
                    
        return intent


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    import json

    normalizer = IntentNormalizer()

    test_intents = [

        # ==================================================
        # TEST 1 — HEADPHONES
        # ==================================================

        {
            "category": "Audio",
            "subcategory": "Wireless Headphones",
            "max_price": 3000,
            "min_price": None,
            "use_cases": [
                "travel",
                "online classes"
            ],
            "preferences": {
                "battery_life": {
                    "value": "long",
                    "importance": "high",
                    "direction": "maximize"
                },
                "connectivity_type": {
                    "value": "wireless",
                    "importance": "critical",
                    "direction": "match"
                }
            }
        },

        # ==================================================
        # TEST 2 — LAPTOP
        # ==================================================

        {
            "category": "Electronics",
            "subcategory": "Laptops",
            "max_price": 60000,
            "min_price": None,
            "use_cases": [
                "coding"
            ],
            "preferences": {
                "RAM": {
                    "value": "16GB",
                    "importance": "high",
                    "direction": "match"
                },
                "battery_life": {
                    "value": "long",
                    "importance": "medium",
                    "direction": "maximize"
                }
            }
        },

        # ==================================================
        # TEST 3 — RUNNING SHOES
        # ==================================================

        {
            "category": "shoes",
            "subcategory": "running shoes",
            "max_price": 4000,
            "min_price": None,
            "use_cases": [
                "running"
            ],
            "preferences": {
                "comfort": {
                    "value": True,
                    "importance": "high",
                    "direction": "match"
                }
            }
        },

        # ==================================================
        # TEST 4 — SMARTPHONE
        # ==================================================

        {
            "category": "Electronics",
            "subcategory": "Mobile Phones",
            "max_price": 20000,
            "min_price": None,
            "use_cases": [],
            "preferences": {
                "Camera Quality": {
                    "value": "High",
                    "importance": "critical",
                    "direction": "maximize"
                }
            }
        }
    ]

    print("=" * 75)
    print(
        "        RAZORPAY AI COMMERCE AGENT"
    )
    print(
        "             INTENT NORMALIZER V5"
    )
    print("=" * 75)

    for i, intent in enumerate(
        test_intents,
        start=1
    ):

        print(f"\n\nTEST {i}")
        print("-" * 75)

        result = normalizer.normalize(intent)

        print(
            json.dumps(
                result,
                indent=2
            )
        )

    print("\n" + "=" * 75)
    print(
        "Intent normalization V5 completed!"
    )
    print("=" * 75)