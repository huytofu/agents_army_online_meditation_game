"""Look up public videos through the YouTube Data API. The key stays on the server."""

import os
import re

import httpx

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _results(payload):
    found = []
    for item in payload.get("items") or []:
        video_id = (item.get("id") or {}).get("videoId")
        if not isinstance(video_id, str) or VIDEO_ID.fullmatch(video_id) is None:
            continue
        snippet = item.get("snippet") or {}
        found.append({
            "id": video_id,
            "title": str(snippet.get("title") or ""),
            "channel": str(snippet.get("channelTitle") or ""),
        })
        if len(found) == 8:
            break
    return found


async def search_videos(query: str, api_key: str | None, client) -> dict:
    if not api_key:
        return {"ok": False, "reason": "unconfigured"}
    text = query.strip()
    if not text:
        return {"ok": False, "reason": "empty"}
    try:
        response = await client.get(SEARCH_URL, params={
            "part": "snippet",
            "type": "video",
            "maxResults": 8,
            "q": text,
            "key": api_key,
        })
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return {"ok": False, "reason": "failed"}
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "failed"}
    return {"ok": True, "results": _results(payload)}


def api_key() -> str | None:
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    return key or None


async def search_with_server_key(query: str) -> dict:
    async with httpx.AsyncClient(timeout=8) as client:
        return await search_videos(query, api_key(), client)
