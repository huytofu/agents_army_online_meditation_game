import pytest
from httpx import ASGITransport, AsyncClient

from forest_server.app import app


@pytest.mark.asyncio
async def test_health_reports_seeded_spots_once():
    seen = []
    for _ in range(2):
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")
        assert response.status_code == 200
        seen.append(response.json())
    assert seen[0] == {"status": "ok", "db": "ok", "spots": 1500}
    assert seen[1] == seen[0]
