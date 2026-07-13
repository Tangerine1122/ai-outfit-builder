"""
main.py

The actual backend server. This is what will eventually host all our
routes (uploading clothes, getting outfit recommendations, etc.) and
is what the React frontend will talk to over HTTP.

Starting point: the smallest possible FastAPI app, just to prove the
server runs and routes respond, before wiring in real logic.
"""

from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Reuse the logic we already built and tested — don't rewrite it here.
from test_stylist import get_outfit_recommendation, validate_outfit
from test_database import get_wardrobe_for_stylist, insert_clothing_item, fetch_all_items, delete_clothing_item
from test_cloudinary import upload_clothing_image, delete_clothing_image

# ---------------------------------------------------------------------------
# Create the FastAPI "app" object.
# Everything we build (routes, middleware, etc.) attaches to this one object.
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Outfit Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://dees-wardrobe.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic model = the "shape" of data we expect the frontend to send us.
# ---------------------------------------------------------------------------
class RecommendRequest(BaseModel):
    prompt: str


@app.get("/")
def read_root():
    return {"message": "AI Outfit Builder API is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/clothes")
def list_clothes():
    return fetch_all_items()


@app.post("/stylist/recommend")
def recommend_outfit(request: RecommendRequest):
    wardrobe = get_wardrobe_for_stylist()

    if not wardrobe:
        raise HTTPException(
            status_code=400,
            detail="Your wardrobe is empty. Upload some clothes before asking for an outfit.",
        )

    result = get_outfit_recommendation(request.prompt, wardrobe)
    problems = validate_outfit(result, wardrobe)

    return {
        "outfit": result["outfit"],
        "reason": result["reason"],
        "validation_problems": problems,
    }


@app.post("/clothes/upload")
async def upload_clothing_item(
    file: UploadFile,
    category: str = Form(...),
    color: str = Form(...),
    style: str = Form(...),
    tags: List[str] = Form(default=[]),
):
    valid_categories = {"top", "bottom", "shoes", "dress", "outerwear", "accessory", "one-piece"}
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Must be one of: {sorted(valid_categories)}",
        )

    file_bytes = await file.read()

    try:
        image_url = upload_clothing_image(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Image upload failed: {e}")

    try:
        saved_item = insert_clothing_item(
            image_url=image_url,
            category=category,
            color=color,
            style=style,
            tags=tags,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Saving to database failed: {e}")

    return saved_item


@app.delete("/clothes/{item_id}")
def delete_clothing(item_id: int):
    # Step 1: delete from Supabase, get the item back so we have its image_url
    deleted_item = delete_clothing_item(item_id)

    if not deleted_item:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found."
        )

    # Step 2: delete the photo from Cloudinary using the image_url
    cloudinary_success = delete_clothing_image(deleted_item["image_url"])

    return {
        "deleted": True,
        "item_id": item_id,
        "cloudinary_deleted": cloudinary_success,
    }