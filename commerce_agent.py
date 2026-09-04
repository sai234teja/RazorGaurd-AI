import os
import json

from google import genai
from pydantic import BaseModel

from product_search import search_products
from recommendation_engine import recommend_products


# --------------------------------------------------
# Gemini client
# --------------------------------------------------

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


# --------------------------------------------------
# Structured request schema
# --------------------------------------------------

class ShoppingRequest(BaseModel):
    category: str | None = None
    max_price: float | None = None
    use_cases: list[str] = []
    long_battery: bool = False
    noise_cancellation: bool = False


# --------------------------------------------------
# Gemini natural-language understanding
# --------------------------------------------------

def understand_request(user_message):

    prompt = f"""
You are the natural-language understanding layer
of a shopping agent.

Convert the user's message into structured shopping
preferences.

IMPORTANT RULES:

1. Understand spelling mistakes.
2. Understand grammar mistakes.
3. Understand abbreviations.
4. Understand informal language.
5. Understand Indian price expressions such as:
   2k, 3k, 2.5k, ₹3000, 3 thousand.
6. Infer the intended product category when reasonable.
7. Do NOT invent requirements that the user did not express.
8. If the user does not provide a budget, return null.
9. If the user does not mention a use case, return [].
10. "hp", "headphone", "headphones" can refer to headphones
    when the context clearly indicates that.
11. "battery should be long", "good battery", "long battery"
    means long_battery=true.
12. "ANC", "noise cancelling", "noise cancellation"
    means noise_cancellation=true.

USER MESSAGE:

{user_message}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ShoppingRequest,
        },
    )

    return ShoppingRequest.model_validate_json(
        response.text
    )


# --------------------------------------------------
# Recommendation explanation
# --------------------------------------------------

def explain_recommendation(product, request):

    reasons = []

    if request.max_price is not None:
        if product["price"] <= request.max_price:
            reasons.append(
                f"fits your ₹{int(request.max_price):,} budget"
            )

    if request.long_battery:
        reasons.append(
            f"has a {int(product['battery_hours'])}-hour battery"
        )

    if request.noise_cancellation:
        if str(product["noise_cancellation"]).lower() == "yes":
            reasons.append(
                "has noise cancellation"
            )

    if request.use_cases:
        product_use_cases = str(
            product["use_case"]
        ).lower()

        matched = [
            use_case
            for use_case in request.use_cases
            if use_case.lower() in product_use_cases
        ]

        if matched:
            reasons.append(
                "matches your " +
                " and ".join(matched) +
                " needs"
            )

    reasons.append(
        f"has a {product['rating']}/5 rating"
    )

    return reasons


# --------------------------------------------------
# Main agent
# --------------------------------------------------

def run_agent(user_message):

    print("\n" + "=" * 70)
    print("              RAZORPAY AI COMMERCE AGENT")
    print("=" * 70)

    print("\nUser:")
    print(user_message)

    # -----------------------------------------
    # Step 1: Gemini understands the message
    # -----------------------------------------

    request = understand_request(user_message)

    print("\n🧠 Gemini Understanding")
    print("-" * 70)

    print(
        json.dumps(
            request.model_dump(),
            indent=2
        )
    )

    # -----------------------------------------
    # Step 2: Search real catalog
    # -----------------------------------------

    search_results = search_products(
        category=request.category,
        max_price=request.max_price
    )

    print("\n🔎 Catalog Search")
    print("-" * 70)

    print(
        f"Found {len(search_results)} "
        f"candidate products."
    )

    # -----------------------------------------
    # Step 3: Rank products
    # -----------------------------------------

    preferences = request.model_dump()

    recommendations = recommend_products(
        preferences,
        top_n=3
    )

    print("\n🏆 Recommendations")
    print("-" * 70)

    if recommendations.empty:

        print(
            "Sorry, I couldn't find a suitable "
            "product matching your requirements."
        )

        return

    for rank, (_, product) in enumerate(
        recommendations.iterrows(),
        start=1
    ):

        print(
            f"\n#{rank} {product['name']}"
        )

        print(
            f"Price: ₹{product['price']}"
        )

        print(
            f"Rating: {product['rating']}"
        )

        print(
            f"Battery: "
            f"{product['battery_hours']} hours"
        )

        print(
            f"Noise Cancellation: "
            f"{product['noise_cancellation']}"
        )

        print(
            f"Match Score: "
            f"{product['match_score']}%"
        )

        reasons = explain_recommendation(
            product,
            request
        )

        print("Why it matches:")

        for reason in reasons:
            print(f"  ✓ {reason}")


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    test_messages = [

        "bro i wnt a gud wireless hp under 3k "
        "for travl n online cls battery shud be long",

        "need a good headphone around 2.5k "
        "for travelling",

        "which headphone is best for gaming under 3k"
    ]

    for message in test_messages:

        try:

            run_agent(message)

        except Exception as error:

            print("\n❌ Agent error:")
            print(error)