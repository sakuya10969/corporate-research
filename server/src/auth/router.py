"""認証・ユーザー同期ルーター"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user_id
from src.auth.schemas import UserResponse, UserSyncRequest
from src.auth.service import upsert_user
from src.shared.db import get_session

router = APIRouter(tags=["auth"])


@router.post("/users/sync", response_model=UserResponse)
async def sync_user(
    body: UserSyncRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """
    Clerk ユーザー情報をアプリケーション DB へ同期する。

    - 未認証: 401（get_current_user_id が処理）
    - DB エラー: 500
    """
    try:
        user = await upsert_user(
            session=session,
            clerk_user_id=user_id,
            email=body.email,
            display_name=body.display_name,
        )
        return UserResponse.model_validate(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User sync failed: {e}",
        ) from e
