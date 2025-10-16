from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database.db_config import mongo
from scheduler.scheduler import DailyScheduler
from app.routers import crawler_router, books_router
from crawler.crawler_registry import get_all_crawlers
from core.auth import get_api_key_header


# Shared objects - in real app prefer startup/shutdown events
scheduler = DailyScheduler(mongo)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----------Start up------------
    # Now mongo will be globally available resource within Fastapi router endpoint
    # we can access it like mongo = request.app.state.mongo within any endpoint
    app.state.mongo = mongo
    await mongo.ensure_indexes()
    scheduler.start_schedule_job()
    
    # The 'yield' pauses the function until the application shuts down
    yield
    
    # ----------Shut Down-----------
    await mongo.close()
    for c in get_all_crawlers():
        try:
            await c.close()
        except:
            pass

app = FastAPI(title="Async Book Crawler", lifespan=lifespan)

# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def hello():
    return {"status": "Server is running..."}

# include routers with dependency on API key
app.include_router(crawler_router.router, prefix="/crawler", dependencies=[Depends(get_api_key_header)]) # type: ignore
