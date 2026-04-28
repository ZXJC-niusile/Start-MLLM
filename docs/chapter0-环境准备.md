# Chapter 0 环境准备与前置说明

> 如果你已有 Python + PyTorch 环境，可跳过本章直接读 [前言](./前言.md)。
> 如果你没有 GPU，也不用担心，第七章提供「纯 API 方案」，有网就能跑。

## 一、你需要准备什么

这份教程的**绝对最低要求**只有两条：

1. 会写基础 Python（能写函数、能装 pip 包）
2. 能打开命令行（Windows 的 cmd / PowerShell，或 Linux/macOS 的 Terminal）

以下这些**有则更好，没有也能先读起来**：

- PyTorch 基础经验
- 对 Transformer、Token、Embedding 的初步认知
- 调通过 LLM 推理

如果暂时不熟悉，先按「概念优先、代码其次」读，后面逐步补齐。

## 二、Python 环境安装（最小路径）

### 1. 安装 Miniconda

访问 https://docs.conda.io/en/latest/miniconda.html 下载对应系统的安装包，按向导安装即可。

### 2. 创建隔离环境

```bash
conda create -n start-mllm python=3.10 -y
conda activate start-mllm
```

### 3. 验证 Python

```bash
python --version   # 应显示 3.10.x
```

## 三、GPU 环境自检（本地推理需要）

如果你有一块 NVIDIA 显卡，且希望本地跑模型，按下面检查：

```bash
# 检查 CUDA 是否可用
python -c "import torch; print(torch.cuda.is_available())"

# 检查 GPU 型号与显存
python -c "import torch; print(torch.cuda.get_device_name(0)); print(torch.cuda.get_device_properties(0).total_memory / 1024**3, 'GB')"
```

输出 `True` 且显存 ≥ 8GB，即可跑第七章的本地推理示例（Qwen2.5-VL-3B 约需 6~8GB）。

如果输出 `False`，有三种可能：
1. 没有 NVIDIA 显卡 → 用第七章的 **API 方案**
2. 有显卡但没装驱动 → 先装驱动
3. 驱动装了但 PyTorch 是 CPU 版 → 重装 PyTorch GPU 版

### PyTorch GPU 版安装（如需）

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

cu121 表示 CUDA 12.1。如果你的 CUDA 版本不同，到 https://pytorch.org/get-started/locally/ 选择对应版本。

## 四、没有 GPU 怎么办（API 方案）

这是**完全可行的路径**，很多读者全程用 API 学完本教程。

### 免费或低成本 API 选项（2026 年 4 月）

| 平台 | 额度 | 特点 | 适用章节 |
|---|---|---|---|
| **DashScope（阿里云）** | 新用户百万 token 免费 | Qwen 系列官方接口，多模态支持好 | 第七、八、九章 |
| **SiliconFlow** | 注册送额度，价格较低 | 聚合多种开源 VLM，OpenAI 兼容 | 第七、八、九章 |
| **ModelScope** | 部分模型免费 | 国产模型生态，社区活跃 | 第七章 |
| **智谱 GLM-4V API** | 新用户免费额度 | 中文场景强，文档清晰 | 第七、八章 |

### API 方案的最小配置

以 DashScope 为例：

```bash
pip install -r docs/chapter7/code/requirements-api.txt   # 不含 torch，仅 50MB
```

.env 文件（或环境变量）：

```bash
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
MODEL_ID=qwen2.5-vl-3b-instruct
```

然后直接运行第七章脚本即可，不需要任何 GPU。

## 五、本书代码依赖总览

| 章节 | 核心依赖 | 大小 | 说明 |
|---|---|---|---|
| 第四章数据校验 | 仅标准库 | 0 | 不依赖 PyTorch |
| 第五章评测 | openai, pillow | ~50MB | API 方式 |
| 第七章本地推理 | torch, transformers, pillow | ~3GB | 需 GPU |
| 第七章 API 推理 | openai, pillow | ~50MB | 无需 GPU |
| 第八章 Demo | gradio, openai | ~200MB | 无需 GPU |
| 第九章 Agent | openai, python-dotenv | ~50MB | 无需 GPU |

**建议**：先走 API 路线跑通第七~九章，建立手感后再决定是否本地部署。

## 六、常见问题

### Q：Mac（M 系列芯片）能跑吗？
A：能。MPS 后端支持大部分操作，但大模型推理速度通常不如 NVIDIA GPU。建议用 API 方案，或跑较小模型（如 Qwen2.5-VL-3B）。

### Q：Windows 和 Linux 命令有区别吗？
A：主要有两处：
- 设置环境变量：`set VAR=value`（Windows） vs `export VAR=value`（Linux/macOS）
- 路径分隔符：`\`（Windows） vs `/`（Linux/macOS），但 Python 的 `pathlib` 已自动处理

### Q：需要多少钱？
A：如果只用免费额度 + 本地跑 3B 小模型，成本接近零。后续如果要微调大模型或高频调用 API，才需要考虑预算。

## 七、本章小结

- **最低门槛**：Python 基础 + 能装 pip 包
- **两条路线**：有 GPU → 本地推理；无 GPU → API 方案
- **推荐顺序**：先 API 跑通 → 建立手感 → 再决定是否本地部署

准备好环境后，从 [前言](./前言.md) 开始阅读，或跳过理论直接从 [第七章](./chapter7/第七章%20动手跑通你的第一个%20VLM.md) 动手。
