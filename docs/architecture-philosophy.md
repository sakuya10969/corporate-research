# アーキテクチャ思想

## 全体方針

- フロントエンドとバックエンドの責務を明確に分離する
- ロジックはバックエンドに集約し、フロントエンドは「表示」と「入力」に専念する
- MVP段階では過剰設計を避けつつ、将来の拡張性を担保する
- AIワークフローの中核はバックエンド側に寄せる

## フロントエンド — FSD（Feature-Sliced Design）

### 採用理由

- 業務プロダクトとして保守しやすく整理された構成を重視
- 機能単位でのコード分割により、チーム開発時のコンフリクトを最小化
- レイヤ間の依存ルールが明確で、アーキテクチャの劣化を防ぎやすい
- Next.js App Router との共存が可能（`app/` を FSD の app レイヤとして兼用）

### レイヤ構成と依存ルール

```
app → pages → widgets → features → entities → shared
（上位レイヤは下位レイヤのみ参照可能。逆方向の依存は禁止）
```

| レイヤ | 責務 |
|--------|------|
| app | アプリ全体の初期化、プロバイダー、グローバル設定。Next.js App Router のルートを兼ねる |
| pages | ページ単位のコンポーネント。widgets / features を組み合わせてページを構成 |
| widgets | ページ内の大きなUIブロック。複数の features を組み合わせた複合コンポーネント |
| features | ユーザー操作に対応する機能単位（企業名検索、分析実行など） |
| entities | ビジネスエンティティ（企業情報などのドメインモデルとその表示） |
| shared | 共通ユーティリティ、UI部品、APIクライアント、型定義。全レイヤから参照される |

### 設計原則

- 各スライスは `index.ts` で公開APIを定義し、内部実装を隠蔽する
- スライス間の直接参照は禁止。必ず公開APIを通じてアクセスする
- `shared` はどのレイヤからも参照されるが、他のレイヤを参照しない
- Orval 自動生成コードは `shared/api/generated/` に配置し、手動編集しない

### OpenAPI 連携の位置づけ

```
FastAPI (自動生成) → openapi.json → Orval (mode: tags-split) → shared/api/generated/{tag}/{tag}.ts
```

フロントエンドの API 層は Orval による自動生成を前提とし、手書きの API 呼び出しは原則不要。生成された React Query フックを features / widgets から利用する。

Orval は `mode: "tags-split"` を使用し、FastAPI ルーターのタグ単位でファイルを分割する。

| タグ | 生成ファイル | 対応エンドポイント |
|------|------------|-----------------|
| `analysis` | `generated/analysis/analysis.ts` | 分析実行・結果取得・ダウンロード |
| `auth` | `generated/auth/auth.ts` | ユーザー同期 |
| `companies` | `generated/companies/companies.ts` | 履歴・深掘り分析 |
| `compare` | `generated/compare/compare.ts` | 複数企業比較 |
| `health` | `generated/health/health.ts` | ヘルスチェック |
| `search` | `generated/search/search.ts` | 企業名検索 |
| `share` | `generated/share/share.ts` | シェア作成・取得 |

FastAPI 側でエンドポイントにタグを付与することで、生成物の分割粒度を制御できる。

## バックエンド — モジュラーモノリス

### 採用理由

- MVP段階ではマイクロサービスは過剰。単一プロセスで十分
- ただしモジュール境界を明確にすることで、将来的な分割・拡張に備える
- FastAPI の Router 機構がモジュール分割と自然に対応する
- LangGraph 導入時にもモジュール単位での置き換えが容易

### 設計原則

- `server/src/` 直下にモジュールを配置
- 各モジュールは独立したドメイン責務を持つ
- モジュール間の依存は `shared` を経由するか、明示的なインターフェースを通じて行う
- 各モジュールは `router.py`（エンドポイント）、`service.py`（ビジネスロジック）、`schemas.py`（型定義）の構成を基本とする
- `main.py` で全モジュールの Router を集約

### モジュール構成（MVP）

| モジュール | 責務 |
|-----------|------|
| `analysis` | 分析リクエストの受付、フロー制御、LLMチェーン実行、結果返却 |
| `collector` | Web情報の収集・HTMLパース |
| `shared` | 設定管理、LLMクライアント初期化、共通例外定義 |

### LangGraph 拡張への備え

MVP では `analysis.service` が逐次的にフローを制御する。将来 LangGraph を導入する際は、この制御部分をグラフ定義に置き換える。そのために：

- 情報収集・要約・分析を独立した関数として実装（LangGraph ノードとして再利用可能）
- 各処理の入出力を Pydantic モデルで明確に定義（LangGraph State として再利用可能）
- プロンプトテンプレートを `prompts.py` に外部化（ノードごとの差し替えが容易）

## フロントエンド・バックエンドの責務分離

| 責務 | フロントエンド | バックエンド |
|------|-------------|------------|
| 入力バリデーション | Valibot（UX向上） | Pydantic（信頼境界） |
| API通信 | Orval生成クライアント | — |
| 状態管理 | React Query + useState | — |
| 情報収集 | — | httpx + BeautifulSoup |
| AI処理 | — | LangChain + Azure AI Foundry |
| フロー制御 | — | analysis.service |
| 結果の構造化 | 表示用の整形のみ | Pydantic スキーマで構造化 |
| エラーハンドリング | UI表示 | 例外定義・HTTPステータス |

## 共通モジュールの命名

フロントエンド・バックエンド双方で `shared` を採用する。

- 英語として自然（"shared resources"）。`share` は動詞であり、ディレクトリ名としては不自然
- FSD の標準レイヤ名が `shared`
- OSS・業界慣例として `shared` が圧倒的に多い（NestJS, Nx 等）
- フロント・バック双方で統一することで認知負荷を下げる
