import os
import re

agent_file = 'agent_pipeline.py'

with open(agent_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add _assign_tradeoffs method
tradeoff_logic = '''
    def _assign_tradeoffs(self, products, intent):
        """Deterministically assigns tradeoff labels to the ranked products."""
        if not products:
            return

        # Product at index 0 is rank 1. 
        # Check if it's a "Strong match" (score >= 0.8)
        best_product = products[0]
        match_score = float(best_product.get("match_score", 0))
        
        if match_score >= 80.0:
            best_product["strong_match"] = True
            best_product["tradeoff_label"] = "BEST OVERALL"
            best_product["tradeoff_reason"] = "Best overall balance for your requirements"
        
        if len(products) > 1:
            best_price = best_product.get("price", 0)
            
            # Find BEST VALUE: strictly cheapest among top 5 valid products
            top_5 = products[:5]
            cheapest = min(top_5, key=lambda x: x.get("price", 0))
            if cheapest.get("price", 0) < best_price and cheapest.get("product_id") != best_product.get("product_id"):
                cheapest["tradeoff_label"] = "BEST VALUE"
                cheapest["tradeoff_reason"] = f"Lower price (₹{cheapest.get('price'):,}) while meeting your requirements"

            # Find BEST PERFORMANCE based on processor/ram if user prioritized performance
            prefs = intent.get("preferences", {})
            prioritizes_perf = any(k in ["processor", "ram_gb"] for k in prefs.keys())
            
            if prioritizes_perf:
                # Find product with best processor/RAM
                best_perf = None
                best_ram = best_product.get("attributes", {}).get("ram_gb", 0)
                try:
                    best_ram = float(best_ram) if best_ram else 0
                except:
                    best_ram = 0
                
                for p in top_5:
                    if p.get("product_id") == best_product.get("product_id"):
                        continue
                        
                    p_ram = p.get("attributes", {}).get("ram_gb", 0)
                    try:
                        p_ram = float(p_ram) if p_ram else 0
                    except:
                        p_ram = 0
                        
                    if p_ram > best_ram:
                        best_perf = p
                        best_ram = p_ram
                
                if best_perf and best_perf.get("tradeoff_label") is None:
                    best_perf["tradeoff_label"] = "BEST PERFORMANCE"
                    best_perf["tradeoff_reason"] = f"Stronger specs ({int(best_ram)}GB RAM), but costs more"

'''

if '_assign_tradeoffs' not in content:
    content = content.replace('    def _generate_merchant_insight(', tradeoff_logic + '\n    def _generate_merchant_insight(')

# 2. Modify product loop to enhance "why" array
# We'll replace the block from `products = []` to `yield emit_stage("recommendations_ready", "Recommendations Ready", "completed")`
# Actually, the loop builds `products`.
# Let's use regex to replace the loop carefully.

import re

loop_pattern = re.compile(
    r'(yield emit_stage\("recommendations_ready", "Recommendations Ready", "running"\)\n\s*products = \[\]\n\s*for _, product in ranked\.iterrows\(\):.*?\n\s*products\.append\(product_dict\))',
    re.DOTALL
)

new_loop = '''yield emit_stage("recommendations_ready", "Recommendations Ready", "running")
            products = []

            for _, product in ranked.iterrows():
                attributes = product.get("attributes", {})
                if not isinstance(attributes, dict):
                    try:
                        import json
                        attributes = json.loads(attributes)
                    except Exception:
                        attributes = {}

                why = []
                price = product.get("price", 0)
                rating = product.get("rating", 0)
                stock = product.get("stock", 0)
                max_price = intent.get("max_price")

                if max_price is not None and price <= max_price:
                    why.append(f"Within your ₹{int(max_price):,} budget")

                # Factual required constraint matches
                reqs = intent.get("required", {})
                for k, v in reqs.items():
                    actual = attributes.get(k)
                    if actual is not None:
                        if isinstance(v, dict) and ">=" in v:
                            why.append(f"Meets your {v['>=']}+ {k.replace('_gb', 'GB').replace('_mp', 'MP').upper()} requirement")
                        elif isinstance(v, dict) and "==" in v:
                            why.append(f"Has {v['==']} {k.replace('_', ' ').title()}")
                        elif not isinstance(v, dict):
                            why.append(f"Has {actual} {k.replace('_', ' ').title()}")

                # Preferences check
                prefs = intent.get("preferences", {})
                if "processor" in prefs or "ram_gb" in prefs:
                    why.append("Strong specs for your stated priority")
                
                # Use cases
                use_cases = intent.get("use_cases", [])
                if use_cases:
                    why.append(f"Suitable for {', '.join(use_cases).title()}")

                product_dict = {
                    "product_id": str(product.get("product_id", "")),
                    "name": str(product.get("name", "")),
                    "brand": str(product.get("brand", "")),
                    "category": str(product.get("category", "")),
                    "subcategory": str(product.get("subcategory", "")),
                    "price": float(price),
                    "stock": int(stock),
                    "rating": float(rating),
                    "reviews": int(product.get("reviews", 0)),
                    "attributes": attributes,
                    "description": str(product.get("description", "")),
                    "use_cases": product.get("use_cases", []),
                    "image_url": str(product.get("image_url", "")),
                    "product_url": str(product.get("product_url", "")),
                    "match_score": float(product.get("score", 0)) * 100,
                    "why": why,
                    "price_comparison": product.get("price_comparison")
                }
                
                products.append(product_dict)
                
            self._assign_tradeoffs(products, intent)
'''

content = loop_pattern.sub(new_loop.replace('\\', '\\\\'), content)

with open(agent_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Backend tradeoff patch complete.")
