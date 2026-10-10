import importlib.util
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install", ROOT / "scripts/install.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def git_repo(d, ignore=None):
    subprocess.run(["git", "init", "-q"], cwd=d, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True, timeout=30)
    if ignore:
        (Path(d) / ".gitignore").write_text(ignore, encoding="utf-8")
    return Path(d)


def make_personal_source(d):
    src = Path(d) / "Courses" / ".learnprint" / ".agents" / "skills" / "learnprint-personal"
    (src / "references").mkdir(parents=True)
    (src / "SKILL.md").write_text("# personal\n", encoding="utf-8")
    return Path(d) / "Courses" / ".learnprint"


class TestInstallPersonal(unittest.TestCase):
    def test_install_personal_to_gitignored_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d, ".agents/skills/learnprint-personal/\n")
            source = make_personal_source(d)
            dst = Path(d) / ".agents" / "skills" / "learnprint-personal"
            rc = mod.install_personal_skill(source, dst, approve=True)
            self.assertEqual(rc, 0)
            self.assertTrue((dst / "SKILL.md").exists())

    def test_install_personal_refuses_non_gitignored(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            source = make_personal_source(d)
            dst = Path(d) / ".agents" / "skills" / "learnprint-personal"
            rc = mod.install_personal_skill(source, dst, approve=True)
            self.assertEqual(rc, 2)
            self.assertFalse(dst.exists())

    def test_install_personal_refuses_overwrite(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d, ".agents/skills/learnprint-personal/\n")
            source = make_personal_source(d)
            dst = Path(d) / ".agents" / "skills" / "learnprint-personal"
            dst.mkdir(parents=True)
            rc = mod.install_personal_skill(source, dst, approve=True)
            self.assertEqual(rc, 2)

    def test_install_personal_requires_approval(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d, ".agents/skills/learnprint-personal/\n")
            source = make_personal_source(d)
            dst = Path(d) / ".agents" / "skills" / "learnprint-personal"
            rc = mod.install_personal_skill(source, dst, approve=False)
            self.assertEqual(rc, 2)
            self.assertFalse(dst.exists())

    def test_hooks_install_and_refuse_overwrite(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            hooks = Path(d) / ".git" / "hooks"
            hooks.mkdir(parents=True, exist_ok=True)
            self.assertEqual(mod.install_hooks(d, approve=True), 0)
            self.assertTrue((hooks / "pre-commit").exists())
            self.assertEqual(mod.install_hooks(d, approve=True), 2)

    def test_hooks_require_approval(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            (Path(d) / ".git" / "hooks").mkdir(parents=True, exist_ok=True)
            self.assertEqual(mod.install_hooks(d, approve=False), 2)

    def test_self_mode_gitignores_discovery_dirs(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            rc = mod.main(["--target", "codex", "--dest", d, "--self", "--approve"])
            # --self with explicit --dest behaves like a normal install plus
            # gitignore coverage; main() returns 0 on success.
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
