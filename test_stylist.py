"""
test_stylist.py

Standalone local test of the AI Outfit Builder's core logic.
Goal: prove that Gemini can take a mock wardrobe + a user prompt,
and return a strictly-structured JSON outfit recommendation
referencing ONLY real item IDs from the wardrobe (zero hallucination).

No database, no backend, no frontend yet — just the AI brain.
"""

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# 1. Load API key from .env
# ---------------------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found. Make sure you created a .env file "
        "in this folder with: GEMINI_API_KEY=your_key_here"
    )

client = genai.Client(api_key=API_KEY)

# ---------------------------------------------------------------------------
# 2. Mock wardrobe data (stand-in for what will later come from Supabase)
# ---------------------------------------------------------------------------
MOCK_WARDROBE = [
    {"id": 1, "category": "top", "color": "White", "style": "Casual", "tags": ["cotton", "everyday"]},
    {"id": 2, "category": "top", "color": "Black turtleneck", "style": "Chic", "tags": ["fall", "date-night"]},
    {"id": 3, "category": "bottom", "color": "Light blue denim", "style": "Casual", "tags": ["jeans", "everyday"]},
    {"id": 4, "category": "bottom", "color": "Black", "style": "Formal", "tags": ["tailored", "work"]},
    {"id": 5, "category": "shoes", "color": "White sneakers", "style": "Casual", "tags": ["comfy", "everyday"]},
    {"id": 6, "category": "shoes", "color": "Black heels", "style": "Formal", "tags": ["date-night", "evening"]},
    {"id": 7, "category": "dress", "color": "Red", "style": "Chic", "tags": ["date-night", "summer"]},
    {"id": 8, "category": "outerwear", "color": "Beige trench coat", "style": "Chic", "tags": ["fall", "rain"]},
    {"id": 9, "category": "accessory", "color": "Gold hoop earrings", "style": "Chic", "tags": ["date-night"]},
    {"id": 10, "category": "top", "color": "Striped linen shirt", "style": "Casual", "tags": ["summer", "linen"]},
    {"id": 11, "category": "bottom", "color": "Khaki shorts", "style": "Casual", "tags": ["summer", "comfy"]},
    {"id": 12, "category": "shoes", "color": "Brown sandals", "style": "Casual", "tags": ["summer"]},
    {"id": 13, "category": "one-piece", "color": "Black swimsuit", "style": "Beach", "tags": ["beach", "summer", "swim"]},
]

# ---------------------------------------------------------------------------
# 3. Strict output schema — Gemini must conform to this shape exactly
# ---------------------------------------------------------------------------
OUTFIT_SCHEMA = {
    "type": "object",
    "properties": {
        "outfit": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "integer"}
                },
                "required": ["item_id"]
            }
        },
        "reason": {"type": "string"}
    },
    "required": ["outfit", "reason"]
}

# ---------------------------------------------------------------------------
# 4. Prompt construction
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """You are a wardrobe stylist AI. You will be given:
1. A JSON array of the user's ACTUAL wardrobe items (with id, category, color, style, tags).
2. A user request (e.g. "what should I wear to a coffee date?").

RULES (must follow strictly):
- You may ONLY use item_id values that exist in the provided wardrobe array. NEVER invent an id.
- An outfit MUST be physically complete. Valid complete outfit combinations are:
  (top + bottom + shoes) OR (dress + shoes) OR (one-piece + shoes).
  You may add outerwear or accessories on top of any minimum combo, but never suggest
  an incomplete outfit (e.g. just a top and an accessory, with no bottom/dress/one-piece or shoes).
- A one-piece is a swimsuit or bodysuit appropriate for the beach or pool -- treat it the same
  as a dress when it comes to outfit completeness (it replaces top + bottom).
- Pick items whose category, color, style, and tags best match the user's request and the
  general vibe implied (formality, weather, occasion).
- Respond with JSON ONLY, matching the required schema exactly. No conversational text,
  no markdown formatting, no explanation outside the 'reason' field.
"""


def get_outfit_recommendation(user_prompt: str, wardrobe: list) -> dict:
    """Send the wardrobe + prompt to Gemini and return the parsed structured outfit JSON."""

    full_prompt = (
        f"Wardrobe:\n{json.dumps(wardrobe, indent=2)}\n\n"
        f"User request: \"{user_prompt}\""
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=OUTFIT_SCHEMA,
        ),
    )

    return json.loads(response.text)


def validate_outfit(result: dict, wardrobe: list) -> list:
    """Sanity-check the AI's response against our hard constraints. Returns a list of problems (empty = all good)."""
    problems = []
    wardrobe_by_id = {item["id"]: item for item in wardrobe}

    outfit_ids = [entry["item_id"] for entry in result.get("outfit", [])]

    # Check 1: every id must exist in the wardrobe (zero hallucination check)
    for item_id in outfit_ids:
        if item_id not in wardrobe_by_id:
            problems.append(f"Hallucinated item_id {item_id} — does not exist in wardrobe!")

    # Check 2: outfit completeness
    categories_used = {wardrobe_by_id[i]["category"] for i in outfit_ids if i in wardrobe_by_id}
    has_top_bottom_shoes = {"top", "bottom", "shoes"}.issubset(categories_used)
    has_dress_shoes = {"dress", "shoes"}.issubset(categories_used)
    has_onepiece_shoes = {"one-piece", "shoes"}.issubset(categories_used)

    if not (has_top_bottom_shoes or has_dress_shoes or has_onepiece_shoes):
        problems.append(
            f"Incomplete outfit — categories used were {categories_used}, "
            f"need (top+bottom+shoes), (dress+shoes), or (one-piece+shoes)."
        )

    return problems


def print_outfit(result: dict, wardrobe: list):
    """Pretty-print the recommended outfit with real item details."""
    wardrobe_by_id = {item["id"]: item for item in wardrobe}
    print("\nRecommended Outfit:")
    for entry in result.get("outfit", []):
        item = wardrobe_by_id.get(entry["item_id"])
        if item:
            print(f"  - [{item['category']}] {item['color']} ({item['style']})")
        else:
            print(f"  - Unknown item_id {entry['item_id']}")
    print(f"\nReason: {result.get('reason')}\n")


# ---------------------------------------------------------------------------
# 5. Test prompts
# ---------------------------------------------------------------------------
TEST_PROMPTS = [
    "What should I wear to a coffee date?",
    "I have a casual summer day out with friends, what should I wear?",
    "What should I wear to a formal work dinner?",
    "What should I wear to the beach?",
]


if __name__ == "__main__":
    for prompt in TEST_PROMPTS:
        print("=" * 70)
        print(f"Prompt: {prompt}")
        try:
            result = get_outfit_recommendation(prompt, MOCK_WARDROBE)
            print_outfit(result, MOCK_WARDROBE)

            problems = validate_outfit(result, MOCK_WARDROBE)
            if problems:
                print("VALIDATION ISSUES:")
                for p in problems:
                    print(f"   - {p}")
            else:
                print("Outfit passed validation (no hallucinations, complete outfit).")

        except Exception as e:
            print(f"Error during request: {e}")