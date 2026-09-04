"""Dynamic merchant catalog REST API."""

from flask import Blueprint, jsonify, request

from services.catalog_service import CatalogService

catalog_api = Blueprint("catalog_api", __name__)


@catalog_api.route("/api/products", methods=["GET"])
def get_products():
    """Return all products from the SQLite catalog with optional filters."""
    service = CatalogService()
    category = request.args.get("category")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    search = request.args.get("search")
    in_stock = request.args.get("in_stock")

    products = service.search_products(
        category=category,
        min_price=float(min_price) if min_price not in (None, "") else None,
        max_price=float(max_price) if max_price not in (None, "") else None,
        query=search,
        in_stock=(str(in_stock).lower() in {"1", "true", "yes"}) if in_stock is not None else None,
    )

    return jsonify(products), 200


@catalog_api.route("/api/products/<product_id>", methods=["GET"])
def get_product(product_id):
    """Return a single product by product_id."""
    service = CatalogService()
    product = service.get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@catalog_api.route("/api/products", methods=["POST"])
def create_product():
    """Create a new product in the SQLite catalog."""
    payload = request.get_json(silent=True) or {}
    required = ["product_id", "name", "category", "price", "stock"]

    missing = [field for field in required if not payload.get(field) and payload.get(field) != 0]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    service = CatalogService()
    if service.get_product(payload["product_id"]) is not None:
        return jsonify({"error": "Product already exists"}), 409

    product = {
        "product_id": str(payload["product_id"]).strip(),
        "brand": payload.get("brand", "Merchant Brand"),
        "name": str(payload["name"]).strip(),
        "category": str(payload["category"]).strip(),
        "price": float(payload["price"]),
        "currency": payload.get("currency", "INR"),
        "description": payload.get("description", ""),
        "rating": float(payload.get("rating", 0) or 0),
        "stock": int(payload["stock"]),
        "image_url": payload.get("image_url", ""),
        "product_url": payload.get("product_url", ""),
        "attributes": payload.get("attributes", {}),
        "use_cases": payload.get("use_cases", []),
    }

    created = service.add_product(product)
    return jsonify(created), 201


@catalog_api.route("/api/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    """Update an existing product."""
    payload = request.get_json(silent=True) or {}
    service = CatalogService()

    if service.get_product(product_id) is None:
        return jsonify({"error": "Product not found"}), 404

    product = {
        "product_id": product_id,
        "brand": payload.get("brand", "Merchant Brand"),
        "name": payload.get("name") or service.get_product(product_id)["name"],
        "category": payload.get("category") or service.get_product(product_id)["category"],
        "price": float(payload.get("price", service.get_product(product_id)["price"])),
        "currency": payload.get("currency", service.get_product(product_id).get("currency", "INR")),
        "description": payload.get("description", service.get_product(product_id).get("description", "")),
        "rating": float(payload.get("rating", service.get_product(product_id)["rating"])),
        "stock": int(payload.get("stock", service.get_product(product_id)["stock"])),
        "image_url": payload.get("image_url", service.get_product(product_id).get("image_url", "")),
        "product_url": payload.get("product_url", service.get_product(product_id).get("product_url", "")),
        "attributes": payload.get("attributes", service.get_product(product_id).get("attributes", {})),
        "use_cases": payload.get("use_cases", service.get_product(product_id).get("use_cases", [])),
    }

    updated = service.update_product(product_id, product)
    return jsonify(updated), 200


@catalog_api.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Delete an existing product."""
    service = CatalogService()
    if service.get_product(product_id) is None:
        return jsonify({"error": "Product not found"}), 404

    service.delete_product(product_id)
    return jsonify({"success": True, "product_id": product_id}), 200
