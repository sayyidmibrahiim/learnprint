"""Integration of canonical private course and durable tutor FSM phases."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = str(ROOT / "scripts/learnprint.py")


def cli(*args):
    return subprocess.run([sys.executable, CLI, *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=45)


class TestCourseTutorPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "Courses"
        init = cli("course", "init", "--courses-root", self.root, "--approve")
        self.assertEqual(init.returncode, 0, init.stderr)
        created = cli("course", "create", "--courses-root", self.root,
                      "--category", "technology", "--title", "SQL",
                      "--goal", "query", "--approve")
        self.assertEqual(created.returncode, 0, created.stderr)
        self.entry = json.loads(created.stdout)
        self.cid = self.entry["course_id"]
        self.file = self.root / self.entry["rel_path"] / "tutor-session.json"
        self.ledger = self.root / ".learnprint" / "events.jsonl"

    def test_init_transition_replay_card_and_idempotence(self):
        before_ledger = self.ledger.read_bytes()
        denied = cli("course", "tutor-init", "--courses-root", self.root,
                     "--course-id", self.cid)
        self.assertNotEqual(denied.returncode, 0)
        self.assertFalse(self.file.exists())
        ok = cli("course", "tutor-init", "--courses-root", self.root,
                 "--course-id", self.cid, "--approve")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["phase"], "ORIENT")
        repeat_init = cli("course", "tutor-init", "--courses-root", self.root,
                          "--course-id", self.cid, "--approve")
        self.assertNotEqual(repeat_init.returncode, 0)
        status = cli("course", "tutor-status", "--courses-root", self.root,
                     "--course-id", self.cid)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["phase"], "ORIENT")
        transition = ["course", "tutor-transit", "--courses-root", self.root,
                      "--course-id", self.cid, "--to", "EXPLAIN",
                      "--event-id", "teaching-start-01", "--approve"]
        done = cli(*transition)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["phase"], "EXPLAIN")
        same = cli(*transition)
        self.assertEqual(same.returncode, 0, same.stderr)
        self.assertEqual(json.loads(same.stdout)["revision"],
                         json.loads(done.stdout)["revision"])
        card = cli("course", "journey-card", "--courses-root", self.root,
                   "--course-id", self.cid)
        self.assertEqual(card.returncode, 0, card.stderr)
        self.assertIn("BELAJAR", card.stdout)
        self.assertIn("FSM tersimpan", card.stdout)
        self.assertEqual(self.ledger.read_bytes(), before_ledger)

    def test_refuse_invalid_stale_and_non_authorized_transitions(self):
        init = cli("course", "tutor-init", "--courses-root", self.root,
                   "--course-id", self.cid, "--approve")
        self.assertEqual(init.returncode, 0, init.stderr)
        denied = cli("course", "tutor-transit", "--courses-root", self.root,
                     "--course-id", self.cid, "--to", "EXPLAIN",
                     "--event-id", "x")
        self.assertNotEqual(denied.returncode, 0)
        stale = cli("course", "tutor-transit", "--courses-root", self.root,
                    "--course-id", self.cid, "--to", "EXPLAIN",
                    "--event-id", "x", "--expect-rev", "99", "--approve")
        self.assertNotEqual(stale.returncode, 0)
        bad = cli("course", "tutor-transit", "--courses-root", self.root,
                  "--course-id", self.cid, "--to", "TRANSFER",
                  "--event-id", "bad", "--approve")
        self.assertNotEqual(bad.returncode, 0)
        intact = cli("course", "tutor-status", "--courses-root", self.root,
                     "--course-id", self.cid)
        self.assertEqual(json.loads(intact.stdout)["phase"], "ORIENT")
        self.assertEqual(self.ledger.read_text(encoding="utf-8"), "")

    def test_evidence_requires_corresponding_private_tutor_task(self):
        """Cannot call an ORIENT or unrelated task a new independent attempt."""
        initialized = cli("course", "tutor-init", "--courses-root", self.root,
                          "--course-id", self.cid, "--approve")
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        payload = {
            "event_id": "independent-attempt-01", "topic": self.cid,
            "course_id": self.cid, "competency": "sample-comp",
            "task_type": "independent_application",
            "answer": "A novel independently written explanation.",
            "rubric": {"application": 2},
            "expected": "Explain mechanism", "feedback": "Provisional AI feedback",
            "grader": "ai_reviewed", "help_level": "none",
            "grader_source": "agent", "task_id": "task-01",
        }
        input_file = Path(self.tmp.name) / "real-answer.json"
        input_file.write_text(json.dumps(payload), encoding="utf-8")
        cmd = ["record", "--workspace", self.root, "--from-file",
               input_file, "--approve"]
        orient = cli(*cmd)
        self.assertNotEqual(orient.returncode, 0)
        self.assertIn("matching live tutor phase", orient.stderr)
        self.assertEqual(self.ledger.read_text(encoding="utf-8"), "")

        opened = cli("course", "tutor-transit", "--courses-root", self.root,
                     "--course-id", self.cid, "--to", "ATTEMPT",
                     "--event-id", "prompt-01", "--task-id", "task-01",
                     "--task-author", "tutor_model", "--approve")
        self.assertEqual(opened.returncode, 0, opened.stderr)
        payload["task_id"] = "another-task"
        input_file.write_text(json.dumps(payload), encoding="utf-8")
        wrong = cli(*cmd)
        self.assertNotEqual(wrong.returncode, 0)
        self.assertIn("matching --task-id", wrong.stderr)

        payload["task_id"] = "task-01"
        input_file.write_text(json.dumps(payload), encoding="utf-8")
        actual = cli(*cmd)
        self.assertEqual(actual.returncode, 0, actual.stderr)
        event = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(event["tutor_task_id"], "task-01")
        self.assertEqual(event["tutor_session_id"],
                         json.loads(initialized.stdout)["session_id"])

    def test_assisted_tutor_task_cannot_be_relabelled_independent(self):
        initialized = cli("course", "tutor-init", "--courses-root", self.root,
                          "--course-id", self.cid, "--approve")
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        opened = cli("course", "tutor-transit", "--courses-root", self.root,
                     "--course-id", self.cid, "--to", "ATTEMPT",
                     "--event-id", "hint-prompt", "--task-id", "assisted-task",
                     "--task-author", "tutor_model", "--help-level", "hint",
                     "--approve")
        self.assertEqual(opened.returncode, 0, opened.stderr)
        payload = {
            "event_id": "assisted-attempt-01", "topic": self.cid,
            "course_id": self.cid, "competency": "sample-comp",
            "task_type": "independent_application",
            "answer": "This answer required a hint.",
            "rubric": {"application": 2},
            "expected": "Explain mechanism", "feedback": "Hint-assisted",
            "grader": "ai_reviewed", "help_level": "none",
            "task_id": "assisted-task",
        }
        input_file = Path(self.tmp.name) / "assisted-answer.json"
        input_file.write_text(json.dumps(payload), encoding="utf-8")
        cmd = ["record", "--workspace", self.root, "--from-file",
               input_file, "--approve"]
        wrong = cli(*cmd)
        self.assertNotEqual(wrong.returncode, 0)
        self.assertIn("help_level conflicts", wrong.stderr)
        payload["help_level"] = "hint"
        input_file.write_text(json.dumps(payload), encoding="utf-8")
        corrected = cli(*cmd)
        self.assertEqual(corrected.returncode, 0, corrected.stderr)
        event = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(event["help_level"], "hint")

    def test_absent_phase_works_as_unverified(self):
        card = cli("course", "journey-card", "--courses-root", self.root,
                   "--course-id", self.cid)
        self.assertEqual(card.returncode, 0, card.stderr)
        self.assertIn("belum tercatat secara pasti", card.stdout)
        self.assertFalse(self.file.exists())


if __name__ == "__main__":
    unittest.main()
