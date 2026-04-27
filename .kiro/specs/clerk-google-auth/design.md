# 設計書: clerk-google-auth

## 概要

本設計書は、Next.js + FastAPI モノレポ構成アプリケーションへの Clerk Google OAuth 認証導入を定義する。

認証フローは以下の 2 系統に分かれる：

1. **Next.js 内部**: Clerk が管理する Session Cookie を利用。Server Component・Server Action・Route Handler はすべて Cookie ベースで認証状態を取得する。Client Component は Bearer Token を直接扱わない。
2. **FastAPI 連携**: Next.js から FastAPI へのリクエスト時のみ、Clerk が発行する JWT を Authorization ヘッダーに付与する。FastAPI 側では JWKS を用いて JWT を検証する。

---

## アーキテクチャ

```mermaid
graph TD
    subgraph Browser
        A[Client Component]
    end

    subgraph Next.js (client/)
        B[ClerkProvider / middleware.ts]
        C[Server Component / Server Action / Route Handler]
        D[API Route: /api/auth/sync]
    end

    subgraph FastAPI (server/)
        E[FastAPI_Auth_Middleware]
        F[Protected Endpoints]
    end

    subgraph External
        G[Clerk SaaS]
        H[Google OAuth]
        I[PostgreSQL: users table]
    end

    A -- "Session Cookie (自動)" --> B
    A -- "getToken() → Bearer JWT" --> F
    B -- "Cookie 検証" --> G
    C -- "auth() / currentUser()" --> G
    D -- "User Sync (upsert)" --> I
    E -- "JWKS 検証" --> G
    G -- "OAuth redirect" --> H
    F --> I
```

---

## コンポーネントとインターフェース

### Next.js 側

#### ClerkProvider（`client/src/app/layout.tsx`）

`@clerk/nextjs` の `ClerkProvider` でルートレイアウトを囲む。

```tsx
import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="ja">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  )
}
```

#### Auth Middleware（`client/middleware.ts`）

`clerkMiddleware` を使用し、保護対象ルートを `createRouteMatcher` で定義する。

```ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher(['/dashboard(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) await auth.protect()
})

export const config = {
  matcher: ['/((?!_next|.*\\..*).*)'],
}
```

#### サインイン・サインアップページ

Clerk の `<SignIn />` / `<SignUp />` コンポーネントを使用する。

- `client/src/app/sign-in/[[...sign-in]]/page.tsx`
- `client/src/app/sign-up/[[...sign-up]]/page.tsx`

#### User Sync Route Handler（`client/src/app/api/auth/sync/route.ts`）

ログイン後に呼び出される Route Handler。`auth()` で `Clerk_User_ID` を取得し、`currentUser()` でメールアドレス・表示名を取得して FastAPI の `/api/users/sync` へ転送する。

```ts
import { auth, currentUser } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

export async function POST() {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const user = await currentUser()
  // FastAPI /api/users/sync へ Bearer Token 付きで転送
  const token = await auth().getToken()
  // ...
}
```

#### FastAPI 向け API クライアント（`client/src/shared/api/client.ts`）

Axios インスタンスに request interceptor を追加し、`getToken()` で取得した JWT を Authorization ヘッダーへ付与する。

```ts
import axios from 'axios'

export function createAuthenticatedClient(getToken: () => Promise<string | null>) {
  const instance = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_BASE_URL })
  instance.interceptors.request.use(async (config) => {
    const token = await getToken()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })
  return instance
}
```

---

### FastAPI 側

#### JWT 検証依存性（`server/src/auth/dependencies.py`）

`python-jose` を使用して Clerk JWKS から公開鍵を取得し、JWT を検証する。

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

