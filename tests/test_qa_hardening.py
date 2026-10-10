"""QA post-merge hardening regression tests (Phase B-E).

Seams: public module functions, CLI subprocess boundary, filesystem
artifacts. No source-text assertions, no private-name coupling.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import learnprint as mod


def make_workspace(d):
    root = Path(d) / "Courses"
    rc = mod.cmd_course_init(_ns(approve=True, courses_root=str(root)))
    assert rc == 0
    return root


class _ns:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def create_kwargs(root, category="languages/english/grammar", title="in on at"):
    return dict(courses_root=root, category_path=category, title=title,
                goal="g", aliases=(),
                confirm_new_segments=("english", "grammar"))


class TestB1CreateCrashConsistency(unittest.TestCase):
    def test_state_registry_coherent_after_create(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(**create_kwargs(root))
            st = json.loads((root / entry["rel_path"] / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(st["course_id"], entry["course_id"])
            self.assertIsNotNone(st["course_id"])

    def test_corrupt_orphan_state_refuses_create(self):
        """RED: pre-existing dir with corrupt state.json must NOT be
        adopted into the registry with a swallowed state-update error."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            # Predict the directory course_create will use.
            from learnprint_routing import slugify
            slug = slugify("in on at")
            orphan = root / "languages/english/grammar" / slug
            orphan.mkdir(parents=True)
            (orphan / "state.json").write_text("{corrupt json", encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.course_create(**create_kwargs(root))
            # Registry must NOT advertise the corrupt course.
            reg = mod.registry_read(root)
            self.assertEqual(reg.get("courses", []), [])

    def test_interrupted_create_retry_converges_to_single_course(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            from learnprint_routing import slugify
            import uuid
            slug = slugify("in on at")
            orphan = root / "languages/english/grammar" / slug
            orphan.mkdir(parents=True)
            orphan_id = str(uuid.uuid4())
            (orphan / "state.json").write_text(json.dumps(
                {"schema_version": "1.0", "course_id": orphan_id, "goal": "g",
                 "learning_scope": [], "sources": []}), encoding="utf-8")
            entry = mod.course_create(**create_kwargs(root))
            self.assertEqual(entry["course_id"], orphan_id)
            reg = mod.registry_read(root)
            self.assertEqual(len(reg["courses"]), 1)


class TestB2RegistryIntegrity(unittest.TestCase):
    def test_backup_preserves_prior_state(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            mod.course_create(**create_kwargs(root, title="course one"))
            prior = (root / ".learnprint" / "registry.json").read_bytes()
            mod.course_create(**create_kwargs(root, title="course two"))
            bak_raw = (root / ".learnprint" / "registry.json.bak").read_bytes()
            bak = json.loads(bak_raw)
            self.assertEqual(len(bak["courses"]), 1)
            self.assertEqual(json.loads(prior)["courses"], bak["courses"])

    def test_missing_registry_in_initialized_workspace_raises(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            (root / ".learnprint" / "registry.json").unlink()
            with self.assertRaises(ValueError):
                mod.registry_read(root)

    def test_corrupt_registry_raises_actionable_error(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            (root / ".learnprint" / "registry.json").write_text("{nope", encoding="utf-8")
            try:
                mod.registry_read(root)
            except ValueError as exc:
                self.assertIn("registry", str(exc).lower())
            else:
                self.fail("expected ValueError")

    def test_validate_detects_state_registry_identity_mismatch(self):
        import tempfile, uuid, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(**create_kwargs(root))
            st_path = root / entry["rel_path"] / "state.json"
            st = json.loads(st_path.read_text(encoding="utf-8"))
            st["course_id"] = str(uuid.uuid4())
            st_path.write_text(json.dumps(st), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_validate(
                    _ns(repair=False, approve=False, courses_root=str(root)))
            self.assertEqual(rc, 2)
            self.assertIn("mismatch", buf.getvalue().lower())

    def test_validate_flags_duplicate_course_ids(self):
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            mod.course_create(**create_kwargs(root, title="course one"))
            mod.course_create(**create_kwargs(root, title="course two"))
            reg = mod.registry_read(root)
            reg["courses"][1]["course_id"] = reg["courses"][0]["course_id"]
            mod.registry_write(root, reg)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_validate(
                    _ns(repair=False, approve=False, courses_root=str(root)))
            self.assertEqual(rc, 2)
            self.assertIn("duplicate", buf.getvalue().lower())


def valid_event(eid="e1", topic="t", comp="c1"):
    return {"event_id": eid, "date": "2026-10-11T10:00:00+00:00",
            "topic_id": topic, "competency_id": comp,
            "task_type": "independent_application",
            "observed_answer": "a", "expected_reasoning": "r",
            "help_level": "none", "rubric": {"application": 2},
            "feedback": "f", "grader": "ai_reviewed",
            "evidence_origin": "observed_response"}


class TestB3LedgerTerminatorSafety(unittest.TestCase):
    def _ledger(self, root):
        return root / ".learnprint" / "events.jsonl"

    def test_diagnose_flags_missing_terminal_newline(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event()) ).encode("utf-8"))  # no \n
            diag = mod.ledger_diagnose(lp, workspace_root=root)
            self.assertEqual(diag["status"], "damaged")

    def test_trusted_read_rejects_unterminated_ledger(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event())).encode("utf-8"))
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_read_trusted(lp, workspace_root=root)

    def test_append_refuses_unterminated_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event())).encode("utf-8"))
            with self.assertRaises(mod.LedgerDamage):
                mod.append_event_line(lp, json.dumps(valid_event("e2")))

    def test_repair_restores_terminator_preserving_record(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event())).encode("utf-8"))
            report = mod.ledger_repair_truncate_partial_tail(lp)
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["records"], 1)
            self.assertTrue(lp.read_bytes().endswith(b"\n"))
            recs = mod.ledger_read_trusted(lp, workspace_root=root)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["event_id"], "e1")

    def test_record_refuses_then_succeeds_after_repair(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(**create_kwargs(root))
            lp = self._ledger(root)
            # Seed one valid event via the trusted path, then strip terminator
            # to simulate an interrupted write.
            mod.append_event_line(lp, json.dumps(valid_event("e0", topic=entry["course_id"])))
            raw = lp.read_bytes()
            lp.write_bytes(raw.rstrip(b"\n"))
            args = _ns(workspace=str(root), event_id="e1", topic=entry["course_id"],
                       competency="c1", task_type="independent_application",
                       answer="a", rubric='{"application": 2}', expected="r",
                       feedback="f", approve=True, course_id=entry["course_id"],
                       help="none", confidence=None, grader="ai_reviewed",
                       confirms=None, corrects=None, corroborates=None,
                       grader_source=None)
            with self.assertRaises(mod.LedgerDamage):
                mod._cmd_record_courses(args, root)
            mod.ledger_repair_truncate_partial_tail(lp)
            self.assertEqual(mod._cmd_record_courses(args, root), 0)
            recs = mod.ledger_read_trusted(lp, workspace_root=root)
            self.assertEqual([r["event_id"] for r in recs], ["e0", "e1"])


if __name__ == "__main__":
    unittest.main()
