# 設計書: deep-research

## 概要

openai-agents SDKのAgentループを使用した深掘り分析。保存済みの `structured` + `summary` をコンテキストとして渡し、不足時のみ追加収集を行う。セッション管理で継続会話に対応する。

## アーキテクチャ

```
POST /api/companies/{company_id}/deep-research
  └── analysis/router.py
        └── DeepResearchService.ask(company_id, question, session_id)
              ├── AnalysisResultRepository.find_latest_by_company() → コンテキスト取得
              ├── DeepResearchSessionRepository.get_or_create()
              ├── Agent(instructions=DEEP_RESEARCH_SYSTEM, context=structured+summary)
              ├── Runner.run(question) → 回答生成
              ├── (不足時) CollectorService で追加収集
              └── DeepResearchMessageRepository.save(question, answer)
```

## コンポーネントとインターフェース

### `server/src/deep_research/service.py`

```python
class DeepResearchService:
    async def ask(
        self,
        company_id: UUID,
        question: str,
        session_id: UUID | None,
        session: AsyncSession
    ) -> DeepResearchResponse:
        # 1. 最新の分析結果からコンテキスト取得
        # 2. セッション取得 or 新規作成
        # 3. 過去メッセージ履歴をコンテキストに追加
        # 4. Agent + Runner.run() で回答生成
        # 5. メッセージ保存
        # 6. DeepResearchResponse を返す
```

### `server/src/analysis/router.py`（追加エンドポイント）

```python
@router.post("/companies/{company_id}/deep-research")
async def deep_research(
    company_id: UUID,
    request: DeepResearchRequest,
    session: AsyncSession = Depends(get_session)
) -> DeepResearchResponse:
```

### `server/src/analysis/schemas.py`（追加スキーマ）

```python
class DeepResearchRequest(BaseModel):
    question: str
    session_id: UUID | None = None

class DeepResearchResponse(BaseModel):
    session_id: UUID
    answer: str
    used_cached_data: bool
    additional_urls: list[str]
```

### DBモデル（`server/src/db/models.py` 追加）

```python
class DeepResearchSession(Base):
    __tablename__ = "deep_research_sessions"
    session_id: UUID (PK)
    company_id: UUID (FK → companies)
    result_id: UUID | None
    status: str  # active / closed
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime

class DeepResearchMessage(Base):
    __tablename__ = "deep_research_messages"
    message_id: UUID (PK)
    session_id: UUID (FK → deep_research_sessions)
    role: str  # user / assistant
    content: str
    used_cached_data: bool | None
    additional_urls: list (JSONB)
    tokens_used: int | None
    sequence: int
    created_at: datetime
```

### フロントエンド

#### `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`（変更）

```tsx
// 「深掘り分析」タブ
const [sessionId, setSessionId] = useState<string | null>(null);
const [messages, setMessages] = useState<Message[]>([]);
const [question, setQuestion] = useState("");

const handleAsk = async () => {
  // POST /api/companies/{company_id}/deep-research
  // { question, session_id: sessionId }
  // → { session_id, answer } を受け取り messages に追加
};
```

## データモデル

`docs/database-design.md` の `deep_research_sessions` / `deep_research_messages` テーブル定義に準拠。

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: セッション継続性
*For any* 既存セッションIDを持つリクエストに対して、返却されるセッションIDは入力と同一である
**Validates: Requirements 1.4**

Property 2: メッセージ順序の保証
*For any* セッションに対して、取得されるメッセージは `sequence` の昇順で並んでいる
**Validates: Requirements 2.3**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| company_id が存在しない | 404 | Company not found |
| 分析結果が存在しない | 404 | No analysis result found |
| LLM呼び出し失敗 | 500 | Agent実行エラー |

## テスト戦略

### ユニットテスト
- 新規セッション作成の確認
- 既存セッションへの継続の確認
- 存在しない company_id に対して 404 が返ることを確認

### プロパティベーステスト
- Property 1: 任意のセッションIDに対してセッション継続性を検証（最低100回）
- Property 2: 任意のメッセージ列に対して順序保証を検証
- タグ形式: `Feature: deep-research, Property {N}: {property_text}`
