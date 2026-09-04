"""
RazorGuard AI - Offer Source Base

Defines the common interface that every legitimate offer source
must follow.

A source can represent:
    - merchant-provided feeds
    - authorized APIs
    - approved commerce integrations
    - other legitimate structured sources

This module deliberately does NOT:
    - scrape websites
    - invent prices
    - invent product URLs
    - claim that a source is live
    - bypass merchant restrictions
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone


class OfferSource(ABC):
    """
    Base interface for a legitimate commerce offer source.

    Every concrete source should:
        1. identify itself
        2. accept a product/request
        3. return raw offers
        4. avoid inventing unavailable information
    """

    # ---------------------------------------------------------
    # SOURCE IDENTITY
    # ---------------------------------------------------------

    @property
    @abstractmethod
    def source_id(self):
        """
        Return a stable identifier for the source.

        Example:
            "merchant_feed"
            "official_api"
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def source_name(self):
        """
        Return a human-readable source name.
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # AVAILABILITY
    # ---------------------------------------------------------

    def is_available(self):
        """
        Return whether the source is currently configured
        and available.

        Sources that do not require external credentials can
        simply return True.

        Concrete integrations can override this method.
        """
        return True

    # ---------------------------------------------------------
    # OFFER FETCHING
    # ---------------------------------------------------------

    @abstractmethod
    def fetch_offers(
        self,
        product_id,
        context=None,
    ):
        """
        Fetch offers for a product.

        Parameters:
            product_id:
                Product identifier from our internal catalog.

            context:
                Optional dictionary containing additional request
                information such as:
                    - category
                    - budget
                    - user preferences
                    - location
                    - quantity

        Returns:
            list[dict]

        The returned offers must contain enough information for
        the normalizer and eligibility layer to validate them.

        A source must never fabricate missing price, URL,
        availability, or merchant information.
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # SOURCE METADATA
    # ---------------------------------------------------------

    def get_metadata(self):
        """
        Return source metadata useful for logging and debugging.
        """

        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "available": bool(
                self.is_available()
            ),
        }

    # ---------------------------------------------------------
    # HEALTH CHECK
    # ---------------------------------------------------------

    def health_check(self):
        """
        Return a standard health-check response.

        This makes source monitoring consistent across
        integrations.
        """

        checked_at = datetime.now(
            timezone.utc
        ).isoformat()

        try:

            available = bool(
                self.is_available()
            )

            return {
                "source_id": self.source_id,
                "source_name": self.source_name,
                "available": available,
                "healthy": available,
                "checked_at": checked_at,
                "error": None,
            }

        except Exception as exc:

            return {
                "source_id": self.source_id,
                "source_name": self.source_name,
                "available": False,
                "healthy": False,
                "checked_at": checked_at,
                "error": str(exc),
            }

    # ---------------------------------------------------------
    # SAFE FETCH WRAPPER
    # ---------------------------------------------------------

    def safe_fetch_offers(
        self,
        product_id,
        context=None,
    ):
        """
        Safely fetch offers from the source.

        This wrapper prevents a failing external source from
        breaking the entire recommendation pipeline.

        Returns:

            {
                "success": True/False,
                "source_id": "...",
                "source_name": "...",
                "offers": [...],
                "error": None
            }
        """

        if not product_id:

            return {
                "success": False,
                "source_id": self.source_id,
                "source_name": self.source_name,
                "offers": [],
                "error": "product_id is required",
            }

        try:

            if not self.is_available():

                return {
                    "success": False,
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "offers": [],
                    "error": "source is unavailable",
                }

            offers = self.fetch_offers(
                product_id,
                context=context,
            )

            if offers is None:

                offers = []

            if not isinstance(
                offers,
                list,
            ):

                return {
                    "success": False,
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "offers": [],
                    "error": (
                        "source returned an invalid "
                        "offer collection"
                    ),
                }

            return {
                "success": True,
                "source_id": self.source_id,
                "source_name": self.source_name,
                "offers": offers,
                "error": None,
            }

        except Exception as exc:

            return {
                "success": False,
                "source_id": self.source_id,
                "source_name": self.source_name,
                "offers": [],
                "error": str(exc),
            }


__all__ = [
    "OfferSource",
]