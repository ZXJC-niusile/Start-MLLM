占位图由脚本生成，不默认提交到 Git。

在 `docs/chapter4/code` 下执行：

```bash
python create_placeholder_images.py
```

再运行 `python prepare_dataset_manifest.py`，此时 `image_exists` 应为 `true`。
