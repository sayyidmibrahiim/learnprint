"""Integration tests for indexed public course policy, all in temporary Git repos."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import learnprint_portfolio as portfolio
import learnprint_publish_guard as guard

IGNORE = """\
/Courses/*
!/Courses/public/
/Courses/public/*
!/Courses/public/*/
"""

class TestIndexedCourseGuard(unittest.TestCase):
    CID = "e5230ed4-8481-425f-882a-332a8718d6cf"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init")
        (self.repo / ".gitignore").write_text(
            (ROOT / ".gitignore").read_text(encoding="utf-8"), encoding="utf-8")
        self.courses = self.repo / "Courses"
        self.private = self.courses / "technology" / "sql-lab"
        self.private.mkdir(parents=True)
        (self.private / "state.json").write_text("private\n", encoding="utf-8")
        (self.courses / ".learnprint").mkdir()
        (self.courses / ".learnprint" / "events.jsonl").write_text("private\n", encoding="utf-8")
        self.lab = self.private / "hands-on"
        self.lab.mkdir()
        (self.lab / "query.sql").write_text("SELECT count(*) FROM records;\n", encoding="utf-8")
        self.manifest = Path(self.tmp.name) / "safe_manifest.json"
        self.manifest.write_text(json.dumps({
            "schema_version": "1", "course_id": self.CID, "visibility": "public",
            "title": "Safe SQL Practice", "summary": "A reproducible example using count.",
            "artifacts": [{"path": "hands-on/query.sql", "origin": "learner_authored"}],
            "achievements": [{"claim": "Counted sample rows", "basis": "self_reported",
                              "evidence_path": "hands-on/query.sql"}],
        }), encoding="utf-8")
        self.destination = self.courses / "public" / self.CID
        self.destination.parent.mkdir()
        p, _ = portfolio.prepare(self.private, self.CID, self.manifest)
        portfolio.export(self.private, self.CID, self.manifest,
                         self.destination, p["preview_digest"], True)
        self.git("add", ".gitignore")
        for rel in ("README.md", "EVIDENCE.md", "PUBLICATION.json", "hands-on/query.sql"):
            self.git("add", "Courses/public/" + self.CID + "/" + rel)

    def git(self, *args):
        p = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, timeout=30)
        if p.returncode:
            raise AssertionError("git failed: " + " ".join(args) + ": " + p.stderr)
        return p

    def test_installed_hook_allows_only_valid_indexed_public_snapshot(self):
        import install
        script_dir = self.repo / "scripts"
        script_dir.mkdir(exist_ok=True)
        for name in ("learnprint_portfolio.py", "learnprint_publish_guard.py"):
            shutil.copyfile(ROOT / "scripts" / name, script_dir / name)
        self.assertEqual(install.install_hooks(self.repo, approve=True), 0)
        completed = subprocess.run(["git", "-c", "user.name=Test User",
                                    "-c", "user.email=test@example.invalid",
                                    "commit", "-m", "verified-disposable-snapshot"],
                                   cwd=self.repo, capture_output=True, text=True, timeout=45)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_public_index_passes_without_private_files(self):
        result = guard.check_index(self.repo)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["public_courses_checked"], 1)
        self.assertEqual(result["public_files_checked"], 4)

    def test_staged_symlink_mode_rejected_even_with_identical_blob_bytes(self):
        # Git symlinks are represented by mode 120000 in the index; a hash-only
        # scanner will miss one if its blob bytes match an approved text file.
        # update-index operates only in this disposable fixture repository and
        # does not require OS privileges to create a real Windows symlink.
        rel = "Courses/public/" + self.CID + "/hands-on/query.sql"
        staged = self.git("ls-files", "--stage", "--", rel).stdout.strip()
        self.assertTrue(staged.startswith("100644 "))
        blob_id = staged.split()[1]
        for mode in ("120000", "100755"):
            with self.subTest(index_mode=mode):
                self.git("update-index", "--cacheinfo", mode + "," + blob_id + "," + rel)
                with self.assertRaisesRegex(ValueError, "regular Git blob mode"):
                    guard.check_index(self.repo)

    def test_exact_personal_skill_directory_root_symlink_is_rejected(self):
        # Git stores a symlink as a single index entry at the directory name.
        # Prefix checks ending with "/" miss this entry entirely.
        rel = "Courses/public/" + self.CID + "/hands-on/query.sql"
        blob_id = self.git("ls-files", "--stage", "--", rel).stdout.split()[1]
        alias = ".agents/skills/learnprint-personal"
        self.git("update-index", "--add", "--cacheinfo",
                 "120000," + blob_id + "," + alias)
        with self.assertRaisesRegex(ValueError, "personal learning skill|private learner"):
            guard.check_index(self.repo)

    def test_exact_courses_directory_root_symlink_is_rejected(self):
        # A separate disposable repository avoids Git's directory/file index
        # conflict with the public snapshot files staged in setUp().
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            def run(*args):
                result = subprocess.run(["git", *args], cwd=repo,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout
            run("init")
            (repo / "symlink-target").write_text("technology/sql-lab", encoding="utf-8")
            run("add", "symlink-target")
            blob_id = run("ls-files", "--stage", "--", "symlink-target").split()[1]
            run("update-index", "--add", "--cacheinfo",
                "120000," + blob_id + ",Courses")
            with self.assertRaisesRegex(ValueError, "private learner"):
                guard.check_index(repo)

    def test_case_variant_private_course_path_is_rejected(self):
        # Windows filesystem paths are case-insensitive while Git index names
        # can carry attacker-controlled casing. Reject a lowercase Courses/
        # variant rather than silently excluding it from the privacy scan.
        rel = "Courses/public/" + self.CID + "/hands-on/query.sql"
        blob_id = self.git("ls-files", "--stage", "--", rel).stdout.split()[1]
        private_variant = "courses/.learnprint/events.jsonl"
        self.git("update-index", "--add", "--cacheinfo",
                 "100644," + blob_id + "," + private_variant)
        with self.assertRaisesRegex(ValueError, "private learner|case-variant"):
            guard.check_index(self.repo)

    def test_nested_private_paths_ignored_and_curated_public_paths_trackable(self):
        private_paths = (
            "Courses/.learnprint/learner/profile.json",
            "Courses/technology/sql-lab/hands-on/secret.sql",
            "Courses/technology/sql-lab/method-sessions.jsonl",
        )
        public_paths = (
            "Courses/public/" + self.CID + "/README.md",
            "Courses/public/" + self.CID + "/hands-on/query.sql",
        )
        for rel in private_paths:
            with self.subTest(private_path=rel):
                result = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel],
                                        cwd=self.repo, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, rel)
        for rel in public_paths:
            with self.subTest(public_path=rel):
                result = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel],
                                        cwd=self.repo, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 1, rel)

    def test_case_colliding_staged_artifact_paths_rejected(self):
        # Exporter rejects casefold-colliding files. A crafted Git index and
        # self-consistent PUBLICATION.json must not bypass the same boundary
        # on Windows/case-insensitive filesystems.
        original = "Courses/public/" + self.CID + "/hands-on/query.sql"
        variant = "Courses/public/" + self.CID + "/hands-on/QUERY.sql"
        blob_id = self.git("ls-files", "--stage", "--", original).stdout.split()[1]
        self.git("update-index", "--add", "--cacheinfo",
                 "100644," + blob_id + "," + variant)
        manifest_path = self.destination / "PUBLICATION.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["hands-on/QUERY.sql"] = manifest["files"]["hands-on/query.sql"]
        manifest["preview_digest"] = hashlib.sha256(json.dumps({
            "course_id": self.CID, "hashes": manifest["files"]
        }, sort_keys=True).encode("utf-8")).hexdigest()
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        self.git("add", "Courses/public/" + self.CID + "/PUBLICATION.json")
        with self.assertRaisesRegex(ValueError, "case-collid"):
            guard.check_index(self.repo)

    def test_distinct_staged_artifact_paths_with_same_blob_are_allowed(self):
        # Matching content digests are not themselves a collision. The path
        # namespace, not the bytes, is what must be unambiguous.
        original = "Courses/public/" + self.CID + "/hands-on/query.sql"
        distinct = "Courses/public/" + self.CID + "/hands-on/second.sql"
        blob_id = self.git("ls-files", "--stage", "--", original).stdout.split()[1]
        self.git("update-index", "--add", "--cacheinfo",
                 "100644," + blob_id + "," + distinct)
        manifest_path = self.destination / "PUBLICATION.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["hands-on/second.sql"] = manifest["files"]["hands-on/query.sql"]
        manifest["preview_digest"] = hashlib.sha256(json.dumps({
            "course_id": self.CID, "hashes": manifest["files"]
        }, sort_keys=True).encode("utf-8")).hexdigest()
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        self.git("add", "Courses/public/" + self.CID + "/PUBLICATION.json")
        result = guard.check_index(self.repo)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["public_files_checked"], 5)

    def test_private_learner_data_is_ignored(self):
        for rel in ("Courses/.learnprint/events.jsonl", "Courses/technology/sql-lab/state.json"):
            p = self.git("check-ignore", rel)
            self.assertIn(rel, p.stdout.strip())
        self.assertEqual(guard.check_index(self.repo)["private_files_indexed"], 0)

    def test_force_added_private_ledger_rejected(self):
        self.git("add", "-f", "Courses/.learnprint/events.jsonl")
        with self.assertRaisesRegex(ValueError, "private learner"):
            guard.check_index(self.repo)

    def test_force_added_extra_public_file_rejected(self):
        rel = "Courses/public/" + self.CID + "/hands-on/bonus.sql"
        (self.destination / "hands-on" / "bonus.sql").write_text("SELECT 99;\n", encoding="utf-8")
        self.git("add", rel)
        with self.assertRaisesRegex(ValueError, "indexed file set"):
            guard.check_index(self.repo)

    def test_staged_mutation_without_digest_update_rejected(self):
        rel = "Courses/public/" + self.CID + "/hands-on/query.sql"
        (self.destination / "hands-on" / "query.sql").write_text("SELECT 42;\n", encoding="utf-8")
        self.git("add", rel)
        with self.assertRaisesRegex(ValueError, "differs"):
            guard.check_index(self.repo)

    def test_unstaged_change_does_not_change_index_validation(self):
        (self.destination / "hands-on" / "query.sql").write_text("SELECT 7;\n", encoding="utf-8")
        self.assertEqual(guard.check_index(self.repo)["status"], "OK")

    def test_tampered_staged_manifest_rejected(self):
        path = self.destination / "PUBLICATION.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["preview_digest"] = "0" * 64
        path.write_text(json.dumps(obj), encoding="utf-8")
        self.git("add", "Courses/public/" + self.CID + "/PUBLICATION.json")
        with self.assertRaisesRegex(ValueError, "preview digest"):
            guard.check_index(self.repo)

    def test_hidden_personal_skill_is_rejected_if_force_staged(self):
        dest = self.repo / ".agents" / "skills" / "learnprint-personal" / "SKILL.md"
        dest.parent.mkdir(parents=True)
        dest.write_text("private\n", encoding="utf-8")
        self.git("add", "-f", str(dest.relative_to(self.repo)).replace("\\", "/"))
        with self.assertRaisesRegex(ValueError, "personal learning skill"):
            guard.check_index(self.repo)

    def test_per_course_ignore_optout_requires_explicit_untracking(self):
        gitignore = self.repo / ".gitignore"
        with gitignore.open("a", encoding="utf-8") as f:
            f.write("/Courses/public/" + self.CID + "/\n")
        rel = "Courses/public/" + self.CID + "/README.md"
        result = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel],
                                cwd=self.repo, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertIn(rel, self.git("ls-files", rel).stdout,
                      "ignore does not automatically untrack previously staged data")

    def test_parent_ignore_rule_does_not_block_explicit_public_folder(self):
        rel = "Courses/public/" + self.CID + "/README.md"
        r = subprocess.run(["git", "check-ignore", "-q", rel], cwd=self.repo,
                           capture_output=True, timeout=30)
        # With tracked files, --no-index matters: test ignore rule itself.
        r = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel],
                           cwd=self.repo, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 1, "public snapshot must be Git-trackable")

if __name__ == "__main__":
    unittest.main()
