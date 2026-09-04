"""
RazorGuard AI - Offer Source Registry

Central registry for legitimate commerce offer sources.

Responsibilities:
    - register offer sources
    - remove sources
    - retrieve sources
    - list available sources
    - safely query multiple sources
    - combine source responses

This module does NOT:
    - scrape websites
    - invent prices
    - invent URLs
    - mark offers as verified
    - bypass merchant/API restrictions

Source-specific validation remains inside the source and
offer-eligibility layers.
"""

from datetime import datetime, timezone

from offer_sources.source_base import OfferSource


class OfferSourceRegistry:
    """
    Registry containing the offer sources used by RazorGuard AI.
    """

    def __init__(self):
        self._sources = {}

    # =========================================================
    # REGISTER SOURCE
    # =========================================================

    def register(
        self,
        source,
        replace=False,
    ):
        """
        Register an OfferSource instance.

        Parameters:
            source:
                Instance of OfferSource.

            replace:
                If True, replace an existing source with the
                same source_id.
        """

        if not isinstance(
            source,
            OfferSource,
        ):

            raise TypeError(
                "source must be an OfferSource instance"
            )

        source_id = str(
            source.source_id
        ).strip()

        if not source_id:

            raise ValueError(
                "source_id cannot be empty"
            )

        if (
            source_id in self._sources
            and not replace
        ):

            raise ValueError(
                f"Source already registered: {source_id}"
            )

        self._sources[
            source_id
        ] = source

        return source

    # =========================================================
    # UNREGISTER SOURCE
    # =========================================================

    def unregister(
        self,
        source_id,
    ):
        """
        Remove a source from the registry.

        Returns:
            True if removed.
            False if the source was not registered.
        """

        source_id = str(
            source_id
        ).strip()

        if source_id in self._sources:

            del self._sources[
                source_id
            ]

            return True

        return False

    # =========================================================
    # GET SOURCE
    # =========================================================

    def get(
        self,
        source_id,
    ):
        """
        Return a registered source.

        Returns:
            OfferSource instance or None.
        """

        source_id = str(
            source_id
        ).strip()

        return self._sources.get(
            source_id
        )

    # =========================================================
    # HAS SOURCE
    # =========================================================

    def has(
        self,
        source_id,
    ):
        """
        Check whether a source is registered.
        """

        source_id = str(
            source_id
        ).strip()

        return (
            source_id
            in self._sources
        )

    # =========================================================
    # LIST SOURCES
    # =========================================================

    def list_sources(
        self,
        available_only=False,
    ):
        """
        Return registered sources.

        Parameters:
            available_only:
                If True, return only sources that are currently
                available.
        """

        sources = []

        for source in self._sources.values():

            if (
                available_only
                and not source.is_available()
            ):

                continue

            sources.append(
                source
            )

        return sources

    # =========================================================
    # SOURCE METADATA
    # =========================================================

    def get_source_metadata(self):
        """
        Return metadata for all registered sources.
        """

        metadata = []

        for source in self._sources.values():

            try:

                metadata.append(
                    source.get_metadata()
                )

            except Exception as exc:

                metadata.append(
                    {
                        "source_id":
                            getattr(
                                source,
                                "source_id",
                                "unknown",
                            ),

                        "source_name":
                            getattr(
                                source,
                                "source_name",
                                "unknown",
                            ),

                        "available":
                            False,

                        "error":
                            str(exc),
                    }
                )

        return metadata

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def health_check(self):
        """
        Run a health check for every registered source.
        """

        checked_at = datetime.now(
            timezone.utc
        ).isoformat()

        results = []

        for source in self._sources.values():

            try:

                result = source.health_check()

            except Exception as exc:

                result = {
                    "source_id":
                        getattr(
                            source,
                            "source_id",
                            "unknown",
                        ),

                    "source_name":
                        getattr(
                            source,
                            "source_name",
                            "unknown",
                        ),

                    "available":
                        False,

                    "healthy":
                        False,

                    "checked_at":
                        checked_at,

                    "error":
                        str(exc),
                }

            results.append(
                result
            )

        return {
            "checked_at": checked_at,
            "source_count": len(
                self._sources
            ),
            "sources": results,
        }

    # =========================================================
    # FETCH FROM ONE SOURCE
    # =========================================================

    def fetch_from_source(
        self,
        source_id,
        product_id,
        context=None,
    ):
        """
        Safely fetch offers from one registered source.
        """

        source = self.get(
            source_id
        )

        if source is None:

            return {
                "success": False,
                "source_id":
                    str(source_id),
                "source_name": None,
                "offers": [],
                "error":
                    "source is not registered",
            }

        return source.safe_fetch_offers(
            product_id,
            context=context,
        )

    # =========================================================
    # FETCH FROM ALL SOURCES
    # =========================================================

    def fetch_all(
        self,
        product_id,
        context=None,
        available_only=True,
    ):
        """
        Fetch offers from all registered sources.

        A failing source does NOT stop the remaining sources.

        Returns:

            {
                "success": True/False,
                "product_id": "...",
                "sources_checked": ...,
                "successful_sources": ...,
                "failed_sources": ...,
                "offers": [...],
                "source_results": [...]
            }
        """

        source_results = []

        combined_offers = []

        successful_sources = 0
        failed_sources = 0

        sources = self.list_sources(
            available_only=available_only
        )

        for source in sources:

            result = source.safe_fetch_offers(
                product_id,
                context=context,
            )

            source_results.append(
                result
            )

            if result.get(
                "success"
            ):

                successful_sources += 1

                offers = result.get(
                    "offers",
                    [],
                )

                if isinstance(
                    offers,
                    list,
                ):

                    combined_offers.extend(
                        offers
                    )

            else:

                failed_sources += 1

        return {
            "success":
                failed_sources == 0,

            "product_id":
                str(product_id),

            "sources_checked":
                len(sources),

            "successful_sources":
                successful_sources,

            "failed_sources":
                failed_sources,

            "offers":
                combined_offers,

            "source_results":
                source_results,
        }

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):
        """
        Remove all registered sources.
        """

        self._sources.clear()

    # =========================================================
    # COUNT
    # =========================================================

    def count(self):
        """
        Return the number of registered sources.
        """

        return len(
            self._sources
        )


# =============================================================
# DEFAULT REGISTRY
# =============================================================

default_registry = OfferSourceRegistry()


__all__ = [
    "OfferSourceRegistry",
    "default_registry",
]