security = HTTPBearer()

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    try:
        # JWKS から公開鍵を取得して検証
        payload = verify_clerk_jwt(token)
        return payload["sub"]  # Clerk_User_ID
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
```

#### ユーザー同期エンドポイント（`server/src/auth/router.py`）

```python
@router.post("/users/sync")
async def sync_user(
    user_id: str = Depends(get_current_user_id),
    body: UserSyncRequest,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    return await upsert_user(session, user_id, body.email, body.display_name)
```

---

## データモデル

### `users` テーブル（新規追加）

```sql
CREATE TABLE users (
    clerk_user_id  TEXT PRIMARY KEY,
    email          TEXT NOT NULL UNIQUE,
    display_name   TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
```

### SQLAlchemy モデル（`server/src/db/models.py` に追加）

```python
class User(Base):
    __tablename__ = "users"

    clerk_user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )
```

### Pydantic スキーマ（`server/src/auth/schemas.py`）

```python
class UserSyncRequest(BaseModel):
    email: str
    display_name: str

class UserResponse(BaseModel):
    clerk_user_id: str
    email: str
    display_name: str
    created_at: datetime
    updated_at: datetime
```

---

## 正確性プロパティ

*プロパティとは、システムのすべての有効な実行において成立すべき特性・振る舞いの形式的な記述である。プロパティはヒューマンリーダブルな仕様と機械検証可能な正確性保証の橋渡しとなる。*

### Property 1: User Sync の冪等性

*For any* 有効な `Clerk_User_ID`・メールアドレス・表示名の組み合わせに対して、`upsert_user` を 1 回実行した結果と 2 回実行した結果は同一の `App_User` レコードを返す（`clerk_user_id`・`email`・`display_name` がすべて一致する）。

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

---

### Property 2: User Sync のラウンドトリップ

*For any* 有効な `Clerk_User_ID`・メールアドレス・表示名の組み合わせに対して、`upsert_user` で作成・更新したレコードを DB から取得すると、入力値と同一の `email` および `display_name` が返る。

**Validates: Requirements 6.2, 6.3, 6.4**

---

### Property 3: 不正 JWT の完全拒否

*For any* 署名改ざん・期限切れ・issuer 不一致・Authorization ヘッダー欠如のいずれかに該当するリクエストに対して、`FastAPI_Auth_Middleware` は必ず HTTP 401 を返し、エンドポイントハンドラーは呼び出されない。

**Validates: Requirements 4.5, 4.6, 4.7, 4.8, 7.4**

---

### Property 4: 有効 JWT からの Clerk_User_ID 抽出

*For any* 有効な Clerk JWT に対して、`verify_clerk_jwt` は JWT の `sub` クレームと同一の文字列を返す。

**Validates: Requirements 4.4**

---

### Property 5: Bearer Token 付与の普遍性

*For any* FastAPI へのリクエストに対して、`API_Client` は必ず `Authorization: Bearer <token>` ヘッダーを付与する（token は `getToken()` の返却値）。

**Validates: Requirements 3.1, 3.2**

---

## エラーハンドリング

| 状況 | レスポンス | 担当コンポーネント |
|------|-----------|-----------------|
| 未認証で保護 Next.js ルートへアクセス | HTTP 307 → サインインページ | `Auth_Middleware` |
| 未認証で保護 FastAPI エンドポイントへアクセス | HTTP 401 | `FastAPI_Auth_Middleware` |
| JWT 署名不正 | HTTP 401 | `FastAPI_Auth_Middleware` |
| JWT 期限切れ | HTTP 401 | `FastAPI_Auth_Middleware` |
| JWT issuer 不一致 | HTTP 401 | `FastAPI_Auth_Middleware` |
| 権限不足 | HTTP 403 | `FastAPI_Auth_Middleware` |
| User Sync DB エラー | HTTP 500 | `User_Sync` |
| 必須環境変数未設定 | アプリ起動失敗（fail fast） | `Settings` |

FastAPI の共通例外ハンドラーは既存の `shared/exceptions.py` パターンに従い追加する。

---

## テスト戦略

### ユニットテスト

- `upsert_user` 関数: 新規作成・更新・DB エラー時の各ケース
- JWT 検証関数: 有効 JWT・署名不正・期限切れ・issuer 不一致の各ケース
- `Auth_Middleware`: 保護ルートへの未認証アクセス・認証済みアクセスの各ケース

### プロパティベーステスト（`hypothesis` を使用）

各プロパティテストは最低 100 回のランダム入力で検証する。

**Property 1: User Sync の冪等性**
- ランダムな `clerk_user_id`・`email`・`display_name` を生成
- `upsert_user` を 2 回実行し、返却値（`clerk_user_id`・`email`・`display_name`）が同一であることを検証
- タグ: `Feature: clerk-google-auth, Property 1: User Sync idempotency`

**Property 2: User Sync のラウンドトリップ**
- ランダムな入力値で `upsert_user` を実行後、DB から取得して入力値と一致することを検証
- タグ: `Feature: clerk-google-auth, Property 2: User Sync round trip`

**Property 3: 不正 JWT の完全拒否**
- ランダムな改ざん（署名変更・`exp` 過去日時・`iss` 変更）を加えた JWT を生成
- `verify_clerk_jwt` が `JWTError` を送出することを検証
- タグ: `Feature: clerk-google-auth, Property 3: Invalid JWT rejection`

**Property 4: 有効 JWT からの Clerk_User_ID 抽出**
- ランダムな `sub` クレームを持つ有効な JWT を生成
- `verify_clerk_jwt` が返す値が `sub` クレームと一致することを検証
- タグ: `Feature: clerk-google-auth, Property 4: Clerk_User_ID extraction`

**Property 5: Bearer Token 付与の普遍性**
- ランダムなエンドポイント・リクエストボディに対して `API_Client` が Authorization ヘッダーを付与することを検証
- タグ: `Feature: clerk-google-auth, Property 5: Bearer Token attachment`

### 統合テスト

- Google OAuth フロー全体（Clerk テスト環境を使用）
- Next.js → FastAPI の JWT 付きリクエスト
- User Sync の end-to-end フロー
