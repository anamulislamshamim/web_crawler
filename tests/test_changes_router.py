# tests/test_changes_router.py
import pytest
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import json
from settings import API_KEY_NAME

@pytest.fixture
async def sample_change():
    """Sample change log document."""
    now = datetime.now(timezone.utc)
    return {
        "_id": ObjectId(),
        "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "change_type": "update",
        "changes": {"price": {"old": 50.0, "new": 51.77}},
        "timestamps": now
    }

@pytest.mark.anyio
async def test_changes_report_json(test_app, mock_mongo, sample_change):
    # Insert sample change log
    await mock_mongo.book_changes.insert_one(sample_change)

    response = await test_app.get("/changes/report?format=json", headers={"x-api-key": API_KEY_NAME})
    assert response.status_code == 200
    content_type = response.headers.get("content-type")
    assert "application/json" in content_type

@pytest.mark.anyio
async def test_changes_report_csv(test_app, mock_mongo, sample_change):
    # Insert sample change log
    await mock_mongo.book_changes.insert_one(sample_change)

    response = await test_app.get("/changes/report?format=csv", headers={"x-api-key": API_KEY_NAME})
    assert response.status_code == 200
    content_type = response.headers.get("content-type")
    assert "text/csv" in content_type