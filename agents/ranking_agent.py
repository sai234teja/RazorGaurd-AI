"""Ranking agent placeholder."""


def rank_products(products):
    """Rank a list of products."""
    return sorted(products, key=lambda item: item.get("score", 0), reverse=True)
