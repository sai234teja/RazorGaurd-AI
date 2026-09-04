import os

from app import app
from catalog.import_products import import_seed_products
from catalog.seed_real_products import get_real_seed_products
from database.database import initialize_database
from services.catalog_service import CatalogService
from services.product_media_service import validate_image_url, validate_product_url
from agent_pipeline import RazorPayCommerceAgent

DB_PATH = os.path.join("database", "commerce.db")


def setup_function():
    initialize_database(DB_PATH)
    import_seed_products(db_path=DB_PATH)


def test_real_seed_data_loads():
    products = get_real_seed_products()
    assert len(products) >= 50
    assert len({item["product_id"] for item in products}) == len(products)


def test_product_count_increases_with_seed_import():
    service = CatalogService(DB_PATH)
    before = service.count_products()
    import_seed_products(db_path=DB_PATH)
    after = service.count_products()
    assert after >= before
    assert after >= 50


def test_no_duplicate_product_ids_in_seed():
    products = get_real_seed_products()
    ids = [item["product_id"] for item in products]
    assert len(ids) == len(set(ids))


def test_every_seeded_product_has_valid_brand_and_name():
    for product in get_real_seed_products():
        assert product["brand"].strip()
        assert product["name"].strip()
        assert product["category"].strip()


def test_every_seeded_product_has_valid_product_url_and_image_url_when_provided():
    for product in get_real_seed_products():
        if product.get("product_url"):
            ok, _ = validate_product_url(product["product_url"])
            assert ok
        if product.get("image_url"):
            ok, _ = validate_image_url(product["image_url"])
            assert ok


def test_dynamic_recommendation_still_works_with_real_catalog():
    agent = RazorPayCommerceAgent()
    result = agent.recommend_for_api("I need a phone under 20000 with the best camera")
    assert result["candidate_count"] > 0
    assert len(result["products"]) > 0


def test_api_products_route_works():
    client = app.test_client()
    response = client.get("/api/products")
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)
    assert len(payload) >= 50


def test_api_recommend_route_works():
    client = app.test_client()
    response = client.post(
        "/api/recommend",
        json={"message": "I need a phone under 20000 with the best camera"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["candidate_count"] > 0
