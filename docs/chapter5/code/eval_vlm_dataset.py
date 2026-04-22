import base64
import json
import mimetypes
import os
import time
from pathlib import Path

from openai import OpenAI


BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "EMPTY")
MODEL_ID = os.getenv("MODEL_ID", "your-vlm")
DATASET_PATH = Path(os.getenv("DATASET_PATH", "sample_eval_dataset.jsonl"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "eval_results.jsonl"))


def to_data_url(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    results = []

    with DATASET_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            sample = json.loads(line)
            start = time.perf_counter()
            result = {
                "id": sample.get("id", ""),
                "question": sample.get("question", ""),
                "reference": sample.get("reference", ""),
                "tags": sample.get("tags", []),
            }
            try:
                data_url = to_data_url(sample["image"])
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": sample["question"]},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        }
                    ],
                    max_tokens=256,
                )
                result["prediction"] = response.choices[0].message.content
                result["status"] = "ok"
            except Exception as exc:
                result["prediction"] = ""
                result["status"] = "error"
                result["error"] = str(exc)
            result["elapsed_seconds"] = round(time.perf_counter() - start, 3)
            results.append(result)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Saved {len(results)} results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
