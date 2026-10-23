"""Git hook installation and upgrade must fail closed, only in temporary repos."""
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install

class TestPrivacyHookInstallation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        result = subprocess.run(["git", "init"], cwd=self.repo,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        script = self.repo / "scripts"
        script.mkdir()
        (script / "learnprint_publish_guard.py").write_text(
            "# Synthetic guard: deny every attempted commit in this fixture\n"
            "raise SystemExit(2)\n", encoding="utf-8")
        (script / "learnprint_portfolio.py").write_text(
            "# Dependency marker for the guarded hook\n", encoding="utf-8")
        self.hook = self.repo / ".git" / "hooks" / "pre-commit"

    def test_custom_active_hooks_path_refuses_inactive_install(self):
        # A Git repo may execute hooks from core.hooksPath instead of
        # .git/hooks. Reporting success for an unused hook is unsafe.
        custom = self.repo / "custom-hooks"
        custom.mkdir()
        result = subprocess.run(["git", "config", "--local", "core.hooksPath",
                                 str(custom)], cwd=self.repo, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(install.install_hooks(self.repo, approve=True), 2)
        self.assertFalse(self.hook.exists())
        self.assertFalse((custom / "pre-commit").exists())

    def test_unreadable_git_config_refuses_hook_install(self):
        # An unavailable Git executable/config must not turn an unverified
        # hook location into a false success.
        with mock.patch.object(install.subprocess, "run",
                               side_effect=OSError("git config unavailable")):
            self.assertEqual(install.install_hooks(self.repo, approve=True), 2)
        self.assertFalse(self.hook.exists())

    def test_no_approval_no_hook(self):
        self.assertEqual(install.install_hooks(self.repo, approve=False), 2)
        self.assertFalse(self.hook.exists())

    def test_approved_hook_is_current_and_refuses_overwrite(self):
        self.assertEqual(install.install_hooks(self.repo, approve=True), 0)
        self.assertEqual(self.hook.read_text(encoding="utf-8").replace("\r\n", "\n"),
                         install.HOOK_SCRIPT)
        self.assertEqual(install.install_hooks(self.repo, approve=True), 2)

    def test_only_known_legacy_hook_is_upgradable(self):
        self.hook.write_text(install.LEGACY_HOOK_SCRIPT, encoding="utf-8")
        self.assertEqual(install.install_hooks(self.repo, approve=False), 2)
        self.assertEqual(self.hook.read_text(encoding="utf-8").replace("\r\n", "\n"),
                         install.LEGACY_HOOK_SCRIPT)
        self.assertEqual(install.install_hooks(self.repo, approve=True), 0)
        self.assertEqual(self.hook.read_text(encoding="utf-8").replace("\r\n", "\n"),
                         install.HOOK_SCRIPT)

    def test_legacy_upgrade_link_swap_after_read_refuses_without_target_write(self):
        # A linked pre-commit can replace a known legacy hook just after
        # the installer reads its contents. The upgraded hook MUST NOT write
        # through that linked inode to another file.
        self.hook.write_text(install.LEGACY_HOOK_SCRIPT, encoding="utf-8")
        outside = self.repo / "unrelated-owned-during-race.txt"
        outside.write_text(install.LEGACY_HOOK_SCRIPT, encoding="utf-8")
        original_read = Path.read_text
        swapped = []

        def swap_after_read(path, *args, **kwargs):
            data = original_read(path, *args, **kwargs)
            if path == self.hook and not swapped:
                self.hook.unlink()
                os.link(outside, self.hook)
                swapped.append(True)
            return data

        with mock.patch.object(Path, "read_text", swap_after_read):
            self.assertEqual(install.install_hooks(self.repo, approve=True), 2)
        # Windows may refuse the attempted unlink while the original inode
        # is pinned open. POSIX may allow the swap; both must reject upgrade.
        self.assertIn(swapped, ([], [True]))
        self.assertEqual(outside.read_text(encoding="utf-8"),
                         install.LEGACY_HOOK_SCRIPT)
        if swapped:
            self.assertEqual(self.hook.stat().st_nlink, 2)
        else:
            self.assertEqual(self.hook.read_text(encoding="utf-8"),
                             install.LEGACY_HOOK_SCRIPT)

    def test_unrecognized_hook_cannot_be_overwritten(self):
        self.hook.write_text("# custom\n", encoding="utf-8")
        self.assertEqual(install.install_hooks(self.repo, approve=True), 2)
        self.assertEqual(self.hook.read_text(encoding="utf-8"), "# custom\n")

    def test_refuses_existing_hardlinked_hook_without_modifying_target(self):
        # Hard links share file content even when the hook path is not a symlink.
        # A legacy-hook upgrade must not overwrite another file through a link.
        outside = self.repo / "unrelated-owned.txt"
        outside.write_text(install.LEGACY_HOOK_SCRIPT, encoding="utf-8")
        try:
            os.link(outside, self.hook)
        except OSError:
            self.skipTest("host filesystem cannot create hard links")
        self.assertGreaterEqual(self.hook.stat().st_nlink, 2)
        self.assertEqual(install.install_hooks(self.repo, approve=True), 2)
        self.assertEqual(outside.read_text(encoding="utf-8"), install.LEGACY_HOOK_SCRIPT)

    def test_refuses_existing_symlink_hook_without_modifying_target(self):
        outside = self.repo / "unrelated-symlink-target.txt"
        outside.write_text(install.LEGACY_HOOK_SCRIPT, encoding="utf-8")
        try:
            self.hook.symlink_to(outside)
        except OSError:
            self.skipTest("host cannot create symlinks")
        self.assertEqual(install.install_hooks(self.repo, approve=True), 2)
        self.assertEqual(outside.read_text(encoding="utf-8"), install.LEGACY_HOOK_SCRIPT)

    def test_hook_rejects_private_commit(self):
        self.assertEqual(install.install_hooks(self.repo, approve=True), 0)
        private = self.repo / "Courses" / ".learnprint" / "events.jsonl"
        private.parent.mkdir(parents=True)
        private.write_text("private evidence\n", encoding="utf-8")
        cmd = subprocess.run(["git", "add", "-f", "Courses/.learnprint/events.jsonl"],
                             cwd=self.repo, capture_output=True, text=True, timeout=30)
        self.assertEqual(cmd.returncode, 0, cmd.stderr)
        cmd = subprocess.run(["git", "-c", "user.name=Test User",
                              "-c", "user.email=test@example.invalid",
                              "commit", "-m", "must-not-commit"],
                             cwd=self.repo, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(cmd.returncode, 0, cmd.stdout)
        self.assertFalse("1 file changed" in cmd.stdout)

if __name__ == "__main__":
    unittest.main()
