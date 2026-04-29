"""ジョブ管理モジュール — バックグラウンドパイプラインのオーケストレーション"""

from src.jobs.router import router as jobs_router

__all__ = ["jobs_router"]
