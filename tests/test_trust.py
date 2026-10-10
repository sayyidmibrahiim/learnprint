import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("learnprint", ROOT / "scripts/learnprint.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def base_event(**kw):
    e = {"event_id": "e1", "date": "2026-10-10T01:00:00+07:00", "topic_id": "t",
         "competency_id": "c1", "task_type": "independent_application",
         "observed_answer": "answer", "expected_reasoning": "reason",
         "feedback": "fb", "help_level": "none",
         "rubric": {"concept": 2, "mechanism": 2, "application": 2, "transfer": 2},
         "grader": "ai_reviewed", "evidence_origin": "observed_response",
         "course_id": "550e8400-e29b-41d4-a716-446655440000",
         "grader_source": "agent"}
    e.update(kw)
    return e


class TestTrustValidator(unittest.TestCase):
    def test_confirmation_and_correction_task_types_accepted(self):
        e = base_event(task_type="confirmation", confirms_event_id="e0")
        self.assertEqual(mod.validate_event(e), [])
        e = base_event(task_type="correction", corrects_event_id="e0",
                       rubric={"concept": 0, "mechanism": 0, "application": 0, "transfer": 0})
        self.assertEqual(mod.validate_event(e), [])

    def test_confirmation_requires_linkage(self):
        e = base_event(task_type="confirmation")
        self.assertTrue(any("confirms_event_id" in x for x in mod.validate_event(e)))

    def test_correction_requires_linkage(self):
        e = base_event(task_type="correction")
        self.assertTrue(any("corrects_event_id" in x for x in mod.validate_event(e)))

    def test_bad_grader_source_rejected(self):
        e = base_event(grader_source="professor")
        self.assertTrue(any("grader_source" in x for x in mod.validate_event(e)))

    def test_bad_course_id_rejected(self):
        e = base_event(course_id="languages-english--in-on-at")
        self.assertTrue(any("course_id" in x for x in mod.validate_event(e)))

    def test_legacy_event_without_new_fields_still_valid(self):
        e = base_event()
        del e["course_id"]
        del e["grader_source"]
        self.assertEqual(mod.validate_event(e), [])

    def test_verified_by_string_confers_nothing(self):
        # verified_by is informational only; basis derives from linkage.
        cycle = [base_event(event_id="a1", grader="human_reviewed", verified_by="prof-x"),
                 base_event(event_id="t1", task_type="novel_transfer",
                            grader="human_reviewed", verified_by="prof-x")]
        self.assertEqual(mod.evidence_basis(cycle, cycle), "provisional")

    def test_learner_confirm_establishes_basis(self):
        cycle = [base_event(event_id="a1"), base_event(event_id="t1", task_type="novel_transfer")]
        confirm = base_event(event_id="c9", task_type="confirmation",
                             confirms_event_id="a1", grader_source="learner")
        self.assertEqual(mod.evidence_basis(cycle, cycle + [confirm]), "learner_confirmed")

    def test_two_source_substantiation(self):
        cycle = [base_event(event_id="a1"), base_event(event_id="t1", task_type="novel_transfer")]
        second = base_event(event_id="x1", task_type="delayed_retrieval",
                            grader_source="third_party", corroborates_event_id="a1")
        self.assertEqual(mod.evidence_basis(cycle, cycle + [second]), "substantiated")

    def test_unlinked_cross_course_not_substantiated(self):
        cycle = [base_event(event_id="a1"), base_event(event_id="t1", task_type="novel_transfer")]
        rogue = base_event(event_id="x9", task_type="delayed_retrieval",
                           course_id="123e4567-e89b-42d3-a456-426614174000",
                           grader_source="third_party")
        self.assertEqual(mod.evidence_basis(cycle, cycle + [rogue]), "provisional")

    def test_self_report_never_state_establishing(self):
        e = base_event(evidence_origin="self_report")
        self.assertEqual(mod.validate_event(e), [])  # valid record...
        self.assertFalse(mod.is_observed_unassisted(e))  # ...but never demonstration evidence

    def test_dangling_confirmation_raises(self):
        t = {"schema_version": "1.0", "topic_id": "t", "goal": "g",
             "learning_scope": [{"id": "c1", "name": "C1", "status": "unknown",
                                 "evidence_ids": [], "due_at": None}],
             "syllabus": [], "question_parking_lot": [], "sources": [], "last_session": None}
        e = [base_event(task_type="confirmation", confirms_event_id="ghost")]
        with self.assertRaises(mod.LedgerReferenceError):
            mod.progress(t, e)

    def test_sources_entry_requires_status(self):
        p = mod.load(ROOT / "templates/topic-state.json")
        p["sources"] = [{"claim": "water boils at 90C"}]
        self.assertTrue(any("status" in x for x in mod.validate_topic(p)))

    def test_invalid_source_status_rejected(self):
        p = mod.load(ROOT / "templates/topic-state.json")
        p["sources"] = [{"claim": "x", "status": "probably fine"}]
        self.assertTrue(any("status" in x for x in mod.validate_topic(p)))

    def test_valid_source_statuses_accepted(self):
        p = mod.load(ROOT / "templates/topic-state.json")
        p["sources"] = [{"claim": "TCP backoff", "status": "verified", "source": "RFC 6298"},
                        {"claim": "recall", "status": "UNVERIFIED"},
                        {"claim": "said", "status": "learner-reported"},
                        {"claim": "graded", "status": "agent-generated"},
                        {"claim": "?", "status": "unknown"}]
        self.assertEqual(mod.validate_topic(p), [])


if __name__ == "__main__":
    unittest.main()
