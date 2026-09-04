from urllib.parse import urlparse


def validate_image_url(image_url):
    """Return (is_valid, normalized_url) for image values."""
    if image_url is None:
        return False, ""

    value = str(image_url).strip()
    if not value:
        return False, ""

    parsed = urlparse(value)
    if value.startswith('/'):
        return True, value
    if parsed.scheme not in {"http", "https"}:
        return False, ""
    if not parsed.netloc:
        return False, ""
    return True, value


def validate_product_url(product_url):
    """Return (is_valid, normalized_url) for product values."""
    if product_url is None:
        return False, ""

    value = str(product_url).strip()
    if not value:
        return False, ""

    parsed = urlparse(value)
    if value.startswith('/'):
        return True, value
    if parsed.scheme not in {"http", "https"}:
        return False, ""
    if not parsed.netloc:
        return False, ""
    return True, value


def get_safe_image_url(image_url):
    """Return a valid image URL or a professional placeholder."""
    ok, url = validate_image_url(image_url)
    if ok:
        return url
    return "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1200&q=80"


def get_safe_product_url(product_url):
    """Return a valid product URL or an empty string for broken links."""
    ok, url = validate_product_url(product_url)
    if ok:
        return url
    return ""
