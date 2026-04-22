"""
生成评测 JSONL 引用的占位图（纯色小图，仅用于跑通脚本与目录结构）。

学习者后续应换成真实截图；有图之后 eval 才有业务意义。
纯标准库，无需 pip 额外依赖。
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack("!I", len(data)) + chunk_type + data + struct.pack("!I", crc)


def save_solid_png(path: Path, width: int, height: int, r: int, g: int, b: int) -> None:
    """写一张 RGB 8-bit、filter 0 的 PNG。"""
    row = bytes([0] + [r, g, b] * width)
    raw = row * height
    compressed = zlib.compress(raw, 9)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0)
    png = signature + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", compressed) + _png_chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def main() -> None:
    root = Path(__file__).resolve().parent / "images"
    # 与 sample_eval_dataset.jsonl 文件名一致
    save_solid_png(root / "sample_ui.png", 320, 200, 230, 240, 255)
    save_solid_png(root / "sample_error.png", 320, 200, 255, 220, 220)
    save_solid_png(root / "sample_chart.png", 400, 240, 220, 235, 220)
    print(f"OK: wrote placeholder PNGs under {root}")


if __name__ == "__main__":
    main()
