"""Migrate the merchant CSV catalog into the SQLite database."""

import os
import sys

if __package__ in (None, ""):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from database.database import DEFAULT_CSV_PATH, DEFAULT_DB_PATH, migrate_csv_to_database


if __name__ == "__main__":
    imported_or_updated, total_products = migrate_csv_to_database(DEFAULT_CSV_PATH, DEFAULT_DB_PATH)
    print(f"Imported/updated products: {imported_or_updated}")
    print(f"Total products in database: {total_products}")
