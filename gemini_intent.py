import json
import os
import re

from dotenv import load_dotenv
from google import genai
from groq import Groq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# RAZORGUARD AI INTENT PARSER
# ============================================================
#
# Provider priority:
#
#   1. Gemini
#   2. Groq
#   3. Ollama
#   4. Rule-based fallback
#
# All providers return the SAME normalized intent structure.
#
# ============================================================


class GeminiIntentParser:

    def __init__(self):

        # ----------------------------------------------------
        # Gemini
        # ----------------------------------------------------

        self.gemini_api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        self.gemini_client = None

        self.gemini_model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        if self.gemini_api_key:

            try:

                self.gemini_client = genai.Client(
                    api_key=self.gemini_api_key
                )

                print("Gemini API configured.")
                print(f"   Model: {self.gemini_model}")

            except Exception as error:

                print(
                    "WARNING: Gemini initialization failed."
                )

                print(
                    f"   Reason: {error}"
                )

        else:

            print(
                "WARNING: GEMINI_API_KEY not configured."
            )

        # ----------------------------------------------------
        # Groq
        # ----------------------------------------------------

        self.groq_api_key = os.getenv(
            "GROQ_API_KEY"
        )

        self.groq_client = None

        self.groq_model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        if self.groq_api_key:

            try:

                # IMPORTANT:
                # Use the official Groq SDK.
                #
                # The previous implementation used urllib
                # directly and produced HTTP 403 / 1010 even
                # though the same key worked with the SDK.

                self.groq_client = Groq(
                    api_key=self.groq_api_key
                )

                print("Groq API configured.")
                print(f"   Model: {self.groq_model}")

            except Exception as error:

                print(
                    "WARNING: Groq initialization failed."
                )

                print(
                    f"   Reason: {error}"
                )

        else:

            print(
                "WARNING: GROQ_API_KEY not configured."
            )

        # ----------------------------------------------------
        # Ollama
        # ----------------------------------------------------

        self.ollama_url = os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434/api/chat"
        )

        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "45"))

        self.ollama_model = os.getenv(
            "OLLAMA_MODEL",
            "gemma3:4b"
        )

        self.ollama_enabled = self._env_bool(
            "OLLAMA_ENABLED",
            True
        )

        if self.ollama_enabled:

                print("Ollama fallback enabled.")
                print(f"   Model: {self.ollama_model}")

        else:

            print(
                "WARNING: Ollama fallback disabled."
            )

        print()

    # ========================================================
    # ENVIRONMENT HELPERS
    # ========================================================

    @staticmethod
    def _env_bool(
        name,
        default=True
    ):

        value = os.getenv(name)

        if value is None:

            return default

        return value.strip().lower() in (
            "1",
            "true",
            "yes",
            "y",
            "on"
        )

    # ========================================================
    # MAIN PARSER
    # ========================================================

    def parse(
        self,
        user_message
    ):

        user_message = str(
            user_message or ""
        ).strip()

        if not user_message:

            return self._normalize(
                self.fallback_intent("")
            )

        # ----------------------------------------------------
        # PROVIDER 1 — GEMINI
        # ----------------------------------------------------

        if self.gemini_client:

            try:

                print(
                    "\nTrying Gemini..."
                )

                result = self._parse_with_gemini(
                    user_message
                )

                result = self._normalize(
                    result
                )

                result = self._normalize_product_category(
                    result,
                    user_message
                )

                print(
                    "Intent generated by Gemini."
                )

                return result

            except Exception as error:

                print(
                    "\nGemini unavailable."
                )

                print(
                    f"   Reason: {error}"
                )

        # ----------------------------------------------------
        # PROVIDER 2 — GROQ
        # ----------------------------------------------------

        if self.groq_client:

            try:

                print(
                    "\nTrying Groq..."
                )

                result = self._parse_with_groq(
                    user_message
                )

                result = self._normalize(
                    result
                )

                result = self._normalize_product_category(
                    result,
                    user_message
                )

                print(
                    "Intent generated by Groq."
                )

                return result

            except Exception as error:

                print(
                    "\nGroq unavailable."
                )

                print(
                    f"   Reason: {error}"
                )

        # ----------------------------------------------------
        # PROVIDER 3 — OLLAMA
        # ----------------------------------------------------

        if self.ollama_enabled:

            try:

                print(
                    "\nTrying Ollama..."
                )

                result = self._parse_with_ollama(
                    user_message
                )

                result = self._normalize(
                    result
                )

                result = self._normalize_product_category(
                    result,
                    user_message
                )

                print(
                    "Intent generated by Ollama."
                )

                return result

            except Exception as error:

                print(
                    "\nOllama unavailable."
                )

                print(
                    f"   Reason: {error}"
                )

        # ----------------------------------------------------
        # PROVIDER 4 — RULE-BASED FALLBACK
        # ----------------------------------------------------

        print(
            "\nUsing rule-based fallback parser..."
        )

        fallback = self.fallback_intent(
            user_message
        )

        fallback = self._normalize(
            fallback
        )

        fallback = self._normalize_product_category(
            fallback,
            user_message
        )

        print(
            "Rule-based intent generated."
        )

        return fallback

    # ========================================================
    # COMMON AI PROMPT
    # ========================================================

    def _build_prompt(
        self,
        user_message
    ):

        return f"""
You are the intent-understanding component of an
AI e-commerce shopping agent called RazorGuard AI.

Convert the user's natural-language shopping request
into JSON.

The user may use:

- spelling mistakes
- grammar mistakes
- abbreviations
- slang
- Hinglish
- informal language
- short messages

Understand the intended meaning.

Return ONLY valid JSON.

Required structure:

{{
  "category": "string",
  "subcategory": "string",
  "max_price": number or null,
  "min_price": number or null,
  "use_cases": [],
  "required": {{}},
  "preferences": {{}}
}}

Rules:

1. Identify the product category.

2. Identify the most specific product subcategory when
   possible.

3. Extract the user's budget.

4. Extract important use cases.

5. Distinguish between HARD CONSTRAINTS and SOFT PREFERENCES.

6. Hard Constraints (Required) MUST use this structure:

"required": {{
    "attribute_name": {{
        "value": value,
        "operator": "==" | ">=" | "<="
    }}
}}
Use "required" for strict conditions (e.g. "at least 16GB RAM" -> ">=" 16, "512GB storage" -> "==" 512).

7. Soft Preferences MUST use this structure:

"preferences": {{
    "attribute_name": {{
        "value": value,
        "importance": "low|medium|high|critical",
        "direction": "match|maximize|minimize"
    }}
}}
Use "preferences" for soft ranking signals (e.g. "best processor" -> maximize).

8. Separate product type from product characteristics.

Product types belong in:
- category
- subcategory

Characteristics belong in:
- preferences

Examples of characteristics:

- wireless
- Bluetooth
- lightweight
- comfortable
- noise cancellation
- battery life
- RAM (ram_gb)
- storage (storage_gb)
- processor
- camera quality (camera_mp)
- style
- waterproof
- GPS
- 5G
- cordless

8. Do NOT create a new subcategory by combining
   a product characteristic with a product type.

Example:

User:
"wireless headphones"

Correct:

"subcategory": "Headphones"

and:

"wireless": {{
    "value": true,
    "importance": "critical",
    "direction": "match"
}}

9. "wireless headphones" must NOT become:

"subcategory": "Wireless Headphones"

10. For descriptive requirements such as:

"casual shirt"

use:

"subcategory": "Shirts"

and:

"style": {{
    "value": "casual",
    "importance": "critical",
    "direction": "match"
}}

11. Do NOT recommend products.

12. Do NOT invent product names.

13. Do NOT invent prices.

14. Do NOT invent requirements that the user did not ask for.

15. Preserve explicit user requirements even when
    expressed informally.

16. Understand abbreviations such as:

hp = headphones
ph = phone
mob = mobile
cls = classes
travl = travel

17. Recognize these product types when appropriate:

headphones
smartphones
laptops
smartwatches
running shoes
backpacks
watches
shirts
t-shirts
air fryers
vacuum cleaners
fitness equipment

18. For:

"best"
"highest"
"maximum"
"longest"

use:

direction = "maximize"

19. For exact requirements such as:

"16GB RAM"

use:

direction = "match"

20. For boolean requirements such as:

wireless
GPS
5G
water resistant
cordless

use:

direction = "match"

21. Use these canonical preference names whenever applicable:

RAM -> ram_gb
battery life -> battery_hours
GPS -> gps
5G -> 5g
camera quality -> camera_mp
storage -> storage_gb
noise cancellation -> noise_cancellation
waterproof / water resistant -> water_resistant

22. For numeric RAM requirements such as:

"16GB RAM"

return:

"ram_gb": {{
    "value": 16,
    "importance": "critical",
    "direction": "match"
}}

23. For battery requirements such as:

"long battery"
"good battery"
"best battery"

return:

"battery_hours": {{
    "value": null,
    "importance": "high",
    "direction": "maximize"
}}

24. For GPS return:

"gps": {{
    "value": true,
    "importance": "high",
    "direction": "match"
}}

25. For camera quality such as:

"best camera"

return:

"camera_mp": {{
    "value": null,
    "importance": "critical",
    "direction": "maximize"
}}

26. Return valid JSON only.

User request:

{user_message}
"""

    # ========================================================
    # GEMINI
    # ========================================================

    def _parse_with_gemini(
        self,
        user_message
    ):

        if not self.gemini_client:

            raise RuntimeError(
                "Gemini client is not configured."
            )

        prompt = self._build_prompt(
            user_message
        )

        response = self.gemini_client.models.generate_content(
            model=self.gemini_model,
            contents=prompt
        )

        if not response:

            raise ValueError(
                "Gemini returned an empty response."
            )

        text = getattr(
            response,
            "text",
            None
        )

        if not text:

            raise ValueError(
                "Gemini response did not contain text."
            )

        return self._parse_json_response(
            text
        )

    # ========================================================
    # GROQ — OFFICIAL SDK
    # ========================================================

    def _parse_with_groq(
        self,
        user_message
    ):

        if not self.groq_client:

            raise RuntimeError(
                "Groq client is not configured."
            )

        prompt = self._build_prompt(
            user_message
        )

        response = self.groq_client.chat.completions.create(

            model=self.groq_model,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise JSON intent "
                        "parser for RazorGuard AI. "
                        "Return valid JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0,

            response_format={
                "type": "json_object"
            }
        )

        if not response:

            raise ValueError(
                "Groq returned an empty response."
            )

        choices = getattr(
            response,
            "choices",
            None
        )

        if not choices:

            raise ValueError(
                "Groq returned no choices."
            )

        message = choices[0].message

        if not message:

            raise ValueError(
                "Groq returned an empty message."
            )

        text = getattr(
            message,
            "content",
            None
        )

        if not text:

            raise ValueError(
                "Groq returned empty content."
            )

        return self._parse_json_response(
            text
        )

    # ========================================================
    # OLLAMA
    # ========================================================

    def _parse_with_ollama(
        self,
        user_message
    ):

        prompt = f"""
Convert this shopping request into ONLY the following JSON structure.

{{
  "category": "string",
  "subcategory": "string",
  "max_price": null,
  "min_price": null,
  "use_cases": [],
  "preferences": {{}}
}}

STRICT RULES:

- Return ONLY JSON.
- preferences MUST be an OBJECT, never a list.
- Each preference MUST have:
  value, importance, direction.
- Do not recommend products.
- Do not invent requirements.
- Keep the product type in subcategory.
- Put characteristics such as wireless, GPS, RAM and battery
  inside preferences.
- Use canonical preference names:
  RAM -> ram_gb
  battery life -> battery_hours
  GPS -> gps
  5G -> 5g
  camera quality -> camera_mp
  storage -> storage_gb
  noise cancellation -> noise_cancellation
  waterproof / water resistant -> water_resistant

Examples:

Wireless headphones:
"subcategory": "Headphones"

"wireless": {{
  "value": true,
  "importance": "critical",
  "direction": "match"
}}

Long battery:
"battery_hours": {{
  "value": null,
  "importance": "high",
  "direction": "maximize"
}}

16GB RAM:
"ram_gb": {{
  "value": 16,
  "importance": "critical",
  "direction": "match"
}}

GPS:
"gps": {{
  "value": true,
  "importance": "high",
  "direction": "match"
}}

Best camera:
"camera_mp": {{
  "value": null,
  "importance": "critical",
  "direction": "maximize"
}}

USER REQUEST:
{user_message}
"""

        payload = {
            "model": self.ollama_model,

            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are RazorGuard AI's shopping intent parser. "
                        "Return ONLY the requested JSON object. "
                        "Do not explain. Do not recommend products. "
                        "Do not output reasoning or thinking."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            "stream": False,

            # Ollama structured-output mode.
            "format": "json",

            # Qwen may expose reasoning separately.
            # We only want the final JSON content.
            "think": False,

            "options": {
                "temperature": 0,
                "num_predict": 220
            }
        }

        response = self._http_json_request(
            url=self.ollama_url,
            payload=payload,
            headers={
                "Content-Type": "application/json"
            },
            timeout=self.ollama_timeout
        )

        if not isinstance(response, dict):
            raise ValueError("Ollama returned an invalid response object.")

        message = response.get("message") or {}

        if not isinstance(message, dict):
            raise ValueError("Ollama returned an invalid message object.")

        # Normally the JSON is here.
        text = message.get("content")

        if text:
            return self._parse_json_response(text)

        # Some Ollama/Qwen configurations can put useful output in
        # alternate fields. Try them before declaring failure.
        for key in ("response", "output", "text"):
            candidate = response.get(key)

            if candidate:
                return self._parse_json_response(candidate)

        # Do NOT parse the "thinking" field as intent JSON.
        thinking = message.get("thinking")

        if thinking:
            raise ValueError(
                "Ollama returned thinking but no final content. "
                "The model did not produce the required JSON output."
            )

        raise ValueError(
            "Ollama returned empty content."
        )

    # ========================================================
    # HTTP HELPER
    # ========================================================

    @staticmethod
    def _http_json_request(
        url,
        payload,
        headers=None,
        timeout=30
    ):

        import urllib.error
        import urllib.request

        data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers or {},
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=timeout
            ) as response:

                raw = response.read().decode(
                    "utf-8"
                )

                if not raw:

                    raise ValueError(
                        "Empty HTTP response."
                    )

                return json.loads(
                    raw
                )

        except urllib.error.HTTPError as error:

            body = ""

            try:

                body = error.read().decode(
                    "utf-8",
                    errors="replace"
                )

            except Exception:

                pass

            raise RuntimeError(
                f"HTTP {error.code}: {body}"
            ) from error

        except urllib.error.URLError as error:

            raise RuntimeError(
                f"Connection failed: {error.reason}"
            ) from error

    # ========================================================
    # JSON PARSER
    # ========================================================

    @staticmethod
    def _parse_json_response(
        text
    ):

        text = str(
            text or ""
        ).strip()

        if not text:

            raise ValueError(
                "AI returned empty text."
            )

        # ----------------------------------------------------
        # Remove markdown fences
        # ----------------------------------------------------

        if text.startswith("```"):

            text = re.sub(
                r"^```(?:json)?",
                "",
                text,
                flags=re.IGNORECASE
            )

            text = re.sub(
                r"```$",
                "",
                text
            )

            text = text.strip()

        # ----------------------------------------------------
        # Direct JSON
        # ----------------------------------------------------

        try:

            return json.loads(
                text
            )

        except json.JSONDecodeError:

            pass

        # ----------------------------------------------------
        # Try extracting JSON object
        # ----------------------------------------------------

        start = text.find("{")

        end = text.rfind("}")

        if start != -1 and end != -1:

            candidate = text[
                start:end + 1
            ]

            try:

                return json.loads(
                    candidate
                )

            except json.JSONDecodeError:

                pass

        raise ValueError(
            "AI returned invalid JSON:\n"
            + text
        )

    # ========================================================
    # RULE-BASED FALLBACK
    # ========================================================

    def fallback_intent(
        self,
        user_message
    ):

        text = str(
            user_message or ""
        ).lower()

        intent = {

            "category": None,

            "subcategory": None,

            "max_price": None,

            "min_price": None,

            "use_cases": [],

            "required": {},

            "preferences": {}

        }

        # ====================================================
        # PRODUCT TYPE
        # ====================================================

        # ----------------------------------------------------
        # HEADPHONES
        # ----------------------------------------------------

        if any(x in text for x in [

            "headphone",
            "headphones",
            "wireless hp",
            "wireless headphone",
            "earphone",
            "earphones",
            "earbuds",
            "airpods",
            "audio"

        ]):

            intent["category"] = "Electronics"

            intent["subcategory"] = "Headphones"

        # ----------------------------------------------------
        # LAPTOPS
        # ----------------------------------------------------

        elif any(x in text for x in [

            "laptop",
            "laptops",
            "notebook"

        ]):

            intent["category"] = "Electronics"

            intent["subcategory"] = "Laptops"

        # ----------------------------------------------------
        # SMARTPHONES
        # ----------------------------------------------------

        elif any(x in text for x in [

            "phone",
            "mobile",
            "smartphone",
            "smart phone"

        ]):

            intent["category"] = "Electronics"

            intent["subcategory"] = "Smartphones"

        # ----------------------------------------------------
        # T-SHIRTS
        # ----------------------------------------------------

        elif any(x in text for x in [

            "t shirt",
            "t-shirt",
            "tshirt",
            "tee"

        ]):

            intent["category"] = "Fashion"

            intent["subcategory"] = "T-Shirts"

        # ----------------------------------------------------
        # SHIRTS
        # ----------------------------------------------------

        elif any(x in text for x in [

            "shirt",
            "shirts",
            "formal shirt",
            "casual shirt",
            "dress shirt"

        ]):

            intent["category"] = "Fashion"

            intent["subcategory"] = "Shirts"

        # ----------------------------------------------------
        # RUNNING SHOES
        # ----------------------------------------------------

        elif any(x in text for x in [

            "running shoes",
            "running shoe"

        ]):

            intent["category"] = "Fashion"

            intent["subcategory"] = "Running Shoes"

        # ----------------------------------------------------
        # GENERAL SHOES
        # ----------------------------------------------------

        elif "shoes" in text:

            intent["category"] = "Fashion"

            intent["subcategory"] = "Running Shoes"

        # ----------------------------------------------------
        # SMARTWATCH
        # ----------------------------------------------------

        elif any(x in text for x in [

            "smartwatch",
            "smart watch",
            "fitness watch"

        ]):

            intent["category"] = "Electronics"

            intent["subcategory"] = "Smartwatches"

        # ----------------------------------------------------
        # BACKPACK
        # ----------------------------------------------------

        elif any(x in text for x in [

            "backpack",
            "back pack",
            "bag pack"

        ]):

            intent["category"] = "Fashion"

            intent["subcategory"] = "Backpacks"

        # ----------------------------------------------------
        # BAG
        # ----------------------------------------------------

        elif "bag" in text:

            intent["category"] = "Fashion"

            intent["subcategory"] = "Backpacks"

        # ----------------------------------------------------
        # WATCH
        # ----------------------------------------------------

        elif any(x in text for x in [

            "watch",
            "wrist watch"

        ]):

            intent["category"] = "Fashion"

            intent["subcategory"] = "Watches"

        # ----------------------------------------------------
        # AIR FRYER
        # ----------------------------------------------------

        elif any(x in text for x in [

            "air fryer",
            "airfryer"

        ]):

            intent["category"] = "Home"

            intent["subcategory"] = "Air Fryers"

        # ----------------------------------------------------
        # VACUUM
        # ----------------------------------------------------

        elif any(x in text for x in [

            "vacuum",
            "vacuum cleaner",
            "cleaner"

        ]):

            intent["category"] = "Home"

            intent["subcategory"] = "Vacuum Cleaners"

        # ----------------------------------------------------
        # FITNESS
        # ----------------------------------------------------

        elif any(x in text for x in [

            "fitness",
            "gym equipment",
            "gym kit",
            "resistance band",
            "exercise equipment",
            "workout equipment"

        ]):

            intent["category"] = "Sports"

            intent["subcategory"] = "Fitness Equipment"

        # ====================================================
        # PRICE EXTRACTION
        # ====================================================

        price_match = re.search(

            r"(?:under|below|around|upto|up to|within)"
            r"\s*₹?\s*"
            r"([\d,]+(?:\.\d+)?)"
            r"\s*(k|K)?",

            text

        )

        if price_match:

            val_str = price_match.group(1).replace(",", "")
            value = float(val_str)

            suffix = price_match.group(2)

            if suffix:

                value *= 1000

            intent["max_price"] = value

        # ----------------------------------------------------
        # Generic K price
        # ----------------------------------------------------

        if intent["max_price"] is None:

            k_match = re.search(

                r"₹?\s*"
                r"([\d,]+(?:\.\d+)?)"
                r"\s*k\b",

                text

            )

            if k_match:

                val_str = k_match.group(1).replace(",", "")
                intent["max_price"] = float(val_str) * 1000

        # ----------------------------------------------------
        # Exact rupee number
        # ----------------------------------------------------

        if intent["max_price"] is None:

            rupee_match = re.search(

                r"₹\s*([\d,]+)",

                text

            )

            if rupee_match:

                value = (
                    rupee_match
                    .group(1)
                    .replace(",", "")
                )

                intent["max_price"] = float(
                    value
                )

        # ====================================================
        # USE CASES
        # ====================================================

        use_cases = []

        if any(x in text for x in [

            "travel",
            "travelling",
            "traveling",
            "travl"

        ]):

            use_cases.append(
                "travel"
            )

        if any(x in text for x in [

            "online class",
            "online classes",
            "classes",
            "cls"

        ]):

            use_cases.append(
                "online classes"
            )

        if any(x in text for x in [

            "gaming",
            "game"

        ]):

            use_cases.append(
                "gaming"
            )

        if any(x in text for x in [

            "coding",
            "programming",
            "developer",
            "development"

        ]):

            use_cases.append(
                "coding"
            )

        if any(x in text for x in [

            "running",
            "jogging"

        ]):

            use_cases.append(
                "running"
            )

        if any(x in text for x in [

            "gym",
            "workout",
            "exercise",
            "fitness"

        ]):

            use_cases.append(
                "fitness"
            )

        intent["use_cases"] = list(
            dict.fromkeys(
                use_cases
            )
        )

        # ====================================================
        # PREFERENCES
        # ====================================================

        # ----------------------------------------------------
        # WIRELESS
        # ----------------------------------------------------

        if any(x in text for x in [

            "wireless",
            "bluetooth"

        ]):

            intent["preferences"][
                "wireless"
            ] = {

                "value": True,

                "importance": "critical",

                "direction": "match"

            }

        # ----------------------------------------------------
        # BATTERY
        # ----------------------------------------------------

        if any(x in text for x in [

            "long battery",
            "long battery life",
            "good battery",
            "best battery",
            "battery should be long",
            "battery shud be long",
            "battery life"

        ]):

            intent["preferences"][
                "battery_hours"
            ] = {

                "value": None,

                "importance": "high",

                "direction": "maximize"

            }

        # ----------------------------------------------------
        # RAM
        # ----------------------------------------------------

        ram_match = re.search(

            r"(?:at least |min |minimum )?(\d+)\s*gb\s*ram",

            text

        )

        if ram_match:

            ram_value = int(
                ram_match.group(1)
            )

            is_min = "at least" in ram_match.group(0) or "min" in ram_match.group(0)

            if is_min:
                intent["required"]["ram_gb"] = {
                    "value": ram_value,
                    "operator": ">="
                }
            else:
                intent["required"]["ram_gb"] = {
                    "value": ram_value,
                    "operator": "=="
                }

        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        if any(x in text for x in [

            "best camera",
            "best camera quality",
            "good camera",
            "excellent camera",
            "best camera phone",
            "camera quality"

        ]):

            intent["preferences"][
                "camera_mp"
            ] = {

                "value": None,

                "importance": "critical",

                "direction": "maximize"

            }

        # ----------------------------------------------------
        # COMFORT
        # ----------------------------------------------------

        if any(x in text for x in [

            "comfortable",
            "comfort"

        ]):

            intent["preferences"][
                "comfort"
            ] = {

                "value": True,

                "importance": "high",

                "direction": "match"

            }

        # ----------------------------------------------------
        # NOISE CANCELLATION
        # ----------------------------------------------------

        if any(x in text for x in [

            "noise cancellation",
            "noise cancelling",
            "anc"

        ]):

            intent["preferences"][
                "noise_cancellation"
            ] = {

                "value": True,

                "importance": "high",

                "direction": "match"

            }

        # ----------------------------------------------------
        # STORAGE
        # ----------------------------------------------------

        storage_match = re.search(

            r"(?:at least |min |minimum )?(\d+)\s*gb\s*(?:storage|rom)",

            text

        )

        if storage_match:

            storage_value = int(
                storage_match.group(1)
            )

            is_min = "at least" in storage_match.group(0) or "min" in storage_match.group(0)

            if is_min:
                intent["required"]["storage_gb"] = {
                    "value": storage_value,
                    "operator": ">="
                }
            else:
                intent["required"]["storage_gb"] = {
                    "value": storage_value,
                    "operator": "=="
                }

        elif any(x in text for x in ["highest storage", "max storage", "maximum storage"]):

            intent["preferences"]["storage_gb"] = {
                "value": None,
                "importance": "critical",
                "direction": "maximize"
            }

        # ----------------------------------------------------
        # 5G
        # ----------------------------------------------------

        if any(x in text for x in [

            "5g",
            "5 g"

        ]):

            intent["preferences"][
                "5g"
            ] = {

                "value": True,

                "importance": "high",

                "direction": "match"

            }

        # ----------------------------------------------------
        # GPS
        # ----------------------------------------------------

        if "gps" in text:

            intent["preferences"][
                "gps"
            ] = {

                "value": True,

                "importance": "high",

                "direction": "match"

            }

        # ----------------------------------------------------
        # WATER RESISTANT
        # ----------------------------------------------------

        if any(x in text for x in [

            "water resistant",
            "waterproof"

        ]):

            intent["preferences"][
                "water_resistant"
            ] = {

                "value": True,

                "importance": "high",

                "direction": "match"

            }

        # ----------------------------------------------------
        # CORDLESS
        # ----------------------------------------------------

        if "cordless" in text:

            intent["preferences"][
                "cordless"
            ] = {

                "value": True,

                "importance": "high",

                "direction": "match"

            }

        return intent
        # ========================================================
    # NORMALIZE OUTPUT
    # ========================================================

    @staticmethod
    def _normalize(data):

        if not isinstance(data, dict):
            data = {}

        result = {
            "category": data.get("category"),
            "subcategory": data.get("subcategory"),
            "max_price": data.get("max_price"),
            "min_price": data.get("min_price"),
            "use_cases": data.get("use_cases", []),
            "preferences": data.get("preferences", {})
        }

        # ----------------------------------------------------
        # PRICE NORMALIZATION
        # ----------------------------------------------------

        for key in [
            "max_price",
            "min_price"
        ]:

            value = result[key]

            if value is not None:

                try:
                    result[key] = float(value)

                except (
                    ValueError,
                    TypeError
                ):

                    result[key] = None

        # ----------------------------------------------------
        # USE CASES
        # ----------------------------------------------------

        if not isinstance(
            result["use_cases"],
            list
        ):

            result["use_cases"] = [
                result["use_cases"]
            ]

        result["use_cases"] = [
            str(x).strip()
            for x in result["use_cases"]
            if x is not None
            and str(x).strip()
        ]

        result["use_cases"] = list(
            dict.fromkeys(
                result["use_cases"]
            )
        )

        # ----------------------------------------------------
        # PREFERENCES
        # ----------------------------------------------------

        if not isinstance(
            result["preferences"],
            dict
        ):

            result["preferences"] = {}

        normalized_preferences = {}

        # Canonical preference names.
        # This protects RazorGuard from small naming
        # differences between Gemini/Groq/Ollama.

        preference_aliases = {

            "ram": "ram_gb",
            "ram gb": "ram_gb",
            "ram_gb": "ram_gb",

            "battery life": "battery_hours",
            "battery_life": "battery_hours",
            "battery": "battery_hours",
            "battery hours": "battery_hours",
            "battery_hours": "battery_hours",

            "gps": "gps",

            "5g": "5g",
            "5 g": "5g",

            "camera": "camera_mp",
            "camera quality": "camera_mp",
            "camera_quality": "camera_mp",
            "camera mp": "camera_mp",
            "camera_mp": "camera_mp",

            "storage": "storage_gb",
            "storage gb": "storage_gb",
            "storage_gb": "storage_gb",
            "rom": "storage_gb",

            "noise cancellation":
                "noise_cancellation",

            "noise cancelling":
                "noise_cancellation",

            "noise_cancellation":
                "noise_cancellation",

            "waterproof":
                "water_resistant",

            "water resistant":
                "water_resistant",

            "water_resistant":
                "water_resistant",

            "wireless": "wireless",

            "bluetooth": "wireless",

            "cordless": "cordless",

            "comfort": "comfort",

            "comfortable": "comfort",

            "style": "style"
        }

        for key, value in result[
            "preferences"
        ].items():

            original_key = str(
                key
            ).strip()

            normalized_key = (
                original_key.lower()
                .replace("-", " ")
            )

            canonical_key = preference_aliases.get(
                normalized_key,
                original_key
            )

            # ------------------------------------------------
            # Already structured
            # ------------------------------------------------

            if isinstance(
                value,
                dict
            ):

                preference = dict(
                    value
                )

            # ------------------------------------------------
            # Simple value
            # ------------------------------------------------

            else:

                preference = {

                    "value": value,

                    "importance": "medium",

                    "direction": "match"
                }

            # ------------------------------------------------
            # Default importance
            # ------------------------------------------------

            importance = str(
                preference.get(
                    "importance",
                    "medium"
                )
            ).lower().strip()

            if importance not in [
                "low",
                "medium",
                "high",
                "critical"
            ]:

                importance = "medium"

            preference[
                "importance"
            ] = importance

            # ------------------------------------------------
            # Default direction
            # ------------------------------------------------

            direction = str(
                preference.get(
                    "direction",
                    "match"
                )
            ).lower().strip()

            if direction not in [
                "match",
                "maximize",
                "minimize"
            ]:

                direction = "match"

            preference[
                "direction"
            ] = direction

            # ------------------------------------------------
            # Make sure value exists
            # ------------------------------------------------

            if "value" not in preference:

                preference[
                    "value"
                ] = None

            # ------------------------------------------------
            # Merge duplicate aliases
            # ------------------------------------------------

            if canonical_key in normalized_preferences:

                existing = normalized_preferences[
                    canonical_key
                ]

                # Prefer a more specific value.
                if (
                    existing.get("value") is None
                    and preference.get("value") is not None
                ):

                    existing["value"] = (
                        preference["value"]
                    )

                # Prefer higher importance.
                importance_rank = {
                    "low": 1,
                    "medium": 2,
                    "high": 3,
                    "critical": 4
                }

                if (
                    importance_rank.get(
                        preference["importance"],
                        2
                    )
                    >
                    importance_rank.get(
                        existing["importance"],
                        2
                    )
                ):

                    existing["importance"] = (
                        preference["importance"]
                    )

                # Preserve maximize/minimize if supplied.
                if preference["direction"] != "match":

                    existing["direction"] = (
                        preference["direction"]
                    )

            else:

                normalized_preferences[
                    canonical_key
                ] = preference

        result[
            "preferences"
        ] = normalized_preferences

        return result

    # ========================================================
    # PRODUCT CATEGORY NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_product_category(
        data,
        user_message=""
    ):

        user_text = str(
            user_message or ""
        ).lower()

        category = str(
            data.get("category") or ""
        ).strip().lower()

        subcategory = str(
            data.get("subcategory") or ""
        ).strip().lower()

        # ----------------------------------------------------
        # ELECTRONICS
        # ----------------------------------------------------

        electronics_subcategories = {

            "headphones":
                "Headphones",

            "headphone":
                "Headphones",

            "earphones":
                "Headphones",

            "earbuds":
                "Headphones",

            "laptops":
                "Laptops",

            "laptop":
                "Laptops",

            "smartphones":
                "Smartphones",

            "smartphone":
                "Smartphones",

            "phones":
                "Smartphones",

            "phone":
                "Smartphones",

            "smartwatches":
                "Smartwatches",

            "smartwatch":
                "Smartwatches"
        }

        if subcategory in electronics_subcategories:

            data["category"] = "Electronics"

            data["subcategory"] = (
                electronics_subcategories[
                    subcategory
                ]
            )

            return data

        # ----------------------------------------------------
        # T-SHIRTS
        # ----------------------------------------------------

        tshirt_terms = [
            "t-shirt",
            "t shirt",
            "tshirt",
            "tee",
            "tees"
        ]

        if (
            category in tshirt_terms
            or
            subcategory in tshirt_terms
            or
            any(
                term in user_text
                for term in tshirt_terms
            )
        ):

            data["category"] = "Fashion"

            data["subcategory"] = "T-Shirts"

            return data

        # ----------------------------------------------------
        # SHIRTS
        # ----------------------------------------------------

        shirt_terms = [
            "shirt",
            "shirts",
            "formal shirt",
            "casual shirt",
            "dress shirt"
        ]

        if (
            category in shirt_terms
            or
            subcategory in shirt_terms
            or
            "shirt" in user_text
        ):

            # Don't turn a T-shirt into Shirts.

            if not any(
                term in user_text
                for term in tshirt_terms
            ):

                data["category"] = "Fashion"

                data["subcategory"] = "Shirts"

                return data

        # ----------------------------------------------------
        # RUNNING SHOES
        # ----------------------------------------------------

        if any(
            term in user_text
            for term in [
                "running shoe",
                "running shoes",
                "jogging shoe",
                "jogging shoes"
            ]
        ):

            data["category"] = "Fashion"

            data["subcategory"] = "Running Shoes"

            return data

        # ----------------------------------------------------
        # GENERAL SHOES
        # ----------------------------------------------------

        if (
            "shoes" in user_text
            and
            not data.get("subcategory")
        ):

            data["category"] = "Fashion"

            data["subcategory"] = "Running Shoes"

            return data

        # ----------------------------------------------------
        # SMARTWATCH
        # ----------------------------------------------------

        if any(
            term in user_text
            for term in [
                "smartwatch",
                "smart watch",
                "fitness watch"
            ]
        ):

            data["category"] = "Electronics"

            data["subcategory"] = "Smartwatches"

            return data

        # ----------------------------------------------------
        # BACKPACK
        # ----------------------------------------------------

        if any(
            term in user_text
            for term in [
                "backpack",
                "back pack",
                "bag pack"
            ]
        ):

            data["category"] = "Fashion"

            data["subcategory"] = "Backpacks"

            return data

        # ----------------------------------------------------
        # BAG
        # ----------------------------------------------------

        if "bag" in user_text:

            data["category"] = "Fashion"

            data["subcategory"] = "Backpacks"

            return data

        # ----------------------------------------------------
        # WATCH
        # ----------------------------------------------------

        if any(
            term in user_text
            for term in [
                "watch",
                "wrist watch"
            ]
        ):

            # Don't overwrite smartwatch.

            if not any(
                term in user_text
                for term in [
                    "smartwatch",
                    "smart watch"
                ]
            ):

                data["category"] = "Fashion"

                data["subcategory"] = "Watches"

                return data

        # ----------------------------------------------------
        # AIR FRYER
        # ----------------------------------------------------

        if any(
            term in user_text
            for term in [
                "air fryer",
                "airfryer"
            ]
        ):

            data["category"] = "Home"

            data["subcategory"] = "Air Fryers"

            return data

        # ----------------------------------------------------
        # VACUUM
        # ----------------------------------------------------

        if any(
            term in user_text
            for term in [
                "vacuum",
                "vacuum cleaner"
            ]
        ):

            data["category"] = "Home"

            data["subcategory"] = "Vacuum Cleaners"

            return data

        # ----------------------------------------------------
        # FITNESS
        # ----------------------------------------------------

        if any(
            term in user_text
            for term in [
                "fitness",
                "gym equipment",
                "gym kit",
                "resistance band",
                "exercise equipment",
                "workout equipment"
            ]
        ):

            data["category"] = "Sports"

            data["subcategory"] = "Fitness Equipment"

            return data

        return data

    # ========================================================
    # OLLAMA HEALTH CHECK
    # ========================================================

    def ollama_health_check(self):
        """
        Check whether the configured Ollama server is reachable.

        This is intentionally separate from provider_status(), because
        provider_status() reports configuration while this method performs
        an actual network check.
        """

        if not self.ollama_enabled:
            return False

        try:
            import urllib.request

            request = urllib.request.Request(
                self.ollama_url.replace("/api/chat", "/api/tags"),
                method="GET"
            )

            with urllib.request.urlopen(
                request,
                timeout=5
            ) as response:

                return response.status == 200

        except Exception:
            return False

    # ========================================================
    # PROVIDER STATUS
    # ========================================================

    def provider_status(self):

        return {

            "gemini": bool(
                self.gemini_client
            ),

            "groq": bool(
                self.groq_client
            ),

            "ollama": bool(
                self.ollama_enabled
            ),

            "rule_based": True
        }

    # ========================================================
    # TEST HELPERS
    # ========================================================

    def print_provider_status(self):

        status = self.provider_status()

        print()
        print("=" * 70)
        print("RAZORGUARD AI PROVIDERS")
        print("=" * 70)

        print(
            "Gemini :",
            "ENABLED"
            if status["gemini"]
            else "NOT CONFIGURED"
        )

        print(
            "Groq   :",
            "ENABLED"
            if status["groq"]
            else "NOT CONFIGURED"
        )

        print(
            "Ollama :",
            "ENABLED"
            if status["ollama"]
            else "DISABLED"
        )

        print(
            "Rules  :",
            "ENABLED"
        )

        print("=" * 70)
        print()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    parser = GeminiIntentParser()

    parser.print_provider_status()

    test_requests = [

        (
            "bro i wnt a gud wireless hp under 3k "
            "for travl n online cls battery shud be long"
        ),

        (
            "need laptop for coding around 60k "
            "with 16gb ram and good battery"
        ),

        (
            "show me comfortable running shoes below 4k"
        ),

        (
            "i need a phone under 20k with best camera"
        ),

        (
            "show me smartwatch under 5k "
            "with gps and long battery"
        ),

        (
            "need a backpack around 2k for travel"
        ),

        (
            "need a shirt under 2k for office"
        ),

        (
            "need a t-shirt under 1k for casual wear"
        ),

        (
            "need a vacuum cleaner under 10k cordless"
        )
    ]

    print("=" * 75)

    print(
        "        RAZORGUARD AI COMMERCE AGENT"
    )

    print(
        "        MULTI-PROVIDER INTENT ENGINE"
    )

    print("=" * 75)

    for request in test_requests:

        print("\n")
        print("USER:")
        print(request)

        print("\nINTENT:")
        print("-" * 75)

        try:

            result = parser.parse(
                request
            )

            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False
                )
            )

        except Exception as error:

            print(
                "Test failed:"
            )

            print(
                str(error)
            )

    print(
        "\n" + "=" * 75
    )

    print(
        "Intent parsing tests completed!"
    )

    print(
        "=" * 75
    )