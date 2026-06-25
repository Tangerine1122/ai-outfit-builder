"""
main.py

The actual backend server. This is what will eventually host all our
routes (uploading clothes, getting outfit recommendations, etc.) and
is what the React frontend will talk to over HTTP.

Starting point: the smallest possible FastAPI app, just to prove the
server runs and routes respond, before wiring in real logic.
"""

from fastapi import FastAPI, HTTPException, UploadFile, Form
from pydantic import BaseModel
from typing import List

# Reuse the logic we already built and tested — don't rewrite it here.
from test_stylist import get_outfit_recommendation, validate_outfit
from test_database import get_wardrobe_for_stylist, insert_clothing_item
from test_cloudinary import upload_clothing_image

# ---------------------------------------------------------------------------
# Create the FastAPI "app" object.
# Everything we build (routes, middleware, etc.) attaches to this one object.
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Outfit Builder API")


# ---------------------------------------------------------------------------
# Pydantic model = the "shape" of data we expect the frontend to send us.
# FastAPI uses this to automatically validate incoming requests — if the
# frontend sends something missing a "prompt" field, FastAPI rejects it
# with a clear error before our function even runs.
# ---------------------------------------------------------------------------
class RecommendRequest(BaseModel):
    prompt: str


# ---------------------------------------------------------------------------
# A "route" = a URL path + an HTTP method (GET, POST, etc.) + a function
# that runs when that path is requested.
#
# @app.get("/") means: "when someone sends a GET request to the root URL,
# run the function right below this decorator."
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "AI Outfit Builder API is running!"}


# A second tiny route, just to prove multiple routes can coexist.
@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# The first REAL route. Note it's @app.post, not @app.get — POST is used
# whenever the caller is SENDING data to us (here: a prompt), rather than
# just asking for something.
#
# "request: RecommendRequest" tells FastAPI: expect a JSON body matching
# the RecommendRequest shape (a "prompt" string). FastAPI automatically
# parses incoming JSON into this object AND validates it for us.
# ---------------------------------------------------------------------------
@app.post("/stylist/recommend")
def recommend_outfit(request: RecommendRequest):
    wardrobe = get_wardrobe_for_stylist()

    # Guard clause: if the closet is empty, there's nothing for Gemini to
    # work with — fail clearly and immediately instead of sending Gemini
    # an empty array and getting a confusing response back.
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
        "validation_problems": problems,  # empty list = all good
    }


# ---------------------------------------------------------------------------
# The upload route. Unlike /stylist/recommend, this does NOT receive a
# clean JSON body — file uploads use a different request format called
# "multipart/form-data", which is why this route's parameters look
# different: each piece of data is its own separate parameter, rather
# than one Pydantic model.
#
# - UploadFile: tells FastAPI "expect an actual file here"
# - Form(...): tells FastAPI "expect a plain text field alongside the file"
#   (this is needed because file uploads can't be sent as plain JSON)
# ---------------------------------------------------------------------------
@app.post("/clothes/upload")
async def upload_clothing_item(
    file: UploadFile,
    category: str = Form(...),
    color: str = Form(...),
    style: str = Form(...),
    tags: List[str] = Form(default=[]),
):
    # Basic validation: catch an obviously wrong category before we waste
    # an upload to Cloudinary on something that will fail at the database
    # step anyway (the table's CHECK constraint would reject it).
    valid_categories = {"top", "bottom", "shoes", "dress", "outerwear", "accessory"}
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Must be one of: {sorted(valid_categories)}",
        )

    # Read the uploaded file's raw bytes into memory.
    # "await" is needed here because reading an uploaded file is an async
    # operation in FastAPI — it doesn't block the server while waiting.
    file_bytes = await file.read()

    # Step 1: upload the photo to Cloudinary, get back a real CDN URL.
    try:
        image_url = upload_clothing_image(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Image upload failed: {e}")

    # Step 2: save the metadata + the new image URL into Supabase.
    try:
        saved_item = insert_clothing_item(
            image_url=image_url,
            category=category,
            color=color,
            style=style,
            tags=tags,
        )
    except Exception as e:
        # Note: at this point the image is already on Cloudinary even
        # though the database save failed. We're not handling that
        # cleanup yet — just surfacing the error clearly for now.
        raise HTTPException(status_code=500, detail=f"Saving to database failed: {e}")

    return saved_item