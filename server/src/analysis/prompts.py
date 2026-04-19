from langchain_core.prompts import ChatPromptTemplate

ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "あなたは企業分析の専門家です。提供された企業情報を分析し、以下のJSON形式で回答してください。"
        "必ず有効なJSONのみを出力し、それ以外のテキストは含めないでください。\n\n"
        '{{"summary": "企業の概要を3〜5文で要約", '
        '"business_description": "事業内容の詳細な説明", '
        '"key_findings": ["発見事項1", "発見事項2", "発見事項3"]}}'
    ),
    (
        "human",
        "以下は「{company_name}」に関する収集情報です。この情報をもとに分析してください。\n\n{raw_content}"
    ),
])
