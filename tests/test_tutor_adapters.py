"""W6 gate: provider-neutral turn contract golden behaviors.

One question per turn, wait-for-answer, hint ladder attribution, confusion
never scored, conservative transfer prompts, delayed needs an external
reference, low-context bounds, invalid output fails closed, and every
preset renders the same deterministic schema.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import learnprint_adapters as ad  # noqa: E402


def contract(**over):
    base = {
        "schema_version": ad.TURN_SCHEMA_VERSION,
        "learning_goal": "Linux networking commands for support work",
        "current_competency": "systemctl-journal-reading",
        "current_state": "EXPLAIN",
        "assistance_allowed": "hint",
        "target_behavior": "ask one attempt question with hidden answer",
        "expected_next_event": "ask_attempt",
        "prohibited_behavior": ["browser_use"],
    }
    base.update(over)
    return base


def turn(kind, content="What does the learner do next?", **over):
    payload = {"kind": kind, "content": content}
    payload.update(over)
    return json.dumps(payload)


class TestContractValidation(unittest.TestCase):
    def test_minimal_contract_validates_and_fills_defaults(self):
        filled = ad.validate_contract(contract())
        self.assertEqual(filled["prohibited_behavior"], ["browser_use"])

    def test_missing_required_field_rejected(self):
        bad = contract()
        del bad["assistance_allowed"]
        with self.assertRaises(ad.TurnContractError):
            ad.validate_contract(bad)

    def test_bad_assistance_level_rejected(self):
        with self.assertRaises(ad.TurnContractError):
            ad.validate_contract(contract(assistance_allowed="cheat"))

    def test_fabricated_source_status_rejected(self):
        with self.assertRaises(ad.TurnContractError) as ctx:
            ad.validate_contract(
                contract(source_context={"status": "verified-by-my-feelings"})
            )
        self.assertIn("fabricated", str(ctx.exception).lower() or "status")

    def test_unknown_preset_rejected(self):
        with self.assertRaises(ad.TurnContractError):
            ad.render(contract(), preset="seductive")


class TestRendererGolden(unittest.TestCase):
    def test_exactly_one_question_instruction(self):
        text = ad.render_generic(contract())
        self.assertEqual(text.count("EXACTLY ONE"), 1)
        self.assertIn(ad.MARKER, text)
        self.assertIn(ad.END_MARKER, text)
        self.assertIn("T01", text)
        self.assertIn("T08", text)

    def test_presets_render_same_deterministic_json_block(self):
        generic = ad.render_generic(contract())
        markdown = ad.render_markdown(contract())
        self.assertIn(generic, markdown)
        first = ad.render_generic(contract())
        self.assertEqual(generic, first, "rendering must be deterministic")

    def test_low_context_bounded_and_truncates(self):
        long_goal = "g" * 5000
        many = [{"note": "n" * 400} for _ in range(10)]
        text = ad.render_low_context(
            contract(learning_goal=long_goal, prior_evidence=many)
        )
        self.assertLessEqual(len(text), ad.LOW_CONTEXT_CHAR_BOUND)
        self.assertIn(ad.MARKER, text)
        self.assertIn("T06", text)

    def test_low_context_rejects_when_unboundable(self):
        original = ad.LOW_CONTEXT_CHAR_BOUND
        ad.LOW_CONTEXT_CHAR_BOUND = 100
        try:
            with self.assertRaises(ad.TurnContractError):
                ad.render_low_context(contract())
        finally:
            ad.LOW_CONTEXT_CHAR_BOUND = original


class TestParseGolden(unittest.TestCase):
    def test_valid_ask_attempt_parses_with_default_assistance(self):
        parsed = ad.parse_turn_output(
            turn("ask_attempt", "Try: journalctl -u nginx --since today shows what?", task_label="t-l1")
        )
        self.assertEqual(parsed["kind"], "ask_attempt")
        self.assertEqual(parsed["assistance"], "none")
        self.assertEqual(parsed["task_label"], "t-l1")

    def test_expected_kind_mismatch_rejected(self):
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(turn("hint", "..."), expected_kind="ask_attempt")

    def test_two_json_objects_rejected_longest_match_fails_closed(self):
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(
                turn("explain", "ok") + "\n" + turn("ask_attempt", "another")
            )

    def test_plain_prose_rejected(self):
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output("I recommend running journalctl first.")

    def test_unknown_kind_rejected(self):
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(turn("grade", "I grade this 2/2."))
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(json.dumps({"kind": "scored", "score": 2, "content": "x"}))

    def test_score_fields_rejected(self):
        for banned in ("rubric", "scored", "score"):
            with self.subTest(banned=banned):
                with self.assertRaises(ad.TurnContractError):
                    ad.parse_turn_output(turn("explain", "fine", **{banned: 2}))

    def test_attempt_prompt_must_not_leak_answer(self):
        with self.assertRaises(ad.TurnContractError) as ctx:
            ad.parse_turn_output(
                turn("ask_attempt", "The answer key is: systemctl status nginx.", task_label="t")
            )
        self.assertIn("T01", str(ctx.exception))

    def test_hint_requires_assistance_attribution(self):
        with self.assertRaises(ad.TurnContractError) as ctx:
            ad.parse_turn_output(turn("hint", "Check the unit file.", task_label="t"))
        self.assertIn("T03", str(ctx.exception))
        parsed = ad.parse_turn_output(
            turn("hint", "Check the unit file.", task_label="t", assistance="hint")
        )
        self.assertEqual(parsed["assistance"], "hint")

    def test_hint_must_not_contain_solution(self):
        with self.assertRaises(ad.TurnContractError) as ctx:
            ad.parse_turn_output(
                turn(
                    "hint",
                    "solution: restart nginx.service",
                    task_label="t",
                    assistance="hint",
                )
            )
        self.assertIn("T03", str(ctx.exception))

    def test_over_help_beyond_contract_rejected(self):
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(
                turn("hint", "Read the unit file.", task_label="t", assistance="worked_example"),
                allowed_help="hint",
            )
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(
                turn("ask_attempt", "Try journalctl.", task_label="t", assistance="hint"),
                allowed_help="none",
            )

    def test_clarify_never_discloses_answer_and_is_not_scored(self):
        with self.assertRaises(ad.TurnContractError) as ctx:
            ad.parse_turn_output(turn("clarify", "answer key: nginx restarts it."))
        self.assertIn("T02", str(ctx.exception))
        parsed = ad.parse_turn_output(
            turn("clarify", "Which part is confusing: the unit name or the flags?")
        )
        self.assertEqual(parsed["kind"], "clarify")
        self.assertEqual(parsed["assistance"], "none")

    def test_delayed_reminder_requires_external_reference(self):
        with self.assertRaises(ad.TurnContractError) as ctx:
            ad.parse_turn_output(turn("delayed_reminder", "Remember journalctl?"))
        self.assertIn("T06", str(ctx.exception))
        parsed = ad.parse_turn_output(
            turn(
                "delayed_reminder",
                "Recall this after a real interval.",
                external_ref="eval:review:2026-10-24:01",
            )
        )
        self.assertEqual(parsed["external_ref"], "eval:review:2026-10-24:01")

    def test_transfer_task_labeled_and_bound(self):
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(turn("transfer_task", "answer key: use rsync."))
        parsed = ad.parse_turn_output(
            turn(
                "transfer_task",
                "Mirror a directory on a remote host you administer without revealing commands in advance.",
                task_label="t-transfer-1",
            )
        )
        self.assertEqual(parsed["kind"], "transfer_task")

    def test_content_bound_rejected(self):
        with self.assertRaises(ad.TurnContractError):
            ad.parse_turn_output(turn("explain", "x" * (ad.CONTENT_CHAR_BOUND + 1)))

    def test_cli_parse_and_render_roundtrip(self):
        import tempfile
        from pathlib import Path as P

        with tempfile.TemporaryDirectory() as d:
            contract_file = P(d) / "contract.json"
            contract_file.write_text(json.dumps(contract()), encoding="utf-8")
            import io
            from contextlib import redirect_stdout

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = ad.main(
                    ["render", "--contract", str(contract_file), "--preset", "low_context"]
                )
            self.assertEqual(rc, 0)
            rendered = buf.getvalue()
            self.assertIn("EXACTLY ONE", rendered)
            self.assertLessEqual(len(rendered), ad.LOW_CONTEXT_CHAR_BOUND + 1)


class TestTurnSchemaFile(unittest.TestCase):
    def test_schema_matches_module_enums(self):
        schema = json.loads((ROOT / "schemas" / "tutor-turn.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            schema["definitions"]["source_status"]["enum"], list(ad.SOURCE_STATUSES)
        )
        self.assertEqual(schema["definitions"]["turn_kind"]["enum"], list(ad.TURN_KINDS))
        self.assertEqual(
            schema["definitions"]["assistance_level"]["enum"], list(ad.ASSISTANCE_LEVELS)
        )


if __name__ == "__main__":
    unittest.main()
