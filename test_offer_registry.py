from offer_sources.merchant_feed import MerchantFeedIngestor
from offer_sources.source_registry import OfferSourceRegistry


def main():
    print("=" * 60)
    print("RAZORGUARD AI - OFFER SOURCE REGISTRY TEST")
    print("=" * 60)

    # --------------------------------------------------
    # CREATE REGISTRY
    # --------------------------------------------------

    registry = OfferSourceRegistry()

    # --------------------------------------------------
    # CREATE MERCHANT FEED SOURCE
    # --------------------------------------------------

    merchant_feed = MerchantFeedIngestor()

    # --------------------------------------------------
    # REGISTER SOURCE
    # --------------------------------------------------

    registry.register(
        merchant_feed
    )

    print()
    print("REGISTERED SOURCES:", registry.count())

    # --------------------------------------------------
    # SOURCE METADATA
    # --------------------------------------------------

    print()
    print("SOURCE METADATA:")

    for source in registry.get_source_metadata():
        print(source)

    # --------------------------------------------------
    # HEALTH CHECK
    # --------------------------------------------------

    print()
    print("HEALTH CHECK:")

    health = registry.health_check()

    print(health)

    # --------------------------------------------------
    # FETCH OFFERS
    # --------------------------------------------------

    print()
    print("FETCHING P001 OFFERS:")

    result = registry.fetch_from_source(
        "merchant_feed",
        "P001",
    )

    print("SUCCESS:", result["success"])
    print("SOURCE:", result["source_name"])
    print("OFFER COUNT:", len(result["offers"]))

    for offer in result["offers"]:
        print(
            offer["merchant_name"],
            "| ₹",
            offer["price"],
            "|",
            offer["product_url"],
        )

    # --------------------------------------------------
    # FETCH ALL SOURCES
    # --------------------------------------------------

    print()
    print("FETCH ALL SOURCES:")

    all_result = registry.fetch_all(
        "P001"
    )

    print(
        "SOURCES CHECKED:",
        all_result["sources_checked"],
    )

    print(
        "SUCCESSFUL SOURCES:",
        all_result["successful_sources"],
    )

    print(
        "FAILED SOURCES:",
        all_result["failed_sources"],
    )

    print(
        "TOTAL OFFERS:",
        len(all_result["offers"]),
    )

    print()
    print("=" * 60)
    print("REGISTRY TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()