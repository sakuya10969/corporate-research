"""Clerk JWT 検証モジュール"""

import time

import httpx
from jose import JWTError, jwt

from src.shared.config import get_settings


# JWKS キャッシュ（TTL: 3600秒）
_jwks_cache: dict = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 3600.0


async def _get_jwks() -> dict:
    """Clerk JWKS エンドポイントから公開鍵を取得する（TTL付きキャッシュ）"""
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache

    settings = get_settings()
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.clerk_jwks_url, timeout=10.0)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_fetched_at = now
        return _jwks_cache


async def verify_clerk_jwt(token: str) -> dict:
    """
    Clerk JWT を検証し、ペイロードを返す。

    検証内容:
    - JWKS による署名検証
    - exp クレームの有効期限検証
    - iss クレームの issuer 検証

    Args:
        token: Bearer トークン文字列

    Returns:
        JWT ペイロード dict

    Raises:
        JWTError: 検証失敗時
    """
    settings = get_settings()
    jwks = await _get_jwks()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},
            issuer=settings.clerk_issuer_url if settings.clerk_issuer_url else None,
        )
        return payload
    except JWTError:
        raise
    except Exception as e:
        raise JWTError(f"JWT verification failed: {e}") from e
