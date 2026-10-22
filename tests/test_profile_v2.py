"""W5 gate: additive reversible profile migration, backward reads, identity
preservation, calibration analytics and fail-closed validation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import learnprint as engine  # noqa: E402
import learnprint_profile as profile_impl  # noqa: E402


V1 = {
    "schema_version": "1.0",
    "profile_id": "local-learner",
    "assessment_status": "provisional",
    "public_template": False,
    "evidence_quality": "limited",
    "observed_claims": [
        {"id": "cl1", "claim": "prefers short examples", "category": "reported_preference",
         "evidence_ids": ["ev1"]}
    ],
    "evidence": [
        {"id": "ev1", "origin": "self_report", "verification": "reported",
         "description": "learner preference statement", "source": "intake chat"}
    ],
    "instruction_defaults": {"example_style": "concise"},
}


class TestMigration(unittest.TestCase):
    def test_additive_migration_preserves_identity_and_content(self):
        migrated = profile_impl.migrate_v1_to_v2(V1)
        self.assertEqual(migrated["schema_version"], "2.0")
        self.assertEqual(migrated["profile_id"], V1["profile_id"])
        self.assertEqual(migrated["observed_claims"], V1["observed_claims"])
        self.assertEqual(migrated["evidence"], V1["evidence"])
        self.assertEqual(migrated["instruction_defaults"], V1["instruction_defaults"])
        self.assertEqual(migrated["constraints"], [])

    def test_migration_is_idempotent_and_nondestructive(self):
        migrated = profile_impl.migrate_v1_to_v2(V1)
        again = profile_impl.migrate_v1_to_v2(V1)
        self.assertEqual(migrated, again)
        self.assertEqual(V1["schema_version"], "1.0", "source must remain untouched")

    def test_v2_profile_reads_and_passes_canonical_validator(self):
        migrated = profile_impl.migrate_v1_to_v2(V1)
        migrated["constraints"] = [
            {"constraint": "max 30-minute sessions", "category": "reported", "evidence_ids": ["ev1"]}
        ]
        self.assertEqual(engine.validate_profile(migrated), [])
        self.assertEqual(engine.validate_profile(V1), [])

    def test_bad_constraint_fail_closed(self):
        migrated = profile_impl.migrate_v1_to_v2(V1)
        migrated["constraints"] = [{"constraint": ""}]
        errs = engine.validate_profile(migrated)
        self.assertTrue(any("constraint" in e for e in errs))

    def test_non_v1_input_rejected(self):
        with self.assertRaises(profile_impl.ProfileError):
            profile_impl.migrate_v1_to_v2({"schema_version": "2.0"})

    def test_profile_read_rejects_non_object(self):
        with tempfile.TemporaryDirectory() as d:
            arr = Path(d) / "arr.json"
            arr.write_text("[]", encoding="utf-8")
            with self.assertRaises(profile_impl.ProfileError):
                profile_impl.read_profile(arr)

    def test_profile_read_rejects_bad_json_and_bad_version(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.json"
            bad.write_text("{nope", encoding="utf-8")
            with self.assertRaises(profile_impl.ProfileError):
                profile_impl.read_profile(bad)
            wrong = Path(d) / "wrong.json"
            wrong.write_text(json.dumps({"schema_version": "3.0"}), encoding="utf-8")
            with self.assertRaises(profile_impl.ProfileError):
                profile_impl.read_profile(wrong)

    def test_cli_migrate_writes_new_file_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "p.json"
            src.write_text(json.dumps(V1), encoding="utf-8")
            out = Path(d) / "out.json"
            rc = profile_impl.main(["migrate", "--profile", str(src), "--out", str(out)])
            self.assertEqual(rc, 0)
            target = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(target["schema_version"], "2.0")
            self.assertEqual(json.loads(src.read_text(encoding="utf-8")), V1)
            rc = profile_impl.main(["migrate", "--profile", str(src), "--out", str(out)])
            self.assertEqual(rc, 2, "overwriting an existing output must require --allow-overwrite")


class TestCalibration(unittest.TestCase):
    def ev(self, event_id, confidence, concept, application, date="2026-01-01T00:00:00+00:00"):
        return {"event_id": event_id, "date": date, "confidence_self_report": confidence,
                "rubric": {"concept": concept, "application": application}}

    def test_confidence_is_not_correctness(self):
        result = profile_impl.calibration([
            self.ev("a", 0.9, 2, 2),
            self.ev("b", 0.9, 0, 0),
        ])
        high = result["buckets"]["high"]
        self.assertEqual(high["n"], 2)
        self.assertEqual(high["accuracy"], 0.5)
        self.assertEqual(high["mean_confidence"], 0.9)
        self.assertGreater(result["mean_overconfidence_gap"], 0.2)

    def test_unscorable_events_not_credited(self):
        result = profile_impl.calibration([
            self.ev("x", 0.9, None, None),
        ])
        self.assertEqual(result["events_analyzed"], 0)
        self.assertIsNone(result["mean_overconfidence_gap"])

    def test_bucket_boundaries(self):
        result = profile_impl.calibration([
            self.ev("l", 0.2, 2, 2),
            self.ev("m", 0.5, 0, 1),
            self.ev("h", 0.8, 1, 2),
        ])
        self.assertEqual(result["buckets"]["low"]["n"], 1)
        self.assertEqual(result["buckets"]["mid"]["n"], 1)
        self.assertEqual(result["buckets"]["high"]["n"], 1)

    def test_malformed_confidence_fails_closed(self):
        with self.assertRaises(profile_impl.ProfileError):
            profile_impl.calibration([self.ev("bad", 1.4, 2, 2)])
        with self.assertRaises(profile_impl.ProfileError):
            profile_impl.calibration([self.ev("bad", "certain", 2, 2)])

    def test_disclaimer_present_and_no_diagnosis(self):
        result = profile_impl.calibration([])
        self.assertIn("not correctness", result["disclaimer"])


if __name__ == "__main__":
    unittest.main()
