"""Chạy attribution trên một file JSONL và ghi prediction ra JSONL.

Ghi append từng dòng ngay sau mỗi instance, nên run dài bị ngắt giữa chừng vẫn giữ
được phần đã chạy và `resume=True` tiếp tục được mà không gọi lại API.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from failure_attribution.evaluate import compute_metrics, format_report
from failure_attribution.llm import Judge, make_judge
from failure_attribution.methods import METHODS
from failure_attribution.normalization import load_failure_instances

SETTINGS = {"with_ground_truth": True, "without_ground_truth": False}


def _existing_ids(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    ids: Set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                ids.add(str(json.loads(line).get("instance_id")))
            except json.JSONDecodeError:
                continue
    return ids


def run_predictions(
    input_path: Path,
    output_path: Path,
    method: str,
    model: str,
    setting: str = "with_ground_truth",
    provider: str = "mock",
    overwrite: bool = False,
    resume: bool = False,
    limit: Optional[int] = None,
    only_failed: bool = True,
    judge: Optional[Judge] = None,
) -> Dict[str, Any]:
    """Chạy một phương pháp trên toàn bộ instance của `input_path`.

    `resume=True` bỏ qua instance đã có trong output. `overwrite=True` xoá output cũ
    trước khi chạy — hai cờ này loại trừ nhau, overwrite được ưu tiên.
    """
    if method not in METHODS:
        raise ValueError(f"method không hợp lệ: {method}; chọn một trong {sorted(METHODS)}")
    if setting not in SETTINGS:
        raise ValueError(f"setting không hợp lệ: {setting}; chọn một trong {sorted(SETTINGS)}")

    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if overwrite and output_path.exists():
        output_path.unlink()

    done: Set[str] = _existing_ids(output_path) if resume and not overwrite else set()

    instances = load_failure_instances(input_path, only_failed=only_failed, limit=limit)
    runner = METHODS[method]
    include_gold = SETTINGS[setting]
    judge = judge or make_judge(provider, model)

    written = 0
    skipped = 0
    with output_path.open("a", encoding="utf-8") as handle:
        for item in instances:
            if item.instance_id in done:
                skipped += 1
                continue
            prediction = runner(item, judge, include_gold)
            row = prediction.to_dict()
            row.update({"model": model, "provider": provider, "setting": setting})
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            written += 1

    return {
        "input": str(input_path),
        "output": str(output_path),
        "method": method,
        "model": model,
        "provider": provider,
        "setting": setting,
        "instances_loaded": len(instances),
        "written": written,
        "skipped_resume": skipped,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Chạy failure attribution trên predictions.jsonl")
    parser.add_argument("--input", required=True, type=Path, help="JSONL đầu vào")
    parser.add_argument("--output", required=True, type=Path, help="JSONL prediction đầu ra")
    parser.add_argument("--method", required=True, choices=sorted(METHODS))
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--provider", default="mock", help="mock | openai")
    parser.add_argument("--setting", default="with_ground_truth", choices=sorted(SETTINGS))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--all-cases", action="store_true", help="giữ cả case đúng, không chỉ case sai")
    parser.add_argument("--metrics-against", type=Path, default=None, help="file gold để tính metric sau khi chạy")
    args = parser.parse_args(argv)

    summary = run_predictions(
        input_path=args.input,
        output_path=args.output,
        method=args.method,
        model=args.model,
        setting=args.setting,
        provider=args.provider,
        overwrite=args.overwrite,
        resume=args.resume,
        limit=args.limit,
        only_failed=not args.all_cases,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.metrics_against:
        metrics = compute_metrics(args.metrics_against, args.output)
        print()
        print(format_report(metrics, title=f"{args.method} / {args.model} / {args.setting}"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
