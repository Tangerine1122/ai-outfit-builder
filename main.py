"""
main.py

The actual backend server. This is what will eventually host all our
routes (uploading clothes, getting outfit recommendations, etc.) and
is what the React frontend will talk to over HTTP.

Starting point: the smallest possible FastAPI app, just to prove the
server runs and routes respond, before wiring in real logic.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Reuse the logic we already built and tested — don't rewrite it here.
from test_stylist import get_outfit_recommendation, validate_outfit
from test_database import get_wardrobe_for_stylist

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