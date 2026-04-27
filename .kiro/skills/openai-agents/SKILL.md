---
name: openai-agents
description: OpenAI Agents SDK（openai-agents）を使ったLLM呼び出しパターン。server/src/analysis/service.py や deep_research/ でコードを書く際に使用する。
license: MIT
metadata:
  author: project
  version: "1.0"
---

# OpenAI Agents SDK — このプロジェクトでの使い方

このプロジェクトは LangChain ではなく **OpenAI Agents SDK（`openai-agents`）** を使用している。

## 初期化（アプリ起動時に1回）

`server/src/shared/llm.py` の `init_llm()` を `main.py` で呼び出す。

```python
from agents import set_default_openai_api, set_default_openai_client, set_tracing_disabled
from openai import AsyncAzureOpenAI
from src.shared.config import get_settings

def init_llm() -> None:
    settings = get_settings()
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.api_version,
    )
    set_default_openai_client(client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
```

## Agent の定義と実行

```python
from agents import Agent, ModelSettings, Runner
from src.shared.config import get_settings

async def run_agent(system_prompt: str, user_message: str) -> str:
    settings = get_settings()
    agent = Agent(
        name="my_agent",
        instructions=system_prompt,   # system プロンプト
        model=settings.azure_deployment,
        model_settings=ModelSettings(temperature=0),
    )
    result = await Runner.run(agent, user_message)
    return result.final_output
```

## このプロジェクトの2エージェント構成

```
extraction_agent  ← EXTRACTION_SYSTEM + EXTRACTION_HUMAN
  → StructuredData（企業プロフィール・財務・ニュース・リスク）

summary_agent     ← get_summary_system(template) + SUMMARY_HUMAN
  → SummaryData + ScoreData（概要・SWOT・競合・展望・スコア）
```

プロンプトは `server/src/analysis/prompts.py` に集約されている。

## エラーハンドリング

```python
from src.shared.exceptions import AnalysisError, ExternalServiceError

try:
    result = await Runner.run(agent, user_message)
except Exception as e:
    if "connection" in str(e).lower() or "timeout" in str(e).lower():
        raise ExternalServiceError(f"Azure OpenAI に接続できません: {e}") from e
    raise AnalysisError(f"LLM処理に失敗しました: {e}") from e
```

## JSON出力のパース

LLMはJSON文字列を返す。コードブロック（` ```json ` 等）が含まれる場合があるため `_clean_json()` で除去してからパースする。

```python
import json

def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        start = 1
        end = next((i for i in range(len(lines)-1, 0, -1) if lines[i].strip().startswith("```")), len(lines))
        text = "\n".join(lines[start:end])
    return text.strip()

parsed = json.loads(_clean_json(result.final_output))
```

## 注意事項

- `Agent` はリクエストごとに生成してよい（ステートレス）
- `Runner.run()` は非同期。必ず `await` する
- `ModelSettings(temperature=0)` で決定論的な出力を得る
- LangChain の `chain.invoke()` や `ChatPromptTemplate` は使わない
