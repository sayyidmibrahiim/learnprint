"""W8 gate: honest assistance/review labels in curated portfolio exports.

human_reviewed names its reviewer; ai_reviewed references its deterministic
evaluation record; self_reported carries neither; publication stays private
by default and hosted snapshots claim no certification.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import learnprint_portfolio as portfolio  # noqa: E402


class TestAchievementLabels(unittest.TestCase):
    CID = "e5230ed4-8481-425f-882a-332a8718d6cf"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / "Courses"
        self.course = self.root / "technology" / "sql-lab"
        self.course.mkdir(parents=True)
        self.lab = self.course / "hands-on"
        self.lab.mkdir()
        (self.lab / "query.sql").write_text("SELECT count(*) FROM invoices;\n", encoding="utf-8")
        (self.course / "state.json").write_text(json.dumps({
            "schema_version": "1.0", "course_id": self.CID,
            "learning_scope": [{"id": "a", "name": "SQL counts",
                                "status": "unknown", "evidence_ids": []}]}), encoding="utf-8")
        metadata = self.root / ".learnprint"
        metadata.mkdir()
        (metadata / "registry.json").write_text(json.dumps({
            "schema_version": "1.0",
            "courses": [{"course_id": self.CID, "title": "SQL Lab",
                         "rel_path": "technology/sql-lab"}]}), encoding="utf-8")
        (metadata / "events.jsonl").write_text("private learner evidence\n", encoding="utf-8")
        self.manifest = base / "publication.json"
        self.data = {"schema_version": "1", "course_id": self.CID,
                     "visibility": "public", "title": "SQL demonstration",
                     "summary": "Counting records using a reproducible query.",
                     "artifacts": [{"path": "hands-on/query.sql", "origin": "learner_authored"}],
                     "achievements": []}
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def preview(self):
        return portfolio.prepare(self.course, self.CID, self.manifest)

    def test_human_reviewed_requires_named_reviewer(self):
        self.data["achievements"] = [{"claim": "Wrote a counting query",
                                      "evidence_path": "hands-on/query.sql",
                                      "basis": "human_reviewed"}]
        self.save()
        with self.assertRaisesRegex(ValueError, "reviewer"):
            self.preview()

    def test_human_reviewed_with_reviewer_is_labeled(self):
        self.data["achievements"] = [{"claim": "Wrote a counting query",
                                      "evidence_path": "hands-on/query.sql",
                                      "basis": "human_reviewed",
                                      "reviewer": "Mentor Andi"}]
        self.save()
        meta, output = self.preview()
        evidence = output["EVIDENCE.md"].decode("utf-8")
        self.assertIn("human_reviewed | hands-on/query.sql | reviewer: Mentor Andi", evidence)

    def test_ai_reviewed_requires_evaluation_reference(self):
        self.data["achievements"] = [{"claim": "Wrote a counting query",
                                      "evidence_path": "hands-on/query.sql",
                                      "basis": "ai_reviewed"}]
        self.save()
        with self.assertRaisesRegex(ValueError, "evaluation"):
            self.preview()
        self.data["achievements"][0]["evaluation_ref"] = "eval:events:e42"
        self.save()
        meta, output = self.preview()
        evidence = output["EVIDENCE.md"].decode("utf-8")
        self.assertIn("evaluation: eval:events:e42", evidence)

    def test_self_reported_may_not_decorate_labels(self):
        for extra in ({"reviewer": "Nobody"}, {"evaluation_ref": "eval:x"}):
            with self.subTest(extra=extra):
                row = {"claim": "Counted", "evidence_path": "hands-on/query.sql",
                       "basis": "self_reported", **extra}
                self.data["achievements"] = [row]
                self.save()
                with self.assertRaisesRegex(ValueError, "only"):
                    self.preview()

    def test_export_disclaimer_marks_non_certification(self):
        self.data["achievements"] = [{"claim": "Wrote a counting query",
                                      "evidence_path": "hands-on/query.sql",
                                      "basis": "human_reviewed",
                                      "reviewer": "Mentor Andi"}]
        self.save()
        meta, output = self.preview()
        self.assertIn("not an accredited certificate", output["README.md"].decode("utf-8"))
        self.assertIn("not independently authenticated", output["EVIDENCE.md"].decode("utf-8"))

    def test_private_visibility_stays_default_private(self):
        self.data["visibility"] = "private"
        self.save()
        meta, _ = self.preview()
        self.assertEqual(meta["status"], "private")
        self.assertFalse(meta["publishable"])


if __name__ == "__main__":
    unittest.main()
