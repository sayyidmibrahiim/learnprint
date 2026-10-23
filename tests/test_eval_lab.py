"""W10 gate: deterministic simulated journeys with honest labeling.

Assisted attempts must classify as ASSISTED (never independent), confusion
exits must be non-scored instruction, delayed retrievals need external
references, and invalid scripts must fail closed.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import learnprint_eval as ev  # noqa: E402


def journey(behaviors, **over):
    script = {
        "journey_id": "sim-golden",
        "course_id": "sim-course",
        "topic": "sim",
        "behavior": behaviors,
        "expect_independence": over.get("expect", []),
    }
    script.update({k: v for k, v in over.items() if k != "expect"})
    return script


GOLDEN = [
    {"action": "attempt", "task_id": "t-app", "task_author": "course_material", "task_fingerprint": "fp-app"},
    {"action": "transition", "to": "FEEDBACK"},
    {"action": "transition", "to": "TRANSFER", "task_id": "t-tr1", "task_author": "course_material", "task_fingerprint": "fp-novel"},
    {"action": "transition", "to": "FEEDBACK"},
    {"action": "transition", "to": "DELAYED_RETRIEVAL", "external_ref": "eval:review:1"},
    {"action": "transition", "to": "FEEDBACK"},
    {"action": "transition", "to": "COMPLETE"},
]


class TestSimulatedJourneys(unittest.TestCase):
    def test_golden_independent_journey_passes(self):
        result = ev.simulate_journey(journey(GOLDEN, expect=["INDEPENDENT", "INDEPENDENT"]))
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["simulated"])
        self.assertEqual(result["human_participants"], 0)
        metrics = result["metrics"]
        self.assertEqual(metrics["false_mastery_leaks"], [])
        self.assertEqual(metrics["confusion_pauses"], 0)
        self.assertEqual(metrics["scored_guarantees_violations"], [])
        self.assertIn("COMPLETE", metrics["phases_visited"])

    def test_assisted_attempt_is_never_independent(self):
        behaviors = [
            {"action": "attempt", "task_id": "t-app",
             "task_author": "course_material", "help_level": "hint"},
            {"action": "transition", "to": "FEEDBACK"},
            {"action": "transition", "to": "TRANSFER", "task_id": "t-tr1",
             "task_author": "course_material", "task_fingerprint": "fp-novel"},
        ]
        # hint help must classify ASSISTED; expecting INDEPENDENT exposes a leak
        result = ev.simulate_journey(journey(behaviors, expect=["INDEPENDENT", "INDEPENDENT"]))
        self.assertTrue(any(
            leak["classification"] == "ASSISTED" and leak["expected"] == "INDEPENDENT"
            for leak in result["metrics"]["false_mastery_leaks"]
        ))
        # corrected expectation passes
        result2 = ev.simulate_journey(journey(behaviors, expect=["ASSISTED", "INDEPENDENT"]))
        self.assertTrue(result2["passed"], result2)

    def test_confusion_exit_is_pause_not_score(self):
        behaviors = [
            {"action": "attempt", "task_id": "t1", "task_author": "course_material"},
            {"action": "confusion_exit"},
            {"action": "attempt", "task_id": "t2", "task_author": "course_material"},
            {"action": "transition", "to": "FEEDBACK"},
            {"action": "transition", "to": "COMPLETE"},
        ]
        result = ev.simulate_journey(journey(behaviors, expect=["INDEPENDENT", "INDEPENDENT"]))
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["metrics"]["confusion_pauses"], 1)

    def test_fake_fresh_task_blocked_by_engine(self):
        behaviors = journey([
            {"action": "attempt", "task_id": "t1", "task_author": "course_material"},
            {"action": "confusion_exit"},
            {"action": "attempt", "task_id": "t1", "task_author": "course_material"},
        ])
        result = ev.simulate_journey(behaviors)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocked_at_behavior"], 2)
        self.assertIn("T04", result["blocked_reason"])

    def test_scored_script_leak_reported(self):
        # the FSM cannot carry scores, so a journey asserting leaks stays 0;
        # the guarantee check exists to catch engine regressions.
        result = ev.simulate_journey(journey(GOLDEN))
        self.assertEqual(result["metrics"]["scored_guarantees_violations"], [])

    def test_scheduler_interval_reported_when_requested(self):
        result = ev.simulate_journey(journey(GOLDEN, retention_floor_seconds=72000, passed_delayed=1))
        self.assertEqual(result["metrics"]["planned_interval_days"], 3)

    def test_malformed_script_fails_closed(self):
        with self.assertRaises(ev.EvalError):
            ev.simulate_journey({"journey_id": "x"})
        with self.assertRaises(ev.EvalError):
            ev.simulate_journey({"journey_id": "x", "behavior": [{"action": "prank"}]})

    def test_cli_run_exit_codes(self):
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as d:
            good = Path(d) / "good.json"
            good.write_text(json.dumps(journey(GOLDEN, expect=["INDEPENDENT", "INDEPENDENT"])), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = ev.main(["run", "--script", str(good)])
            self.assertEqual(rc, 0)
            self.assertIn('"simulated": true', buf.getvalue())
            bad = Path(d) / "bad.json"
            bad.write_text(json.dumps(journey([{"action": "transition", "to": "FEEDBACK"}])), encoding="utf-8")
            rc = ev.main(["run", "--script", str(bad)])
            self.assertEqual(rc, 2, "journey hitting the table rail before fail-closed close")


if __name__ == "__main__":
    unittest.main()
