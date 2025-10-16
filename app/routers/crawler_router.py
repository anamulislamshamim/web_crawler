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
from core.deps import get_mongo
from database.storage import MongoStorage


router = APIRouter()

@router.post("/start/{site_key}")
async def start_crawl(site_key: str, background_tasks: BackgroundTasks, mongo: MongoStorage = Depends(get_mongo)):
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
async def resume_crawl(site_key: str, mongo: MongoStorage = Depends(get_mongo)):
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
async def status(site_key: str, mongo: MongoStorage = Depends(get_mongo)):
    state = await mongo.get_state(site_key)
    if state:
        state['_id'] = str(state['_id'])
    return {"site_key": site_key, "state": state}