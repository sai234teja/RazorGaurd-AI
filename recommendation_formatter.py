import pandas as pd


class RecommendationFormatter:

    @staticmethod
    def format_results(
        results,
        intent
    ):

        if results is None or results.empty:

            return {
                "message": (
                    "Sorry, I couldn't find "
                    "matching products."
                ),
                "products": []
            }

        products = []

        for _, product in results.iterrows():

            item = {

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

                "category": str(
                    product.get(
                        "category",
                        ""
                    )
                ),

                "subcategory": str(
                    product.get(
                        "subcategory",
                        ""
                    )
                ),

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

                "match_score": float(
                    product.get(
                        "match_score",
                        0
                    )
                )
            }

            products.append(
                item
            )

        category = intent.get(
            "subcategory"
        ) or intent.get(
            "category"
        )

        max_price = intent.get(
            "max_price"
        )

        if max_price is not None:

            message = (
                f"I found {len(products)} "
                f"{category} products under "
                f"₹{max_price:,.0f}."
            )

        else:

            message = (
                f"I found {len(products)} "
                f"{category} products "
                "for you."
            )

        return {

            "message": message,

            "products": products
        }


if __name__ == "__main__":

    from shopping_pipeline import ShoppingPipeline

    pipeline = ShoppingPipeline()

    result = pipeline.process(
        "I need wireless headphones under 2500",
        top_n=3
    )

    formatted = RecommendationFormatter.format_results(
        result["results"],
        result["intent"]
    )

    print("\n")
    print("=" * 75)
    print("             RECOMMENDATION RESPONSE")
    print("=" * 75)

    print("\nMESSAGE")
    print("-" * 75)
    print(
        formatted["message"]
    )

    print("\nPRODUCTS")
    print("-" * 75)

    for index, product in enumerate(
        formatted["products"],
        start=1
    ):

        print(
            f"\n#{index} "
            f"{product['name']}"
        )

        print(
            f"₹{product['price']:,.0f} "
            f"| ⭐ {product['rating']}"
        )

        print(
            f"Match: "
            f"{product['match_score']}%"
        )

        print(
            f"Stock: "
            f"{product['stock']}"
        )

    print("\n")
    print("=" * 75)