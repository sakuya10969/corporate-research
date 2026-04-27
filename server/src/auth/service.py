"""ユーザー同期サービス"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


async def upsert_user(
    session: AsyncSession,
    clerk_user_id: str,
    email: str,
    display_name: str,
) -> User:
    """
    Clerk ユーザー情報をアプリケーション DB へ upsert する。

    - clerk_user_id が存在しない場合: 新規 INSERT
    - clerk_user_id が存在する場合: email / display_name / updated_at を UPDATE

    Args:
        session: AsyncSession
        clerk_user_id: Clerk が発行するユーザー固有識別子
        email: プライマリメールアドレス
        display_name: 表示名

    Returns:
        User: upsert 後の App_User レコード

    Raises:
        Exception: DB エラー時（呼び出し元で HTTP 500 に変換）
    """
    result = await session.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if user is None:
        user = User(
            clerk_user_id=clerk_user_id,
            email=email,
            display_name=display_name,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
    else:
        user.email = email
        user.display_name = display_name
        user.updated_at = now

    await session.commit()
    await session.refresh(user)
    return user
