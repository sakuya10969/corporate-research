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


def generate_markdown_report(
    company_url: str,
    structured: dict,
    summary: dict,
    sources: list[dict],
) -> str:
    """構造化データ・要約データからMarkdownレポートを生成する。"""
    lines: list[str] = []

    profile = structured.get("company_profile", {})
    company_name = profile.get("name", "") or company_url

    lines.append(f"# {company_name}")
    lines.append("")
    lines.append(f"URL: {company_url}")
    lines.append("")

    # --- 企業プロフィール ---
    if any(profile.get(k) for k in ("name", "founded", "ceo", "location", "employees", "capital")):
        lines.append("## 企業プロフィール")
        lines.append("")
        _field_labels = [
            ("name", "社名"), ("founded", "設立"), ("ceo", "代表者"),
            ("location", "所在地"), ("employees", "従業員数"), ("capital", "資本金"),
        ]
        for key, label in _field_labels:
            val = profile.get(key, "")
            if val:
                lines.append(f"- {label}: {val}")
        lines.append("")

    # --- 事業領域 ---
    domains = structured.get("business_domains", [])
    if domains:
        lines.append("## 事業領域")
        lines.append("")
        for d in domains:
            lines.append(f"- {d}")
        lines.append("")

    # --- プロダクト一覧 ---
    products = structured.get("products", [])
    if products:
        lines.append("## プロダクト・サービス")
        lines.append("")
        for p in products:
            lines.append(f"- {p}")
        lines.append("")

    # --- 財務情報 ---
    fin = structured.get("financials", {})
    if any(fin.get(k) for k in ("revenue", "operating_income", "net_income", "growth_rate")):
        lines.append("## 財務情報")
        lines.append("")
        _fin_labels = [
            ("revenue", "売上高"), ("operating_income", "営業利益"),
            ("net_income", "純利益"), ("growth_rate", "成長率"),
        ]
        for key, label in _fin_labels:
            val = fin.get(key, "")
            if val:
                lines.append(f"- {label}: {val}")
        lines.append("")

    # --- ニュース ---
    news = structured.get("news", [])
    if news:
        lines.append("## ニュース")
        lines.append("")
        for n in news:
            date_str = f" ({n['date']})" if n.get("date") else ""
            lines.append(f"- {n.get('title', '')}{date_str}")
            if n.get("summary"):
                lines.append(f"  - {n['summary']}")
        lines.append("")

    # --- 企業概要サマリー ---
    overview = summary.get("overview", "")
    if overview:
        lines.append("## 企業概要")
        lines.append("")
        lines.append(overview)
        lines.append("")

    # --- 事業モデル ---
    biz_model = summary.get("business_model", "")
    if biz_model:
        lines.append("## 事業モデル")
        lines.append("")
        lines.append(biz_model)
        lines.append("")

    # --- SWOT ---
    swot = summary.get("swot", {})
    if any(swot.get(k) for k in ("strengths", "weaknesses", "opportunities", "threats")):
        lines.append("## SWOT分析")
        lines.append("")
        _swot_labels = [
            ("strengths", "強み"), ("weaknesses", "弱み"),
            ("opportunities", "機会"), ("threats", "脅威"),
        ]
        for key, label in _swot_labels:
            items = swot.get(key, [])
            if items:
                lines.append(f"### {label}")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")

    # --- リスク要因 ---
    risks = summary.get("risks", [])
    if risks:
        lines.append("## リスク要因")
        lines.append("")
        for r in risks:
            lines.append(f"- {r}")
        lines.append("")

    # --- 競合企業 ---
    competitors = summary.get("competitors", [])
    if competitors:
        lines.append("## 競合企業（推定）")
        lines.append("")
        for c in competitors:
            lines.append(f"- {c}")
        lines.append("")

    # --- 今後の展望 ---
    outlook = summary.get("outlook", "")
    if outlook:
        lines.append("## 今後の展望")
        lines.append("")
        lines.append(outlook)
        lines.append("")

    # --- 参照ソース ---
    if sources:
        lines.append("## 参照ソース")
        lines.append("")
        for s in sources:
            cat = f" [{s.get('category', '')}]" if s.get("category") and s["category"] != "その他" else ""
            lines.append(f"- [{s.get('title', s.get('url', ''))}]({s.get('url', '')}){cat}")
        lines.append("")

    return "\n".join(lines)


def generate_diff_report(
    current_structured: dict,
    previous_structured: dict | None,
) -> str:
    """現在と過去の構造化データを比較し、差分レポートを生成する。

    過去データがない場合は空文字列を返す。
    """
    if not previous_structured:
        return ""

    diffs: list[str] = []

    # ニュースの差分
    current_news = {n.get("title", "") for n in current_structured.get("news", [])}
    previous_news = {n.get("title", "") for n in previous_structured.get("news", [])}
    new_news = current_news - previous_news
    if new_news:
        diffs.append("## 新しいニュース")
        for title in new_news:
            diffs.append(f"- {title}")
        diffs.append("")

    # プロダクトの差分
    current_products = set(current_structured.get("products", []))
    previous_products = set(previous_structured.get("products", []))
    new_products = current_products - previous_products
    if new_products:
        diffs.append("## 新しいプロダクト")
        for p in new_products:
            diffs.append(f"- {p}")
        diffs.append("")

    # 会社概要の変更
    current_profile = current_structured.get("company_profile", {})
    previous_profile = previous_structured.get("company_profile", {})
    profile_changes: list[str] = []
    for key in ("name", "ceo", "location", "employees", "capital"):
        cur = current_profile.get(key, "")
        prev = previous_profile.get(key, "")
        if cur and prev and cur != prev:
            profile_changes.append(f"- {key}: {prev} → {cur}")
    if profile_changes:
        diffs.append("## 会社概要の変更")
        diffs.extend(profile_changes)
        diffs.append("")

    # 財務情報の変更
    current_fin = current_structured.get("financials", {})
    previous_fin = previous_structured.get("financials", {})
    fin_changes: list[str] = []
    for key in ("revenue", "operating_income", "net_income", "growth_rate"):
        cur = current_fin.get(key, "")
        prev = previous_fin.get(key, "")
        if cur and prev and cur != prev:
            fin_changes.append(f"- {key}: {prev} → {cur}")
    if fin_changes:
        diffs.append("## 財務情報の変更")
        diffs.extend(fin_changes)
        diffs.append("")

    if not diffs:
        return "変更は検出されませんでした。"

    return "\n".join(["# 差分レポート", ""] + diffs)
