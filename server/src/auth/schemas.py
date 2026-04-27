"""認証関連 Pydantic スキーマ"""

from datetime import datetime

from pydantic import BaseModel


class UserSyncRequest(BaseModel):
    email: str
    display_name: str


class UserResponse(BaseModel):
    clerk_user_id: str
    email: str
    display_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
