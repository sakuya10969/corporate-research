# 実装計画: clerk-google-auth

## 概要

Clerk Google OAuth 認証を Next.js + FastAPI モノレポへ段階的に導入する。
Next.js 側は Cookie Session ベース、FastAPI 側は JWT 検証ベースで実装し、
アプリケーション DB に `users` テーブルを追加してユーザー同期を行う。

## タスク

- [x] 1. 環境変数・依存パッケージのセットアップ
  - `client/` に `@clerk/nextjs` を追加（`npm install @clerk/nextjs`）
  - `server/` に `python-jose[cryptography]`・`httpx` を追加（`requirements.txt` または `pyproject.toml`）
  - `client/.env.local.example` に以下を追記:
    - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
    - `CLERK_SECRET_KEY`
    - `NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in`
    - `NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up`
    - `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard`
    - `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard`
  - `server/.env.example` に以下を追記:
    - `CLERK_ISSUER_URL`
    - `CLERK_JWKS_URL`
  - `server/src/shared/config.py` の `Settings` クラスに `clerk_issuer_url` と `clerk_jwks_url` フィールドを追加
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 2. DB マイグレーション: users テーブル追加
  - [x] 2.1 SQLAlchemy `User` モデルを `server/src/db/models.py` に追加
    - カラム: `clerk_user_id` (TEXT PK), `email` (TEXT UNIQUE NOT NULL), `display_name` (TEXT NOT NULL), `created_at`, `updated_at`
    - _Requirements: 5.1, 5.2_
  - [x] 2.2 Alembic マイグレーションファイルを生成・編集
    - `alembic revision --autogenerate -m "add_users_table"` を実行
    - 生成されたマイグレーションファイルを確認し、`idx_users_email` インデックスを追加
    - _Requirements: 5.1, 5.3_
  - [ ]* 2.3 User モデルのユニットテストを作成
    - `server/tests/test_user_model.py` を作成
    - `User` モデルのカラム定義・ユニーク制約を検証
    - _Requirements: 5.2, 5.3_

- [x] 3. FastAPI: JWT 検証・ユーザー同期の実装
  - [x] 3.1 `server/src/auth/` ディレクトリを作成し、JWT 検証モジュールを実装
    - `server/src/auth/jwt.py`: `verify_clerk_jwt(token: str) -> dict` 関数を実装
      - `httpx` で `CLERK_JWKS_URL` から公開鍵を取得（キャッシュ付き）
      - `python-jose` で署名・`exp`・`iss` を検証
      - 検証失敗時は `JWTError` を送出
    - _Requirements: 4.1, 4.2, 4.3_
  - [x] 3.2 FastAPI 依存性 `get_current_user_id` を実装
    - `server/src/auth/dependencies.py` を作成
    - `HTTPBearer` で Authorization ヘッダーを取得
    - `verify_clerk_jwt` を呼び出し、`sub` クレームを返す
    - 検証失敗・ヘッダー欠如時は HTTP 401 を返す
    - _Requirements: 4.4, 4.5, 4.6, 4.7, 4.8_
  - [ ]* 3.3 JWT 検証のプロパティテストを作成
    - `server/tests/test_jwt.py` を作成（`hypothesis` 使用、最低 100 回）
    - **Property 3: 不正 JWT の完全拒否** — 署名改ざん・期限切れ・issuer 不一致の JWT が `JWTError` を送出することを検証
    - **Property 4: 有効 JWT からの Clerk_User_ID 抽出** — 有効 JWT の `sub` クレームが正しく返ることを検証
    - タグ: `Feature: clerk-google-auth, Property 3 / Property 4`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [x] 3.4 `upsert_user` サービス関数を実装
    - `server/src/auth/service.py` を作成
    - `upsert_user(session, clerk_user_id, email, display_name) -> User` を実装
    - `clerk_user_id` が存在しない場合は INSERT、存在する場合は `email`・`display_name`・`updated_at` を UPDATE
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [ ]* 3.5 User Sync のプロパティテストを作成
    - `server/tests/test_user_sync.py` を作成（`hypothesis` 使用、最低 100 回）
    - **Property 1: User Sync の冪等性** — 同一入力で 2 回実行した結果が同一であることを検証
    - **Property 2: User Sync のラウンドトリップ** — upsert 後に DB から取得した値が入力値と一致することを検証
    - タグ: `Feature: clerk-google-auth, Property 1 / Property 2`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [x] 3.6 `server/src/auth/router.py` を作成し、ユーザー同期エンドポイントを実装
    - `POST /api/users/sync`: `get_current_user_id` 依存性を使用し、`upsert_user` を呼び出す
    - Pydantic スキーマ `UserSyncRequest`・`UserResponse` を `server/src/auth/schemas.py` に定義
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 3.7 `server/src/main.py`（または FastAPI アプリ初期化ファイル）に `auth` ルーターを登録
    - `app.include_router(auth_router, prefix="/api")`
    - _Requirements: 6.1_

