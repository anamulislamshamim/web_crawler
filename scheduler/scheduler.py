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


# Setup basic logging configuration
logging.basicConfig(
    filename="crawler_daily.log", 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class BookChangeDetector:
    def __init__(self, mongo: MongoStorage):
        self.mongo = mongo 
    
    async def compute_fingerprint(self, book_doc: dict) -> str:
        """Compute hash for key fields to detect changes."""
        relevant_fields = {
            'name': book_doc.get('name'),
            'price_including_tax': book_doc.get('price_including_tax'),
            'price_excluding_tax': book_doc.get('price_excluding_tax'),
            'availability': book_doc.get('availability'),
            'rating': book_doc.get('rating'),
        }
        
        encoded = json.dumps(relevant_fields, sort_keys=True).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()

    async def detect_and_update_changes(self, new_book: dict):
        """Compare new vs stored book data, update if necessary, log changes.""" 
        existing_book = await self.mongo.get_one_book(new_book)
        
        # Compute fingerprint for new book
        new_fp = await self.compute_fingerprint(new_book)
        
        if not existing_book:
            # New book detected
            new_book['fingerprint'] = new_fp
            new_book['status'] = 'new'
            await self.mongo.upsert_book(new_book)
            await self.mongo.insert_one_book_change(new_book)
            
            return "new"
        
        old_fp = existing_book.get('fingerprint')
        if old_fp != new_fp:
            #Book updated
            changes = {}
            for key in ['price_including_tax', 'price_excluding_tax', 'availability', 'rating']:
                if existing_book.get(key) != new_book.get(key):
                    changes[key] = {'old': existing_book.get(key), 'new': new_book.get(key)}
            
            if changes:
                new_book['fingerprint'] = new_fp
                new_book['crawl_timestamp'] = datetime.now(timezone.utc)
                await self.mongo.upsert_book(new_book)
                
                new_book_changes = {
                    'source_url': new_book['source_url'],
                    'change_type': 'update',
                    'changes': changes,
                    'timestamp': new_book['crawl_timestamp']
                }
                await self.mongo.insert_one_book_change(new_book_changes)
                logging.info(f"Book Updated: {new_book['name']} | Changes: {changes}")
                return 'updated'
        
        return 'unchanged'


class DailyScheduler:
    def __init__(self, mongo: MongoStorage) -> None:
        self.mongo = mongo 
        self.detector = BookChangeDetector(mongo)
    
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
        
        # Once crawl finishes, detect changes
        async for book in self.mongo.books.find({}):
            await self.detector.detect_and_update_changes(book)
        
        logging.info("Schedule crawl and change detection completed.")
        