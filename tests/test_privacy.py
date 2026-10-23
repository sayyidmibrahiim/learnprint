import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, timeout=30)


class TestPrivacy(unittest.TestCase):
    def test_gitignore_covers_courses(self):
        r = git("check-ignore", "-q", "Courses/events.jsonl")
        self.assertEqual(r.returncode, 0, "Courses/ must be gitignored")

    def test_gitignore_covers_personal_skill_paths(self):
        for p in (".agents/skills/learnprint-personal/SKILL.md",
                  ".claude/skills/learnprint-personal/SKILL.md",
                  ".kiro/skills/learnprint-personal/SKILL.md"):
            r = git("check-ignore", "-q", p)
            self.assertEqual(r.returncode, 0, f"{p} must be gitignored")

    def test_no_courses_tracked(self):
        r = git("ls-files")
        self.assertEqual(r.returncode, 0)
        tracked = r.stdout.splitlines()
        self.assertFalse(any(f.startswith("Courses/") and
                             not f.startswith("Courses/public/") for f in tracked),
                         "canonical private course records must not be tracked")
        import sys
        guard = subprocess.run([sys.executable, str(ROOT / "scripts" / "learnprint_publish_guard.py"),
                                "--repo", str(ROOT)], cwd=ROOT, capture_output=True,
                               text=True, timeout=30)
        self.assertEqual(guard.returncode, 0, guard.stderr)
        self.assertFalse(any("learnprint-personal" in f for f in tracked),
                         "no personal skill file may be tracked")

    def test_no_private_data_in_tracked_planning_docs(self):
        # Audit living planning files, not the removed hardening-plan filename.
        # Never read ignored private learner files from Courses/.
        import re
        result = git("ls-files", "-z")
        self.assertEqual(result.returncode, 0, result.stderr)
        planning = sorted(
            p for p in result.stdout.split("\0")
            if p.endswith(".md") and p.startswith(("plan/", ".scratch/"))
        )
        self.assertTrue(planning, "expected tracked planning notes to audit")
        patterns = (
            r"(?i)api[_-]?key\s*[:=]",
            r"(?i)password\s*[:=]",
            r"sk-[A-Za-z0-9]{8,}",
            r"(?i)bearer\s+[A-Za-z0-9._-]+",
        )
        for relative in planning:
            content = (ROOT / relative).read_text(encoding="utf-8")
            for pattern in patterns:
                with self.subTest(file=relative, pattern=pattern):
                    self.assertIsNone(
                        re.search(pattern, content),
                        f"sensitive pattern in {relative}: {pattern}"
                    )


if __name__ == "__main__":
    unittest.main()
