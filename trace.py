import sys
import json
import sqlite3
import pandas as pd
from intent_normalizer import IntentNormalizer
from services.catalog_service import CatalogService
from universal_ranker import UniversalRanker
from product_search import ProductSearch

sys.stdout.reconfigure(encoding='utf-8')

# Mock Intents from AI
intent1 = {
    "primary_category": "smartphone",
    "max_price": 30000,
    "preferences": {"processor": "best", "storage": "highest"}
}

intent2 = {
    "primary_category": "laptop",
    "use_cases": ["coding"],
    "min_ram_gb": 16,
    "min_storage_gb": 512,
    "max_price": 80000
}

intent3 = {
    "primary_category": "smartphone",
    "max_price": 40000,
    "preferences": {"camera": "best", "storage_gb": 256}
}

normalizer = IntentNormalizer()
catalog = CatalogService('database/commerce.db')
ranker = UniversalRanker()
product_search = ProductSearch()

queries = [
    ("QUERY 1", "Find me the best phone with the best processor and highest storage under \u20b930,000", intent1),
    ("QUERY 2", "I need a laptop for coding with at least 16GB RAM and 512GB storage under \u20b980,000", intent2),
    ("QUERY 3", "Show me a phone under \u20b940,000 with the best camera and 256GB storage", intent3)
]

print("="*50)
for q_name, text, raw_intent in queries:
    print(q_name + ":")
    print(f"Text: {text}")
    print(f"Raw Intent: {raw_intent}")
    
    norm_intent = normalizer.normalize(raw_intent)
    print(f"Normalized Intent: {norm_intent}")
    
    # 1. Direct Catalog Match
    # 2. Product Search Match
    candidates_list = product_search.search_products(
        category=norm_intent.get("subcategory") or norm_intent.get("primary_category"),
        max_price=norm_intent.get("max_price"),
        min_price=norm_intent.get("min_price"),
        use_cases=norm_intent.get("use_cases", [])
    )
    
    candidates_df = product_search.to_universal_dataframe(candidates_list)
    print(f"CatalogService Candidates Count: {len(candidates_df)}")
    if len(candidates_df) > 0:
        prices = candidates_df['price'].tolist()
        print(f"Max Price in Candidates: {max(prices)}")
        
    ranked = ranker.rank(
        candidates_df,
        max_price=norm_intent.get("max_price"),
        min_price=norm_intent.get("min_price"),
        use_cases=norm_intent.get("use_cases", []),
        preferences=norm_intent.get("preferences", {}),
        top_n=5
    )
    print(f"Ranker Results Count: {len(ranked)}")
    
    print("Returned products:")
    for _, row in ranked.iterrows():
        print(f"  - {row['name']} | Price: {row['price']} | Attrs: {row['attributes']}")
        
    print("Violations:")
    for _, row in ranked.iterrows():
        violations = []
        if norm_intent.get('max_price') and row['price'] > norm_intent['max_price']:
            violations.append(f"Price {row['price']} > {norm_intent['max_price']}")
        if raw_intent.get('min_ram_gb'):
            # parse attrs
            import json
            attrs = json.loads(row['attributes']) if isinstance(row['attributes'], str) else row['attributes']
            if attrs.get('ram_gb', 0) < raw_intent['min_ram_gb']:
                violations.append(f"RAM {attrs.get('ram_gb', 0)} < {raw_intent['min_ram_gb']}")
        if len(violations) > 0:
             print(f"  - {row['name']} violations: {', '.join(violations)}")
             
    print("-" * 50)
