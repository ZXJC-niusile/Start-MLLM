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


def validate_sft_format(record: dict[str, Any], line_num: int) -> list[str]:
    """
    严格校验单条 SFT 样本格式是否符合多模态训练标准。
    返回错误列表，空列表表示通过。
    """
    errors: list[str] = []

    # 1. 必须有 id
    if not record.get("id"):
        errors.append(f"[{line_num}] 缺少 'id' 字段")

    # 2. 必须有 messages
    messages = record.get("messages")
    if not messages:
        errors.append(f"[{line_num}] 缺少 'messages' 字段或为空")
        return errors
    if not isinstance(messages, list):
        errors.append(f"[{line_num}] 'messages' 必须是列表")
        return errors

    # 3. messages 结构校验
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            errors.append(f"[{line_num}] messages[{i}] 必须是字典")
            continue

        role = msg.get("role")
        if role not in ("user", "assistant", "system"):
            errors.append(f"[{line_num}] messages[{i}].role 非法: '{role}'，必须为 user/assistant/system")

        content = msg.get("content")
        if not content:
            errors.append(f"[{line_num}] messages[{i}] 缺少 'content'")
            continue
        if not isinstance(content, list):
            errors.append(f"[{line_num}] messages[{i}].content 必须是列表")
            continue

        for j, part in enumerate(content):
            if not isinstance(part, dict):
                errors.append(f"[{line_num}] messages[{i}].content[{j}] 必须是字典")
                continue

            part_type = part.get("type")
            if part_type not in ("text", "image"):
                errors.append(
                    f"[{line_num}] messages[{i}].content[{j}].type 非法: '{part_type}'，必须为 text/image"
                )

            if part_type == "text":
                text_val = part.get("text")
                if text_val is None:
                    errors.append(f"[{line_num}] messages[{i}].content[{j}] text 类型缺少 'text' 值")
                elif not str(text_val).strip():
                    errors.append(f"[{line_num}] messages[{i}].content[{j}] text 值为空")

            if part_type == "image":
                img_val = part.get("image")
                if not img_val:
                    errors.append(f"[{line_num}] messages[{i}].content[{j}] image 类型缺少 'image' 路径")

    # 4. 轮次校验：必须以 user 开始，user/assistant 交替（允许 system 在开头）
    non_system = [m for m in messages if m.get("role") != "system"]
    if non_system:
        if non_system[0].get("role") != "user":
            errors.append(f"[{line_num}] 非 system 消息必须以 user 开始")
        for i in range(1, len(non_system)):
            expected = "assistant" if non_system[i - 1].get("role") == "user" else "user"
            if non_system[i].get("role") != expected:
                errors.append(
                    f"[{line_num}] 轮次不交替: messages[{i}] 为 {non_system[i].get('role')}，"
                    f"期望 {expected}"
                )

    # 5. user 消息中至少包含一个 image 或 text
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            content = msg.get("content", [])
            has_image = any(c.get("type") == "image" for c in content)
            has_text = any(c.get("type") == "text" and str(c.get("text", "")).strip() for c in content)
            if not has_image and not has_text:
                errors.append(f"[{line_num}] messages[{i}] (user) 既无 image 也无有效 text")

    # 6. assistant 消息中至少包含一个 text
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", [])
            has_text = any(c.get("type") == "text" and str(c.get("text", "")).strip() for c in content)
            if not has_text:
                errors.append(f"[{line_num}] messages[{i}] (assistant) 缺少有效 text")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="校验多模态 SFT 风格 JSONL（图片是否存在、轮次、SFT 格式合规性等）。"
    )
    parser.add_argument(
        "--dataset",
        "-d",
        default="sample_multimodal_sft.jsonl",
        help="JSONL 路径（相对当前工作目录或绝对路径），默认 sample_multimodal_sft.jsonl",
    )
    parser.add_argument(
        "--check-sft-format",
        action="store_true",
        help="启用严格的 SFT 格式校验（role/content 结构、类型合法性、轮次交替等）",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset).expanduser()
    if not dataset_path.is_absolute():
        dataset_path = (Path.cwd() / dataset_path).resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    dataset_dir = dataset_path.parent
    summaries: list[dict[str, Any]] = []
    sft_errors: list[str] = []
    line_num = 0

    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            summaries.append(validate_record(record, dataset_dir=dataset_dir))
            if args.check_sft_format:
                sft_errors.extend(validate_sft_format(record, line_num))

    # 基础校验结果
    print(json.dumps(summaries, ensure_ascii=False, indent=2))

    # SFT 格式校验报告
    if args.check_sft_format:
        print("\n" + "=" * 50)
        if sft_errors:
            print(f"SFT 格式校验：发现 {len(sft_errors)} 个问题")
            for err in sft_errors:
                print(f"  ❌ {err}")
            print("\n修复建议：")
            print("  1. 每条样本必须有 'id' 字段")
            print("  2. messages 必须是列表，每个元素是字典")
            print("  3. role 必须是 user/assistant/system 之一")
            print("  4. content 必须是列表，元素 type 必须是 text 或 image")
            print("  5. user/assistant 必须交替出现，以 user 开始")
            print("  6. user 消息至少包含一个 image 或 text")
            print("  7. assistant 消息至少包含一个 text")
        else:
            print("SFT 格式校验：✅ 全部通过（共 {} 条）".format(len(summaries)))


if __name__ == "__main__":
    main()
