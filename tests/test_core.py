import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("learnprint", ROOT/"scripts/learnprint.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestCore(unittest.TestCase):
    def test_founder_valid(self):
        self.assertEqual(mod.validate_profile(mod.load(ROOT/"profiles/founder-default.json")), [])

    def test_unassessed_valid(self):
        self.assertEqual(mod.validate_profile(mod.load(ROOT/"templates/learner-profile-starter.json")), [])

    def test_claim_must_link_evidence(self):
        p=mod.load(ROOT/"profiles/founder-default.json")
        p["observed_claims"][0]["evidence_ids"]=["E999"]
        self.assertTrue(any("missing linked evidence" in x for x in mod.validate_profile(p)))

    def test_reported_cannot_be_observed(self):
        p=mod.load(ROOT/"profiles/founder-default.json")
        p["observed_claims"][0]["evidence_ids"]=["E08"]
        self.assertTrue(any("self-report" in x for x in mod.validate_profile(p)))

    def test_topic_valid(self):
        self.assertEqual(mod.validate_topic(mod.load(ROOT/"templates/topic-state.json")), [])

    def test_event_validation(self):
        p=mod.load(ROOT/"templates/example-event.json")
        self.assertEqual(mod.validate_event(p), [])
        p["help_level"]="oracle"
        self.assertTrue(mod.validate_event(p))

    def test_no_events_means_no_mastery(self):
        p=mod.load(ROOT/"templates/topic-state.json")
        r=mod.progress(p,[])
        self.assertEqual(r["observed_immediate_coverage_percent"],0)
        self.assertEqual(r["observed_maintained_percent"],0)
        self.assertTrue(all(x["status"]=="unknown" for x in r["competencies"]))

    def _event(self, kind, n, scorekey):
        return {"event_id":str(n), "date":"2026-10-10T01:00:00+07:00", "topic_id":"sample-topic",
             "competency_id":"c1", "task_type":kind,"observed_answer":"Actual learner answer",
             "expected_reasoning":"Some expected reason", "feedback":"Checked carefully", "help_level":"none",
             "rubric":{"concept":2,"mechanism":2,"application":2,"transfer":2},
             "grader":"human_reviewed", "evidence_origin":"observed_response"}

    def test_independent_application_alone_insufficient(self):
        p=mod.load(ROOT/"templates/topic-state.json")
        r=mod.progress(p,[self._event("independent_application",1,"application")])
        self.assertEqual(r["competencies"][0]["status"],"emerging")

    def test_transfer_and_application_qualify_immediate_only(self):
        import datetime as _dt
        p=mod.load(ROOT/"templates/topic-state.json")
        e=[self._event("independent_application",1,"application"),self._event("novel_transfer",2,"transfer")]
        now=_dt.datetime.fromisoformat("2026-10-10T02:00:00+07:00")
        r=mod.progress(p,e,now=now)
        self.assertEqual(r["competencies"][0]["status"],"demonstrated")
        self.assertEqual(r["observed_maintained_percent"],0)
        # Delayed retrieval counts as retention only after the policy floor
        # elapses (contract change C5/F4: immediate re-tests are not retention).
        e.append(self._event("delayed_retrieval",3,"concept"))
        e[-1]["date"]="2026-10-11T03:00:00+07:00"
        now2=_dt.datetime.fromisoformat("2026-10-11T04:00:00+07:00")
        self.assertEqual(mod.progress(p,e,now=now2)["competencies"][0]["status"],"maintained")

    def test_ai_grade_is_provisional_not_verified(self):
        # Contract change C4/F4: AI-graded observed responses ARE usable
        # progress, honestly labeled provisional — never filtered out, never
        # presented as verified mastery. Replaces test_ai_grade_not_strong_mastery.
        import datetime as _dt
        p=mod.load(ROOT/"templates/topic-state.json")
        e=[self._event("independent_application",1,"application"),self._event("novel_transfer",2,"transfer")]
        e[1]["grader"]="ai_reviewed"
        now=_dt.datetime.fromisoformat("2026-10-10T02:00:00+07:00")
        r=mod.progress(p,e,now=now)
        self.assertEqual(r["competencies"][0]["status"],"demonstrated")
        self.assertEqual(r["competencies"][0]["basis"],"provisional")

    def test_synthetic_excluded(self):
        p=mod.load(ROOT/"templates/topic-state.json")
        e=[self._event("independent_application",1,"application"),self._event("novel_transfer",2,"transfer")]
        e[0]["is_synthetic_example"]=True
        self.assertEqual(mod.progress(p,e)["competencies"][0]["status"],"emerging")

    def test_review_scheduler_is_evidence_based_and_non_blocking(self):
        p=mod.load(ROOT/"templates/topic-state.json")
        self.assertEqual(mod.reviews_from_events([p],[])["reviews"],[])
        e=[self._event("independent_application",1,"application"),self._event("novel_transfer",2,"transfer")]
        due=mod.reviews_from_events([p],e)["reviews"]
        self.assertEqual(len(due),1)
        self.assertEqual(due[0]["interval_days"],1)
        self.assertEqual(due[0]["delivery"],"manual; no automatic notification")
        e.append(self._event("delayed_retrieval",3,"concept"))
        e[-1]["date"]="2026-10-11T03:00:00+07:00"
        self.assertEqual(mod.reviews_from_events([p],e)["reviews"][0]["interval_days"],3)

    def test_empty_workspace_init_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/"work"
            args=type("Args",(),{"workspace":str(w)})()
            mod.cmd_init(args)
            self.assertTrue((w/"learner/profile.json").exists())
            self.assertEqual(mod.load(w/"manifest.json")["active_topic"],None)
            with self.assertRaises(ValueError): mod.cmd_init(args)

    def test_new_topic_only_with_scope_and_approval(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/"work"
            mod.cmd_init(type("Args",(),{"workspace":str(w)})())
            a=type("Args",(),{"workspace":str(w),"topic":"in-on-at","goal":"Speak in meetings",
                "competency":["locate:Choose preposition by real location"],"approve":False})()
            with self.assertRaises(ValueError):mod.cmd_new_topic(a)
            a.approve=True
            mod.cmd_new_topic(a)
            state=mod.load(w/"topics/in-on-at/state.json")
            self.assertEqual(state["learning_scope"][0]["status"],"unknown")
            with self.assertRaises(ValueError):mod.cmd_new_topic(a)

    def test_cannot_generate_without_assessment(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/"work"
            mod.cmd_init(type("Args",(),{"workspace":str(w)})())
            with self.assertRaises(ValueError): mod.cmd_generate(type("Args",(),{"workspace":str(w),"approve":True})())

    def test_profile_precedence_assessed_over_founder(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            local = Path(d)/"profile.json"
            prof = mod.load(ROOT/"profiles/founder-default.json")
            prof["public_template"] = False
            prof["assessment_status"] = "assessed"
            mod.dump(local, prof)
            p, source = mod.resolve_effective_profile(local)
            self.assertEqual(source, "local")
            self.assertFalse(p["public_template"])

    def test_profile_precedence_provisional_over_founder(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            local = Path(d)/"profile.json"
            prof = mod.load(ROOT/"templates/learner-profile-starter.json")
            prof["assessment_status"] = "provisional"
            mod.dump(local, prof)
            p, source = mod.resolve_effective_profile(local)
            self.assertEqual(source, "local")

    def test_profile_precedence_unassessed_uses_founder_prefs(self):
        p, source = mod.resolve_effective_profile(ROOT/"templates/learner-profile-starter.json")
        self.assertTrue(source.startswith("founder_fallback"))
        self.assertTrue(p["public_template"])

    def test_profile_precedence_missing_uses_founder(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p, source = mod.resolve_effective_profile(Path(d)/"nope.json")
            self.assertEqual(source, "founder_fallback_missing")
            self.assertTrue(p["public_template"])

    def test_profile_precedence_invalid_uses_founder(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            local = Path(d)/"profile.json"
            local.write_text('{"broken": true}', encoding="utf-8")
            p, source = mod.resolve_effective_profile(local)
            self.assertTrue(source.startswith("founder_fallback"))
            self.assertTrue(p["public_template"])

    def test_personal_skill_optional_for_personalization(self):
        # Personalization works through direct profile read; no generated
        # skill needs to exist or be installed (plan Step 2.2, capability 1).
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            local = Path(d)/"profile.json"
            prof = mod.load(ROOT/"profiles/founder-default.json")
            prof["public_template"] = False
            prof["assessment_status"] = "assessed"
            mod.dump(local, prof)
            p, source = mod.resolve_effective_profile(local)
            self.assertEqual(source, "local")
            self.assertFalse((Path(d)/".agents/skills/learnprint-personal/SKILL.md").exists())

    def test_generated_skill_references_only_profile_and_protocols(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/"work"
            mod.cmd_init(type("Args",(),{"workspace":str(w)})())
            profile=mod.load(ROOT/"profiles/founder-default.json")
            profile["public_template"]=False
            profile["assessment_status"]="assessed"
            mod.dump(w/"learner/profile.json",profile,overwrite=True)
            # A distinctive raw learner answer lives in the workspace ledger...
            marker="zz-unique-learner-answer-9f8c"
            (w/"events.jsonl").write_text(
                '{"event_id":"e1","observed_answer":"%s"}\n' % marker, encoding="utf-8")
            mod.cmd_generate(type("Args",(),{"workspace":str(w),"approve":True})())
            # ...but must never be copied into the generated skill artifact.
            skill_dir=w/".agents/skills/learnprint-personal"
            for f in skill_dir.rglob("*"):
                if f.is_file() and f.suffix in {".md", ".json"}:
                    self.assertNotIn(marker, f.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/"work"
            mod.cmd_init(type("Args",(),{"workspace":str(w)})())
            with self.assertRaises(ValueError): mod.cmd_generate(type("Args",(),{"workspace":str(w),"approve":True})())

    def test_generate_assessed_profile_with_explicit_approval(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/"work"
            mod.cmd_init(type("Args",(),{"workspace":str(w)})())
            profile=mod.load(ROOT/"profiles/founder-default.json")
            profile["public_template"]=False
            profile["assessment_status"]="assessed"
            mod.dump(w/"learner/profile.json",profile,overwrite=True)
            a=type("Args",(),{"workspace":str(w),"approve":False})()
            with self.assertRaises(ValueError): mod.cmd_generate(a)
            a.approve=True
            mod.cmd_generate(a)
            skill=w/".agents/skills/learnprint-personal/SKILL.md"
            self.assertTrue(skill.exists())
            self.assertTrue((skill.parent/"references/profile.json").exists())
            with self.assertRaises(ValueError): mod.cmd_generate(a)

if __name__=="__main__":unittest.main()
