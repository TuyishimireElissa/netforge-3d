"""Verification exit policy and diagnostic report tests (no fake engine success)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from tools.verify import Verifier


class VerificationTests(unittest.TestCase):
    def test_optional_engine_marks_blocked_and_strict_engine_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            reports = Path(directory)
            optional = Verifier(reports / "optional", False)
            optional.godot_checks(None)
            self.assertEqual(optional.finish(), 0)
            state = json.loads((reports / "optional" / "report.json").read_text())
            self.assertEqual([item["status"] for item in state["checks"]], ["blocked"] * 3)
            required = Verifier(reports / "strict", True)
            required.godot_checks(None)
            self.assertEqual(required.finish(), 1)
            self.assertEqual(json.loads((reports / "strict" / "report.json").read_text())["exit_code"], 1)

    def test_failure_retains_process_output_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            verify = Verifier(Path(directory), False)
            self.assertFalse(verify.run("expected_failure", [sys.executable, "-c", "print('diagnostic');raise SystemExit(7)"]))
            self.assertEqual(verify.finish(), 1)
            self.assertIn("diagnostic", (Path(directory) / "expected_failure.log").read_text())
