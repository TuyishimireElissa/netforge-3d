"""Actual SQLite file migration/round-trip/rollback; no mock database."""
import sqlite3
import tempfile
from pathlib import Path
import unittest

from backend.server import App
from database.store import SQLiteStore, PersistenceError, MAX_CHECKPOINTS
from simulation.core import Lab


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "lab.sqlite3"

    def action(self, app, payload):
        status, result = app.handle("POST", "/action", "token", payload)
        self.assertEqual(status, 200, result)
        return result

    def test_migration_initialization_and_future_version_rejected(self):
        store = SQLiteStore(self.path)
        self.assertEqual(store.db.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertTrue(store.db.execute("PRAGMA foreign_keys").fetchone()[0])
        self.assertEqual(store.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        store.close()
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA user_version=55")
        with self.assertRaisesRegex(PersistenceError, "Unsupported SQLite schema version"):
            SQLiteStore(self.path)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 55)

    def test_migration_rollback_on_conflicting_table(self):
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE links (bad_column TEXT)")
        with self.assertRaises(sqlite3.DatabaseError):
            SQLiteStore(self.path)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall(), [("links",)])

    def test_round_trip_mission_b_restart_reset_restore(self):
        app = App("token", self.path)
        self.assertTrue(app.provider.capabilities()["persistent_checkpoint"])
        self.action(app, {"action": "connect", "a": "pc-b:eth0", "b": "sw1:fa0/3"})
        for command in ("enable", "configure terminal", "interface fastethernet 0/3", "switchport port-security",
                        "switchport port-security mac-address sticky", "end"):
            self.action(app, {"action": "command", "device": "sw1", "line": command})
        self.action(app, {"action": "ping", "source": "pc-b:eth0", "target": "pc-a:eth0"})
        self.action(app, {"action": "command", "device": "sw1", "line": "write memory"})
        original = app.provider.lab.state()
        self.assertTrue(original["assessment"]["mission_b"]["complete"])
        self.assertEqual(self.action(app, {"action": "checkpoint"})["result"]["checkpoint_id"],
                         app.provider.read_device_state()["checkpoints"][0]["id"])
        checkpoint_id = app.provider.read_device_state()["checkpoints"][0]["id"]
        app.close()

        app = App("token", self.path)
        loaded = app.provider.lab.state()
        for field in ("ports", "links", "mac_table", "trace", "events", "assessment", "cli_mode", "saved"):
            self.assertEqual(loaded[field], original[field], field)
        self.action(app, {"action": "reset"})
        self.assertFalse(app.provider.lab.assess()["mission_a"]["complete"])
        self.assertFalse(app.provider.lab.state()["ports"]["pc-b:eth0"]["linked"])
        self.assertTrue(app.provider.read_device_state()["checkpoints"])
        self.action(app, {"action": "restore", "checkpoint_id": checkpoint_id})
        self.assertEqual(app.provider.lab.state()["assessment"], original["assessment"])
        self.action(app, {"action": "delete_checkpoint", "checkpoint_id": checkpoint_id})
        self.assertEqual(app.provider.read_device_state()["checkpoints"], [])
        app.close()
        app = App("token", self.path)
        self.assertTrue(app.provider.lab.assess()["mission_b"]["complete"])
        self.assertEqual(app.provider.read_device_state()["checkpoints"], [])
        app.close()

    def test_cli_mode_and_persistence_of_failed_ping(self):
        app = App("token", self.path)
        self.action(app, {"action": "command", "device": "sw1", "line": "enable"})
        self.action(app, {"action": "command", "device": "sw1", "line": "configure terminal"})
        self.action(app, {"action": "command", "device": "sw1", "line": "interface fastethernet 0/3"})
        self.action(app, {"action": "ping", "source": "pc-b:eth0", "target": "pc-a:eth0"})
        app.close()
        app = App("token", self.path)
        self.assertEqual((app.provider.lab.cli.mode, app.provider.lab.cli.selected), ("interface", "sw1:fa0/3"))
        self.assertIn("disconnected", " ".join(app.provider.lab.traces))
        self.assertEqual(app.provider.lab.events.count("Lab reset: PC-B cable is disconnected"), 1)
        app.close()

    def test_invalid_checkpoint_id_and_ephemeral_rejection(self):
        app = App("token", self.path)
        for bad_id in (None, True, -1, "1", 999):
            self.assertEqual(app.handle("POST", "/action", "token", {"action": "restore", "checkpoint_id": bad_id})[0], 400)
        self.assertEqual(app.handle("GET", "/missions", "wrong")[0], 401)
        status, body = app.handle("GET", "/missions", "token")
        self.assertEqual(status, 200)
        self.assertEqual(body["missions"][0]["fidelity"], "SIMULATED")
        app.close()
        ephemeral = App("token")
        self.assertFalse(ephemeral.provider.capabilities()["persistent_checkpoint"])
        self.assertEqual(ephemeral.handle("POST", "/action", "token", {"action":"checkpoint"})[0], 400)

    def test_checkpoint_limit_and_delete(self):
        store = SQLiteStore(self.path)
        lab = Lab(durable=True)
        ids = [store.save_checkpoint(lab) for _ in range(MAX_CHECKPOINTS)]
        self.assertEqual(len(store.list_checkpoints()), MAX_CHECKPOINTS)
        with self.assertRaisesRegex(PersistenceError, "Checkpoint limit"):
            store.save_checkpoint(lab)
        store.delete_checkpoint(ids[0])
        self.assertEqual(len(store.list_checkpoints()), MAX_CHECKPOINTS - 1)
        store.close()

    def test_atomic_save_rollback_and_foreign_keys(self):
        store = SQLiteStore(self.path)
        lab = Lab(durable=True)
        store.save_active(lab)
        lab.connect("pc-b:eth0", "sw1:fa0/3")
        store.db.execute("""CREATE TRIGGER reject_port BEFORE INSERT ON port_states
                            BEGIN SELECT RAISE(ABORT, 'simulated disk failure'); END""")
        with self.assertRaises(sqlite3.DatabaseError):
            store.save_active(lab)
        self.assertFalse(store.load_active().link_of("pc-b:eth0"))
        self.assertEqual(store.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        store.close()
