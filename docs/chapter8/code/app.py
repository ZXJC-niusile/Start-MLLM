import base64
import mimetypes
import os
import time
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


TASK_PROMPTS = {
    "自由问答": "{question}",
    "截图报错分析": "请阅读这张截图，定位最关键的问题，解释可能原因，并给出下一步排查建议。\n用户补充问题：{question}",
    "关键信息提取": "请从图片中提取关键信息，并尽量按条目列出。\n用户补充问题：{question}",
    "商品图卖点总结": "请根据图片中的商品外观和使用场景，总结 3 条简洁卖点。\n用户补充问题：{question}",
}


def to_data_url(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def build_prompt(task_mode: str, question: str) -> str:
    template = TASK_PROMPTS.get(task_mode, "{question}")
    return template.format(question=question.strip() or "请分析这张图片。")


def ask_vlm(image_path: str, question: str, task_mode: str) -> tuple[str, str]:
    if not image_path:
        return "请先上传一张图片。", "状态：未执行"

    start = time.perf_counter()
    try:
        client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "EMPTY"),
        )
        model_id = os.getenv("MODEL_ID", "your-vlm")
        data_url = to_data_url(image_path)
        prompt = build_prompt(task_mode, question)

        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            max_tokens=512,
        )
        elapsed = time.perf_counter() - start
        return response.choices[0].message.content, f"状态：已完成，模式={task_mode}，耗时={elapsed:.2f}s"
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return f"请求失败：{exc}", f"状态：失败，模式={task_mode}，耗时={elapsed:.2f}s"


with gr.Blocks(title="Start-MLLM Demo") as demo:
    gr.Markdown("# Start-MLLM 图像问答 Demo")
    gr.Markdown("上传图片，输入问题，通过 OpenAI 兼容接口调用你的多模态模型。")
    gr.Markdown("支持自由问答、截图报错分析、关键信息提取、商品图卖点总结四种基础模式。")
    gr.Markdown("示例问题：请描述图片主要内容 / 请解释截图错误 / 请提取关键信息 / 请总结 3 条卖点")

    with gr.Row():
        image_input = gr.Image(type="filepath", label="上传图片")
        with gr.Column():
            task_mode = gr.Dropdown(
                choices=list(TASK_PROMPTS.keys()),
                value=os.getenv("DEFAULT_MODE", "自由问答"),
                label="任务模式",
            )
            question_input = gr.Textbox(
                label="问题",
                placeholder="例如：请描述这张图，并指出最值得注意的细节。",
                lines=4,
            )
            submit_btn = gr.Button("开始分析")

    answer_output = gr.Textbox(label="模型回答", lines=12)
    status_output = gr.Textbox(label="运行状态", lines=1)

    submit_btn.click(
        fn=ask_vlm,
        inputs=[image_input, question_input, task_mode],
        outputs=[answer_output, status_output],
    )


if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
    )
