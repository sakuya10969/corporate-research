"""FastAPI 認証依存性"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from src.auth.jwt import verify_clerk_jwt

security = HTTPBearer(auto_error=True)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Authorization ヘッダーから JWT を取得・検証し、Clerk_User_ID を返す。

    Returns:
        str: JWT の sub クレーム（Clerk_User_ID）

    Raises:
        HTTPException 401: JWT 検証失敗またはヘッダー欠如時
    """
    try:
        payload = await verify_clerk_jwt(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing sub claim",
            )
        return user_id
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        ) from e
