"""Evidence correction regressions only use disposable learner workspaces."""
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

CLI = Path(__file__).resolve().parents[1] / "scripts" / "learnprint.py"


def run(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                          capture_output=True, text=True, timeout=60)


class TestEvidenceExclusion(unittest.TestCase):
    def new_course(self, d):
        root = Path(d) / "Courses"
        self.assertEqual(run("course", "init", "--courses-root", root, "--approve").returncode, 0)
        created = run("course", "create", "--courses-root", root, "--category",
                      "technology", "--title", "Test SQL", "--goal", "SQL", "--approve")
        self.assertEqual(created.returncode, 0, created.stderr)
        cid = json.loads(created.stdout)["course_id"]
        scope = Path(d) / "scope.json"
        scope.write_text(json.dumps([{"id": "sql", "name": "SQL",
                                      "status": "unknown", "evidence_ids": []}]))
        self.assertEqual(run("course", "scope-set", "--courses-root", root,
                             "--course-id", cid, "--from-file", scope, "--approve").returncode, 0)
        return root, cid

    def record(self, root, cid, answer, task="recognition", target=None, exclude=False):
        args = ["record", "--workspace", root, "--course-id", cid,
                "--topic", cid, "--event-id", str(uuid.uuid4()), "--competency", "sql",
                "--task-type", task, "--answer", answer,
                "--rubric", json.dumps({"concept": 0, "mechanism": 0,
                                        "application": 0, "transfer": 0}),
                "--expected", "Concept check", "--feedback", "Reviewed correction",
                "--approve"]
        if target is not None:
            args.extend(["--corrects", target])
        if exclude:
            args.append("--exclude-from-assessment")
        return run(*args)

    def counts(self, root):
        result = run("course", "overview", "--courses-root", root)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["courses"][0]["progress"]["competencies"][0]

    def test_old_confusion_remains_readable_and_explicitly_excludable(self):
        with tempfile.TemporaryDirectory() as d:
            root, cid = self.new_course(d)
            ledger = root / ".learnprint" / "events.jsonl"
            rejected = self.record(root, cid, "masih gak ngerti")
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(ledger.read_bytes(), b"")
            old_id = str(uuid.uuid4())
            old = {"event_id": old_id, "date": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "topic_id": cid, "course_id": cid, "competency_id": "sql",
                   "task_type": "recognition", "observed_answer": "masih gak ngerti",
                   "expected_reasoning": "recognition", "help_level": "none",
                   "rubric": {"concept": 0, "mechanism": 0, "application": 0, "transfer": 0},
                   "feedback": "Incorrect score", "grader": "ai_reviewed",
                   "evidence_origin": "observed_response", "is_synthetic_example": False}
            ledger.write_text(json.dumps(old) + "\n", encoding="utf-8")
            self.assertEqual(self.counts(root)["observations"], 1)
            no_target = self.record(root, cid, "No target", task="correction",
                                    target=str(uuid.uuid4()), exclude=True)
            self.assertEqual(no_target.returncode, 2)
            self.assertEqual(ledger.read_text(encoding="utf-8").count("\n"), 1)
            correction = self.record(root, cid, "Not an answer", task="correction",
                                     target=old_id, exclude=True)
            self.assertEqual(correction.returncode, 0, correction.stderr)
            stats = self.counts(root)
            self.assertEqual(stats["observations"], 0)
            self.assertEqual(stats["excluded_observations"], 1)
            self.assertEqual(stats["status"], "unknown")
            rows = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertEqual(rows[0], old)
            self.assertEqual(rows[1]["corrects_event_id"], old_id)
            self.assertTrue(rows[1]["exclude_from_assessment"])
            duplicate = self.record(root, cid, "Duplicate", task="correction",
                                    target=old_id, exclude=True)
            self.assertEqual(duplicate.returncode, 2)
            self.assertEqual(len(ledger.read_text().splitlines()), 2)

    def test_correction_is_not_itself_a_mastery_observation(self):
        with tempfile.TemporaryDirectory() as d:
            root, cid = self.new_course(d)
            good = self.record(root, cid, "SQL is a language")
            self.assertEqual(good.returncode, 0, good.stderr)
            data = json.loads((root / ".learnprint" / "events.jsonl").read_text().splitlines()[0])
            self.assertEqual(self.counts(root)["observations"], 1)
            correction = self.record(root, cid, "Rubric clarification",
                                     task="correction", target=data["event_id"])
            self.assertEqual(correction.returncode, 0, correction.stderr)
            self.assertEqual(self.counts(root)["observations"], 1)

    def test_cross_course_identity_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root, cid = self.new_course(d)
            good = self.record(root, cid, "SQL is a language")
            self.assertEqual(good.returncode, 0, good.stderr)
            eid = json.loads((root / ".learnprint" / "events.jsonl").read_text().splitlines()[0])["event_id"]
            foreign = run("course", "create", "--courses-root", root, "--category",
                          "technology", "--title", "Other SQL", "--goal", "SQL", "--approve")
            self.assertEqual(foreign.returncode, 0, foreign.stderr)
            other = json.loads(foreign.stdout)["course_id"]
            scope = Path(d) / "scope2.json"
            scope.write_text(json.dumps([{"id": "sql", "name": "SQL",
                                          "status": "unknown", "evidence_ids": []}]))
            self.assertEqual(run("course", "scope-set", "--courses-root", root,
                                 "--course-id", other, "--from-file", scope, "--approve").returncode, 0)
            no = self.record(root, other, "Wrong course", "correction", eid, True)
            self.assertEqual(no.returncode, 2)


if __name__ == "__main__":
    unittest.main()
