"""QA post-merge hardening regression tests (Phase B-E).

Seams: public module functions, CLI subprocess boundary, filesystem
artifacts. No source-text assertions, no private-name coupling.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import learnprint as mod


def make_workspace(d):
    root = Path(d) / "Courses"
    rc = mod.cmd_course_init(_ns(approve=True, courses_root=str(root)))
    assert rc == 0
    return root


class _ns:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def create_kwargs(root, category="languages/english/grammar", title="in on at"):
    return dict(courses_root=root, category_path=category, title=title,
                goal="g", aliases=(),
                confirm_new_segments=("english", "grammar"))


class TestB1CreateCrashConsistency(unittest.TestCase):
    def test_state_registry_coherent_after_create(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(**create_kwargs(root))
            st = json.loads((root / entry["rel_path"] / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(st["course_id"], entry["course_id"])
            self.assertIsNotNone(st["course_id"])

    def test_corrupt_orphan_state_refuses_create(self):
        """RED: pre-existing dir with corrupt state.json must NOT be
        adopted into the registry with a swallowed state-update error."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            # Predict the directory course_create will use.
            from learnprint_routing import slugify
            slug = slugify("in on at")
            orphan = root / "languages/english/grammar" / slug
            orphan.mkdir(parents=True)
            (orphan / "state.json").write_text("{corrupt json", encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.course_create(**create_kwargs(root))
            # Registry must NOT advertise the corrupt course.
            reg = mod.registry_read(root)
            self.assertEqual(reg.get("courses", []), [])

    def test_interrupted_create_retry_converges_to_single_course(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            from learnprint_routing import slugify
            import uuid
            slug = slugify("in on at")
            orphan = root / "languages/english/grammar" / slug
            orphan.mkdir(parents=True)
            orphan_id = str(uuid.uuid4())
            (orphan / "state.json").write_text(json.dumps(
                {"schema_version": "1.0", "course_id": orphan_id, "goal": "g",
                 "learning_scope": [], "sources": []}), encoding="utf-8")
            entry = mod.course_create(**create_kwargs(root))
            self.assertEqual(entry["course_id"], orphan_id)
            reg = mod.registry_read(root)
            self.assertEqual(len(reg["courses"]), 1)


class TestB2RegistryIntegrity(unittest.TestCase):
    def test_backup_preserves_prior_state(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            mod.course_create(**create_kwargs(root, title="course one"))
            prior = (root / ".learnprint" / "registry.json").read_bytes()
            mod.course_create(**create_kwargs(root, title="course two"))
            bak_raw = (root / ".learnprint" / "registry.json.bak").read_bytes()
            bak = json.loads(bak_raw)
            self.assertEqual(len(bak["courses"]), 1)
            self.assertEqual(json.loads(prior)["courses"], bak["courses"])

    def test_missing_registry_in_initialized_workspace_raises(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            (root / ".learnprint" / "registry.json").unlink()
            with self.assertRaises(ValueError):
                mod.registry_read(root)

    def test_corrupt_registry_raises_actionable_error(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            (root / ".learnprint" / "registry.json").write_text("{nope", encoding="utf-8")
            try:
                mod.registry_read(root)
            except ValueError as exc:
                self.assertIn("registry", str(exc).lower())
            else:
                self.fail("expected ValueError")

    def test_validate_detects_state_registry_identity_mismatch(self):
        import tempfile, uuid, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(**create_kwargs(root))
            st_path = root / entry["rel_path"] / "state.json"
            st = json.loads(st_path.read_text(encoding="utf-8"))
            st["course_id"] = str(uuid.uuid4())
            st_path.write_text(json.dumps(st), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_validate(
                    _ns(repair=False, approve=False, courses_root=str(root)))
            self.assertEqual(rc, 2)
            self.assertIn("mismatch", buf.getvalue().lower())

    def test_validate_flags_duplicate_course_ids(self):
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            mod.course_create(**create_kwargs(root, title="course one"))
            mod.course_create(**create_kwargs(root, title="course two"))
            reg = mod.registry_read(root)
            reg["courses"][1]["course_id"] = reg["courses"][0]["course_id"]
            mod.registry_write(root, reg)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_validate(
                    _ns(repair=False, approve=False, courses_root=str(root)))
            self.assertEqual(rc, 2)
            self.assertIn("duplicate", buf.getvalue().lower())


def valid_event(eid="e1", topic="t", comp="c1"):
    return {"event_id": eid, "date": "2026-10-11T10:00:00+00:00",
            "topic_id": topic, "competency_id": comp,
            "task_type": "independent_application",
            "observed_answer": "a", "expected_reasoning": "r",
            "help_level": "none", "rubric": {"application": 2},
            "feedback": "f", "grader": "ai_reviewed",
            "evidence_origin": "observed_response"}


class TestB3LedgerTerminatorSafety(unittest.TestCase):
    def _ledger(self, root):
        return root / ".learnprint" / "events.jsonl"

    def test_diagnose_flags_missing_terminal_newline(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event()) ).encode("utf-8"))  # no \n
            diag = mod.ledger_diagnose(lp, workspace_root=root)
            self.assertEqual(diag["status"], "damaged")

    def test_trusted_read_rejects_unterminated_ledger(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event())).encode("utf-8"))
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_read_trusted(lp, workspace_root=root)

    def test_append_refuses_unterminated_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event())).encode("utf-8"))
            with self.assertRaises(mod.LedgerDamage):
                mod.append_event_line(lp, json.dumps(valid_event("e2")))

    def test_repair_restores_terminator_preserving_record(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            lp.write_bytes((json.dumps(valid_event())).encode("utf-8"))
            report = mod.ledger_repair_truncate_partial_tail(lp)
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["records"], 1)
            self.assertTrue(lp.read_bytes().endswith(b"\n"))
            recs = mod.ledger_read_trusted(lp, workspace_root=root)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["event_id"], "e1")

    def test_record_refuses_then_succeeds_after_repair(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(**create_kwargs(root))
            lp = self._ledger(root)
            # Seed one valid event via the trusted path, then strip terminator
            # to simulate an interrupted write.
            mod.append_event_line(lp, json.dumps(valid_event("e0", topic=entry["course_id"])))
            raw = lp.read_bytes()
            lp.write_bytes(raw.rstrip(b"\n"))
            args = _ns(workspace=str(root), event_id="e1", topic=entry["course_id"],
                       competency="c1", task_type="independent_application",
                       answer="a", rubric='{"application": 2}', expected="r",
                       feedback="f", approve=True, course_id=entry["course_id"],
                       help="none", confidence=None, grader="ai_reviewed",
                       confirms=None, corrects=None, corroborates=None,
                       grader_source=None)
            with self.assertRaises(mod.LedgerDamage):
                mod.cmd_record(args)
            mod.ledger_repair_truncate_partial_tail(lp)
            self.assertEqual(mod.cmd_record(args), 0)
            recs = mod.ledger_read_trusted(lp, workspace_root=root)
            self.assertEqual([r["event_id"] for r in recs], ["e0", "e1"])


class TestB4RepairTransactions(unittest.TestCase):
    def _ledger(self, root):
        return root / ".learnprint" / "events.jsonl"

    def _backups(self, root):
        return sorted((root / ".learnprint").glob("events.jsonl.bak.*"))

    def test_repair_idempotent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            mod.append_event_line(lp, json.dumps(valid_event("e1")))
            with open(lp, "ab") as fh:
                fh.write(b'{"broken": tru')
            first = mod.ledger_repair_truncate_partial_tail(lp)
            self.assertEqual(first["status"], "ok")
            second = mod.ledger_repair_truncate_partial_tail(lp)
            self.assertEqual(second["status"], "ok")
            self.assertEqual(second["records"], 1)
            self.assertEqual(len(self._backups(root)), 1)

    def test_repair_backup_hash_chain(self):
        import tempfile, hashlib
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            mod.append_event_line(lp, json.dumps(valid_event("e1")))
            with open(lp, "ab") as fh:
                fh.write(b'{"broken": tru')
            pre_sha = mod.ledger_diagnose(lp)["sha256"]
            mod.ledger_repair_truncate_partial_tail(lp)
            backups = self._backups(root)
            self.assertEqual(len(backups), 1)
            self.assertEqual(hashlib.sha256(backups[0].read_bytes()).hexdigest(), pre_sha)
            audit = (root / ".learnprint" / "recovery-log.jsonl").read_text(encoding="utf-8")
            entry = json.loads(audit.strip().splitlines()[-1])
            self.assertEqual(entry["original_sha256"], pre_sha)
            self.assertEqual(entry["backup_sha256"], pre_sha)
            self.assertEqual(entry["repaired_sha256"], mod.ledger_diagnose(lp)["sha256"])

    def test_successive_repairs_keep_distinct_backups(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            mod.append_event_line(lp, json.dumps(valid_event("e1")))
            with open(lp, "ab") as fh:
                fh.write(b'{"broken": tru')
            mod.ledger_repair_truncate_partial_tail(lp)
            mod.append_event_line(lp, json.dumps(valid_event("e2")))
            with open(lp, "ab") as fh:
                fh.write(b'{"broken": xx')
            mod.ledger_repair_truncate_partial_tail(lp)
            backups = self._backups(root)
            self.assertEqual(len(backups), 2)
            self.assertNotEqual(backups[0].name, backups[1].name)
            recs = mod.ledger_read_trusted(lp, workspace_root=root)
            self.assertEqual([r["event_id"] for r in recs], ["e1", "e2"])

    def test_repair_refuses_midfile_corruption(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = self._ledger(root)
            mod.append_event_line(lp, json.dumps(valid_event("e1")))
            mod.append_event_line(lp, json.dumps(valid_event("e2")))
            lines = lp.read_bytes().split(b"\n")
            lines[0] = b"{mid-file garbage"
            before = b"\n".join(lines)
            lp.write_bytes(before)
            with self.assertRaises(mod.LedgerDamage):
                mod.ledger_repair_truncate_partial_tail(lp)
            self.assertEqual(lp.read_bytes(), before)


class TestHotfixInitAndLedgerValidation(unittest.TestCase):
    def test_init_refuses_existing_workspace_with_missing_registry(self):
        """Init must never overwrite existing evidence if registry was lost."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = root / ".learnprint"
            original_ledger = b'{"existing":"learner-evidence-canary"}\\n'
            original_profile = b'{"existing":"learner-profile-canary"}\\n'
            (lp / "events.jsonl").write_bytes(original_ledger)
            (lp / "learner" / "profile.json").write_bytes(original_profile)
            (lp / "registry.json").unlink()
            result = _cli("course", "init", "--courses-root", str(root), "--approve")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("recover", (result.stdout + result.stderr).lower())
            self.assertEqual((lp / "events.jsonl").read_bytes(), original_ledger)
            self.assertEqual((lp / "learner" / "profile.json").read_bytes(), original_profile)
            self.assertFalse((lp / "registry.json").exists())

    def test_course_validate_rejects_schema_invalid_ledger(self):
        """JSON syntax alone cannot make invalid evidence authoritative."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            ledger = root / ".learnprint" / "events.jsonl"
            original = b'{"not_an_event": true}\\n'
            ledger.write_bytes(original)
            result = _cli("course", "validate", "--courses-root", str(root))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("INVALID", result.stdout)
            self.assertIn("ledger", result.stdout.lower())
            self.assertEqual(ledger.read_bytes(), original)


class TestB5ValidateHonesty(unittest.TestCase):
    def test_repair_does_not_claim_success_with_damaged_ledger(self):
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = root / ".learnprint" / "events.jsonl"
            mod.append_event_line(lp, json.dumps(valid_event("e1")))
            mod.append_event_line(lp, json.dumps(valid_event("e2")))
            lines = lp.read_bytes().split(b"\n")
            lines[0] = b"{mid-file garbage"
            lp.write_bytes(b"\n".join(lines))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_validate(
                    _ns(repair=True, approve=True, courses_root=str(root)))
            out = buf.getvalue()
            self.assertEqual(rc, 2)
            self.assertIn("INVALID", out)
            self.assertNotIn("REPAIRED", out)

    def test_repair_adopts_orphan_then_valid(self):
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            orphan = root / "life/imported/orphan-topic"
            orphan.mkdir(parents=True)
            (orphan / "state.json").write_text(json.dumps(
                {"schema_version": "1.0", "course_id": None, "goal": "g",
                 "learning_scope": [], "sources": []}), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_validate(
                    _ns(repair=True, approve=True, courses_root=str(root)))
            self.assertEqual(rc, 0)
            self.assertIn("REPAIRED", buf.getvalue())
            buf2 = io.StringIO()
            with redirect_stdout(buf2):
                rc2 = mod.cmd_course_validate(
                    _ns(repair=False, approve=False, courses_root=str(root)))
            self.assertEqual(rc2, 0)
            self.assertIn("VALID", buf2.getvalue())


class TestCRoutingLifecycle(unittest.TestCase):
    def test_parent_scoped_grammar_coexistence(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            en = mod.course_create(**create_kwargs(root, "languages/english/grammar", "in on at"))
            jp = mod.course_create(root, "languages/japanese/grammar", "particles wa ga",
                                    "g", (), ("japanese", "grammar"))
            self.assertEqual(en["category_path"], "languages/english/grammar")
            self.assertEqual(jp["category_path"], "languages/japanese/grammar")
            self.assertNotEqual(en["course_id"], jp["course_id"])
            # Case-insensitive reuse under the SAME canonical parent.
            again = mod.course_create(root, "languages/english/Grammar", "articles a the",
                                       "g", (), ())
            self.assertEqual(again["category_path"], "languages/english/grammar")

    def test_typo_segment_needs_confirmation_never_merges(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            mod.course_create(**create_kwargs(root, "languages/english/grammar", "in on at"))
            with self.assertRaises(ValueError):
                mod.course_create(root, "languages/english/grammer", "Grammer", "g", (), ("approve",))
            reg = mod.registry_read(root)
            self.assertEqual(len(reg["courses"]), 1)

    def test_vocabulary_scopes_independent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            dev = mod.course_create(root, "technology/devops/vocabulary", "cicd terms",
                                     "g", (), ("devops", "vocabulary"))
            eng = mod.course_create(root, "languages/english/vocabulary", "word list",
                                     "g", (), ("english", "vocabulary"))
            self.assertEqual(dev["category_path"], "technology/devops/vocabulary")
            self.assertEqual(eng["category_path"], "languages/english/vocabulary")

    def test_root_alias_resolves_before_validation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            c = mod.course_create(root, "tech/devops", "cicd", "g", (), ("devops",))
            self.assertEqual(c["category_path"], "technology/devops")

    def test_unknown_root_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            with self.assertRaises(ValueError):
                mod.course_create(root, "cooking/italian", "pasta", "g", (), ())

    def test_rename_move_preserve_identity_evidence_resume(self):
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            c = mod.course_create(**create_kwargs(root))
            cid = c["course_id"]
            mod.course_rename(root, cid, "English Prepositions")
            moved = mod.course_move(root, cid, "languages/english/development",
                                    ("development",))
            self.assertEqual(moved["course_id"], cid)
            st = json.loads((root / moved["rel_path"] / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(st["course_id"], cid)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_resume(_ns(courses_root=str(root)))
            self.assertEqual(rc, 0)
            # No active set in this flow; resume may be ambiguous — but it
            # must never surface a wrong identity.
            out = buf.getvalue()
            if '"status": "found"' in out:
                self.assertIn(cid, out)

    def test_concurrent_create_same_course_single_winner(self):
        import tempfile, threading
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            barrier = threading.Barrier(2)
            outcomes = []

            def attempt():
                barrier.wait(timeout=10)
                try:
                    e = mod.course_create(root, "languages/english/grammar", "in on at",
                                           "g", (), ("english", "grammar"))
                    outcomes.append(("ok", e["course_id"]))
                except Exception as exc:  # noqa: BLE001 — assert below
                    outcomes.append(("refused", str(exc)))

            threads = [threading.Thread(target=attempt) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=60)
            reg = mod.registry_read(root)
            ids = [c["course_id"] for c in reg["courses"]]
            self.assertEqual(len(ids), len(set(ids)))  # no duplicate IDs
            self.assertLessEqual(len(ids), 2)
            oks = [o for o in outcomes if o[0] == "ok"]
            self.assertEqual(len(oks), 1)
            self.assertIn(oks[0][1], ids)


def _cli(*argv):
    import subprocess
    script = str(ROOT / "scripts" / "learnprint.py")
    return subprocess.run([sys.executable, script, *argv],
                          capture_output=True, text=True, timeout=60)


class TestCCliGates(unittest.TestCase):
    def test_cli_root_alias_end_to_end(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = str(Path(d) / "Courses")
            self.assertEqual(
                _cli("course", "init", "--courses-root", root, "--approve").returncode, 0)
            r = _cli("course", "create", "--courses-root", root,
                     "--category", "tech/devops", "--title", "cicd",
                     "--goal", "g", "--confirm-new-segment", "devops",
                     "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("technology/devops", r.stdout)

    def test_cli_unknown_root_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = str(Path(d) / "Courses")
            self.assertEqual(
                _cli("course", "init", "--courses-root", root, "--approve").returncode, 0)
            r = _cli("course", "create", "--courses-root", root,
                     "--category", "cooking/italian", "--title", "pasta",
                     "--goal", "g", "--approve")
            self.assertEqual(r.returncode, 2)


class TestDWindowsPaths(unittest.TestCase):
    def test_reserved_names_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            for bad in ("languages/CON", "languages/NUL.txt", "languages/COM1/stuff"):
                valid, err = mod.validate_path(bad, Path(d))
                self.assertFalse(valid, bad)
                self.assertTrue(err)

    def test_case_collision_detected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Grammar").mkdir()
            valid, err = mod.validate_path("Grammar", Path(d))
            self.assertTrue(valid)
            (Path(d) / "other").mkdir()
            valid, err = mod.validate_path("OTHER", Path(d))
            self.assertFalse(valid)
            self.assertIn("collision", err.lower())

    def test_trailing_dots_spaces_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            for bad in ("languages/english.", "languages/eng /x"):
                valid, err = mod.validate_path(bad, Path(d))
                self.assertFalse(valid, bad)

    def test_backslash_segment_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            valid, err = mod.validate_path("languages\\english", Path(d))
            self.assertFalse(valid)

    def test_unicode_title_creates_usable_course(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(root, "languages/japanese/grammar",
                                       "は particle", "g", (), ("japanese", "grammar"))
            self.assertTrue((root / entry["rel_path"] / "state.json").exists())
            st = json.loads((root / entry["rel_path"] / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(st["course_id"], entry["course_id"])

    def test_atomic_write_failure_leaves_no_temp(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ghost = Path(d) / "no-such-dir" / "f.json"
            with self.assertRaises((OSError, ValueError)):
                mod.atomic_write(ghost, "{}")
            leftovers = list(Path(d).rglob("*.tmp"))
            self.assertEqual(leftovers, [])

    def test_concurrent_appends_lose_nothing(self):
        import tempfile, threading
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = root / ".learnprint" / "events.jsonl"
            barrier = threading.Barrier(4)
            errors = []

            def worker(n):
                try:
                    barrier.wait(timeout=10)
                    for i in range(5):
                        mod.append_event_line(
                            lp, json.dumps(valid_event(f"w{n}-{i}")))
                except Exception as exc:  # noqa: BLE001 — asserted empty
                    errors.append(exc)

            threads = [threading.Thread(target=worker, args=(n,)) for n in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=60)
            self.assertEqual(errors, [])
            recs = mod.ledger_read_trusted(lp, workspace_root=root)
            self.assertEqual(len(recs), 20)
            ids = [r["event_id"] for r in recs]
            self.assertEqual(len(set(ids)), 20)

    def test_concurrent_cli_records_both_land(self):
        import tempfile, threading
        with tempfile.TemporaryDirectory() as d:
            root = str(Path(d) / "Courses")
            self.assertEqual(
                _cli("course", "init", "--courses-root", root, "--approve").returncode, 0)
            r = _cli("course", "create", "--courses-root", root,
                     "--category", "languages/english/grammar",
                     "--title", "in on at", "--goal", "g",
                     "--confirm-new-segment", "english",
                     "--confirm-new-segment", "grammar", "--approve")
            self.assertEqual(r.returncode, 0, r.stderr)
            cid = json.loads(r.stdout)["course_id"]
            barrier = threading.Barrier(2)
            results = []

            def record(n):
                barrier.wait(timeout=30)
                results.append(_cli(
                    "record", "--workspace", root, "--event-id", f"conc-{n}",
                    "--topic", cid, "--competency", "c1",
                    "--task-type", "independent_application",
                    "--answer", "a", "--rubric", '{"application": 2}',
                    "--expected", "r", "--feedback", "f",
                    "--course-id", cid, "--approve"))

            threads = [threading.Thread(target=record, args=(n,)) for n in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=120)
            for res in results:
                self.assertEqual(res.returncode, 0, res.stderr)
            lp = Path(root) / ".learnprint" / "events.jsonl"
            recs = mod.ledger_read_trusted(lp, workspace_root=Path(root))
            self.assertEqual({r["event_id"] for r in recs}, {"conc-0", "conc-1"})


class TestReviewFindings(unittest.TestCase):
    def test_move_crash_retry_converges(self):
        """Interrupted move AFTER os.replace but BEFORE registry commit:
        retry must converge (adopt the already-moved directory)."""
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            c = mod.course_create(**create_kwargs(root))
            cid = c["course_id"]
            src = root / c["rel_path"]
            dst = root / "languages/english/development/in-on-at"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))  # simulate completed replace, lost commit
            moved = mod.course_move(root, cid, "languages/english/development",
                                    ("development",))
            self.assertEqual(moved["rel_path"], "languages/english/development/in-on-at")
            st = json.loads((dst / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(st["course_id"], cid)

    def test_move_refuses_stray_file_at_dest(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            c = mod.course_create(**create_kwargs(root))
            block = root / "languages/english/development"
            block.mkdir(parents=True)
            planted = block / "in-on-at"
            planted.write_text("stray user file", encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.course_move(root, c["course_id"], "languages/english/development",
                                ("development",))
            self.assertEqual(planted.read_text(encoding="utf-8"), "stray user file")

    def test_registry_write_unreadable_prior_raises(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            cur = root / ".learnprint" / "registry.json"
            raw = cur.read_bytes()
            cur.unlink()
            cur.mkdir()  # directory in place of the file: read_bytes -> OSError
            try:
                with self.assertRaises(ValueError):
                    mod.registry_write(root, {"schema_version": "1.0", "courses": [],
                                              "active_course_id": None})
            finally:
                import shutil as _sh
                _sh.rmtree(cur, ignore_errors=True)
                cur.write_bytes(raw)

    def test_repair_skips_colliding_orphan(self):
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            mod.course_create(**create_kwargs(root, "languages/english/grammar", "in on at"))
            # Orphan dir whose DERIVED title normalizes to the registered
            # course title in the same category: adopting it would create a
            # duplicate-title pair.
            dup = root / "languages/english/grammar" / "IN ON AT"
            dup.mkdir(parents=True)
            (dup / "state.json").write_text(json.dumps(
                {"schema_version": "1.0", "course_id": None, "goal": "g",
                 "learning_scope": [], "sources": []}), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = mod.cmd_course_validate(
                    _ns(repair=True, approve=True, courses_root=str(root)))
            self.assertEqual(rc, 2)
            self.assertIn("MANUAL", buf.getvalue())
            reg = mod.registry_read(root)
            self.assertEqual(len(reg["courses"]), 1)

    def test_case_walk_sees_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Grammar").write_text("file, not dir", encoding="utf-8")
            valid, err = mod.validate_path("grammar", Path(d))
            self.assertFalse(valid)
            self.assertTrue(err)

    def test_repair_append_race_loses_nothing(self):
        """Repair racing same-process appends: the mutex serializes
        diagnose + mutate against appends, so appended records are never
        truncated away. Retry loops are bounded; no sleeps."""
        import tempfile, threading
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            lp = root / ".learnprint" / "events.jsonl"
            mod.append_event_line(lp, json.dumps(valid_event("seed")))
            with open(lp, "ab") as fh:
                fh.write(b'{"broken": tru')
            errors = []

            def appender():
                try:
                    for i in range(5):
                        for _ in range(500):
                            try:
                                mod.append_event_line(lp, json.dumps(valid_event(f"race-{i}")))
                                break
                            except mod.LedgerDamage:
                                continue
                        else:
                            raise AssertionError(f"append race-{i} never landed")
                except Exception as exc:  # noqa: BLE001 — asserted empty
                    errors.append(exc)

            def repairer():
                try:
                    for _ in range(500):
                        try:
                            rep = mod.ledger_repair_truncate_partial_tail(lp)
                        except mod.LedgerDamage:
                            continue
                        if rep["status"] == "ok":
                            try:
                                mod.ledger_read_trusted(lp, workspace_root=root)
                                return
                            except mod.LedgerDamage:
                                continue
                    raise AssertionError("ledger never converged to ok")
                except Exception as exc:  # noqa: BLE001 — asserted empty
                    errors.append(exc)

            threads = [threading.Thread(target=appender),
                       threading.Thread(target=repairer)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=120)
            self.assertEqual(errors, [])
            recs = mod.ledger_read_trusted(lp, workspace_root=root)
            ids = {r["event_id"] for r in recs}
            self.assertIn("seed", ids)
            for i in range(5):
                self.assertIn(f"race-{i}", ids)


class TestEWorkspaceAcceptance(unittest.TestCase):
    def test_readonly_ops_do_not_create_workspace(self):
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as d:
            ghost = str(Path(d) / "NoCourses")
            buf = io.StringIO()
            with redirect_stdout(buf):
                mod.cmd_course_resolve(_ns(query="in on at", courses_root=ghost))
            self.assertFalse(Path(ghost).exists())
            buf = io.StringIO()
            with redirect_stdout(buf):
                mod.cmd_course_list(_ns(courses_root=ghost))
            self.assertFalse(Path(ghost).exists())

    def test_dashboard_separates_due_now_from_scheduled(self):
        import tempfile
        import datetime as dt
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            entry = mod.course_create(**create_kwargs(root))
            cid = entry["course_id"]
            sp = root / entry["rel_path"] / "state.json"
            st = json.loads(sp.read_text(encoding="utf-8"))
            st["learning_scope"] = [
                {"id": "c1", "name": "C1", "status": "unknown",
                 "evidence_ids": [], "due_at": None}]
            sp.write_text(json.dumps(st) + "\n", encoding="utf-8")
            now = dt.datetime.now(dt.timezone.utc)
            base = {"date": now.isoformat(), "topic_id": cid, "competency_id": "c1",
                    "observed_answer": "a", "expected_reasoning": "r",
                    "help_level": "none", "feedback": "f", "grader": "ai_reviewed",
                    "evidence_origin": "observed_response", "course_id": cid}
            mod.append_event_line(
                root / ".learnprint" / "events.jsonl",
                json.dumps({**base, "event_id": "a1",
                            "task_type": "independent_application",
                            "rubric": {"application": 2}}))
            mod.append_event_line(
                root / ".learnprint" / "events.jsonl",
                json.dumps({**base, "event_id": "t1",
                            "task_type": "novel_transfer",
                            "rubric": {"transfer": 2}}))
            mod.cmd_course_dashboard(_ns(approve=True, courses_root=str(root)))
            index = (root / "INDEX.md").read_text(encoding="utf-8")
            # Fresh demonstration: review is scheduled ~1 day out, NOT due.
            self.assertIn("Scheduled", index)
            due_section = index.split("Scheduled")[0]
            self.assertNotIn("c1: due", due_section)


class TestGPathContainment(unittest.TestCase):
    def test_move_traversal_refused_without_escape(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            c = mod.course_create(**create_kwargs(root))
            with self.assertRaises(ValueError):
                mod.course_move(root, c["course_id"], "languages/../evil",
                                ("..", "evil"))
            # Nothing escaped the workspace root.
            self.assertFalse((Path(d) / "evil").exists())
            reg = mod.registry_read(root)
            self.assertEqual(reg["courses"][0]["category_path"],
                             "languages/english/grammar")

    def test_move_absolute_path_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = make_workspace(d)
            c = mod.course_create(**create_kwargs(root))
            with self.assertRaises(ValueError):
                mod.course_move(root, c["course_id"], "/tmp/evil", ())


if __name__ == "__main__":
    unittest.main()
