"""Method configuration/audit regression tests. Only disposable Courses/ workspaces."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "learnprint.py"


def run(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                          capture_output=True, text=True, timeout=60)


def data(*args):
    result = run(*args)
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout)


class TestEffectiveMethod(unittest.TestCase):
    def setup_workspace(self, home):
        root = Path(home) / "Courses"
        result = run("course", "init", "--courses-root", root, "--approve")
        self.assertEqual(result.returncode, 0, result.stderr)
        return root

    def setup_course(self, home):
        root = self.setup_workspace(home)
        course = data("course", "create", "--category", "technology",
                      "--title", "SQL interview", "--goal", "Use SQL",
                      "--courses-root", root, "--approve")
        return root, course

    def test_complete_founder_method_and_legacy_fingerprint(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            first = data("learner", "method", "--courses-root", root)
            self.assertFalse(root.exists())
            self.assertEqual(first["source"], "founder_default")
            self.assertIn("language", first["preferences"])
            self.assertIn("analogies", first["preferences"])
            self.assertTrue(first["fingerprint"].startswith("sha256:"))
            self.assertTrue(first["effective_fingerprint"].startswith("sha256:"))
            self.assertNotEqual(first["fingerprint"], first["effective_fingerprint"])
            self.assertEqual(first["method_revision"], 0)
            self.assertEqual(first["effective_fingerprint_scope"],
                             "instruction_defaults_and_preferences")
            self.setup_workspace(d)
            saved = data("learner", "method", "--courses-root", root)
            self.assertEqual(saved["effective_fingerprint"], first["effective_fingerprint"])
            self.assertEqual(saved["fingerprint"], first["fingerprint"])
            self.assertEqual(saved["assessment_status"], "unassessed")

    def test_assessed_personal_preferences_are_effective_and_fingerprinted(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.setup_workspace(d)
            data("learner", "assessment-start", "--courses-root", root, "--approve")
            observed = []
            for mode in ("prior_knowledge", "transfer"):
                observed.append(data("learner", "assessment-record",
                                     "--courses-root", root, "--question", "Question " + mode,
                                     "--answer", "Actual fixture learner answer for " + mode,
                                     "--task-type", mode, "--approve"))
            file = root / ".learnprint" / "learner" / "profile.json"
            profile = json.loads(file.read_text(encoding="utf-8"))
            candidate = dict(profile)
            candidate.update({
                "assessment_status": "assessed",
                "instruction_defaults": {"teach_one_unit_at_a_time": True},
                "preferences": {"language": "English for SQL", "analogies": "Use SQL table examples"},
                "evidence": [
                    {"id": "e" + str(i), "origin": "observed_task",
                     "verification": "observed", "description": e["observed_answer"],
                     "source": "assessment-event:" + e["event_id"]}
                    for i, e in enumerate(observed)
                ],
                "observed_claims": [
                    {"id": "claim", "category": "observed",
                     "claim": "A behavior observed in isolated test fixture",
                     "evidence_ids": ["e0", "e1"]}
                ],
            })
            candidate_path = file.with_name("profile-candidate.json")
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            finish = data("learner", "assessment-complete", "--courses-root", root, "--approve")
            self.assertEqual(finish["assessment_status"], "assessed")
            result = data("learner", "method", "--courses-root", root)
            self.assertEqual(result["source"], "personal_assessment")
            self.assertEqual(result["preferences"], candidate["preferences"])
            self.assertEqual(result["method_revision"], 1)
            self.assertNotEqual(result["effective_fingerprint"],
                                data("learner", "method", "--courses-root", Path(d) / "Other")["effective_fingerprint"])
            # Preferences are part of v2 fingerprint, while the old stored
            # defaults-only fingerprint remains backward compatible.
            candidate["preferences"]["language"] = "Different language"
            private = json.loads(file.read_text(encoding="utf-8"))
            private["preferences"] = candidate["preferences"]
            file.write_text(json.dumps(private), encoding="utf-8")
            updated = data("learner", "method", "--courses-root", root)
            self.assertNotEqual(updated["effective_fingerprint"], result["effective_fingerprint"])
            self.assertEqual(updated["fingerprint"], result["fingerprint"])

    def test_unverified_without_session_and_session_receipt_not_behavior_proof(self):
        with tempfile.TemporaryDirectory() as d:
            root, course = self.setup_course(d)
            cid = course["course_id"]
            initial = data("course", "method-audit", "--courses-root", root, "--course-id", cid)
            self.assertEqual(initial["overall"], "NOT_VERIFIED")
            self.assertEqual(initial["checks"]["method_receipt"]["status"], "NOT_VERIFIED")
            self.assertEqual(initial["checks"]["learner_preferences_followed"]["status"], "NOT_VERIFIED")
            p = root / course["rel_path"] / "method-sessions.jsonl"
            self.assertFalse(p.exists())  # Read-only audit never creates receipts.
            self.assertEqual(run("course", "session-start", "--courses-root", root,
                                 "--course-id", cid).returncode, 2)
            session = data("course", "session-start", "--courses-root", root,
                           "--course-id", cid, "--approve")
            self.assertTrue(uuid.UUID(session["session_id"]))
            saved = p.read_bytes()
            after = data("course", "method-audit", "--courses-root", root,
                         "--course-id", cid, "--session-id", session["session_id"])
            self.assertEqual(after["checks"]["method_receipt"]["status"], "PASS")
            self.assertEqual(after["checks"]["roadmap_shown_to_learner"]["status"], "NOT_VERIFIED")
            self.assertEqual(after["overall"], "NOT_VERIFIED")
            self.assertEqual(saved, p.read_bytes())
            self.assertNotEqual(run("course", "method-audit", "--courses-root", root,
                                    "--course-id", cid, "--session-id", str(uuid.uuid4())).returncode, 0)

    def test_session_linked_activity_and_ledger_are_not_claims_of_adherence(self):
        with tempfile.TemporaryDirectory() as d:
            root, course = self.setup_course(d)
            cid = course["course_id"]
            scope = Path(d) / "scope.json"
            scope.write_text(json.dumps([
                {"id": "sql", "name": "Use SQL", "status": "unknown", "evidence_ids": []}]),
                encoding="utf-8")
            self.assertEqual(run("course", "scope-set", "--courses-root", root,
                                 "--course-id", cid, "--from-file", scope, "--approve").returncode, 0)
            plan = Path(d) / "plan.json"
            plan.write_text(json.dumps([
                {"unit_id": "sql-basics", "title": "SQL basics",
                 "outcome": "Use SELECT", "competency_ids": ["sql"],
                 "requires": [], "practice_mode": "hands_on",
                 "hands_on": "Run SELECT 1 in SQLite",
                 "success_check": "Show the result"}]), encoding="utf-8")
            self.assertEqual(run("course", "plan-set", "--courses-root", root,
                                 "--course-id", cid, "--from-file", plan, "--approve").returncode, 0)
            session = data("course", "session-start", "--courses-root", root,
                           "--course-id", cid, "--approve")
            sid = session["session_id"]
            base = ("course", "lesson-log", "--course-id", cid, "--courses-root", root,
                    "--unit-id", "sql-basics", "--kind", "practice",
                    "--note", "Agent claims learner executed SELECT 1",
                    "--session-id", sid)
            self.assertEqual(run(*base).returncode, 2)
            self.assertEqual(run(*base, "--approve").returncode, 0)
            self.assertEqual(run("course", "lesson-log", "--course-id", cid,
                                 "--courses-root", root, "--unit-id", "sql-basics",
                                 "--kind", "covered", "--note", "Unknown session",
                                 "--session-id", str(uuid.uuid4()), "--approve").returncode, 2)
            rec = ["record", "--workspace", str(root), "--event-id", str(uuid.uuid4()),
                   "--topic", cid, "--competency", "sql",
                   "--task-type", "independent_application",
                   "--answer", "SELECT 1;", "--rubric",
                   json.dumps({"concept": 1, "mechanism": 1, "application": 1, "transfer": 0}),
                   "--expected", "Run a SELECT", "--feedback", "Needs transfer",
                   "--grader", "ai_reviewed", "--course-id", cid,
                   "--session-id", sid, "--approve"]
            self.assertEqual(run(*rec).returncode, 0)
            report = data("course", "method-audit", "--course-id", cid, "--courses-root", root,
                          "--session-id", sid)
            self.assertEqual(report["checks"]["recorded_practice"]["status"], "PASS")
            self.assertEqual(report["checks"]["recorded_assessment"]["status"], "PASS")
            self.assertEqual(report["checks"]["rubric_fairness"]["status"], "NOT_VERIFIED")
            self.assertEqual(report["checks"]["hands_on_actually_performed"]["status"], "NOT_VERIFIED")
            self.assertEqual(report["overall"], "NOT_VERIFIED")
            transcript = Path(d) / "session.txt"
            transcript.write_text("Agent: I followed everything.\n", encoding="utf-8")
            report2 = data("course", "method-audit", "--course-id", cid, "--courses-root", root,
                           "--session-id", sid, "--transcript-file", transcript)
            self.assertEqual(report2["checks"]["transcript_available"]["status"], "PASS")
            self.assertEqual(report2["overall"], "NOT_VERIFIED")
            self.assertEqual(report2["checks"]["learner_preferences_followed"]["status"], "NOT_VERIFIED")

    def test_method_drift_detected_and_log_corruption_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root, course = self.setup_course(d)
            cid = course["course_id"]
            session = data("course", "session-start", "--courses-root", root,
                           "--course-id", cid, "--approve")
            p = root / course["rel_path"] / "method-sessions.jsonl"
            original = p.read_bytes()
            founder = ROOT / "profiles" / "founder-default.json"
            # We cannot alter the tracked founder method here. Instead,
            # tamper a private receipt to demonstrate fail-closed behavior.
            receipt = json.loads(original)
            receipt["effective_fingerprint"] = "sha256:" + "0" * 64
            p.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            result = run("course", "method-audit", "--courses-root", root, "--course-id", cid)
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertEqual(report["overall"], "FAIL")
            self.assertEqual(report["checks"]["method_receipt"]["status"], "FAIL")
            p.write_bytes(original[:-1])
            failed = run("course", "method-audit", "--courses-root", root, "--course-id", cid)
            self.assertEqual(failed.returncode, 2)
            self.assertIn("ERROR", failed.stderr)


if __name__ == "__main__":
    unittest.main()
