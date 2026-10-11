"""Static regressions for portable, learner-facing presentation policy."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestPresentationContract(unittest.TestCase):
    def test_mirrored_references_match(self):
        portable = ROOT / "skills/learnprint/references/PRESENTATION.md"
        host = ROOT / ".agents/skills/learnprint/references/PRESENTATION.md"
        self.assertEqual(portable.read_bytes(), host.read_bytes())
        self.assertEqual(
            (ROOT / "skills/learnprint/references/JOURNEY.md").read_bytes(),
            (ROOT / ".agents/skills/learnprint/references/JOURNEY.md").read_bytes())

    def test_contract_is_discoverable_and_safe(self):
        for path in (
            "AGENTS.md",
            "skills/learnprint/references/JOURNEY.md",
            ".agents/skills/learnprint/references/JOURNEY.md",
            "skills/learnprint-learn/references/TEACHING.md",
        ):
            self.assertIn("PRESENTATION.md", (ROOT / path).read_text(encoding="utf-8"))
        contract = (ROOT / "skills/learnprint/references/PRESENTATION.md").read_text(encoding="utf-8")
        for required in ("--approve", "without plugins", "one", "JSON", "confused", "ASCII"):
            self.assertIn(required, contract)

    def test_skills_still_under_packaging_limit(self):
        for path in (
            ".agents/skills/learnprint/SKILL.md",
            "skills/learnprint/SKILL.md",
        ):
            self.assertLessEqual(len((ROOT / path).read_text(encoding="utf-8")), 8000)


if __name__ == "__main__":
    unittest.main()
