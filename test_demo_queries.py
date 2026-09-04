import asyncio
import json
from agent_pipeline import RazorPayCommerceAgent # RazorPayCommerceAgent

queries = [
    "Find me the best phone with the best processor and highest storage under ₹30,000",
    "I need a laptop for coding with at least 16GB RAM and 512GB storage under ₹80,000",
    "Show me a phone under ₹40,000 with the best camera and 256GB storage"
]

async def run_tests():
    pipeline = RazorPayCommerceAgent()
    for i, q in enumerate(queries):
        print(f"\n{'='*50}\nQUERY {i+1}: {q}\n{'='*50}")
        try:
            result = await pipeline.process(q)
            
            print(f"\nNORMALIZED INTENT:\n{json.dumps(result['intent'], indent=2)}")
            print(f"\nTOP RESULTS:")
            
            for j, p in enumerate(result['products'][:3]):
                print(f"\n{j+1}. {p['name']} ({p['category']})")
                print(f"   Score: {p['match_score']}%")
                print(f"   Price: ₹{p['price']}")
                
                attrs = p.get('attributes', {})
                if isinstance(attrs, str):
                    attrs = json.loads(attrs)
                    
                print(f"   Processor: {attrs.get('processor', 'N/A')}")
                print(f"   RAM: {attrs.get('ram_gb', 'N/A')}GB")
                print(f"   Storage: {attrs.get('storage_gb', 'N/A')}GB")
                print(f"   Camera: {attrs.get('camera_mp', 'N/A')}MP")
                
                why = p.get('why_matches', [])
                print(f"   Why: {why}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
