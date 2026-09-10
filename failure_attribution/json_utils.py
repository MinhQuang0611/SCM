"""Trích JSON object từ output của LLM.

LLM thường bọc JSON trong code fence hoặc kèm lời dẫn. Module này lấy ra object
đầu tiên hợp lệ; không sửa được thì raise, để caller quyết định có retry hay không.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _candidates(text: str):
    """Sinh các đoạn có khả năng là JSON, theo thứ tự ưu tiên giảm dần."""
    stripped = text.strip()
    yield stripped
    for block in _FENCE.findall(text):
        yield block.strip()
    # Quét object cân bằng ngoặc, bỏ qua ngoặc nằm trong string.
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for i, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    yield text[start : i + 1]


def parse_json_object(text: str) -> Dict[str, Any]:
    """Trả về JSON object đầu tiên đọc được trong `text`.

    Raise ValueError nếu không có đoạn nào parse thành dict.
    """
    if not text or not text.strip():
        raise ValueError("empty response")
    for candidate in _candidates(text):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("no JSON object found in response")
