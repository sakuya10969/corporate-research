"""共通HTTPクライアント — リトライ・タイムアウト・ヘッダー管理"""

import httpx

from src.shared.logger import logger

DEFAULT_TIMEOUT = 15.0
MAX_RETRIES = 2

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.9",
}


async def fetch_page(
    client: httpx.AsyncClient,
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = MAX_RETRIES,
) -> str | None:
    """URLからHTMLを取得する。失敗時はリトライし、最終的にNoneを返す。"""
    for attempt in range(1, retries + 1):
        try:
            resp = await client.get(
                url,
                headers=BROWSER_HEADERS,
                timeout=timeout,
                follow_redirects=True,
            )
            resp.raise_for_status()
            logger.debug("取得成功: {} ({})", url, resp.status_code)
            return resp.text
        except httpx.HTTPError as e:
            logger.warning("取得失敗 (試行{}/{}): {} - {}", attempt, retries, url, e)
            if attempt == retries:
                return None
    return None


def create_client() -> httpx.AsyncClient:
    """共通設定済みの非同期HTTPクライアントを生成する。"""
    return httpx.AsyncClient(headers=BROWSER_HEADERS, timeout=DEFAULT_TIMEOUT)
