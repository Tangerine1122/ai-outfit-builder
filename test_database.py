"""
test_database.py

Standalone local test of the Supabase connection.
Goal: prove that we can INSERT mock clothing items into the real
`clothes` table, and READ them back out — before wiring this into
FastAPI or the React frontend.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# 1. Load credentials from .env
# ---------------------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL or SUPABASE_KEY not found. Make sure both are set "
        "in your .env file."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# 2. Mock items to insert (same style as our Gemini test wardrobe,
#    but this time these are REAL rows going into REAL Postgres)
# ---------------------------------------------------------------------------
MOCK_ITEMS_TO_INSERT = [
    {
        "image_url": "https://example.com/placeholder-white-tshirt.jpg",
        "category": "top",
        "color": "White",
        "style": "Casual",
        "tags": ["cotton", "everyday"],
    },
    {
        "image_url": "https://example.com/placeholder-blue-jeans.jpg",
        "category": "bottom",
        "color": "Light blue denim",
        "style": "Casual",
        "tags": ["jeans", "everyday"],
    },
    {
        "image_url": "https://example.com/placeholder-white-sneakers.jpg",
        "category": "shoes",
        "color": "White sneakers",
        "style": "Casual",
        "tags": ["comfy", "everyday"],
    },
]


def insert_mock_items():
    """Insert the mock items into the clothes table."""
    print("Inserting mock items into Supabase...")
    response = supabase.table("clothes").insert(MOCK_ITEMS_TO_INSERT).execute()
    print(f"Inserted {len(response.data)} item(s).")
    return response.data


def fetch_all_items():
    """Read back everything currently in the clothes table."""
    print("\nFetching all items from Supabase...")
    response = supabase.table("clothes").select("*").execute()
    items = response.data
    print(f"Found {len(items)} item(s) in the database:\n")
    for item in items:
        print(
            f"  - id={item['id']} | [{item['category']}] {item['color']} "
            f"({item['style']}) | tags={item['tags']}"
        )
    return items


def get_wardrobe_for_stylist() -> list:
    """
    Fetch the real wardrobe from Supabase and reshape it into exactly the
    format the Gemini stylist logic expects: a list of dicts with
    id, category, color, style, tags (no image_url/created_at needed --
    Gemini doesn't need those to make a recommendation).

    Used by main.py's /stylist/recommend route in place of MOCK_WARDROBE.
    """
    response = supabase.table("clothes").select("*").execute()
    items = response.data

    return [
        {
            "id": item["id"],
            "category": item["category"],
            "color": item["color"],
            "style": item["style"],
            "tags": item["tags"],
        }
        for item in items
    ]


def insert_clothing_item(image_url: str, category: str, color: str, style: str, tags: list) -> dict:
    """
    Insert a single new clothing item into Supabase and return the saved
    row (including its new auto-generated id) -- used by main.py's
    upload route, after the photo has already been uploaded to Cloudinary.
    """
    new_item = {
        "image_url": image_url,
        "category": category,
        "color": color,
        "style": style,
        "tags": tags,
    }
    response = supabase.table("clothes").insert(new_item).execute()
    return response.data[0]  # .insert() always returns a list; we only inserted one row


if __name__ == "__main__":
    insert_mock_items()
    fetch_all_items()