"""Bốn phương pháp attribution, dùng chung một judge interface.

Khác nhau ở số lượt gọi LLM và ở lượng trajectory đưa vào mỗi lượt:

  all_at_once   — một lượt, thấy toàn bộ trajectory
  step_by_step  — hỏi tuần tự từng bước, dừng ở bước decisive đầu tiên
  binary_search — thu hẹp khoảng nghi vấn theo log2(n) lượt rồi xác nhận
  hybrid        — chọn agent trước, sau đó chỉ quét các bước của agent đó

Mọi phương pháp đều bắt buộc kết quả nhất quán với trajectory: agent phải tồn tại,
step phải tồn tại, và step phải thuộc về đúng agent đó. Judge trả về cặp không hợp lệ
thì tính là `invalid_prediction`, không phải im lặng nhận bừa.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

from failure_attribution.json_utils import parse_json_object
from failure_attribution.llm import Judge
from failure_attribution.schema import FailureInstance, Prediction, TrajectoryStep

SYSTEM_PROMPT = (
    "Ban la chuyen gia phan tich loi cua he thong Text-to-SQL nhieu agent. "
    "Nhiem vu: xac dinh agent nao va buoc nao la nguyen nhan QUYET DINH khien SQL cuoi cung sai. "
    "Chi chon buoc dau tien ma o do loi tro nen khong the cuu van. "
    "Luon tra loi bang MOT JSON object hop le, khong kem giai thich ngoai JSON."
)

_REPAIR_SUFFIX = (
    "\n\nOutput truoc do khong phai JSON hop le. "
    "Tra loi lai bang DUNG mot JSON object, khong co text nao khac."
)


def validate_agent_step(
    trajectory: Sequence[TrajectoryStep],
    agent: Optional[str],
    step_id: Optional[int],
) -> Optional[str]:
    """Trả về None nếu cặp (agent, step) nhất quán với trajectory, ngược lại là mô tả lỗi."""
    agents = {step.agent for step in trajectory}
    by_step = {step.step_id: step for step in trajectory}

    if agent is None or agent not in agents:
        return f"unknown agent: {agent!r}"
    if step_id is None or step_id not in by_step:
        return f"unknown step: {step_id!r}"
    if by_step[step_id].agent != agent:
        return f"step {step_id} belongs to {by_step[step_id].agent!r}, not {agent!r}"
    return None


def _payload(item: FailureInstance, include_gold: bool, steps: Sequence[TrajectoryStep]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "question": item.question,
        "db_id": item.db_id,
        "predicted_sql": item.predicted_sql,
        "trajectory": [step.as_prompt_entry() for step in steps],
    }
    if item.database_schema:
        payload["database_schema"] = item.database_schema
    if item.execution_result:
        payload["execution_result"] = item.execution_result
    if include_gold:
        payload["gold_sql"] = item.gold_sql
    return payload


def _ask(judge: Judge, prompt: str, raw_log: List[str], tag: str = "") -> Tuple[Optional[Dict[str, Any]], int]:
    """Gọi judge, tự thử sửa một lần nếu output không phải JSON.

    Trả về (object hoặc None, số lượt gọi đã dùng).
    """
    calls = 0
    current = prompt
    for attempt in range(2):
        raw = judge.complete(SYSTEM_PROMPT, current)
        calls += 1
        raw_log.append(f"{tag}: {raw}" if tag else raw)
        try:
            return parse_json_object(raw), calls
        except ValueError:
            if attempt == 0:
                current = prompt + _REPAIR_SUFFIX
    return None, calls


def _finalize(
    item: FailureInstance,
    method: str,
    agent: Optional[str],
    step_id: Optional[int],
    obj: Dict[str, Any],
    calls: int,
    raw_log: List[str],
) -> Prediction:
    error = validate_agent_step(item.trajectory, agent, step_id)
    if error:
        return Prediction(
            instance_id=item.instance_id,
            method=method,
            status="invalid_prediction",
            failure_agent=agent,
            failure_step=step_id,
            reason=str(obj.get("reason") or ""),
            confidence=_as_float(obj.get("confidence")),
            llm_calls=calls,
            raw_responses=raw_log,
            error=error,
        )
    return Prediction(
        instance_id=item.instance_id,
        method=method,
        status="ok",
        failure_agent=agent,
        failure_step=step_id,
        reason=str(obj.get("reason") or ""),
        confidence=_as_float(obj.get("confidence")),
        llm_calls=calls,
        raw_responses=raw_log,
    )


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _empty(item: FailureInstance, method: str) -> Prediction:
    return Prediction(
        instance_id=item.instance_id,
        method=method,
        status="no_candidate_step",
        error="trajectory rỗng, không có bước nào để quy lỗi",
    )


def _judge_error(item: FailureInstance, method: str, calls: int, raw_log: List[str]) -> Prediction:
    return Prediction(
        instance_id=item.instance_id,
        method=method,
        status="judge_error",
        llm_calls=calls,
        raw_responses=raw_log,
        error="judge không trả về JSON hợp lệ sau khi đã thử sửa",
    )


def all_at_once(item: FailureInstance, judge: Judge, include_gold: bool = True) -> Prediction:
    """Đưa toàn bộ trajectory vào một lượt hỏi duy nhất."""
    if not item.trajectory:
        return _empty(item, "all_at_once")

    prompt = (
        "Duoi day la mot case Text-to-SQL that bai, kem toan bo trajectory cac agent.\n\n"
        + json.dumps(_payload(item, include_gold, item.trajectory), ensure_ascii=False, indent=2)
        + '\n\nTra ve JSON: {"failure_agent": <ten agent>, "failure_step": <step_id>, '
        '"reason": <giai thich ngan>, "confidence": <0..1>}'
    )
    raw_log: List[str] = []
    obj, calls = _ask(judge, prompt, raw_log)
    if obj is None:
        return _judge_error(item, "all_at_once", calls, raw_log)
    return _finalize(item, "all_at_once", obj.get("failure_agent"), _as_int(obj.get("failure_step")), obj, calls, raw_log)


def _scan(
    item: FailureInstance,
    judge: Judge,
    steps: Sequence[TrajectoryStep],
    include_gold: bool,
    method: str,
    raw_log: List[str],
    calls_so_far: int = 0,
) -> Prediction:
    """Quét tuần tự `steps`, dừng ở bước decisive đầu tiên."""
    calls = calls_so_far
    last_obj: Dict[str, Any] = {}
    for step in steps:
        prompt = (
            "Duoi day la mot case Text-to-SQL that bai. Xet DUNG MOT buoc duoi day.\n\n"
            + json.dumps(_payload(item, include_gold, item.trajectory), ensure_ascii=False, indent=2)
            + "\n\nBuoc dang xet:\n"
            + json.dumps(step.as_prompt_entry(), ensure_ascii=False, indent=2)
            + '\n\nBuoc nay co phai loi quyet dinh khong? Tra ve JSON: '
            '{"is_decisive_error": <true|false>, "failure_agent": <ten agent>, '
            '"failure_step": <step_id>, "reason": <ly do>, "confidence": <0..1>}'
        )
        obj, used = _ask(judge, prompt, raw_log)
        calls += used
        if obj is None:
            return _judge_error(item, method, calls, raw_log)
        last_obj = obj
        if bool(obj.get("is_decisive_error")):
            agent = obj.get("failure_agent") or step.agent
            step_id = _as_int(obj.get("failure_step"))
            if step_id is None:
                step_id = step.step_id
            return _finalize(item, method, agent, step_id, obj, calls, raw_log)

    # Không bước nào được nhận là decisive — báo rõ thay vì đoán bừa.
    return Prediction(
        instance_id=item.instance_id,
        method=method,
        status="invalid_prediction",
        reason=str(last_obj.get("reason") or ""),
        llm_calls=calls,
        raw_responses=raw_log,
        error="không có bước nào được judge nhận là decisive",
    )


def step_by_step(item: FailureInstance, judge: Judge, include_gold: bool = True) -> Prediction:
    """Hỏi lần lượt từng bước theo thứ tự thời gian, dừng ở bước decisive đầu tiên."""
    if not item.trajectory:
        return _empty(item, "step_by_step")
    return _scan(item, judge, item.trajectory, include_gold, "step_by_step", [])


def binary_search(item: FailureInstance, judge: Judge, include_gold: bool = True) -> Prediction:
    """Thu hẹp khoảng nghi vấn bằng nhị phân, rồi xác nhận ở bước còn lại."""
    if not item.trajectory:
        return _empty(item, "binary_search")

    raw_log: List[str] = []
    calls = 0
    low, high = 0, len(item.trajectory) - 1

    while low < high:
        mid = (low + high) // 2
        prompt = (
            "Duoi day la mot case Text-to-SQL that bai.\n\n"
            + json.dumps(_payload(item, include_gold, item.trajectory), ensure_ascii=False, indent=2)
            + f"\n\nBuoc moc dang xet la step_id={item.trajectory[mid].step_id} "
            f"(agent {item.trajectory[mid].agent!r}).\n"
            'Loi quyet dinh nam o phia nao cua moc nay? "left" nghia la tai moc hoac truoc do, '
            '"right" nghia la sau moc.\n'
            'Tra ve JSON: {"side": "left"|"right", "reason": <ly do>, "confidence": <0..1>}'
        )
        obj, used = _ask(judge, prompt, raw_log, tag="range_decision")
        calls += used
        if obj is None:
            return _judge_error(item, "binary_search", calls, raw_log)
        if str(obj.get("side") or "").lower() == "left":
            high = mid
        else:
            low = mid + 1

    return _scan(item, judge, [item.trajectory[low]], include_gold, "binary_search", raw_log, calls)


def hybrid(item: FailureInstance, judge: Judge, include_gold: bool = True) -> Prediction:
    """Chọn agent nghi vấn trước, sau đó chỉ quét các bước của agent đó.

    Step id gốc được giữ nguyên — sub-trajectory không đánh số lại.
    """
    if not item.trajectory:
        return _empty(item, "hybrid")

    raw_log: List[str] = []
    agents: List[str] = []
    for step in item.trajectory:
        if step.agent not in agents:
            agents.append(step.agent)

    prompt = (
        "Duoi day la mot case Text-to-SQL that bai, kem toan bo trajectory.\n\n"
        + json.dumps(_payload(item, include_gold, item.trajectory), ensure_ascii=False, indent=2)
        + f"\n\nCac agent co mat: {json.dumps(agents, ensure_ascii=False)}\n"
        'Agent nao chiu trach nhiem cho loi quyet dinh? '
        'Tra ve JSON: {"failure_agent": <ten agent>, "reason": <ly do>, "confidence": <0..1>}'
    )
    obj, calls = _ask(judge, prompt, raw_log, tag="agent_selection")
    if obj is None:
        return _judge_error(item, "hybrid", calls, raw_log)

    agent = obj.get("failure_agent")
    if agent not in agents:
        return Prediction(
            instance_id=item.instance_id,
            method="hybrid",
            status="invalid_prediction",
            failure_agent=agent,
            reason=str(obj.get("reason") or ""),
            confidence=_as_float(obj.get("confidence")),
            llm_calls=calls,
            raw_responses=raw_log,
            error=f"unknown agent: {agent!r}",
        )

    steps = [step for step in item.trajectory if step.agent == agent]
    return _scan(item, judge, steps, include_gold, "hybrid", raw_log, calls)


METHODS = {
    "all_at_once": all_at_once,
    "step_by_step": step_by_step,
    "binary_search": binary_search,
    "hybrid": hybrid,
}
