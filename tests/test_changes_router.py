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
        "change_type": "price_update",
        "changes": {"price": {"old": 50.0, "new": 51.77}},
        "timestamps": now
    }

@pytest.mark.anyio
async def test_changes_report_json(test_app, mock_mongo, sample_change):
    # Insert sample change log
    await mock_mongo.book_changes.insert_one(sample_change)

    response = await test_app.get("/changes/report?format=json", headers={"x-api-key": API_KEY_NAME})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    change = data[0]
    assert change["source_url"] == sample_change["source_url"]
    assert change["change_type"] == "price_update"
    assert change["changes"]["price"]["new"] == 51.77

@pytest.mark.anyio
async def test_changes_report_csv(test_app, mock_mongo, sample_change):
    # Insert sample change log
    await mock_mongo.book_changes.insert_one(sample_change)

    response = await test_app.get("/changes/report?format=csv", headers={"x-api-key": API_KEY_NAME})
    assert response.status_code == 200
    content_type = response.headers.get("content-type")
    assert "text/csv" in content_type

    content = response.text
    # Check CSV header
    assert "source_url,change_type,changes,timestamp" in content
    # Check row content
    assert sample_change["source_url"] in content
    assert "price_update" in content