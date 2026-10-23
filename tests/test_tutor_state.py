"""W2 gate: table-driven transitions, idempotency, replay, crash persistence,
stale-write rejection, T01/T04 guards and schema compatibility for the tutor
FSM (scripts/learnprint_tutor.py)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import learnprint_tutor as tutor  # noqa: E402


def fresh_state(**kw):
    return tutor.initial_state(course_id=kw.pop("course_id", "C-1"), topic=kw.pop("topic", "t"))


def open_attempt(doc, event_id, task_id, author="tutor_model", fingerprint=None, **kw):
    return tutor.apply_transition(
        doc, "ATTEMPT", event_id, task_id=task_id, task_author=author,
        task_fingerprint=fingerprint, **kw
    )


class TestTransitionTable(unittest.TestCase):
    def test_terminal_phase_has_no_outgoing_transitions(self):
        self.assertEqual(tutor.ALLOWED_TRANSITIONS["COMPLETE"], set())

    def test_every_phase_present_in_table(self):
        for phase in tutor.PHASES:
            self.assertIn(phase, tutor.ALLOWED_TRANSITIONS)

    def test_full_reference_lifecycle_reaches_complete(self):
        doc = fresh_state()
        doc = tutor.apply_transition(doc, "EXPLAIN", "e1")
        doc = tutor.apply_transition(doc, "GUIDED", "e2")
        doc = open_attempt(doc, "e3", "t-1", author="course_material", fingerprint="fp-app")
        self.assertEqual(doc["phase"], "ATTEMPT")
        self.assertTrue(doc["current_task"]["answer_hidden"])
        doc = tutor.apply_transition(doc, "FEEDBACK", "e4")
        self.assertEqual(doc["phase"], "FEEDBACK")
        doc = tutor.apply_transition(doc, "TEACH_BACK", "e5")
        doc = tutor.apply_transition(
            doc, "TRANSFER", "e6", task_id="t-transfer-1",
            task_author="course_material", task_fingerprint="fp-transfer",
        )
        doc = tutor.apply_transition(doc, "FEEDBACK", "e7")
        doc = tutor.apply_transition(doc, "DELAYED_RETRIEVAL", "e8", external_ref="eval:review:1")
        self.assertEqual(doc["phase"], "DELAYED_RETRIEVAL")
        doc = tutor.apply_transition(doc, "FEEDBACK", "e9")
        doc = tutor.apply_transition(doc, "COMPLETE", "e10")
        self.assertEqual(doc["phase"], "COMPLETE")
        self.assertIsNone(doc["current_task"])
        self.assertEqual(doc["revision"], 11)

    def test_advanced_learner_compression_orient_to_attempt(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t-adv")
        self.assertEqual(doc["phase"], "ATTEMPT")

    def test_orient_to_guided_allowed(self):
        doc = fresh_state()
        doc = tutor.apply_transition(doc, "GUIDED", "e1")
        self.assertEqual(doc["phase"], "GUIDED")

    def test_guided_self_loop_allowed_for_faded_steps(self):
        doc = fresh_state()
        doc = tutor.apply_transition(doc, "GUIDED", "e1")
        again = tutor.apply_transition(doc, "GUIDED", "e2")
        self.assertEqual(again["revision"], doc["revision"] + 1)


class TestInvalidTransitions(unittest.TestCase):
    def test_every_unlisted_pair_rejected(self):
        for phase in tutor.PHASES:
            for target in tutor.PHASES:
                if target in tutor.ALLOWED_TRANSITIONS[phase]:
                    continue
                synthetic = fresh_state()
                synthetic["phase"] = phase
                synthetic["current_task"] = (
                    {
                        "task_id": "t0", "answer_hidden": True,
                        "help_level": "none", "authored_by": "tutor_model",
                    }
                    if phase == "ATTEMPT" else None
                )
                reason = "confusion" if (phase == "ATTEMPT" and target == "EXPLAIN") else None
                with self.subTest(phase=phase, target=target):
                    with self.assertRaises(tutor.TutorStateError):
                        tutor.apply_transition(
                            synthetic,
                            target,
                            f"evt-{phase}-{target}",
                            task_id=(("t1-{}-{}".format(phase, target)) if target == "ATTEMPT" else None),
                            task_author=("tutor_model" if target == "ATTEMPT" else None),
                            reason=reason,
                        )

    def test_unknown_target_phase_rejected(self):
        doc = fresh_state()
        with self.assertRaises(tutor.InvalidTransition):
            tutor.apply_transition(doc, "NAP", "e-x")

    def test_transit_after_complete_rejected(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t1")
        doc = tutor.apply_transition(doc, "FEEDBACK", "e2")
        doc = tutor.apply_transition(doc, "COMPLETE", "e3")
        with self.assertRaises(tutor.InvalidTransition):
            tutor.apply_transition(doc, "EXPLAIN", "e4")


class TestIndependenceAndTransferGuards(unittest.TestCase):
    """W3 gate: assist never becomes independent evidence; conservative transfer."""

    def build_assisted_then_transfer_ready(self, fp_original="fp-sql-select"):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t-app", author="course_material", fingerprint=fp_original)
        doc = tutor.apply_transition(doc, "FEEDBACK", "e2")
        self.assertEqual(doc["current_task"]["task_id"], "t-app")
        return doc

    def test_independence_classification(self):
        self.assertEqual(tutor.attempt_independence(None), "NO_TASK")
        task = {"task_id": "a", "answer_hidden": True, "help_level": "none", "authored_by": "course_material"}
        self.assertEqual(tutor.attempt_independence(task), "INDEPENDENT")
        hinted = dict(task, help_level="hint")
        self.assertEqual(tutor.attempt_independence(hinted), "ASSISTED")
        worked = dict(task, help_level="worked_example")
        self.assertEqual(tutor.attempt_independence(worked), "ASSISTED")
        solution = dict(task, help_level="solution")
        self.assertEqual(tutor.attempt_independence(solution), "ASSISTED")
        self.assertEqual(
            tutor.attempt_independence(task, not_scored={"reason": "confusion_exit"}),
            "NOT_SCORED",
        )

    def test_attempt_without_authorship_provenance_rejected(self):
        doc = fresh_state()
        with self.assertRaises(tutor.TutorStateError) as ctx:
            tutor.apply_transition(doc, "ATTEMPT", "e1", task_id="t1")
        self.assertIn("authored_by", str(ctx.exception))

    def test_transfer_requires_fresh_fingerprinted_task(self):
        doc = self.build_assisted_then_transfer_ready()
        with self.assertRaises(tutor.TutorStateError):
            tutor.apply_transition(doc, "TRANSFER", "e3")
        with self.assertRaises(tutor.InvalidTransition):
            tutor.apply_transition(
                doc, "TRANSFER", "e3", task_id="t-novel", task_author="course_material"
            )
        with self.assertRaises(tutor.InvalidTransition) as ctx:
            tutor.apply_transition(
                doc, "TRANSFER", "e3", task_id="t-novel",
                task_author="course_material", task_fingerprint="fp-sql-select",
            )
        self.assertIn("T05", str(ctx.exception))
        moved = tutor.apply_transition(
            doc, "TRANSFER", "e3", task_id="t-novel",
            task_author="course_material", task_fingerprint="fp-sql-aggregate",
        )
        self.assertEqual(moved["phase"], "TRANSFER")
        self.assertEqual(moved["current_task"]["task_id"], "t-novel")

    def test_transfer_contract_helper_rejects_ambiguity(self):
        source = {"task_id": "s", "task_fingerprint": "fp-x", "answer_hidden": True, "help_level": "none"}
        with self.assertRaises(tutor.TutorStateError):
            tutor.transfer_contract(None, {"task_id": "c", "task_fingerprint": "fp-c"})
        with self.assertRaises(tutor.TutorStateError):
            tutor.transfer_contract(source, {"task_id": "s", "task_fingerprint": "fp-c"})
        with self.assertRaises(tutor.InvalidTransition):
            tutor.transfer_contract(source, {"task_id": "c"})
        with self.assertRaises(tutor.InvalidTransition):
            tutor.transfer_contract(source, {"task_id": "c", "task_fingerprint": "FP-X"})
        tutor.transfer_contract(source, {"task_id": "c", "task_fingerprint": "fp-y"})

    def test_delayed_retrieval_requires_external_reference_and_never_scores(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t1")
        doc = tutor.apply_transition(doc, "FEEDBACK", "e2")
        with self.assertRaises(tutor.TutorStateError):
            tutor.apply_transition(doc, "DELAYED_RETRIEVAL", "e3")
        moved = tutor.apply_transition(
            doc, "DELAYED_RETRIEVAL", "e3", external_ref="review-2026-10-23-001"
        )
        self.assertEqual(moved["phase"], "DELAYED_RETRIEVAL")
        self.assertEqual(moved["events"][-1]["refs"]["external_ref"], "review-2026-10-23-001")
        for event in moved["events"]:
            self.assertIsNone(event["refs"].get("scored"), "tutor must never attach scores")

    def test_fresh_task_required_after_attempt_or_confusion(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t-original")
        doc = tutor.apply_transition(doc, "EXPLAIN", "e2", reason="confusion")
        with self.assertRaises(tutor.InvalidTransition) as ctx:
            open_attempt(doc, "e3", "t-original")
        self.assertIn("T04", str(ctx.exception))
        doc2 = open_attempt(doc, "e4", "t-fresh")
        self.assertEqual(doc2["current_task"]["task_id"], "t-fresh")
        self.assertIsNone(doc2["outcome_not_scored"])


class TestAttemptGuards(unittest.TestCase):
    def test_attempt_requires_task(self):
        doc = fresh_state()
        with self.assertRaises(tutor.TutorStateError):
            tutor.apply_transition(doc, "ATTEMPT", "e1", task_author="tutor_model")

    def test_attempt_with_exposed_answer_rejected(self):
        with self.assertRaises(tutor.TutorStateError):
            tutor._validate_task({"task_id": "t1", "answer_hidden": False})

    def test_confusion_exit_is_never_scored(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t-confuse")
        doc = tutor.apply_transition(doc, "EXPLAIN", "e2", reason="masih gak ngerti")
        self.assertEqual(doc["phase"], "EXPLAIN")
        self.assertEqual(doc["outcome_not_scored"]["reason"], "confusion_exit")
        self.assertEqual(doc["outcome_not_scored"]["task_id"], "t-confuse")
        scored = [e for e in doc["events"] if e["refs"].get("scored")]
        self.assertFalse(scored, "no scored event may exist for a confusion exit")

    def test_confusion_requires_reason(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t1")
        with self.assertRaises(tutor.InvalidTransition):
            tutor.apply_transition(doc, "EXPLAIN", "e2")

    def test_fresh_task_required_after_attempt_or_confusion(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t-original")
        doc = tutor.apply_transition(doc, "EXPLAIN", "e2", reason="confusion")
        with self.assertRaises(tutor.InvalidTransition) as ctx:
            open_attempt(doc, "e3", "t-original")
        self.assertIn("T04", str(ctx.exception))
        doc2 = open_attempt(doc, "e4", "t-fresh")
        self.assertEqual(doc2["current_task"]["task_id"], "t-fresh")
        self.assertIsNone(doc2["outcome_not_scored"])

    def test_help_level_recorded_on_attempt(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t1", help_level="hint")
        self.assertEqual(doc["current_task"]["help_level"], "hint")


class TestIdempotencyAndStaleWrites(unittest.TestCase):
    def test_identical_replay_is_noop(self):
        doc = fresh_state()
        moved = tutor.apply_transition(doc, "EXPLAIN", "e1")
        replayed = tutor.apply_transition(moved, "EXPLAIN", "e1")
        self.assertEqual(replayed, moved)
        self.assertEqual(replayed["revision"], moved["revision"])

    def test_conflicting_reuse_of_event_id_rejected(self):
        doc = fresh_state()
        doc = tutor.apply_transition(doc, "EXPLAIN", "e1")
        with self.assertRaises(tutor.DuplicateEventId):
            tutor.apply_transition(doc, "GUIDED", "e1")

    def test_stale_revision_rejected(self):
        doc = fresh_state()
        rev1 = doc["revision"]
        moved = tutor.apply_transition(doc, "EXPLAIN", "e1")
        with self.assertRaises(tutor.StaleRevision):
            tutor.apply_transition(
                moved, "ATTEMPT", "e1-fresh", task_id="t2", expect_rev=rev1
            )
        self.assertNotEqual(moved["revision"], rev1)


class TestPersistenceCrashAndReplay(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.file = Path(self.dir.name) / "session.json"

    def build_session(self):
        doc = fresh_state()
        doc = tutor.apply_transition(doc, "EXPLAIN", "e1")
        doc = open_attempt(doc, "e2", "t1")
        doc = tutor.apply_transition(doc, "FEEDBACK", "e3")
        return doc

    def test_roundtrip_load_matches(self):
        doc = self.build_session()
        tutor.atomic_write_session(self.file, doc)
        loaded = tutor.load_session(self.file)
        self.assertEqual(loaded, doc)

    def test_load_validates_schema_version(self):
        doc = self.build_session()
        doc["schema_version"] = 2
        with self.assertRaises(tutor.CorruptState):
            tutor.validate_state(doc)

    def test_crash_mid_write_keeps_previous_state(self):
        doc = self.build_session()
        tutor.atomic_write_session(self.file, doc)
        snapshot = self.file.read_text(encoding="utf-8")
        next_doc = tutor.apply_transition(doc, "TEACH_BACK", "e4")
        real_replace = os.replace
        with mock.patch("os.replace", side_effect=OSError("simulated crash")):
            with self.assertRaises(OSError):
                tutor.atomic_write_session(self.file, next_doc)
        self.assertEqual(self.file.read_text(encoding="utf-8"), snapshot)
        leftovers = [p.name for p in self.file.parent.iterdir() if p.name.endswith(".tmp")]
        self.assertFalse(leftovers, "crash must not leave temp litter")
        self.assertTrue(real_replace is os.replace)

    def test_resume_after_crash_agrees_with_replay(self):
        doc = self.build_session()
        tutor.atomic_write_session(self.file, doc)
        loaded = tutor.load_session(self.file)
        self.assertEqual(loaded["phase"], doc["phase"])
        derived = tutor.replay_events(loaded["events"])
        self.assertEqual(derived["phase"], loaded["phase"])

    def test_tampered_phase_detected_by_replay(self):
        doc = self.build_session()
        tutor.atomic_write_session(self.file, doc)
        tampered = json.loads(self.file.read_text(encoding="utf-8"))
        tampered["phase"] = "COMPLETE"
        self.file.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaises(tutor.CorruptState):
            tutor.load_session(self.file)

    def test_replay_rejects_unknown_event_type(self):
        doc = self.build_session()
        events = [dict(e) for e in doc["events"]]
        events.append({"rev": 99, "event_id": "bad", "type": "mystery", "to": "ORIENT", "ts": "x", "refs": {}})
        with self.assertRaises(tutor.CorruptState):
            tutor.replay_events(events)

    def test_cli_replay_reports_ok_exit_code(self):
        doc = self.build_session()
        tutor.atomic_write_session(self.file, doc)
        rc = tutor.main(["replay", "--file", str(self.file)])
        self.assertEqual(rc, 0)

    def test_cli_transit_roundtrip_end_to_end(self):
        tutor.main(["init", "--file", str(self.file), "--course-id", "C-1", "--topic", "t"])
        rc = tutor.main(["transit", "--file", str(self.file), "--to", "EXPLAIN", "--event-id", "e1"])
        self.assertEqual(rc, 0)
        rc = tutor.main([
            "transit", "--file", str(self.file), "--to", "ATTEMPT",
            "--event-id", "e2", "--task-id", "t1", "--task-author", "course_material",
            "--help-level", "hint",
        ])
        self.assertEqual(rc, 0)
        doc = tutor.load_session(self.file)
        self.assertEqual(doc["phase"], "ATTEMPT")
        self.assertEqual(doc["current_task"]["help_level"], "hint")
        rc = tutor.main([
            "transit", "--file", str(self.file), "--to", "FEEDBACK", "--event-id", "e3",
        ])
        self.assertEqual(rc, 0)
        doc = tutor.load_session(self.file)
        self.assertEqual(doc["phase"], "FEEDBACK")
        self.assertEqual(doc["events"][-1]["refs"]["task_id"], "t1")
        # assisted attempt must never be re-opened and transfers need novelty
        rc = tutor.main([
            "transit", "--file", str(self.file), "--to", "TRANSFER", "--event-id", "e4",
            "--task-id", "t1", "--task-author", "course_material",
            "--task-fingerprint", "not-needed",
        ])
        self.assertEqual(rc, 2, "reusing the attempted task id for transfer must fail")
        rc = tutor.main([
            "transit", "--file", str(self.file), "--to", "TRANSFER", "--event-id", "e4",
            "--task-id", "t-novel", "--task-author", "course_material",
            "--task-fingerprint", "fp-novel-1",
        ])
        self.assertEqual(rc, 0)
        doc = tutor.load_session(self.file)
        self.assertEqual(doc["phase"], "TRANSFER")

    def test_cli_delayed_requires_external_ref(self):
        tutor.main(["init", "--file", str(self.file), "--course-id", "C-1", "--topic", "t"])
        tutor.main(["transit", "--file", str(self.file), "--to", "EXPLAIN", "--event-id", "e1"])
        tutor.main([
            "transit", "--file", str(self.file), "--to", "ATTEMPT", "--event-id", "e2",
            "--task-id", "t1", "--task-author", "course_material",
        ])
        tutor.main(["transit", "--file", str(self.file), "--to", "FEEDBACK", "--event-id", "e3"])
        rc = tutor.main(["transit", "--file", str(self.file), "--to", "DELAYED_RETRIEVAL", "--event-id", "e4"])
        self.assertEqual(rc, 2, "delayed retrieval without an external reference is a fake event")
        rc = tutor.main([
            "transit", "--file", str(self.file), "--to", "DELAYED_RETRIEVAL", "--event-id", "e4",
            "--external-ref", "eval:events:e9",
        ])
        self.assertEqual(rc, 0)

    def test_cli_rejects_answer_shown_with_attempt(self):
        tutor.main(["init", "--file", str(self.file), "--course-id", "C-1", "--topic", "t"])
        rc = tutor.main([
            "transit", "--file", str(self.file), "--to", "ATTEMPT",
            "--event-id", "e1", "--task-id", "t1", "--answer-shown",
        ])
        self.assertEqual(rc, 2, "T01: answer shown before attempt must be rejected")
        doc = tutor.load_session(self.file)
        self.assertEqual(doc["phase"], "ORIENT", "sessions must persist untouched when a guard rejects")



class TestNextActionPresentation(unittest.TestCase):
    """W9 gate: one learner-visible action per phase, no internals dumped."""

    def test_every_phase_has_one_action(self):
        for phase in tutor.PHASES:
            with self.subTest(phase=phase):
                self.assertIn(phase, tutor.NEXT_ACTION_TEXT)
                self.assertTrue(tutor.NEXT_ACTION_TEXT[phase].strip())
                self.assertNotIn(chr(0x2014), tutor.NEXT_ACTION_TEXT[phase])

    def test_next_action_for_active_attempt(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t1")
        action = tutor.next_action(doc)
        self.assertEqual(action["phase"], "ATTEMPT")
        self.assertEqual(action["assistance_next_turn"], "none")
        self.assertEqual(action["allowed_next_phases"], ["EXPLAIN", "FEEDBACK"])

    def test_indonesian_next_action_for_orient_and_attempt(self):
        initial = fresh_state()
        before = json.loads(json.dumps(initial))
        orient = tutor.next_action(initial, language="id")
        self.assertEqual(orient["phase"], "ORIENT")
        self.assertIn("tujuan", orient["learner_action"].lower())
        self.assertEqual(initial, before, "presentation must not mutate session state")
        attempted = open_attempt(initial, "e1", "t1")
        action = tutor.next_action(attempted, language="id")
        self.assertEqual(action["phase"], "ATTEMPT")
        self.assertIn("sendiri", action["learner_action"].lower())
        self.assertEqual(action["assistance_next_turn"], "none")

    def test_all_phases_have_indonesian_actions(self):
        self.assertEqual(set(tutor.NEXT_ACTION_TEXT_ID), set(tutor.PHASES))
        for phase, message in tutor.NEXT_ACTION_TEXT_ID.items():
            with self.subTest(phase=phase):
                self.assertTrue(message.strip())
                self.assertNotIn("mastery", message.lower())
                self.assertNotIn("100%", message)

    def test_default_english_output_is_backward_compatible(self):
        doc = fresh_state()
        self.assertEqual(tutor.next_action(doc), tutor.next_action(doc, language="en"))
        self.assertEqual(tutor.next_action(doc)["learner_action"], tutor.NEXT_ACTION_TEXT["ORIENT"])

    def test_unsupported_language_rejected_without_state_mutation(self):
        doc = fresh_state()
        original = json.loads(json.dumps(doc))
        for language in ("es", "", "id-ID", None, 42, ["id"]):
            with self.subTest(language=language):
                with self.assertRaises(ValueError):
                    tutor.next_action(doc, language=language)
        self.assertEqual(doc, original)

    def test_complete_action_never_claims_mastery_score(self):
        doc = fresh_state()
        doc = open_attempt(doc, "e1", "t1")
        doc = tutor.apply_transition(doc, "FEEDBACK", "e2")
        doc = tutor.apply_transition(doc, "COMPLETE", "e3")
        action = tutor.next_action(doc)
        self.assertNotIn("score", action["learner_action"].lower())
        self.assertNotIn("passed", action["learner_action"].lower())


class TestTutorSessionSchemaFile(unittest.TestCase):
    def test_schema_file_declares_versioned_contract(self):
        schema = json.loads((ROOT / "schemas" / "tutor-session.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], tutor.SCHEMA_VERSION)
        expected_phases = set(tutor.PHASES)
        self.assertEqual(set(schema["properties"]["phase"]["enum"]), expected_phases)
        self.assertEqual(set(schema["properties"]["events"]["items"]["properties"]["to"]["enum"]), expected_phases)


if __name__ == "__main__":
    unittest.main()
