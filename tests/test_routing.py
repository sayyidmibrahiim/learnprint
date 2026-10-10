import datetime as _dt
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


rt = load_mod("learnprint_routing", "scripts/learnprint_routing.py")
mod = load_mod("learnprint", "scripts/learnprint.py")

T0 = "2026-10-10T01:00:00+07:00"
CID = "550e8400-e29b-41d4-a716-446655440000"


def mkroot(d):
    root = Path(d) / "Courses"
    lp = root / ".learnprint"
    lp.mkdir(parents=True)
    (lp / "registry.json").write_text(
        json.dumps({"schema_version": "1.0", "courses": [], "active_course_id": None}),
        encoding="utf-8")
    (lp / "events.jsonl").write_bytes(b"")
    return root


def mkcourse(root, category, title, **kw):
    # Test helper simulating a reviewing agent: run the gate, confirm every
    # new segment verbatim, then create. Unknown roots still raise ValueError
    # from course_create itself.
    reg = mod.registry_read(root)
    ok, gate = rt.validate_classification(category, reg)
    flags = []
    if ok and isinstance(gate, dict):
        flags = [v["segment"] for v in gate.get("segments", [])
                 if v["verdict"] == "new-needs-confirmation"]
    if "confirm_new_segments" in kw:
        flags = kw.pop("confirm_new_segments")
    return mod.course_create(root, category, title, kw.pop("goal", "g"),
                             confirm_new_segments=flags, **kw)


def ev(eid, kind, date, course_id, comp="c1", rubric=None):
    return {"event_id": eid, "date": date, "topic_id": course_id,
            "course_id": course_id, "competency_id": comp, "task_type": kind,
            "observed_answer": "a", "expected_reasoning": "r", "feedback": "f",
            "help_level": "none",
            "rubric": rubric or {"concept": 2, "mechanism": 2, "application": 2, "transfer": 2},
            "grader": "ai_reviewed", "evidence_origin": "observed_response",
            "grader_source": "agent"}


def topic_for(course_id, comp="c1"):
    return {"schema_version": "1.0", "topic_id": course_id, "goal": "g",
            "learning_scope": [{"id": comp, "name": "C", "status": "unknown",
                                "evidence_ids": [], "due_at": None}],
            "syllabus": [], "question_parking_lot": [], "sources": [], "last_session": None}


class TestSlugs(unittest.TestCase):
    def test_unicode_slug(self):
        self.assertEqual(rt.slugify("in/on/at"), "in-on-at")

    def test_slash_in_title(self):
        self.assertNotIn("/", rt.slugify("a/b/c"))

    def test_cjk_slug_fallback(self):
        s = rt.slugify("中文")
        self.assertTrue(s.startswith("topic-") and len(s) == 14)

    def test_arabic_slug_fallback(self):
        s = rt.slugify("العربية")
        self.assertTrue(s.startswith("topic-") and len(s) == 14)

    def test_nfc_nfd_collision(self):
        import unicodedata
        self.assertEqual(rt.normalize_key(unicodedata.normalize("NFC", "café")),
                         rt.normalize_key(unicodedata.normalize("NFD", "café")))

    def test_case_collision(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "In On At")
            with self.assertRaises(ValueError):
                mkcourse(root, "languages/english/grammar", "IN ON AT")


