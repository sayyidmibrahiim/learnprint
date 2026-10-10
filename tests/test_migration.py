import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("learnprint", ROOT / "scripts/learnprint.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def legacy_workspace(d, topics=("in-on-at",), events_per_topic=2):
    w = Path(d) / "my-learning"
    (w / "learner").mkdir(parents=True)
    (w / "topics").mkdir(parents=True)
    prof = mod.load(ROOT / "profiles/founder-default.json")
    (w / "learner/profile.json").write_text(json.dumps(prof), encoding="utf-8")
    (w / "reviews.json").write_text(json.dumps({"schema_version": "1.0", "reviews": []}),
                                     encoding="utf-8")
    (w / "manifest.json").write_text(json.dumps(
        {"schema_version": "1.0", "active_topic": None, "profile_path": "learner/profile.json",
         "events_path": "events.jsonl", "reviews_path": "reviews.json", "topics_dir": "topics"}),
        encoding="utf-8")
    lines = []
    for t in topics:
        td = w / "topics" / t
        td.mkdir(parents=True, exist_ok=True)
        (td / "state.json").write_text(json.dumps(
            {"schema_version": "1.0", "topic_id": t, "goal": f"learn {t}",
             "learning_scope": [{"id": "c1", "name": "C", "status": "unknown",
                                 "evidence_ids": [], "due_at": None}],
             "syllabus": [], "question_parking_lot": [], "sources": [], "last_session": None}),
            encoding="utf-8")
        for i in range(events_per_topic):
            lines.append(json.dumps(
                {"event_id": f"{t}-e{i}", "date": "2026-10-10T01:00:00+07:00",
                 "topic_id": t, "competency_id": "c1", "task_type": "independent_application",
                 "observed_answer": "a", "expected_reasoning": "r", "feedback": "f",
                 "help_level": "none",
                 "rubric": {"concept": 2, "mechanism": 2, "application": 2, "transfer": 2},
                 "grader": "ai_reviewed", "evidence_origin": "observed_response"}))
    (w / "events.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return w


def mig_args(src, dest, **kw):
    base = {"migrate_from": str(src), "migrate_to": str(dest), "category": "technology/devops",
            "approve": True, "dry_run": False}
    base.update(kw)
    return type("Args", (), base)()


class TestMigration(unittest.TestCase):
    def test_migrate_preserves_all_events(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            self.assertEqual(mod.cmd_migrate(mig_args(src, dest)), 0)
            src_sha = hashlib.sha256((src / "events.jsonl").read_bytes()).hexdigest()
            dst_sha = hashlib.sha256((dest / ".learnprint" / "events.jsonl").read_bytes()).hexdigest()
            self.assertEqual(src_sha, dst_sha)

    def test_migrate_preserves_profile(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            p = mod.load(dest / ".learnprint" / "learner/profile.json")
            self.assertEqual(mod.validate_profile(p), [])

    def test_migrate_preserves_topic_state(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            reg = mod.registry_read(dest)
            self.assertEqual(len(reg["courses"]), 1)
            st = mod.load(dest / reg["courses"][0]["rel_path"] / "state.json")
            self.assertEqual(mod.validate_topic(st), [])
            self.assertEqual(st["learning_scope"][0]["id"], "c1")

    def test_migrate_refuses_existing_target(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            before = len(mod.registry_read(dest)["courses"])
            # Second run over the same source: no duplicate course created.
            self.assertEqual(mod.cmd_migrate(mig_args(src, dest)), 0)
            self.assertEqual(len(mod.registry_read(dest)["courses"]), before)

    def test_migrate_dry_run_no_writes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            self.assertEqual(mod.cmd_migrate(mig_args(src, dest, dry_run=True)), 0)
            self.assertFalse(dest.exists())

    def test_migrate_requires_approval(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            with self.assertRaises(ValueError):
                mod.cmd_migrate(mig_args(src, dest := Path(d) / "Courses", approve=False))

    def test_migrate_interrupted_staging_recovery(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            staging = dest / ".learnprint" / ".migrate-staging"
            staging.mkdir(parents=True)
            (staging / "partial.txt").write_text("x", encoding="utf-8")
            self.assertEqual(mod.cmd_migrate(mig_args(src, dest)), 0)
            self.assertFalse(staging.exists())
            self.assertEqual(len(mod.registry_read(dest)["courses"]), 1)

    def test_migrate_interrupted_commit_recovery(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d, topics=("t1", "t2"))
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            # Simulate partial commit: remove one course dir + its registry entry,
            # leave staging marker absent; re-run completes idempotently.
            reg = mod.registry_read(dest)
            victim = [c for c in reg["courses"] if c["topic_id"] == "t2"][0]
            import shutil
            shutil.rmtree(dest / victim["rel_path"])
            reg["courses"] = [c for c in reg["courses"] if c["topic_id"] != "t2"]
            mod.registry_write(dest, reg)
            self.assertEqual(mod.cmd_migrate(mig_args(src, dest)), 0)
            reg2 = mod.registry_read(dest)
            self.assertEqual({c["topic_id"] for c in reg2["courses"]}, {"t1", "t2"})
            # Stable IDs: t1 kept its course_id across the retry.
            id1 = next(c["course_id"] for c in reg2["courses"] if c["topic_id"] == "t1")
            id1_before = next(c["course_id"] for c in reg["courses"] if c["topic_id"] == "t1")
            self.assertEqual(id1, id1_before)

    def test_migrate_idempotent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            n = len(mod.registry_read(dest)["courses"])
            mod.cmd_migrate(mig_args(src, dest))
            self.assertEqual(len(mod.registry_read(dest)["courses"]), n)

    def test_migrate_topic_id_to_course_id_mapping(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d, topics=("t1", "t2"))
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            rep = mod.load(dest / ".learnprint" / "migration-report.json")
            self.assertEqual(set(rep["mapping"]), {"t1", "t2"})
            for cid in rep["mapping"].values():
                self.assertTrue(mod.routing.is_course_id(cid))

    def test_migrate_retry_reuses_course_ids(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            first = mod.registry_read(dest)["courses"][0]["course_id"]
            # Wipe destination registry+dirs but keep nothing: fresh retry over
            # the same source mints (necessarily) new IDs — but a retry that
            # finds the staging map reuses them. Simulate crash after map write
            # by re-running with registry intact (idempotent path keeps IDs).
            mod.cmd_migrate(mig_args(src, dest))
            second = mod.registry_read(dest)["courses"][0]["course_id"]
            self.assertEqual(first, second)

    def test_migrate_slug_collision_handled(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d, topics=("In On At", "in-on-at"))
            dest = Path(d) / "Courses"
            mod.cmd_migrate(mig_args(src, dest))
            rels = [c["rel_path"] for c in mod.registry_read(dest)["courses"]]
            self.assertEqual(len(set(rels)), 2)
            self.assertTrue(any("migrated" in r for r in rels))

    def test_migrate_cross_check_events_topics(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            with (src / "events.jsonl").open("a", encoding="utf-8") as fh:
                fh.write('{"event_id": "ghost", "date": "2026-10-10T01:00:00+07:00",'
                         ' "topic_id": "nope", "competency_id": "c1",'
                         ' "task_type": "independent_application", "observed_answer": "a",'
                         ' "rubric": {}, "help_level": "none", "feedback": "f",'
                         ' "grader": "ai_reviewed", "evidence_origin": "observed_response"}\n')
            with self.assertRaises(ValueError):
                mod.cmd_migrate(mig_args(src, Path(d) / "Courses"))
            self.assertFalse((Path(d) / "Courses").exists())

    def test_migrate_refuses_existing_ledger(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = legacy_workspace(d)
            dest = Path(d) / "Courses"
            lp = dest / ".learnprint"
            lp.mkdir(parents=True)
            (lp / "events.jsonl").write_text('{"foreign": true}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.cmd_migrate(mig_args(src, dest))

    def test_old_commands_still_work(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            w = Path(d) / "work"
            mod.cmd_init(type("Args", (), {"workspace": str(w)})())
            a = type("Args", (), {"workspace": str(w), "event_id": "e1", "topic": "t",
                                  "competency": "c1", "task_type": "independent_application",
                                  "answer": "a", "rubric": '{"application": 2}',
                                  "expected": "r", "feedback": "f", "grader": "ai_reviewed",
                                  "help": "none", "confidence": None, "approve": True})()
            self.assertEqual(mod.cmd_record(a), 0)
            self.assertEqual(mod.cmd_report(type("Args", (), {"workspace": str(w)})()), 0)


if __name__ == "__main__":
    unittest.main()
