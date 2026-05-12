# 要件定義書: 企業分析ワークフロー変革

## はじめに

本ドキュメントは、現行の「URL即時分析ツール」を「企業登録ファースト型SaaS」へ変革するための要件を定義する。現在のシステムは同期的なURL入力→分析→結果表示のワンショット型であるが、これを企業登録→バックグラウンドジョブ→蓄積データ活用→テンプレート別深掘り分析という非同期ワークフローに転換する。

既存の11個のspec（company-analysis-core, data-persistence, diff-refresh, deep-research, analysis-history, download, analysis-template-scoring, company-search, share, compare, clerk-google-auth）を本specに統合・置換する。

### 現行システムの課題

1. 同期処理のため、クロール・抽出・分析の全工程でユーザーが待機する必要がある
2. 企業データが分析結果に埋め込まれており、蓄積資産として再利用しにくい
3. テンプレート別の再分析でも毎回フルクロールが走る
4. `analyze_company()` が単一の巨大関数であり、責務分離ができていない

### 変革の目的

- 企業を「登録」し、データを蓄積資産として管理する
- クロール・抽出・分析をバックグラウンドジョブ化し、UXを改善する
- 蓄積データに対してテンプレート別の深掘り分析を可能にする
- 既存のURL即時分析はレガシー/デモモードとして維持する

## 用語集

- **System**: 企業分析エージェントのバックエンド・フロントエンド全体
- **Company_Registry**: 企業の登録・管理を担うサービス層
- **Crawl_Service**: 企業サイトのクロール・ページ収集を担うサービス層
- **Extraction_Service**: 収集ページから構造化データを抽出するサービス層
- **Analysis_Service**: 要約・SWOT・スコアリング・レポート生成を担うサービス層
- **Job_Manager**: バックグラウンドジョブの状態管理を担うサービス層
- **Company_Status**: 企業の処理状態（pending, crawling, extracting, analyzing, completed, failed）
- **Analysis_Run**: 1回の分析実行単位（既存テーブル `analysis_runs` に対応）
- **Deep_Analysis**: 蓄積済み企業データに対するテンプレート別の追加分析
- **Legacy_Analysis**: 既存のURL即時同期分析フロー（POST /api/analysis）
- **User**: Clerk認証済みのシステム利用者

## 要件

### 要件 1: 企業登録

**ユーザーストーリー:** ユーザーとして、企業URLを登録して分析対象として管理したい。これにより、企業データを蓄積資産として活用できる。

#### 受入基準

1. WHEN ユーザーが企業URLを送信した場合、THE Company_Registry SHALL 企業レコードを作成し、status を "pending" に設定する
2. WHEN 登録済みURLと同一の正規化URLが送信された場合、THE Company_Registry SHALL 新規登録を拒否し、既存の企業レコードを返却する
3. WHEN 企業が登録された場合、THE Company_Registry SHALL URL正規化（スキーム+ドメイン抽出）を実行し、normalized_url と primary_domain を設定する
4. THE Company_Registry SHALL 企業登録時に重い同期処理（クロール・LLM呼び出し）を実行しない
5. WHEN 企業が登録された場合、THE System SHALL クロールジョブを自動的にキューに追加する

### 要件 2: 企業一覧・詳細表示

**ユーザーストーリー:** ユーザーとして、登録済み企業の一覧と詳細を確認したい。これにより、分析状況を把握し、次のアクションを判断できる。

#### 受入基準

1. WHEN ユーザーが企業一覧を要求した場合、THE System SHALL 企業名、URL、最終クロール日時、最終分析日時、Company_Status、最新スコア、詳細リンクを含むリストを返却する
2. WHEN ユーザーが企業詳細を要求した場合、THE System SHALL 企業概要、基本情報、事業内容、製品・サービス、財務情報、ニュース、リスク、SWOT、競合、展望、スコア、ソース、差分レポート、最終更新日時を返却する
3. WHILE 企業の Company_Status が "crawling" または "analyzing" の場合、THE System SHALL 処理中であることをユーザーに表示する

### 要件 3: バックグラウンドクロールジョブ

**ユーザーストーリー:** ユーザーとして、企業登録後にバックグラウンドでクロールが実行されてほしい。これにより、待機時間なく他の作業を続けられる。

#### 受入基準

