# 技術スタック

## フロントエンド

| カテゴリ | 技術 | バージョン | 役割 |
|---------|------|-----------|------|
| フレームワーク | Next.js | 16.x | App Router、SSR/SSG、ファイルベースルーティング |
| UI ライブラリ | React | 19.x | コンポーネントベースUI |
| 言語 | TypeScript | 5.x | 型安全性 |
| コンポーネント | Mantine | 9.x | 業務UIコンポーネント、テーマ |
| フック | Mantine Hooks | 9.x | ユーティリティフック |
| アイコン | @tabler/icons-react | 3.x | アイコンセット |
| サーバー状態管理 | TanStack React Query | 5.x | API通信の状態管理 |
| HTTP クライアント | Axios | 1.x | Orval生成のHTTPクライアント基盤 |
| バリデーション | Valibot | 1.x | フォーム入力の型安全バリデーション |
| API クライアント生成 | Orval | 8.x | OpenAPIからの自動生成 |
| リンター/フォーマッター | Biome | 2.x | lint + format 統合ツール |
| CSS | PostCSS | 8.x | postcss-preset-mantine + postcss-simple-vars |

## バックエンド

| カテゴリ | 技術 | バージョン | 役割 |
|---------|------|-----------|------|
| フレームワーク | FastAPI | 0.136+ | 非同期API、自動OpenAPIスキーマ生成 |
| 言語 | Python | 3.14+ | — |
| LLM フレームワーク | openai-agents（OpenAI Agents SDK） | 0.14.6+ | Agent / Runner によるLLM呼び出し |
| OpenAI クライアント | openai | 2.32+ | AsyncAzureOpenAI 経由でAzure OpenAIに接続 |
| スクレイピング | beautifulsoup4 + lxml | — | HTML パース |
| HTTP クライアント | httpx | 0.28+ | 非同期Web情報収集 |
| 設定管理 | pydantic-settings | 2.13+ | .env からの型安全な設定読み込み |
| リンター/フォーマッター | Ruff | 0.15+ | Python lint + format |

## 技術選定の要点

### フロントエンド

- Mantine を採用し、業務UIの開発速度を優先。Headless UIではなくスタイル付きコンポーネントでMVPを素早く構築する
- Orval で OpenAPI スキーマから API クライアント + 型 + React Query フックを自動生成し、フロント・バック間の型安全性を担保
- Valibot は Zod 同等の型安全バリデーションをより軽量に実現
- Biome で ESLint + Prettier を単一ツールに統合

### バックエンド

- FastAPI の自動 OpenAPI スキーマ生成がフロントエンドとの連携に最適
- OpenAI Agents SDK（`openai-agents`）で `Agent` + `Runner` によるLLM呼び出しを管理。プロンプトは `instructions` として `Agent` に渡し、`Runner.run()` で非同期実行する
- Azure OpenAI には `AsyncAzureOpenAI` クライアントを `set_default_openai_client()` でSDKに注入して使用
- httpx + BeautifulSoup で非同期Web情報収集を実現

### Azure OpenAI / OpenAI Agents SDK

- Azure OpenAI: LLMモデルのホスティング基盤。`openai` ライブラリの `AsyncAzureOpenAI` 経由でアクセス
- OpenAI Agents SDK: `Agent`（プロンプト・モデル設定）と `Runner`（実行）でLLM処理を構成。アプリ起動時に `init_llm()` でデフォルトクライアントを設定する
- LangGraph: 現時点では未採用。将来の深掘り分析（F-007）・差分更新（F-006）での状態付きワークフロー導入時に検討

## MVP時点で採用しないもの

| 技術/機能 | 理由 |
|----------|------|
| LangChain / LangGraph | OpenAI Agents SDKに移行済み。LangGraphは将来のF-006/F-007で再検討 |
| RAG / ベクトルDB | Web情報収集ベースで開始。Phase 6以降 |
| 認証・認可 | シングルユーザー前提 |
| グローバル状態管理（Zustand等） | React Query + useState で十分 |
| E2E テスト | MVP段階では手動テスト |
| Docker / コンテナ化 | ローカル実行前提。デプロイ時に検討 |
