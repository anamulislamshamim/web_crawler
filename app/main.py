from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database.db_config import mongo
from scheduler.scheduler import DailyScheduler
from app.routers import crawler_router, books_router, changes_router
from crawler.crawler_registry import get_all_crawlers
from core.auth import get_api_key_header

# ---------- Lifespan for startup/shutdown ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context: startup and shutdown events.
    - Ensure Mongo indexes.
    - Initialize scheduler after Mongo is ready.
    - Clean up scheduler and crawlers on shutdown.
    """
    # ---------- Startup ----------
    app.state.mongo = mongo
    await mongo.ensure_indexes()

    # Initialize scheduler AFTER Mongo is ready
    app.state.scheduler = DailyScheduler(app.state.mongo)
    # start scheduled jobs automatically
    app.state.scheduler.start_schedule_job()

    yield  # Pause here until shutdown

    # ---------- Shutdown ----------
    # Close Mongo connection
    await mongo.close()

    # Close crawlers safely
    for crawler in get_all_crawlers():
        try:
            await crawler.close()
        except Exception:
            pass


# ---------- Create FastAPI app ----------
app = FastAPI(title="Async Book Crawler", lifespan=lifespan)

# ---------- CORS Middleware ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Health Check ----------
@app.get("/health")
async def health():
    return {"status": "Hay Shamim! Server is running..."}


# ---------- Include Routers ----------
app.include_router(crawler_router.router, prefix="/crawler", dependencies=[Depends(get_api_key_header)])
app.include_router(books_router.router, prefix="", dependencies=[Depends(get_api_key_header)])
app.include_router(changes_router.router, prefix="/changes", dependencies=[Depends(get_api_key_header)])