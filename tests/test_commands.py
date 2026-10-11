"""Public-boundary regression tests for portable Learnprint commands.

Uses only stdlib, temporary isolated learner roots and CLI subprocesses.
Never touches the repository's private Courses/.
"""
import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "learnprint.py"


def cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, timeout=90)


def read_json(result):
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout)


class TestLearnerMethodLifecycle(unittest.TestCase):
    def test_first_run_status_is_read_only_and_uses_founder_fingerprint(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            first = read_json(cli("learner", "status", "--courses-root", root))
            second = read_json(cli("learner", "status", "--courses-root", root))
            self.assertEqual(first, second)
            self.assertEqual(first["workspace"], "not_initialized")
            self.assertEqual(first["assessment_offer"], "not_offered")
            self.assertTrue(first["method_fingerprint"].startswith("sha256:"))
            self.assertFalse(root.exists())

    def test_default_choice_persists_without_assessment_claim(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            self.assertEqual(cli("course", "init", "--courses-root", root, "--approve").returncode, 0)
            before = read_json(cli("learner", "status", "--courses-root", root))
            self.assertEqual(before["assessment_offer"], "not_offered")
            self.assertTrue(uuid.UUID(before["profile_id"]).version == 4)
            denied = cli("learner", "use-default", "--courses-root", root)
            self.assertEqual(denied.returncode, 2)
            after = read_json(cli("learner", "use-default", "--courses-root", root, "--approve"))
            self.assertEqual(after["assessment_offer"], "deferred")
            self.assertEqual(after["assessment_status"], "unassessed")
            self.assertEqual(after["method_source"], "founder_default")
            self.assertTrue(after["stored_fingerprint_matches"])
            self.assertEqual(read_json(cli("learner", "status", "--courses-root", root)),
                             after)

    def test_assessment_requires_real_evidence_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            self.assertEqual(cli("course", "init", "--courses-root", root, "--approve").returncode, 0)
            start = read_json(cli("learner", "assessment-start", "--courses-root", root, "--approve"))
            self.assertEqual(start["assessment_offer"], "in_progress")
            fail = cli("learner", "assessment-complete", "--courses-root", root, "--approve")
            self.assertEqual(fail.returncode, 2)
            profile_path = root / ".learnprint" / "learner" / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            candidate = dict(profile)
            candidate.update({"assessment_status": "assessed",
                              "observed_claims": [
                                  {"id": "c1", "claim": "Explained a concept independently",
                                   "category": "observed", "evidence_ids": ["e1"]}],
                              "evidence": [
                                  {"id": "e1", "origin": "observed_task",
                                   "description": "Independent response to a real task",
                                   "verification": "observed", "source": "private assessment"}],
                              "instruction_defaults": {"teach_one_unit_at_a_time": True}})
            candidate_path = profile_path.with_name("profile-candidate.json")
            candidate_path.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
            complete = read_json(cli("learner", "assessment-complete", "--courses-root", root, "--approve"))
            self.assertEqual(complete["profile_id"], start["profile_id"])
            self.assertEqual(complete["assessment_status"], "assessed")
            self.assertEqual(complete["assessment_offer"], "completed")
            self.assertEqual(complete["method_revision"], 1)
            self.assertTrue(complete["stored_fingerprint_matches"])
            self.assertTrue(profile_path.with_name("profile.previous-0000.json").exists())
            self.assertEqual(cli("learner", "assessment-start", "--courses-root", root, "--approve").returncode, 2)
            self.assertEqual(cli("learner", "assessment-complete", "--courses-root", root, "--approve").returncode, 2)
            # Reassessment preserves the same stable identity and evidence.
            read_json(cli("learner", "assessment-start", "--courses-root", root, "--reassess", "--approve"))
            candidate["instruction_defaults"] = {"teach_one_unit_at_a_time": False}
            candidate_path.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
            updated = read_json(cli("learner", "assessment-complete", "--courses-root", root, "--approve"))
            self.assertEqual(updated["method_revision"], 2)
            self.assertEqual(updated["profile_id"], start["profile_id"])
            self.assertNotEqual(updated["method_fingerprint"], complete["method_fingerprint"])
            self.assertTrue(profile_path.with_name("profile.previous-0001.json").exists())

    def test_corrupt_profile_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            cli("course", "init", "--courses-root", root, "--approve")
            p = root / ".learnprint" / "learner" / "profile.json"
            p.write_text("{broken", encoding="utf-8")
            self.assertEqual(cli("learner", "status", "--courses-root", root).returncode, 2)
            self.assertEqual(cli("learner", "use-default", "--courses-root", root, "--approve").returncode, 2)


class TestPortableCourseOverview(unittest.TestCase):
    def test_overview_no_workspace_has_no_side_effect(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            result = read_json(cli("course", "overview", "--courses-root", root))
            self.assertEqual(result["status"], "workspace_not_initialized")
            self.assertFalse(root.exists())

    def test_overview_uses_canonical_ledger_and_reports_invalid_state(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            self.assertEqual(cli("course", "init", "--courses-root", root, "--approve").returncode, 0)
            r = read_json(cli("course", "create", "--courses-root", root,
                              "--category", "technology", "--title", "SQL",
                              "--goal", "interview", "--approve"))
            summary = read_json(cli("course", "overview", "--courses-root", root))
            self.assertEqual(len(summary["courses"]), 1)
            self.assertEqual(summary["courses"][0]["status"], "not_assessed")
            self.assertIsNone(summary["courses"][0]["progress"])
            path = root / r["rel_path"] / "state.json"
            st = json.loads(path.read_text(encoding="utf-8"))
            st["learning_scope"] = [{"id": "joins", "status": "unknown"}]  # flawed agent output
            path.write_text(json.dumps(st) + "\n", encoding="utf-8")
            bad = read_json(cli("course", "overview", "--courses-root", root))
            self.assertEqual(bad["courses"][0]["status"], "state_invalid")
            self.assertIsNone(bad["courses"][0]["progress"])
            # This same invalid state must not be stamped VALID by course validate.
            validation = cli("course", "validate", "--courses-root", root)
            self.assertEqual(validation.returncode, 2)
            self.assertIn("INVALID", validation.stdout)

    def test_legacy_unnamed_scope_can_be_repaired_without_loss(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            cli("course", "init", "--courses-root", root, "--approve")
            course = read_json(cli("course", "create", "--courses-root", root,
                                   "--category", "technology", "--title", "SQL sprint",
                                   "--goal", "interview", "--approve"))
            state_path = root / course["rel_path"] / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["learning_scope"] = [{"id": "joins", "status": "unknown"}]
            state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
            before_id = state["course_id"]
            self.assertEqual(cli("course", "validate", "--courses-root", root).returncode, 2)
            scope = Path(d) / "safe-scope.json"
            scope.write_text(json.dumps([{"id": "joins", "name": "SQL joins",
                                          "status": "unknown", "evidence_ids": []}]),
                             encoding="utf-8")
            repaired = cli("course", "scope-set", "--courses-root", root,
                           "--course-id", before_id, "--from-file", scope, "--approve")
            self.assertEqual(repaired.returncode, 0, repaired.stderr)
            final = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(final["course_id"], before_id)
            self.assertEqual(final["learning_scope"][0]["id"], "joins")
            self.assertEqual(cli("course", "validate", "--courses-root", root).returncode, 0)
            self.assertEqual(read_json(cli("course", "overview", "--courses-root", root))
                             ["courses"][0]["status"], "scored")

    def test_scope_set_requires_approval_and_retains_other_state(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            cli("course", "init", "--courses-root", root, "--approve")
            created = read_json(cli("course", "create", "--courses-root", root,
                                    "--category", "technology", "--title", "SQL",
                                    "--goal", "interview", "--approve"))
            draft = Path(d) / "scope.json"
            draft.write_text(json.dumps([{"id": "joins", "name": "JOINs and aggregate",
                                          "status": "unknown", "evidence_ids": []}]),
                             encoding="utf-8")
            cmd = ["course", "scope-set", "--courses-root", str(root),
                   "--course-id", created["course_id"], "--from-file", str(draft)]
            self.assertEqual(cli(*cmd).returncode, 2)
            self.assertEqual(cli(*cmd, "--approve").returncode, 0)
            overview = read_json(cli("course", "overview", "--courses-root", root))
            self.assertEqual(overview["courses"][0]["status"], "scored")
            self.assertEqual(overview["courses"][0]["progress"]["observed_immediate_coverage_percent"], 0.0)
            saved = json.loads((root / created["rel_path"] / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["course_id"], created["course_id"])
            self.assertEqual(saved["goal"], "interview")
            invalid = Path(d) / "invalid.json"
            invalid.write_text('[{"id": "bad", "status": "unknown"}]', encoding="utf-8")
            self.assertEqual(cli("course", "scope-set", "--courses-root", root,
                                 "--course-id", created["course_id"],
                                 "--from-file", invalid, "--approve").returncode, 2)
            self.assertEqual(len(json.loads((root / created["rel_path"] / "state.json")
                                            .read_text(encoding="utf-8"))["learning_scope"]), 1)


class TestPortableDiscovery(unittest.TestCase):
    def test_native_project_skill_and_commands_are_bundled(self):
        names = ["learnprint", "learnprint-assess", "learnprint-learn"]
        for name in names:
            self.assertTrue((ROOT / ".agents" / "skills" / name / "SKILL.md").is_file())
            self.assertTrue((ROOT / "skills" / name / "SKILL.md").is_file())
            self.assertEqual((ROOT / ".agents" / "skills" / name / "SKILL.md")
                             .read_bytes(), (ROOT / "skills" / name / "SKILL.md").read_bytes())
        commands = ["learnprint", "learnprint-learn", "learnprint-continue-learn",
                    "learnprint-assessment", "learnprint-reassessment",
                    "learnprint-test", "learnprint-progress", "learnprint-review",
                    "learnprint-dashboard", "learnprint-help"]
        for name in commands:
            p = ROOT / ".opencode" / "commands" / (name + ".md")
            self.assertTrue(p.is_file(), str(p))
            self.assertIn("$ARGUMENTS", p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
