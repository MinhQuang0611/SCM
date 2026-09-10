#!/usr/bin/env python3
"""Minimal iterative repair loop over BIRD-CRITIC PostgreSQL instances.

Establishes the baseline that any attribution-guided method has to beat: the
model proposes a fix, the fix is executed against the real database, and the
observation is fed back for another attempt, up to k rounds. This is the
Self-Debugging setting (Chen et al., ICLR 2024) applied to SQL issue repair --
deliberately *without* any localization signal, so the lift it produces is
attributable to execution feedback alone.

Three things are measured, in order of how much they matter:

1. Success rate versus single-shot, which bounds how much room a localization
   signal could still add.
2. The round at which the final answer stops changing. If everything is decided
   in round 1, later rounds are inert and step-level attribution has nothing to
   attribute over -- this is a go/no-go gate, not a secondary statistic.
3. The lift split by failure class. Execution errors come with a database
   message that names the defect; assertion failures come with silence. The
   loop is expected to recover the former and not the latter.

Grading is deliberately NOT done here: the hidden test cases only run inside
the evaluation container. This script executes predictions solely to produce
feedback for the next round, then writes trajectories for the harness to grade.
Every statement runs inside a transaction that is rolled back, so database
state is never mutated.
"""

import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
from openai import OpenAI

COHERE_BASE_URL = "https://api.cohere.ai/compatibility/v1"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PG = dict(host="127.0.0.1", port=5432, user="root", password="123123")

MAX_ATTEMPTS = 5
MAX_ROWS_SHOWN = 10
MAX_FEEDBACK_CHARS = 1500

# Same generation settings as the single-shot run, so the only difference
# between this and the baseline is the feedback loop itself.
TEMPERATURE = 0
TOP_P = 1

FEEDBACK_PROMPT = """Your previous SQL was executed against the database. Here is what happened.

# Your previous SQL:
{prev_sql}

# Execution outcome:
{observation}

Revise your SQL so it correctly resolves the user's issue. If the outcome above
shows an error, fix its cause. If it ran but you believe the result does not
answer the issue, reconsider your interpretation.
Wrap your corrected SQL in ```sql ... ``` tags."""


def load_env(path):
    env = {}
    if not os.path.isfile(path):
        return env
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def extract_sql(text):
    """Same extraction rule as the upstream post-processor."""
    return [s.strip() for s in re.findall(r"```[ \t]*sql\s*([\s\S]*?)```", text or "", re.I)]


def observe(db_name, preprocess_sql, pred_sqls):
    """Execute a candidate and describe the outcome in natural language.

    Everything happens inside one transaction that is always rolled back, so
    running the loop leaves the shared databases untouched -- including for the
    Management-category instances whose fixes are UPDATE/DDL statements.
    """
    if not pred_sqls:
        return "No SQL statement could be parsed from your response.", "no_sql"

    conn = None
    try:
        conn = psycopg2.connect(dbname=db_name, **PG)
        conn.autocommit = False
        cur = conn.cursor()
        try:
            for sql in preprocess_sql or []:
                cur.execute(sql)
            last_desc, last_rows = None, None
            for sql in pred_sqls:
                cur.execute(sql)
                last_desc = cur.description
                if cur.description is not None:
                    last_rows = cur.fetchmany(MAX_ROWS_SHOWN)
        except Exception as exc:
            msg = str(exc).strip().splitlines()[0]
            return f"The statement failed with a database error:\n{msg}", "error"
        finally:
            conn.rollback()

        if last_desc is None:
            return "The statement executed successfully and returned no result set.", "ok_no_rows"
        cols = [d[0] for d in last_desc]
        if not last_rows:
            return (
                f"The statement executed successfully. Columns: {cols}. "
                "It returned zero rows.",
                "ok_empty",
            )
        body = "\n".join(str(r) for r in last_rows)
        return (
            f"The statement executed successfully. Columns: {cols}.\n"
            f"First rows:\n{body}"[:MAX_FEEDBACK_CHARS],
            "ok_rows",
        )
    except Exception as exc:
        return f"Could not connect to the database: {exc}", "conn_error"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def call(client, model, messages, max_tokens):
    last = None
    kwargs = {"max_tokens": max_tokens} if max_tokens else {}
    for attempt in range(MAX_ATTEMPTS):
        try:
            c = client.chat.completions.create(
                model=model, messages=messages,
                temperature=TEMPERATURE, top_p=TOP_P, **kwargs,
            )
            ch = c.choices[0]
            usage = {}
            if c.usage is not None:
                usage = {
                    "input_tokens": c.usage.prompt_tokens,
                    "output_tokens": c.usage.completion_tokens,
                    "total_tokens": c.usage.total_tokens,
                }
            return ch.message.content or "", getattr(ch, "finish_reason", None), usage, None
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            status = getattr(exc, "status_code", None)
            if status in (400, 401, 403, 404, 422):
                break
            time.sleep(min(2 ** attempt, 30))
    return "", None, {}, last


