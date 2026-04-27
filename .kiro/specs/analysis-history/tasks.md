# 実装計画: analysis-history

## 概要

企業ごとの分析実行履歴を取得するAPIエンドポイントと、フロントエンドの「分析履歴」タブを実装する。data-persistence スペックの完了が前提。

## タスク

- [x] 1. 分析履歴 API
  - `server/src/analysis/schemas.py` に AnalysisRunResponse スキーマ追加
  - `server/src/analysis/router.py` に `GET /api/companies/{company_id}/runs` エンドポイント追加
  - AnalysisRunRepository.list_by_company() を使用して新しい順で返す
  - 存在しない company_id に対して 404 を返す
  - _要件: 1.1, 1.2, 1.3_

- [x] 2. フロントエンド — 分析履歴タブ
  - `client/src/widgets/analysis-result/ui/AnalysisResult.tsx` に Mantine Tabs 追加
  - 「分析結果」「分析履歴」「深掘り分析」タブ構成
  - 「分析履歴」タブ: 実行日時・種別バッジ・状態バッジ（completed=緑/failed=赤）・処理時間を一覧表示
  - Orval 生成フック `useGetCompanyRunsApiCompaniesCompanyIdRunsGet` を使用
  - _要件: 2.1, 2.2, 2.3, 2.4_

- [x] 3. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
