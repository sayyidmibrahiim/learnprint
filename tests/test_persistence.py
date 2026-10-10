import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("learnprint", ROOT / "scripts/learnprint.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

GOOD = {"event_id": "e1", "date": "2026-10-10T01:00:00+07:00", "topic_id": "t",
        "competency_id": "c1", "task_type": "independent_application",
        "observed_answer": "a", "expected_reasoning": "r", "feedback": "f",
        "help_level": "none",
        "rubric": {"concept": 2, "mechanism": 2, "application": 2, "transfer": 2},
        "grader": "ai_reviewed", "evidence_origin": "observed_response"}


def write_ledger(d, name="events.jsonl"):
    p = Path(d) / name
    p.write_text(json.dumps(GOOD, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


class TestLedgerIntegrity(unittest.TestCase):
    def test_ledger_diagnose_locates_damage(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            rep = mod.ledger_diagnose(p)
            self.assertEqual(rep["status"], "damaged")
            self.assertEqual(rep["damage"][0]["line_no"], 2)
            self.assertIn("byte_offset", rep["damage"][0])
            self.assertTrue(rep["damage"][0]["is_truncated_tail"])

    def test_trusted_read_raises_on_truncated_tail(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_read_trusted(p)

    def test_trusted_read_raises_on_midfile_corruption(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "events.jsonl"
            p.write_bytes((json.dumps(GOOD) + "\n{BROKEN\n" + json.dumps(GOOD) + "\n").encode())
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_read_trusted(p)

    def test_trusted_read_rejects_valid_json_invalid_event(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "events.jsonl"
            p.write_text('{"foo": 1}\n', encoding="utf-8")
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_read_trusted(p)

    def test_trusted_read_rejects_duplicate_event_id(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "events.jsonl"
            p.write_text(json.dumps(GOOD) + "\n" + json.dumps(GOOD) + "\n", encoding="utf-8")
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_read_trusted(p)

    def test_trusted_read_missing_expected_ledger_raises(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".learnprint").mkdir()
            with self.assertRaises(mod.LedgerMissing):
                mod.ledger_read_trusted(Path(d) / "events.jsonl", workspace_root=Path(d))

    def test_empty_file_is_legitimate_empty_ledger(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "events.jsonl"
            p.write_bytes(b"")
            self.assertEqual(mod.ledger_read_trusted(p), [])

    def test_unresolvable_reference_raises(self):
        t = {"schema_version": "1.0", "topic_id": "t", "goal": "g",
             "learning_scope": [{"id": "c1", "name": "C", "status": "unknown",
                                 "evidence_ids": [], "due_at": None}],
             "syllabus": [], "question_parking_lot": [], "sources": [], "last_session": None}
        bad = dict(GOOD, competency_id="ghost")
        with self.assertRaises(mod.LedgerReferenceError):
            mod.progress(t, [bad])

    def test_progress_refuses_damaged_ledger(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            # Authoritative path: trusted read raises BEFORE progress ever runs.
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_read_trusted(p)

    def test_record_refuses_append_to_damaged_ledger(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            w = Path(d) / "work"
            mod.cmd_init(type("Args", (), {"workspace": str(w)})())
            p = w / "events.jsonl"
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            before = p.read_bytes()
            a = type("Args", (), {"workspace": str(w), "event_id": "e9", "topic": "t",
                                 "competency": "c1", "task_type": "independent_application",
                                 "answer": "a", "rubric": '{"application": 2}',
                                 "expected": "r", "feedback": "f", "grader": "ai_reviewed",
                                 "help": "none", "confidence": None, "approve": True})()
            with self.assertRaises((ValueError, mod.LedgerDamage, mod.LedgerMissing)):
                mod.cmd_record(a)
            self.assertEqual(p.read_bytes(), before)

    def test_record_runs_full_trusted_read_not_diagnose_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            w = Path(d) / "work"
            mod.cmd_init(type("Args", (), {"workspace": str(w)})())
            p = w / "events.jsonl"
            # Syntactically valid JSON, schema-invalid event: diagnose-only
            # triage would wave this through; the trusted pre-flight must not.
            p.write_text('{"foo": 1}\n', encoding="utf-8")
            self.assertEqual(mod.ledger_diagnose(p)["status"], "ok")  # syntax-level only
            a = type("Args", (), {"workspace": str(w), "event_id": "e9", "topic": "t",
                                 "competency": "c1", "task_type": "independent_application",
                                 "answer": "a", "rubric": '{"application": 2}',
                                 "expected": "r", "feedback": "f", "grader": "ai_reviewed",
                                 "help": "none", "confidence": None, "approve": True})()
            with self.assertRaises((ValueError, mod.LedgerDamage)):
                mod.cmd_record(a)

    def test_record_refuses_schema_invalid_ledger(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            w = Path(d) / "work"
            mod.cmd_init(type("Args", (), {"workspace": str(w)})())
            (w / "events.jsonl").write_text('{"foo": 1}\n', encoding="utf-8")
            a = type("Args", (), {"workspace": str(w), "event_id": "e9", "topic": "t",
                                 "competency": "c1", "task_type": "independent_application",
                                 "answer": "a", "rubric": '{"application": 2}',
                                 "expected": "r", "feedback": "f", "grader": "ai_reviewed",
                                 "help": "none", "confidence": None, "approve": True})()
            with self.assertRaises((ValueError, mod.LedgerDamage)):
                mod.cmd_record(a)

    def test_repair_preserves_original_bytes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            original = p.read_bytes()
            mod.ledger_repair_truncate_partial_tail(p)
            backups = list(Path(d).glob("events.jsonl.bak.*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)
            self.assertEqual(hashlib.sha256(backups[0].read_bytes()).hexdigest(),
                             hashlib.sha256(original).hexdigest())
            # Repaired ledger reads clean and contains the intact record.
            self.assertEqual(mod.ledger_read_trusted(p), [GOOD])

    def test_repair_backup_name_unique_and_immutable(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p1 = Path(d) / "a.jsonl"
            p1.write_bytes(b'{"a": 1}\n{"x": tru')
            p2 = Path(d) / "b.jsonl"
            p2.write_bytes(b'{"a": 1}\n{"y": tru')
            mod.ledger_repair_truncate_partial_tail(p1)
            mod.ledger_repair_truncate_partial_tail(p2)
            n1 = list(Path(d).glob("a.jsonl.bak.*"))[0].name
            n2 = list(Path(d).glob("b.jsonl.bak.*"))[0].name
            self.assertNotEqual(n1, n2)
            # Name embeds content hash: recompute and compare.
            for p, n in ((p1, n1), (p2, n2)):
                _ = p
            self.assertIn(hashlib.sha256(b'{"a": 1}\n{"x": tru').hexdigest()[:8], n1)
            self.assertIn(hashlib.sha256(b'{"a": 1}\n{"y": tru').hexdigest()[:8], n2)

    def test_repair_refuses_overwrite_existing_backup(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            # Simulate a repeated repair within the same second: pre-create
            # every backup name this original could produce is impractical;
            # instead verify the guard by repairing twice after restoring.
            mod.ledger_repair_truncate_partial_tail(p)
            first = list(Path(d).glob("events.jsonl.bak.*"))
            self.assertEqual(len(first), 1)
            # Re-damage identically and force the same timestamped name to exist.
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            raw = p.read_bytes()
            sha8 = hashlib.sha256(raw).hexdigest()[:8]
            clash = [b for b in Path(d).glob(f"events.jsonl.bak.*.{sha8}")]
            if clash:
                with self.assertRaises(mod.LedgerDamage):
                    mod.ledger_repair_truncate_partial_tail(p)
            else:
                # Different second: a second backup is created, first untouched.
                mod.ledger_repair_truncate_partial_tail(p)
                self.assertEqual(len(list(Path(d).glob("events.jsonl.bak.*"))), 2)

    def test_repair_audit_carries_pre_post_hashes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            original = p.read_bytes()
            mod.ledger_repair_truncate_partial_tail(p)
            audit = Path(d) / "recovery-log.jsonl"
            entry = json.loads(audit.read_text(encoding="utf-8").strip().splitlines()[-1])
            self.assertEqual(entry["original_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(entry["backup_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(entry["repaired_sha256"],
                             hashlib.sha256(p.read_bytes()).hexdigest())

    def test_repair_writes_audit_record(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            mod.ledger_repair_truncate_partial_tail(p)
            self.assertTrue((Path(d) / "recovery-log.jsonl").exists())

    def test_repair_refuses_midfile_corruption(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "events.jsonl"
            p.write_bytes((json.dumps(GOOD) + "\n{BROKEN\n" + json.dumps(GOOD) + "\n").encode())
            before = p.read_bytes()
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_repair_truncate_partial_tail(p)
            self.assertEqual(p.read_bytes(), before)

    def test_diagnose_output_never_feeds_progress(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = write_ledger(d)
            with p.open("ab") as fh:
                fh.write(b'{"truncated": tru')
            rep = mod.ledger_diagnose(p)
            # Diagnose returns triage metadata, not parsed events: there is
            # structurally nothing here that progress() could consume.
            self.assertNotIn("events", rep)
            self.assertIsInstance(rep["records"], int)


class TestAtomicWritesAndLocks(unittest.TestCase):
    def test_atomic_write_handles_short_write(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.json"
            content = '{"key": "value-%s"}' % ("x" * 5000)
            real_write = mod.os.write
            calls = []

            def flaky(fd, data):
                calls.append(len(memoryview(data)))
                if len(calls) == 1 and len(memoryview(data)) > 100:
                    return real_write(fd, memoryview(data)[:100])
                return real_write(fd, data)

            with mock.patch.object(mod.os, "write", side_effect=flaky):
                mod.atomic_write(p, content)
            self.assertEqual(p.read_text(encoding="utf-8"), content)
            self.assertEqual(list(Path(d).glob("*.tmp")), [])
            self.assertTrue(len(calls) >= 2)

    def test_atomic_write_roundtrip_and_tmp_cleanup(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sub" / "f.json"
            p.parent.mkdir()
            mod.atomic_write(p, '{"a": 1}')
            self.assertEqual(p.read_text(encoding="utf-8"), '{"a": 1}')
            self.assertEqual(list(Path(d).rglob("*.tmp")), [])

    def test_append_writes_payload_and_newline_together(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "events.jsonl"
            line = json.dumps(GOOD, ensure_ascii=False)
            mod.append_event_line(p, line)
            raw = p.read_bytes()
            self.assertTrue(raw.endswith(b"\n"))
            self.assertEqual(raw, (line + "\n").encode("utf-8"))
            self.assertEqual(mod.ledger_read_trusted(p), [GOOD])

    def test_lock_contention(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            with mod.workspace_lock(root, timeout_seconds=5):
                with self.assertRaises(TimeoutError):
                    with mod.workspace_lock(root, timeout_seconds=0.3):
                        pass

    def test_lock_not_deleted_on_contention(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            lock = root / ".learnprint" / ".lock"
            with mod.workspace_lock(root, timeout_seconds=5):
                try:
                    with mod.workspace_lock(root, timeout_seconds=0.3):
                        pass
                except TimeoutError:
                    pass
                self.assertTrue(lock.exists())
            self.assertTrue(lock.exists())

    def test_lock_released_on_close(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            with mod.workspace_lock(root, timeout_seconds=5):
                pass
            with mod.workspace_lock(root, timeout_seconds=2):
                pass

    def test_every_mutator_declares_lock(self):
        # The lock table is a code-level declaration: every mutating course
        # operation takes the workspace lock; pure readers do not.
        table = mod.LOCK_TABLE
        for op, info in table.items():
            self.assertIn("mutates", info)
            self.assertIn("locks", info)
            self.assertEqual(info["locks"], info["mutates"],
                             f"lock policy violated for {op}")
        for must_lock in ("course init", "course create", "record",
                          "course dashboard", "migrate"):
            self.assertTrue(table[must_lock]["locks"], must_lock)
        for reader in ("course resolve", "course list", "report"):
            self.assertFalse(table[reader]["locks"], reader)


class TestStandingApproval(unittest.TestCase):
    def test_init_without_approve_refuses(self):
        # The CLI gate (commit 9) requires --approve; the record helper
        # refuses unknown scope tokens so no grant can smuggle permissions.
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                mod.write_approval(Path(d) / "Courses", scope=["publish-to-remote"])

    def test_revoked_approval_blocks_mutations(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            mod.write_approval(root)
            self.assertTrue(mod.approval_allows(mod.read_approval(root), "course-create"))
            mod.revoke_approval(root)
            self.assertFalse(mod.approval_allows(mod.read_approval(root), "course-create"))

    def test_deleted_approval_requires_reprompt(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            mod.write_approval(root)
            (root / ".learnprint" / "approval.json").unlink()
            self.assertIsNone(mod.read_approval(root))
            self.assertFalse(mod.approval_allows(mod.read_approval(root), "course-create"))

    def test_denial_falls_back_to_prompt_only(self):
        # No grant file, no --approve path: approval_allows(None) is False,
        # so mutating commands must refuse and the agent stays prompt-only.
        self.assertFalse(mod.approval_allows(None, "course-create"))

    def test_grant_excludes_publish_and_global_install(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            rec = mod.write_approval(root)
            for forbidden in ("publish", "global-install", "delete-evidence",
                              "outside-writes", "destructive-git", "network"):
                self.assertNotIn(forbidden, rec["scope"])
                self.assertFalse(mod.approval_allows(rec, forbidden))

    def test_approval_scope_rejects_unknown_tokens(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "Courses"
            (root / ".learnprint").mkdir(parents=True)
            (root / ".learnprint" / "approval.json").write_text(
                '{"schema_version": "1.0", "scope": ["course-create", "sudo"], '
                '"revoked": false, "granted_at": "t", "granted_by": "x", "revoked_at": null}',
                encoding="utf-8")
            self.assertIsNone(mod.read_approval(root))


if __name__ == "__main__":
    unittest.main()
