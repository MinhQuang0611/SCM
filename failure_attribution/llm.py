"""Judge interface và các implementation không tốn API.

Judge chỉ có một hợp đồng: nhận (system, user) và trả về text. Nhờ vậy test chạy
được offline, và việc đổi provider không đụng tới `methods.py`.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


class Judge:
    """Hợp đồng tối thiểu cho một judge."""

    name: str = "judge"

    def complete(self, system: str, user: str) -> str:  # pragma: no cover - abstract
        raise NotImplementedError


class MockJudge(Judge):
    """Trả về các response đã định sẵn, theo đúng thứ tự.

    `calls` ghi lại từng lượt gọi dạng `(system, {"role": "user", "content": ...})`
    để test kiểm tra được nội dung prompt thực sự gửi đi.
    """

    name = "mock"

    def __init__(self, responses: Sequence[str]) -> None:
        self.responses: List[str] = list(responses)
        self.calls: List[Tuple[str, Dict[str, str]]] = []
        self._cursor = 0

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, {"role": "user", "content": user}))
        if self._cursor >= len(self.responses):
            raise IndexError(f"MockJudge hết response ở lượt gọi thứ {self._cursor + 1}")
        response = self.responses[self._cursor]
        self._cursor += 1
        return response


class DeterministicJudge(Judge):
    """Judge offline suy ra câu trả lời từ chính trajectory trong prompt.

    Dùng cho smoke run và test end-to-end: luôn sinh cặp agent/step hợp lệ nên
    pipeline chạy hết được mà không gọi API. Nó KHÔNG phải baseline attribution —
    không dùng số của nó để báo cáo.
    """

    name = "deterministic"

    def complete(self, system: str, user: str) -> str:
        steps = _extract_steps(user)
        if not steps:
            return json.dumps({"failure_agent": None, "failure_step": None, "reason": "no step", "confidence": 0.0})
        step_id, agent = steps[0]
        payload: Dict[str, Any] = {
            "failure_agent": agent,
            "failure_step": step_id,
            "reason": "deterministic offline judge: chọn bước đầu tiên",
            "confidence": 0.0,
        }
        if "is_decisive_error" in user:
            payload["is_decisive_error"] = True
        if "range_decision" in user or '"side"' in user:
            payload["side"] = "left"
        return json.dumps(payload)


_STEP_RE = re.compile(r'"step_id"\s*:\s*(\d+)\s*,\s*"agent"\s*:\s*"([^"]+)"')


def _extract_steps(prompt: str) -> List[Tuple[int, str]]:
    return [(int(m.group(1)), m.group(2)) for m in _STEP_RE.finditer(prompt)]


class OpenAIJudge(Judge):
    """Judge gọi OpenAI-compatible API. Chỉ khởi tạo khi thực sự dùng."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        from openai import OpenAI  # import trễ để môi trường không có SDK vẫn chạy test

        self.name = model
        self.model = model
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("thiếu OPENAI_API_KEY")
        self._client = OpenAI(api_key=key, base_url=base_url or os.environ.get("OPENAI_BASE_URL") or None)

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return response.choices[0].message.content or ""


def make_judge(provider: str, model: str) -> Judge:
    """Tạo judge theo tên provider.

    `mock` và `deterministic` chạy offline; `openai` cần API key.
    """
    key = (provider or "").lower()
    if key in {"mock", "deterministic", "offline"}:
        return DeterministicJudge()
    if key in {"openai", "azure", "compatible"}:
        return OpenAIJudge(model=model)
    raise ValueError(f"provider không hỗ trợ: {provider}")
