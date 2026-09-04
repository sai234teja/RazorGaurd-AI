from services.catalog_service import CatalogService
from agent_pipeline import RazorPayCommerceAgent

TEST_ID = 'DYNAMIC_TEST_PHONE_001'
service = CatalogService()
service.delete_product(TEST_ID)
start_count = service.count_products()
print('START_COUNT', start_count)

service.add_product({
    'product_id': TEST_ID,
    'brand': 'TestBrand',
    'name': 'Dynamic Test Phone',
    'category': 'smartphones',
    'price': 18999,
    'currency': 'INR',
    'description': 'Dynamic test product for AI recommendation pipeline',
    'rating': 4.8,
    'stock': 10,
    'image_url': '',
    'product_url': '',
    'attributes': {
        'camera_mp': 108,
        'ram_gb': 8,
        'storage_gb': 128,
        'battery_mah': 5000
    },
    'use_cases': ['photography', 'daily use']
})

count_after_add = service.count_products()
print('COUNT_AFTER_ADD', count_after_add)
assert count_after_add == start_count + 1

found = service.search_for_intent({
    'category': 'Smartphones',
    'subcategory': 'smartphones',
    'max_price': 20000,
    'use_cases': ['photography'],
    'preferences': {'camera_mp': {'value': 108, 'importance': 'critical'}}
})
print('SEARCH_FOUND', len(found), [p['product_id'] for p in found[:5]])
assert any(p['product_id'] == TEST_ID for p in found)

agent = RazorPayCommerceAgent()
result = agent.recommend_for_api('I need a smartphone under 20k with the best camera')
print('RESULT_COUNT', result.get('candidate_count'))
print('RESULT_PRODUCTS', [p.get('product_id') for p in result.get('products', [])[:5]])
assert result.get('candidate_count', 0) > 0
assert any(p.get('product_id') == TEST_ID for p in result.get('products', []))

service.delete_product(TEST_ID)
final_count = service.count_products()
print('FINAL_COUNT', final_count)
assert final_count == start_count
print('DYNAMIC_TEST_PASSED')
