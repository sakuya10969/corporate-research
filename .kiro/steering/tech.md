---
inclusion: auto
---

# 技術スタック — 企業分析エージェント

## 採用技術一覧

### フロントエンド

| カテゴリ | 技術 | バージョン目安 |
|---------|------|--------------|
| フレームワーク | Next.js | 16.x |
| UI ライブラリ | React | 19.x |
| 言語 | TypeScript | 5.x |
| コンポーネント | Mantine | 9.x |
| ユーティリティフック | Mantine Hooks | 9.x |
| アイコン | Tabler Icons (@tabler/icons-react) | 3.x |
| サーバー状態管理 | TanStack React Query | 5.x |
| HTTP クライアント | Axios | 1.x |
| バリデーション | Valibot | 1.x |
| API クライアント生成 | Orval | 8.x |
| リンター / フォーマッター | Biome | 2.x |
| CSS | PostCSS + postcss-preset-mantine + postcss-simple-vars | — |

### バックエンド

| カテゴリ | 技術 | 備考 |
|---------|------|------|
| フレームワーク | FastAPI | 0.136+ |
| 言語 | Python | 3.14+ |
| AI 基盤 | azure-ai-projects | Azure AI Foundry 接続 |
| 認証 | azure-identity | Azure 認証 |
| Web スクレイピング | beautifulsoup4 + lxml | HTML パース |
| HTTP クライアント | httpx | 非同期対応 |
| LLM フレームワーク | langchain + langchain-azure-ai | AI チェーン構築 |
| ワークフロー（将来） | langgraph | MVP では未使用、依存のみ保持 |
| 設定管理 | pydantic-settings | 環境変数管理 |
| リンター / フォーマッター | Ruff | dev dependency |

## フロントエンドの採用理由

- Next.js: App Router によるファイルベースルーティング、SSR/SSG の柔軟性、React 19 の Server Components 対応。業務プロダクトとして十分な基盤。
- Mantine: 業務UIに適したコンポーネントが豊富。Headless ではなくスタイル付きで提供されるため、MVP での開発速度を優先できる。PostCSS ベースのテーマカスタマイズにも対応。
- TanStack React Query: サーバー状態管理のデファクト。分析リクエストの状態（loading / success / error）管理に最適。
- Axios: Orval との親和性が高く、インターセプター等の拡張性も確保。
- Valibot: Zod と同等の型安全バリデーションを、より軽量なバンドルサイズで実現。フォーム入力のバリデーションに使用。
- Orval: OpenAPI スキーマから API クライアント + 型 + React Query フックを自動生成。フロントエンド・バックエンド間の型安全性を担保。
- Biome: ESLint + Prettier の代替として、高速な lint / format を単一ツールで実現。

## バックエンドの採用理由

- FastAPI: 非同期対応、自動 OpenAPI スキーマ生成、Pydantic ベースの型安全性。フロントエンドとの OpenAPI 連携に最適。
- LangChain: LLM 呼び出しのチェーン構築を抽象化。プロンプト管理、出力パーサー、チェーン合成が容易。
- langchain-azure-ai: Azure AI Foundry のモデルを LangChain から直接利用するためのアダプター。
- httpx + BeautifulSoup + lxml: Web 情報収集のための非同期 HTTP クライアントと HTML パーサー。企業情報のスクレイピングに使用。
- pydantic-settings: `.env` ファイルからの設定読み込みを型安全に行う。

## Azure AI Foundry / LangChain / LangGraph の位置づけ

```
[ユーザー入力]
    ↓
[FastAPI エンドポイント]
    ↓
[情報収集モジュール] ← httpx + BeautifulSoup
    ↓
[LangChain チェーン] ← langchain + langchain-azure-ai
    ↓                    ↑
    ↓              [Azure AI Foundry]
    ↓              （LLM モデル提供）
[構造化された分析結果]
    ↓
[フロントエンドへ返却]
```

- Azure AI Foundry: LLM モデルのホスティング・提供基盤。langchain-azure-ai 経由でアクセス。
- LangChain: MVP では単一チェーン（収集→要約→分析）として使用。プロンプトテンプレート、出力パーサーを活用。
- LangGraph: MVP では未使用。依存には含めておき、将来的にマルチステップワークフロー（条件分岐、リトライ、並列実行）が必要になった段階で導入。LangChain のチェーンから LangGraph のグラフへの移行が自然にできるよう、処理単位をモジュール化しておく。

## OpenAPI + Orval による型・APIクライアント自動生成方針

```
[FastAPI] → 自動生成 → [openapi.json]
                            ↓
                        [Orval CLI]
                            ↓
              [API クライアント + 型定義 + React Query フック]
```

1. FastAPI が OpenAPI スキーマ（`/openapi.json`）を自動公開
2. Orval がそのスキーマを読み取り、以下を自動生成：
   - API クライアント関数（Axios ベース）
   - リクエスト / レスポンスの TypeScript 型定義
   - TanStack React Query 用のカスタムフック
3. 生成コードは `client/src/shared/api/generated/` に配置
4. 生成コードは手動編集しない（再生成で上書きされる前提）

## 各レイヤの技術的役割整理

| 関心事 | 技術 | 備考 |
|--------|------|------|
| バリデーション（フォーム） | Valibot | 企業名入力等のクライアントサイドバリデーション |
| バリデーション（API） | Pydantic（FastAPI） | リクエスト / レスポンスの型検証 |
| サーバー状態管理 | TanStack React Query | API 通信の状態管理（キャッシュ、再取得、楽観的更新） |
| クライアント状態管理 | React useState / Mantine Hooks | MVP では十分。グローバル状態管理ライブラリは不要 |
| API 通信 | Axios（Orval 生成） | 手書きの API 呼び出しは原則不要 |
| スタイリング | Mantine + PostCSS | CSS Modules + Mantine テーマ。Tailwind は不採用 |
| 開発体験 | Biome + TypeScript + Ruff | フロントは Biome、バックは Ruff で lint / format 統一 |

## MVP 時点で採用しないもの

| 技術 / 機能 | 理由 |
|------------|------|
| LangGraph（本格運用） | MVP のフローは単純なチェーンで十分。依存のみ保持 |
| RAG / ベクトルDB | MVP は Web 情報収集ベース。社内ナレッジ統合は Phase 6 以降 |
| 認証・認可 | MVP はシングルユーザー前提 |
| グローバル状態管理（Zustand 等） | React Query + useState で十分 |
| E2E テストフレームワーク | MVP 段階では手動テストで対応 |
| Docker / コンテナ化 | 開発環境はローカル実行前提。デプロイ時に検討 |
