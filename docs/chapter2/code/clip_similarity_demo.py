"""
最小可运行的 CLIP 图文相似度示例
================================
体验"跨模态对齐"的最短路径：把图片和文字编码到同一语义空间，计算余弦相似度。

依赖：
    pip install transformers pillow torch

运行：
    python clip_similarity_demo.py

说明：
    首次运行会自动下载 openai/clip-vit-base-patch32（约 600MB）。
    如果网络受限，可先用 HF-Mirror：
        export HF_ENDPOINT=https://hf-mirror.com   # Linux/macOS
        set HF_ENDPOINT=https://hf-mirror.com      # Windows
"""

from pathlib import Path

from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel


def main():
    # 1. 加载模型和 processor
    print("Loading CLIP model...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    # 2. 准备图片（用占位图或你自己的图片）
    # 如果没有图片，先运行 docs/chapter4/code/create_placeholder_images.py 生成一张
    img_candidates = [
        Path(__file__).with_name("sample_image.png"),
        Path(__file__).parents[2] / "chapter4" / "code" / "images" / "sample_image_000.png",
        Path("cat.jpg"),
    ]
    image_path = None
    for p in img_candidates:
        if p.exists():
            image_path = p
            break

    if image_path is None:
        print("No image found. Please run: python docs/chapter4/code/create_placeholder_images.py")
        return

    image = Image.open(image_path).convert("RGB")
    print(f"Using image: {image_path}")

    # 3. 候选文本
    texts = [
        "a photo of a cat",
        "a photo of a dog",
        "a photo of a car",
        "a screenshot of a website",
        "a document with text",
    ]

    # 4. 编码
    inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)

    # 5. 计算相似度
    logits = outputs.logits_per_image[0]
    probs = logits.softmax(dim=0)

    # 6. 输出结果
    print("\n图文相似度（CLIP  logits）：")
    for text, logit in zip(texts, logits):
        print(f"  {text:30s}  logit={logit:7.3f}")

    print("\nSoftmax 概率分布：")
    for text, prob in zip(texts, probs):
        print(f"  {text:30s}  prob={prob:.4f}")

    # 7. 最匹配的文本
    best_idx = int(probs.argmax())
    print(f"\n最匹配的描述：\"{texts[best_idx]}\"（概率 {probs[best_idx]:.2%}）")

    # 8. 扩展实验建议
    print("\n扩展实验：")
    print("  1. 换一张截图，问 'error message' / 'login page' / 'dashboard'，观察概率变化")
    print("  2. 换一张票据图，问 'invoice' / 'receipt' / 'contract'，验证 OCR 相关语义")
    print("  3. 自己写 10 条描述，跑一遍，理解 CLIP 的'判别式'边界在哪里")


if __name__ == "__main__":
    main()
