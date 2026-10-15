"""Bundle/schema validation and outcome scoring; no untrusted expression evaluation."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from simulation.core import Lab
from simulation import missions


class MissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        for source in missions.SCENARIOS.glob("mission_*.json"):
            (self.folder / source.name).write_bytes(source.read_bytes())

    def change(self, filename, **changes):
        path = self.folder / filename
        doc = json.loads(path.read_text())
        doc.update(changes)
        path.write_text(json.dumps(doc))

    def test_bundle_and_weighted_outcome_not_commands(self):
        defs = missions.load_missions(self.folder)
        self.assertEqual([m.api_key for m in defs], ["mission_a", "mission_b"])
        self.assertEqual(defs[1].describe()["max_score"], 5)
        lab = Lab()
        with patch.object(missions, "MISSIONS", defs):
            self.assertFalse(lab.assess()["mission_a"]["complete"])
            lab.connect("pc-b:eth0", "sw1:fa0/3")
            report = lab.assess()["mission_a"]
            self.assertEqual(report["score"], 1)
            self.assertFalse(report["complete"])
            self.assertTrue(lab.ping("pc-b:eth0", "pc-a:eth0"))
            self.assertEqual(lab.assess()["mission_a"]["score"], 2)
            self.assertTrue(lab.assess()["mission_a"]["complete"])

    def test_changed_rubric_weights_are_executed(self):
        self.change("mission_a.json", rubric={"cable_present": 7, "successful_ping_evidence": 3})
        defs = missions.load_missions(self.folder)
        lab = Lab()
        lab.connect("pc-b:eth0", "sw1:fa0/3")
        with patch.object(missions, "MISSIONS", defs):
            self.assertEqual((lab.assess()["mission_a"]["score"], lab.assess()["mission_a"]["max_score"]), (7, 10))

    def test_invalid_schema_and_expression_fail_closed(self):
        cases = [
            {"schema_version": 99},
            {"rubric": {"execute_shell": 1}},
            {"success": "cable_present AND __import__('os').system('whoami')"},
            {"success": "cable_present"},
            {"authorized_targets": ["third-party-host:eth0"]},
            {"prerequisites": ["school-sticky-security"]},
        ]
        original = json.loads((self.folder / "mission_a.json").read_text())
        for mutation in cases:
            with self.subTest(mutation=mutation):
                self.change("mission_a.json", **mutation)
                with self.assertRaises(missions.MissionDefinitionError):
                    missions.load_missions(self.folder)
                (self.folder / "mission_a.json").write_text(json.dumps(original))

    def test_duplicate_json_fields_rejected(self):
        path = self.folder / "mission_a.json"
        raw = path.read_text()
        path.write_text(raw.replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,'))
        with self.assertRaisesRegex(missions.MissionDefinitionError, "Duplicate JSON field"):
            missions.load_missions(self.folder)

    def test_missing_definition_and_duplicate_id(self):
        self.change("mission_b.json", id="school-link-repair")
        with self.assertRaises(missions.MissionDefinitionError):
            missions.load_missions(self.folder)
        for file in self.folder.iterdir():
            file.unlink()
        with self.assertRaises(missions.MissionDefinitionError):
            missions.load_missions(self.folder)

    def test_unsaved_or_stale_config_fails(self):
        lab = Lab()
        lab.connect("pc-b:eth0", "sw1:fa0/3")
        for line in ("enable", "configure terminal", "interface fastethernet 0/3", "switchport port-security",
                     "switchport port-security mac-address sticky"):
            lab.cli.execute(line)
        lab.ping("pc-b:eth0", "pc-a:eth0")
        self.assertFalse(lab.assess()["mission_b"]["complete"])
        lab.cli.execute("end")
        lab.cli.execute("write memory")
        self.assertTrue(lab.assess()["mission_b"]["complete"])
        lab.ports["sw1:fa0/3"].maximum = 2
        self.assertFalse(lab.assess()["mission_b"]["complete"])
