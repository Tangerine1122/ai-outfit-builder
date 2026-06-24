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
    print("📤 Inserting mock items into Supabase...")
    response = supabase.table("clothes").insert(MOCK_ITEMS_TO_INSERT).execute()
    print(f"✅ Inserted {len(response.data)} item(s).")
    return response.data


def fetch_all_items():
    """Read back everything currently in the clothes table."""
    print("\n📥 Fetching all items from Supabase...")
    response = supabase.table("clothes").select("*").execute()
    items = response.data
    print(f"✅ Found {len(items)} item(s) in the database:\n")
    for item in items:
        print(
            f"  - id={item['id']} | [{item['category']}] {item['color']} "
            f"({item['style']}) | tags={item['tags']}"
        )
    return items


if __name__ == "__main__":
    insert_mock_items()
    fetch_all_items()