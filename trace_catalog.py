import sys
import sqlite3
import pandas as pd
from intent_normalizer import IntentNormalizer
from services.catalog_service import CatalogService
from universal_ranker import UniversalRanker

sys.stdout.reconfigure(encoding='utf-8')

gemini_intent1 = {'category': 'Electronics', 'subcategory': 'Smartphones', 'max_price': 30000.0, 'min_price': None, 'use_cases': ['best phone'], 'preferences': {'processor': {'value': None, 'importance': 'critical', 'direction': 'maximize'}, 'storage_gb': {'value': None, 'importance': 'critical', 'direction': 'maximize'}}}
gemini_intent2 = {'category': 'Electronics', 'subcategory': 'Laptops', 'max_price': 80000.0, 'min_price': None, 'use_cases': ['coding'], 'required': {'ram_gb': {'value': 16, 'operator': '>='}, 'storage_gb': {'value': 512, 'operator': '>='}}}
gemini_intent3 = {'category': 'Electronics', 'subcategory': 'Smartphones', 'max_price': 40000.0, 'min_price': None, 'use_cases': [], 'preferences': {'camera_mp': {'value': None, 'importance': 'critical', 'direction': 'maximize'}, 'storage_gb': {'value': 256, 'importance': 'critical', 'direction': 'match'}}}

intents = [
    ("QUERY 1", gemini_intent1),
    ("QUERY 2", gemini_intent2),
    ("QUERY 3", gemini_intent3),
]

normalizer = IntentNormalizer()
catalog = CatalogService('database/commerce.db')
ranker = UniversalRanker()

for q_name, raw_intent in intents:
    print("="*50)
    print(q_name + ":")
    
    # We pretend normalizer has already been called as Gemini intents are already structured,
    # but let's pass them through anyway (they might change).
    norm_intent = normalizer.normalize(raw_intent)
    print(f"Norm Intent: {norm_intent}")
    
    candidates_list = catalog.search_for_intent(norm_intent)
    print(f"CatalogService Candidates Count: {len(candidates_list)}")
    if len(candidates_list) > 0:
        prices = [p['price'] for p in candidates_list]
        print(f"Max Price in Candidates: {max(prices)}")
        
    ranked = ranker.rank(
        pd.DataFrame(candidates_list) if len(candidates_list) > 0 else pd.DataFrame(),
        max_price=norm_intent.get("max_price"),
        min_price=norm_intent.get("min_price"),
        use_cases=norm_intent.get("use_cases", []),
        preferences=norm_intent.get("preferences", {}),
        top_n=5
    )
    print(f"Ranker Results Count: {len(ranked)}")
    
    print("Returned products:")
    for _, row in ranked.iterrows():
        print(f"  - {row['name']} | Price: {row['price']}")
