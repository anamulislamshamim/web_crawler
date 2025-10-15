import asyncio
from typing import Dict, Any, List, Optional
import httpx
from lxml import html
from .models import Book
from ..database.storage import MongoStorage
from .utils import retry_async, parse_price


class AsyncBookCrawler:
    def __init__(self, site_key: str, site_config: Dict[str, Any], mongo: MongoStorage, concurrency: int = 10):
        self.site_key = site_key
        self.config = site_config
        self.mongo = mongo
        self.sem = asyncio.Semaphore(concurrency) # It's a crucial tool for limiting concurrency in asynchronous programming.
        self.client = httpx.AsyncClient(timeout=20)
        self._stop = False
        
    async def close(self):
        await self.client.aclose()
    
    async def crawl(self, resume: bool = False):
        await self.mongo.ensure_indexes()
        state = await self.mongo.get_state(self.site_key) if resume else None
        
        if state and resume:
            page = state.get('last_page', self.config['pagination'].get('start_page', 1))
            print(f"Resuming from page {page}")
        else:
            page = self.config['pagination'].get('start_page', 1)
        
        max_pages = self.config['pagination'].get("max_pages", None)
        while not self._stop:
            # generate url
            if self.config['pagination']['type'] == 'pattern':
                url = self.config['pagination']['pattern'].format(page=page)
            else:
                # Link-based pagination not implemented in this project
                break
            
            try:
                page_html = await retry_async(self._fetch_text, retries=3, url=url)
            except Exception as e:
                # transient error for page - save state and break
                await self.mongo.save_state(self.site_key, {'last_page': page, 'failed': True, 'error': str(e)})
                break
            
            tree = html.fromstring(page_html)
            book_cards = tree.cssselect(self.config['selectors']['book_card'])
            if not book_cards:
                # no more pages 
                await self.mongo.save_state(self.site_key, {'last_page': page, 'done': True})
                break
            
            tasks = []
            for card in book_cards:
                link_el = card.cssselect(self.config['selectors']['book_link'])[0]
                href = link_el.get('href')
                # make absolute if necessary
                make_abs = self.config.get('make_absolute')
                book_url = make_abs(href) if callable(make_abs) else href
                tasks.append(asyncio.create_task(self._process_book(book_url)))
                
            # wait for page's books to finish
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # save progress
            await self.mongo.save_state(self.site_key, {'last_page': page, 'done': False})
            
            page += 1
            if max_pages and page > max_pages:
                break
    
    async def _fetch_text(self, url: str) -> str:
        async with self.sem:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        
    async def _process_book(self, url: str):
        try:
            text = await retry_async(self._fetch_text, retries=3, url=url)
            tree = html.fromstring(text)
            
            selectors = self.config["selectors"]
            def safe_text(selector):
                try:
                    element = tree.cssselect(selector)
                    if not element:
                        return None 
                    # if it is an element List, pick first and text_content
                    first = element[0]
                    return first.text_content().strip()
                except Exception:
                    return None

            name = safe_text(selectors['name'])
            description = safe_text(selectors['description'])
            category = safe_text(selectors['category'])
            price_incl = parse_price(safe_text(selectors.get('price_including_tax')))
            price_excl = parse_price(safe_text(selectors.get('price_excluding_tax')))
            availability = safe_text(selectors.get('availability'))
            reviews = safe_text(selectors.get('number_of_reviews'))
            
            try:
                reviews = int(reviews) if reviews else None 
            except:
                reviews = None
            
            # rating is encoded in class names like <p class="star-rating Three">
            rating_element = tree.cssselect(selectors.get("rating"))
            rating = None 
            if rating_element:
                classes = rating_element[0].get('class', '')
                for c in classes.split():
                    if c.lower() in ['one', 'two', 'three', 'four', 'five', 'zero']:
                        rating  = c
            
            image_element = tree.cssselect(selectors.get('image'))
            image_url = None 
            if image_element:
                src = image_element[0].get('src')
                make_abs = self.config.get("make_absolute")
                image_url = make_abs(src) if callable(make_abs) else src
                
            book = Book(
                name=name or "",
                description=description,
                category=category,
                price_including_tax=price_incl,
                price_excluding_tax=price_excl,
                availability=availability,
                number_of_reviews=reviews,
                image_url=image_url,
                rating=rating,
                source_url=url,
                raw_html=text,
                status="fetched"
            )   
            # serialize book object
            mongo_document = book.model_dump(mode='json')
            await self.mongo.upsert_book(mongo_document)
        except Exception as e:
            # Save failed state for this URL
            await self.mongo.upsert_book({
                'source_url': url,
                'status': 'failed',
                'crawl_timestamp': Book().crawl_timestamp if False else __import__('datetime').datetime.utcnow(),
                'raw_html': None,
                'error': str(e)
            })
    
    def stop(self):
        self._stop = True
    