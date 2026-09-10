#!/usr/bin/env python3
"""Preflight checks for the CHESS reproduction baseline.

This script is intentionally read-only except for writing a manifest under
`results/preflight/`. It does not call an LLM and does not run preprocessing.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
BASELINE = ROOT / "baselines/text2sql/22_chess"
CHESS = BASELINE / "code/CHESS"
RESULTS = BASELINE / "results/preflight"


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def command_output(args: list[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(args, cwd=cwd, text=True).strip()
    except Exception as exc:  # noqa: BLE001
        return f"UNAVAILABLE: {exc}"


def check_python_packages(packages: list[str]) -> dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in packages}


def main() -> int:
    env = load_env(CHESS / ".env")
    data_mode = env.get("DATA_MODE", "dev")
    data_path = CHESS / env.get("DATA_PATH", "./data/dev/dev.json")
    db_root_path = CHESS / env.get("DB_ROOT_PATH", "./data/dev")
    db_root_directory = CHESS / env.get("DB_ROOT_DIRECTORY", "./data/dev/dev_databases")
    tables_path = CHESS / env.get("DATA_TABLES_PATH", "./data/dev/dev_tables.json")
    sds_path = CHESS / "data/dev/sub_sampled_bird_dev_set.json"

    checks: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "baseline": "22_chess",
        "chess_dir": rel(CHESS),
        "source_commit": command_output(["git", "rev-parse", "HEAD"], CHESS) if (CHESS / ".git").exists() else None,
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
        },
        "env_file_exists": (CHESS / ".env").exists(),
        "api_key_present": bool(env.get("OPENAI_API_KEY")),
        "data_mode": data_mode,
        "paths": {
            "data_path": {"path": rel(data_path), "exists": data_path.exists()},
            "sds_path": {"path": rel(sds_path), "exists": sds_path.exists()},
            "db_root_path": {"path": rel(db_root_path), "exists": db_root_path.exists()},
            "db_root_directory": {"path": rel(db_root_directory), "exists": db_root_directory.exists()},
            "tables_path": {"path": rel(tables_path), "exists": tables_path.exists()},
        },
        "scripts": {
            "run_preprocess": (CHESS / "run/run_preprocess.sh").exists(),
            "run_main_ir_ss_cg": (CHESS / "run/run_main_ir_ss_cg.sh").exists(),
            "run_main_ir_cg_ut": (CHESS / "run/run_main_ir_cg_ut.sh").exists(),
        },
        "configs": {
            "IR_SS_CG": (CHESS / "run/configs/CHESS_IR_SS_CG.yaml").exists(),
            "IR_CG_UT": (CHESS / "run/configs/CHESS_IR_CG_UT.yaml").exists(),
        },
        "python_packages_current_env": check_python_packages(
            ["langchain_openai", "langchain_chroma", "datasketch", "sqlglot", "sentence_transformers", "faiss"]
        ),
        "sds": {},
        "blocking_issues": [],
        "warnings": [],
    }

    if sds_path.exists():
        sds = json.loads(sds_path.read_text(encoding="utf-8"))
        checks["sds"] = {
            "n": len(sds),
            "first_db_id": sds[0].get("db_id") if sds else None,
            "difficulty_counts": {
                difficulty: sum(1 for row in sds if row.get("difficulty") == difficulty)
                for difficulty in sorted({row.get("difficulty") for row in sds})
            },
        }

    if not checks["env_file_exists"]:
        checks["blocking_issues"].append("Run scripts/configure_env.sh to create code/CHESS/.env.")
    if not checks["api_key_present"]:
        checks["warnings"].append("OPENAI_API_KEY is missing; LLM stages will fail until configured.")
    if not data_path.exists():
        checks["blocking_issues"].append("DATA_PATH is missing. For SDS pilot, copy sub_sampled_bird_dev_set.json to data/dev/dev.json.")
    if not db_root_directory.exists():
        checks["blocking_issues"].append("DB_ROOT_DIRECTORY is missing. Provide BIRD dev_databases under code/CHESS/data/dev/dev_databases.")
    if not tables_path.exists():
        checks["blocking_issues"].append("DATA_TABLES_PATH is missing. Provide BIRD dev_tables.json under code/CHESS/data/dev/dev_tables.json.")
    missing_packages = [name for name, ok in checks["python_packages_current_env"].items() if not ok]
    if missing_packages:
        checks["warnings"].append(
            "Current Python environment is missing packages: "
            + ", ".join(missing_packages)
            + ". Install requirements in the CHESS venv before running."
        )

    checks["status"] = "PASS" if not checks["blocking_issues"] and not checks["warnings"] else (
        "PASS_WITH_WARNINGS" if not checks["blocking_issues"] else "BLOCKED"
    )

    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "run_manifest.json"
    output.write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"status": checks["status"], "manifest": rel(output), "blocking_issues": checks["blocking_issues"], "warnings": checks["warnings"]}, indent=2))
    return 0 if checks["status"] in {"PASS", "PASS_WITH_WARNINGS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
