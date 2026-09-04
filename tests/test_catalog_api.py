import os

from app import app
from database.database import migrate_csv_to_database

TEST_PRODUCT_ID = "TEMP_API_TEST_001"


def setup_function():
    migrate_csv_to_database()


def teardown_function():
    from services.catalog_service import CatalogService

    service = CatalogService()
    if service.get_product(TEST_PRODUCT_ID) is not None:
        service.delete_product(TEST_PRODUCT_ID)


def test_get_products_returns_100_products():
    client = app.test_client()
    response = client.get("/api/products")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 100


def test_get_existing_product_works():
    client = app.test_client()
    response = client.get("/api/products/P001")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["product_id"] == "P001"
    assert payload["name"] == "SoundMax Air Pro"


def test_get_unknown_product_returns_404():
    client = app.test_client()
    response = client.get("/api/products/UNKNOWN_PRODUCT_999")
    assert response.status_code == 404


def test_post_creates_new_product():
    client = app.test_client()
    response = client.post(
        "/api/products",
        json={
            "product_id": TEST_PRODUCT_ID,
            "name": "Temp API Product",
            "category": "audio",
            "price": 1999,
            "stock": 7,
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["product_id"] == TEST_PRODUCT_ID


def test_post_duplicate_product_returns_409():
    client = app.test_client()
    client.post(
        "/api/products",
        json={
            "product_id": TEST_PRODUCT_ID,
            "name": "Temp API Product",
            "category": "audio",
            "price": 1999,
            "stock": 7,
        },
    )
    response = client.post(
        "/api/products",
        json={
            "product_id": TEST_PRODUCT_ID,
            "name": "Temp API Product",
            "category": "audio",
            "price": 1999,
            "stock": 7,
        },
    )
    assert response.status_code == 409


def test_put_updates_product():
    client = app.test_client()
    client.post(
        "/api/products",
        json={
            "product_id": TEST_PRODUCT_ID,
            "name": "Temp API Product",
            "category": "audio",
            "price": 1999,
            "stock": 7,
        },
    )
    response = client.put(
        "/api/products/" + TEST_PRODUCT_ID,
        json={
            "name": "Updated Temp Product",
            "price": 2999,
            "stock": 12,
            "brand": "Temp Brand",
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["name"] == "Updated Temp Product"
    assert payload["price"] == 2999
    assert payload["stock"] == 12


def test_delete_removes_product():
    client = app.test_client()
    client.post(
        "/api/products",
        json={
            "product_id": TEST_PRODUCT_ID,
            "name": "Temp API Product",
            "category": "audio",
            "price": 1999,
            "stock": 7,
        },
    )
    response = client.delete("/api/products/" + TEST_PRODUCT_ID)
    assert response.status_code == 200
    lookup = client.get("/api/products/" + TEST_PRODUCT_ID)
    assert lookup.status_code == 404
