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


@router.get("/report")
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
        writer.writerow(['source_url', 'change_type', 'changes', 'timestamp'])
        for c in changes:
            writer.writerow([c['source_url'], c['change_type'], json.dumps(c['changes']), c['timestamp']])
        return Response(content=output.getvalue(), media_type='text/csv') 

    # default JSON
    for c in changes:
        c['_id'] = str(c['_id'])
    
    if changes:
        return changes
    
    return {"status": "no changes detected yet!"}