def run_instance(client, model, rec, k, max_tokens, out_path, lock):
    messages = [{"role": "user", "content": rec["prompt"]}]
    rounds = []
    started = time.time()
    final_sqls, final_obs, final_kind = [], None, None

    for r in range(1, k + 1):
        text, finish, usage, err = call(client, model, messages, max_tokens)
        sqls = extract_sql(text)
        obs, kind = observe(rec["db_id"], rec.get("preprocess_sql"), sqls)

        rounds.append({
            "round": r,
            "model": model,
            "prompt": messages[-1]["content"],
            "response": text,
            "pred_sqls": sqls,
            "observation": obs,
            "outcome_kind": kind,
            "usage": usage,
            "finish_reason": finish,
            "call_error": err,
        })
        final_sqls, final_obs, final_kind = sqls, obs, kind

        if err:
            break
        # An error message is actionable; a clean run is not self-evidently
        # wrong, but we still let the model reconsider once more, because the
        # silent-failure class is exactly what a single execution cannot catch.
        if r == k:
            break
        messages = messages + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": FEEDBACK_PROMPT.format(
                prev_sql="\n".join(sqls) if sqls else "(none parsed)", observation=obs)},
        ]

    # Which round produced the SQL that was ultimately submitted.
    settled = 1
    for i in range(len(rounds) - 1, 0, -1):
        if rounds[i]["pred_sqls"] != rounds[i - 1]["pred_sqls"]:
            settled = i + 1
            break

    row = {k_: v for k_, v in rec.items() if k_ != "prompt"}
    row.update({
        "pred_sqls": final_sqls,
        "final_observation": final_obs,
        "final_outcome_kind": final_kind,
        "n_rounds": len(rounds),
        "settled_round": settled,
        "changed_after_round1": settled > 1,
        "latency_s": round(time.time() - started, 3),
        "usage": {
            "input_tokens": sum(r["usage"].get("input_tokens", 0) for r in rounds),
            "output_tokens": sum(r["usage"].get("output_tokens", 0) for r in rounds),
            "total_tokens": sum(r["usage"].get("total_tokens", 0) for r in rounds),
        },
        "call_error": next((r["call_error"] for r in rounds if r["call_error"]), None),
        "stage_logs": {"prompt_flow": [
            {"model": r["model"], "prompt": r["prompt"], "response": r["response"]} for r in rounds
        ], "rounds": rounds},
    })

    with lock:
        with open(out_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return rec["instance_id"], settled, final_kind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt_path", required=True)
    ap.add_argument("--output_path", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--model", default=None)
    ap.add_argument("--max_tokens", type=int, default=0, help="0 sends no cap")
    args = ap.parse_args()

    env = load_env(os.path.join(REPO_ROOT, ".env"))
    key = env.get("COHERE_API_KEY") or env.get("API_KEY_2") or os.environ.get("COHERE_API_KEY")
    model = args.model or env.get("COHERE_MODEL")
    if not key:
        sys.exit("No Cohere key (COHERE_API_KEY / API_KEY_2)")

    recs = load_jsonl(args.prompt_path)
    if args.limit:
        recs = recs[: args.limit]

    os.makedirs(os.path.dirname(os.path.abspath(args.output_path)), exist_ok=True)
    done = set()
    if os.path.isfile(args.output_path):
        done = {json.loads(l)["instance_id"] for l in open(args.output_path, encoding="utf-8") if l.strip()}
    todo = [r for r in recs if r["instance_id"] not in done]

    print(f"model={model}  k={args.k}  todo={len(todo)}  (skipped {len(done)})")
    if not todo:
        return

    client = OpenAI(base_url=COHERE_BASE_URL, api_key=key)
    lock = threading.Lock()
    settled_hist, kinds = {}, {}

    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futs = [pool.submit(run_instance, client, model, r, args.k, args.max_tokens,
                            args.output_path, lock) for r in todo]
        for n, f in enumerate(as_completed(futs), 1):
            iid, settled, kind = f.result()
            settled_hist[settled] = settled_hist.get(settled, 0) + 1
            kinds[kind] = kinds.get(kind, 0) + 1
            if n % 10 == 0 or n == len(futs):
                print(f"  [{n}/{len(futs)}]")

    print(f"\nvong ma dap an duoc chot: {dict(sorted(settled_hist.items()))}")
    print(f"ket qua thuc thi vong cuoi: {kinds}")
    print(f"output -> {os.path.normpath(args.output_path)}")


if __name__ == "__main__":
    main()
