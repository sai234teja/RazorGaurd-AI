"""Seed the SQLite merchant catalog with verified real-world product data."""

import os

from catalog.seed_real_products import get_real_seed_products
from services.catalog_service import CatalogService


def import_seed_products(db_path=None):
    """Load real product data into SQLite without duplicating product IDs."""
    service = CatalogService(db_path or os.path.join("database", "commerce.db"))
    products = get_real_seed_products()

    for product in products:
        service.add_product(product)

    return service.count_products()


if __name__ == "__main__":
    count = import_seed_products()
    print(f"Imported {count} real catalog products to SQLite.")
