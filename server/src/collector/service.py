"""情報収集サービス — 企業URL基点のサイトマップ探索・内部リンク探索

Google検索は使用しない。入力は企業URLのみ。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from urllib.parse import urlparse

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

# サイトマップから優先的に取得するページのキーワード
_SITEMAP_PRIORITY_KEYWORDS = [
    "about",
    "company",
    "corporate",
    "business",
    "service",
    "product",
    "ir",
    "investor",
    "news",
    "press",
    "recruit",
    "career",
    "会社概要",
    "企業情報",
    "事業",
    "サービス",
    "製品",
    "ニュース",
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
    company_url: str
    sources: list[SourceInfo]
    raw_content: str
    classified_sections: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# URL正規化
# ---------------------------------------------------------------------------


def _normalize_base_url(url: str) -> str:
    """入力URLからベースURL（スキーム + ドメイン）を正規化する。"""
    parsed = urlparse(url.strip())
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc
    if not netloc:
        raise CollectionError(f"無効なURLです: {url}")
    return f"{scheme}://{netloc}"


# ---------------------------------------------------------------------------
# サイトマップ探索
# ---------------------------------------------------------------------------


async def _fetch_sitemap_urls(client, base_url: str) -> list[str]:
    """サイトマップからURL一覧を取得する。"""
    sitemap_url = f"{base_url}/sitemap.xml"
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
    client,
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


async def _fetch_and_parse(client, url: str) -> SourceInfo | None:
    """単一ページを取得し、構造化テキストを抽出する。"""
    html = await fetch_page(client, url)
    if not html:
        return None

    title = extract_title(html)
    body = extract_body_text(html)
    meta = extract_meta(html)

    if not body or len(body.strip()) < 50:
        logger.debug(
            "本文が短すぎるためスキップ: {} ({}文字)", url, len(body) if body else 0
        )
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
# メインエントリポイント
# ---------------------------------------------------------------------------


async def collect_company_info(company_url: str) -> CompanyInfo:
    """企業URLを基点に情報を収集・構造化する。

    Google検索は使用しない。サイトマップ or 内部リンク探索のみ。

    1. URL正規化（スキーム + ドメイン抽出）
    2. サイトマップ探索 → 優先度付きURL選定
    3. サイトマップなし → トップページから内部リンク探索（深さ2）
    4. 各ページを並行取得・解析・分類
    5. 前処理済みデータを構造化して返却
    """
    logger.info("情報収集開始: {}", company_url)

    try:
        base_url = _normalize_base_url(company_url)
    except CollectionError:
        raise

    try:
        async with create_client() as client:
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

            if not target_urls:
                raise CollectionError(
                    f"対象ページが見つかりませんでした: {company_url}"
                )

            # 並行取得
            tasks = [_fetch_and_parse(client, url) for url in target_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            sources: list[SourceInfo] = []
            for result in results:
                if isinstance(result, SourceInfo):
                    sources.append(result)
                elif isinstance(result, Exception):
                    logger.warning("ページ解析エラー: {}", result)

            if not sources:
                raise CollectionError(f"企業情報を取得できませんでした: {company_url}")

            logger.info("情報収集完了: {} ({} ソース)", company_url, len(sources))

            # 分類済みセクション構築
            classified_sections = [
                {
                    "category": src.category,
                    "title": src.title,
                    "url": src.url,
                    "content": src.content,
                }
                for src in sources
            ]

            # LLM向けコンテキスト整形
            from src.shared.text import build_llm_context

            raw_content = build_llm_context(classified_sections)

            return CompanyInfo(
                company_url=company_url,
                sources=sources,
                raw_content=raw_content,
                classified_sections=classified_sections,
            )

    except CollectionError:
        raise
    except Exception as e:
        logger.error("情報収集中に予期しないエラー: {}", e)
        raise CollectionError(f"情報収集中にエラーが発生しました: {e}") from e
