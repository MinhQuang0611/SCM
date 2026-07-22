import os
from pathlib import Path


def _load_env_file() -> None:
    candidates = [Path.cwd() / ".env"]
    candidates.extend(parent / ".env" for parent in Path.cwd().parents)
    for candidate in candidates:
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        return


_load_env_file()

API_BASE = os.getenv("OPENAI_API_BASE") or os.getenv("API_BASE") or None
API_KEY = (
    os.getenv("OPENAI_API_KEY_2")
    or os.getenv("API_KEY_2")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("API_KEY")
    or ""
)
MODEL_NAME = os.getenv("OPENAI_MODEL") or os.getenv("MODEL_NAME") or "gpt-4o-mini"
