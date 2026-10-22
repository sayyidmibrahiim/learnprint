"""Curated derived docs must preserve canonical state, evidence and manual edits."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = str(ROOT / "scripts" / "learnprint.py")


def run(*args):
    return subprocess.run([sys.executable, CLI, *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=45)


class TestCourseDocsSync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "Courses"
        created = run("course", "init", "--courses-root", self.root, "--approve")
        self.assertEqual(created.returncode, 0, created.stderr)
        created = run("course", "create", "--courses-root", self.root,
                      "--category", "technology", "--title", "DNS Lookup",
                      "--goal", "Explain cache and recursive resolver", "--approve")
        self.assertEqual(created.returncode, 0, created.stderr)
        self.entry = json.loads(created.stdout)
        self.cid = self.entry["course_id"]
        self.folder = self.root / self.entry["rel_path"]
        self.ledger = self.root / ".learnprint" / "events.jsonl"

    def _structured_plan(self):
        scope = Path(self.tmp.name) / "scope.json"
        scope.write_text(json.dumps([
            {"id": "dns-cache", "name": "Explain resolver cache",
             "status": "unknown", "evidence_ids": []},
        ]), encoding="utf-8")
        saved = run("course", "scope-set", "--courses-root", self.root,
                    "--course-id", self.cid, "--from-file", scope, "--approve")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        candidate = Path(self.tmp.name) / "units.json"
        candidate.write_text(json.dumps([{
            "unit_id": "dns-01", "title": "Cache and recursive lookup",
            "outcome": "Explain what gets cached and why",
            "requires": [], "competency_ids": ["dns-cache"],
            "hands_on": "Trace a safe local query on sample data",
            "success_check": "Predict which step uses cache",
            "practice_mode": "written",
        }]), encoding="utf-8")
        planned = run("course", "plan-set", "--courses-root", self.root,
                      "--course-id", self.cid, "--from-file", candidate,
                      "--approve")
        self.assertEqual(planned.returncode, 0, planned.stderr)

    def _preview(self):
        response = run("course", "docs-preview", "--courses-root", self.root,
                       "--course-id", self.cid)
        self.assertEqual(response.returncode, 0, response.stderr)
        return json.loads(response.stdout)

    def test_no_plan_cannot_generate_fake_syllabus(self):
        response = run("course", "docs-preview", "--courses-root", self.root,
                       "--course-id", self.cid)
        self.assertNotEqual(response.returncode, 0)
        self.assertIn("no structured plan", response.stderr.lower())

    def test_sync_scaffolds_and_preserves_ledger_and_state(self):
        self._structured_plan()
        before = (self.folder / "state.json").read_bytes()
        ledger = self.ledger.read_bytes()
        prev = self._preview()
        self.assertEqual(len(prev["files"]), 4)
        no_permission = run("course", "docs-sync", "--courses-root", self.root,
                            "--course-id", self.cid, "--preview-digest",
                            prev["preview_digest"])
        self.assertNotEqual(no_permission.returncode, 0)
        actual = run("course", "docs-sync", "--courses-root", self.root,
                     "--course-id", self.cid, "--preview-digest",
                     prev["preview_digest"], "--approve")
        self.assertEqual(actual.returncode, 0, actual.stderr)
        self.assertIn("Cache and recursive lookup",
                      (self.folder / "SYLLABUS.md").read_text(encoding="utf-8"))
        self.assertIn("flowchart TD",
                      (self.folder / "MAP.mmd").read_text(encoding="utf-8"))
        self.assertIn("Registered courses: 1",
                      (self.root / "HANDOFF.md").read_text(encoding="utf-8"))
        self.assertEqual(before, (self.folder / "state.json").read_bytes())
        self.assertEqual(ledger, self.ledger.read_bytes())
        refreshed = self._preview()
        self.assertTrue(all(v["status"] == "unchanged"
                            for v in refreshed["files"]))
        duplicate = run("course", "docs-sync", "--courses-root", self.root,
                        "--course-id", self.cid, "--preview-digest",
                        refreshed["preview_digest"], "--approve")
        self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
        self.assertEqual(json.loads(duplicate.stdout)["updated"], [])

    def test_manual_edit_preserved_and_stale_digest_rejected(self):
        self._structured_plan()
        prev = self._preview()
        (self.folder / "HANDOFF.md").write_text("Human-edited private notes\n",
                                                encoding="utf-8")
        failed = run("course", "docs-sync", "--courses-root", self.root,
                     "--course-id", self.cid, "--preview-digest",
                     prev["preview_digest"], "--approve")
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("unmanaged", failed.stderr.lower())
        self.assertEqual((self.folder / "HANDOFF.md").read_text(encoding="utf-8"),
                         "Human-edited private notes\n")
        self.assertIn("— syllabus", (self.folder / "SYLLABUS.md").read_text(
            encoding="utf-8"))

    def test_windows_crlf_scaffold_is_reviewable_without_byte_normalization(self):
        """Old Windows stubs use CRLF; preview digest must seal their actual bytes."""
        self._structured_plan()
        target = self.folder / "HANDOFF.md"
        target.write_bytes(b"# Handoff \xe2\x80\x94 DNS Lookup\r\n")
        proposed = self._preview()
        expected_sha = __import__("hashlib").sha256(target.read_bytes()).hexdigest()
        row = next(x for x in proposed["files"] if x["file"] == "HANDOFF.md")
        self.assertEqual(row["original_sha256"], expected_sha)
        actual = run("course", "docs-sync", "--courses-root", self.root,
                     "--course-id", self.cid, "--preview-digest",
                     proposed["preview_digest"], "--approve")
        self.assertEqual(actual.returncode, 0, actual.stderr)
        self.assertIn("Cache and recursive lookup",
                      (self.folder / "HANDOFF.md").read_text(encoding="utf-8"))

    def test_hardlinked_source_document_is_rejected(self):
        self._structured_plan()
        target = self.folder / "MAP.mmd"
        second_name = self.folder / "linked-copy.mmd"
        try:
            __import__("os").link(target, second_name)
        except OSError:
            self.skipTest("hardlinks unavailable on this filesystem")
        old = target.read_bytes()
        result = run("course", "docs-preview", "--courses-root",
                     self.root, "--course-id", self.cid)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular file", result.stderr)
        self.assertEqual(target.read_bytes(), old)

    def test_recheck_blocks_post_preview_changes(self):
        self._structured_plan()
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location(
            "learnprint_course_docs", ROOT / "scripts/learnprint_course_docs.py")
        import sys as _sys
        _sys.path.insert(0, str(ROOT / "scripts"))
        helper = module_from_spec(spec)
        spec.loader.exec_module(helper)
        state = json.loads((self.folder / "state.json").read_text(encoding="utf-8"))
        course = json.loads(run("course", "plan", "--courses-root", self.root,
                                "--course-id", self.cid).stdout)
        registry = json.loads((self.root / ".learnprint" / "registry.json").read_text(encoding="utf-8"))
        preview, targets = helper.preview_documents(self.root, self.folder, course, registry)
        target = self.folder / "MAP.mmd"
        target.write_text("flowchart TD\n  A --> B\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed after preview"):
            helper.verify_unchanged_targets(preview, targets)
        self.assertEqual(state["course_id"], self.cid)

    def test_refuse_symlink_document(self):
        self._structured_plan()
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("private", encoding="utf-8")
        target = self.folder / "MAP.mmd"
        target.unlink()
        try:
            target.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks denied on this Windows host")
        failed = run("course", "docs-preview", "--courses-root", self.root,
                     "--course-id", self.cid)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("linked", failed.stderr.lower())
        self.assertEqual(outside.read_text(encoding="utf-8"), "private")


if __name__ == "__main__":
    unittest.main()
