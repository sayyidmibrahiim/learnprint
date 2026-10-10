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
        self.assertFalse(any(f.startswith("Courses/") for f in tracked),
                         "no Courses/ file may be tracked")
        self.assertFalse(any("learnprint-personal" in f for f in tracked),
                         "no personal skill file may be tracked")

    def test_no_private_data_in_plan_diff(self):
        # The published plan must not embed learner answers, tokens, or keys.
        import re
        text = (ROOT / "plan/learnprint-hardening-workspace.md").read_text(encoding="utf-8")
        for pat in (r"(?i)api[_-]?key\s*[:=]", r"(?i)password\s*[:=]",
                    r"sk-[A-Za-z0-9]{8,}", r"(?i)bearer\s+[A-Za-z0-9._-]+"):
            self.assertIsNone(re.search(pat, text), f"sensitive pattern: {pat}")


if __name__ == "__main__":
    unittest.main()