- [x] 4. チェックポイント — FastAPI 側テストをすべてパスさせる
  - すべてのテストが通ることを確認し、疑問点があればユーザーに確認する。

- [x] 5. Next.js: Clerk プロバイダー・ミドルウェアの実装
  - [x] 5.1 `client/src/app/layout.tsx` を更新して `ClerkProvider` でラップ
    - 既存の `MantineProvider`・`QueryProvider` を `ClerkProvider` の内側に配置
    - _Requirements: 1.1_
  - [x] 5.2 `client/middleware.ts` を作成して Auth Middleware を実装
    - `clerkMiddleware` と `createRouteMatcher` を使用
    - `/dashboard(.*)` を保護対象ルートとして定義
    - 未認証アクセスは `auth.protect()` で HTTP 307 リダイレクト
    - _Requirements: 2.1, 2.5, 7.3_
  - [x] 5.3 サインイン・サインアップページを作成
    - `client/src/app/sign-in/[[...sign-in]]/page.tsx`: Clerk `<SignIn />` コンポーネントを配置
    - `client/src/app/sign-up/[[...sign-up]]/page.tsx`: Clerk `<SignUp />` コンポーネントを配置
    - _Requirements: 1.2, 1.3_

- [x] 6. Next.js: User Sync Route Handler の実装
  - [x] 6.1 `client/src/app/api/auth/sync/route.ts` を作成
    - `auth()` で `userId` を取得し、未認証時は 401 を返す
    - `currentUser()` でメールアドレス・表示名を取得
    - `auth().getToken()` で JWT を取得し、FastAPI `POST /api/users/sync` へ転送
    - _Requirements: 2.2, 2.3, 3.2, 6.1_
  - [ ]* 6.2 User Sync Route Handler のユニットテストを作成
    - `client/src/__tests__/api/auth/sync.test.ts` を作成
    - Clerk の `auth`・`currentUser` をモックして、未認証・認証済みの各ケースを検証
    - _Requirements: 2.2, 6.1_

- [x] 7. Next.js: FastAPI 向け認証済み API クライアントの実装
  - [x] 7.1 `client/src/shared/api/client.ts` を作成
    - `createAuthenticatedClient(getToken)` 関数を実装
    - Axios request interceptor で `Authorization: Bearer <token>` を付与
    - _Requirements: 3.1, 3.2_
  - [ ]* 7.2 API クライアントのプロパティテストを作成
    - `client/src/__tests__/shared/api/client.test.ts` を作成
    - **Property 5: Bearer Token 付与の普遍性** — 任意のリクエストに Authorization ヘッダーが付与されることを検証
    - タグ: `Feature: clerk-google-auth, Property 5: Bearer Token attachment`
    - _Requirements: 3.1, 3.2_

- [x] 8. チェックポイント — 全テストをパスさせ、統合動作を確認する
  - すべてのユニットテスト・プロパティテストが通ることを確認する。
  - 疑問点があればユーザーに確認する。

## 備考

- `*` が付いたサブタスクはオプションであり、MVP では省略可能
- 各タスクは設計書 `design.md` の対応するコンポーネント・プロパティを参照すること
- Clerk のテスト環境（Test Mode）を使用することで、実際の Google OAuth なしに認証フローをテストできる
- `python-jose` の JWKS キャッシュは TTL 付きで実装し、Clerk の鍵ローテーションに対応すること
