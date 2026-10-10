#!/usr/bin/env python3
"""Learnprint local validator/record keeper. Python stdlib only; no network or grading AI."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"unknown", "emerging", "demonstrated", "retention_due", "maintained", "needs_review"}
ASSESSMENT = {"unassessed", "provisional", "assessed"}
ORIGINS = {"observed_task", "self_report", "source_document"}
VERIFICATIONS = {"observed", "reported", "independently_checked", "unverified"}
HELP = {"none", "hint", "worked_example", "solution"}
TYPES = {"recognition", "causal_explanation", "independent_application", "novel_transfer", "delayed_retrieval", "debugging", "decision"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, obj, overwrite=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise ValueError(f"Refusing to overwrite {path}")
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_profile(p):
    errs = []
    for k in ("schema_version", "profile_id", "assessment_status", "public_template", "evidence_quality", "observed_claims", "evidence", "instruction_defaults"):
        if k not in p: errs.append("missing " + k)
    if errs: return errs
    if p["schema_version"] != "1.0": errs.append("unsupported schema_version")
    if p["assessment_status"] not in ASSESSMENT: errs.append("invalid assessment_status")
    if p["evidence_quality"] not in {"limited", "moderate", "strong"}: errs.append("invalid evidence_quality")
    if not isinstance(p["public_template"], bool): errs.append("public_template must be boolean")
    if not isinstance(p["instruction_defaults"], dict): errs.append("instruction_defaults must be object")
    if not isinstance(p["evidence"], list) or not isinstance(p["observed_claims"], list):
        return errs + ["evidence and observed_claims must be arrays"]
    ids = set()
    for e in p["evidence"]:
        if not isinstance(e, dict): errs.append("evidence entry not object"); continue
        for x in ("id", "description", "source"):
            if not isinstance(e.get(x), str) or not e[x].strip(): errs.append("bad evidence " + x)
        if e.get("origin") not in ORIGINS: errs.append("invalid evidence origin")
        if e.get("verification") not in VERIFICATIONS: errs.append("invalid verification")
        if e.get("origin") == "self_report" and e.get("verification") in {"observed", "independently_checked"}:
            errs.append("self_report cannot be upgraded to observed without a task")
        if e.get("id") in ids: errs.append("duplicate evidence id")
        ids.add(e.get("id"))
    cids = set()
    for c in p["observed_claims"]:
        if not isinstance(c, dict): errs.append("claim entry not object"); continue
        if c.get("id") in cids: errs.append("duplicate claim id")
        cids.add(c.get("id"))
        if c.get("category") not in {"observed", "reported_preference", "hypothesis"}: errs.append("invalid claim category")
        if not isinstance(c.get("claim"), str) or not c["claim"].strip(): errs.append("claim missing statement")
        if not c.get("evidence_ids") or not isinstance(c["evidence_ids"], list): errs.append("claim missing evidence ids")
        else:
            for ref in c["evidence_ids"]:
                if ref not in ids: errs.append(f"claim missing linked evidence: {ref}")
        if c.get("category") == "observed":
            for ref in c.get("evidence_ids", []):
                matched = next((e for e in p["evidence"] if e.get("id") == ref), {})
                if matched.get("origin") == "self_report": errs.append(f"observed claim {c.get('id')} backed by self-report")
    if p["assessment_status"] == "assessed" and not p["observed_claims"]:
        errs.append("assessed profile requires evidence-linked claims")
    if p["public_template"] and p["assessment_status"] == "assessed":
        errs.append("public founder template must not claim assessed learner-specific best method")
    return errs


def validate_topic(p):
    errs=[]
    for k in ("schema_version", "topic_id", "goal", "learning_scope", "syllabus"):
        if k not in p: errs.append("missing " + k)
    if errs: return errs
    if p["schema_version"] != "1.0": errs.append("unsupported schema_version")
    ids=set()
    for x in p["learning_scope"]:
        if x.get("status") not in STATUSES: errs.append("bad competency status")
        if not x.get("id") or x["id"] in ids: errs.append("bad/duplicate competency id")
        ids.add(x.get("id"))
    return errs


def events_read(path):
    if not path.exists(): return []
    out=[]
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: item=json.loads(line)
        except json.JSONDecodeError as e: raise ValueError(f"events.jsonl line {lineno}: {e}")
        out.append(item)
    return out


def validate_event(e):
    errs=[]
    for key in ("event_id", "date", "topic_id", "competency_id", "task_type", "observed_answer", "help_level", "rubric", "feedback", "grader", "evidence_origin"):
        if key not in e: errs.append("missing event."+key)
    if errs: return errs
    if e["task_type"] not in TYPES: errs.append("invalid event.task_type")
    if e["help_level"] not in HELP: errs.append("invalid event.help_level")
    if e["grader"] not in {"ai_reviewed", "human_reviewed", "not_graded"}: errs.append("invalid event.grader")
    if e["evidence_origin"] not in {"observed_response", "self_report"}: errs.append("invalid event origin")
    if not isinstance(e["observed_answer"], str) or not e["observed_answer"].strip(): errs.append("missing actual observed answer")
    if not isinstance(e["rubric"], dict): errs.append("rubric must be object")
    else:
        for k in ("concept", "mechanism", "application", "transfer"):
            if e["rubric"].get(k) not in (0,1,2,None): errs.append("invalid rubric."+k)
    try:
        d=dt.datetime.fromisoformat(e["date"])
        if d.tzinfo is None: errs.append("event timestamp must have timezone")
    except (ValueError, TypeError): errs.append("invalid timestamp")
    if e.get("is_synthetic_example", False) and e.get("grader") == "human_reviewed":
        # fixtures are allowed but excluded from real scoring
        pass
    return errs


def progress(topic, events, now=None):
    """Conservative evidence-derived progress; not a semantic correctness verifier."""
    now = now or dt.datetime.now(dt.timezone.utc)
    by_comp={}
    for e in events:
        if e.get("topic_id") != topic.get("topic_id") or e.get("is_synthetic_example"): continue
        if validate_event(e): continue
        by_comp.setdefault(e["competency_id"], []).append(e)
    results=[]
    for c in topic.get("learning_scope", []):
        ev=sorted(by_comp.get(c["id"], []),key=lambda x:x["date"])
        independent = [x for x in ev if x["help_level"] == "none" and x["grader"] == "human_reviewed" and x["evidence_origin"] == "observed_response"]
        application = any(x["task_type"] == "independent_application" and x["rubric"].get("application") == 2 for x in independent)
        transfer = any(x["task_type"] == "novel_transfer" and x["rubric"].get("transfer") == 2 for x in independent)
        delayed = [x for x in independent if x["task_type"] == "delayed_retrieval" and all(v == 2 for v in (x["rubric"].get("concept"),x["rubric"].get("application")))]
        if not ev: status="unknown"
        elif delayed and application and transfer: status="maintained"
        elif application and transfer: status="demonstrated"
        else: status="emerging"
        due=c.get("due_at")
        if status in {"demonstrated", "maintained"} and due:
            try:
                t=dt.datetime.fromisoformat(due)
                if t.tzinfo is not None and t<=now: status="retention_due"
            except ValueError: pass
        results.append({"id":c["id"],"name":c["name"],"status":status,"observations":len(ev),"independent_pass_application":application,"independent_pass_transfer":transfer,"delayed_pass":bool(delayed)})
    denominator=len(results)
    eligible=sum(x["status"] in {"demonstrated", "maintained", "retention_due"} for x in results)
    maintained=sum(x["status"] == "maintained" for x in results)
    return {"topic_id":topic["topic_id"], "bounded_competencies":denominator,
            "observed_immediate_coverage_percent":round(eligible/denominator*100,1) if denominator else None,
            "observed_maintained_percent":round(maintained/denominator*100,1) if denominator else None,
            "important_note":"These metrics require human-reviewed recorded answers and do not assert permanent whole-field mastery.",
            "competencies":results}


def cmd_validate(a):
    p=load(a.profile)
    err=validate_profile(p)
    if a.topic: err.extend(validate_topic(load(a.topic)))
    if a.events:
        for i,e in enumerate(events_read(Path(a.events)),1): err.extend(f"event {i}: {x}" for x in validate_event(e))
    print("VALID" if not err else "INVALID\n"+"\n".join(err))
    return 0 if not err else 2


def cmd_init(a):
    path=Path(a.workspace).expanduser().resolve()
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Nonempty workspace; refuse to overwrite: {path}")
    path.mkdir(parents=True, exist_ok=True)
    for name, rel in (("learner/profile.json","learner-profile-starter.json"),("reviews.json","review-queue.json")):
        dest=path/name; dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/"templates"/rel,dest)
    dump(path/"manifest.json", {"schema_version":"1.0","active_topic":None,
        "profile_path":"learner/profile.json","events_path":"events.jsonl",
        "reviews_path":"reviews.json", "topics_dir":"topics",
        "profile_priority":"local assessed profile > public founder fallback; never publish private state"})
    (path/"topics").mkdir()
    (path/"events.jsonl").write_text("",encoding="utf-8")
    (path/"HANDOFF.md").write_text("# Learnprint handoff\n\nNo verified completed learning events. Next: assessment or select a topic.\n",encoding="utf-8")
    print(f"CREATED private workspace: {path}")
    return 0


def cmd_generate(a):
    w=Path(a.workspace).expanduser().resolve()
    p=load(w/"learner/profile.json")
    err=validate_profile(p)
    if err: raise ValueError("Invalid local profile: "+"; ".join(err))
    if p["public_template"] or p["assessment_status"] != "assessed":
        raise ValueError("Personal skill generation requires a local assessed non-public profile")
    if (len(p["observed_claims"]) < 2 or
        sum(e.get("origin") == "observed_task" for e in p["evidence"]) < 2 or
        not any(c.get("category") == "observed" for c in p["observed_claims"])):
        raise ValueError("Need >=2 claims, >=2 observed-task entries and >=1 observation-backed claim")
    if not a.approve:
        raise ValueError("Explicit local file write approval required: --approve")
    dest=w/".agents/skills/learnprint-personal"
    if dest.exists(): raise ValueError(f"Will not overwrite existing personal skill: {dest}")
    (dest/"references").mkdir(parents=True)
    (dest/"SKILL.md").write_text("""---
