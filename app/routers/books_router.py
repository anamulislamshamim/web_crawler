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
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    rating: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, description='rating, price, reviews'),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List books with filters, sorting, and pagination."""
    mongo = request.app.state.mongo
    query = {}
    if category:
        query['category'] = {'$regex': f'^{category}$', '$options': 'i'}
    
    # Price range filters on price_including_tax.amount
    if min_price is not None or max_price is not None:
        price_q = {}
        if not min_price:
            price_q["$gte"] = min_price
        if not max_price:
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
    
    cursor = mongo.books.find(query)
    if sort:
        cursor.sort(sort)
    cursor = cursor.skip((page - 1) * per_page).limit(per_page)
    items = await cursor.to_list(length=per_page)
    items = [serialize_doc(i) for i in items]
    
    return BookListResponse(total=total, page=page, per_page=per_page, total_pages=total_pages, items=items)

@router.get('/books/{book_id}')
async def get_book(bookd_id: str, request: Request):
    '''Return full details about a single book by object id.'''
    mongo = request.app.state.mongo
    try:
        oid = ObjectId(bookd_id)
    except Exception:
        raise HTTPException(status_code=400, detail='invalid book id')
    
    doc = await mongo.books.find_one({'_id': oid})
    if not doc:
        raise HTTPException(status_code=404, detail='book not found')
    return serialize_doc(doc)

@router.get("/report/daily")
async def daily_report(request: Request, format: str = 'json'):
    """Generate a daily change report (JSON or csv)"""
    mongo = request.app.state.mongo
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
