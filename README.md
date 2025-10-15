Notes:
- Designed to be generic: provide a `site_config` for a site (example included for books.toscrape.com)
- Uses httpx.AsyncClient, asyncio, motor.motor_asyncio
- Retry logic with exponential backoff and jitter implemented in utils.py
- Resume capability by storing a `crawler_state` document in MongoDB with last processed page and queue
- Raw HTML snapshot stored as part of book document
- Deduplication via unique index on `source_url`
- FastAPI endpoints: /start, /status, /stop, /resume

# ------------------------------- NOTES & INSTRUCTIONS ---------------------------------
# How to integrate these changes into your repo:
# 1. Create `app/routers` and put `crawler_router.py`, `book_router.py`, and `__init__.py` as shown.
# 2. Create `core` package with `auth.py`, `limiter.py`, and `deps.py`.
# 3. Replace your existing `app/main.py` with the updated one above.
# 4. Ensure environment variable `CRAWLER_API_KEY` is set for production; default key is `test-api-key-123`.
# 5. Install additional dependency `apscheduler` if you haven't already.
# 6. Run the app: `uvicorn app.main:app --reload` and use header `x-api-key: test-api-key-123` when calling APIs.


# Security & Scaling notes:
# - API key storage: currently from env var (CRAWLER_API_KEY). For multiple keys, store keys in Mongo `api_keys` collection and update get_api_key_header accordingly.
# - Rate limiter: current implementation is in-memory per-process. For multi-instance deployment, replace with Redis-based counters or use `slowapi` (Starlette integration) for robust limiting.
# - Sorting by rating mapping: for robust sorting, store a numeric `rating_value` in the book document as part of your crawler parsing.