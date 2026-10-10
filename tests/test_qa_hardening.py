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


if __name__ == "__main__":
    unittest.main()
