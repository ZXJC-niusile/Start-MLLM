"""
教程共用：解析图片路径，减少「当前工作目录不同就找不到图」的摩擦。

放置于 `docs/`，各章脚本通过 `Path(__file__).resolve().parents[2]` 将 `docs` 加入 `sys.path` 后
`import learner_paths`，或自行复制逻辑（第七章依赖此模块）。
"""

from __future__ import annotations

from pathlib import Path

DOCS_ROOT = Path(__file__).resolve().parent


def resolve_image_path(raw: str | None, *, script_file: str) -> Path:
    """
    - 未设置 IMAGE_PATH 时：若存在第五章占位图则使用，否则抛出明确提示。
    - 已设置时：依次尝试绝对/相对路径、当前工作目录、脚本目录、`docs/` 下的相对路径。
    """
    placeholder = DOCS_ROOT / "chapter5" / "code" / "images" / "sample_ui.png"
    s = (raw or "").strip()
    script_dir = Path(script_file).resolve().parent

    if not s:
        if placeholder.is_file():
            return placeholder
        raise FileNotFoundError(
            "未设置 IMAGE_PATH，且未找到第五章占位图 "
            f"{placeholder}。请在 docs/chapter5/code 运行 "
            "`python create_placeholder_images.py`，或设置环境变量 IMAGE_PATH。"
        )

    candidates: list[Path] = [
        Path(s).expanduser(),
        Path.cwd() / s,
        script_dir / s,
        DOCS_ROOT / s,
    ]
    seen: set[str] = set()
    for c in candidates:
        key = str(c)
        if key in seen:
            continue
        seen.add(key)
        try:
            if c.is_file():
                return c.resolve()
        except OSError:
            continue

    raise FileNotFoundError(
        f"找不到图片: {raw!r}。已尝试：当前目录、脚本目录、以及相对于 {DOCS_ROOT} 的路径。"
    )
