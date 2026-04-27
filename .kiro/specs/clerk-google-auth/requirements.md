# 要件定義書

## はじめに

本機能は、Next.js + FastAPI のモノレポ構成アプリケーションに Clerk を用いた Google OAuth 認証を導入するものである。
認証基盤を Clerk に統一し、Next.js 内部では Cookie Session ベース、FastAPI 連携時は Bearer Token（JWT）ベースで認証状態を管理する。
アプリケーション DB（PostgreSQL）に `users` テーブルを追加し、Clerk User ID を主キーとしてユーザー情報を管理する。

---

## 用語集

- **Clerk**: 認証・ユーザー管理 SaaS。Google OAuth プロバイダーとの連携、セッション管理、JWT 発行を担う。
- **Clerk_User_ID**: Clerk が発行するユーザー固有識別子（例: `user_xxxxxxxxxxxxxxxx`）。アプリケーション DB のユーザー識別子として使用する。
- **Session_Cookie**: Clerk が Next.js アプリケーションに発行するセッション Cookie。Server Component・Server Action・Route Handler での認証状態取得に使用する。
- **JWT**: Clerk が発行する JSON Web Token。FastAPI への API リクエスト時に Authorization ヘッダーへ付与する Bearer Token として使用する。
- **ClerkProvider**: Next.js アプリケーション全体を囲む Clerk の React コンテキストプロバイダー。
- **Auth_Middleware**: Next.js の `middleware.ts` に配置する Clerk 認証ミドルウェア。保護対象ルートへの未認証アクセスを制御する。
- **User_Sync**: 初回ログイン時に Clerk ユーザー情報をアプリケーション DB へ同期する処理。
- **App_User**: アプリケーション DB の `users` テーブルに格納されるユーザーレコード。
- **FastAPI_Auth_Middleware**: FastAPI 側で JWT を検証する依存性注入ミドルウェア。

---

## 要件

### 要件 1: Google OAuth ログイン・サインアップ

**ユーザーストーリー:** 開発者として、Google アカウントでログイン・サインアップできるようにしたい。そうすることで、パスワード管理不要で安全に認証できる。

#### 受け入れ基準

1. THE `ClerkProvider` SHALL wrap the Next.js application root layout to enable authentication context throughout the application.
2. WHEN a user accesses the sign-in page, THE `Auth_UI` SHALL display a Google OAuth sign-in button provided by Clerk.
3. WHEN a user clicks the Google sign-in button, THE `Auth_UI` SHALL redirect the user to Google's OAuth consent screen via Clerk.
4. WHEN Google OAuth authentication succeeds, THE `Clerk` SHALL issue a `Session_Cookie` and redirect the user to the configured redirect URL.
5. WHEN Google OAuth authentication fails, THE `Auth_UI` SHALL display an error message and allow the user to retry.
6. WHEN a user accesses the sign-out endpoint, THE `Clerk` SHALL invalidate the `Session_Cookie` and redirect the user to the sign-in page.

---

### 要件 2: Next.js 認証状態管理（Cookie Session）

**ユーザーストーリー:** 開発者として、Next.js の Server Component・Server Action・Route Handler で認証状態を取得できるようにしたい。そうすることで、サーバーサイドで安全にユーザー情報を利用できる。

#### 受け入れ基準

1. THE `Auth_Middleware` SHALL protect all routes under `/dashboard` and other designated protected paths by redirecting unauthenticated requests to the sign-in page.
2. WHEN an authenticated request is received by a Server Component, THE `Server_Component` SHALL retrieve the current user's `Clerk_User_ID` from the `Session_Cookie` without requiring a Bearer Token.
3. WHEN an authenticated request is received by a Route Handler, THE `Route_Handler` SHALL retrieve the current user's `Clerk_User_ID` from the `Session_Cookie` without requiring a Bearer Token.
4. WHEN an authenticated request is received by a Server Action, THE `Server_Action` SHALL retrieve the current user's `Clerk_User_ID` from the `Session_Cookie` without requiring a Bearer Token.
5. IF an unauthenticated request reaches a protected route, THEN THE `Auth_Middleware` SHALL return a redirect response to the sign-in page with HTTP status 307.
6. THE `Client_Component` SHALL NOT handle or store Bearer Tokens directly.

---

### 要件 3: FastAPI 向け JWT 発行・送信

**ユーザーストーリー:** 開発者として、Next.js から FastAPI へのリクエスト時に Clerk JWT を Authorization ヘッダーへ付与できるようにしたい。そうすることで、FastAPI 側でユーザーを安全に識別できる。

#### 受け入れ基準

1. WHEN a Client Component calls the FastAPI, THE `API_Client` SHALL retrieve a JWT from Clerk using `getToken()` and attach it as a Bearer Token in the `Authorization` header.
2. WHEN a Server Component or Server Action calls the FastAPI, THE `Server_Caller` SHALL retrieve a JWT from Clerk using `getToken()` and attach it as a Bearer Token in the `Authorization` header.
3. THE `API_Client` SHALL NOT expose the Clerk Secret Key to the client-side JavaScript bundle.
4. WHEN the JWT has expired, THE `API_Client` SHALL request a refreshed token from Clerk before sending the request to FastAPI.

---

### 要件 4: FastAPI JWT 検証

**ユーザーストーリー:** バックエンド開発者として、FastAPI で受信した JWT を検証してユーザーを識別したい。そうすることで、不正なリクエストを拒否し、認証済みユーザーのみ API を利用できる。

#### 受け入れ基準