1. WHEN クロールジョブが開始された場合、THE Crawl_Service SHALL Company_Status を "crawling" に更新し、Analysis_Run レコードを作成する
2. WHEN クロールが完了した場合、THE Crawl_Service SHALL 収集したページを pages テーブルに、ページ内容を page_versions テーブルに保存する
3. WHEN クロールが完了した場合、THE Crawl_Service SHALL Company の last_page_crawl_at を更新する
4. IF クロール中にエラーが発生した場合、THEN THE Crawl_Service SHALL Company_Status を "failed" に更新し、Analysis_Run に error_code と error_message を記録する
5. WHEN クロールが正常完了した場合、THE System SHALL 抽出ジョブを自動的にキューに追加する

### 要件 4: バックグラウンド抽出・分析ジョブ

**ユーザーストーリー:** ユーザーとして、クロール完了後に自動的に構造化抽出と分析が実行されてほしい。これにより、手動操作なしで分析結果が得られる。

#### 受入基準

1. WHEN 抽出ジョブが開始された場合、THE Extraction_Service SHALL Company_Status を "extracting" に更新する
2. WHEN 抽出が完了した場合、THE Extraction_Service SHALL 構造化データ（CompanyProfile, Financials, News, Risks）を analysis_results の structured フィールドに保存する
3. WHEN 分析ジョブが開始された場合、THE Analysis_Service SHALL Company_Status を "analyzing" に更新する
4. WHEN 分析が完了した場合、THE Analysis_Service SHALL 要約、SWOT、スコア、markdown_page、diff_report を analysis_results に保存する
5. WHEN 全ジョブが正常完了した場合、THE Job_Manager SHALL Company_Status を "completed" に更新し、Company の last_analyzed_at と analysis_count を更新する
6. IF 抽出または分析中にエラーが発生した場合、THEN THE Job_Manager SHALL Company_Status を "failed" に更新し、Analysis_Run にエラー情報を記録する

### 要件 5: ジョブ状態管理

**ユーザーストーリー:** ユーザーとして、バックグラウンドジョブの進捗状況をリアルタイムで確認したい。これにより、分析完了を待つ間の不安を解消できる。

#### 受入基準

1. WHEN ユーザーがジョブ状態を問い合わせた場合、THE Job_Manager SHALL Analysis_Run の現在の status（pending, running, completed, failed）を返却する
2. WHEN ジョブの状態が変化した場合、THE Job_Manager SHALL Analysis_Run の status、started_at、completed_at、duration_ms を更新する
3. THE Job_Manager SHALL 各ジョブフェーズ（crawling, extracting, analyzing）の進捗を Analysis_Run の collection_summary に記録する

### 要件 6: テンプレート別深掘り分析（Deep Analysis）

**ユーザーストーリー:** ユーザーとして、蓄積済みの企業データに対してテンプレートを変えて再分析したい。これにより、目的に応じた観点で企業を評価できる。

#### 受入基準

1. WHEN ユーザーが Deep_Analysis を要求した場合、THE Analysis_Service SHALL 蓄積済みの pages/page_versions データを使用し、フルクロールを実行しない
2. WHEN Deep_Analysis が要求された場合、THE Analysis_Service SHALL 指定されたテンプレート（general, investment, sales, hiring, competitor, risk）に基づいて分析を実行する
3. WHEN Deep_Analysis の結果が生成された場合、THE System SHALL 新しい Analysis_Run と analysis_results レコードを作成する
4. IF 蓄積データが古い（last_page_crawl_at が一定期間以上前）場合、THEN THE System SHALL ユーザーに再クロールを推奨する通知を表示する

### 要件 7: キャッシュ・再分析ポリシー

**ユーザーストーリー:** ユーザーとして、不要な再処理を避けつつ、必要に応じて最新データで再分析したい。これにより、効率的にリソースを使える。

#### 受入基準

1. WHEN force_refresh が false の場合、THE System SHALL 最新の analysis_results を返却し、再クロール・再分析を実行しない
2. WHEN force_refresh が true の場合、THE System SHALL 再クロールから開始し、新しい Analysis_Run を作成する
3. WHEN 再分析が実行された場合、THE Analysis_Service SHALL 前回の structured データとの差分レポートを生成する
4. THE System SHALL 同一正規化URLに対する企業の重複登録を防止する

### 要件 8: レガシー即時分析の維持

