from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from typing import Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from bson import ObjectId
import math 
import json 
import io 
import csv
from datetime import datetime, timedelta, timezone
from core.deps import get_mongo
from database.storage import MongoStorage


router = APIRouter()


class BookListResponse(BaseModel):
    total: int 
    page: int 
    per_page: int 
    total_pages: int 
    items: list

# Helper to convert Mongo doc to JSON-serializable dict 
def serialize_doc(doc):
    doc['id'] = str(doc.get('_id'))
    doc.pop('_id', None)
    return doc 

@router.get('/books', response_model=BookListResponse)
async def list_books(request: Request, 
    mongo: MongoStorage = Depends(get_mongo),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    rating: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description='rating, price, reviews'),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List books with filters, sorting, and pagination."""
    query = {}
    if category:
        query['category'] = {'$regex': f'^{category}$', '$options': 'i'}
    
    # Price range filters on price_including_tax.amount
    if min_price is not None or max_price is not None:
        price_q = {}
        if min_price is not None:
            price_q["$gte"] = min_price
        if max_price is not None:
            price_q["$lte"] = max_price
        query['price_including_tax.amount'] = price_q
    
    if rating:
        query['rating'] = {"$regex":  f"^{rating}$", "$options": "i"}
        
    sort = []
    if sort_by:
        if sort_by == 'rating':
            # rating stored as word; we map to numeric scale for sorting.
            # pipeline.append({
            #     '$addFields': {
            #         'rating_numeric': {
            #             '$switch': {
            #                 'branches': [
            #                     { 'case': { '$eq': ['$rating', word] }, 'then': num }
            #                     for word, num in RATING_MAP.items()
            #                 ],
            #                 'default': 0 # Fallback for unmapped or bad data
            #             }
            #         }
            #     }
            # })
            # # Sort by the newly created numeric field (highest first)
            # sort = {'rating_numeric': -1}
            sort = [('rating', -1)]
        elif sort_by == 'price':
            sort = [('price_including_tax.amount', 1)]
        elif sort_by == 'reviews':
            sort = [('number_of_reviews', -1)]
    
    total = await mongo.books.count_documents(query)
    total_pages = math.ceil(total / per_page) if total else 0
    
    # 1 means include it, 0 means exclude it
    PROJECTION_FIELDS = {
        '_id': 1,
        'name': 1,
        'rating': 1,
        'category': 1,
        'number_of_reviews': 1,
        'availability': 1,
        'price_including_tax.amount': 1,
    }
    
    cursor = mongo.books.find(query, PROJECTION_FIELDS)
    if sort:
        cursor.sort(sort)
    cursor = cursor.skip((page - 1) * per_page).limit(per_page)
    items = await cursor.to_list(length=per_page)
    items = [serialize_doc(i) for i in items]
    
    return BookListResponse(total=total, page=page, per_page=per_page, total_pages=total_pages, items=items)

@router.get('/books/{book_id}')
async def get_book(book_id: str, request: Request, mongo: MongoStorage = Depends(get_mongo)):
    '''Return full details about a single book by object id.'''
    mongo = request.app.state.mongo
    try:
        oid = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail='invalid book id')
    
    PROJECTION_FIELDS = {
        "_id": 1,
        "availability": 1,
        "category": 1,
        "description": 1,
        "image_url": 1,
        "name": 1,
        "number_of_reviews": 1,
        "price_excluding_tax": 1,
        "price_including_tax": 1,
        "rating": 1
    }
    
    doc = await mongo.books.find_one({'_id': oid}, PROJECTION_FIELDS)
    if not doc:
        raise HTTPException(status_code=404, detail='book not found')
    return serialize_doc(doc)

@router.get("/changes/report")
async def daily_report(request: Request, format: str = 'json', mongo: MongoStorage = Depends(get_mongo)):
    """Generate a daily change report (JSON or csv)"""
    mongo = request.app.state.mongo
    today = datetime.now(timezone.utc).date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today + timedelta(days=1), datetime.min.time())
    
    cursor = mongo.book_changes.find({'timestamps': {'$gte': start, '$lt': end}})
    changes = await cursor.to_list(length=None)
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['source_url', 'change_type', 'changes', 'timestamps'])
        for c in changes:
            writer.writerow([c['source_url'], c['change_type'], json.dumps(c['changes']), c['timestamps']])
        return Response(content=output.getvalue(), media_type='text/csv') 

    # default JSON
    for c in changes:
        c['_id'] = str(c['_id'])
    
    if changes:
        return changes
    
    return {"status": "no changes detected yet!"}
