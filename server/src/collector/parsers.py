"""HTML パーサー — 構造保持抽出・メタデータ抽出・ページ分類"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

# ---------------------------------------------------------------------------
# ページカテゴリ分類キーワード
# ---------------------------------------------------------------------------
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "会社概要": [
        "会社概要",
        "企業情報",
        "about",
        "company",
        "corporate",
        "会社情報",
        "企業概要",
        "沿革",
        "history",
        "経営理念",
        "philosophy",
        "代表挨拶",
        "役員",
        "組織",
    ],
    "事業内容": [
        "事業内容",
        "事業紹介",
        "business",
        "事業領域",
        "事業案内",
        "ソリューション",
        "solution",
    ],
    "プロダクト・サービス": [
        "製品",
        "サービス",
        "product",
        "service",
        "プロダクト",
        "ラインナップ",
        "lineup",
    ],
    "IR・財務情報": [
        "ir",
        "investor",
        "株主",
        "財務",
        "決算",
        "有価証券",
        "annual report",
        "業績",
        "financial",
    ],
    "プレスリリース・ニュース": [
        "ニュース",
        "news",
        "プレスリリース",
        "press",
        "お知らせ",
        "topics",
        "新着情報",
        "release",
    ],
    "採用情報": [
        "採用",
        "recruit",
        "career",
        "キャリア",
        "求人",
        "jobs",
        "新卒",
        "中途",
    ],
}


def extract_title(html: str) -> str:
    """<title> タグからページタイトルを抽出する。"""
    soup = BeautifulSoup(html, "lxml")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    # OGP fallback
    og = soup.find("meta", property="og:title")
    if og and isinstance(og, Tag) and og.get("content"):
        return str(og["content"]).strip()
    return ""


def extract_meta(html: str) -> dict[str, str]:
    """OGP・meta description 等のメタデータを抽出する。"""
    soup = BeautifulSoup(html, "lxml")
    meta: dict[str, str] = {}

    desc = soup.find("meta", attrs={"name": "description"})
    if desc and isinstance(desc, Tag) and desc.get("content"):
        meta["description"] = str(desc["content"]).strip()

    for prop in ("og:title", "og:description", "og:site_name", "og:type"):
        tag = soup.find("meta", property=prop)
        if tag and isinstance(tag, Tag) and tag.get("content"):
            meta[prop] = str(tag["content"]).strip()

    return meta


def extract_body_text(html: str) -> str:
    """HTMLから本文テキストを構造保持しつつ抽出する。

    - script/style/nav/footer/header/aside を除去
    - main/article/section を優先
    - 表（table）・箇条書き（ul/ol）は構造を保持
    """
    soup = BeautifulSoup(html, "lxml")

    # 不要タグ除去
    for tag in soup(
        ["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]
    ):
        tag.decompose()

    # main/article/section を優先的に探す
    content_root = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", role="main")
        or soup.body
        or soup
    )

    return _extract_structured_text(content_root)


def _extract_structured_text(element: Tag | BeautifulSoup) -> str:
    """要素から構造を保持したテキストを再帰的に抽出する。"""
    parts: list[str] = []

    for child in element.children:
        if isinstance(child, Tag):
            if child.name in ("table",):
                parts.append(_extract_table(child))
            elif child.name in ("ul", "ol"):
                parts.append(_extract_list(child))
            elif child.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                text = child.get_text(strip=True)
                if text:
                    level = int(child.name[1])
                    prefix = "#" * level
                    parts.append(f"\n{prefix} {text}\n")
            elif child.name in ("p", "div", "section", "article", "blockquote"):
                inner = _extract_structured_text(child)
                if inner.strip():
                    parts.append(inner + "\n")
            elif child.name in ("dl",):
                parts.append(_extract_dl(child))
            else:
                text = child.get_text(strip=True)
                if text:
                    parts.append(text)
        else:
            text = str(child).strip()
            if text:
                parts.append(text)

    return "\n".join(parts)


def _extract_table(table: Tag) -> str:
    """テーブルをMarkdown風テキストに変換する。"""
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    lines: list[str] = []
    for i, row in enumerate(rows):
        lines.append("| " + " | ".join(row) + " |")
        if i == 0:
            lines.append("| " + " | ".join("---" for _ in row) + " |")
    return "\n".join(lines)


def _extract_list(ul: Tag) -> str:
    """ul/ol をインデント付きリストテキストに変換する。"""
    items: list[str] = []
    for li in ul.find_all("li", recursive=False):
        text = li.get_text(strip=True)
        if text:
            items.append(f"- {text}")
    return "\n".join(items)


def _extract_dl(dl: Tag) -> str:
    """定義リスト（dl）をテキストに変換する。"""
    parts: list[str] = []
    current_dt = ""
    for child in dl.children:
        if isinstance(child, Tag):
            if child.name == "dt":
                current_dt = child.get_text(strip=True)
            elif child.name == "dd":
                dd_text = child.get_text(strip=True)
                if current_dt:
                    parts.append(f"{current_dt}: {dd_text}")
                    current_dt = ""
                else:
                    parts.append(dd_text)
    return "\n".join(parts)


def classify_page(url: str, title: str, content: str) -> str:
    """URL・タイトル・本文からページカテゴリを推定する。"""
    text_lower = f"{url} {title} {content[:500]}".lower()

    scores: dict[str, int] = {}
    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "その他"
    return max(scores, key=scores.get)  # type: ignore[arg-type]


def extract_internal_links(html: str, base_url: str) -> list[str]:
    """HTMLから同一ドメインの内部リンクを抽出する。"""
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    links: list[str] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if isinstance(href, list):
            href = href[0]

        # フラグメントのみ、javascript:、mailto: を除外
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # 同一ドメインのみ
        if parsed.netloc != base_domain:
            continue

        # 正規化（フラグメント除去）
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean.endswith("/"):
            clean = clean[:-1]

        # 静的ファイルを除外
        if re.search(
            r"\.(pdf|jpg|jpeg|png|gif|svg|css|js|zip|xlsx?)$", clean, re.IGNORECASE
        ):
            continue

        if clean not in seen:
            seen.add(clean)
            links.append(clean)

    return links


def extract_sitemap_urls(xml_text: str) -> list[str]:
    """sitemap.xml からURLリストを抽出する。"""
    soup = BeautifulSoup(xml_text, "lxml-xml")
    urls: list[str] = []

    # 通常の sitemap
    for loc in soup.find_all("loc"):
        url = loc.get_text(strip=True)
        if url:
            urls.append(url)

    return urls
