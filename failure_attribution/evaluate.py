"""Tính metric attribution bằng cách join gold và prediction theo `instance_id`.

Ba metric chính:

  agent_accuracy      — tỉ lệ đoán đúng agent
  step_accuracy       — tỉ lệ đoán đúng chính xác step
  step_accuracy_at_2  — tỉ lệ đoán step lệch không quá 2 bước so với gold

`step_accuracy_at_2` là metric khoan dung, dùng để phân biệt "sai hoàn toàn vị trí"
với "định vị gần đúng". Nó KHÔNG phải top-2 accuracy: mỗi instance chỉ có một dự đoán.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

STEP_TOLERANCE = 2


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def compute_metrics(gold_path: Path, pred_path: Path) -> Dict[str, Any]:
    """So prediction với nhãn gold, trả về dict metric.

    Chỉ những instance vừa có nhãn gold vừa có prediction `status == "ok"` mới được
    tính vào mẫu số — `evaluable_instances`. Các instance khác được đếm riêng theo
    status để không giấu đi phần pipeline hỏng.
    """
    gold_rows = _read_jsonl(gold_path)
    pred_rows = _read_jsonl(pred_path)

    gold_by_id = {str(row.get("instance_id")): row for row in gold_rows}
    pred_by_id = {str(row.get("instance_id")): row for row in pred_rows}

    status_counts: Counter = Counter(str(row.get("status")) for row in pred_rows)

    agent_hits = 0
    step_hits = 0
    step_within_tolerance = 0
    evaluable = 0
    llm_calls = 0
    missing_prediction = 0
    missing_gold_label = 0

    for instance_id, gold in gold_by_id.items():
        gold_agent = gold.get("gold_failure_agent")
        gold_step = gold.get("gold_failure_step")
        if gold_agent is None or gold_step is None:
            missing_gold_label += 1
            continue

        pred = pred_by_id.get(instance_id)
        if pred is None:
            missing_prediction += 1
            continue

        llm_calls += int(pred.get("llm_calls") or 0)
        if pred.get("status") != "ok":
            continue

        evaluable += 1
        if pred.get("failure_agent") == gold_agent:
            agent_hits += 1
        pred_step = pred.get("failure_step")
        if pred_step is not None:
            if int(pred_step) == int(gold_step):
                step_hits += 1
            if abs(int(pred_step) - int(gold_step)) <= STEP_TOLERANCE:
                step_within_tolerance += 1

    return {
        "gold_instances": len(gold_by_id),
        "predicted_instances": len(pred_by_id),
        "evaluable_instances": evaluable,
        "missing_prediction": missing_prediction,
        "missing_gold_label": missing_gold_label,
        "agent_accuracy": _ratio(agent_hits, evaluable),
        "step_accuracy": _ratio(step_hits, evaluable),
        "step_accuracy_at_2": _ratio(step_within_tolerance, evaluable),
        "agent_hits": agent_hits,
        "step_hits": step_hits,
        "step_within_tolerance": step_within_tolerance,
        "total_llm_calls": llm_calls,
        "status_counts": dict(status_counts),
        "step_tolerance": STEP_TOLERANCE,
    }


def format_report(metrics: Dict[str, Any], title: Optional[str] = None) -> str:
    """Bản in gọn cho terminal hoặc để dán vào report."""
    lines = [f"# {title}" if title else "# Attribution metrics", ""]
    lines.append(f"- Instance có nhãn gold: `{metrics['gold_instances'] - metrics['missing_gold_label']}`")
    lines.append(f"- Đánh giá được: `{metrics['evaluable_instances']}`")
    lines.append(f"- Agent accuracy: `{metrics['agent_accuracy']:.4f}` ({metrics['agent_hits']})")
    lines.append(f"- Step accuracy: `{metrics['step_accuracy']:.4f}` ({metrics['step_hits']})")
    lines.append(
        f"- Step accuracy @±{metrics['step_tolerance']}: "
        f"`{metrics['step_accuracy_at_2']:.4f}` ({metrics['step_within_tolerance']})"
    )
    lines.append(f"- Tổng lượt gọi LLM: `{metrics['total_llm_calls']}`")
    if metrics["status_counts"]:
        lines.append("")
        lines.append("| status | count |")
        lines.append("|---|---:|")
        for status, count in sorted(metrics["status_counts"].items()):
            lines.append(f"| {status} | {count} |")
    return "\n".join(lines) + "\n"
