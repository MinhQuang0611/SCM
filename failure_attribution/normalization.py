"""Chuẩn hoá `predictions.jsonl` của các baseline về một `FailureInstance` chung.

Mỗi baseline log theo kiểu riêng. Module này quy về một trajectory duy nhất để bốn
phương pháp attribution dùng chung được, và để việc thêm baseline mới chỉ là thêm
một adapter ở đây chứ không đụng tới `methods.py`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from failure_attribution.schema import FailureInstance, TrajectoryStep

# Thứ tự bốn stage của DIN-SQL, theo đúng thứ tự chạy trong pipeline.
DIN_STAGE_ORDER: Sequence[tuple] = (
    ("schema_links_raw", "schema_agent", "schema_linking"),
    ("classification_raw", "classification_agent", "difficulty_classification"),
    ("sql_raw", "sql_generation_agent", "sql_generation"),
    ("correction_raw", "correction_agent", "self_correction"),
)

_XVAR = re.compile(r"^x(\d+)$")


def _first(record: Dict[str, Any], *keys: str) -> Any:
    """Giá trị đầu tiên không None trong các key, tìm cả ở `record['case']`."""
    case = record.get("case") or {}
    for key in keys:
        if record.get(key) is not None:
            return record[key]
        if isinstance(case, dict) and case.get(key) is not None:
            return case[key]
    return None


def _instance_id(record: Dict[str, Any]) -> str:
    value = _first(record, "instance_id", "idx", "id", "question_id")
    # `idx` bằng 0 là hợp lệ — không được coi là thiếu.
    return str(value) if value is not None else ""


def _steps_from_stage_logs(stage_logs: Any) -> List[TrajectoryStep]:
    steps: List[TrajectoryStep] = []
    if isinstance(stage_logs, dict):
        for key, agent, stage in DIN_STAGE_ORDER:
            if stage_logs.get(key) is None:
                continue
            steps.append(TrajectoryStep(len(steps), agent, stage, None, str(stage_logs[key])))
        # Key lạ ngoài bốn stage chuẩn: vẫn giữ, xếp sau, để không mất evidence.
        known = {key for key, _, _ in DIN_STAGE_ORDER}
        for key in stage_logs:
            if key in known or stage_logs.get(key) is None:
                continue
            steps.append(TrajectoryStep(len(steps), key, key, None, str(stage_logs[key])))
    elif isinstance(stage_logs, list):
        for entry in stage_logs:
            if not isinstance(entry, dict):
                steps.append(TrajectoryStep(len(steps), f"step_{len(steps)}", "", None, str(entry)))
                continue
            agent = str(entry.get("agent") or entry.get("name") or entry.get("stage") or f"step_{len(steps)}")
            content = entry.get("content") or entry.get("output") or entry.get("raw") or ""
            steps.append(TrajectoryStep(len(steps), agent, str(entry.get("stage") or ""), None, str(content)))
    return steps


def _steps_from_intermediate_vars(record: Dict[str, Any]) -> List[TrajectoryStep]:
    """Fallback: biến trung gian dạng `x1`, `x2`… giữ nguyên chỉ số làm step_id."""
    found = []
    for key, value in record.items():
        match = _XVAR.match(key)
        if match and value is not None:
            found.append((int(match.group(1)), key, value))
    found.sort(key=lambda item: item[0])
    return [TrajectoryStep(index, key, key, None, str(value)) for index, key, value in found]


def normalize_record(record: Dict[str, Any]) -> FailureInstance:
    """Chuyển một record thô thành `FailureInstance`.

    Nhận ba dạng: bản ghi đã chuẩn hoá (có `trajectory`), log DIN-style (có
    `stage_logs`), và log dùng biến trung gian `x1`/`x2`.
    """
    if record.get("trajectory") is not None:
        data = dict(record)
        data.setdefault("instance_id", _instance_id(record))
        data.setdefault("predicted_sql", _first(record, "predicted_sql", "pred_sql") or "")
        data.setdefault("gold_sql", _first(record, "gold_sql", "query") or "")
        return FailureInstance.from_dict(data)

    trajectory = _steps_from_stage_logs(record.get("stage_logs"))
    if not trajectory:
        trajectory = _steps_from_intermediate_vars(record)

    return FailureInstance(
        instance_id=_instance_id(record),
        question=str(_first(record, "question", "utterance") or ""),
        gold_sql=str(_first(record, "gold_sql", "query") or ""),
        predicted_sql=str(_first(record, "predicted_sql", "pred_sql") or ""),
        trajectory=trajectory,
        db_id=_first(record, "db_id"),
        database_schema=_first(record, "database_schema", "schema"),
        execution_result=record.get("pred_exec") or record.get("execution_result"),
        gold_failure_agent=record.get("gold_failure_agent"),
        gold_failure_step=record.get("gold_failure_step"),
    )


def _normalize_sql(sql: str) -> str:
    return " ".join((sql or "").strip().rstrip(";").lower().split())


def is_failed_record(record: Dict[str, Any]) -> bool:
    """Case này có sai không.

    Ưu tiên bằng chứng execution; chỉ khi không có mới so text SQL. So text là
    proxy yếu — hai SQL khác chữ vẫn có thể cho cùng result set.
    """
    if record.get("execution_match") is not None:
        return not bool(record["execution_match"])

    pred_exec = record.get("pred_exec")
    gold_exec = record.get("gold_exec")
    if isinstance(pred_exec, dict) and isinstance(gold_exec, dict):
        both_ok = pred_exec.get("status") == "ok" and gold_exec.get("status") == "ok"
        pred_hash = pred_exec.get("result_hash")
        gold_hash = gold_exec.get("result_hash")
        if both_ok and pred_hash is not None and gold_hash is not None:
            return pred_hash != gold_hash
        return not both_ok

    gold = _normalize_sql(str(_first(record, "gold_sql", "query") or ""))
    pred = _normalize_sql(str(_first(record, "predicted_sql", "pred_sql") or ""))
    return gold != pred


def load_failure_instances(
    path: Path,
    only_failed: bool = True,
    limit: Optional[int] = None,
) -> List[FailureInstance]:
    """Đọc JSONL và trả về các instance đã chuẩn hoá.

    Mặc định chỉ lấy case sai — attribution chỉ có nghĩa trên case sai.
    """
    instances: List[FailureInstance] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if only_failed and not is_failed_record(record):
                continue
            instances.append(normalize_record(record))
            if limit is not None and len(instances) >= limit:
                break
    return instances
