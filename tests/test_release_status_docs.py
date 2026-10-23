"""Prevent obsolete release-status claims from becoming the current documentation.

This is a documentation consistency test, not proof of live tutor behavior or
future CI runs. Human UAT and adversarial review remain distinct gates.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class ReleaseStatusContractTests(unittest.TestCase):
    def test_public_portfolio_status_cites_observed_ci(self):
        content = read("docs/COURSE-PORTFOLIO.md")
        current = content.split("## Select per course", 1)[0]
        self.assertIn("engineering integration verified on `main`", current)
        self.assertIn("39909186179", current)
        self.assertIn("Human tutor UAT", current)
        self.assertNotIn("cross-platform CI not yet verified", current)
        self.assertIn("3.11, 3.12, 3.13, 3.14, 3.15", content)
        self.assertNotIn("Python 3.9/3.12 suite", content)
        self.assertIn("never automatically overwritten", content)

    def test_tracker_no_longer_calls_merged_pr_pending(self):
        content = read("to-do.md")
        first = content.split("## A. Takeover protocol", 1)[0]
        self.assertIn("Merged.", first)
        self.assertIn("15/15", first)
        self.assertNotIn("Merge into `main` is a separate pending decision", first)
        self.assertIn("human", first.lower())
        self.assertIn("adversarial", first.lower())

    def test_research_says_final_hook_policy_not_abandoned_candidate(self):
        content = read("docs/research/2026-10-23-production-release-gates.md")
        self.assertIn("Final resolution supersedes earlier proposed identity checks", content)
        self.assertIn("refuses all existing hooks", content)
        self.assertIn("That candidate was abandoned", content)
        self.assertIn("39909186179", content)
        self.assertIn("independent adversarial security review", content)

    def test_branch_and_release_notes_truthful(self):
        publish = read("docs/PUBLISHING.md")
        notes = read("docs/RELEASE-NOTES.md")
        self.assertIn("PR #9", publish)
        self.assertIn("closed without merge", publish)
        self.assertIn("merged to `main`", notes.lower())
        self.assertIn("Historical pre-merge local verification", notes)
        self.assertIn("Superseded", notes)
        self.assertIn("human", notes.lower())
        self.assertNotIn("PR #9 open against `main`", notes)

    def test_premerge_status_not_presented_as_current_anymore(self):
        notes = read("docs/RELEASE-NOTES.md")
        for obsolete in (
            "Status: release candidate on `feature/hardening-workspace`",
            "### 2026-10-23 full release-candidate verification (current)",
        ):
            self.assertNotIn(obsolete, notes)
        self.assertRegex(notes, re.compile(r"15[/ ](?:of )?15", re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