name: learnprint-personal
description: Apply the assessed learner's private evidence-linked teaching preferences and topic-specific tests to any learning request. Use for personalized study, practice, review, and progress tracking.
license: MIT
---

# Learnprint Personal (local)

1. Read `references/profile.json` and `references/TEACHING.md` before teaching.
2. This profile overrides the public founder defaults **only for this learner and only locally**.
3. Distinguish observed performance, reported preferences, hypothesis, and unknown. Re-test competence on each new topic.
4. Teach with accurate close analogies (and limits), functional diagrams, concrete examples, technical mechanism, guided hands-on, independent transfer and spaced retrieval.
5. Record evidence and track bounded competencies; do not claim fixed learning styles or whole-subject permanent mastery.
6. Do not publish learner data or write outside the approved workspace.
""", encoding="utf-8")
    shutil.copyfile(w/"learner/profile.json",dest/"references/profile.json")
    shutil.copyfile(ROOT/"protocols/TEACHING.md",dest/"references/TEACHING.md")
    shutil.copyfile(ROOT/"protocols/REVIEW.md",dest/"references/REVIEW.md")
    print(f"GENERATED standalone personal skill: {dest}; not installed globally, not pushed")
    return 0


def cmd_new_topic(a):
    w=Path(a.workspace).expanduser().resolve()
    if not (w/"manifest.json").exists(): raise ValueError("Initialize workspace first")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.topic): raise ValueError("topic ID must be lower-case kebab-case")
    if not a.approve: raise ValueError("Explicit local write approval required: --approve")
    scope=[]
    for raw in a.competency:
        if ":" not in raw: raise ValueError("--competency must be id:observable outcome")
        cid,label=raw.split(":",1)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",cid) or not label.strip():
            raise ValueError("Invalid competency slug/name")
        scope.append({"id":cid,"name":label.strip(),"status":"unknown","evidence_ids":[],"due_at":None})
    if len({x["id"] for x in scope}) != len(scope):raise ValueError("duplicate competency id")
    out=w/"topics"/a.topic
    if out.exists():raise ValueError(f"Refusing to overwrite topic: {out}")
    out.mkdir(parents=True)
    payload={"schema_version":"1.0","topic_id":a.topic,"goal":a.goal,
             "assumptions":[],"learning_scope":scope,"syllabus":[],
             "question_parking_lot":[],"sources":[],"last_session":None}
    dump(out/"state.json",payload)
    (out/"map.mmd").write_text("flowchart TD\n    GOAL[\"" + a.goal.replace('"', "'") + "\"]\n",encoding="utf-8")
    (out/"SYLLABUS.md").write_text("# "+a.topic+"\n\nSyllabus awaits learner-specific prerequisites and sourced research.\n",encoding="utf-8")
    (out/"HANDOFF.md").write_text("# Topic handoff\n\nGoal: "+a.goal+"\nNo learning evidence has been recorded yet.\n",encoding="utf-8")
    print(f"CREATED topic: {out} with {len(scope)} scoped competencies; none claimed mastered")
    return 0


def reviews_from_events(topics, events):
    """Derive upcoming spaced checks; no claimed delivery/reminder."""
    out=[]
    for topic in topics:
        for c in topic.get("learning_scope", []):
            relevant=[e for e in events if e.get("topic_id")==topic["topic_id"]
                and e.get("competency_id")==c["id"]
                and e.get("grader")=="human_reviewed"
                and e.get("help_level")=="none"
                and e.get("evidence_origin")=="observed_response"
                and not e.get("is_synthetic_example") and not validate_event(e)]
            applied=any(e["task_type"]=="independent_application" and e["rubric"].get("application")==2 for e in relevant)
            transferred=any(e["task_type"]=="novel_transfer" and e["rubric"].get("transfer")==2 for e in relevant)
            if not(applied and transferred): continue
            last=max(relevant,key=lambda x:x["date"])
            passed_delayed=sum(e["task_type"]=="delayed_retrieval" and
                               e["rubric"].get("concept")==2 and e["rubric"].get("application")==2
                               for e in relevant)
            failed_latest=last["task_type"]=="delayed_retrieval" and (
                last["rubric"].get("concept") != 2 or last["rubric"].get("application") != 2)
            intervals=[1,3,7,21]
            days=1 if failed_latest else intervals[min(passed_delayed,3)]
            due=dt.datetime.fromisoformat(last["date"]) + dt.timedelta(days=days)
            out.append({"topic_id":topic["topic_id"],"competency_id":c["id"],
                        "due_at":due.isoformat(),"reason":"retrieval after observed independently assessed performance",
                        "interval_days":days,"based_on_event":last["event_id"],"delivery":"manual; no automatic notification"})
    return {"schema_version":"1.0","reviews":out}


def cmd_plan_reviews(a):
    w=Path(a.workspace).expanduser().resolve()
    manifest=load(w/"manifest.json")
    events=events_read(w/manifest["events_path"])
    topics=[load(p) for p in sorted((w/manifest["topics_dir"]).glob("*/state.json"))]
    if any(validate_event(e) for e in events): raise ValueError("Invalid event records")
    if any(validate_topic(t) for t in topics): raise ValueError("Invalid topic records")
    result=reviews_from_events(topics,events)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.dry_run: return 0
    if not a.approve: raise ValueError("Explicit approval required to save review queue: --approve")
    dump(w/manifest["reviews_path"],result,overwrite=True)
    return 0

def cmd_report(a):
    w=Path(a.workspace).expanduser().resolve()
    manifest=load(w/"manifest.json")
    profile=load(w/manifest["profile_path"])
    errs=validate_profile(profile)
    if errs: raise ValueError("Invalid profile: "+"; ".join(errs))
    event_path=w/manifest["events_path"]
    events=events_read(event_path)
    for i,e in enumerate(events,1):
        errs=validate_event(e)
        if errs: raise ValueError(f"Invalid event {i}: "+"; ".join(errs))
    states=[]
    queue=load(w/manifest["reviews_path"]) if (w/manifest["reviews_path"]).exists() else {"reviews":[]}
    for path in sorted((w/manifest["topics_dir"]).glob("*/state.json")):
        topic=load(path)
        for comp in topic.get("learning_scope",[]):
            next_review=next((r for r in queue.get("reviews", []) if r["topic_id"]==topic["topic_id"] and r["competency_id"]==comp["id"]),None)
            if next_review: comp["due_at"]=next_review["due_at"]
        errs=validate_topic(topic)
        if errs: raise ValueError(f"Invalid topic {path}: "+"; ".join(errs))
        states.append(progress(topic,events))
    res={"profile_status":profile["assessment_status"],"effective_profile":"local" if profile["assessment_status"] in {"assessed","provisional"} else "founder_fallback_until_assessed", "event_count":len(events),"topics":states}
    print(json.dumps(res,ensure_ascii=False,indent=2))
    return 0


def cmd_record(a):
    w=Path(a.workspace).expanduser().resolve()
    p=w/"events.jsonl"
    if not (w/"manifest.json").exists(): raise ValueError("Initialize workspace first")
    if not a.approve: raise ValueError("Explicit write approval required: --approve")
    rubric=json.loads(a.rubric)
    e={"event_id":a.event_id,"date":dt.datetime.now(dt.timezone.utc).isoformat(),
       "topic_id":a.topic,"competency_id":a.competency,"task_type":a.task_type,
       "expected_reasoning":a.expected,"observed_answer":a.answer,"rubric":rubric,
       "help_level":a.help,"feedback":a.feedback,"grader":a.grader,
       "evidence_origin":"observed_response", "confidence_self_report":a.confidence,
       "is_synthetic_example":False}
    errs=validate_event(e)
    if errs: raise ValueError("Invalid event: "+"; ".join(errs))
    known={x.get("event_id") for x in events_read(p)}
    if e["event_id"] in known: raise ValueError("Duplicate event_id")
    with p.open("a",encoding="utf-8") as f: f.write(json.dumps(e,ensure_ascii=False)+"\n")
    print(f"RECORDED: {a.event_id}; grading supplied by {a.grader}, NOT independently verified by script")
    return 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate");v.add_argument("--profile",required=True);v.add_argument("--topic");v.add_argument("--events");v.set_defaults(func=cmd_validate)
    ini=sub.add_parser("init");ini.add_argument("--workspace",required=True);ini.set_defaults(func=cmd_init)
    nt=sub.add_parser("new-topic");nt.add_argument("--workspace",required=True);nt.add_argument("--topic",required=True)
    nt.add_argument("--goal",required=True);nt.add_argument("--competency",action="append",required=True)
    nt.add_argument("--approve",action="store_true");nt.set_defaults(func=cmd_new_topic)
    g=sub.add_parser("generate");g.add_argument("--workspace",required=True);g.add_argument("--approve",action="store_true");g.set_defaults(func=cmd_generate)
    r=sub.add_parser("report");r.add_argument("--workspace",required=True);r.set_defaults(func=cmd_report)
    rr=sub.add_parser("plan-reviews");rr.add_argument("--workspace",required=True)
    rr.add_argument("--dry-run",action="store_true");rr.add_argument("--approve",action="store_true")
    rr.set_defaults(func=cmd_plan_reviews)
    rec=sub.add_parser("record")
    for key in ("workspace","event-id","topic","competency","task-type","answer","rubric","expected","feedback"):
        rec.add_argument("--"+key,required=True)
    rec.add_argument("--grader",choices=["ai_reviewed","human_reviewed","not_graded"],default="not_graded")
    rec.add_argument("--help-level",dest="help",choices=sorted(HELP),default="none")
    rec.add_argument("--confidence",type=int);rec.add_argument("--approve",action="store_true");rec.set_defaults(func=cmd_record)
    a=p.parse_args()
    try: return a.func(a)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("ERROR:",e,file=sys.stderr);return 2

if __name__ == "__main__": sys.exit(main())
