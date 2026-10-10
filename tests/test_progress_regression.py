import datetime as _dt
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("learnprint", ROOT / "scripts/learnprint.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

T0 = "2026-10-10T01:00:00+07:00"


def topic():
    return {"schema_version": "1.0", "topic_id": "t", "goal": "g",
            "learning_scope": [{"id": "c1", "name": "C1", "status": "unknown",
                                "evidence_ids": [], "due_at": None}],
            "syllabus": [], "question_parking_lot": [], "sources": [], "last_session": None}


def ev(eid, kind, date, rubric=None, **kw):
    e = {"event_id": eid, "date": date, "topic_id": "t", "competency_id": "c1",
         "task_type": kind, "observed_answer": "a", "expected_reasoning": "r",
         "feedback": "f", "help_level": "none",
         "rubric": rubric or {"concept": 2, "mechanism": 2, "application": 2, "transfer": 2},
         "grader": "ai_reviewed", "evidence_origin": "observed_response",
         "course_id": "550e8400-e29b-41d4-a716-446655440000", "grader_source": "agent"}
    e.update(kw)
    return e


def app(eid, date, ok=True):
    return ev(eid, "independent_application", date,
              {"concept": 2, "mechanism": 2, "application": 2 if ok else 0, "transfer": 2})


def tra(eid, date, ok=True):
    return ev(eid, "novel_transfer", date,
              {"concept": 2, "mechanism": 2, "application": 2, "transfer": 2 if ok else 0})


def dla(eid, date, ok=True):
    v = 2 if ok else 0
    return ev(eid, "delayed_retrieval", date,
              {"concept": v, "mechanism": 2, "application": v, "transfer": 2})


def H(n):
    """n hours after T0, formatted with +07:00."""
    return (_dt.datetime.fromisoformat(T0) + _dt.timedelta(hours=n)).isoformat()


def status_of(events, now=None):
    t = topic()
    if now is None:
        if not events:
            now = _dt.datetime.now(_dt.timezone.utc)
        else:
            last = max(mod._parse_dt(e["date"]) for e in events)
            now = last + _dt.timedelta(hours=1)
    return mod.progress(t, events, now=now)["competencies"][0]


class TestProgressRegression(unittest.TestCase):
    def test_p1a_original_bug(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26)), dla("d2", H(100), ok=False)]
        self.assertEqual(status_of(e)["status"], "needs_review")

    def test_latest_delayed_pass(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26))]
        self.assertEqual(status_of(e)["status"], "maintained")

    def test_interleaved_delayed(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26)),
             dla("d2", H(50), ok=False), dla("d3", H(100))]
        self.assertEqual(status_of(e)["status"], "maintained")

    def test_app_regression(self):
        e = [app("a", H(0)), tra("t", H(1)), app("a2", H(30), ok=False)]
        self.assertEqual(status_of(e)["status"], "emerging")

    def test_transfer_regression(self):
        e = [app("a", H(0)), tra("t", H(1)), tra("t2", H(30), ok=False)]
        self.assertEqual(status_of(e)["status"], "emerging")

    def test_remediation_clears_old_delayed_fail(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26), ok=False),
             app("a2", H(100)), tra("t2", H(101))]
        self.assertEqual(status_of(e)["status"], "demonstrated")

    def test_remediation_then_new_delayed_pass(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26), ok=False),
             app("a2", H(100)), tra("t2", H(101)), dla("d2", H(130))]
        self.assertEqual(status_of(e)["status"], "maintained")

    def test_delayed_pass_no_new_cycle(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26), ok=False), dla("d2", H(50))]
        self.assertEqual(status_of(e)["status"], "maintained")

    def test_delayed_before_cycle_ignored(self):
        e = [dla("d0", H(-100)), app("a", H(0)), tra("t", H(1))]
        self.assertEqual(status_of(e)["status"], "demonstrated")

    def test_delayed_too_soon(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(2))]
        self.assertEqual(status_of(e)["status"], "demonstrated")

    def test_retention_due_stale(self):
        e = [app("a", H(0)), tra("t", H(1))]
        now = mod._parse_dt(H(0)) + _dt.timedelta(days=5)
        self.assertEqual(status_of(e, now)["status"], "retention_due")

    def test_retention_due_then_delayed_fail(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(100), ok=False)]
        self.assertEqual(status_of(e)["status"], "needs_review")

    def test_retention_due_then_delayed_pass(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(100))]
        self.assertEqual(status_of(e)["status"], "maintained")

    def test_assisted_attempt_ignored(self):
        e = [app("a", H(0)), tra("t", H(1))]
        for x in e:
            x["help_level"] = "hint"
        self.assertEqual(status_of(e)["status"], "emerging")

    def test_ai_graded_drives_provisional(self):
        e = [app("a", H(0)), tra("t", H(1))]
        r = status_of(e)
        self.assertEqual(r["status"], "demonstrated")
        self.assertEqual(r["basis"], "provisional")

    def test_verified_by_string_confers_nothing(self):
        e = [app("a", H(0)), tra("t", H(1))]
        for x in e:
            x["grader"] = "human_reviewed"
            x["verified_by"] = "prof-x"
        r = status_of(e)
        self.assertEqual((r["status"], r["basis"]), ("demonstrated", "provisional"))

    def test_learner_confirm_establishes_basis(self):
        e = [app("a", H(0)), tra("t", H(1)),
             ev("c9", "confirmation", H(2), confirms_event_id="a")]
        r = status_of(e)
        self.assertEqual((r["status"], r["basis"]), ("demonstrated", "learner_confirmed"))

    def test_correction_supersedes_original(self):
        e = [app("a", H(0)),
             ev("k1", "correction", H(2), corrects_event_id="a",
                rubric={"concept": 0, "mechanism": 0, "application": 0, "transfer": 0})]
        # app superseded to failing, transfer missing entirely
        self.assertEqual(status_of(e)["status"], "emerging")

    def test_two_source_substantiation(self):
        e = [app("a", H(0)), tra("t", H(1)),
             ev("x1", "delayed_retrieval", H(26), grader_source="third_party",
                corroborates_event_id="a")]
        self.assertEqual(status_of(e)["basis"], "substantiated")

    def test_unlinked_cross_course_not_substantiated(self):
        e = [app("a", H(0)), tra("t", H(1)),
             ev("x9", "delayed_retrieval", H(26),
                course_id="123e4567-e89b-42d3-a456-426614174000",
                grader_source="third_party")]
        self.assertEqual(status_of(e)["basis"], "provisional")

    def test_basis_reported_per_competency(self):
        t = topic()
        t["learning_scope"].append({"id": "c2", "name": "C2", "status": "unknown",
                                   "evidence_ids": [], "due_at": None})
        e = [app("a", H(0)), tra("t", H(1)),
             ev("c9", "confirmation", H(2), confirms_event_id="a")]
        r = mod.progress(t, e, now=mod._parse_dt(H(3)))
        by_id = {c["id"]: c for c in r["competencies"]}
        self.assertEqual(by_id["c1"]["basis"], "learner_confirmed")
        self.assertEqual(by_id["c2"]["status"], "unknown")
        self.assertIn("learner_confirmed", r["coverage_basis"])

    def test_tiebreak_deterministic(self):
        e = [app("a", H(0)), tra("t", H(0))]
        r1 = status_of(e)
        e2 = list(reversed(e))
        r2 = status_of(e2)
        self.assertEqual((r1["status"], r2["status"]), ("demonstrated", "demonstrated"))

    def test_cross_timezone_ordering(self):
        # Same UTC day, different offsets: +07:00 10:00 is EARLIER than +00:00 04:00.
        e = [app("a", "2026-10-10T10:00:00+07:00"),
             tra("t", "2026-10-10T04:00:00+00:00")]
        # transfer (03:00Z) is BEFORE app (04:00Z... wait 10:00+07 = 03:00Z; 04:00+00 = 04:00Z)
        # transfer at 04:00Z >= app at 03:00Z -> demonstrated
        r = status_of(e)
        self.assertEqual(r["status"], "demonstrated")
        e2 = [app("a", "2026-10-10T10:00:00+07:00"),
              tra("t", "2026-10-10T02:00:00+00:00")]
        # transfer 02:00Z < app 03:00Z -> emerging (string sort would wrongly pass)
        self.assertEqual(status_of(e2)["status"], "emerging")

    def test_progress_reviews_agree_on_latest(self):
        t = topic()
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26))]
        now = mod._parse_dt(H(27))
        s = mod.progress(t, e, now=now)["competencies"][0]["status"]
        rev = mod.reviews_from_events([t], e)
        self.assertEqual(s, "maintained")
        self.assertEqual(len(rev["reviews"]), 1)
        self.assertEqual(rev["reviews"][0]["interval_days"], 3)

    def test_empty_events(self):
        self.assertEqual(status_of([])["status"], "unknown")

    def test_transfer_before_app(self):
        e = [tra("t", H(0)), app("a", H(5))]
        self.assertEqual(status_of(e)["status"], "emerging")

    def test_simultaneous_app_transfer(self):
        e = [app("a", H(0)), tra("t", H(0))]
        self.assertEqual(status_of(e)["status"], "demonstrated")

    def test_retention_threshold_configurable(self):
        policy = {"min_elapsed_hours": 48, "intervals_days": [1, 3, 7, 21]}
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26))]
        t = topic()
        r = mod.progress(t, e, now=mod._parse_dt(H(27)), policy=policy)
        self.assertEqual(r["competencies"][0]["status"], "demonstrated")
        r2 = mod.progress(t, e, now=mod._parse_dt(H(27)))
        self.assertEqual(r2["competencies"][0]["status"], "maintained")

    def test_min_elapsed_boundary(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(21))]
        # cycle start = H(1); elapsed exactly 20h -> inclusive -> maintained
        self.assertEqual(status_of(e)["status"], "maintained")

    def test_immediate_retest_not_maintained(self):
        e = [app("a", H(0)), tra("t", H(1)),
             dla("d1", (_dt.datetime.fromisoformat(H(1)) + _dt.timedelta(minutes=30)).isoformat())]
        self.assertEqual(status_of(e)["status"], "demonstrated")

    def test_fresh_delayed_pass_clears_retention_due(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(100))]
        r = status_of(e)
        self.assertEqual(r["status"], "maintained")
        self.assertTrue(mod._parse_dt(r["due_at"]) > mod._parse_dt(H(100)))

    def test_stale_stored_due_ignored_by_evaluator(self):
        t = topic()
        t["learning_scope"][0]["due_at"] = "2026-09-11T00:00:00+00:00"  # 30 days stale
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26))]
        r = mod.progress(t, e, now=mod._parse_dt(H(27)))["competencies"][0]
        self.assertEqual(r["status"], "maintained")

    def test_precycle_failure_does_not_dominate_new_cycle(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26), ok=False),
             app("a2", H(200)), tra("t2", H(201))]
        self.assertEqual(status_of(e)["status"], "demonstrated")

    def test_due_date_from_current_cycle(self):
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26), ok=False),
             app("a2", H(200)), tra("t2", H(201))]
        rev = mod.reviews_from_events([topic()], e)["reviews"][0]
        cycle2 = mod._parse_dt(H(201))
        self.assertTrue(mod._parse_dt(rev["due_at"]) > cycle2)
        self.assertTrue(mod._parse_dt(rev["cycle_start"]) >= cycle2)

    def test_shared_event_snapshot(self):
        t = topic()
        e = [app("a", H(0)), tra("t", H(1)), dla("d1", H(26))]
        now = mod._parse_dt(H(27))
        s = mod.progress(t, e, now=now)["competencies"][0]
        rev = mod.reviews_from_events([t], e)[ "reviews"][0]
        self.assertEqual(s["status"], "maintained")
        self.assertEqual(rev["due_at"], s["due_at"])

    def test_single_evaluator_no_drift(self):
        import inspect
        src = inspect.getsource(mod.reviews_from_events)
        self.assertIn("_evaluate_competency", src)
        self.assertNotIn("for x in reversed(", src)
        self.assertNotIn("passed_delayed", src)

    def test_stale_review_queue_superseded(self):
        t = topic()
        # Old cycle (H0/H1) produced a stored entry; remediation opened cycle 2.
        e = [app("a", H(0)), tra("t", H(1)),
             app("a2", H(200)), tra("t2", H(201)), dla("d2", H(230))]
        stored = {"schema_version": "1.0", "reviews": [
            {"competency_id": "c1", "due_at": H(30),
             "cycle_start": H(1), "interval_days": 1}]}
        rev = mod.reviews_from_events([t], e, stored_reviews=stored)
        self.assertEqual(len(rev["reviews"]), 1)
        self.assertNotEqual(rev["reviews"][0]["cycle_start"], H(1))
        now = mod._parse_dt(H(231))
        self.assertEqual(mod.progress(t, e, now=now)["competencies"][0]["status"],
                         "maintained")

    def test_existing_16_tests_pass(self):
        loader = unittest.TestLoader()
        try:
            suite = loader.loadTestsFromName("tests.test_core")
        except ImportError:
            suite = loader.loadTestsFromName("test_core")
        result = unittest.TextTestRunner(verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful())


if __name__ == "__main__":
    unittest.main()
