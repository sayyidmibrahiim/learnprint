"""Static wiring contract for multilingual tutor guidance.

These tests ensure prompt entrypoints still load the policy after refactors.
They DO NOT prove a live LLM produced correct language or stage labels.
Run: python -m unittest discover -s tests -p 'test_tutor_policy_contract.py'
"""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY = "skills/learnprint/references/TUTOR-LANGUAGE-AND-STAGES.md"
UAT = "docs/TUTOR-LANGUAGE-STAGES-UAT.md"
TRACKER = "docs/TUTOR-FIX-TRACKER.md"
ENTRYPOINTS = (
    "AGENTS.md",
    "skills/learnprint/SKILL.md",
    ".agents/skills/learnprint/SKILL.md",
    "skills/learnprint-learn/SKILL.md",
    "skills/learnprint/references/JOURNEY.md",
    "skills/learnprint/references/PRESENTATION.md",
    ".opencode/commands/learnprint-learn.md",
)


class TutorPolicyContractTests(unittest.TestCase):
    def test_policy_and_manual_uat_documents_exist(self):
        for path in (POLICY, UAT, TRACKER):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_all_host_entrypoints_explicitly_load_policy(self):
        for path in ENTRYPOINTS:
            with self.subTest(path=path):
                content = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("TUTOR-LANGUAGE-AND-STAGES.md", content)

    def test_portable_orchestrator_mirrors_identical_and_bounded(self):
        primary = (ROOT / "skills/learnprint/SKILL.md").read_text(encoding="utf-8")
        mirror = (ROOT / ".agents/skills/learnprint/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(primary, mirror)
        self.assertLess(len(primary), 8000)

    def test_stage_contract_separates_modes_and_progress_basis(self):
        policy = (ROOT / POLICY).read_text(encoding="utf-8")
        for marker in (
            "PERSIAPAN",
            "SCREENING AWAL",
            "BELAJAR",
            "TES MANDIRI",
            "TES TRANSFER",
            "REVIEW TERTUNDA",
            "JEDA / KLARIFIKASI",
            "0–3",
            "[#--]",
            "not a quota",
            "unit-position",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, policy)

    def test_live_acceptance_is_not_conflated_with_static_contract(self):
        uat = (ROOT / UAT).read_text(encoding="utf-8")
        for scenario in ("LANG-01", "LANG-04", "STAGE-05", "EVID-01", "PORT-01"):
            self.assertIn(scenario, uat)
        self.assertIn("human reviewer", uat)
        self.assertIn("not", uat.lower())


if __name__ == "__main__":
    unittest.main()
