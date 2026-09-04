import json
from agent_pipeline import RazorPayCommerceAgent
from services.catalog_service import CatalogService
import traceback

agent = RazorPayCommerceAgent()
catalog = CatalogService()

queries = [
    "Find me the best phone with the best processor and highest storage under ₹30,000.",
    "I need a laptop for coding with at least 16GB RAM and 512GB storage under ₹80,000.",
    "Show me a phone under ₹40,000 with the best camera and 256GB storage.",
    "Find me the cheapest tablet with 256GB storage"
]

print("\n" + "="*80)
print("DEMO QUERIES VERIFICATION")
print("="*80)

for query in queries:
    print(f"\n\n>>> QUERY: {query}")
    try:
        gemini_intent = agent.gemini.parse(query)
        intent = agent.normalizer.normalize(gemini_intent)
        intent = agent.normalizer.recover_constraints(query, intent, agent.gemini.fallback_intent)
        
        print("\n--- FINAL NORMALIZED INTENT ---")
        print(json.dumps(intent, indent=2))
        
        # Candidate counting before hard filter (search_products without required)
        raw_candidates = catalog.search_products(
            category=intent.get("subcategory"),
            max_price=intent.get("max_price"),
            min_price=intent.get("min_price"),
            use_cases=intent.get("use_cases", [])
        )
        print(f"\nCandidates BEFORE Required Filter: {len(raw_candidates)}")
        
        # Candidate counting after hard filter (search_for_intent)
        filtered_candidates = catalog.search_for_intent(intent)
        print(f"Candidates AFTER Required Filter: {len(filtered_candidates)}")
        
        # Run full pipeline to get Top 3
        response = agent.recommend_for_api(query)
        
        print("\n--- TOP 3 RESULTS ---")
        products = response.get("products", [])[:3]
        if not products:
            print("No matching products found. (Valid behavior for no-match)")
        for idx, prod in enumerate(products, 1):
            attr = prod.get("attributes", {})
            print(f"\n{idx}. {prod['name']}")
            print(f"   Price: ₹{prod['price']}")
            print(f"   Processor: {attr.get('processor', 'N/A')}")
            print(f"   RAM: {attr.get('ram_gb', 'N/A')}GB")
            print(f"   Storage: {attr.get('storage_gb', 'N/A')}GB")
            print(f"   Camera: {attr.get('camera_mp', 'N/A')}MP")
            print(f"   Score: {prod['match_score']}%")
            print(f"   Why: {', '.join(prod['why'])}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

print("\n" + "="*80)
