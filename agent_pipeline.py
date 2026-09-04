import json

import pandas as pd

from gemini_intent import GeminiIntentParser
from intent_normalizer import IntentNormalizer
from catalog_engine import CatalogEngine
from product_search import ProductSearch
from services.catalog_service import CatalogService
from audit.audit_service import record_event
from universal_ranker import UniversalRanker


class RazorPayCommerceAgent:

    def __init__(self):

        print(
            "Initializing RazorPay AI Commerce Agent..."
        )

        self.gemini = GeminiIntentParser()

        self.normalizer = IntentNormalizer()

        # Keep the existing catalog engine because
        # UniversalRanker may still depend on it.
        self.catalog = CatalogEngine()

        # Real merchant catalog
        self.product_search = ProductSearch()
        self.catalog_service = CatalogService()

        self.ranker = UniversalRanker(
            self.catalog
        )

    # ==================================================
    # API RECOMMENDATION METHOD
    # ==================================================



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
                PROCESSOR_TIERS = {
                    "core i9": 4.0, "ryzen 9": 4.0,
                    "core i7": 3.0, "ryzen 7": 3.0,
                    "core i5": 2.0, "ryzen 5": 2.0,
                    "core i3": 1.0, "ryzen 3": 1.0
                }
                
                def get_proc_tier(proc_str):
                    if not proc_str: return 0.5
                    proc_str = str(proc_str).lower().strip()
                    for k, v in PROCESSOR_TIERS.items():
                        if k in proc_str:
                            return v
                    return 0.5

                best_perf = None
                best_tier = get_proc_tier(best_product.get("attributes", {}).get("processor", ""))
                
                for p in top_5:
                    if p.get("product_id") == best_product.get("product_id"):
                        continue
                        
                    p_tier = get_proc_tier(p.get("attributes", {}).get("processor", ""))
                    
                    if p_tier > best_tier:
                        best_perf = p
                        best_tier = p_tier
                
                if best_perf and best_perf.get("tradeoff_label") is None:
                    best_perf["tradeoff_label"] = "BEST PERFORMANCE"
                    proc_name = best_perf.get("attributes", {}).get("processor", "Stronger processor")
                    best_perf["tradeoff_reason"] = f"Higher processor tier ({proc_name}), but costs more"


    def _generate_merchant_insight(self, intent, user_message):
        """Generates a Merchant Growth Intelligence insight when no match is found."""
        try:
            # 1. Formulate opportunity string
            reqs = []
            if intent.get("max_price"):
                reqs.append(f"under ₹{intent.get('max_price'):,}")
            
            required_attrs = intent.get("required", {})
            for k, v in required_attrs.items():
                if isinstance(v, dict):
                    # v is like {">=": 32}
                    for op, val in v.items():
                        reqs.append(f"{k} {op} {val}")
                else:
                    reqs.append(f"{k} == {v}")
                    
            opportunity_str = " ".join(reqs)
            
            insight = {
                "type": "lost_sale",
                "reason": "catalog_gap",
                "query": user_message,
                "constraints": intent,
                "matching_products": 0,
                "opportunity": f"Shoppers are searching for: {intent.get('subcategory', 'Products')} {opportunity_str}",
                "severity": "medium",
                "closest_alternatives": []
            }
            
            # 2. Relaxed search for alternatives (drop max_price, min_price, required attributes)
            relaxed_candidates = self.product_search.search_products(
                category=intent.get("subcategory"),
                use_cases=intent.get("use_cases", [])
            )
            
            if not relaxed_candidates:
                relaxed_candidates = []
                
            if isinstance(relaxed_candidates, list):
                import pandas as pd
                relaxed_candidates = pd.DataFrame(relaxed_candidates)
                
            if not relaxed_candidates.empty:
                # Rank alternatives
                closest = self.ranker.rank(
                    relaxed_candidates,
                    preferences=intent.get("preferences", {}),
                    top_n=2
                )
                
                alts = []
                for _, row in closest.iterrows():
                    diffs = []
                    # Simple deterministic diffs
                    if intent.get("max_price") and float(row.get("price", 0)) > float(intent.get("max_price")):
                        diffs.append(f"₹{float(row.get('price', 0)) - float(intent.get('max_price')):,} over budget")
                    
                    attrs = row.get("attributes", {})
                    if isinstance(attrs, str):
                        import json
                        try:
                            attrs = json.loads(attrs)
                        except:
                            attrs = {}
                            
                    for k, v in required_attrs.items():
                        if isinstance(v, dict) and '>=' in v:
                            req_val = v['>=']
                            actual = attrs.get(k)
                            if actual is not None and float(actual) < float(req_val):
                                diffs.append(f"{k}: {actual} (requested at least {req_val})")
                        elif isinstance(v, dict) and '==' in v:
                            req_val = v['==']
                            actual = attrs.get(k)
                            if actual != req_val:
                                diffs.append(f"{k}: {actual} (requested {req_val})")
                                
                    alts.append({
                        "name": str(row.get("name")),
                        "price": float(row.get("price", 0)),
                        "difference": " | ".join(diffs) if diffs else "Does not satisfy all constraints"
                    })
                
                insight["closest_alternatives"] = alts
            
            # 3. Log audit event
            record_event(
                event="MERCHANT_LOST_SALE_INSIGHT",
                status="INFO",
                details={
                    "query": user_message,
                    "intent": intent,
                    "insight": insight
                }
            )
            
            return insight
            
        except Exception as e:
            print(f"Error generating insight: {e}")
            return None

    def recommend_for_api(
        self,
        user_message
    ):
        """
        Runs the complete AI commerce pipeline and returns
        frontend-friendly Python data.

        Flow:

        User request
            ↓
        Gemini / fallback intent
            ↓
        Intent normalization
            ↓
        Merchant products.csv
            ↓
        Universal product adapter
            ↓
        Universal V6 ranker
            ↓
        Frontend-ready recommendations
        """

        # ==================================================
        # STEP 1 — GEMINI UNDERSTANDING
        # ==================================================

        gemini_intent = self.gemini.parse(
            user_message
        )

        # ==================================================
        # STEP 2 — INTENT NORMALIZATION
        # ==================================================

        intent = self.normalizer.normalize(
            gemini_intent
        )
        
        # ==================================================
        # STEP 2.5 — DETERMINISTIC CONSTRAINT RECOVERY
        # ==================================================

        intent = self.normalizer.recover_constraints(
            user_message,
            intent,
            self.gemini.fallback_intent
        )

        foldable_keywords = ["foldable", "fold", "flip", "form factor"]
        if any(kw in user_message.lower() for kw in foldable_keywords):
            if "required" not in intent:
                intent["required"] = {}
            intent["required"]["form_factor"] = {"value": "foldable", "operator": "=="}

        # ==================================================
        # STEP 3 — MERCHANT CATALOG SEARCH
        # ==================================================

        candidates = self.catalog_service.search_for_intent(
            intent
        )

        if not candidates and not intent.get("required"):

            candidates = self.product_search.search_products(

                category=intent.get(
                    "subcategory"
                ),

                max_price=intent.get(
                    "max_price"
                ),

                min_price=intent.get(
                    "min_price"
                ),

                use_cases=intent.get(
                    "use_cases",
                    []
                )
            )

        # --------------------------------------------------
        # No products found
        # --------------------------------------------------

        if isinstance(candidates, pd.DataFrame):
            if candidates.empty:
                return {
                    "query": user_message,
                    "intent": intent,
                    "candidate_count": 0,
                    "products": [],
                    "message": "No matching products found."
                }
        elif not candidates:
            return {
                "query": user_message,
                "intent": intent,
                "candidate_count": 0,
                "products": [],
                "message": "No matching products found."
            }

        # ==================================================
        # STEP 3.5 — UNIVERSAL PRODUCT ADAPTER
        # ==================================================

        if isinstance(candidates, list):
            candidates = pd.DataFrame(candidates)

        # --------------------------------------------------
        # Safety check
        # --------------------------------------------------

        if candidates.empty:

            return {

                "query": user_message,

                "intent": intent,

                "candidate_count": 0,

                "products": [],

                "message":
                    "No matching products found."
            }

        # ==================================================
        # STEP 3.5 — UNIVERSAL PRODUCT ADAPTER
        # ==================================================

        if not isinstance(candidates, pd.DataFrame):
            candidates = (
                self.product_search
                .to_universal_dataframe(
                    candidates
                )
            )

        # --------------------------------------------------
        # Safety check
        # --------------------------------------------------

        if candidates.empty:

            return {

                "query": user_message,

                "intent": intent,

                "candidate_count": 0,

                "products": [],

                "message":
                    "No compatible products found."
            }

        # ==================================================
        # STEP 4 — UNIVERSAL V6 RANKING
        # ==================================================

        ranked = self.ranker.rank(

            candidates,

            max_price=intent.get(
                "max_price"
            ),

            min_price=intent.get(
                "min_price"
            ),

            use_cases=intent.get(
                "use_cases",
                []
            ),

            preferences=intent.get(
                "preferences",
                {}
            ),

            top_n=50
        )

        # ==================================================
        # STEP 5 — CONVERT PRODUCTS FOR FRONTEND
        # ==================================================

        products = []

        for _, product in ranked.iterrows():

            # ----------------------------------------------
            # Product attributes
            # ----------------------------------------------

            attributes = product.get(
                "attributes",
                {}
            )

            if not isinstance(
                attributes,
                dict
            ):

                try:

                    attributes = json.loads(
                        attributes
                    )

                except Exception:

                    attributes = {}

            # ----------------------------------------------
            # WHY THIS PRODUCT MATCHES
            # ----------------------------------------------

            why = []

            price = product.get(
                "price",
                0
            )

            rating = product.get(
                "rating",
                0
            )

            stock = product.get(
                "stock",
                0
            )

            max_price = intent.get(
                "max_price"
            )

            # ----------------------------------------------
            # Budget explanation
            # ----------------------------------------------

            if (
                max_price is not None
                and price <= max_price
            ):

                why.append(
                    f"Within your ₹{int(max_price):,} budget"
                )

            # ----------------------------------------------
            # Rating explanation
            # ----------------------------------------------

            if rating:

                why.append(
                    f"Rated {float(rating):.1f}/5"
                )

            # ----------------------------------------------
            # Stock explanation
            # ----------------------------------------------

            if stock > 0:

                why.append(
                    f"In stock ({int(stock)} available)"
                )

            # ==================================================
            # STEP 5.1 — PREFERENCE EXPLANATIONS
            # ==================================================

            all_requirements = {}
            all_requirements.update(intent.get("required", {}))
            all_requirements.update(intent.get("preferences", {}))

            for key, requirement in (
                all_requirements.items()
            ):

                if not isinstance(
                    requirement,
                    dict
                ):

                    continue

                actual = attributes.get(
                    key
                )

                # ------------------------------------------
                # Attribute aliases
                # ------------------------------------------

                if actual is None:

                    aliases = {

                        "camera_mp": [
                            "camera_mp"
                        ],

                        "ram_gb": [
                            "ram_gb"
                        ],

                        "storage_gb": [
                            "storage_gb"
                        ],

                        "battery_hours": [
                            "battery_hours"
                        ],

                        "battery_days": [
                            "battery_days"
                        ],

                        "battery_mah": [
                            "battery_mah"
                        ],

                        "capacity_liters": [
                            "capacity_liters"
                        ],

                        "power_watts": [
                            "power_watts"
                        ],

                        "suction_power": [
                            "suction_power"
                        ],

                        "battery_minutes": [
                            "battery_minutes"
                        ],

                        "wireless": [
                            "wireless"
                        ],

                        "noise_cancellation": [
                            "noise_cancellation"
                        ],

                        "comfort": [
                            "comfort"
                        ],

                        "water_resistant": [
                            "water_resistant"
                        ],

                        "gps": [
                            "gps"
                        ],

                        "heart_rate": [
                            "heart_rate"
                        ],

                        "cordless": [
                            "cordless"
                        ],

                        "portable": [
                            "portable"
                        ],

                        "laptop_compartment": [
                            "laptop_compartment"
                        ]
                    }

                    for alias in aliases.get(
                        key,
                        []
                    ):

                        if alias in attributes:

                            actual = (
                                attributes[
                                    alias
                                ]
                            )

                            break

                if actual is None:
                    if key in ["processor", "ram_gb", "storage_gb", "camera_mp"]:
                        why.append(f"{key.replace('_gb', ' GB').replace('_mp', ' MP').capitalize()} comparison unavailable")
                    continue

                # ==================================================
                # NUMERIC & STRING ATTRIBUTES
                # ==================================================

                if key == "processor":
                    
                    why.append(
                        f"{actual} processor"
                    )

                elif key == "camera_mp":

                    why.append(
                        f"{actual} MP camera"
                    )

                elif key == "ram_gb":

                    why.append(
                        f"{actual} GB RAM"
                    )

                elif key == "storage_gb":

                    why.append(
                        f"{actual} GB storage"
                    )

                elif key == "battery_hours":

                    why.append(
                        f"{actual}-hour battery"
                    )

                elif key == "battery_days":

                    why.append(
                        f"{actual}-day battery"
                    )

                elif key == "battery_mah":

                    why.append(
                        f"{actual} mAh battery"
                    )

                elif key == "capacity_liters":

                    why.append(
                        f"{actual}L capacity"
                    )

                elif key == "power_watts":

                    why.append(
                        f"{actual}W power"
                    )

                elif key == "suction_power":

                    why.append(
                        f"{actual} suction power"
                    )

                elif key == "battery_minutes":

                    why.append(
                        f"{actual}-minute battery"
                    )

                # ==================================================
                # TEXT / BOOLEAN ATTRIBUTES
                # ==================================================

                elif key == "comfort":

                    why.append(
                        f"{str(actual).capitalize()} comfort"
                    )

                elif key == "wireless":

                    if actual:

                        why.append(
                            "Wireless connectivity"
                        )

                elif key == "noise_cancellation":

                    if actual:

                        why.append(
                            "Noise cancellation"
                        )

                elif key == "water_resistant":

                    if actual:

                        why.append(
                            "Water resistant"
                        )

                elif key == "gps":

                    if actual:

                        why.append(
                            "GPS included"
                        )

                elif key == "heart_rate":

                    if actual:

                        why.append(
                            "Heart-rate monitoring"
                        )

                elif key == "cordless":

                    if actual:

                        why.append(
                            "Cordless design"
                        )

                elif key == "portable":

                    if actual:

                        why.append(
                            "Portable design"
                        )

                elif key == "laptop_compartment":

                    if actual:

                        why.append(
                            "Laptop compartment included"
                        )

            # ==================================================
            # STEP 5.2 — USE CASE EXPLANATION
            # ==================================================

            product_use_cases = product.get(
                "use_cases",
                []
            )

            if not isinstance(
                product_use_cases,
                list
            ):

                product_use_cases = []

            requested_use_cases = intent.get(
                "use_cases",
                []
            )

            if isinstance(
                requested_use_cases,
                str
            ):

                requested_use_cases = [
                    requested_use_cases
                ]

            matched_use_cases = []

            for requested in (
                requested_use_cases
            ):

                requested_lower = str(
                    requested
                ).lower()

                for available in (
                    product_use_cases
                ):

                    if (
                        requested_lower
                        in str(
                            available
                        ).lower()
                    ):

                        matched_use_cases.append(
                            str(
                                available
                            )
                        )

            for use_case in matched_use_cases:

                message = (
                    f"Suitable for {use_case}"
                )

                if message not in why:

                    why.append(
                        message
                    )

            # ==================================================
            # STEP 5.3 — PRICE COMPARISON
            # ==================================================

            product_id = str(
                product.get(
                    "product_id",
                    "",
                )
            )

            try:
                price_comparison = (
                    self.catalog_service.get_price_comparison(
                        product_id
                    )
                )
            except Exception as exc:
                # Price comparison must never break recommendations.
                print(
                    f"⚠️ Price comparison unavailable for "
                    f"{product_id}: {exc}"
                )

                price_comparison = {
                    "has_offers": False,
                    "offer_count": 0,
                    "lowest_price": None,
                    "lowest_total": None,
                    "lowest_merchant": None,
                    "lowest_merchant_id": None,
                    "savings": 0,
                    "currency": str(
                        product.get(
                            "currency",
                            "INR",
                        )
                    ),
                    "offers": [],
                }

            # ==================================================
            # STEP 5.4 — PRODUCT JSON
            # ==================================================

            products.append({

                "product_id": product_id,

                "name": str(
                    product.get(
                        "name",
                        ""
                    )
                ),

                "brand": str(
                    product.get(
                        "brand",
                        ""
                    )
                ),

                "category": str(
                    product.get(
                        "category",
                        ""
                    )
                ),

                "subcategory": str(
                    product.get(
                        "subcategory",
                        ""
                    )
                ),

                "price": float(
                    product.get(
                        "price",
                        0
                    )
                ),

                "currency": str(
                    product.get(
                        "currency",
                        "INR"
                    )
                ),

                "description": str(
                    product.get(
                        "description",
                        ""
                    )
                ),

                "rating": float(
                    product.get(
                        "rating",
                        0
                    )
                ),

                "stock": int(
                    product.get(
                        "stock",
                        0
                    )
                ),

                "match_score": float(
                    product.get(
                        "match_score",
                        0
                    )
                ),

                "attributes": attributes,

                "use_cases": product_use_cases,

                "image_url": str(
                    product.get(
                        "image_url",
                        ""
                    )
                ),

                "product_url": str(
                    product.get(
                        "product_url",
                        ""
                    )
                ),

                # Multi-merchant price comparison.
                # Current seeded offers are explicitly demo data.
                "price_comparison": price_comparison,

                "why": why[:8]
            })

        # ==================================================
        # FINAL API RESPONSE
        # ==================================================

        return {

            "query": user_message,

            "intent": intent,

            "candidate_count": int(
                len(candidates)
            ),

            "products": products
        }

    # ==================================================
    # API STREAMING METHOD (SSE)
    # ==================================================

    def recommend_stream(
        self,
        user_message
    ):
        """
        Runs the complete AI commerce pipeline and yields
        SSE-formatted JSON events.
        """
        import json

        def emit_stage(stage, label, status):
            payload = {
                "type": "stage",
                "stage": stage,
                "label": label,
                "status": status
            }
            return f"data: {json.dumps(payload)}\n\n"

        def emit_result(success, data=None, error=None):
            payload = {
                "type": "result",
                "success": success
            }
            if data:
                payload["data"] = data
            if error:
                payload["error"] = error
            return f"data: {json.dumps(payload)}\n\n"

        try:
            # ==================================================
            # STEP 1 — GEMINI UNDERSTANDING
            # ==================================================
            yield emit_stage("intent_parser", "Intent Parser", "running")
            gemini_intent = self.gemini.parse(user_message)
            yield emit_stage("intent_parser", "Intent Parser", "completed")

            # ==================================================
            # STEP 2 — INTENT NORMALIZATION
            # ==================================================
            yield emit_stage("intent_normalizer", "Intent Normalizer", "running")
            intent = self.normalizer.normalize(gemini_intent)
            yield emit_stage("intent_normalizer", "Intent Normalizer", "completed")

            # ==================================================
            # STEP 2.5 — DETERMINISTIC CONSTRAINT RECOVERY
            # ==================================================

            intent = self.normalizer.recover_constraints(
                user_message,
                intent,
                self.gemini.fallback_intent
            )

            foldable_keywords = ["foldable", "fold", "flip", "form factor"]
            if any(kw in user_message.lower() for kw in foldable_keywords):
                if "required" not in intent:
                    intent["required"] = {}
                intent["required"]["form_factor"] = {"value": "foldable", "operator": "=="}

            # ==================================================
            # STEP 3 — MERCHANT CATALOG SEARCH
            # ==================================================
            yield emit_stage("catalog_search", "Catalog Search", "running")
            candidates = self.catalog_service.search_for_intent(intent)

            if not candidates:
                candidates = self.product_search.search_products(
                    category=intent.get("subcategory"),
                    max_price=intent.get("max_price"),
                    min_price=intent.get("min_price"),
                    use_cases=intent.get("use_cases", [])
                )

            # --------------------------------------------------
            # No products found
            # --------------------------------------------------
            if isinstance(candidates, pd.DataFrame):
                if candidates.empty:
                    yield emit_stage("catalog_search", "Catalog Search", "completed")
                    yield emit_stage("product_ranking", "Product Ranking", "running")
                    yield emit_stage("product_ranking", "Product Ranking", "completed")
                    yield emit_stage("recommendations_ready", "Recommendations Ready", "running")
                    yield emit_stage("recommendations_ready", "Recommendations Ready", "completed")
                    insight = self._generate_merchant_insight(intent, user_message)
                    yield emit_result(True, {"query": user_message, "intent": intent, "candidate_count": 0, "products": [], "message": "No matching products found.", "merchant_insight": insight})
                    return
            elif not candidates:
                yield emit_stage("catalog_search", "Catalog Search", "completed")
                yield emit_stage("product_ranking", "Product Ranking", "running")
                yield emit_stage("product_ranking", "Product Ranking", "completed")
                yield emit_stage("recommendations_ready", "Recommendations Ready", "running")
                yield emit_stage("recommendations_ready", "Recommendations Ready", "completed")
                insight = self._generate_merchant_insight(intent, user_message)
                yield emit_result(True, {"query": user_message, "intent": intent, "candidate_count": 0, "products": [], "message": "No matching products found.", "merchant_insight": insight})
                return

            # ==================================================
            # STEP 3.5 — UNIVERSAL PRODUCT ADAPTER
            # ==================================================
            if isinstance(candidates, list):
                candidates = pd.DataFrame(candidates)

            if candidates.empty:
                yield emit_stage("catalog_search", "Catalog Search", "completed")
                yield emit_stage("product_ranking", "Product Ranking", "running")
                yield emit_stage("product_ranking", "Product Ranking", "completed")
                yield emit_stage("recommendations_ready", "Recommendations Ready", "running")
                yield emit_stage("recommendations_ready", "Recommendations Ready", "completed")
                insight = self._generate_merchant_insight(intent, user_message)
                yield emit_result(True, {"query": user_message, "intent": intent, "candidate_count": 0, "products": [], "message": "No matching products found.", "merchant_insight": insight})
                return

            if not isinstance(candidates, pd.DataFrame):
                candidates = self.product_search.to_universal_dataframe(candidates)

            if candidates.empty:
                yield emit_stage("catalog_search", "Catalog Search", "completed")
                yield emit_stage("product_ranking", "Product Ranking", "running")
                yield emit_stage("product_ranking", "Product Ranking", "completed")
                yield emit_stage("recommendations_ready", "Recommendations Ready", "running")
                yield emit_stage("recommendations_ready", "Recommendations Ready", "completed")
                insight = self._generate_merchant_insight(intent, user_message)
                yield emit_result(True, {"query": user_message, "intent": intent, "candidate_count": 0, "products": [], "message": "No compatible products found.", "merchant_insight": insight})
                return

            yield emit_stage("catalog_search", "Catalog Search", "completed")

            # ==================================================
            # STEP 4 — UNIVERSAL V6 RANKING
            # ==================================================
            yield emit_stage("product_ranking", "Product Ranking", "running")
            ranked = self.ranker.rank(
                candidates,
                max_price=intent.get("max_price"),
                min_price=intent.get("min_price"),
                use_cases=intent.get("use_cases", []),
                preferences=intent.get("preferences", {}),
                top_n=50
            )
            yield emit_stage("product_ranking", "Product Ranking", "completed")

            # ==================================================
            # STEP 5 — CONVERT PRODUCTS FOR FRONTEND
            # ==================================================
            yield emit_stage("recommendations_ready", "Recommendations Ready", "running")
            products = []

            for _, product in ranked.iterrows():
                attributes = product.get("attributes", {})
                if not isinstance(attributes, dict):
                    try:
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

                if rating:
                    why.append(f"Rated {float(rating):.1f}/5")

                if stock > 0:
                    why.append(f"In stock ({int(stock)} available)")

                preferences = intent.get("preferences", {})
                for key, requirement in preferences.items():
                    if not isinstance(requirement, dict):
                        continue

                    actual = attributes.get(key)
                    if actual is None:
                        aliases = {
                            "camera_mp": ["camera_mp"],
                            "ram_gb": ["ram_gb"],
                            "storage_gb": ["storage_gb"],
                            "battery_hours": ["battery_hours"],
                            "battery_days": ["battery_days"],
                            "battery_mah": ["battery_mah"],
                            "capacity_liters": ["capacity_liters"],
                            "power_watts": ["power_watts"],
                            "suction_power": ["suction_power"],
                            "battery_minutes": ["battery_minutes"],
                            "wireless": ["wireless"],
                            "noise_cancellation": ["noise_cancellation"],
                            "comfort": ["comfort"],
                            "water_resistant": ["water_resistant"],
                            "gps": ["gps"],
                            "heart_rate": ["heart_rate"],
                            "cordless": ["cordless"],
                            "portable": ["portable"],
                            "laptop_compartment": ["laptop_compartment"]
                        }
                        for alias in aliases.get(key, []):
                            if alias in attributes:
                                actual = attributes[alias]
                                break

                    if actual is None:
                        continue

                    if key == "camera_mp": why.append(f"{actual} MP camera")
                    elif key == "ram_gb": why.append(f"{actual} GB RAM")
                    elif key == "storage_gb": why.append(f"{actual} GB storage")
                    elif key == "battery_hours": why.append(f"{actual}-hour battery")
                    elif key == "battery_days": why.append(f"{actual}-day battery")
                    elif key == "battery_mah": why.append(f"{actual} mAh battery")
                    elif key == "capacity_liters": why.append(f"{actual}L capacity")
                    elif key == "power_watts": why.append(f"{actual}W power")
                    elif key == "suction_power": why.append(f"{actual} suction power")
                    elif key == "battery_minutes": why.append(f"{actual}-minute battery")
                    elif key == "comfort": why.append(f"{str(actual).capitalize()} comfort")
                    elif key == "wireless":
                        if actual: why.append("Wireless connectivity")
                    elif key == "noise_cancellation":
                        if actual: why.append("Noise cancellation")
                    elif key == "water_resistant":
                        if actual: why.append("Water resistant")
                    elif key == "gps":
                        if actual: why.append("GPS included")
                    elif key == "heart_rate":
                        if actual: why.append("Heart-rate monitoring")
                    elif key == "cordless":
                        if actual: why.append("Cordless design")
                    elif key == "portable":
                        if actual: why.append("Portable design")
                    elif key == "laptop_compartment":
                        if actual: why.append("Laptop compartment included")

                product_use_cases = product.get("use_cases", [])
                if not isinstance(product_use_cases, list):
                    product_use_cases = []

                requested_use_cases = intent.get("use_cases", [])
                if isinstance(requested_use_cases, str):
                    requested_use_cases = [requested_use_cases]

                matched_use_cases = []
                for requested in requested_use_cases:
                    requested_lower = str(requested).lower()
                    for available in product_use_cases:
                        if requested_lower in str(available).lower():
                            matched_use_cases.append(str(available))

                for use_case in matched_use_cases:
                    message = f"Suitable for {use_case}"
                    if message not in why:
                        why.append(message)

                product_id = str(product.get("product_id", ""))
                try:
                    price_comparison = self.catalog_service.get_price_comparison(product_id)
                except Exception as exc:
                    print(f"⚠️ Price comparison unavailable for {product_id}: {exc}")
                    price_comparison = {
                        "has_offers": False,
                        "offer_count": 0,
                        "lowest_price": None,
                        "lowest_total": None,
                        "lowest_merchant": None,
                        "lowest_merchant_id": None,
                        "savings": 0,
                        "currency": str(product.get("currency", "INR")),
                        "offers": [],
                    }

                products.append({
                    "product_id": product_id,
                    "name": str(product.get("name", "")),
                    "brand": str(product.get("brand", "")),
                    "category": str(product.get("category", "")),
                    "subcategory": str(product.get("subcategory", "")),
                    "price": float(product.get("price", 0)),
                    "currency": str(product.get("currency", "INR")),
                    "description": str(product.get("description", "")),
                    "rating": float(product.get("rating", 0)),
                    "stock": int(product.get("stock", 0)),
                    "match_score": float(product.get("match_score", 0)),
                    "attributes": attributes,
                    "use_cases": product_use_cases,
                    "image_url": str(product.get("image_url", "")),
                    "product_url": str(product.get("product_url", "")),
                    "price_comparison": price_comparison,
                    "why": why[:8]
                })

            yield emit_stage("recommendations_ready", "Recommendations Ready", "completed")
            
            final_data = {
                "query": user_message,
                "intent": intent,
                "candidate_count": int(len(candidates)),
                "products": products
            }
            yield emit_result(True, final_data)

        except Exception as e:
            yield emit_result(False, None, str(e))

    # ==================================================
    # TERMINAL PIPELINE
    # ==================================================

    def process(
        self,
        user_message
    ):

        print("\n")

        print(
            "=" * 80
        )

        print(
            "                 RAZORPAY AI COMMERCE AGENT"
        )

        print(
            "=" * 80
        )

        print(
            "\n🗣️ USER REQUEST"
        )

        print(
            "-" * 80
        )

        print(
            user_message
        )

        # ==================================================
        # STEP 1 — GEMINI
        # ==================================================

        print(
            "\n🧠 STEP 1 — GEMINI UNDERSTANDING"
        )

        print(
            "-" * 80
        )

        gemini_intent = self.gemini.parse(
            user_message
        )

        print(
            json.dumps(
                gemini_intent,
                indent=2
            )
        )

        # ==================================================
        # STEP 2 — NORMALIZATION
        # ==================================================

        print(
            "\n🔄 STEP 2 — INTENT NORMALIZATION"
        )

        print(
            "-" * 80
        )

        intent = self.normalizer.normalize(
            gemini_intent
        )

        print(
            json.dumps(
                intent,
                indent=2
            )
        )

        # ==================================================
        # STEP 3 — MERCHANT CATALOG SEARCH
        # ==================================================

        print(
            "\n🛒 STEP 3 — MERCHANT CATALOG SEARCH"
        )

        print(
            "-" * 80
        )

        candidates = (
            self.product_search.search_from_intent(
                intent
            )
        )

        print(
            f"Merchant candidates: "
            f"{len(candidates)}"
        )

        if candidates.empty:

            print(
                "\n❌ No matching products found."
            )

            return

        # ==================================================
        # STEP 3.5 — UNIVERSAL ADAPTER
        # ==================================================

        candidates = (
            self.product_search
            .to_universal_dataframe(
                candidates
            )
        )

        print(
            f"Universal candidates: "
            f"{len(candidates)}"
        )

        if candidates.empty:

            print(
                "\n❌ No compatible products found."
            )

            return

        # ==================================================
        # STEP 4 — UNIVERSAL RANKING
        # ==================================================

        print(
            "\n📊 STEP 4 — UNIVERSAL RANKING"
        )

        print(
            "-" * 80
        )

        ranked = self.ranker.rank(

            candidates,

            max_price=intent.get(
                "max_price"
            ),

            min_price=intent.get(
                "min_price"
            ),

            use_cases=intent.get(
                "use_cases",
                []
            ),

            preferences=intent.get(
                "preferences",
                {}
            ),

            top_n=50
        )

        # ==================================================
        # STEP 5 — RECOMMENDATIONS
        # ==================================================

        print(
            "\n🏆 STEP 5 — RECOMMENDATIONS"
        )

        print(
            "-" * 80
        )

        for i, (_, product) in enumerate(
            ranked.iterrows(),
            start=1
        ):

            print(
                f"\n#{i} {product['name']}"
            )

            print(
                f"   Category: "
                f"{product.get('subcategory', '')}"
            )

            print(
                f"   Price: "
                f"₹{product['price']}"
            )

            print(
                f"   Rating: "
                f"{product['rating']}/5"
            )

            print(
                f"   Stock: "
                f"{product['stock']}"
            )

            print(
                f"   Match Score: "
                f"{product.get('match_score', 0)}%"
            )

            print(
                f"   Product ID: "
                f"{product.get('product_id', '')}"
            )

            if product.get(
                "product_url",
                ""
            ):

                print(
                    f"   Product URL: "
                    f"{product['product_url']}"
                )

        print(
            "\n" + "=" * 80
        )


# ======================================================
# TERMINAL TEST
# ======================================================

if __name__ == "__main__":

    agent = RazorPayCommerceAgent()

    test_requests = [

        "bro i wnt a gud wireless hp under 3k for travl n online cls battery shud be long",

        "need laptop for coding around 60k with 16gb ram and good battery",

        "show me comfortable running shoes below 4k",

        "i need a phone under 20k with best camera"
    ]

    for request in test_requests:

        agent.process(
            request
        )