class TestIdentity(unittest.TestCase):
    def test_rename_preserves_course_id(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            cid = c["course_id"]
            self.assertRegex(cid, rt._COURSE_ID_RE)
            r = mod.course_rename(root, cid, "English Prepositions")
            self.assertEqual(r["course_id"], cid)
            self.assertEqual(r["title"], "English Prepositions")

    def test_rename_preserves_event_references(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            cid = c["course_id"]
            events = [ev("a", "independent_application", T0, cid),
                      ev("t", "novel_transfer", T0, cid)]
            before = mod.progress(topic_for(cid), events,
                                  now=_dt.datetime.fromisoformat(T0))
            mod.course_rename(root, cid, "English Prepositions", update_path=True)
            after = mod.progress(topic_for(cid), events,
                                 now=_dt.datetime.fromisoformat(T0))
            self.assertEqual(before, after)

    def test_rename_updates_normalized_title(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            mod.course_rename(root, c["course_id"], "English Prepositions")
            reg = mod.registry_read(root)
            self.assertEqual(reg["courses"][0]["normalized_title"], "english-prepositions")

    def test_move_preserves_course_id(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            cid = c["course_id"]
            m = mod.course_move(root, cid, "languages/english/language-development",
                                confirm_new_segments=["language-development"])
            self.assertEqual(m["course_id"], cid)
            self.assertEqual(m["category_path"], "languages/english/language-development")

    def test_move_preserves_event_references(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            cid = c["course_id"]
            events = [ev("a", "independent_application", T0, cid)]
            before = mod.progress(topic_for(cid), events,
                                  now=_dt.datetime.fromisoformat(T0))
            mod.course_move(root, cid, "languages/english/language-development",
                            confirm_new_segments=["language-development"])
            after = mod.progress(topic_for(cid), events,
                                 now=_dt.datetime.fromisoformat(T0))
            self.assertEqual(before, after)

    def test_move_updates_rel_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            old_rel = c["rel_path"]
            m = mod.course_move(root, c["course_id"], "languages/english/language-development",
                                confirm_new_segments=["language-development"])
            self.assertNotEqual(m["rel_path"], old_rel)
            self.assertTrue((root / m["rel_path"] / "state.json").exists())
            self.assertFalse((root / old_rel).exists())

    def test_evidence_resolves_after_move(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            cid = c["course_id"]
            mod.course_move(root, cid, "languages/english/language-development",
                            confirm_new_segments=["language-development"])
            reg = mod.registry_read(root)
            found = mod.course_resolve(root, cid)
            self.assertEqual(found["status"], "found")
            self.assertEqual(found["course"]["rel_path"], reg["courses"][0]["rel_path"])

    def test_progress_identical_before_and_after_move(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            cid = c["course_id"]
            events = [ev("a", "independent_application", T0, cid),
                      ev("t", "novel_transfer", T0, cid)]
            now = _dt.datetime.fromisoformat(T0)
            before = mod.progress(topic_for(cid), events, now=now, registry=mod.registry_read(root))
            mod.course_move(root, cid, "languages/english/language-development",
                            confirm_new_segments=["language-development"])
            after = mod.progress(topic_for(cid), events, now=now, registry=mod.registry_read(root))
            self.assertEqual(before, after)

    def test_same_slug_different_category(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            a = mkcourse(root, "technology/devops", "Introduction")
            b = mkcourse(root, "science/biology", "Introduction")
            self.assertNotEqual(a["course_id"], b["course_id"])
            self.assertNotEqual(a["rel_path"], b["rel_path"])


class TestAliases(unittest.TestCase):
    def test_alias_resolves_same_course(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at",
                         aliases=["prepositions in on at"])
            found = mod.course_resolve(root, "Prepositions In On At")
            self.assertEqual(found["status"], "found")
            self.assertEqual(found["course"]["course_id"], c["course_id"])

    def test_alias_collision_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at",
                     aliases=["prepositions"])
            with self.assertRaises(ValueError):
                mkcourse(root, "languages/english/vocabulary", "words",
                         aliases=["Prepositions"])

    def test_alias_collision_reports_both_courses(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            first = mkcourse(root, "languages/english/grammar", "in on at",
                             aliases=["prepositions"])
            try:
                mkcourse(root, "languages/english/vocabulary", "words",
                         aliases=["prepositions"])
                self.fail("expected refusal")
            except ValueError as e:
                self.assertIn(first["course_id"], str(e))

    def test_two_introductions_ambiguous(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "technology/devops", "Introduction")
            mkcourse(root, "science/biology", "Introduction")
            r = mod.course_resolve(root, "Introduction")
            self.assertEqual(r["status"], "ambiguous")
            self.assertEqual(len(r["candidates"]), 2)


class TestTaxonomy(unittest.TestCase):
    def test_unknown_top_level_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            with self.assertRaises(ValueError):
                mkcourse(root, "cooking/italian/pasta", "Pasta")

    def test_new_top_level_requires_flag(self):
        ok, _ = rt.validate_classification("cooking/italian", {"courses": []})
        self.assertFalse(ok)

    def test_reuse_before_create(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at")
            ok, gate = rt.validate_classification("languages/english/grammar",
                                                  mod.registry_read(root))
            self.assertTrue(ok)
            self.assertEqual(gate["verdict"], "reuse")

    def test_grammer_segment_needs_confirmation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at")
            ok, gate = rt.validate_classification("languages/english/grammer",
                                                  mod.registry_read(root))
            self.assertTrue(ok)
            self.assertEqual(gate["verdict"], "new-needs-confirmation")
            cands = [v for v in gate["segments"] if v["segment"] == "grammer"][0]["candidates"]
            self.assertIn("grammar", cands)

    def test_create_without_confirmation_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at")
            with self.assertRaises(ValueError):
                mod.course_create(root, "languages/english/grammer", "Grammer", "g")

    def test_confirm_new_segment_exact_echo(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            with self.assertRaises(ValueError):
                mod.course_create(root, "technology/devops/docker", "Docker", "g",
                                  confirm_new_segments=["wrong-name"])

    def test_legitimate_new_subject_passes_with_flags(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mod.course_create(root, "technology/devops/docker", "Docker", "g",
                                  confirm_new_segments=["devops", "docker"])
            self.assertEqual(c["category_path"], "technology/devops/docker")

    def test_japanese_grammar_not_satisfied_by_english(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at")
            ok, gate = rt.validate_classification("languages/japanese/grammar",
                                                  mod.registry_read(root))
            segs = {v["segment"]: v["verdict"] for v in gate["segments"]}
            self.assertEqual(segs.get("japanese"), "new-needs-confirmation")

    def test_grammar_case_reuse_same_category(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at")
            ok, gate = rt.validate_classification("languages/english/Grammar",
                                                  mod.registry_read(root))
            self.assertEqual(gate["verdict"], "reuse")
            self.assertEqual(gate["resolved_path"], "languages/english/grammar")

    def test_vocab_parent_scoped_devops_vs_english(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "technology/devops/vocabulary", "DevOps words",
                     confirm_new_segments=["devops", "vocabulary"])
            ok, gate = rt.validate_classification("languages/english/vocabulary",
                                                  mod.registry_read(root))
            segs = {v["segment"]: v["verdict"] for v in gate["segments"]}
            self.assertEqual(segs.get("vocabulary"), "new-needs-confirmation")

    def test_same_child_name_different_parents(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            a = mkcourse(root, "languages/indonesian/grammar", "Tata Bahasa",
                         confirm_new_segments=["indonesian", "grammar"])
            b = mkcourse(root, "languages/japanese/grammar", "Bunpou",
                         confirm_new_segments=["japanese", "grammar"])
            self.assertNotEqual(a["category_path"], b["category_path"])
            r = mod.course_resolve(root, "Tata Bahasa")
            self.assertEqual(r["course"]["course_id"], a["course_id"])

    def test_root_alias_resolves_canonical(self):
        ok, gate = rt.validate_classification("tech/devops", {"courses": []})
        self.assertTrue(ok)
        self.assertEqual(gate["resolved_path"], "technology/devops")

    def test_create_revalidates_under_lock(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            a = mkcourse(root, "technology/devops", "Docker A")
            # Competitor created the category first: second create reuses it
            # without any confirmation flags, mints its own course_id, and
            # never duplicates the category.
            b = mod.course_create(root, "technology/devops", "Docker B", "g",
                                  confirm_new_segments=[])
            self.assertNotEqual(a["course_id"], b["course_id"])
            self.assertEqual(a["category_path"], b["category_path"])
            # Same title in the same category: precise conflict, not a copy.
            with self.assertRaises(ValueError):
                mod.course_create(root, "technology/devops", "Docker B", "g",
                                  confirm_new_segments=[])


class TestRoutingModelIndependent(unittest.TestCase):
    def test_grammar_typo_gated_not_silently_created(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at")
            dirs_before = {p.name for p in (root / "languages/english").iterdir()}
            with self.assertRaises(ValueError):
                mod.course_create(root, "languages/english/grammer", "Grammer", "g")
            dirs_after = {p.name for p in (root / "languages/english").iterdir()}
            self.assertEqual(dirs_before, dirs_after)

    def test_java_vs_javanese_distinct(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            j = mod.course_create(root, "technology/programming/java", "Java", "g",
                                  confirm_new_segments=["programming", "java"])
            v = mod.course_create(root, "languages/javanese", "Javanese", "g",
                                  confirm_new_segments=["javanese"])
            self.assertNotEqual(j["course_id"], v["course_id"])
            self.assertEqual(mod.course_resolve(root, "Java")["course"]["course_id"],
                             j["course_id"])
            self.assertEqual(mod.course_resolve(root, "Javanese")["course"]["course_id"],
                             v["course_id"])

    def test_semantic_scenarios_a_to_j_gate_outcomes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            mkcourse(root, "languages/english/grammar", "in on at")
            mkcourse(root, "technology/devops/vocabulary", "DevOps words",
                     confirm_new_segments=["devops", "vocabulary"])
            reg = mod.registry_read(root)

            def verdict(path):
                ok, gate = rt.validate_classification(path, reg)
                self.assertTrue(ok, path)
                return gate

            # A/B: distinct branches, neither satisfied by english/grammar
            g = verdict("languages/indonesian/grammar")
            self.assertEqual(g["verdict"], "new-needs-confirmation")
            g = verdict("languages/japanese/grammar")
            self.assertEqual(g["verdict"], "new-needs-confirmation")
            # D: devops vocabulary reuses existing category
            g = verdict("technology/devops/vocabulary")
            self.assertEqual(g["verdict"], "reuse")
            # F: python grammar is technology, unaffected by Languages grammar
            g = verdict("technology/programming/python")
            self.assertEqual(
                [v["verdict"] for v in g["segments"] if v["segment"] != "technology"],
                ["new-needs-confirmation", "new-needs-confirmation"])

    def test_exact_title_reuse(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = mkroot(d)
            c = mkcourse(root, "languages/english/grammar", "in on at")
            found = mod.course_resolve(root, "in/on/at")
            self.assertEqual(found["status"], "found")
            self.assertEqual(found["matched_by"], "title")

    def test_traversal_rejected(self):
        valid, _ = mod.validate_path("../evil", "/tmp/Courses")
        self.assertFalse(valid)

    def test_reserved_names(self):
        valid, _ = mod.validate_path("languages/CON", "/tmp/Courses")
        self.assertFalse(valid)

    def test_absolute_path(self):
        valid, _ = mod.validate_path("/etc/passwd", "/tmp/Courses")
        self.assertFalse(valid)

    def test_invalid_chars(self):
        valid, _ = mod.validate_path("a/b<c", "/tmp/Courses")
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
