import json
from pathlib import Path
from typing import Any


DATASET_PATH = Path("sample_multimodal_sft.jsonl")


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    image_path = Path(record.get("image", ""))
    messages = record.get("messages", [])
    user_turns = sum(1 for item in messages if item.get("role") == "user")
    assistant_turns = sum(1 for item in messages if item.get("role") == "assistant")
    has_empty_text = False

    for message in messages:
        for content in message.get("content", []):
            if content.get("type") == "text" and not str(content.get("text", "")).strip():
                has_empty_text = True

    return {
        "id": record.get("id", ""),
        "image": str(image_path),
        "image_exists": image_path.exists(),
        "message_count": len(messages),
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "has_empty_text": has_empty_text,
    }


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    summaries: list[dict[str, Any]] = []
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            summaries.append(validate_record(record))

    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

