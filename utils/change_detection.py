import hashlib
import json 
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from database.storage import MongoStorage
from log.logger_config import get_logger


logging = get_logger(__name__)

class BookChangeDetector:
    def __init__(self, mongo: MongoStorage):
        self.mongo = mongo 
    
    async def compute_fingerprint(self, book_doc: Dict[str, Any]) -> str:
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
        new_fp = await self.compute_fingerprint(new_book)
        
        if not existing_book:
            # New book detected
            new_book['fingerprint'] = new_fp
            new_book['status'] = 'new'
            await self.mongo.upsert_book(new_book)
            await self.mongo.insert_one_book_change({
                    'source_url': new_book['source_url'],
                    'change_type': 'new',
                    'timestamp': new_book['crawl_timestamp']
                })
            
            return "new"
        
        old_fp = existing_book.get('fingerprint')
        if old_fp and new_fp and old_fp != new_fp:
            #Book updated
            print("Debug: Old_FP: ", old_fp[:20], " new_fp: ", new_fp[:20])
            
            changes = {}
            
            for key in ["name", 'price_including_tax', 'price_excluding_tax', 'availability', 'rating']:
                if existing_book.get(key) != new_book.get(key):
                    changes[key] = {'old': existing_book.get(key), 'new': new_book.get(key)}
            
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
        
        print("Debug: new_fp: ", new_fp)
        return 'unchanged'