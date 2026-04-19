"""情報収集サービス — URL正規化・サイトマップ探索・ページ分類付き収集"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from urllib.parse import quote, urlparse

import httpx

from src.collector.parsers import (
    classify_page,
    extract_body_text,
    extract_internal_links,
    extract_meta,
    extract_sitemap_urls,
    extract_title,
)
from src.shared.exceptions import CollectionError
from src.shared.http_client import create_client, fetch_page
from src.shared.logger import logger
from src.shared.text import normalize_whitespace, remove_boilerplate, truncate

_MAX_CONTENT_LENGTH = 10000
_MAX_PAGES = 15
_SEARCH_URL = "https://www.google.com/search"

# サイトマップから優先的に取得するページのキーワード
_SITEMAP_PRIORITY_KEYWORDS = [
    "about", "company", "corporate", "business", "service", "product",
    "ir", "investor", "news", "press", "recruit", "career",
    "会社概要", "企業情報", "事業", "サービス", "製品", "ニュース",
]


@dataclass
class SourceInfo:
    url: str
    title: str
    content: str
    category: str = "その他"
    meta: dict[str, str] = field(default_factory=dict)


@dataclass
class CompanyInfo:
    company_name: str
    sources: list[SourceInfo]
    raw_content: str
    classified_sections: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# URL正規化
# ---------------------------------------------------------------------------

def _normalize_url(input_str: str) -> str | None:
    """入力がURLならそのまま返す。企業名なら None を返す。"""
    input_str = input_str.strip()
    if input_str.startswith(("http://", "https://")):
        return input_str
    # ドメインっぽい入力（例: toyota.co.jp）
    if "." in input_str and " " not in input_str:
        return f"https://{input_str}"
    return None


async def _resolve_company_url(client: httpx.AsyncClient, company_name: str) -> str | None:
    """企業名からGoogle検索で公式サイトURLを推定する。"""
    query = f"{company_name} 公式サイト"
    search_url = f"{_SEARCH_URL}?q={quote(query)}"
    html = await fetch_page(client, search_url)
    if not html:
        return None

    urls = _extract_search_urls(html)
    return urls[0] if urls else None


def _extract_search_urls(html: str) -> list[str]:
    """Google検索結果HTMLからURLを抽出する。"""
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
    return urls[:10]


# ---------------------------------------------------------------------------
# サイトマップ探索
# ---------------------------------------------------------------------------

async def _fetch_sitemap_urls(client: httpx.AsyncClient, base_url: str) -> list[str]:
    """サイトマップからURL一覧を取得する。"""
    parsed = urlparse(base_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    xml = await fetch_page(client, sitemap_url)
    if not xml:
        logger.debug("サイトマップ未検出: {}", sitemap_url)
        return []

    urls = extract_sitemap_urls(xml)
    logger.info("サイトマップから {} URL 取得", len(urls))
    return urls


def _prioritize_sitemap_urls(urls: list[str]) -> list[str]:
    """サイトマップURLを重要度順にソートし、上位を返す。"""
    scored: list[tuple[int, str]] = []
    for url in urls:
        url_lower = url.lower()
        score = sum(1 for kw in _SITEMAP_PRIORITY_KEYWORDS if kw in url_lower)
        # トップページは高優先
        path = urlparse(url).path.strip("/")
        if not path or path == "index.html":
            score += 3
        scored.append((score, url))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [url for _, url in scored[:_MAX_PAGES]]


# ---------------------------------------------------------------------------
# 内部リンク探索（サイトマップがない場合のフォールバック）
# ---------------------------------------------------------------------------

async def _crawl_internal_links(
    client: httpx.AsyncClient,
    base_url: str,
    depth: int = 2,
) -> list[str]:
    """トップページから内部リンクを深さ指定で探索する。"""
    visited: set[str] = set()
    to_visit: list[tuple[str, int]] = [(base_url, 0)]
    found: list[str] = [base_url]

    while to_visit and len(found) < _MAX_PAGES:
        url, current_depth = to_visit.pop(0)
        if url in visited or current_depth > depth:
            continue
        visited.add(url)

        html = await fetch_page(client, url)
        if not html:
            continue

        if current_depth < depth:
            links = extract_internal_links(html, base_url)
            for link in links:
                if link not in visited and link not in [u for u, _ in to_visit]:
                    to_visit.append((link, current_depth + 1))
                    if link not in found:
                        found.append(link)

    return found[:_MAX_PAGES]


# ---------------------------------------------------------------------------
# ページ取得・解析
# ---------------------------------------------------------------------------

async def _fetch_and_parse(client: httpx.AsyncClient, url: str) -> SourceInfo | None:
    """単一ページを取得し、構造化テキストを抽出する。"""
    html = await fetch_page(client, url)
    if not html:
        return None

    title = extract_title(html)
    body = extract_body_text(html)
    meta = extract_meta(html)

    if not body or len(body.strip()) < 50:
        logger.debug("本文が短すぎるためスキップ: {} ({}文字)", url, len(body) if body else 0)
        return None

    # 前処理
    body = remove_boilerplate(body)
    body = normalize_whitespace(body)
    body = truncate(body, _MAX_CONTENT_LENGTH)

    category = classify_page(url, title, body)

    return SourceInfo(
        url=url,
        title=title or url,
        content=body,
        category=category,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Google検索ベースの補完収集
# ---------------------------------------------------------------------------

async def _search_and_collect(
    client: httpx.AsyncClient,
    company_name: str,
) -> list[SourceInfo]:
    """Google検索で企業関連ページを収集する（サイト収集の補完用）。"""
    query = f"{company_name} 企業情報 会社概要 事業内容"
    search_url = f"{_SEARCH_URL}?q={quote(query)}"
    logger.info("補完検索: {}", query)

    html = await fetch_page(client, search_url)
    if not html:
        return []

    urls = _extract_search_urls(html)
    logger.info("検索結果: {} 件", len(urls))

    sources: list[SourceInfo] = []
    tasks = [_fetch_and_parse(client, url) for url in urls[:8]]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, SourceInfo):
            sources.append(result)
        elif isinstance(result, Exception):
            logger.warning("ページ解析エラー: {}", result)

    return sources


# ---------------------------------------------------------------------------
# メインエントリポイント
# ---------------------------------------------------------------------------

async def collect_company_info(company_name: str) -> CompanyInfo:
    """企業情報を収集・構造化する。

    1. 入力がURLか企業名かを判定
    2. 公式サイトURLを特定
    3. サイトマップ or 内部リンク探索でページ一覧を取得
    4. 各ページを取得・解析・分類
    5. Google検索で補完
    6. 前処理済みデータを構造化して返却
    """
    logger.info("情報収集開始: {}", company_name)

    try:
        async with create_client() as client:
            # 1. URL正規化
            base_url = _normalize_url(company_name)

            if not base_url:
                # 企業名 → 公式サイトURL推定
                base_url = await _resolve_company_url(client, company_name)
                if base_url:
                    logger.info("公式サイトURL推定: {}", base_url)

            # 2. サイトからの収集
            site_sources: list[SourceInfo] = []
            if base_url:
                # サイトマップ探索
                sitemap_urls = await _fetch_sitemap_urls(client, base_url)

                if sitemap_urls:
                    target_urls = _prioritize_sitemap_urls(sitemap_urls)
                    logger.info("サイトマップから {} ページを対象に収集", len(target_urls))
                else:
                    # フォールバック: 内部リンク探索
                    logger.info("サイトマップなし → 内部リンク探索")
                    target_urls = await _crawl_internal_links(client, base_url, depth=2)
                    logger.info("内部リンクから {} ページを対象に収集", len(target_urls))

                # 並行取得
                tasks = [_fetch_and_parse(client, url) for url in target_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, SourceInfo):
                        site_sources.append(result)

            # 3. Google検索で補完
            search_sources = await _search_and_collect(client, company_name)

            # 4. 統合（重複URL除去）
            seen_urls: set[str] = set()
            all_sources: list[SourceInfo] = []
            for src in site_sources + search_sources:
                if src.url not in seen_urls:
                    seen_urls.add(src.url)
                    all_sources.append(src)

            if not all_sources:
                raise CollectionError(f"企業情報を取得できませんでした: {company_name}")

            logger.info(
                "情報収集完了: {} ({} ソース, サイト: {}, 検索: {})",
                company_name, len(all_sources), len(site_sources), len(search_sources),
            )

            # 5. 分類済みセクション構築
            classified_sections = [
                {
                    "category": src.category,
                    "title": src.title,
                    "url": src.url,
                    "content": src.content,
                }
                for src in all_sources
            ]

            # 6. raw_content（LLM向けコンテキスト用）
            from src.shared.text import build_llm_context
            raw_content = build_llm_context(classified_sections)

            return CompanyInfo(
                company_name=company_name,
                sources=all_sources,
                raw_content=raw_content,
                classified_sections=classified_sections,
            )

    except CollectionError:
        raise
    except Exception as e:
        logger.error("情報収集中に予期しないエラー: {}", e)
        raise CollectionError(f"情報収集中にエラーが発生しました: {e}") from e
