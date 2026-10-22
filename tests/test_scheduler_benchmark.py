"""W4-03 synthetic scheduler benchmark regression and honesty gates."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import learnprint_scheduler_benchmark as benchmark  # noqa: E402


class TestSyntheticSchedulerBenchmark(unittest.TestCase):
    def test_seeded_replay_is_byte_deterministic(self):
        first = benchmark.run_benchmark(seed=17, horizon_days=70)
        second = benchmark.run_benchmark(seed=17, horizon_days=70)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_both_policies_and_all_profiles_are_compared(self):
        report = benchmark.run_benchmark(seed=3, horizon_days=60)
        self.assertEqual(set(report["results"]), set(benchmark.PROFILES))
        for profile, policies in report["results"].items():
            self.assertEqual(set(policies), {"fixed_v1", "adaptive_v2"})
            for policy, result in policies.items():
                with self.subTest(profile=profile, policy=policy):
                    self.assertEqual(result["policy_version"], policy)
                    self.assertGreater(result["reviews"], 0)
                    self.assertGreaterEqual(result["simulated_passes"], 0)
                    self.assertLessEqual(result["simulated_passes"], result["reviews"])
                    self.assertGreaterEqual(result["retention_probability_proxy"], 0.0)
                    self.assertLessEqual(result["retention_probability_proxy"], 1.0)

    def test_daily_workload_is_capped_even_when_backlog_exists(self):
        report = benchmark.run_benchmark(horizon_days=12, competencies=15, max_reviews_per_day=2)
        for policies in report["results"].values():
            for result in policies.values():
                self.assertLessEqual(result["peak_reviews_per_day"], 2)
                self.assertLessEqual(result["reviews"], 12 * 2)
        self.assertGreater(
            report["results"]["steady"]["fixed_v1"]["peak_due_backlog"], 2
        )

    def test_adaptive_policy_is_not_silently_equivalent_to_fixed(self):
        report = benchmark.run_benchmark(horizon_days=120)
        differences = [
            (policies["fixed_v1"]["reviews"], policies["fixed_v1"]["retention_probability_proxy"])
            != (policies["adaptive_v2"]["reviews"], policies["adaptive_v2"]["retention_probability_proxy"])
            for policies in report["results"].values()
        ]
        self.assertTrue(any(differences))

    def test_report_does_not_claim_real_human_efficacy(self):
        report = benchmark.run_benchmark(horizon_days=5, competencies=2)
        self.assertEqual(report["production_default"], "fixed_v1")
        self.assertEqual(report["evidence"], "SIMULATED_ONLY_NOT_HUMAN_EFFICACY")
        self.assertEqual(report["decision"], "INSUFFICIENT_EMPIRICAL_EVIDENCE_FOR_ADAPTIVE_OPT_IN")
        self.assertIn("assumptions", report["model"])

    def test_invalid_policy_profile_and_parameters_fail_closed(self):
        for policy, profile in [("magic", "steady"), ("fixed_v1", "unknown")]:
            with self.subTest(policy=policy, profile=profile):
                with self.assertRaises(ValueError):
                    benchmark.simulate(policy, profile)
        for kwargs in [
            {"seed": True}, {"seed": -1}, {"horizon_days": 0},
            {"horizon_days": 366}, {"max_reviews_per_day": 0},
            {"max_reviews_per_day": False}, {"competencies": 0},
            {"competencies": 51}, {"competencies": 2.5},
        ]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    benchmark.run_benchmark(**kwargs)

    def test_one_day_boundary_and_seed_sensitivity(self):
        one_day = benchmark.run_benchmark(seed=2, horizon_days=1, competencies=1)
        for policies in one_day["results"].values():
            for result in policies.values():
                self.assertEqual(result["reviews"], 1)
                self.assertIsInstance(result["retention_probability_proxy"], float)
        a = benchmark.run_benchmark(seed=1, horizon_days=90)
        b = benchmark.run_benchmark(seed=2, horizon_days=90)
        self.assertNotEqual(a["results"], b["results"])

    def test_cli_emits_json_without_writing_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "learnprint_scheduler_benchmark.py"),
                 "--seed", "5", "--days", "7", "--competencies", "2"],
                cwd=temp_dir, text=True, capture_output=True, timeout=20, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["horizon_days"], 7)
            self.assertEqual(list(Path(temp_dir).iterdir()), [])

    def test_cli_rejects_invalid_horizon(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "learnprint_scheduler_benchmark.py"),
             "--days", "0"],
            text=True, capture_output=True, timeout=20, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("horizon_days", result.stderr)


if __name__ == "__main__":
    unittest.main()
