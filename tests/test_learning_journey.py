"""Learner-journey CLI acceptance: no global plugins, no real Courses/ writes."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "learnprint.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, timeout=90)


def success(*args):
    result = run(*args)
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout)


class TestLearnerJourney(unittest.TestCase):
    def setup_course(self, temp):
        root = Path(temp) / "Courses"
        init = run("course", "init", "--courses-root", root, "--approve")
        self.assertEqual(init.returncode, 0, init.stderr)
        course = success("course", "create", "--courses-root", root,
                         "--category", "technology", "--title", "SQL interview",
                         "--goal", "Explain joins and use SQL", "--approve")
        scope = Path(temp) / "scope.json"
        scope.write_text(json.dumps([
            {"id": "db", "name": "Understand database engines",
             "status": "unknown", "evidence_ids": []},
            {"id": "join", "name": "Explain and apply SQL joins",
             "status": "unknown", "evidence_ids": []}]), encoding="utf-8")
        result = run("course", "scope-set", "--courses-root", root,
                     "--course-id", course["course_id"],
                     "--from-file", scope, "--approve")
        self.assertEqual(result.returncode, 0, result.stderr)
        return root, course

    def plan(self):
        return [
            {"unit_id": "db-basics", "title": "SQL vs engines and client tools",
             "outcome": "Distinguish SQL, MySQL and DBeaver",
             "hands_on": "Run a SELECT in an available safe SQLite sandbox",
             "success_check": "Explain which component executed the query",
             "practice_mode": "hands_on", "requires": [], "competency_ids": ["db"]},
            {"unit_id": "sql-joins", "title": "SQL JOINs",
             "outcome": "Use joins without duplicate counts",
             "hands_on": "Query two small tables and inspect output",
             "success_check": "Correct new dataset without hints",
             "practice_mode": "hands_on", "requires": ["db-basics"],
             "competency_ids": ["join"]}
        ]

    def test_plan_first_and_method_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root, c = self.setup_course(d)
            method = success("learner", "method", "--courses-root", root)
            self.assertEqual(method["source"], "founder_default")
            self.assertTrue(method["fingerprint"].startswith("sha256:"))
            self.assertTrue(method["instruction_defaults"]["teach_one_unit_at_a_time"])
            before = success("course", "plan", "--courses-root", root,
                             "--course-id", c["course_id"])
            self.assertEqual(before["syllabus_status"], "needs_adoption")
            self.assertEqual(before["method"]["fingerprint"], method["fingerprint"])
            self.assertEqual(before["units"], [])
            p = Path(d) / "syllabus.json"
            p.write_text(json.dumps(self.plan()), encoding="utf-8")
            self.assertEqual(run("course", "plan-set", "--courses-root", root,
                                 "--course-id", c["course_id"],
                                 "--from-file", p).returncode, 2)
            result = success("course", "plan-set", "--courses-root", root,
                             "--course-id", c["course_id"],
                             "--from-file", p, "--approve")
            self.assertEqual(result["units"], 2)
            self.assertTrue(Path(result["backup"]).exists())
            listed = success("course", "plan", "--courses-root", root,
                             "--course-id", c["course_id"])
            self.assertEqual([u["unit_id"] for u in listed["units"]],
                             ["db-basics", "sql-joins"])
            self.assertEqual(listed["units"][0]["evidence_status"], "not_assessed")
            self.assertEqual(listed["course_completion"], "not_yet_maintained")
            self.assertIn("hands_on", listed["units"][0])
            self.assertEqual(run("course", "validate", "--courses-root", root).returncode, 0)

    def test_prerequisite_insertion_and_safe_rejections(self):
        with tempfile.TemporaryDirectory() as d:
            root, c = self.setup_course(d)
            src = Path(d) / "syllabus.json"
            command = ["course", "plan-set", "--courses-root", str(root),
                       "--course-id", c["course_id"], "--from-file", str(src), "--approve"]
            def attempt(items):
                src.write_text(json.dumps(items), encoding="utf-8")
                return run(*command)
            self.assertEqual(attempt(self.plan()).returncode, 0)
            new = dict(self.plan()[0], unit_id="prerequisite", title="What is data?",
                       competency_ids=["db"], requires=[])
            updated = self.plan()
            updated[0] = dict(updated[0], requires=["prerequisite"])
            updated.append(new)
            self.assertEqual(attempt(updated).returncode, 0)
            listed = success("course", "plan", "--courses-root", root,
                             "--course-id", c["course_id"])
            self.assertEqual([u["unit_id"] for u in listed["units"]][:2],
                             ["prerequisite", "db-basics"])
            self.assertNotEqual(attempt([updated[0], updated[1]]).returncode, 0)
            bad = [dict(u) for u in updated]
            bad[0] = dict(bad[0], requires=["sql-joins"])
            self.assertNotEqual(attempt(bad).returncode, 0)
            bad = [dict(u) for u in updated]
            bad[0] = dict(bad[0], hands_on="")
            self.assertNotEqual(attempt(bad).returncode, 0)
            bad = [dict(u) for u in updated]
            bad[0] = dict(bad[0], competency_ids=["unregistered"])
            self.assertNotEqual(attempt(bad).returncode, 0)
            self.assertEqual([u["unit_id"] for u in
                success("course", "plan", "--courses-root", root,
                        "--course-id", c["course_id"])["units"]][:2],
                             ["prerequisite", "db-basics"])

    def test_read_only_plan_does_not_create_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            output = success("learner", "method", "--courses-root", root)
            self.assertEqual(output["source"], "founder_default")
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
