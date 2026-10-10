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

INSTALL_SCRIPT = str(ROOT / "scripts" / "install.py")


def install_cli(*argv):
    import sys
    return subprocess.run([sys.executable, INSTALL_SCRIPT, *argv],
                          capture_output=True, text=True, timeout=60)


class TestInstallMainCLI(unittest.TestCase):
    def test_main_dry_run(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            r = install_cli("--target", "codex", "--dest", d, "--dry-run")
            self.assertEqual(r.returncode, 0)

    def test_main_requires_approve(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            r = install_cli("--target", "codex", "--dest", d)
            self.assertEqual(r.returncode, 2)

    def test_main_installs_and_refuses_overwrite(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            r = install_cli("--target", "codex", "--dest", d, "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(d) / ".agents" / "skills" / "learnprint-learn" / "SKILL.md").exists())
            r = install_cli("--target", "codex", "--dest", d, "--approve")
            self.assertEqual(r.returncode, 2)

    def test_main_personal_skill_needs_gitignored_dest(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            source = make_personal_source(d)
            r = install_cli("--target", "codex", "--dest", d,
                            "--personal-skill", "--source", str(source), "--approve")
            self.assertEqual(r.returncode, 2)  # .agents/skills/learnprint-personal not ignored here
            (Path(d) / ".gitignore").write_text(".agents/skills/learnprint-personal/\n")
            r = install_cli("--target", "codex", "--dest", d,
                            "--personal-skill", "--source", str(source), "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_main_hooks(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            (Path(d) / ".git" / "hooks").mkdir(parents=True, exist_ok=True)
            r = install_cli("--target", "codex", "--dest", d, "--hooks", "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(d) / ".git" / "hooks" / "pre-commit").exists())

    def test_main_missing_personal_source_writes_nothing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            ghost = str(Path(d) / "no-such-source")
            r = install_cli("--target", "codex", "--dest", d,
                            "--personal-skill", "--source", ghost, "--approve")
            self.assertEqual(r.returncode, 2)
            self.assertFalse((Path(d) / ".agents").exists())

    def test_self_dry_run_has_no_side_effects(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            git_repo(d)
            before = set(p.name for p in Path(d).iterdir())
            r = install_cli("--target", "codex", "--dest", d, "--self", "--dry-run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse((Path(d) / ".gitignore").exists())
            self.assertEqual(set(p.name for p in Path(d).iterdir()), before)


if __name__ == "__main__":
    unittest.main()
