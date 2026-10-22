"""Guard against stale portable skill copies in packaged distributions."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ADR-0003: protocols/ is the authoritative policy source; these locations
# must stay byte-identical to it.
CANONICAL_POLICY_MIRRORS = {
    "protocols/TUTOR-LANGUAGE-AND-STAGES.md": (
        "skills/learnprint/references/TUTOR-LANGUAGE-AND-STAGES.md",
        ".agents/skills/learnprint/references/TUTOR-LANGUAGE-AND-STAGES.md",
        "skills/learnprint-learn/references/TUTOR-LANGUAGE-AND-STAGES.md",
        ".agents/skills/learnprint-learn/references/TUTOR-LANGUAGE-AND-STAGES.md",
        "distribution/claude-plugin/skills/learnprint-learn/references/TUTOR-LANGUAGE-AND-STAGES.md",
    ),
    "protocols/TEACHING.md": (
        "skills/learnprint-learn/references/TEACHING.md",
        ".agents/skills/learnprint-learn/references/TEACHING.md",
        "distribution/claude-plugin/skills/learnprint-learn/references/TEACHING.md",
    ),
    "protocols/ASSESSMENT.md": (
        "skills/learnprint-assess/references/ASSESSMENT.md",
        ".agents/skills/learnprint-assess/references/ASSESSMENT.md",
        "distribution/claude-plugin/skills/learnprint-assess/references/ASSESSMENT.md",
    ),
    "protocols/REVIEW.md": (
        "skills/learnprint-learn/references/REVIEW.md",
        ".agents/skills/learnprint-learn/references/REVIEW.md",
        "distribution/claude-plugin/skills/learnprint-learn/references/REVIEW.md",
    ),
    "protocols/JOURNEY.md": (
        "skills/learnprint/references/JOURNEY.md",
        ".agents/skills/learnprint/references/JOURNEY.md",
    ),
    "protocols/PRESENTATION.md": (
        "skills/learnprint/references/PRESENTATION.md",
        ".agents/skills/learnprint/references/PRESENTATION.md",
    ),
}

# ADR-0003: T01-T08 guard anchors must remain visible in the canonical
# teaching policy so behavioral tests keep a stable reference.
GUARD_ANCHORS = (
    "T01 Attempt gate",
    "T02 Confusion gate",
    "T03 Help contamination",
    "T04 Fresh task",
    "T05 Transfer",
    "T06 Delayed floor",
    "T07 Source",
    "T08 Evidence",
)


class TestSkillDistributionSync(unittest.TestCase):
    def test_canonical_protocol_mirrors_match_source(self):
        for source, mirrors in CANONICAL_POLICY_MIRRORS.items():
            source_path = ROOT / source
            self.assertTrue(source_path.is_file(), f"missing canonical source: {source}")
            source_bytes = source_path.read_bytes()
            for mirror in mirrors:
                with self.subTest(source=source, mirror=mirror):
                    mirror_path = ROOT / mirror
                    self.assertTrue(mirror_path.is_file(), f"missing mirror: {mirror}")
                    self.assertEqual(
                        source_bytes,
                        mirror_path.read_bytes(),
                        f"stale protocol mirror for {source}: {mirror}",
                    )

    def test_teaching_policy_carries_guard_anchors(self):
        teaching = (ROOT / "protocols/TEACHING.md").read_text(encoding="utf-8")
        for anchor in GUARD_ANCHORS:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, teaching, f"missing guard anchor: {anchor}")

    def test_agent_skill_copies_match_canonical_sources(self):
        for source in sorted((ROOT / "skills").rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(ROOT / "skills")
            mirror = ROOT / ".agents" / "skills" / relative
            with self.subTest(path=str(relative)):
                self.assertTrue(mirror.is_file(), f"missing mirror: {mirror}")
                self.assertEqual(source.read_text(encoding="utf-8"), mirror.read_text(encoding="utf-8"),
                                 f"stale agent skill mirror: {relative}")

    def test_packaging_check_stays_green(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_package.py")],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PACKAGING OK", result.stdout)

    def test_claude_distribution_matches_canonical_sources(self):
        distribution = ROOT / "distribution" / "claude-plugin" / "skills"
        files = sorted(p for p in distribution.rglob("*") if p.is_file())
        self.assertTrue(files, "missing Claude plugin skill distribution")
        for mirror in files:
            relative = mirror.relative_to(distribution)
            source = ROOT / "skills" / relative
            with self.subTest(path=str(relative)):
                self.assertTrue(source.is_file(), f"orphaned distribution file: {relative}")
                self.assertEqual(source.read_text(encoding="utf-8"), mirror.read_text(encoding="utf-8"),
                                 f"stale Claude skill distribution: {relative}")


if __name__ == "__main__":
    unittest.main()
