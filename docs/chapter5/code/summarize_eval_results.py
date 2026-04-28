"""汇总 eval_vlm_dataset.py 输出的 JSONL，便于写报告或做 A/B 对照（仅标准库）。"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def _try_utf8_stdio() -> None:
    """尽量在 Windows 等环境下用 UTF-8 输出，避免中文表头在终端乱码。"""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if reconf is None:
            continue
        try:
            reconf(encoding="utf-8")
        except (OSError, ValueError, AttributeError):
            pass


def _load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _rough_ref_hit(row: dict) -> bool:
    """reference 非空且 prediction 含 reference（小写子串）视为粗命中。"""
    ref = (row.get("reference") or "").strip()
    if not ref or row.get("status") != "ok":
        return False
    pred = (row.get("prediction") or "").strip().lower()
    return ref.lower() in pred


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    ok = sum(1 for r in rows if r.get("status") == "ok")
    err = n - ok
    ref_ok = [r for r in rows if (r.get("reference") or "").strip() and r.get("status") == "ok"]
    hits = sum(1 for r in ref_ok if _rough_ref_hit(r))
    ref_den = len(ref_ok)
    hit_rate = (hits / ref_den) if ref_den else None

    times = [
        float(r["elapsed_seconds"])
        for r in rows
        if r.get("status") == "ok" and isinstance(r.get("elapsed_seconds"), (int, float))
    ]
    mean_t = statistics.mean(times) if times else None
    median_t = statistics.median(times) if times else None

    by_tag: dict[str, dict[str, int]] = {}
    for r in rows:
        tags = r.get("tags") or []
        if not isinstance(tags, list):
            continue
        for t in tags:
            if not isinstance(t, str):
                continue
            bucket = by_tag.setdefault(t, {"n": 0, "ok": 0, "ref_ok": 0, "hit": 0})
            bucket["n"] += 1
            if r.get("status") == "ok":
                bucket["ok"] += 1
            if (r.get("reference") or "").strip() and r.get("status") == "ok":
                bucket["ref_ok"] += 1
                if _rough_ref_hit(r):
                    bucket["hit"] += 1

    return {
        "n": n,
        "ok": ok,
        "err": err,
        "ref_den": ref_den,
        "rough_hits": hits,
        "rough_hit_rate": hit_rate,
        "latency_mean": mean_t,
        "latency_median": median_t,
        "by_tag": by_tag,
    }


def _format_text_section(label: str, s: dict) -> str:
    lines = [
        f"=== {label} ===",
        f"样本数: {s['n']}, status=ok: {s['ok']}, status=error: {s['err']}",
    ]
    if s["ref_den"]:
        lines.append(
            f"含 reference 且 ok: {s['ref_den']}, 粗粒度子串命中: {s['rough_hits']} "
            f"({s['rough_hit_rate']:.1%})"
        )
    else:
        lines.append("无 reference 或无可评的 ok 行：粗粒度命中率跳过（可只做耗时与错误率）。")
    if s["latency_mean"] is not None:
        lines.append(f"耗时(s): mean={s['latency_mean']:.3f}, median={s['latency_median']:.3f}")
    if s["by_tag"]:
        lines.append("按 tags（在 ok 子集上有 reference 时统计 hit/ref_ok）：")
        for tag in sorted(s["by_tag"]):
            b = s["by_tag"][tag]
            hr = (b["hit"] / b["ref_ok"]) if b["ref_ok"] else None
            hr_s = f"{hr:.1%}" if hr is not None else "n/a"
            lines.append(
                f"  [{tag}] n={b['n']}, ok={b['ok']}, ref_ok={b['ref_ok']}, hit={b['hit']}, hit/ref_ok={hr_s}"
            )
    lines.append("")
    return "\n".join(lines) + "\n"


def _format_markdown_table(names: list[str], stats: list[dict]) -> str:
    headers = ["指标", *names]
    rows_out: list[list[str]] = []

    def row(metric: str, cells: list[str]) -> None:
        rows_out.append([metric, *cells])

    row("样本数", [str(s["n"]) for s in stats])
    row("status=ok", [str(s["ok"]) for s in stats])
    row("status=error", [str(s["err"]) for s in stats])
    row("错误率", [f"{s['err'] / s['n']:.1%}" if s["n"] else "n/a" for s in stats])
    row(
        "粗粒度参考命中率",
        [
            f"{s['rough_hit_rate']:.1%}" if s["rough_hit_rate"] is not None else "n/a"
            for s in stats
        ],
    )
    row(
        "平均耗时(s)",
        [f"{s['latency_mean']:.3f}" if s["latency_mean"] is not None else "n/a" for s in stats],
    )

    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows_out:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="汇总 eval_results.jsonl：错误率、粗粒度 reference 命中、耗时、按 tags 分桶。",
    )
    p.add_argument("input", type=str, help="eval_vlm_dataset.py 输出的 JSONL")
    p.add_argument(
        "--compare",
        "-c",
        action="append",
        default=[],
        help="可多次传入，与主文件并列对比（Markdown 表）",
    )
    p.add_argument(
        "--markdown",
        action="store_true",
        help="只输出 Markdown 表（单文件为一列，多文件为多列对比）",
    )
    p.add_argument(
        "--label",
        action="append",
        default=[],
        help="与每个输入文件对应的列名（顺序与 input + --compare 一致）",
    )
    p.add_argument(
        "--write",
        "-w",
        type=str,
        default="",
        metavar="PATH",
        help="将本次终端应输出的全文写入 UTF-8 文件（便于 Windows 下用编辑器查看）",
    )
    return p.parse_args()


def main() -> None:
    _try_utf8_stdio()
    args = parse_args()
    paths = [Path(args.input).expanduser().resolve(), *[Path(p).expanduser().resolve() for p in args.compare]]
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)

    labels = list(args.label)
    default_labels = [path.stem for path in paths]
    if len(labels) < len(paths):
        labels = labels + default_labels[len(labels) :]
    labels = labels[: len(paths)]

    stats_list = [summarize(_load_rows(p)) for p in paths]

    chunks: list[str] = []
    if args.markdown:
        chunks.append(_format_markdown_table(labels, stats_list))
    else:
        for label, st in zip(labels, stats_list):
            chunks.append(_format_text_section(label, st))
        if len(stats_list) > 1:
            chunks.append("--- Markdown（便于粘贴进笔记/报告）---\n")
            chunks.append(_format_markdown_table(labels, stats_list))

    report = "".join(chunks)
    out_path = (args.write or "").strip()
    if out_path:
        Path(out_path).expanduser().resolve().write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
