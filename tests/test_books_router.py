# tests/test_books_router.py
import pytest
from bson import ObjectId
from settings import API_KEY_NAME


@pytest.fixture
async def sample_book():
    return {
        "_id": ObjectId("68f0c1232a4f50cf3bdfb702"),
        "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "availability": "In stock (22 available)",
        "category": "Poetry",
        "crawl_timestamp": "2025-10-16T09:56:53.780004Z",
        "description": "Shel, you never sounded so good. ...more",
        "image_url": "http://books.toscrape.com/catalogue/media/cache/fe/72/fe72f0532301ec28892ae79a629a293c.jpg",
        "name": "A Light in the Attic",
        "number_of_reviews": 0,
        "price_excluding_tax": {"amount": 51.77, "currency": "£"},
        "price_including_tax": {"amount": 51.77, "currency": "£"},
        "rating": "Three",
        "raw_html": "",
        "status": "fetched"
    }


@pytest.mark.anyio
async def test_get_books_list(test_app, mock_mongo, sample_book):
    await mock_mongo.insert_book(sample_book)

    response = await test_app.get("/books", headers={"x-api-key": API_KEY_NAME})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "A Light in the Attic"


@pytest.mark.anyio
async def test_get_books_filtered_by_category(test_app, mock_mongo, sample_book):
    await mock_mongo.insert_book(sample_book)

    response = await test_app.get("/books?category=Poetry", headers={"x-api-key": API_KEY_NAME})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["category"] == "Poetry"


@pytest.mark.anyio
async def test_get_book_detail(test_app, mock_mongo, sample_book):
    await mock_mongo.insert_book(sample_book)
    book_id = str(sample_book["_id"])

    response = await test_app.get(f"/books/{book_id}", headers={"x-api-key": API_KEY_NAME})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "A Light in the Attic"
    assert data["category"] == "Poetry"
