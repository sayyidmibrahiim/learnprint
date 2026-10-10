import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("learnprint", ROOT / "scripts/learnprint.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def args(**kw):
    base = {"courses_root": None, "approve": True, "alias": [], "confirm_new_segment": [],
            "repair": False, "dry_run": False, "update_path": False, "query": "",
            "category": "", "title": "", "goal": "", "course_id": ""}
    base.update(kw)
    return type("Args", (), base)()


def run(fn, a):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(a)
    return rc, buf.getvalue()


def fresh_courses(d):
    return Path(d) / "Courses"


class TestCourseInit(unittest.TestCase):
    def test_init_creates_tree(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = fresh_courses(d)
            a = args(courses_root=str(root))
            rc, _ = run(mod.cmd_course_init, a)
            self.assertEqual(rc, 0)
            lp = root / ".learnprint"
            for f in ("registry.json", "approval.json", "config.json",
                      "learner/profile.json", "events.jsonl", "reviews.json"):
                self.assertTrue((lp / f).exists(), f)
            self.assertTrue((root / "HANDOFF.md").exists())
            reg = mod.registry_read(root)
            self.assertEqual(reg["courses"], [])

    def test_init_requires_approve(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                mod.cmd_course_init(args(courses_root=str(fresh_courses(d)), approve=False))

    def test_init_refuses_when_initialized(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = fresh_courses(d)
            mod.cmd_course_init(args(courses_root=str(root)))
            with self.assertRaises(ValueError):
                mod.cmd_course_init(args(courses_root=str(root)))


class TestCourseCLI(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.root = fresh_courses(self._tmp.name)
        mod.cmd_course_init(args(courses_root=str(self.root)))

    def tearDown(self):
        self._tmp.cleanup()

    def mk(self, category, title, **kw):
        reg = mod.registry_read(self.root)
        ok, gate = mod.routing.validate_classification(category, reg)
        flags = []
        if ok and isinstance(gate, dict):
            flags = [v["segment"] for v in gate.get("segments", [])
                     if v["verdict"] == "new-needs-confirmation"]
        a = args(courses_root=str(self.root), category=category, title=title,
                 goal=kw.get("goal", "g"), alias=kw.get("alias", []),
                 confirm_new_segment=flags)
        rc, out = run(mod.cmd_course_create, a)
        self.assertEqual(rc, 0)
        return json.loads(out)

    def test_create_requires_approval_and_flag(self):
        with self.assertRaises(ValueError):
            mod.cmd_course_create(args(courses_root=str(self.root), category="languages/english",
                                       title="T", goal="g", approve=False))
        mod.cmd_course_revoke_approval(args(courses_root=str(self.root)))
        with self.assertRaises(ValueError):
            mod.cmd_course_create(args(courses_root=str(self.root), category="languages/english",
                                       title="T", goal="g", approve=True))

    def test_resolve_list_resume(self):
        c = self.mk("languages/english/grammar", "in on at")
        rc, out = run(mod.cmd_course_resolve, args(courses_root=str(self.root), query="in/on/at"))
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["course"]["course_id"], c["course_id"])
        rc, out = run(mod.cmd_course_list, args(courses_root=str(self.root)))
        self.assertEqual(len(json.loads(out)), 1)
        rc, out = run(mod.cmd_course_resume, args(courses_root=str(self.root)))
        # created course became active
        self.assertEqual(json.loads(out)["course"]["course_id"], c["course_id"])

    def test_record_into_courses_ledger(self):
        c = self.mk("languages/english/grammar", "in on at")
        a = args(courses_root=None, workspace=str(self.root), event_id="e1",
                 topic=c["course_id"], competency="c1",
                 task_type="independent_application", answer="a",
                 rubric='{"application": 2}', expected="r", feedback="f",
                 grader="ai_reviewed", help="none", confidence=None,
                 approve=True, course_id=c["course_id"], grader_source=None,
                 confirms=None, corrects=None, corroborates=None)
        self.assertEqual(mod.cmd_record(a), 0)
        ledger = mod.ledger_read_trusted(self.root / ".learnprint" / "events.jsonl",
                                         workspace_root=self.root)
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["course_id"], c["course_id"])
        reg = mod.registry_read(self.root)
        self.assertIsNotNone(reg["courses"][0]["last_activity"])
        # duplicate refused
        with self.assertRaises(ValueError):
            mod.cmd_record(a)

    def test_dashboard_regenerates_index(self):
        self.mk("languages/english/grammar", "in on at")
        rc, _ = run(mod.cmd_course_dashboard, args(courses_root=str(self.root)))
        self.assertEqual(rc, 0)
        text = (self.root / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("in on at", text)
        self.assertIn("[no-evidence]", text)

    def test_dashboard_refuses_damaged_ledger(self):
        self.mk("languages/english/grammar", "in on at")
        with (self.root / ".learnprint" / "events.jsonl").open("ab") as fh:
            fh.write(b'{"broken": tru')
        with self.assertRaises(mod.LedgerDamage):
            mod.cmd_course_dashboard(args(courses_root=str(self.root)))

    def test_validate_and_repair(self):
        self.mk("languages/english/grammar", "in on at")
        rc, out = run(mod.cmd_course_validate, args(courses_root=str(self.root)))
        self.assertEqual(rc, 0)
        self.assertIn("VALID", out)
        # orphan dir detected, adopted on --repair
        orphan = self.root / "languages/english/vocabulary/words"
        orphan.mkdir(parents=True)
        (orphan / "state.json").write_text("{}", encoding="utf-8")
        rc, out = run(mod.cmd_course_validate, args(courses_root=str(self.root)))
        self.assertEqual(rc, 2)
        rc, out = run(mod.cmd_course_validate,
                      args(courses_root=str(self.root), repair=True, approve=True))
        self.assertEqual(rc, 0)
        self.assertIn("adopted orphan", out)

    def test_repair_evidence_flow(self):
        self.mk("languages/english/grammar", "in on at")
        with (self.root / ".learnprint" / "events.jsonl").open("ab") as fh:
            fh.write(b'{"broken": tru')
        rc, out = run(mod.cmd_course_repair_evidence, args(courses_root=str(self.root)))
        self.assertEqual(rc, 0)
        rep = json.loads(out)
        self.assertEqual(rep["status"], "ok")

    def test_plan_reviews_writes_queue(self):
        self.mk("languages/english/grammar", "in on at")
        rc, out = run(mod.cmd_course_plan_reviews,
                      args(courses_root=str(self.root), dry_run=True))
        self.assertEqual(rc, 0)
        self.assertIn("reviews", json.loads(out))

    def test_revoke_blocks_mutations(self):
        mod.cmd_course_revoke_approval(args(courses_root=str(self.root)))
        with self.assertRaises(ValueError):
            mod.cmd_course_dashboard(args(courses_root=str(self.root)))


if __name__ == "__main__":
    unittest.main()
