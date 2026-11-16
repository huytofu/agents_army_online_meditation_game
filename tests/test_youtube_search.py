import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from forest_server.app import app
from forest_server.youtube_search import search_videos

pytestmark = pytest.mark.asyncio


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"status {self.status}")

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    async def get(self, url, params=None):
        self.calls.append((url, params))
        if self.error:
            raise self.error
        return self.response


async def test_missing_key_does_not_call_youtube():
    client = FakeClient()
    result = await search_videos("forest rain", None, client)
    assert result == {"ok": False, "reason": "unconfigured"}
    assert client.calls == []


async def test_empty_query_does_not_call_youtube():
    client = FakeClient()
    result = await search_videos("   ", "secret-key", client)
    assert result == {"ok": False, "reason": "empty"}
    assert client.calls == []


async def test_search_returns_titles_without_the_key():
    client = FakeClient(FakeResponse({
        "items": [
            {
                "id": {"videoId": "eKFTSSKCzWA"},
                "snippet": {"title": "Forest waterfall", "channelTitle": "johnnielawson"},
            },
            {"id": {"kind": "youtube#channel"}, "snippet": {"title": "Skip me"}},
        ]
    }))
    result = await search_videos("forest", "secret-key", client)
    assert result == {
        "ok": True,
        "results": [{"id": "eKFTSSKCzWA", "title": "Forest waterfall", "channel": "johnnielawson"}],
    }
    assert "secret-key" not in str(result)
    url, params = client.calls[0]
    assert url == "https://www.googleapis.com/youtube/v3/search"
    assert params["key"] == "secret-key"
    assert params["q"] == "forest"
    assert params["part"] == "snippet"
    assert params["type"] == "video"
    assert params["maxResults"] == 8


async def test_failed_request_stays_on_the_server():
    client = FakeClient(error=RuntimeError("down"))
    result = await search_videos("forest", "secret-key", client)
    assert result == {"ok": False, "reason": "failed"}


async def test_route_hides_a_missing_key_and_a_missing_session(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    calls = []

    async def fake_get(self, url, params=None):
        calls.append(url)
        raise AssertionError("youtube was called")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            missing = await client.post("/api/youtube/search", json={"token": "nope", "q": "forest"})
            assert missing.json() == {"ok": False, "reason": "missing"}
            opened = await client.post("/api/session", json={"token": None})
            result = await client.post(
                "/api/youtube/search",
                json={"token": opened.json()["token"], "q": "forest"},
            )
            assert result.json() == {"ok": False, "reason": "unconfigured"}
    assert calls == []
