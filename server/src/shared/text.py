"""テキスト前処理ユーティリティ"""

import re


def normalize_whitespace(text: str) -> str:
    """連続する空白・改行を正規化する。"""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, max_length: int) -> str:
    """テキストを指定文字数で切り詰める。"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "…"


def remove_boilerplate(text: str) -> str:
    """Cookie同意、広告、トラッキング系の定型文を除去する。"""
    patterns = [
        r"(?i)cookie.*?(同意|accept|consent).*?\n",
        r"(?i)copyright\s*©.*?\n",
        r"(?i)all rights reserved.*?\n",
        r"(?i)プライバシーポリシー.*?\n",
        r"(?i)個人情報保護.*?\n",
    ]
    for pat in patterns:
        text = re.sub(pat, "", text)
    return text.strip()


def build_llm_context(sections: list[dict[str, str]], max_total: int = 30000) -> str:
    """カテゴリ分類済みセクションをLLM向けコンテキスト文字列に整形する。

    各セクションは {"category": "...", "title": "...", "url": "...", "content": "..."} の形式。
    カテゴリごとにグルーピングし、優先度順に配置する。
    """
    priority = [
        "会社概要",
        "事業内容",
        "プロダクト・サービス",
        "IR・財務情報",
        "プレスリリース・ニュース",
        "採用情報",
        "その他",
    ]

    by_category: dict[str, list[dict[str, str]]] = {}
    for sec in sections:
        cat = sec.get("category", "その他")
        by_category.setdefault(cat, []).append(sec)

    parts: list[str] = []
    total = 0
    for cat in priority:
        items = by_category.pop(cat, [])
        if not items:
            continue
        part = f"## {cat}\n\n"
        for item in items:
            entry = f"### {item['title']} ({item['url']})\n{item['content']}\n\n"
            if total + len(entry) > max_total:
                break
            part += entry
            total += len(entry)
        parts.append(part)

    # 未分類カテゴリ
    for cat, items in by_category.items():
        part = f"## {cat}\n\n"
        for item in items:
            entry = f"### {item['title']} ({item['url']})\n{item['content']}\n\n"
            if total + len(entry) > max_total:
                break
            part += entry
            total += len(entry)
        parts.append(part)

    return "\n".join(parts)
