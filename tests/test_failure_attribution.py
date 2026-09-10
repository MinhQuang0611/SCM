from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from failure_attribution.evaluate import compute_metrics
from failure_attribution.json_utils import parse_json_object
from failure_attribution.llm import MockJudge
from failure_attribution.methods import all_at_once, binary_search, hybrid, step_by_step, validate_agent_step
from failure_attribution.normalization import load_failure_instances, normalize_record
from failure_attribution.run import run_predictions
from failure_attribution.schema import FailureInstance, TrajectoryStep


class FailureAttributionTests(unittest.TestCase):
    def instance(self) -> FailureInstance:
        return FailureInstance(
            instance_id="a",
            db_id="db",
            question="q",
            database_schema=None,
            gold_sql="select 1",
            predicted_sql="select 2",
            execution_result={"status": "ok"},
            trajectory=[
                TrajectoryStep(0, "intent_agent", "intent", None, "intent ok"),
                TrajectoryStep(1, "schema_agent", "schema", None, "missing column"),
                TrajectoryStep(2, "sql_generation_agent", "sql", None, "select wrong"),
            ],
            gold_failure_agent="schema_agent",
            gold_failure_step=1,
        )

    def test_normalizes_din_stage_logs(self) -> None:
        record = {
            "case": {"idx": 7, "db_id": "db", "question": "q", "query": "select 1"},
            "pred_sql": "select 2",
            "gold_sql": "select 1",
            "execution_match": False,
            "stage_logs": {"schema_links_raw": "s", "classification_raw": "c", "sql_raw": "sql", "correction_raw": "fix"},
        }
        item = normalize_record(record)
        self.assertEqual(item.instance_id, "7")
        self.assertEqual([step.step_id for step in item.trajectory], [0, 1, 2, 3])
        self.assertEqual(item.trajectory[0].agent, "schema_agent")

    def test_maps_intermediate_variables_to_steps(self) -> None:
        item = normalize_record({"idx": 1, "question": "q", "gold_sql": "a", "pred_sql": "b", "x2": "b", "x1": "a"})
        self.assertEqual([(step.step_id, step.agent) for step in item.trajectory], [(1, "x1"), (2, "x2")])

    def test_preserves_gold_step_zero(self) -> None:
        item = normalize_record({"idx": 0, "question": "q", "gold_sql": "a", "pred_sql": "b", "gold_failure_agent": "x1", "gold_failure_step": 0, "x1": "bad"})
        self.assertEqual(item.instance_id, "0")
        self.assertEqual(item.gold_failure_step, 0)

    def test_validate_agent_step_consistency(self) -> None:
        item = self.instance()
        self.assertIsNone(validate_agent_step(item.trajectory, "schema_agent", 1))
        self.assertIn("unknown agent", validate_agent_step(item.trajectory, "missing", 1) or "")
        self.assertIn("unknown step", validate_agent_step(item.trajectory, "schema_agent", 9) or "")
        self.assertIn("belongs", validate_agent_step(item.trajectory, "schema_agent", 2) or "")

    def test_rejects_nonexistent_agent_prediction(self) -> None:
        judge = MockJudge(['{"failure_agent": "missing", "failure_step": 1, "reason": "bad", "confidence": 0.5}'])
        pred = all_at_once(self.instance(), judge, include_gold=True)
        self.assertEqual(pred.status, "invalid_prediction")
        self.assertIn("unknown agent", pred.error or "")

    def test_rejects_nonexistent_step_prediction(self) -> None:
        judge = MockJudge(['{"failure_agent": "schema_agent", "failure_step": 99, "reason": "bad", "confidence": 0.5}'])
        pred = all_at_once(self.instance(), judge, include_gold=True)
        self.assertEqual(pred.status, "invalid_prediction")
        self.assertIn("unknown step", pred.error or "")

    def test_parse_valid_and_malformed_json(self) -> None:
        self.assertEqual(parse_json_object('{"a":1}')["a"], 1)
        self.assertEqual(parse_json_object('text ```json\n{"a":2}\n```')["a"], 2)

    def test_repairs_malformed_json_response(self) -> None:
        judge = MockJudge(["not json", '{"failure_agent": "schema_agent", "failure_step": 1, "reason": "repaired", "confidence": 0.8}'])
        pred = all_at_once(self.instance(), judge, include_gold=True)
        self.assertEqual(pred.status, "ok")
        self.assertEqual(pred.llm_calls, 2)

    def test_step_by_step_stops_first_positive(self) -> None:
        judge = MockJudge(
            [
                '{"is_decisive_error": false, "failure_agent": null, "failure_step": 0, "reason": "no", "confidence": 0.1}',
                '{"is_decisive_error": true, "failure_agent": "schema_agent", "failure_step": 1, "reason": "schema miss", "confidence": 0.8}',
                '{"is_decisive_error": true, "failure_agent": "sql_generation_agent", "failure_step": 2, "reason": "late", "confidence": 0.8}',
            ]
        )
        pred = step_by_step(self.instance(), judge, include_gold=True)
        self.assertEqual(pred.status, "ok")
        self.assertEqual(pred.failure_step, 1)
        self.assertEqual(pred.llm_calls, 2)

    def test_binary_search_range_updates(self) -> None:
        judge = MockJudge(
            [
                '{"side": "left", "reason": "before mid", "confidence": 0.7}',
                '{"side": "right", "reason": "after first", "confidence": 0.7}',
                '{"is_decisive_error": true, "failure_agent": "schema_agent", "failure_step": 1, "reason": "verify", "confidence": 0.8}',
            ]
        )
        pred = binary_search(self.instance(), judge, include_gold=True)
        self.assertEqual(pred.failure_step, 1)
        self.assertTrue(any("range_decision" in raw for raw in pred.raw_responses))

    def test_hybrid_preserves_original_step_ids(self) -> None:
        judge = MockJudge(
            [
                '{"failure_agent": "sql_generation_agent", "reason": "sql", "confidence": 0.8}',
                '{"is_decisive_error": true, "failure_agent": "sql_generation_agent", "failure_step": 2, "reason": "sql", "confidence": 0.8}',
            ]
        )
        pred = hybrid(self.instance(), judge, include_gold=True)
        self.assertEqual(pred.failure_step, 2)

    def test_no_candidate_step(self) -> None:
        item = self.instance()
        item.trajectory = []
        pred = all_at_once(item, MockJudge([]), include_gold=True)
        self.assertEqual(pred.status, "no_candidate_step")

    def test_without_ground_truth_prompt_omits_gold_sql(self) -> None:
        judge = MockJudge(['{"failure_agent": "schema_agent", "failure_step": 1, "reason": "schema", "confidence": 0.8}'])
        pred = all_at_once(self.instance(), judge, include_gold=False)
        self.assertEqual(pred.status, "ok")
        prompt = judge.calls[0][1]["content"]
        self.assertNotIn('"gold_sql"', prompt)

    def test_resume_behavior_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gold = root / "gold.jsonl"
            pred = root / "pred.jsonl"
            row = self.instance().to_dict()
            gold.write_text(json.dumps(row) + "\n", encoding="utf-8")
            run_predictions(
                input_path=gold,
                output_path=pred,
                method="all_at_once",
                model="mock",
                setting="with_ground_truth",
                provider="mock",
                overwrite=True,
            )
            run_predictions(
                input_path=gold,
                output_path=pred,
                method="all_at_once",
                model="mock",
                setting="with_ground_truth",
                provider="mock",
                resume=True,
            )
            lines = pred.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            metrics = compute_metrics(gold, pred)
            self.assertEqual(metrics["evaluable_instances"], 1)
            self.assertEqual(metrics["step_accuracy_at_2"], 1.0)

    def test_load_only_failed_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            ok = {"idx": 1, "question": "q", "gold_sql": "select 1", "pred_sql": "select 1"}
            fail = {"idx": 2, "question": "q", "gold_sql": "select 1", "pred_sql": "select 2"}
            path.write_text(json.dumps(ok) + "\n" + json.dumps(fail) + "\n", encoding="utf-8")
            rows = load_failure_instances(path)
            self.assertEqual([row.instance_id for row in rows], ["2"])

    def test_execution_match_takes_precedence_over_sql_text_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            row = {
                "idx": 1,
                "question": "q",
                "gold_sql": "select count(*) from t",
                "pred_sql": "select count(*) as c from t",
                "pred_exec": {"status": "ok", "result_hash": "same"},
                "gold_exec": {"status": "ok", "result_hash": "same"},
            }
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.assertEqual(load_failure_instances(path), [])


if __name__ == "__main__":
    unittest.main()
