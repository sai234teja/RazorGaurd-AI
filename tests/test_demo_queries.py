import pytest
from agent_pipeline import RazorPayCommerceAgent

def test_best_processor_highest_storage_budget():
    pipeline = RazorPayCommerceAgent()
    q = "Find me the best phone with the best processor and highest storage under ₹30,000"
    intent = pipeline.normalizer.normalize(pipeline.gemini.fallback_intent(q))
    
    assert intent['category'] == 'Electronics'
    assert intent['subcategory'] == 'Smartphones'
    assert intent['max_price'] == 30000.0
    
    # Check preferences
    prefs = intent.get('preferences', {})
    assert prefs.get('storage_gb', {}).get('direction') == 'maximize'

def test_min_ram_exact_storage_budget():
    pipeline = RazorPayCommerceAgent()
    q = "I need a laptop for coding with at least 16GB RAM and 512GB storage under ₹80,000"
    intent = pipeline.normalizer.normalize(pipeline.gemini.fallback_intent(q))
    
    assert intent['category'] == 'Electronics'
    assert intent['subcategory'] == 'Laptops'
    assert intent['max_price'] == 80000.0
    
    # Check required constraints
    req = intent.get('required', {})
    assert req.get('ram_gb', {}).get('value') == 16
    assert req.get('ram_gb', {}).get('operator') == '>='
    assert req.get('storage_gb', {}).get('value') == 512
    assert req.get('storage_gb', {}).get('operator') == '=='

def test_best_camera_exact_storage_budget():
    pipeline = RazorPayCommerceAgent()
    q = "Show me a phone under ₹40,000 with the best camera and 256GB storage"
    intent = pipeline.normalizer.normalize(pipeline.gemini.fallback_intent(q))
    
    assert intent['category'] == 'Electronics'
    assert intent['subcategory'] == 'Smartphones'
    assert intent['max_price'] == 40000.0
    
    req = intent.get('required', {})
    assert req.get('storage_gb', {}).get('value') == 256
    
    prefs = intent.get('preferences', {})
    assert prefs.get('camera_mp', {}).get('direction') == 'maximize'

def test_unknown_attribute():
    pipeline = RazorPayCommerceAgent()
    q = "Show me a phone with a flux capacitor"
    intent = pipeline.normalizer.normalize(pipeline.gemini.fallback_intent(q))
    assert intent['subcategory'] == 'Smartphones'
    
def test_image_category_consistency():
    pipeline = RazorPayCommerceAgent()
    q = "Find a laptop"
    result = pipeline.recommend_for_api(q)
    assert result['intent']['subcategory'] == 'Laptops'
    for product in result['products']:
        assert product['category'].lower() == 'laptops'

def test_no_match_zero_fallback():
    pipeline = RazorPayCommerceAgent()
    q = "Find me the cheapest tablet with 256GB storage"
    result = pipeline.recommend_for_api(q)
    assert result['candidate_count'] == 0
    assert len(result['products']) == 0
    assert "No matching products found." in result['message']
