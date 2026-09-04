import json

from gemini_intent import GeminiIntentParser
from catalog_engine import CatalogEngine
from universal_ranker import UniversalRanker


class ShoppingPipeline:

    def __init__(self):

        self.parser = GeminiIntentParser()

        self.catalog = CatalogEngine()

        self.ranker = UniversalRanker()

    def process(self, user_message, top_n=3):

        # ----------------------------------------------
        # 1. Understand user request
        # ----------------------------------------------

        intent = self.parser.parse(
            user_message
        )

        # ----------------------------------------------
        # 2. Search catalog
        # ----------------------------------------------

        candidates = self.catalog.search(

            query=None,

            category=intent.get(
                "category"
            ),

            subcategory=intent.get(
                "subcategory"
            ),

            max_price=intent.get(
                "max_price"
            ),

            min_price=intent.get(
                "min_price"
            )
        )

        # ----------------------------------------------
        # 3. Rank candidates
        # ----------------------------------------------

        ranked = self.ranker.rank(

            candidates,

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

            preferences=intent.get(
                "preferences",
                {}
            ),

            top_n=top_n
        )

        # ----------------------------------------------
        # 4. Return complete pipeline result
        # ----------------------------------------------

        return {

            "query": user_message,

            "intent": intent,

            "candidate_count": len(
                candidates
            ),

            "results": ranked

        }


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    pipeline = ShoppingPipeline()

    user_request = (
        "I need wireless headphones under 2500"
    )

    result = pipeline.process(
        user_request,
        top_n=3
    )

    print("\n")
    print("=" * 75)
    print("              RAZORGUARD AI")
    print("             SHOPPING PIPELINE")
    print("=" * 75)

    print("\nUSER REQUEST")
    print("-" * 75)
    print(user_request)

    print("\nINTENT")
    print("-" * 75)

    print(
        json.dumps(
            result["intent"],
            indent=2
        )
    )

    print("\nCANDIDATES FOUND")
    print("-" * 75)

    print(
        result["candidate_count"]
    )

    print("\nTOP RECOMMENDATIONS")
    print("-" * 75)

    if result["results"].empty:

        print(
            "No matching products found."
        )

    else:

        display_columns = [

            "product_id",
            "name",
            "category",
            "subcategory",
            "price",
            "rating",
            "stock",
            "match_score"
        ]

        available_columns = [

            column

            for column in display_columns

            if column in result["results"].columns
        ]

        print(
            result["results"][
                available_columns
            ].to_string(
                index=False
            )
        )

    print("\n")
    print("=" * 75)
    print("Pipeline completed!")
    print("=" * 75)