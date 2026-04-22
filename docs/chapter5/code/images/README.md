本目录下的示例图默认**不会**随仓库提供二进制文件，避免体积膨胀。

首次跑 `eval_vlm_dataset.py` 前，在 `docs/chapter5/code` 下执行：

```bash
python create_placeholder_images.py
```

生成的是纯色占位 PNG，仅用于**跑通路径**；要得到有意义的预测，请换成你自己的截图并同步修改 `sample_eval_dataset.jsonl`。
