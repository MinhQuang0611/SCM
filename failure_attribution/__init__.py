"""Failure attribution cho Text-to-SQL multi-agent pipelines.

Trả lời câu hỏi: khi final SQL sai, agent/stage nào là nguyên nhân quyết định.
Đầu vào là `predictions.jsonl` do các baseline sinh ra (xem `.claude/CLAUDE.md`),
trong đó `stage_logs` giữ raw output của từng stage.
"""

from failure_attribution.schema import FailureInstance, Prediction, TrajectoryStep

__all__ = ["FailureInstance", "Prediction", "TrajectoryStep"]
