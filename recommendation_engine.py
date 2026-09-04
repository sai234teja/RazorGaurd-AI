import pandas as pd


CATALOG_PATH = "catalog/products.csv"


# ============================================================
# LOAD CATALOG
# ============================================================

products = pd.read_csv(
    CATALOG_PATH
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _to_bool(value):

    if isinstance(value, bool):
        return value

    if value is None:
        return False

    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass

    return str(value).strip().lower() in {
        "yes",
        "true",
        "1",
        "y",
        "on",
        "available"
    }


def _number(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):

        pass

    try:

        text = str(value).lower().strip()

        text = (
            text
            .replace("gb", "")
            .replace("mp", "")
            .replace("hours", "")
            .replace("hour", "")
            .strip()
        )

        return float(text)

    except (
        TypeError,
        ValueError
    ):

        return None


def _preference_data(
    preferences,
    name
):

    value = preferences.get(
        name
    )

    if isinstance(
        value,
        dict
    ):

        return value

    return {
        "value": value,
        "importance": "medium",
        "direction": "match"
    }


# ============================================================
# CALCULATE MATCH SCORE
# ============================================================

def calculate_match_score(
    product,
    intent
):

    score = 0.0

    preferences = intent.get(
        "preferences",
        {}
    )

    if not isinstance(
        preferences,
        dict
    ):

        preferences = {}

    # ========================================================
    # 1. BUDGET FIT — 25 POINTS
    # ========================================================

    max_price = intent.get(
        "max_price"
    )

    min_price = intent.get(
        "min_price"
    )

    price = _number(
        product.get("price")
    )

    if price is not None:

        if max_price is not None:

            if price <= float(
                max_price
            ):

                score += 25

            else:

                score -= 20

        if min_price is not None:

            if price >= float(
                min_price
            ):

                score += 5

    # ========================================================
    # 2. USE CASE FIT — 20 POINTS
    # ========================================================

    use_cases = intent.get(
        "use_cases",
        []
    )

    if isinstance(
        use_cases,
        str
    ):

        use_cases = [
            use_cases
        ]

    product_use_case = str(
        product.get(
            "use_case",
            ""
        )
    ).lower()

    if use_cases:

        matches = 0

        for use_case in use_cases:

            if str(
                use_case
            ).lower() in product_use_case:

                matches += 1

        if matches:

            score += min(
                20,
                matches * 10
            )

    # ========================================================
    # 3. RATING — 15 POINTS
    # ========================================================

    rating = _number(
        product.get(
            "rating"
        )
    )

    if rating is not None:

        score += (
            rating / 5
        ) * 15

    # ========================================================
    # 4. STOCK — 10 POINTS
    # ========================================================

    stock = _number(
        product.get(
            "stock"
        )
    )

    if stock and stock > 0:

        score += 10

    # ========================================================
    # 5. BATTERY — UP TO 15 POINTS
    # ========================================================

    battery_pref = _preference_data(
        preferences,
        "battery_hours"
    )

    battery = _number(
        product.get(
            "battery_hours"
        )
    )

    battery_direction = str(
        battery_pref.get(
            "direction",
            ""
        )
    ).lower()

    battery_importance = str(
        battery_pref.get(
            "importance",
            "medium"
        )
    ).lower()

    if (
        battery is not None
        and battery_direction == "maximize"
    ):

        if battery >= 40:

            battery_score = 15

        elif battery >= 30:

            battery_score = 12

        elif battery >= 20:

            battery_score = 8

        else:

            battery_score = 3

        if battery_importance == "critical":

            battery_score = min(
                18,
                battery_score + 3
            )

        score += battery_score

    # ========================================================
    # 6. WIRELESS — UP TO 10 POINTS
    # ========================================================

    wireless_pref = _preference_data(
        preferences,
        "wireless"
    )

    if (
        wireless_pref.get(
            "value"
        ) is True
        and wireless_pref.get(
            "direction"
        ) == "match"
    ):

        if _to_bool(
            product.get(
                "wireless"
            )
        ):

            score += 10

        else:

            # Try catalog text as fallback.
            text = " ".join([
                str(
                    product.get(
                        "name",
                        ""
                    )
                ),
                str(
                    product.get(
                        "category",
                        ""
                    )
                ),
                str(
                    product.get(
                        "description",
                        ""
                    )
                )
            ]).lower()

            if (
                "wireless" in text
                or "bluetooth" in text
            ):

                score += 10

    # ========================================================
    # 7. NOISE CANCELLATION — UP TO 5 POINTS
    # ========================================================

    noise_pref = _preference_data(
        preferences,
        "noise_cancellation"
    )

    if (
        noise_pref.get(
            "value"
        ) is True
    ):

        if _to_bool(
            product.get(
                "noise_cancellation"
            )
        ):

            score += 5

    # ========================================================
    # 8. GPS — UP TO 5 POINTS
    # ========================================================

    gps_pref = _preference_data(
        preferences,
        "gps"
    )

    if (
        gps_pref.get(
            "value"
        ) is True
    ):

        if _to_bool(
            product.get(
                "gps"
            )
        ):

            score += 5

    # ========================================================
    # 9. 5G — UP TO 5 POINTS
    # ========================================================

    five_g_pref = _preference_data(
        preferences,
        "5g"
    )

    if (
        five_g_pref.get(
            "value"
        ) is True
    ):

        if _to_bool(
            product.get(
                "5g"
            )
        ):

            score += 5

    # ========================================================
    # FINAL SCORE
    # ========================================================

    return round(
        max(
            0,
            min(
                score,
                100
            )
        ),
        2
    )


# ============================================================
# RECOMMEND PRODUCTS
# ============================================================

def recommend_products(
    intent,
    candidates=None,
    top_n=3
):

    # --------------------------------------------------------
    # Use candidates from ProductSearch when supplied.
    # Otherwise use complete catalog.
    # --------------------------------------------------------

    if candidates is None:

        results = products.copy()

    else:

        results = candidates.copy()

    if results.empty:

        return results

    # ========================================================
    # HARD PRICE FILTER
    # ========================================================

    max_price = intent.get(
        "max_price"
    )

    min_price = intent.get(
        "min_price"
    )

    if max_price is not None:

        results = results[
            results["price"]
            <= float(max_price)
        ]

    if min_price is not None:

        results = results[
            results["price"]
            >= float(min_price)
        ]

    # ========================================================
    # REMOVE OUT-OF-STOCK PRODUCTS
    # ========================================================

    results = results[
        results["stock"] > 0
    ]

    if results.empty:

        return results

    # ========================================================
    # CALCULATE MATCH SCORE
    # ========================================================

    results[
        "match_score"
    ] = results.apply(

        lambda product:

        calculate_match_score(
            product,
            intent
        ),

        axis=1
    )

    # ========================================================
    # SORT
    # ========================================================

    results = results.sort_values(

        by=[
            "match_score",
            "rating"
        ],

        ascending=[
            False,
            False
        ]
    )

    return results.head(
        top_n
    ).reset_index(
        drop=True
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "       RAZORPAY AI COMMERCE AGENT"
    )

    print(
        "             RECOMMENDATION ENGINE"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # Test using the NEW AI intent format
    # --------------------------------------------------------

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

                "importance": "critical",

                "direction": "match"
            }

        }
    }

    print(
        "\nBuyer Intent"
    )

    print(
        "-" * 70
    )

    print(
        "Budget: ₹3,000"
    )

    print(
        "Use cases: Travel + Online Classes"
    )

    print(
        "Priority: Long battery"
    )

    print(
        "Requirement: Wireless"
    )

    # --------------------------------------------------------
    # Search candidates
    # --------------------------------------------------------

    candidates = products.copy()

    candidates = candidates[
        candidates["category"]
        .astype(str)
        .str.lower()
        .str.contains(
            "wireless headphones",
            na=False
        )
    ]

    # --------------------------------------------------------
    # Recommend
    # --------------------------------------------------------

    recommendations = recommend_products(

        test_intent,

        candidates=candidates,

        top_n=3
    )

    print(
        "\nTop Recommendations"
    )

    print(
        "-" * 70
    )

    if recommendations.empty:

        print(
            "No suitable products found."
        )

    else:

        for rank, (
            _,
            product
        ) in enumerate(

            recommendations.iterrows(),

            start=1
        ):

            print(
                f"\n#{rank} "
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
                f"Battery: "
                f"{product['battery_hours']} "
                f"hours"
            )

            print(
                f"Wireless: "
                f"{product.get('wireless', 'derived')}"
            )

            print(
                f"Match Score: "
                f"{product['match_score']}%"
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "Recommendation engine completed!"
    )

    print(
        "=" * 70
    )