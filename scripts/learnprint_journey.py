"""Deterministic validation for learner-visible course plans. Python stdlib only."""
from __future__ import annotations


MODES = {"hands_on", "role_play", "physical", "written", "simulation"}


def validate_units(units, competency_ids):
    """Return ordered unit IDs or raise ValueError. No mastery decisions here."""
    if not isinstance(units, list) or not units:
        raise ValueError("course plan needs at least one unit")
    known = set(competency_ids)
    graph = {}
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("plan unit must be an object")
        for key in ("unit_id", "title", "outcome", "hands_on", "success_check"):
            if not isinstance(unit.get(key), str) or not unit[key].strip():
                raise ValueError("plan unit missing " + key)
        uid = unit["unit_id"]
        if uid in graph:
            raise ValueError("duplicate unit_id " + uid)
        deps = unit.get("requires")
        comps = unit.get("competency_ids")
        if (not isinstance(deps, list) or not isinstance(comps, list)
                or not comps or len(deps) != len(set(deps))
                or len(comps) != len(set(comps))
                or any(not isinstance(v, str) or not v.strip() for v in deps + comps)):
            raise ValueError("invalid unit dependency/competency IDs")
        if any(v not in known for v in comps):
            raise ValueError("unknown competency in plan " + uid)
        if unit.get("practice_mode") not in MODES:
            raise ValueError("invalid practice_mode in " + uid)
        graph[uid] = deps
    done, busy, order = set(), set(), []
    def visit(uid):
        if uid not in graph:
            raise ValueError("missing prerequisite " + uid)
        if uid in busy:
            raise ValueError("cycle in course prerequisites at " + uid)
        if uid in done:
            return
        busy.add(uid)
        for dep in graph[uid]:
            visit(dep)
        busy.remove(uid)
        done.add(uid)
        order.append(uid)
    for uid in graph:
        visit(uid)
    return order


def preserve_existing(old, proposed):
    """Append/insertion is allowed; silent removal or reassignment is not."""
    if not isinstance(old, list):
        raise ValueError("existing plan malformed")
    by_new = {v["unit_id"]: v for v in proposed}
    for prior in old:
        if not isinstance(prior, dict) or not isinstance(prior.get("unit_id"), str):
            raise ValueError("existing plan malformed; manual recovery required")
        uid = prior["unit_id"]
        if uid not in by_new:
            raise ValueError("existing unit cannot be removed: " + uid)
        before = prior.get("competency_ids")
        if before and set(before) != set(by_new[uid]["competency_ids"]):
            raise ValueError("existing competency linkage cannot change: " + uid)
