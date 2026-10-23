"""W4-03 deterministic *synthetic-only* scheduler evaluation.

This is a toy exponential-forgetting simulation, NOT evidence of improved
human retention. No learner records, network, randomness or filesystem writes
are involved. fixed_v1 remains the production default; adaptive_v2 is opt-in.
Python 3.9+ standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

import learnprint_scheduler as scheduler


PROFILES: Dict[str, Tuple[float, float]] = {
    "fragile": (1.5, 1.20),
    "steady": (4.0, 1.40),
    "durable": (10.0, 1.80),
}
POLICIES = ("fixed_v1", "adaptive_v2")
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _bounded_integer(name: str, value: int, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _draw(seed: int, profile: str, competency: str, attempt: int) -> float:
    """Stable pseudo-random quantile, independent of Python hash seed."""
    key = f"{seed}|{profile}|{competency}|{attempt}".encode("ascii")
    digest = hashlib.sha256(key).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def simulate(
    policy: str,
    profile: str,
    *,
    seed: int = 7,
    horizon_days: int = 90,
    max_reviews_per_day: int = 7,
    competencies: int = 8,
) -> Dict[str, Any]:
    """Run one deterministic toy cohort. Never infer real learning efficacy."""
    if policy not in POLICIES:
        raise ValueError("policy must be fixed_v1 or adaptive_v2")
    if profile not in PROFILES:
        raise ValueError("unknown synthetic profile")
    _bounded_integer("seed", seed, 0, 2**31 - 1)
    _bounded_integer("horizon_days", horizon_days, 1, 365)
    _bounded_integer("max_reviews_per_day", max_reviews_per_day, 1, 50)
    _bounded_integer("competencies", competencies, 1, 50)

    initial_strength, pass_gain = PROFILES[profile]
    states = {}
    for index in range(competencies):
        key = f"c{index:03d}"
        states[key] = {
            "strength": initial_strength,
            "last_review": START,
            "next_due": START + timedelta(days=1),
            "passed_delayed": 0,
            "failed_latest": False,
            "events": [],
            "attempts": 0,
        }

    reviews = passes = peak_daily_reviews = peak_due_backlog = 0
    for day in range(1, horizon_days + 1):
        now = START + timedelta(days=day)
        pending = [(state["next_due"], key) for key, state in states.items()]
        due_count = sum(1 for due, _ in pending if due <= now)
        peak_due_backlog = max(peak_due_backlog, due_count)
        selected = scheduler.select_due(pending, now, max_reviews_per_day)
        peak_daily_reviews = max(peak_daily_reviews, len(selected))

        for _, key in selected:
            state = states[key]
            elapsed = (now - state["last_review"]).total_seconds() / 86400.0
            recall_probability = math.exp(-elapsed / state["strength"])
            passed = _draw(seed, profile, key, state["attempts"]) < recall_probability
            state["attempts"] += 1
            reviews += 1
            if passed:
                passes += 1
                state["passed_delayed"] += 1
            state["failed_latest"] = not passed
            # This learning-strength update is a declared *synthetic assumption*.
            state["strength"] = min(
                365.0, max(1.0, state["strength"] * (pass_gain if passed else 0.85))
            )
            state["last_review"] = now
            score = 2 if passed else 1
            state["events"].append((now, {"concept": score, "application": score}))
            decision = scheduler.schedule_from_policy(
                demonstrated=True,
                last_eligible_date=now,
                passed_delayed=state["passed_delayed"],
                failed_latest=state["failed_latest"],
                policy_version=policy,
                delayed_events=state["events"],
            )
            state["next_due"] = datetime.fromisoformat(decision["due_at"])

    end = START + timedelta(days=horizon_days)
    retention = sum(
        math.exp(
            -((end - state["last_review"]).total_seconds() / 86400.0)
            / state["strength"]
        )
        for state in states.values()
    ) / competencies
    return {
        "policy_version": policy,
        "synthetic_profile": profile,
        "reviews": reviews,
        "simulated_passes": passes,
        "simulated_pass_rate": round(passes / reviews, 6) if reviews else None,
        "retention_probability_proxy": round(retention, 6),
        "peak_reviews_per_day": peak_daily_reviews,
        "peak_due_backlog": peak_due_backlog,
        "overdue_at_horizon": sum(1 for state in states.values() if state["next_due"] <= end),
    }


def run_benchmark(
    *,
    seed: int = 7,
    horizon_days: int = 90,
    max_reviews_per_day: int = 7,
    competencies: int = 8,
) -> Dict[str, Any]:
    """Compare policies under shared assumptions, never assert superiority."""
    _bounded_integer("seed", seed, 0, 2**31 - 1)
    _bounded_integer("horizon_days", horizon_days, 1, 365)
    _bounded_integer("max_reviews_per_day", max_reviews_per_day, 1, 50)
    _bounded_integer("competencies", competencies, 1, 50)
    results = {
        profile: {
            policy: simulate(
                policy, profile, seed=seed, horizon_days=horizon_days,
                max_reviews_per_day=max_reviews_per_day, competencies=competencies,
            )
            for policy in POLICIES
        }
        for profile in PROFILES
    }
    return {
        "kind": "synthetic_scheduler_diagnostic",
        "evidence": "SIMULATED_ONLY_NOT_HUMAN_EFFICACY",
        "decision": "INSUFFICIENT_EMPIRICAL_EVIDENCE_FOR_ADAPTIVE_OPT_IN",
        "production_default": "fixed_v1",
        "model": (
            "Toy exponential forgetting with seeded quantile draws, profile-specific "
            "initial strength and heuristic pass/fail updates. These parameters are "
            "assumptions, not calibrated from learners."
        ),
        "seed": seed,
        "horizon_days": horizon_days,
        "max_reviews_per_day": max_reviews_per_day,
        "competencies_per_profile": competencies,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--max-per-day", type=int, default=7)
    parser.add_argument("--competencies", type=int, default=8)
    args = parser.parse_args()
    try:
        report = run_benchmark(
            seed=args.seed, horizon_days=args.days,
            max_reviews_per_day=args.max_per_day, competencies=args.competencies,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
