from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Response
import asyncio
import csv
import io
import json
from datetime import datetime, timezone, timedelta
from assignment.fastapi_book_crawler.database.storage import MongoStorage
from crawler.config import SITE_CONFIG
from crawler.scraper import AsyncBookCrawler
from scheduler.scheduler import DailyScheduler
from ..settings import MONGO_URI, DB_NAME


# We'll manage crawler instances by site key
CRAWLERS = {}
# Shared objects - in real app prefer startup/shutdown events
mongo = MongoStorage(uri=MONGO_URI, db_name=DB_NAME)
scheduler = DailyScheduler(mongo)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----------Start up------------
    await mongo.ensure_indexes()
    scheduler.start_schedule_job()
    
    # The 'yield' pauses the function until the application shuts down
    yield
    
    # ----------Shut Down-----------
    await mongo.close()
    for c in CRAWLERS.values():
        try:
            await c.close()
        except:
            pass

app = FastAPI(title="Async Book Crawler", lifespan=lifespan)

@app.get("/health")
async def hello():
    return {"status": "Server is running..."}

@app.post("/start/{site_key}")
async def start_crawl(site_key: str, background_tasks: BackgroundTasks):
    if site_key not in SITE_CONFIG:
        return {"error": "Unknown site_key"}
    
    if site_key in  CRAWLERS:
        return {"status": "already_running"}
    
    crawler = AsyncBookCrawler(site_key, SITE_CONFIG[site_key], mongo, concurrency=10) 
    CRAWLERS[site_key] = crawler
    
    # run in background
    loop = asyncio.get_event_loop()
    loop.create_task(crawler.crawl(resume=False))
    return {"status": "started", "site_key": site_key}

@app.post("/resume/{site_key}")
async def resume_crawl(site_key: str):
    if site_key not in SITE_CONFIG:
        return {"error": "Unknown site_key"}
    if site_key in CRAWLERS:
        return {"status": "already_running"}
    crawler = AsyncBookCrawler(site_key, SITE_CONFIG[site_key], mongo, concurrency=10)
    CRAWLERS[site_key] = crawler
    
    loop = asyncio.get_event_loop()
    loop.create_task(crawler.crawl(resume=False))
    
    return {"status": "resumed", "site_key": site_key}

@app.post("/stop/{site_key}")
async def stop_crawl(site_key: str):
    if site_key not in SITE_CONFIG:
        return {"error": "unknown site_key"}
    c = CRAWLERS.get(site_key)
    if not c:
        return {"error": "not_running"}
    c.stop()
    del CRAWLERS[site_key]
    return {"status": "stopped", "site_key": site_key}

@app.get("/status/{site_key}")
async def status(site_key: str):
    state = await mongo.get_state(site_key)
    return {"site_key": site_key, "state": state}

@app.get("/report/daily")
async def daily_report(format: str = 'json'):
    """Generate a daily change report (JSON or csv)"""
    today = datetime.now(timezone.utc).date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today + timedelta(days=1), datetime.min.time())
    
    cursor = mongo.db.book_changes.find({'timestamps': {'$gte': start, '$lt': end}})
    changes = await cursor.to_list(length=None)
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['source_url', 'change_type', 'changes', 'timestamp'])
        for c in changes:
            writer.writerow([c['source_url'], c['change_type'], json.dumps(c['changes']), c['timestamp']])
        return Response(content=output.getvalue(), media_type='text/csv') 

    # default JSON
    for c in changes:
        c['_id'] = str(c['_id'])
    
    return changes
