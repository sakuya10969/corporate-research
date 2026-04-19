class CollectionError(Exception):
    """情報収集に失敗した場合の例外"""


class AnalysisError(Exception):
    """AI分析処理に失敗した場合の例外"""


class ExternalServiceError(Exception):
    """外部サービス（Azure AI Foundry等）が利用不可の場合の例外"""
