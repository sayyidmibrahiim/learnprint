"""Legacy Python 3.9 grammar compatibility gate for first-party Python sources.

Python 3.9 is EOL as of 2025-10-31 and is NOT a supported production runtime.

This test runs on newer Python as a fast portability smoke check. Passing
does NOT prove Python 3.9 runtime, stdlib API, or OS compatibility.
"""
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MINIMUM_PYTHON = (3, 9)


class TestPython39Syntax(unittest.TestCase):
    def test_first_party_sources_parse_as_python39(self):
        paths = sorted((ROOT / "scripts").glob("*.py"))
        paths += sorted((ROOT / "tests").glob("*.py"))
        self.assertTrue(paths, "first-party Python source files must be found")
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                source = path.read_text(encoding="utf-8-sig")
                ast.parse(source, filename=str(path), feature_version=MINIMUM_PYTHON)

    def test_positive_control_python39_syntax_is_accepted(self):
        source = "def f(x):\n    return x if x is not None else 0\n"
        self.assertIsInstance(
            ast.parse(source, feature_version=MINIMUM_PYTHON), ast.Module
        )

    def test_negative_control_python310_match_is_rejected(self):
        source = "match x:\n    case 1:\n        pass\n"
        with self.assertRaises(SyntaxError):
            ast.parse(source, feature_version=MINIMUM_PYTHON)


if __name__ == "__main__":
    unittest.main()
