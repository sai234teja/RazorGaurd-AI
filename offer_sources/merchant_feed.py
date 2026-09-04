"""
RazorGuard AI - Merchant Feed Ingestion

This module accepts legitimate merchant/feed data and
stores normalized offers in the existing product_offers table.

IMPORTANT:
- This module does NOT scrape websites.
- This module does NOT invent prices.
- This module does NOT invent product URLs.
- Demo offers remain separate from real/merchant-feed offers.
"""

from database.database import (
    get_connection,
    add_product_offer,
)

from offer_sources.offer_normalizer import (
    normalize_offers,
    current_utc_timestamp,
)

from offer_sources.source_base import OfferSource


# ============================================================
# MERCHANT FEED INGESTOR
# ============================================================

class MerchantFeedIngestor(OfferSource):
    """
    Ingest offers supplied by a merchant/feed source.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path

    @property
    def source_id(self):
        """Stable identifier used by OfferSourceRegistry."""
        return "merchant_feed"

    @property
    def source_name(self):
        """Human-readable source name."""
        return "Merchant Feed"

    def is_available(self):
        """
        Merchant-feed source is available when the ingestor can
        operate. It does not claim that an external merchant API
        is live; this source only accepts supplied feed data.
        """
        return True

    def fetch_offers(self, product_id, context=None):
        """
        Fetch already-ingested merchant-feed offers for a product.

        This method intentionally reads from our database rather
        than scraping an external website or inventing prices.
        """
        conn = (
            get_connection(self.db_path)
            if self.db_path
            else get_connection()
        )

        try:
            rows = conn.execute(
                """
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
                  AND source_type = 'merchant_feed'
                ORDER BY
                    (price + shipping_fee) ASC,
                    price ASC
                """,
                (str(product_id),),
            ).fetchall()

            offers = []

            for row in rows:
                offer = dict(row)

                offer["total_price"] = round(
                    float(offer.get("price") or 0)
                    + float(offer.get("shipping_fee") or 0),
                    2,
                )

                offers.append(offer)

            return offers

        finally:
            conn.close()

    # ========================================================
    # PRODUCT CHECK
    # ========================================================

    def product_exists(self, product_id):
        """
        Check whether the product exists in our catalog.
        """

        conn = get_connection(
            self.db_path
        ) if self.db_path else get_connection()

        try:

            row = conn.execute(
                """
                SELECT 1
                FROM products
                WHERE product_id = ?
                LIMIT 1
                """,
                (
                    str(product_id),
                ),
            ).fetchone()

            return row is not None

        finally:

            conn.close()

    # ========================================================
    # INGEST ONE OFFER
    # ========================================================

    def ingest_offer(
        self,
        raw_offer,
        source_type="merchant_feed",
    ):
        """
        Normalize, validate and store one offer.

        Returns:

            {
                "success": True,
                "offer_id": ...,
                "offer": {...}
            }
        """

        result = normalize_offers(
            [raw_offer],
            source_type=source_type,
        )

        offers = result["offers"]
        rejected = result["rejected"]

        if not offers:

            reason = (
                rejected[0]["reason"]
                if rejected
                else "Unknown validation error"
            )

            return {
                "success": False,
                "offer_id": None,
                "offer": None,
                "error": reason,
            }

        offer = offers[0]

        product_id = offer["product_id"]

        # ----------------------------------------------------
        # Product must already exist.
        # ----------------------------------------------------

        if not self.product_exists(
            product_id
        ):

            return {
                "success": False,
                "offer_id": None,
                "offer": offer,
                "error":
                    f"Product not found: {product_id}",
            }

        # ----------------------------------------------------
        # Store offer.
        # ----------------------------------------------------

        try:

            offer_id = add_product_offer(
                product_id=offer["product_id"],
                merchant_id=offer["merchant_id"],
                merchant_name=offer["merchant_name"],
                price=offer["price"],
                currency=offer["currency"],
                product_url=offer["product_url"],
                availability=offer["availability"],
                shipping_fee=offer["shipping_fee"],
                delivery_days=offer["delivery_days"],
                is_verified=offer["is_verified"],
                source_type=offer["source_type"],
                db_path=self.db_path
                if self.db_path
                else None,
            )

        except TypeError:

            # Existing database helper may use the
            # default DB path when db_path is omitted.
            offer_id = add_product_offer(
                product_id=offer["product_id"],
                merchant_id=offer["merchant_id"],
                merchant_name=offer["merchant_name"],
                price=offer["price"],
                currency=offer["currency"],
                product_url=offer["product_url"],
                availability=offer["availability"],
                shipping_fee=offer["shipping_fee"],
                delivery_days=offer["delivery_days"],
                is_verified=offer["is_verified"],
                source_type=offer["source_type"],
            )

        return {
            "success": True,
            "offer_id": offer_id,
            "offer": offer,
            "checked_at":
                current_utc_timestamp(),
        }

    # ========================================================
    # INGEST MANY OFFERS
    # ========================================================

    def ingest_offers(
        self,
        raw_offers,
        source_type="merchant_feed",
    ):
        """
        Normalize, validate and store multiple offers.

        Invalid offers are rejected individually.

        Returns a detailed ingestion report.
        """

        normalized_result = normalize_offers(
            raw_offers,
            source_type=source_type,
        )

        offers = normalized_result[
            "offers"
        ]

        rejected = normalized_result[
            "rejected"
        ]

        inserted = []
        failed = []

        for offer in offers:

            product_id = offer[
                "product_id"
            ]

            # ----------------------------------------------
            # Product validation
            # ----------------------------------------------

            if not self.product_exists(
                product_id
            ):

                failed.append(
                    {
                        "offer": offer,
                        "reason":
                            f"Product not found: {product_id}",
                    }
                )

                continue

            # ----------------------------------------------
            # Database insertion
            # ----------------------------------------------

            try:

                try:

                    offer_id = add_product_offer(
                        product_id=offer[
                            "product_id"
                        ],
                        merchant_id=offer[
                            "merchant_id"
                        ],
                        merchant_name=offer[
                            "merchant_name"
                        ],
                        price=offer[
                            "price"
                        ],
                        currency=offer[
                            "currency"
                        ],
                        product_url=offer[
                            "product_url"
                        ],
                        availability=offer[
                            "availability"
                        ],
                        shipping_fee=offer[
                            "shipping_fee"
                        ],
                        delivery_days=offer[
                            "delivery_days"
                        ],
                        is_verified=offer[
                            "is_verified"
                        ],
                        source_type=offer[
                            "source_type"
                        ],
                        db_path=self.db_path
                        if self.db_path
                        else None,
                    )

                except TypeError:

                    offer_id = add_product_offer(
                        product_id=offer[
                            "product_id"
                        ],
                        merchant_id=offer[
                            "merchant_id"
                        ],
                        merchant_name=offer[
                            "merchant_name"
                        ],
                        price=offer[
                            "price"
                        ],
                        currency=offer[
                            "currency"
                        ],
                        product_url=offer[
                            "product_url"
                        ],
                        availability=offer[
                            "availability"
                        ],
                        shipping_fee=offer[
                            "shipping_fee"
                        ],
                        delivery_days=offer[
                            "delivery_days"
                        ],
                        is_verified=offer[
                            "is_verified"
                        ],
                        source_type=offer[
                            "source_type"
                        ],
                    )

                inserted.append(
                    {
                        "offer_id":
                            offer_id,
                        "offer":
                            offer,
                    }
                )

            except Exception as exc:

                failed.append(
                    {
                        "offer": offer,
                        "reason":
                            str(exc),
                    }
                )

        return {
            "success":
                len(failed) == 0
                and len(rejected) == 0,

            "received":
                len(raw_offers)
                if isinstance(
                    raw_offers,
                    list,
                )
                else 0,

            "normalized":
                len(offers),

            "inserted":
                len(inserted),

            "rejected":
                len(rejected),

            "failed":
                len(failed),

            "inserted_offers":
                inserted,

            "rejected_offers":
                rejected,

            "failed_offers":
                failed,

            "checked_at":
                current_utc_timestamp(),
        }


# ============================================================
# SIMPLE HELPER
# ============================================================

def ingest_merchant_offers(
    offers,
    source_type="merchant_feed",
):
    """
    Convenience function for application code.
    """

    ingestor = MerchantFeedIngestor()

    return ingestor.ingest_offers(
        offers,
        source_type=source_type,
    )