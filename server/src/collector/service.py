from dataclasses import dataclass
from urllib.parse import quote

import httpx

from src.collector.parsers import extract_body_text, extract_title
from src.shared.exceptions import CollectionError

_TIMEOUT = 15.0
_MAX_CONTENT_LENGTH = 8000
_SEARCH_URL = "https://www.google.com/search"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


@dataclass
class SourceInfo:
    url: str
    title: str
    content: str


@dataclass
class CompanyInfo:
    company_name: str
    sources: list[SourceInfo]
    raw_content: str


async def _fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError:
        return None


def _extract_search_urls(html: str) -> list[str]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    urls: list[str] = []
    for a in soup.select("a[href]"):
        href = a["href"]
        if isinstance(href, list):
            href = href[0]
        if href.startswith("/url?q="):
            url = href.split("/url?q=")[1].split("&")[0]
            if url.startswith("http") and "google" not in url:
                urls.append(url)
    return urls[:5]


async def collect_company_info(company_name: str) -> CompanyInfo:
    query = f"{company_name} 企業情報 会社概要"
    search_url = f"{_SEARCH_URL}?q={quote(query)}"

    try:
        async with httpx.AsyncClient() as client:
            search_html = await _fetch_page(client, search_url)
            if not search_html:
                raise CollectionError(f"検索結果を取得できませんでした: {company_name}")

            urls = _extract_search_urls(search_html)
            if not urls:
                raise CollectionError(f"関連ページが見つかりませんでした: {company_name}")

            sources: list[SourceInfo] = []
            for url in urls:
                page_html = await _fetch_page(client, url)
                if not page_html:
                    continue
                title = extract_title(page_html)
                body = extract_body_text(page_html)
                if body:
                    sources.append(SourceInfo(
                        url=url,
                        title=title or url,
                        content=body[:_MAX_CONTENT_LENGTH],
                    ))

            if not sources:
                raise CollectionError(f"企業情報を取得できませんでした: {company_name}")

            raw_content = "\n\n---\n\n".join(
                f"【{s.title}】\n{s.content}" for s in sources
            )

            return CompanyInfo(
                company_name=company_name,
                sources=sources,
                raw_content=raw_content,
            )
    except CollectionError:
        raise
    except Exception as e:
        raise CollectionError(f"情報収集中にエラーが発生しました: {e}") from e
