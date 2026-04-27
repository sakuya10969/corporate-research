"""企業名検索サービス（F-011）— DuckDuckGo Instant Answer API"""

from __future__ import annotations

import httpx

from src.shared.logger import logger


async def search_company_url(query: str, limit: int = 5) -> list[dict]:
    """DuckDuckGo Instant Answer API で企業の公式 URL 候補を返す"""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("DuckDuckGo 検索エラー: {}", e)
        return []

    results: list[dict] = []

    # AbstractURL（最も信頼性が高い）
    if data.get("AbstractURL"):
        results.append({"name": data.get("Heading", query), "url": data["AbstractURL"]})

    # RelatedTopics
    for topic in data.get("RelatedTopics", []):
        if len(results) >= limit:
            break
        if isinstance(topic, dict) and topic.get("FirstURL"):
            name = topic.get("Text", "")[:50]
            results.append({"name": name, "url": topic["FirstURL"]})

    return results[:limit]
