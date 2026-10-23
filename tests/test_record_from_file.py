"""Windows-safe JSON event input regression tests using disposable Courses only."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = str(REPO / "scripts" / "learnprint.py")
CID = "record-fixture-not-a-real-uuid"


def call(*args):
    return subprocess.run([sys.executable, CLI, *map(str, args)],
                          cwd=REPO, capture_output=True, text=True, timeout=35)


class TestRecordFromFile(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Courses"
        self.assertEqual(call("course", "init", "--courses-root", self.root,
                              "--approve").returncode, 0)
        created = call("course", "create", "--courses-root", self.root,
                       "--category", "technology", "--title", "DNS",
                       "--goal", "explain DNS", "--approve")
        self.assertEqual(created.returncode, 0, created.stderr)
        self.cid = json.loads(created.stdout)["course_id"]
        self.ledger = self.root / ".learnprint" / "events.jsonl"
        self.data = {
            "event_id": "record-json-001",
            "topic": self.cid,
            "course_id": self.cid,
            "competency": "dns-name-resolution",
            "task_type": "independent_application",
            "answer": "Resolver queries the DNS cache before contacting upstream.",
            "rubric": {"concept": None, "mechanism": None,
                       "application": 2, "transfer": None},
            "expected": "Explain lookup sequence",
            "feedback": "Demonstrated resolver lookup ordering in this response.",
            "grader": "ai_reviewed",
            "help_level": "none",
            "confidence": 90,
            "grader_source": "agent",
        }
        self.jsonfile = Path(self.temp.name) / "event.json"
        self._save()

    def _save(self):
        self.jsonfile.write_text(json.dumps(self.data), encoding="utf-8")

    def test_record_file_preserves_json_and_learner_answer(self):
        r = call("record", "--workspace", self.root, "--from-file",
                 self.jsonfile, "--approve")
        self.assertEqual(r.returncode, 0, r.stderr)
        events = [json.loads(s) for s in self.ledger.read_text(
            encoding="utf-8").splitlines() if s.strip()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["observed_answer"], self.data["answer"])
        self.assertEqual(events[0]["rubric"], self.data["rubric"])
        self.assertEqual(events[0]["grader_source"], "agent")

    def test_approval_cannot_be_granted_by_json(self):
        self.data["approve"] = True
        self._save()
        before = self.ledger.read_bytes()
        r = call("record", "--workspace", self.root,
                 "--from-file", self.jsonfile)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertIn("unknown", r.stderr.lower())

    def test_no_approve_denies_valid_file(self):
        before = self.ledger.read_bytes()
        r = call("record", "--workspace", self.root, "--from-file", self.jsonfile)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("approval", r.stderr.lower())
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_unknown_fields_do_not_bypass_schema(self):
        self.data["is_synthetic_example"] = False
        self._save()
        r = call("record", "--workspace", self.root, "--from-file",
                 self.jsonfile, "--approve")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.ledger.read_text(encoding="utf-8"), "")

    def test_mixed_inline_and_file_rejected(self):
        r = call("record", "--workspace", self.root, "--from-file",
                 self.jsonfile, "--answer", "wrong", "--approve")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("combined", r.stderr.lower())

    def test_confusion_is_not_scored_even_from_file(self):
        self.data["answer"] = "masih gak ngerti"
        self._save()
        r = call("record", "--workspace", self.root,
                 "--from-file", self.jsonfile, "--approve")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("confusion", r.stderr.lower())
        self.assertEqual(self.ledger.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
