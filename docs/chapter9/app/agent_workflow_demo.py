import base64
import json
import mimetypes
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_DOCS = Path(__file__).resolve().parents[2]
if str(_DOCS) not in sys.path:
    sys.path.insert(0, str(_DOCS))
from learner_paths import resolve_image_path
from openai import OpenAI


load_dotenv()


def to_data_url(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


class MultimodalAgent:
    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "EMPTY"),
        )
        self.model_id = os.getenv("MODEL_ID", "your-vlm")

    def perceive(self, image_path: str, question: str) -> str:
        data_url = to_data_url(image_path)
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "请先对图片做感知摘要，提取最关键的对象、文本、界面元素或异常信息。"
                                f"\n用户目标：{question}"
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            max_tokens=256,
        )
        return response.choices[0].message.content

    def decide_tools(self, summary: str) -> list[str]:
        tools = []
        if "报错" in summary or "error" in summary.lower():
            tools.append("knowledge_lookup")
        if "表格" in summary or "金额" in summary:
            tools.append("structured_extract")
        return tools

    def knowledge_lookup(self, summary: str) -> str:
        return f"知识检索占位结果：可根据感知摘要进一步查询错误码、产品文档或 FAQ。\n摘要：{summary}"

    def structured_extract(self, summary: str) -> str:
        return f"结构化提取占位结果：后续可接 OCR、规则抽取或表格解析工具。\n摘要：{summary}"

    def run(self, image_path: str, question: str) -> dict[str, object]:
        if not question.strip():
            return {
                "status": "error",
                "error": "Question is empty.",
            }

        perception = self.perceive(image_path, question)
        tools = self.decide_tools(perception)
        tool_outputs = []

        for tool in tools:
            if tool == "knowledge_lookup":
                tool_outputs.append(self.knowledge_lookup(perception))
            elif tool == "structured_extract":
                tool_outputs.append(self.structured_extract(perception))

        final_response = {
            "status": "ok",
            "question": question,
            "perception": perception,
            "tools": tools,
            "tool_outputs": tool_outputs,
            "next_action": "你可以把这里改成最终总结、JSON 输出或进一步的工具调用。",
        }
        return final_response


def main() -> None:
    raw_path = os.getenv("IMAGE_PATH", "").strip()
    image_path = str(resolve_image_path(raw_path or None, script_file=__file__))
    question = os.getenv("QUESTION", "请分析这张图片，并给出下一步建议。")
    try:
        agent = MultimodalAgent()
        result = agent.run(image_path, question)
    except Exception as exc:
        result = {
            "status": "error",
            "error": str(exc),
            "question": question,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
