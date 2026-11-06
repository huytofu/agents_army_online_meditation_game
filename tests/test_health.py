import pytest
from httpx import ASGITransport, AsyncClient

from forest_server.app import app


@pytest.mark.asyncio
async def test_health_reports_database_and_zero_spots():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok", "spots": 0}
