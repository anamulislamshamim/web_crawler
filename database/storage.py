import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
from pymongo import ASCENDING
from datetime import datetime, timezone


class MongoStorage:
    def __init__(self, uri: str = "mongodb://localhost:27017", db_name: str = "book_crawler"):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        # book table
        self.books = self.db["books"]
        # state table
        self.state = self.db["crawler_state"]
        # book changes table
        self.book_changes = self.db["book_changes"]
    
    async def insert_one_book_change(self, book_doc: Dict[str, Any]):
        """Insert Book changes into this table"""
        await self.book_changes.insert_one({
            'source_url': book_doc['source_url'],
            'change_type': 'new',
            'changes': book_doc,
            'timestamp': datetime.now(timezone.utc)
        })
        
    async def ensure_indexes(self):
        # unique on source_url to deduplicate
        await self.books.create_index([("source_url", ASCENDING)], unique=True)
        await self.state.create_index([("name", ASCENDING)], unique=True)
    
    async def upsert_book(self, book_doc: Dict[str, Any]):
        # Upsert based on source_url
        res = await self.books.update_one({"source_url": book_doc["source_url"]}, {"$set": book_doc}, upsert=True)
        return res
    
    async def get_one_book(self, book_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.books.find_one({"source_url": book_doc["source_url"]})
        
    async def save_raw_html(self, source_url: str, html: str):
        await self.books.update_one({"source_url": source_url}, {"$set": html}, upsert=True)
        
    async def save_state(self, name: str, state_doc: Dict[str, Any]):
        await self.state.update_one({"name": name}, {"$set": state_doc}, upsert=True)
    
    async def get_state(self, name: str) -> Optional[Dict[str, Any]]:
        return await self.state.find_one({"name": name})
    
    async def close(self):
        # motor does not require explicit close in most cases, but close socket
        self.client.close()
        
        '''
        Motor handles connection reuse and garbage collection automatically. 
        The explicit close() is for an intentional, graceful shutdown of the 
        entire connection resource, rather than a necessity after every database query.
        '''