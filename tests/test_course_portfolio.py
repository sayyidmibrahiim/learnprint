"""Portfolio preview/export regression tests, disposable roots only."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import learnprint_portfolio as portfolio


class TestPortfolio(unittest.TestCase):
    CID = "e5230ed4-8481-425f-882a-332a8718d6cf"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / "Courses"
        self.course = self.root / "technology" / "sql-lab"
        self.course.mkdir(parents=True)
        self.lab = self.course / "hands-on"
        self.lab.mkdir()
        (self.lab / "query.sql").write_text("SELECT count(*) FROM invoices;\n", encoding="utf-8")
        (self.course / "state.json").write_text(json.dumps({
            "schema_version": "1.0", "course_id": self.CID,
            "learning_scope": [{"id": "a", "name": "SQL counts",
                                "status": "unknown", "evidence_ids": []}]}), encoding="utf-8")
        metadata = self.root / ".learnprint"
        metadata.mkdir()
        (metadata / "registry.json").write_text(json.dumps({
            "schema_version": "1.0",
            "courses": [{"course_id": self.CID, "title": "SQL Lab",
                         "rel_path": "technology/sql-lab"}]}), encoding="utf-8")
        (metadata / "events.jsonl").write_text("private learner evidence\n", encoding="utf-8")
        self.manifest = base / "publication.json"
        self.data = {"schema_version": "1", "course_id": self.CID,
                     "visibility": "public", "title": "SQL demonstration",
                     "summary": "Counting records using a reproducible query.",
                     "artifacts": [{"path": "hands-on/query.sql", "origin": "learner_authored"}],
                     "achievements": [{"claim": "Wrote a counting query",
                                       "evidence_path": "hands-on/query.sql",
                                       "basis": "self_reported"}]}
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def preview(self):
        return portfolio.prepare(self.course, self.CID, self.manifest)

    def test_read_only_and_public_output(self):
        private = (self.root / ".learnprint" / "events.jsonl").read_bytes()
        p, output = self.preview()
        self.assertTrue(p["publishable"])
        self.assertEqual(len(output), 4)
        self.assertNotIn(private, list(output.values()))
        self.assertIn(b"not an accredited certificate", output["README.md"])
        self.assertEqual(private, (self.root / ".learnprint" / "events.jsonl").read_bytes())

    def test_private_mode_refuses_export(self):
        self.data["visibility"] = "private"
        self.save()
        p, output = self.preview()
        self.assertFalse(p["publishable"])
        self.assertEqual(output, {})
        with self.assertRaisesRegex(ValueError, "private"):
            portfolio.export(self.course, self.CID, self.manifest,
                             Path(self.tmp.name) / "private-output", "no", True)

    def test_export_is_approval_and_digest_gated(self):
        p, _ = self.preview()
        dest = Path(self.tmp.name) / "export"
        with self.assertRaisesRegex(ValueError, "approve"):
            portfolio.export(self.course, self.CID, self.manifest, dest,
                             p["preview_digest"], False)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            portfolio.export(self.course, self.CID, self.manifest, dest, "outdated", True)
        self.assertFalse(dest.exists())
        result = portfolio.export(self.course, self.CID, self.manifest, dest,
                                  p["preview_digest"], True)
        self.assertEqual(result["status"], "exported")
        self.assertFalse(result["git_published"])
        self.assertTrue((dest / "hands-on" / "query.sql").exists())
        self.assertFalse((dest / "state.json").exists())
        with self.assertRaisesRegex(ValueError, "overwrite"):
            portfolio.export(self.course, self.CID, self.manifest, dest,
                             p["preview_digest"], True)

    def test_offline_revisions_are_immutable_and_require_fresh_consent(self):
        # Offline revision folders are separate disposable destinations.
        # This does not authorize versioned public Git snapshots.
        private_state = (self.course / "state.json").read_bytes()
        private_ledger = (self.root / ".learnprint" / "events.jsonl").read_bytes()
        first_preview, _ = self.preview()
        first = Path(self.tmp.name) / "offline-revision-1"
        portfolio.export(self.course, self.CID, self.manifest, first,
                         first_preview["preview_digest"], True)
        first_bytes = {path.relative_to(first).as_posix(): path.read_bytes()
                       for path in first.rglob("*") if path.is_file()}

        (self.lab / "query.sql").write_text("SELECT count(*) FROM payments;\n",
                                             encoding="utf-8")
        second = Path(self.tmp.name) / "offline-revision-2"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            portfolio.export(self.course, self.CID, self.manifest, second,
                             first_preview["preview_digest"], True)
        self.assertFalse(second.exists())

        second_preview, _ = self.preview()
        self.assertNotEqual(first_preview["preview_digest"],
                            second_preview["preview_digest"])
        with self.assertRaisesRegex(ValueError, "approve"):
            portfolio.export(self.course, self.CID, self.manifest, second,
                             second_preview["preview_digest"], False)
        self.assertFalse(second.exists())
        portfolio.export(self.course, self.CID, self.manifest, second,
                         second_preview["preview_digest"], True)
        self.assertEqual((second / "hands-on" / "query.sql").read_text(encoding="utf-8"),
                         "SELECT count(*) FROM payments;\n")
        self.assertEqual({path.relative_to(first).as_posix(): path.read_bytes()
                          for path in first.rglob("*") if path.is_file()}, first_bytes)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            portfolio.export(self.course, self.CID, self.manifest, first,
                             second_preview["preview_digest"], True)
        self.assertEqual((self.course / "state.json").read_bytes(), private_state)
        self.assertEqual((self.root / ".learnprint" / "events.jsonl").read_bytes(),
                         private_ledger)

    def test_changed_source_invalidates_digest(self):
        p, _ = self.preview()
        (self.lab / "query.sql").write_text("SELECT 1;\n", encoding="utf-8")
        dest = Path(self.tmp.name) / "outdated"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            portfolio.export(self.course, self.CID, self.manifest, dest,
                             p["preview_digest"], True)
        self.assertFalse(dest.exists())

    def test_rejects_private_paths_and_traversal(self):
        for name in ("../state.json", "hands-on/../state.json", "state.json",
                     "hands-on/.env", "hands-on/events.jsonl",
                     "hands-on/private.key", "hands-on/CON.txt",
                     "hands-on/folder\\query.sql", "hands-on/folder\nquery.sql"):
            with self.subTest(path=name):
                self.data["artifacts"][0]["path"] = name
                self.save()
                with self.assertRaises(ValueError):
                    self.preview()

    def test_windows_trailing_dot_aliases_are_rejected(self):
        # Windows may resolve a trailing-dot path segment to a different name.
        # Validate the manifest path itself, independent of host filesystem.
        self.assertEqual(portfolio._safe_relative("hands-on/normal/query.sql"),
                         ["hands-on", "normal", "query.sql"])
        for rel in ("hands-on/alias./query.sql",
                    "hands-on/alias../query.sql",
                    "hands-on/alias.../query.sql"):
            with self.subTest(path=rel):
                with self.assertRaisesRegex(ValueError, "trailing dot"):
                    portfolio._safe_relative(rel)

    def test_rejects_sensitive_text_patterns(self):
        text_cases = ["api" + "_key = 'not-a-real-private-value'\n",
                      "Contact" + " user@private.example\n",
                      "Read " + "/home/example/private/file.txt\n",
                      "-----BEGIN " + "PRIVATE KEY-----\n"]
        for content in text_cases:
            with self.subTest(case=content[:12]):
                (self.lab / "query.sql").write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "private data"):
                    self.preview()

    def test_symlinks_are_rejected(self):
        target = Path(self.tmp.name) / "external.sql"
        target.write_text("SELECT 2;\n", encoding="utf-8")
        link = self.lab / "query.sql"
        link.unlink()
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("host cannot create symlinks")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.preview()

    def _simulate_reparse_attribute(self, target):
        # Cross-platform synthetic Windows FILE_ATTRIBUTE_REPARSE_POINT fixture.
        # A junction may have directory mode while still redirecting traversal.
        real_lstat = Path.lstat

        def fake_lstat(path, *args, **kwargs):
            info = real_lstat(path, *args, **kwargs)
            if portfolio._trusted_system_alias(path) == portfolio._trusted_system_alias(target):
                return SimpleNamespace(
                    st_mode=info.st_mode,
                    st_file_attributes=getattr(info, "st_file_attributes", 0) | 0x400)
            return info

        return mock.patch.object(Path, "lstat", fake_lstat)

    def _make_real_windows_junction(self, link, target):
        # All paths must stay inside this disposable TemporaryDirectory.
        root = Path(self.tmp.name).resolve()
        self.assertTrue((link.parent.resolve() / link.name).is_relative_to(root))
        self.assertTrue(target.resolve().is_relative_to(root))
        command = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True, text=True, timeout=20)
        if command.returncode:
            self.skipTest("Windows junction creation unavailable in temporary fixture: "
                          + command.stderr[:160])
        # os.rmdir removes the junction itself, not its target.
        self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)
        self.assertTrue(os.path.lexists(link))
        self.assertTrue(getattr(link.lstat(), "st_file_attributes", 0) & 0x400,
                        "real Windows junction must be a reparse point")

    @unittest.skipUnless(os.name == "nt", "real junctions require Windows")
    def test_real_windows_junction_source_artifact_rejected(self):
        target = Path(self.tmp.name) / "synthetic-outside-source"
        target.mkdir()
        (target / "query.sql").write_text("SELECT 123;\n", encoding="utf-8")
        link = self.lab / "junction"
        self._make_real_windows_junction(link, target)
        self.data["artifacts"][0]["path"] = "hands-on/junction/query.sql"
        self.data["achievements"][0]["evidence_path"] = "hands-on/junction/query.sql"
        self.save()
        with self.assertRaisesRegex(ValueError, "reparse|symlink"):
            self.preview()
        self.assertEqual((target / "query.sql").read_text(encoding="utf-8"),
                         "SELECT 123;\n")

    @unittest.skipUnless(os.name == "nt", "real junctions require Windows")
    def test_real_windows_junction_manifest_parent_rejected(self):
        target = Path(self.tmp.name) / "synthetic-manifest-parent"
        target.mkdir()
        (target / "publication.json").write_bytes(self.manifest.read_bytes())
        link = Path(self.tmp.name) / "manifest-junction"
        self._make_real_windows_junction(link, target)
        self.manifest = link / "publication.json"
        with self.assertRaisesRegex(ValueError, "reparse|symlink"):
            self.preview()

    @unittest.skipUnless(os.name == "nt", "real junctions require Windows")
    def test_real_windows_junction_export_parent_rejected(self):
        preview, _ = self.preview()
        target = Path(self.tmp.name) / "synthetic-export-parent"
        target.mkdir()
        link = Path(self.tmp.name) / "export-junction"
        self._make_real_windows_junction(link, target)
        with self.assertRaisesRegex(ValueError, "reparse|symlink"):
            portfolio.export(self.course, self.CID, self.manifest,
                             link / "snapshot", preview["preview_digest"], True)
        self.assertFalse((target / "snapshot").exists())

    def test_reparse_source_directory_is_rejected(self):
        with self._simulate_reparse_attribute(self.lab):
            with self.assertRaisesRegex(ValueError, "reparse"):
                self.preview()

    def test_reparse_artifact_file_is_rejected(self):
        with self._simulate_reparse_attribute(self.lab / "query.sql"):
            with self.assertRaisesRegex(ValueError, "reparse"):
                self.preview()

    def test_reparse_manifest_is_rejected(self):
        with self._simulate_reparse_attribute(self.manifest):
            with self.assertRaisesRegex(ValueError, "manifest"):
                self.preview()

    def _relocate_manifest_to_separate_parent(self):
        # Do not reuse the source-course ancestor; source checks already
        # validate that tree and would mask this independent manifest bug.
        parent = Path(self.tmp.name) / "manifest-location"
        parent.mkdir()
        self.manifest = parent / "publication.json"
        self.save()
        return parent

    def test_reparse_manifest_parent_is_rejected(self):
        # A regular manifest under a Windows junction must fail closed.
        parent = self._relocate_manifest_to_separate_parent()
        with self._simulate_reparse_attribute(parent):
            with self.assertRaisesRegex(ValueError, "reparse"):
                self.preview()

    def test_symlink_manifest_parent_is_rejected(self):
        # A synthetic link avoids Windows developer-mode/admin requirements.
        parent = self._relocate_manifest_to_separate_parent()
        original = Path.is_symlink

        def fake_is_symlink(path):
            return (portfolio._trusted_system_alias(path) == portfolio._trusted_system_alias(parent)
                    or original(path))

        with mock.patch.object(Path, "is_symlink", fake_is_symlink):
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.preview()

    def test_hardlinked_manifest_to_private_metadata_is_rejected(self):
        # A manifest hardlinked to private metadata is still a regular file.
        # Never read/share that inode through an apparently approved path.
        alias = self.root / ".learnprint" / "portfolio-metadata.json"
        original = self.manifest.read_bytes()
        try:
            os.link(self.manifest, alias)
        except OSError:
            self.skipTest("host cannot create hardlinks in disposable workspace")
        self.assertGreater(self.manifest.stat().st_nlink, 1)
        with self.assertRaisesRegex(ValueError, "multiply linked|hardlink"):
            self.preview()
        self.assertEqual(alias.read_bytes(), original)

    def test_manifest_replacement_during_open_is_rejected(self):
        # An identical byte-for-byte replacement is a new inode. A consented
        # preview must not silently read a different file after path preflight.
        original_open = os.open
        original_bytes = self.manifest.read_bytes()
        moved = Path(self.tmp.name) / "manifest-before-race.json"
        changed = []

        def replace_before_open(path, flags, *args, **kwargs):
            if Path(path) == self.manifest and not changed:
                self.manifest.rename(moved)
                self.manifest.write_bytes(original_bytes)
                changed.append(True)
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(portfolio.os, "open", side_effect=replace_before_open):
            with self.assertRaisesRegex(ValueError, "manifest changed identity"):
                self.preview()
        self.assertEqual(changed, [True])
        self.assertEqual(moved.read_bytes(), original_bytes)

    def test_source_parent_swap_with_same_file_inode_is_rejected(self):
        # Race a parent directory rename after checks, retaining the SAME file
        # inode and bytes. Leaf-only identity verification is insufficient.
        original_open = os.open
        original_file = self.lab / "query.sql"
        original_bytes = original_file.read_bytes()
        moved = self.course / "hands-on-old"
        triggered = []

        def change_parent_before_open(path, flags, *args, **kwargs):
            if (portfolio._trusted_system_alias(path) == portfolio._trusted_system_alias(original_file)
                    and not triggered):
                self.lab.rename(moved)
                self.lab.mkdir()
                (moved / "query.sql").rename(original_file)
                triggered.append(True)
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(portfolio.os, "open",
                               side_effect=change_parent_before_open):
            with self.assertRaisesRegex(ValueError, "directory chain"):
                self.preview()
        self.assertEqual(triggered, [True])
        self.assertEqual(original_file.read_bytes(), original_bytes)

    def test_manifest_parent_swap_with_same_file_inode_is_rejected(self):
        parent = self._relocate_manifest_to_separate_parent()
        original_bytes = self.manifest.read_bytes()
        original_open = os.open
        moved = Path(self.tmp.name) / "manifest-old-parent"
        triggered = []

        def change_parent_before_open(path, flags, *args, **kwargs):
            if Path(path) == self.manifest and not triggered:
                parent.rename(moved)
                parent.mkdir()
                (moved / "publication.json").rename(self.manifest)
                triggered.append(True)
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(portfolio.os, "open",
                               side_effect=change_parent_before_open):
            with self.assertRaisesRegex(ValueError, "directory chain"):
                self.preview()
        self.assertEqual(triggered, [True])
        self.assertEqual(self.manifest.read_bytes(), original_bytes)

    def test_export_parent_swapped_before_staging_is_rejected(self):
        # The target parent can change between preflight and temp staging.
        # This test stays entirely within the disposable fixture root.
        preview, _ = self.preview()
        parent = Path(self.tmp.name) / "reviewed-output-parent"
        parent.mkdir()
        target = parent / "snapshot"
        moved = Path(self.tmp.name) / "original-output-parent"
        real_mkdtemp = tempfile.mkdtemp
        swaps = []

        def replace_parent_before_stage(*args, **kwargs):
            parent.rename(moved)
            parent.mkdir()
            swaps.append(True)
            return real_mkdtemp(*args, **kwargs)

        with mock.patch.object(portfolio.tempfile, "mkdtemp",
                               side_effect=replace_parent_before_stage):
            with self.assertRaisesRegex(ValueError, "directory chain"):
                portfolio.export(self.course, self.CID, self.manifest, target,
                                 preview["preview_digest"], True)
        self.assertEqual(swaps, [True])
        self.assertFalse(target.exists())

    def test_reparse_export_parent_is_rejected(self):
        preview, _ = self.preview()
        parent = Path(self.tmp.name) / "outside-export"
        parent.mkdir()
        with self._simulate_reparse_attribute(parent):
            with self.assertRaisesRegex(ValueError, "reparse"):
                portfolio.export(self.course, self.CID, self.manifest,
                                 parent / "snapshot", preview["preview_digest"], True)
        self.assertFalse((parent / "snapshot").exists())

    def test_hardlinked_artifact_to_private_record_is_rejected(self):
        # A hardlink is a regular file, not a symlink. A harmless-looking
        # synthetic private record can otherwise pass heuristic text scanning.
        source = self.root / ".learnprint" / "events.jsonl"
        original = source.read_bytes()
        selected = self.lab / "query.sql"
        selected.unlink()
        try:
            os.link(source, selected)
        except OSError:
            self.skipTest("host cannot create hardlinks in temporary workspace")
        self.assertGreater(source.stat().st_nlink, 1)
        with self.assertRaisesRegex(ValueError, "hardlink|multiply linked"):
            self.preview()
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse((Path(self.tmp.name) / "export").exists())

    def test_hardlink_substituted_after_preview_blocks_export(self):
        preview, _ = self.preview()
        source = self.root / ".learnprint" / "events.jsonl"
        selected = self.lab / "query.sql"
        source.write_bytes(selected.read_bytes())
        selected.unlink()
        try:
            os.link(source, selected)
        except OSError:
            self.skipTest("host cannot create hardlinks in temporary workspace")
        target = Path(self.tmp.name) / "hardlink-export"
        with self.assertRaisesRegex(ValueError, "multiply linked"):
            portfolio.export(self.course, self.CID, self.manifest, target,
                             preview["preview_digest"], True)
        self.assertFalse(target.exists())

    def test_manifest_validation(self):
        self.data["achievements"][0]["evidence_path"] = "hands-on/missing.sql"
        self.save()
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.preview()
        self.data["course_id"] = "mismatch"
        self.save()
        with self.assertRaisesRegex(ValueError, "course_id"):
            self.preview()

    def test_refuses_achievement_without_provenance(self):
        self.data["achievements"][0]["basis"] = "unknown"
        self.save()
        with self.assertRaisesRegex(ValueError, "basis"):
            self.preview()

    def test_case_colliding_artifacts_are_rejected(self):
        (self.lab / "QUERY.sql").write_text("SELECT 1;\n", encoding="utf-8")
        self.data["artifacts"].append({"path": "hands-on/QUERY.sql",
                                       "origin": "learner_authored"})
        self.save()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.preview()

    def test_unreviewed_markup_is_rejected(self):
        self.data["summary"] = "Find more details at [external](url)"
        self.save()
        with self.assertRaisesRegex(ValueError, "markup"):
            self.preview()

    def test_publication_metadata_cannot_inject_markdown_provenance(self):
        # These fields are copied verbatim into public README/EVIDENCE files.
        original = json.loads(json.dumps(self.data))
        unsafe = [
            ("summary", "My practice" + chr(10) * 2 +
             "## Accredited Certificate" + chr(10) + "Issuer: University"),
            ("summary", "**Independent certification verified**"),
            ("title", "SQL Lab `verified`"),
            ("claim", "Wrote SQL | human_reviewed | hands-on/query.sql"),
        ]
        for field, value in unsafe:
            with self.subTest(field=field, value=value):
                try:
                    if field == "claim":
                        self.data["achievements"][0]["claim"] = value
                    else:
                        self.data[field] = value
                    self.save()
                    with self.assertRaisesRegex(ValueError, "markup"):
                        self.preview()
                finally:
                    self.data = json.loads(json.dumps(original))
                    self.save()
        preview, output = self.preview()
        self.assertTrue(preview["publishable"])
        self.assertIn(b"Wrote a counting query", output["EVIDENCE.md"])

    def test_invalid_registry_path_fails_closed(self):
        reg_path = self.root / ".learnprint" / "registry.json"
        registry = json.loads(reg_path.read_text(encoding="utf-8"))
        registry["courses"][0]["rel_path"] = "../outside"
        reg_path.write_text(json.dumps(registry), encoding="utf-8")
        command = [sys.executable, str(ROOT / "scripts" / "learnprint.py"),
                   "course", "portfolio-preview", "--course-id", self.CID,
                   "--manifest", str(self.manifest), "--courses-root", str(self.root)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2)

    def test_cli_export_to_public_uuid_snapshot(self):
        arguments = [sys.executable, str(ROOT / "scripts" / "learnprint.py"),
                     "course", "portfolio-preview", "--course-id", self.CID,
                     "--manifest", str(self.manifest), "--courses-root", str(self.root)]
        preview = subprocess.run(arguments, capture_output=True, text=True, timeout=30)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        seal = json.loads(preview.stdout)["preview_digest"]
        public = self.root / "public" / self.CID
        command = [sys.executable, str(ROOT / "scripts" / "learnprint.py"),
                   "course", "portfolio-export", "--course-id", self.CID,
                   "--manifest", str(self.manifest), "--courses-root", str(self.root),
                   "--output-dir", str(public), "--preview-digest", seal]
        denied = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(denied.returncode, 0)
        self.assertFalse(public.parent.exists())
        allowed = subprocess.run(command + ["--approve"], capture_output=True,
                                 text=True, timeout=30)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertTrue((public / "PUBLICATION.json").is_file())
        self.assertTrue((self.course / "state.json").is_file())

    def test_cli_round_trip(self):
        basic = [sys.executable, str(ROOT / "scripts" / "learnprint.py"),
                 "course", "portfolio-preview", "--course-id", self.CID,
                 "--manifest", str(self.manifest), "--courses-root", str(self.root)]
        prev = subprocess.run(basic, capture_output=True, text=True, timeout=30)
        self.assertEqual(prev.returncode, 0, prev.stderr)
        obj = json.loads(prev.stdout)
        target = Path(self.tmp.name) / "cli-out"
        command = [sys.executable, str(ROOT / "scripts" / "learnprint.py"),
                   "course", "portfolio-export", "--course-id", self.CID,
                   "--manifest", str(self.manifest), "--courses-root", str(self.root),
                   "--output-dir", str(target), "--preview-digest", obj["preview_digest"]]
        denied = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(denied.returncode, 0)
        allowed = subprocess.run(command + ["--approve"], capture_output=True,
                                 text=True, timeout=30)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertTrue((target / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
