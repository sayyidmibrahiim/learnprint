"""CLI-seam tests: drive scripts/learnprint.py as a subprocess.

Seam under test: process boundary (argv in, exit code + stdout out).
Nothing here touches module internals.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = str(ROOT / "scripts" / "learnprint.py")


def cli(*argv, cwd=None):
    return subprocess.run([sys.executable, SCRIPT, *argv], cwd=cwd,
                          capture_output=True, text=True, timeout=60)


class TestCourseInitCLI(unittest.TestCase):
    def test_init_happy_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = str(Path(d) / "Courses")
            r = cli("course", "init", "--courses-root", root, "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(root) / ".learnprint" / "registry.json").exists())

    def test_init_refuses_without_approve(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = str(Path(d) / "Courses")
            r = cli("course", "init", "--courses-root", root)
            self.assertEqual(r.returncode, 2)
            self.assertFalse(Path(root).exists())

    def test_init_refuses_when_initialized(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = str(Path(d) / "Courses")
            self.assertEqual(cli("course", "init", "--courses-root", root, "--approve").returncode, 0)
            r = cli("course", "init", "--courses-root", root, "--approve")
            self.assertEqual(r.returncode, 2)


def init_courses(d):
    root = str(Path(d) / "Courses")
    r = cli("course", "init", "--courses-root", root, "--approve")
    assert r.returncode == 0, r.stderr
    return root


class TestCourseCreateResolveCLI(unittest.TestCase):
    def test_create_resolve_list_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            r = cli("course", "create", "--courses-root", root,
                    "--category", "languages/english/grammar",
                    "--title", "in on at", "--goal", "meetings",
                    "--alias", "prepositions in on at",
                    "--confirm-new-segment", "english",
                    "--confirm-new-segment", "grammar", "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            created = json.loads(r.stdout)
            self.assertIn("course_id", created)
            r = cli("course", "resolve", "--courses-root", root, "--query", "in/on/at")
            self.assertEqual(r.returncode, 0, r.stderr)
            found = json.loads(r.stdout)
            self.assertEqual(found["status"], "found")
            self.assertEqual(found["course"]["course_id"], created["course_id"])
            r = cli("course", "list", "--courses-root", root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(len(json.loads(r.stdout)), 1)

    def test_create_requires_approve_flag(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            r = cli("course", "create", "--courses-root", root,
                    "--category", "languages/english/grammar",
                    "--title", "in on at", "--goal", "meetings")
            self.assertEqual(r.returncode, 2)

    def test_create_typo_category_refused_without_confirmation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            base = ["course", "create", "--courses-root", root,
                    "--category", "languages/english/grammar",
                    "--title", "in on at", "--goal", "g",
                    "--confirm-new-segment", "english",
                    "--confirm-new-segment", "grammar", "--approve"]
            self.assertEqual(cli(*base).returncode, 0)
            r = cli("course", "create", "--courses-root", root,
                    "--category", "languages/english/grammer",
                    "--title", "Grammer", "--goal", "g", "--approve")
            self.assertEqual(r.returncode, 2)
            self.assertIn("confirm", r.stderr.lower())


def make_course(root, category="languages/english/grammar", title="in on at"):
    flags = []
    if "english" in category or "grammar" in category:
        pass
    import json as _json
    segs = [s for s in category.strip("/").split("/") if s]
    # confirm every non-root segment (mirrors a reviewing agent)
    cmd = ["course", "create", "--courses-root", root, "--category", category,
           "--title", title, "--goal", "g"]
    for s in segs[1:]:
        cmd += ["--confirm-new-segment", s]
    cmd += ["--approve"]
    r = cli(*cmd)
    assert r.returncode == 0, r.stderr
    return _json.loads(r.stdout)


class TestCourseLifecycleCLI(unittest.TestCase):
    def test_rename_move_dashboard_resume(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            c = make_course(root)
            cid = c["course_id"]
            r = cli("course", "rename", "--courses-root", root,
                    "--course-id", cid, "--title", "English Prepositions", "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["course_id"], cid)
            r = cli("course", "move", "--courses-root", root,
                    "--course-id", cid, "--category", "languages/english/development",
                    "--confirm-new-segment", "development", "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("languages/english/development", r.stdout)
            r = cli("course", "dashboard", "--courses-root", root, "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(root) / "INDEX.md").exists())
            r = cli("course", "resume", "--courses-root", root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["course"]["course_id"], cid)

    def test_record_plan_reviews_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            c = make_course(root)
            cid = c["course_id"]
            # Scope must resolve before authoritative reads: fail-closed
            # consumption (record itself stays lenient to capture evidence).
            st_path = Path(root) / c["rel_path"] / "state.json"
            st = json.loads(st_path.read_text(encoding="utf-8"))
            st["learning_scope"] = [{"id": "c1", "name": "C1", "status": "unknown",
                                     "evidence_ids": [], "due_at": None}]
            st_path.write_text(json.dumps(st) + "\n", encoding="utf-8")
            for eid, kind in (("e1", "independent_application"), ("e2", "novel_transfer")):
                r = cli("record", "--workspace", root, "--event-id", eid,
                        "--topic", cid, "--competency", "c1", "--task-type", kind,
                        "--answer", "a", "--rubric", '{"application": 2}',
                        "--expected", "r", "--feedback", "f",
                        "--course-id", cid, "--approve")
                self.assertEqual(r.returncode, 0, r.stderr)
            r = cli("course", "plan-reviews", "--courses-root", root, "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            r = cli("course", "validate", "--courses-root", root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("VALID", r.stdout)

    def test_record_duplicate_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            c = make_course(root)
            base = ["record", "--workspace", root, "--event-id", "e1",
                    "--topic", c["course_id"], "--competency", "c1",
                    "--task-type", "independent_application",
                    "--answer", "a", "--rubric", '{"application": 2}',
                    "--expected", "r", "--feedback", "f",
                    "--course-id", c["course_id"], "--approve"]
            self.assertEqual(cli(*base).returncode, 0)
            self.assertEqual(cli(*base).returncode, 2)

    def test_revoke_blocks_mutations(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            make_course(root)
            self.assertEqual(cli("course", "revoke-approval",
                                 "--courses-root", root).returncode, 0)
            r = cli("course", "dashboard", "--courses-root", root, "--approve")
            self.assertEqual(r.returncode, 2)

    def test_repair_evidence_flow(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = init_courses(d)
            make_course(root)
            with open(Path(root) / ".learnprint" / "events.jsonl", "ab") as fh:
                fh.write(b'{"broken": tru')
            r = cli("course", "repair-evidence", "--courses-root", root, "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('"status": "ok"', r.stdout)


class TestMigrateCLI(unittest.TestCase):
    def test_migrate_dry_run_and_full(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "my-learning"
            (src / "topics/t1").mkdir(parents=True)
            (src / "learner").mkdir(parents=True)
            (src / "manifest.json").write_text(json.dumps(
                {"schema_version": "1.0", "active_topic": None,
                 "profile_path": "learner/profile.json", "events_path": "events.jsonl",
                 "reviews_path": "reviews.json", "topics_dir": "topics"}))
            prof = json.loads((ROOT / "profiles/founder-default.json").read_text(encoding="utf-8"))
            (src / "learner/profile.json").write_text(json.dumps(prof))
            (src / "reviews.json").write_text(json.dumps({"schema_version": "1.0", "reviews": []}))
            (src / "topics/t1/state.json").write_text(json.dumps(
                {"schema_version": "1.0", "topic_id": "t1", "goal": "g",
                 "learning_scope": [], "syllabus": [], "question_parking_lot": [],
                 "sources": [], "last_session": None}))
            (src / "events.jsonl").write_text("", encoding="utf-8")
            dest = str(Path(d) / "Courses")
            r = cli("migrate", "--from", str(src), "--to", dest,
                    "--category", "technology/devops", "--approve", "--dry-run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(Path(dest).exists())
            r = cli("migrate", "--from", str(src), "--to", dest,
                    "--category", "technology/devops", "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(dest) / ".learnprint" / "migration-report.json").exists())


if __name__ == "__main__":
    unittest.main()
