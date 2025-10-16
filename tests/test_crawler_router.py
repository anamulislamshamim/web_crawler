# tests/test_crawler_router.py
import pytest
from unittest.mock import patch, AsyncMock
from settings import API_KEY_NAME, SITE_KEY


@pytest.mark.anyio
async def test_start_crawl_endpoint(test_app):
    # Patch the AsyncBookCrawler to avoid real network calls
    with patch("app.routers.crawler_router.AsyncBookCrawler") as MockCrawler:
        mock_instance = AsyncMock()
        MockCrawler.return_value = mock_instance

        response = await test_app.post(
            f"/crawler/start/{SITE_KEY}",
            headers={"x-api-key": API_KEY_NAME}
        )

        # Assert response is correct
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["site_key"] == SITE_KEY

        # Ensure the crawler was initialized with the site key
        MockCrawler.assert_called()
        mock_instance.crawl.assert_called_with(resume=False)


@pytest.mark.anyio
async def test_stop_crawl_endpoint(test_app):
    response = await test_app.post(
        f"/crawler/stop/{SITE_KEY}",
        headers={"x-api-key": API_KEY_NAME}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["site_key"] == SITE_KEY


@pytest.mark.anyio
async def test_resume_crawl_endpoint(test_app):
    with patch("app.routers.crawler_router.AsyncBookCrawler") as MockCrawler:
        mock_instance = AsyncMock()
        MockCrawler.return_value = mock_instance

        response = await test_app.post(
            F"/crawler/resume/{SITE_KEY}",
            headers={"x-api-key": API_KEY_NAME}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resumed"
        assert data["site_key"] == SITE_KEY

        MockCrawler.assert_called()
        mock_instance.crawl.assert_called_with(resume=False)
