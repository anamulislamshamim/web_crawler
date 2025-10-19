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
async def daily_report_generate(
    request: Request,
    format: str = "json",
    mongo: MongoStorage = Depends(get_mongo)
):
    """
    Generate a daily change report (JSON or CSV) based on today's timestamp.
    """
    mongo = request.app.state.mongo
    
    # Current UTC time
    now = datetime.now(timezone.utc)
    # 24 hours ago
    start = now - timedelta(hours=24)
    # Query MongoDB for documents within last 24 hour
    cursor = mongo.book_changes.find({})

    changes = await cursor.to_list(length=None)
    print("Debug:", len(changes), " start_time:", start)
    # CSV format
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["source_url", "change_type", "changes", "timestamp"])
        for c in changes:
            writer.writerow([
                c.get("source_url", ""),
                c.get("change_type", ""),
                json.dumps(c.get("changes", {}), ensure_ascii=False),
                c.get("timestamp").isoformat() if "timestamp" in c else ""
            ])
        return Response(content=output.getvalue(), media_type="text/csv")

    # Default JSON format
    for c in changes:
        c["_id"] = str(c["_id"])
        if "timestamp" in c and isinstance(c["timestamp"], datetime):
            c["timestamp"] = c["timestamp"].isoformat()

    if changes:
        return changes

    return {"status": "No change!"}