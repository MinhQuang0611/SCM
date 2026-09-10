"""Kiểu dữ liệu lõi: một trajectory step, một failure instance, một prediction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TrajectoryStep:
    """Một bước trong pipeline, tương ứng output của một agent/stage."""

    step_id: int
    agent: str
    stage: str = ""
    inputs: Any = None
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent": self.agent,
            "stage": self.stage,
            "inputs": self.inputs,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrajectoryStep":
        return cls(
            step_id=int(data["step_id"]),
            agent=str(data["agent"]),
            stage=str(data.get("stage") or ""),
            inputs=data.get("inputs"),
            content=str(data.get("content") or ""),
        )

    def as_prompt_entry(self) -> Dict[str, Any]:
        """Rút gọn cho prompt — judge chỉ cần định danh bước và nội dung."""
        return {"step_id": self.step_id, "agent": self.agent, "stage": self.stage, "output": self.content}


@dataclass
class FailureInstance:
    """Một case sai, kèm trajectory và (tuỳ chọn) nhãn gold để đánh giá."""

    instance_id: str
    question: str
    gold_sql: str
    predicted_sql: str
    trajectory: List[TrajectoryStep] = field(default_factory=list)
    db_id: Optional[str] = None
    database_schema: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    gold_failure_agent: Optional[str] = None
    gold_failure_step: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "db_id": self.db_id,
            "question": self.question,
            "database_schema": self.database_schema,
            "gold_sql": self.gold_sql,
            "predicted_sql": self.predicted_sql,
            "execution_result": self.execution_result,
            "trajectory": [step.to_dict() for step in self.trajectory],
            "gold_failure_agent": self.gold_failure_agent,
            "gold_failure_step": self.gold_failure_step,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureInstance":
        return cls(
            instance_id=str(data["instance_id"]),
            question=str(data.get("question") or ""),
            gold_sql=str(data.get("gold_sql") or ""),
            predicted_sql=str(data.get("predicted_sql") or ""),
            trajectory=[TrajectoryStep.from_dict(s) for s in data.get("trajectory") or []],
            db_id=data.get("db_id"),
            database_schema=data.get("database_schema"),
            execution_result=data.get("execution_result"),
            gold_failure_agent=data.get("gold_failure_agent"),
            gold_failure_step=data.get("gold_failure_step"),
        )

    def has_gold_label(self) -> bool:
        return self.gold_failure_agent is not None and self.gold_failure_step is not None


@dataclass
class Prediction:
    """Kết quả attribution cho một instance.

    `status` nhận một trong:
      ok                 — dự đoán hợp lệ và nhất quán với trajectory
      invalid_prediction — judge trả về agent/step không tồn tại hoặc lệch nhau
      no_candidate_step  — trajectory rỗng, không có gì để quy lỗi
      judge_error        — judge không trả về JSON hợp lệ sau khi đã thử sửa
    """

    instance_id: str
    method: str
    status: str
    failure_agent: Optional[str] = None
    failure_step: Optional[int] = None
    reason: str = ""
    confidence: Optional[float] = None
    llm_calls: int = 0
    raw_responses: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "method": self.method,
            "status": self.status,
            "failure_agent": self.failure_agent,
            "failure_step": self.failure_step,
            "reason": self.reason,
            "confidence": self.confidence,
            "llm_calls": self.llm_calls,
            "raw_responses": self.raw_responses,
            "error": self.error,
        }
