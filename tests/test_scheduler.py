"""W4 gate: fixed_v1 backward compatibility (byte-equivalent intervals), a
deterministic opt-in adaptive_v2, timezone/DST-safe day math, burden caps
and replay determinism."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import learnprint_scheduler as sched  # noqa: E402
import learnprint as engine  # noqa: E402  (canonical evaluator for parity checks)


JKT = timezone(timedelta(hours=7))


def eligible_event(event_id, task_type, date, **rubric):
    return {
        "event_id": event_id,
        "task_type": task_type,
        "date": date,
        "evidence_origin": "observed_response",
        "synthetic": False,
        "help_level": "none",
        "rubric": rubric,
    }


def event_date(iso):
    return datetime.fromisoformat(iso)


class TestFixedV1Matrix(unittest.TestCase):
    def test_failed_latest_retries_after_one_day(self):
        self.assertEqual(sched.fixed_v1(0, True), 1)
        self.assertEqual(sched.fixed_v1(2, True), 1)

    def test_pass_ramp_matches_1_3_7_21(self):
        for passed, expected in [(0, 1), (1, 3), (2, 7), (3, 21), (4, 21), (9, 21)]:
            with self.subTest(passed=passed):
                self.assertEqual(sched.fixed_v1(passed), expected)

    def test_invalid_inputs_fail_closed(self):
        for args in [(-1, False), (True, False)]:
            with self.assertRaises(sched.SchedulerError):
                sched.fixed_v1(*args)
        with self.assertRaises(sched.SchedulerError):
            sched.fixed_v1(1, False, intervals=[0, 3])

    def test_naive_datetime_rejected(self):
        naive = datetime(2026, 1, 1, 12, 0)
        with self.assertRaises(sched.SchedulerError):
            sched.due_after(naive, 3)


class TestEvaluatorParity(unittest.TestCase):
    """fixed_v1 must reproduce the canonical evaluator's schedule exactly."""

    def evaluator_fixture(self, passed, failed_latest, base):
        app = eligible_event("a1", "independent_application", base.isoformat(), application=2, concept=2)
        transfer = eligible_event("t1", "novel_transfer", (base + timedelta(minutes=30)).isoformat(),
                                  transfer=2, application=2)
        events = [app, transfer]
        for i in range(passed):
            events.append(eligible_event(
                f"d{i}", "delayed_retrieval",
                (base + timedelta(days=2 + i, hours=2)).isoformat(),
                concept=2, application=2))
        if failed_latest:
            events.append(eligible_event(
                "dfail", "delayed_retrieval",
                (base + timedelta(days=2 + passed, hours=2)).isoformat(),
                concept=1, application=1))
        topic = {"topic_id": "t", "learning_scope": [{"id": "c1"}, {"id": "c2"}]}
        ledger = list(events) + [
            {"event_id": f"c{i}", "task_type": "confirmation", "date": events[-1]["date"],
             "competency_id": "c1"} for i in range(1)
        ]
        for e in events + ledger:
            e["competency_id"] = "c1"
        topic_events = events
        competency = {"id": "c1"}
        now = base + timedelta(days=90)
        status, detail = engine._evaluate_competency(competency, topic_events, ledger, now,
                                                     {"min_elapsed_hours": 20, "intervals_days": [1, 3, 7, 21]})
        return status, detail

    def parity_case(self, passed, failed_latest):
        base = datetime(2026, 1, 1, 9, 0, tzinfo=JKT)
        status, detail = self.evaluator_fixture(passed, failed_latest, base)
        expected_days = sched.fixed_v1(passed, failed_latest)
        self.assertEqual(detail["interval_days"], expected_days,
                         "scheduler must mirror the canonical interval rule")
        # the canonical eligible tail is the max-date independent event
        if failed_latest:
            # failed identical after the passing tail: it is the eligible tail
            last_eligible = base + timedelta(days=2 + passed, hours=2)
        elif passed == 0:
            last_eligible = base + timedelta(minutes=30)  # the novel transfer
        else:
            last_eligible = base + timedelta(days=2 + passed - 1, hours=2)
        expected_due = sched.due_after(last_eligible, expected_days)
        self.assertEqual(
            event_date(detail["fresh_due_at"]).replace(microsecond=0),
            expected_due.replace(microsecond=0),
            "scheduler due date must reproduce the canonical fresh_due_at",
        )
        # now is base+90d, past all fixture due dates
        self.assertEqual(status, "needs_review" if failed_latest else "retention_due")

    def test_parity_matrix(self):
        self.parity_case(0, False)
        self.parity_case(1, False)
        self.parity_case(2, False)
        self.parity_case(3, False)
        self.parity_case(1, True)

    def test_frontier_day_math_is_dst_safe(self):
        start = datetime(2026, 3, 8, 1, 30, tzinfo=timezone.utc)
        self.assertEqual(
            sched.due_after(start, 1).astimezone(timezone.utc),
            start + timedelta(days=1),
        )


class TestAdaptiveV2(unittest.TestCase):
    def base(self):
        return datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)

    def event(self, offset_days, concept, application):
        return (self.base() + timedelta(days=offset_days), {"concept": concept, "application": application})

    def test_deterministic_replay(self):
        events = [self.event(3, 2, 2), self.event(8, 2, 2)]
        first = sched.adaptive_v2(events)
        second = sched.adaptive_v2(events)
        self.assertEqual(first, second)

    def test_failing_recent_outcome_compresses(self):
        result = sched.adaptive_v2([self.event(3, 2, 2), self.event(9, 1, 0)])
        self.assertEqual(result["policy_version"], "adaptive_v2")
        self.assertEqual(result["multiplier"], 0.5)
        self.assertEqual(result["interval_days"], 1)

    def test_passes_ramp_with_cap(self):
        result = sched.adaptive_v2([
            self.event(3, 2, 2), self.event(7, 2, 2), self.event(30, 2, 2), self.event(34, 2, 2)
        ])
        self.assertGreater(result["multiplier"], 1.0)
        self.assertLessEqual(result["interval_days"], 42)

    def test_unscorable_history_keeps_fixed_cadence(self):
        result = sched.adaptive_v2([(self.base() + timedelta(days=1), {"concept": 2, "application": None})])
        self.assertEqual(result["multiplier"], 1.0)
        self.assertEqual(result["interval_days"], 1)

    def test_opt_out_returns_fixed(self):
        out = sched.schedule_from_policy(True, self.base(), 3, False)
        self.assertEqual(out["policy_version"], "fixed_v1")
        self.assertEqual(out["interval_days"], 21)

    def test_unknown_policy_rejected(self):
        with self.assertRaises(sched.SchedulerError):
            sched.schedule_from_policy(True, self.base(), 3, False, policy_version="turbo")


class TestBurdenGate(unittest.TestCase):
    def test_cap_and_deterministic_order(self):
        t0 = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        items = [(t0 + timedelta(days=d), f"k-{(name)}")
                 for d, name in [(0, "z"), (0, "a"), (0, "m"), (1, "later"), (-1, "past"), (0, "b")]]
        due = sched.select_due(items, t0 + timedelta(minutes=1), max_per_day=3)
        self.assertEqual([key for _, key in due], ["k-past", "k-a", "k-b"])
        capped = sched.select_due([(t0, f"k{i}") for i in range(20)], t0, max_per_day=4)
        self.assertEqual(len(capped), 4)

    def test_naive_input_rejected(self):
        with self.assertRaises(sched.SchedulerError):
            sched.select_due([(datetime(2026, 1, 1), "k")], datetime(2026, 1, 2))


if __name__ == "__main__":
    unittest.main()
