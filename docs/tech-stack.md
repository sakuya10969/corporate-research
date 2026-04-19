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
| AI 基盤 | azure-ai-projects | 2.0+ | Azure AI Foundry 接続 |
| 認証 | azure-identity | 1.25+ | Azure 認証 |
| スクレイピング | beautifulsoup4 + lxml | — | HTML パース |
| HTTP クライアント | httpx | 0.28+ | 非同期Web情報収集 |
| LLM フレームワーク | langchain + langchain-azure-ai | — | AIチェーン構築 |
| ワークフロー（将来） | langgraph | — | MVP未使用、依存のみ保持 |
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
- LangChain でLLM呼び出しを抽象化し、プロンプト管理・出力パーサー・チェーン合成を容易にする
- httpx + BeautifulSoup で非同期Web情報収集を実現

### Azure AI Foundry / LangChain / LangGraph

- Azure AI Foundry: LLMモデルのホスティング基盤。langchain-azure-ai 経由でアクセス
- LangChain: MVPでは単一チェーン（収集→要約→分析）として使用
- LangGraph: MVP未使用。将来のマルチステップワークフロー導入時に採用予定。依存のみ保持

## MVP時点で採用しないもの

| 技術/機能 | 理由 |
|----------|------|
| LangGraph（本格運用） | MVPのフローは単純なチェーンで十分 |
| RAG / ベクトルDB | Web情報収集ベースで開始。Phase 6以降 |
| 認証・認可 | シングルユーザー前提 |
| グローバル状態管理（Zustand等） | React Query + useState で十分 |
| E2E テスト | MVP段階では手動テスト |
| Docker / コンテナ化 | ローカル実行前提。デプロイ時に検討 |
