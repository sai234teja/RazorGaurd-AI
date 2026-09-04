import os
import sqlite3

from database.database import (
    get_connection,
    initialize_database,
    migrate_csv_to_database,
)
from services.catalog_service import CatalogService


CSV_PATH = os.path.join("catalog", "products.csv")
DB_PATH = os.path.join("database", "commerce.db")


def setup_function():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    initialize_database(DB_PATH)
    migrate_csv_to_database(CSV_PATH, DB_PATH)


def test_database_initializes():
    conn = get_connection(DB_PATH)
    assert conn is not None
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
    ).fetchone()
    assert row is not None
    conn.close()


def test_100_products_migrated():
    service = CatalogService(DB_PATH)
    assert service.count_products() == 100


def test_product_lookup_works():
    service = CatalogService(DB_PATH)
    product = service.get_product("P001")
    assert product is not None
    assert product["name"] == "SoundMax Air Pro"
    assert product["category"] == "wireless headphones"


def test_product_count_works():
    service = CatalogService(DB_PATH)
    assert service.count_products() >= 1


def test_add_product_increases_count():
    service = CatalogService(DB_PATH)
    before = service.count_products()
    service.add_product({
        "product_id": "TEST_NEW_001",
        "brand": "Test Brand",
        "name": "Test Speaker",
        "category": "audio",
        "price": 2999,
        "currency": "INR",
        "description": "Test product for catalog service",
        "rating": 4.8,
        "stock": 10,
        "image_url": "https://example.com/image.jpg",
        "product_url": "https://example.com/product",
        "attributes": {"battery_hours": 20, "noise_cancellation": True},
        "use_cases": ["travel", "music"],
    })
    assert service.count_products() == before + 1


def test_updating_existing_product_does_not_increase_count():
    service = CatalogService(DB_PATH)
    before = service.count_products()
    service.update_product("P001", {
        "product_id": "P001",
        "brand": "Updated Brand",
        "name": "SoundMax Air Pro",
        "category": "wireless headphones",
        "price": 2599,
        "currency": "INR",
        "description": "Updated description",
        "rating": 4.6,
        "stock": 30,
        "image_url": "",
        "product_url": "",
        "attributes": {"battery_hours": 45},
        "use_cases": ["travel"],
    })
    assert service.count_products() == before
    product = service.get_product("P001")
    assert product["price"] == 2599


def test_delete_product_works():
    service = CatalogService(DB_PATH)
    service.add_product({
        "product_id": "TEMP_DELETE_001",
        "brand": "Temp Brand",
        "name": "Temp Product",
        "category": "audio",
        "price": 1999,
        "currency": "INR",
        "description": "Temporary product",
        "rating": 4.0,
        "stock": 5,
        "image_url": "",
        "product_url": "",
        "attributes": {},
        "use_cases": ["music"],
    })
    assert service.get_product("TEMP_DELETE_001") is not None
    service.delete_product("TEMP_DELETE_001")
    assert service.get_product("TEMP_DELETE_001") is None


def test_search_products_works():
    service = CatalogService(DB_PATH)
    result = service.search_products(category="wireless headphones", max_price=3000, use_cases=["travel"])
    assert len(result) > 0
    assert all(item["category"] == "wireless headphones" for item in result)
