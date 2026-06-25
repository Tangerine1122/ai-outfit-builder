"""
test_cloudinary.py

Standalone local test of the Cloudinary connection.
Goal: prove that we can upload an image file to Cloudinary and get
back a working CDN URL — before wiring this into FastAPI's upload
route or the React frontend.
"""

import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------------------------
# 1. Load credentials from .env and configure the SDK
# ---------------------------------------------------------------------------
load_dotenv()

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if not all([CLOUD_NAME, API_KEY, API_SECRET]):
    raise RuntimeError(
        "Missing one or more Cloudinary credentials. Check your .env file "
        "for CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET."
    )

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
    secure=True,  # always use https URLs
)

# ---------------------------------------------------------------------------
# 2. Upload a test image
# ---------------------------------------------------------------------------
# We use a small public test image URL so you don't need a local file yet.
# Cloudinary can upload directly from a URL, a local file path, or raw bytes.
TEST_IMAGE_SOURCE = "https://res.cloudinary.com/demo/image/upload/sample.jpg"


def upload_test_image():
    print("Uploading test image to Cloudinary...")
    result = cloudinary.uploader.upload(
        TEST_IMAGE_SOURCE,
        folder="ai-outfit-builder/test",  # keeps test uploads organized/separate
        tags=["test-upload"],
    )
    print("Upload successful!\n")
    print(f"  Public ID:    {result['public_id']}")
    print(f"  Secure URL:   {result['secure_url']}")
    print(f"  Format:       {result['format']}")
    print(f"  Dimensions:   {result['width']}x{result['height']}")
    return result


def upload_local_file(file_path: str):
    """Optional helper: upload an actual file from your computer instead of a URL."""
    print(f"Uploading local file: {file_path}...")
    result = cloudinary.uploader.upload(
        file_path,
        folder="ai-outfit-builder/test",
        tags=["test-upload"],
    )
    print("Upload successful!")
    print(f"  Secure URL: {result['secure_url']}")
    return result

def upload_clothing_image(file_bytes: bytes) -> str:
    """
    Upload a real clothing photo to Cloudinary (separate folder from test
    uploads) and return just the secure URL — this is what the FastAPI
    upload route will store in Supabase's image_url column.

    Cloudinary can accept raw bytes directly, which is exactly what we get
    from a FastAPI UploadFile after reading it.
    """
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="ai-outfit-builder/clothes",  # separate from the test/ folder
        tags=["wardrobe-item"],
    )
    return result["secure_url"]

if __name__ == "__main__":
    result = upload_test_image()

    print("\nOpen this URL in your browser to confirm the image loads:")
    print(f"   {result['secure_url']}")

    # Uncomment and edit this line to also test uploading a real local image:
    # upload_local_file(r"C:\Users\Jimbrio\Desktop\some-photo.jpg")