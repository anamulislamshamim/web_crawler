import asyncio
import hashlib
import json 
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from crawler.scraper import AsyncBookCrawler
from database.storage import MongoStorage
from crawler.config import SITE_CONFIG
from settings import (
    SITE_KEY,
    SCHEDULER_TIMEZONE,
    SCHEDULER_RUN_TIME,
    SCHEDULER_INTERVAL_MINUTES,
)
from log.logger_config import get_logger


logging = get_logger(__name__)


class DailyScheduler:
    def __init__(self, mongo: MongoStorage) -> None:
        self.mongo = mongo
    
    def init_scheduler(self):
        """
        Initialize the scheduler dynamically based on environment variables.
        If SCHEDULER_RUN_TIME (e.g., "02:00") is set, it runs daily at that time.
        Otherwise, it uses interval-based scheduling.
        """
        scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)

        if SCHEDULER_RUN_TIME:
            # Fixed daily run time (e.g., 02:00)
            hour, minute = map(int, SCHEDULER_RUN_TIME.split(":"))
            trigger = CronTrigger(hour=hour, minute=minute, timezone=SCHEDULER_TIMEZONE)
            print(f"[green]✅ Scheduler configured to run daily at {hour:02d}:{minute:02d} ({SCHEDULER_TIMEZONE})[/green]")
        else:
            # Interval-based schedule (fallback)
            trigger = IntervalTrigger(minutes=SCHEDULER_INTERVAL_MINUTES)
            print(f"[cyan]✅ Scheduler configured to run every {SCHEDULER_INTERVAL_MINUTES} minutes[/cyan]")

        # Add the job
        scheduler.add_job(self.run_daily_task, trigger, args=[])
        scheduler.start()
        print("[yellow]🕒 Scheduler started successfully![/yellow]")
        return scheduler 
    
    def start_schedule_job(self):
        """Start daily job at 2 AM using cron trigger"""      
        self.init_scheduler()
    
    async def run_daily_task(self):
        """Main daily task: crawl, detect, update, log"""
        logging.info("Starting schedule crawl...")
        site_key = "books_toscrape"
        config = SITE_CONFIG[site_key]
        crawler = AsyncBookCrawler(site_key, config, self.mongo, concurrency=10)
        await self.mongo.ensure_indexes()
        await crawler.crawl(resume=False)
        
        # # Once crawl finishes, detect changes
        # async for book in self.mongo.books.find({}):
        #     await self.detector.detect_and_update_changes(book)
        
        logging.info("Schedule crawl completed.")
        