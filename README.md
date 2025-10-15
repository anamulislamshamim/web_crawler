Notes:
- Designed to be generic: provide a `site_config` for a site (example included for books.toscrape.com)
- Uses httpx.AsyncClient, asyncio, motor.motor_asyncio
- Retry logic with exponential backoff and jitter implemented in utils.py
- Resume capability by storing a `crawler_state` document in MongoDB with last processed page and queue
- Raw HTML snapshot stored as part of book document
- Deduplication via unique index on `source_url`
- FastAPI endpoints: /start, /status, /stop, /resume