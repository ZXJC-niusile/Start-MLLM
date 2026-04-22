"""
生成 sample_multimodal_sft.jsonl 中引用的占位图（纯色块）。

跑通 prepare_dataset_manifest.py 前请先执行本脚本，或自行替换为真实票据/截图。
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
    save_solid_png(root / "sample_receipt.png", 360, 480, 250, 248, 240)
    save_solid_png(root / "sample_error.png", 320, 200, 255, 225, 225)
    save_solid_png(root / "sample_product.png", 400, 400, 245, 245, 250)
    print(f"OK: wrote placeholder PNGs under {root}")


if __name__ == "__main__":
    main()
