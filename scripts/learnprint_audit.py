"""Read-only, conservative Learnprint method audit.

PASS applies only to machine-checkable local artifacts. A tutor can fake
self-reported activity logs, so pedagogical compliance cannot auto-PASS.
No network, global memory, or third-party dependencies.
"""


def check(status, evidence, note):
    return {"status": status, "evidence": evidence, "note": note}


def build_report(course_id, method, sessions, lesson_units, activities,
                 evidence_events, selected_session=None, transcript=None,
                 state_problem=None):
    matching = [s for s in sessions if s["course_id"] == course_id]
    if selected_session:
        matching = [s for s in matching if s["session_id"] == selected_session]
    session = matching[-1] if matching else None
    checks = {}
    checks["course_state"] = check(
        "FAIL" if state_problem else "PASS",
        [] if state_problem else [course_id],
        state_problem or "Course state identity and competency structure validated")
    if session is None:
        checks["method_receipt"] = check(
            "NOT_VERIFIED", [], "No method-session receipt for requested course/session")
    else:
        same = (session["effective_fingerprint"] == method["effective_fingerprint"]
                and session["legacy_fingerprint"] == method["fingerprint"]
                and session["method_source"] == method["source"]
                and session["method_revision"] == method["method_revision"])
        checks["method_receipt"] = check(
            "PASS" if same else "FAIL",
            [session["session_id"]],
            "Recorded method configuration matches current active method"
            if same else "Method changed or mismatched since session started; inspect revisions")
    checks["syllabus_exists"] = check(
        "PASS" if lesson_units else "NOT_VERIFIED",
        [u["unit_id"] for u in lesson_units] if lesson_units else [],
        "Validated structured syllabus exists" if lesson_units
        else "No structured syllabus; cannot verify roadmap even exists")
    sid = session["session_id"] if session else None
    relevant_notes = [x for x in activities if sid and x.get("session_id") == sid]
    relevant_evidence = [x for x in evidence_events
                         if sid and x.get("session_id") == sid
                         and (x.get("course_id") == course_id
                              or x.get("topic_id") == course_id)]
    counts = {name: sum(x["kind"] == name for x in relevant_notes)
              for name in ("covered", "practice", "question", "clarification")}
    checks["logged_activity"] = check(
        "PASS" if relevant_notes else "NOT_VERIFIED",
        [x["event_id"] for x in relevant_notes],
        "Agent-reported lesson activities exist, but are not independently authenticated"
        if relevant_notes else "No session-linked lesson activities")
    checks["recorded_practice"] = check(
        "PASS" if counts["practice"] else "NOT_VERIFIED",
        [x["event_id"] for x in relevant_notes if x["kind"] == "practice"],
        "Practice was logged, not independently proven to have occurred"
        if counts["practice"] else "No session-linked practice log")
    checks["recorded_assessment"] = check(
        "PASS" if relevant_evidence else "NOT_VERIFIED",
        [x["event_id"] for x in relevant_evidence],
        "Trusted ledger contains graded or ungraded responses; scoring correctness not authenticated"
        if relevant_evidence else "No session-linked canonical learner response")
    for key, note in (
        ("roadmap_shown_to_learner", "A stored plan does not prove the agent displayed it"),
        ("learner_preferences_followed", "Configuration and agent notes do not attest language, analogy, feedback or pacing"),
        ("confusion_handled_correctly", "Requires an independent review of actual learner-tutor exchanges"),
        ("hands_on_actually_performed", "Agent-written practice notes cannot prove a real-world or tool action"),
        ("rubric_fairness", "A recorded rubric cannot independently prove grading correctness"),
    ):
        checks[key] = check("NOT_VERIFIED", [], note)
    if transcript is not None:
        checks["transcript_available"] = check(
            "PASS", [transcript["sha256"]],
            "Transcript bytes were supplied for human review; untrusted export not auto-graded")
    else:
        checks["transcript_available"] = check(
            "NOT_VERIFIED", [], "No independent session transcript supplied")
    status = ("FAIL" if any(v["status"] == "FAIL" for v in checks.values())
              else "NOT_VERIFIED")
    return {"course_id": course_id, "session_id": sid, "overall": status,
            "method_source": method["source"],
            "method_revision": method["method_revision"],
            "effective_fingerprint": method["effective_fingerprint"],
            "checks": checks, "activity_counts": counts,
            "limitations": [
                "PASS means the specified local artifact exists or matches; not proof of teaching quality",
                "Tutor-authored notes and optional transcripts can be incomplete or forged",
                "Behavioral adherence cannot be fully auto-certified; human/independent review required",
            ]}
