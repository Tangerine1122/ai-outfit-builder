# AI Outfit Builder (backend)

FastAPI backend for DEE'S WARDROBE. Users upload photos of their real clothes; Gemini recommends outfits using only items that exist in their closet (no generated or stock images). The React frontend is a separate repo: `ai-outfit-builder-frontend`.

## Stack
- Python, FastAPI + Uvicorn
- Supabase (Postgres) via `supabase-py`, table `clothes`
- Cloudinary for image storage
- Gemini via `google-genai`, structured JSON output

## Layout
- `main.py` - the FastAPI app: CORS, routes. Keep it thin; it imports logic from the modules below.
- `test_stylist.py` - Gemini prompt, `get_outfit_recommendation()`, `validate_outfit()`
- `test_database.py` - Supabase client and `clothes` table queries
- `test_cloudinary.py` - image upload/delete

Despite the `test_` prefix, these three files are app modules that `main.py` imports, not test files. Don't let pytest collect or "fix" them as tests. If you add real tests, put them in a `tests/` folder.

## Routes
- `GET /`, `GET /health`
- `GET /clothes` - all items
- `POST /clothes/upload` - multipart image + form fields (category, color, style, tags) → Cloudinary → `clothes` row
- `DELETE /clothes/{item_id}` - deletes the row and its Cloudinary image
- `POST /stylist/recommend` - `{ "prompt": str }` → outfit that references real item IDs only

## Commands
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload      # http://localhost:8000, docs at /docs
```
`requirements.txt` is saved as UTF-16. If you regenerate it, use `pip freeze | Out-File -Encoding utf8 requirements.txt` so it becomes UTF-8.

There is no linter or test suite yet.

## Environment (`.env`, git-ignored)
`GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`. There is no `.env.example` yet; add one with placeholders if you add a variable.

## Rules
- The stylist must only return item IDs that exist in the wardrobe. Always run `validate_outfit()` on model output before returning it; never weaken this check.
- Allowed CORS origins are listed in `main.py` (`http://localhost:5173`, `https://dees-wardrobe.vercel.app`). Add new frontend URLs there instead of using `*`.
- Keys stay server-side. Never send Supabase, Cloudinary or Gemini secrets to the frontend or into logs.
- Validate request bodies with Pydantic models and return proper HTTP errors (`HTTPException`).
