"""分析モジュール — DB モデル ↔ レスポンス変換ユーティリティ"""

from __future__ import annotations

from src.analysis.schemas import (
    AnalysisResponse,
    RawSource,
    ScoreData,
    SourceInfo,
    StructuredData,
    SummaryData,
)
from src.db.models import AnalysisResult as AnalysisResultModel


def model_to_response(
    model: AnalysisResultModel, is_cached: bool = False
) -> AnalysisResponse:
    """DB モデル → AnalysisResponse 変換"""
    structured = StructuredData.model_validate(model.structured)
    summary = SummaryData.model_validate(model.summary)
    scores = ScoreData.model_validate(model.scores) if model.scores else None
    sources = [SourceInfo.model_validate(s) for s in (model.sources or [])]
    raw_sources = [RawSource.model_validate(s) for s in (model.raw_sources or [])]
    return AnalysisResponse(
        company_url=model.company.primary_url if model.company else "",
        result_id=model.result_id,
        company_id=model.company_id,
        is_cached=is_cached,
        analyzed_at=model.created_at,
        structured=structured,
        summary=summary,
        scores=scores,
        sources=sources,
        raw_sources=raw_sources,
        markdown_page=model.markdown_page or "",
        diff_report=model.diff_report or "",
        template=model.template,
    )
