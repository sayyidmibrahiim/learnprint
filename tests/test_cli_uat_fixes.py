"""Regression: read-only UAT previews and Windows-safe CLI output."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / "scripts" / "learnprint.py"


def run(*args, env=None):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                          capture_output=True, text=True, timeout=60, env=env)


class TestSafeCLIPreview(unittest.TestCase):
    def test_preview_read_only_and_windows_encoding(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            self.assertEqual(run("course", "init", "--courses-root", root, "--approve").returncode, 0)
            made = run("course", "create", "--courses-root", root, "--category", "technology",
                       "--title", "SQL → basics", "--goal", "Learn SQL", "--approve")
            self.assertEqual(made.returncode, 0, made.stderr)
            created = json.loads(made.stdout)
            cid = created["course_id"]
            scope = Path(d) / "scope.json"
            scope.write_text(json.dumps([{"id": "sql", "name": "SQL",
                                          "status": "unknown", "evidence_ids": []}]))
            result = run("course", "scope-set", "--courses-root", root, "--course-id", cid,
                         "--from-file", scope, "--approve")
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = Path(d) / "plan.json"
            units = [{"unit_id": "intro", "title": "Introduction", "outcome": "Run SELECT",
                      "competency_ids": ["sql"], "requires": [],
                      "practice_mode": "hands_on", "hands_on": "Run SELECT 1",
                      "success_check": "Observe result 1"}]
            plan.write_text(json.dumps(units))
            state = root / created["rel_path"] / "state.json"
            original = state.read_bytes()
            review = root / ".learnprint" / "reviews.json"
            original_review = review.read_bytes()
            v = run("course", "plan-set", "--courses-root", root, "--course-id", cid,
                    "--from-file", plan, "--dry-run")
            self.assertEqual(v.returncode, 0, v.stderr)
            self.assertEqual(json.loads(v.stdout)["status"], "valid_preview")
            self.assertEqual(state.read_bytes(), original)
            units[0]["competency_ids"] = []
            plan.write_text(json.dumps(units))
            bad = run("course", "plan-set", "--courses-root", root, "--course-id", cid,
                      "--from-file", plan, "--dry-run")
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(state.read_bytes(), original)
            preview = run("course", "plan-reviews", "--courses-root", root, "--dry-run")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(review.read_bytes(), original_review)
            select = run("course", "resume", "--courses-root", root, "--course-id", cid)
            self.assertEqual(select.returncode, 0, select.stderr)
            self.assertEqual(json.loads(select.stdout)["course"]["course_id"], cid)
            env = dict(os.environ, PYTHONIOENCODING="cp1252:strict")
            narrow = run("course", "overview", "--courses-root", root, env=env)
            self.assertEqual(narrow.returncode, 0, narrow.stderr)
            self.assertIn("SQL", narrow.stdout)


if __name__ == "__main__":
    unittest.main()
