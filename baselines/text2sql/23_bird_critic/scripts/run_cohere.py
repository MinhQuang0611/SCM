#!/usr/bin/env python3
"""Run a Cohere model over BIRD-CRITIC prompts via the OpenAI-compatible API.

Replaces the repo's ``baseline/src/call_api.py`` rather than patching it, for
three reasons:

1. ``call_api.py`` dispatches on substrings of the model name (``gpt`` /
   ``claude`` / ``gemini``) and raises on anything else, so ``command-r-*``
   cannot run through it.
2. Its ``api_request`` retries in a bare ``while True`` with no cap -- a bad
   key or a permanent 4xx spins forever.
3. It records only the final string. We need the full ``prompt_flow``
   (model / prompt / response per step), which is both the BIRD-CRITIC
   submission format and the trajectory this project's attribution work reads.

Generation parameters follow the repo defaults (temperature 0, max_tokens 512)
so the result stays comparable to the published baseline.

Output is one JSON object per line: the source record plus ``response``,
``prompt_flow``, ``usage``, ``latency_s`` and ``call_error``. Appends as it
goes and skips instances already present, so an interrupted run resumes
without paying for completed calls again.
"""

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

COHERE_BASE_URL = "https://api.cohere.ai/compatibility/v1"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

# Repo defaults from baseline/src/call_api.py
DEFAULT_TEMPERATURE = 0
DEFAULT_TOP_P = 1

# Upstream hardcodes max_tokens=512 (call_api.py:116, undocumented -- neither the
# README nor run_baseline.sh mentions it). At that cap 16.7% of command-a's
# answers were cut mid-statement, and a cut answer yields broken SQL that scores
# as a model failure rather than a configuration artefact. We send no cap at all,
# so the model stops where it wants, bounded only by its own limit.
UPSTREAM_MAX_TOKENS = 512

MAX_ATTEMPTS = 5


def load_env(path):
    """Minimal .env reader -- avoids a python-dotenv dependency."""
    env = {}
    if not os.path.isfile(path):
        return env
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def done_ids(path):
    if not os.path.isfile(path):
        return set()
    seen = set()
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                seen.add(json.loads(line)["instance_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return seen


def call_once(client, model, prompt, max_tokens):
    """One completion with bounded retry. Returns (text, usage, finish, error).

    ``finish_reason`` is recorded because token counts alone do not identify a
    truncated answer: a response cut off at the cap reports 511 completion
    tokens, not 512, so a `>= max_tokens` test silently misses every one of
    them. A truncated answer ends mid-statement and the SQL extractor then
    yields broken SQL, which scores as a model failure when it is really a
    configuration artefact.
    """
    last_error = None
    kwargs = {}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    for attempt in range(MAX_ATTEMPTS):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=DEFAULT_TEMPERATURE,
                top_p=DEFAULT_TOP_P,
                **kwargs,
            )
            choice = completion.choices[0]
            text = choice.message.content or ""
            finish = getattr(choice, "finish_reason", None)
            usage = {}
            if completion.usage is not None:
                usage = {
                    "input_tokens": completion.usage.prompt_tokens,
                    "output_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens,
                }
            return text, usage, finish, None
        except Exception as exc:  # noqa: BLE001 - surface whatever the SDK raises
            last_error = f"{type(exc).__name__}: {exc}"
            status = getattr(exc, "status_code", None)
            # Do not burn retries on errors that will never succeed.
            if status is not None and status in (400, 401, 403, 404, 422):
                break
            time.sleep(min(2 ** attempt, 30))
    return "", {}, None, last_error


def worker(client, model, record, out_path, lock, max_tokens):
    prompt = record["prompt"]
    started = time.time()
    text, usage, finish, error = call_once(client, model, prompt, max_tokens)
    elapsed = round(time.time() - started, 3)

    row = {k: v for k, v in record.items() if k != "prompt"}
    row["response"] = text
    row["prompt_flow"] = [{"model": model, "prompt": prompt, "response": text}]
    row["usage"] = usage
    row["finish_reason"] = finish
    row["truncated"] = finish == "length"
    row["max_tokens"] = max_tokens
    row["latency_s"] = elapsed
    row["call_error"] = error

    with lock:
        with open(out_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return record["instance_id"], error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt_path", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--model", default=None, help="defaults to COHERE_MODEL in .env")
    parser.add_argument("--limit", type=int, default=None, help="first N instances only")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=0,
        help=f"0 (default) sends no cap; pass {UPSTREAM_MAX_TOKENS} to reproduce upstream's hidden limit",
    )
    args = parser.parse_args()

    env = load_env(os.path.join(REPO_ROOT, ".env"))
    # API_KEY holds an OpenAI-format key; the Cohere one lives in API_KEY_2.
    api_key = (
        env.get("COHERE_API_KEY")
        or env.get("CO_API_KEY")
        or env.get("API_KEY_2")
        or os.environ.get("COHERE_API_KEY")
    )
    model = args.model or env.get("COHERE_MODEL")
    if not api_key:
        sys.exit("No API key: set API_KEY in .env or COHERE_API_KEY in the environment")
    if not model:
        sys.exit("No model: pass --model or set COHERE_MODEL in .env")

    records = load_jsonl(args.prompt_path)
    if args.limit is not None:
        records = records[: args.limit]

    os.makedirs(os.path.dirname(os.path.abspath(args.output_path)), exist_ok=True)
    already = done_ids(args.output_path)
    todo = [r for r in records if r["instance_id"] not in already]

    print(f"model      : {model}")
    print(f"max_tokens : {args.max_tokens or 'no cap sent'}")
    print(f"prompts    : {len(records)}")
    print(f"already    : {len(already)}")
    print(f"to run     : {len(todo)}")
    if not todo:
        return

    client = OpenAI(base_url=COHERE_BASE_URL, api_key=api_key)
    lock = threading.Lock()
    errors = 0
    completed = 0

    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = [
            pool.submit(worker, client, model, r, args.output_path, lock, args.max_tokens)
            for r in todo
        ]
        for future in as_completed(futures):
            instance_id, error = future.result()
            completed += 1
            if error:
                errors += 1
                print(f"  [{completed}/{len(todo)}] {instance_id} ERROR {error[:140]}")
            elif completed % 10 == 0 or completed == len(todo):
                print(f"  [{completed}/{len(todo)}] ok")

    print(f"\ndone. call_error on {errors}/{len(todo)}")
    print(f"output -> {os.path.normpath(args.output_path)}")


if __name__ == "__main__":
    main()
