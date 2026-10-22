"""Read-only journey and publication choices, domain-neutral and evidence-honest."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from learnprint_stage_card import render_stage_card  # noqa: E402


class TestStageCard(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "title": "Matematika: Pecahan",
            "units": [
                {"unit_id": "a", "title": "Pecahan senilai",
                 "evidence_status": "not_assessed"},
                {"unit_id": "b", "title": "Penjumlahan pecahan",
                 "evidence_status": "in_progress"},
                {"unit_id": "c", "title": "Soal cerita",
                 "evidence_status": "not_assessed"},
            ],
        }

    def test_stage_and_position_different_from_mastery(self):
        text = render_stage_card(self.plan, stage="TRANSFER",
                                 unit_id="b", screening_used=2)
        self.assertIn("TES TRANSFER", text)
        self.assertIn("2/3 pertanyaan", text)
        self.assertIn("[2/3] Penjumlahan pecahan", text)
        self.assertIn("[-#-]", text)
        self.assertNotIn("66%", text)
        self.assertIn("bukan persentase kemampuan", text)

    def test_unknown_stage_and_screening_not_invented(self):
        text = render_stage_card(self.plan)
        self.assertIn("belum tercatat secara pasti", text)
        self.assertIn("belum ada hitungan", text)
        self.assertNotIn("0%", text)
        self.assertIn("Unit aktif: belum dikonfirmasi", text)

    def test_unknown_unit_and_phase_conflict_rejected(self):
        with self.assertRaisesRegex(ValueError, "absent"):
            render_stage_card(self.plan, unit_id="invented")
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            render_stage_card(self.plan, stage="LESSON",
                              stored_phase="EXPLAIN")

    def test_english_card_and_verified_fsm_phase(self):
        text = render_stage_card(self.plan, language="en",
                                 stored_phase="GUIDED", unit_id="a")
        self.assertIn("GUIDED PRACTICE", text)
        self.assertIn("validated persisted FSM", text)
        self.assertIn("NOT mastery", text)

    def test_fsm_feedback_not_mislabeled_as_confusion_pause(self):
        feedback = render_stage_card(self.plan, stored_phase="FEEDBACK")
        completed = render_stage_card(self.plan, stored_phase="COMPLETE")
        teach_back = render_stage_card(self.plan, stored_phase="TEACH_BACK")
        self.assertIn("UMPAN BALIK", feedback)
        self.assertNotIn("JEDA/KLARIFIKASI", feedback)
        self.assertIn("SESI SELESAI", completed)
        self.assertIn("JELASKAN KEMBALI", teach_back)

    def test_screening_bounds(self):
        for bad in (-1, 4, True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                render_stage_card(self.plan, screening_used=bad)


class TestPortfolioOptionsCLI(unittest.TestCase):
    def test_all_courses_selectable_without_export_or_git(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Courses"
            cmd = [sys.executable, str(ROOT / "scripts/learnprint.py")]
            init = subprocess.run(cmd + ["course", "init", "--courses-root",
                                         str(root), "--approve"], capture_output=True,
                                  text=True, timeout=40)
            self.assertEqual(init.returncode, 0, init.stderr)
            created = []
            for cat, title in (("technology", "DNS"), ("languages", "Japanese")):
                run = subprocess.run(cmd + ["course", "create", "--courses-root",
                                            str(root), "--category", cat,
                                            "--title", title, "--goal", "learn",
                                            "--approve"], capture_output=True,
                                     text=True, timeout=40)
                self.assertEqual(run.returncode, 0, run.stderr)
                created.append(json.loads(run.stdout)["course_id"])
            record = root / ".learnprint" / "events.jsonl"
            original = record.read_bytes()
            run = subprocess.run(cmd + ["course", "portfolio-options",
                                        "--courses-root", str(root)],
                                 capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stderr)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["github_push"], "never_automatic")
            self.assertEqual({c["course_id"] for c in payload["courses"]}, set(created))
            self.assertTrue(all(c["selectable_for_portfolio"] for c in payload["courses"]))
            self.assertTrue(all(c["snapshot_status"] == "not_exported"
                                for c in payload["courses"]))
            self.assertEqual(record.read_bytes(), original)
            self.assertFalse((root / "public").exists())

    def test_cli_journey_card_no_fake_score(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Courses"
            cmd = [sys.executable, str(ROOT / "scripts/learnprint.py")]
            init = subprocess.run(cmd + ["course", "init", "--courses-root", str(root),
                                         "--approve"], capture_output=True, text=True,
                                  timeout=40)
            self.assertEqual(init.returncode, 0, init.stderr)
            created = subprocess.run(cmd + ["course", "create", "--courses-root",
                                            str(root), "--category", "technology",
                                            "--title", "DNS", "--goal", "learn",
                                            "--approve"], capture_output=True,
                                     text=True, timeout=40)
            self.assertEqual(created.returncode, 0, created.stderr)
            cid = json.loads(created.stdout)["course_id"]
            run = subprocess.run(cmd + ["course", "journey-card", "--courses-root",
                                        str(root), "--course-id", cid,
                                        "--stage", "SCREENING", "--screening-used", "1"],
                                 capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("SCREENING AWAL", run.stdout)
            self.assertIn("1/3 pertanyaan", run.stdout)
            self.assertIn("silabus terstruktur belum tersedia", run.stdout)
            self.assertNotIn("100%", run.stdout)


if __name__ == "__main__":
    unittest.main()
