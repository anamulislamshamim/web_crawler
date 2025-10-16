# Shared fixtures: FastAPI client, mock DB, etc
import pytest
from httpx import AsyncClient, ASGITransport
import mongomock
from fastapi import FastAPI

from app.main import app 
from core import deps


class MockCursor:
    """Mimics Motor cursor with async chaining and iteration."""
    def __init__(self, docs):
        self.docs = list(docs)
        self._skip = 0
        self._limit = len(self.docs)

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def sort(self, *args, **kwargs):
        # Sorting can be skipped for now; implement if needed
        return self

    async def to_list(self, length=None):
        return self.docs[self._skip:self._skip + self._limit]

    def __aiter__(self):
        async def gen():
            for doc in self.docs[self._skip:self._skip + self._limit]:
                yield doc
        return gen()


class AsyncMockCollection:
    """Async-compatible wrapper for mongomock collections."""
    def __init__(self, collection):
        self._collection = collection

    async def insert_one(self, doc):
        return self._collection.insert_one(doc)

    async def find_one(self, query, projection=None):
        return self._collection.find_one(query, projection)

    def find(self, query=None, projection=None):
        # ✅ Return a mock cursor that supports skip/limit chaining
        query = query or {}
        docs = list(self._collection.find(query, projection))
        return MockCursor(docs)

    async def count_documents(self, query):
        return self._collection.count_documents(query)


class MockMongoStorage:
    """Async-compatible Mock MongoDB Storage with in-memory data."""
    def __init__(self):
        db = mongomock.MongoClient().db
        self.books = AsyncMockCollection(db.books)
        self.book_changes = AsyncMockCollection(db.book_change_logs)

    async def insert_book(self, book_data):
        return await self.books.insert_one(book_data)

    async def find_books(self, query=None):
        cursor = self.books.find(query)
        return await cursor.to_list(length=None)

    async def find_one_book(self, book_id):
        return await self.books.find_one({"_id": book_id})


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def mock_mongo():
    """Fixture that provides an in-memory MongoDB mock."""
    return MockMongoStorage()


@pytest.fixture
async def test_app(mock_mongo):
    """Attach mock DB to FastAPI app and return async test client."""
    app.dependency_overrides[deps.get_mongo] = lambda: mock_mongo
    app.state.mongo = mock_mongo  # Attach directly to app state
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides = {}
