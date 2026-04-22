# 第七章 动手跑通你的第一个 VLM

这一章开始进入实践。目标很明确：你至少要跑通一条最小多模态链路，并真正看懂输入输出长什么样。

本章提供两种方式：

1. 直接用 `Transformers` 调本地模型
2. 用 OpenAI 兼容接口调用多模态服务

## 一、代码位置

本章配套代码位于：

- `docs/chapter7/code/transformers_chat.py`
- `docs/chapter7/code/openai_compatible_client.py`
- `docs/chapter7/code/requirements.txt`

## 二、方式一：用 Transformers 本地推理

### 1. 安装依赖

```bash
pip install -r docs/chapter7/code/requirements.txt
```

### 2. 准备模型和图片

你需要准备：

- 一个支持图文对话的视觉语言模型
- 一张待测试图片

脚本默认使用环境变量：

- `MODEL_ID`：模型名称或本地路径
- `IMAGE_PATH`：图片路径
- `QUESTION`：用户问题

### 3. 运行示例

```bash
set MODEL_ID=Qwen/Qwen2.5-VL-3B-Instruct
set IMAGE_PATH=demo.jpg
set QUESTION=请详细描述这张图，并指出其中最重要的视觉元素。
python docs/chapter7/code/transformers_chat.py
```

### 4. 这个脚本在做什么

脚本的关键步骤其实就四步：

1. 加载模型和 processor
2. 构造图文消息
3. 让 processor 把消息变成模型输入
4. 调 `generate` 输出答案

你应该重点关注的不是“命令跑通了”，而是下面三个点：

- 图像消息在代码里是如何表示的
- chat template 是怎么把图文消息拼接成输入的
- 生成后怎样把 prompt 部分裁掉，只保留模型新增输出

## 三、方式二：调用 OpenAI 兼容接口

很多时候你的模型并不直接由业务代码加载，而是由某个服务提供 OpenAI 兼容接口。这时候应用层只需要做两件事：

1. 把图片转成 URL 或 base64 data URL
2. 用 `chat.completions` 方式提交图文消息

### 1. 运行方式

```bash
set OPENAI_BASE_URL=http://127.0.0.1:8000/v1
set OPENAI_API_KEY=EMPTY
set MODEL_ID=your-vlm
set IMAGE_PATH=demo.jpg
set QUESTION=这张图传递了什么信息？
python docs/chapter7/code/openai_compatible_client.py
```

### 2. 为什么推荐保留这一层

如果你后续要做：

- Web Demo
- API 服务
- Agent 工作流
- 多模型路由

那 OpenAI 兼容接口会比直接在业务层加载模型更灵活。

## 四、实践时最常见的报错

### 1. 模型能加载，但回答空白或很奇怪

优先检查：

- 是否用了正确的 chat template
- 图像是否真的传给了 processor
- 输入消息里的 `type` 字段是否符合模型要求

### 2. 接口调用成功，但服务端说图像格式不对

优先检查：

- 是不是把本地路径直接当 URL 发了
- data URL 是否包含 MIME 类型前缀
- 服务端是否真的支持多模态消息

### 3. 显存不够

可以从这些方向降低压力：

- 更换小参数模型
- 量化部署
- 降低输入图像分辨率
- 减少 `max_new_tokens`

## 五、建议你主动做的三个小实验

### 实验 1：同一张图问不同问题

观察模型是否会围绕问题聚焦不同证据。

### 实验 2：换成截图或文档

感受自然图像能力和 OCR/文档能力之间的差异。

### 实验 3：对同一张图问“图中没有的东西”

例如“这张图里有没有红色汽车”，观察模型是否会幻觉。

## 六、从这一步开始，你应该具备什么能力

如果你顺利跑通本章代码，你应该已经能：

- 读懂一个基础 VLM 推理脚本
- 知道图像消息如何进入模型
- 知道 OpenAI 兼容多模态接口怎么写
- 开始自己搭更复杂的 Demo

## 七、进阶实战：把“单次提问”扩成“实验任务”

如果你已经跑通脚本，建议不要停在“问一张图一个问题”。更好的做法是立刻把脚本变成实验工具。

### 你可以增加的三个方向

1. 固定 5 张图片，比较同一 prompt 下的稳定性。
2. 固定 1 张图片，比较不同 prompt 对结果的影响。
3. 固定任务，比较 `Transformers` 本地推理和 OpenAI 兼容接口的回答差异。

### 观察时建议记录

- 模型输出是否基于图像证据
- 是否出现模板化回答
- 对截图、小字、图表是否明显变差
- 同一问题多次请求是否稳定

这会把“能跑通”升级成“会做实验”。

## 八、章末练习

1. 使用本章脚本，对同一张图设计 3 个不同层次的问题。
2. 找一张自然图像和一张截图，比较模型回答差异。
3. 修改脚本，加入 `SYSTEM_PROMPT` 或输出文件保存逻辑。
4. 解释 `apply_chat_template` 在多模态推理链路里的作用。

## 九、配图占位建议

- 建议图 1
  建议文件名：`docs/images/ch7-local-vs-api.png`
  插入位置：第二节后
  画面描述：本地 Transformers 推理和 OpenAI 兼容接口调用两条链路的对比示意图。
- 建议图 2
  建议文件名：`docs/images/ch7-script-output-sample.png`
  插入位置：第六节后
  画面描述：终端运行多模态脚本并输出回答的示意截图，占位即可。

## 十、本章小结

本章不是为了让你记住某个模型命令，而是为了把“多模态推理链路”变具体。只要你能读懂这里的代码，后面无论是做 Demo、做 Agent 还是做服务封装，难度都会明显下降。

## 十一、章节跳转

- 上一篇：[第六章 推理部署与 Serving](../chapter6/第六章%20推理部署与%20Serving.md)
- 下一篇：[第八章 构建一个图像问答 Demo](../chapter8/第八章%20构建一个图像问答%20Demo.md)
- 对应代码：[chapter7/code](./code)
