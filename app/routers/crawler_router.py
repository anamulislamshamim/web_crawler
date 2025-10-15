from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
# from fastapi.responses import JSONResponse
# from starlette.status import HTTP_400_BAD_REQUEST
from crawler.scraper import AsyncBookCrawler
from crawler.config import SITE_CONFIG
import io 
import csv
import json
# from database.storage import MongoStorage
from crawler.crawler_registry import get_crawler, add_crawler, remove_crawler
import asyncio
from database.db_config import mongo
from datetime import datetime, timezone, timedelta


router = APIRouter()

@router.post("/start/{site_key}")
async def start_crawl(site_key: str, background_tasks: BackgroundTasks):
    if site_key not in SITE_CONFIG:
        return {"error": "Unknown site_key"}
    
    if get_crawler(site_key):
        return {"status": "already_running"}
    
    crawler = AsyncBookCrawler(site_key, SITE_CONFIG[site_key], mongo, concurrency=10) 
    add_crawler(site_key, crawler)
    
    # run in background
    loop = asyncio.get_event_loop()
    loop.create_task(crawler.crawl(resume=False))
    return {"status": "started", "site_key": site_key}

@router.post("/resume/{site_key}")
async def resume_crawl(site_key: str):
    if site_key not in SITE_CONFIG:
        return {"error": "Unknown site_key"}
    if get_crawler(site_key):
        return {"status": "already_running"}
    crawler = AsyncBookCrawler(site_key, SITE_CONFIG[site_key], mongo, concurrency=10)
    add_crawler(site_key, crawler)
    
    loop = asyncio.get_event_loop()
    loop.create_task(crawler.crawl(resume=False))
    
    return {"status": "resumed", "site_key": site_key}

@router.post("/stop/{site_key}")
async def stop_crawl(site_key: str):
    if site_key not in SITE_CONFIG:
        return {"error": "unknown site_key"}
    c = get_crawler(site_key)
    if not c:
        return {"error": "not_running"}
    c.stop()
    remove_crawler(site_key)
    return {"status": "stopped", "site_key": site_key}

@router.get("/status/{site_key}")
async def status(site_key: str):
    state = await mongo.get_state(site_key)
    if state:
        state['_id'] = str(state['_id'])
    return {"site_key": site_key, "state": state}

@router.get("/report/daily")
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