1. WHEN a request is received by a protected FastAPI endpoint, THE `FastAPI_Auth_Middleware` SHALL verify the JWT signature using Clerk's JWKS endpoint.
2. WHEN a request is received by a protected FastAPI endpoint, THE `FastAPI_Auth_Middleware` SHALL verify the JWT expiration (`exp` claim).
3. WHEN a request is received by a protected FastAPI endpoint, THE `FastAPI_Auth_Middleware` SHALL verify the JWT issuer (`iss` claim) matches the configured Clerk issuer URL.
4. WHEN a request is received by a protected FastAPI endpoint, THE `FastAPI_Auth_Middleware` SHALL extract the `Clerk_User_ID` from the JWT `sub` claim and make it available to the endpoint handler.
5. IF the JWT signature is invalid, THEN THE `FastAPI_Auth_Middleware` SHALL return HTTP 401 with an error detail.
6. IF the JWT has expired, THEN THE `FastAPI_Auth_Middleware` SHALL return HTTP 401 with an error detail.
7. IF the JWT issuer does not match, THEN THE `FastAPI_Auth_Middleware` SHALL return HTTP 401 with an error detail.
8. IF the Authorization header is absent, THEN THE `FastAPI_Auth_Middleware` SHALL return HTTP 401 with an error detail.

---

### 要件 5: アプリケーション DB ユーザー管理

**ユーザーストーリー:** 開発者として、アプリケーション DB に認証済みユーザー情報を保持したい。そうすることで、Clerk User ID を外部キーとしてアプリケーションデータと紐付けられる。

#### 受け入れ基準

1. THE `Database` SHALL contain a `users` table with columns: `clerk_user_id` (TEXT, PRIMARY KEY), `email` (TEXT, NOT NULL, UNIQUE), `display_name` (TEXT, NOT NULL), `created_at` (TIMESTAMPTZ, NOT NULL), `updated_at` (TIMESTAMPTZ, NOT NULL).
2. THE `User` SQLAlchemy model SHALL map to the `users` table with the above columns.
3. THE `Database` SHALL enforce uniqueness on the `email` column of the `users` table.

---

### 要件 6: ユーザー同期（初回ログイン・更新）

**ユーザーストーリー:** 開発者として、ログイン時に Clerk ユーザー情報をアプリケーション DB へ自動同期したい。そうすることで、DB 側のユーザーレコードを常に最新状態に保てる。

#### 受け入れ基準

1. WHEN a user successfully authenticates via Clerk, THE `User_Sync` SHALL check whether a record with the corresponding `Clerk_User_ID` exists in the `users` table.
2. IF the `Clerk_User_ID` does not exist in the `users` table, THEN THE `User_Sync` SHALL create a new `App_User` record with the `Clerk_User_ID`, primary email address, and display name obtained from Clerk.
3. IF the `Clerk_User_ID` already exists in the `users` table, THEN THE `User_Sync` SHALL update the `email` and `display_name` fields with the latest values from Clerk and set `updated_at` to the current timestamp.
4. WHEN the `User_Sync` operation completes successfully, THE `User_Sync` SHALL return the upserted `App_User` record.
5. IF the `User_Sync` operation fails due to a database error, THEN THE `User_Sync` SHALL raise an exception and the authentication flow SHALL return HTTP 500.

---

### 要件 7: セキュリティ要件

**ユーザーストーリー:** セキュリティ担当者として、認証基盤のセキュリティ要件を満たしたい。そうすることで、不正アクセスや情報漏洩を防止できる。

#### 受け入れ基準

1. THE `Application` SHALL NOT expose the Clerk Secret Key (`CLERK_SECRET_KEY`) in any client-side JavaScript bundle or HTTP response.
2. THE `Application` SHALL use `Clerk_User_ID` as the user identifier in all application logic, and SHALL NOT use email address as a primary identifier.
3. IF an unauthenticated request reaches a protected Next.js route, THEN THE `Auth_Middleware` SHALL return HTTP 307 redirect to the sign-in page.
4. IF an unauthenticated request reaches a protected FastAPI endpoint, THEN THE `FastAPI_Auth_Middleware` SHALL return HTTP 401.
5. IF an authenticated user lacks the required permissions for a FastAPI endpoint, THEN THE `FastAPI_Auth_Middleware` SHALL return HTTP 403.
6. THE `Application` SHALL operate under HTTPS in production environments.
7. THE `Application` SHALL validate all JWTs on every protected FastAPI request without exception.

---

### 要件 8: 環境変数管理

**ユーザーストーリー:** 開発者として、認証に必要な環境変数を安全に管理したい。そうすることで、Secret Key の漏洩を防ぎ、環境ごとに設定を切り替えられる。

#### 受け入れ基準

1. THE `Next.js_Application` SHALL read `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` as a public environment variable accessible on both server and client.
2. THE `Next.js_Application` SHALL read `CLERK_SECRET_KEY` as a server-only environment variable, and SHALL NOT prefix it with `NEXT_PUBLIC_`.
3. THE `Next.js_Application` SHALL read `NEXT_PUBLIC_CLERK_SIGN_IN_URL`, `NEXT_PUBLIC_CLERK_SIGN_UP_URL`, `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`, and `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL` as redirect URL configuration.
4. THE `FastAPI_Application` SHALL read `CLERK_ISSUER_URL` and `CLERK_JWKS_URL` as server-only environment variables for JWT verification.
5. THE `FastAPI_Application` SHALL read `API_BASE_URL` as a server-only environment variable.
6. IF a required environment variable is missing at application startup, THEN THE `Application` SHALL fail fast with a descriptive error message.