**ユーザーストーリー:** ユーザーとして、企業登録なしでURLを入力して即座に分析結果を得たい。これにより、デモや単発利用が可能になる。

#### 受入基準

1. THE System SHALL 既存の POST /api/analysis エンドポイントを維持し、同期的な即時分析フローを提供する
2. WHEN Legacy_Analysis が実行された場合、THE System SHALL 内部的に企業登録・ページ保存・結果保存を行い、データを蓄積する
3. WHEN Legacy_Analysis の結果が返却された場合、THE System SHALL 既存の AnalysisResponse スキーマとの後方互換性を維持する

### 要件 9: サービス分割（モノリシック関数の分解）

**ユーザーストーリー:** 開発者として、現行の `analyze_company()` 関数を責務ごとに分割したい。これにより、保守性・テスト容易性・再利用性が向上する。

#### 受入基準

1. THE System SHALL analyze_company() の責務を CompanyService、CrawlService、ExtractionService、AnalysisService、JobManager に分割する
2. WHEN 各サービスが独立して呼び出された場合、THE System SHALL 他のサービスに影響を与えずに動作する
3. THE System SHALL 各サービス間のデータ受け渡しを既存の Pydantic スキーマおよび SQLAlchemy モデルを通じて行う

### 要件 10: API設計（新規エンドポイント）

**ユーザーストーリー:** フロントエンド開発者として、企業登録・一覧・詳細・ジョブ管理のAPIを利用したい。これにより、新しいUXを実装できる。

#### 受入基準

1. THE System SHALL POST /api/companies エンドポイントで企業登録を受け付ける
2. THE System SHALL GET /api/companies エンドポイントで企業一覧を返却する
3. THE System SHALL GET /api/companies/{company_id} エンドポイントで企業詳細を返却する
4. THE System SHALL POST /api/companies/{company_id}/crawl エンドポイントでクロールジョブの開始を受け付ける
5. THE System SHALL POST /api/companies/{company_id}/analysis-runs エンドポイントで分析ジョブの開始を受け付ける
6. THE System SHALL GET /api/companies/{company_id}/analysis-results/latest エンドポイントで最新分析結果を返却する
7. THE System SHALL GET /api/companies/{company_id}/analysis-results エンドポイントで分析履歴を返却する
8. THE System SHALL GET /api/analysis-runs/{run_id} エンドポイントでジョブ状態を返却する

### 要件 11: 非同期処理基盤

**ユーザーストーリー:** 開発者として、バックグラウンドジョブを実行する基盤を構築したい。これにより、将来的なスケーリングにも対応できる。

#### 受入基準

1. THE System SHALL FastAPI BackgroundTasks を使用してバックグラウンドジョブを実行する
2. THE System SHALL ジョブの実行状態を Analysis_Run テーブルで管理する
3. WHEN ジョブが失敗した場合、THE System SHALL エラー情報を記録し、Company_Status を "failed" に更新する
4. THE System SHALL 将来的な Celery/Redis Queue/Cloud Tasks への移行を妨げない設計とする

### 要件 12: 既存機能の維持

**ユーザーストーリー:** ユーザーとして、既存の機能（ダウンロード、シェア、比較、深掘りリサーチ、検索）が引き続き利用できてほしい。

#### 受入基準

1. THE System SHALL 既存のダウンロード機能（PDF/Word）を維持する
2. THE System SHALL 既存のシェア機能（共有URL生成・OGP対応）を維持する
3. THE System SHALL 既存の複数企業比較機能を維持する
4. THE System SHALL 既存の深掘りリサーチ（会話型）機能を維持する
5. THE System SHALL 既存の企業名検索（URL補完）機能を維持する
6. THE System SHALL 既存の Clerk Google OAuth 認証を維持する

### 要件 13: マイグレーション戦略

**ユーザーストーリー:** 開発者として、既存コードを壊さずに段階的に新アーキテクチャへ移行したい。

#### 受入基準

1. THE System SHALL 既存のデータベーススキーマとの後方互換性を維持する
2. WHEN 新しいサービス層が導入された場合、THE System SHALL 既存の analyze_company() を新サービス層のオーケストレーションとしてリファクタリングする
3. THE System SHALL 既存のフロントエンドコードを段階的に新APIに移行する
4. THE System SHALL 新旧エンドポイントを並行稼働させる移行期間を設ける
