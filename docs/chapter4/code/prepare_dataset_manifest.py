import argparse
import json
from pathlib import Path
from typing import Any


def validate_record(record: dict[str, Any], *, dataset_dir: Path) -> dict[str, Any]:
    raw = record.get("image", "")
    image_path = Path(raw) if Path(raw).is_absolute() else (dataset_dir / raw)
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
        "image_exists": image_path.is_file(),
        "message_count": len(messages),
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "has_empty_text": has_empty_text,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="校验多模态 SFT 风格 JSONL（图片是否存在、轮次等）。")
    parser.add_argument(
        "--dataset",
        "-d",
        default="sample_multimodal_sft.jsonl",
        help="JSONL 路径（相对当前工作目录或绝对路径），默认 sample_multimodal_sft.jsonl",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset).expanduser()
    if not dataset_path.is_absolute():
        dataset_path = (Path.cwd() / dataset_path).resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    dataset_dir = dataset_path.parent
    summaries: list[dict[str, Any]] = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            summaries.append(validate_record(record, dataset_dir=dataset_dir))

    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
