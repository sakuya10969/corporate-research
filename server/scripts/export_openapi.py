"""FastAPI アプリから OpenAPI JSON をファイルに出力するスクリプト"""

import json
import sys
from pathlib import Path

# server/ ディレクトリを sys.path に追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OpenAPI schema exported to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
