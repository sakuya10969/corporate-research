# 要件定義: share

## はじめに

分析結果を固有URLで共有できる機能（F-012）。認証不要のパブリックリンクで、URLを知っている人なら誰でも閲覧できる。OGPメタタグでSNSシェア時のプレビューにも対応する。data-persistence スペックの実装が前提。

## 用語集

- **System**: 企業分析エージェント全体
- **ShareService**: シェアID生成・取得サービス
- **SharePage**: 共有ページ（読み取り専用）
- **ShareButton**: シェアボタンUIコンポーネント
- **share_id**: UUID v4の先頭8文字で生成される公開共有ID

## 要件

### 要件1: シェアID生成（F-012）

**ユーザーストーリー:** ユーザーとして、分析結果を固有URLで他者に共有したい。そうすることで、URLを送るだけで分析結果を見せられる。

#### 受け入れ基準

1. WHEN `POST /api/analysis/{result_id}/share` が呼ばれた場合, THE ShareService SHALL UUID v4の先頭8文字を `share_id` として生成する
2. THE System SHALL 生成した `share_id` を `analysis_results.share_id` カラムに保存する
3. THE System SHALL `shared_at` タイムスタンプを記録する
4. IF 指定された `result_id` が存在しない場合, THEN THE System SHALL HTTP 404エラーを返す
5. WHEN 既にシェア済みの分析結果に対して再度シェアリクエストが来た場合, THE System SHALL 既存の `share_id` を返す

---

### 要件2: 共有分析結果取得（F-012）

**ユーザーストーリー:** 共有URLを受け取った人として、認証なしで分析結果を閲覧したい。そうすることで、アカウント登録なしに企業分析を確認できる。

#### 受け入れ基準

1. WHEN `GET /api/share/{share_id}` が呼ばれた場合, THE System SHALL 対応する分析結果を返す
2. THE System SHALL 認証なしで `GET /api/share/{share_id}` にアクセスできる
3. IF 指定された `share_id` が存在しない場合, THEN THE System SHALL HTTP 404エラーを返す

---

### 要件3: シェアUI（F-012）

**ユーザーストーリー:** ユーザーとして、分析結果ページのボタン1つで共有URLをコピーしたい。そうすることで、手軽に共有できる。

#### 受け入れ基準

1. WHEN 分析結果が表示された場合, THE ShareButton SHALL シェアボタンを表示する
2. WHEN シェアボタンが押された場合, THE ShareButton SHALL 共有URLをクリップボードにコピーする
3. WHEN URLがコピーされた場合, THE ShareButton SHALL コピー完了フィードバックを表示する

---

### 要件4: 共有ページとOGP（F-012）

**ユーザーストーリー:** 共有URLを受け取った人として、SNSでシェアされた際にプレビューを確認したい。そうすることで、内容を事前に把握できる。

#### 受け入れ基準

1. THE SharePage SHALL `/share/[shareId]` パスで分析結果を読み取り専用で表示する
2. THE SharePage SHALL OGPメタタグ（og:title, og:description, og:url）を動的に生成する
3. THE System SHALL og:title を `{企業名} の企業分析レポート` とする
4. THE System SHALL og:description を `overview` の先頭150文字とする
