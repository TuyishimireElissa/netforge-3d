"""SQLite v1 normalized, atomic persistence for the built-in *simulation* only.

One active revision and up to 20 user checkpoints. No OS networking or real-lab data.
A future schema requires an explicit forward migration; unknown versions fail closed.
"""
from __future__ import annotations

from datetime import datetime, timezone
import ipaddress
from pathlib import Path
import sqlite3

from simulation.core import Lab, Link, Port

SCHEMA_VERSION = 1
MAX_CHECKPOINTS = 20


class PersistenceError(ValueError):
    pass


DDL = (
    """CREATE TABLE revisions (
        id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('active','checkpoint')),
        created_at TEXT NOT NULL, last_ping INTEGER NOT NULL CHECK(last_ping IN (0,1)),
        last_source TEXT NOT NULL, last_target TEXT NOT NULL,
        cli_mode TEXT NOT NULL, cli_selected TEXT NOT NULL,
        has_saved INTEGER NOT NULL CHECK(has_saved IN (0,1)))""",
    "CREATE UNIQUE INDEX one_active ON revisions(kind) WHERE kind='active'",
    """CREATE TABLE port_states (
        revision_id INTEGER NOT NULL REFERENCES revisions(id) ON DELETE CASCADE,
        port_id TEXT NOT NULL, device TEXT NOT NULL, mac TEXT NOT NULL, address TEXT NOT NULL,
        enabled INTEGER NOT NULL CHECK(enabled IN (0,1)), vlan INTEGER NOT NULL CHECK(vlan BETWEEN 1 AND 4094),
        mode TEXT NOT NULL, security INTEGER NOT NULL CHECK(security IN (0,1)),
        sticky INTEGER NOT NULL CHECK(sticky IN (0,1)), maximum INTEGER NOT NULL CHECK(maximum BETWEEN 1 AND 4),
        violation TEXT NOT NULL, violated INTEGER NOT NULL CHECK(violated IN (0,1)),
        PRIMARY KEY(revision_id, port_id))""",
    """CREATE TABLE links (
        revision_id INTEGER NOT NULL REFERENCES revisions(id) ON DELETE CASCADE,
        a TEXT NOT NULL, b TEXT NOT NULL, media TEXT NOT NULL CHECK(media='copper'),
        PRIMARY KEY(revision_id,a,b), UNIQUE(revision_id,a), UNIQUE(revision_id,b),
        FOREIGN KEY(revision_id,a) REFERENCES port_states(revision_id,port_id),
        FOREIGN KEY(revision_id,b) REFERENCES port_states(revision_id,port_id))""",
    """CREATE TABLE learned_macs (
        revision_id INTEGER NOT NULL, port_id TEXT NOT NULL, mac TEXT NOT NULL,
        PRIMARY KEY(revision_id,port_id,mac),
        FOREIGN KEY(revision_id,port_id) REFERENCES port_states(revision_id,port_id) ON DELETE CASCADE)""",
    """CREATE TABLE mac_entries (
        revision_id INTEGER NOT NULL, vlan INTEGER NOT NULL, mac TEXT NOT NULL, port_id TEXT NOT NULL,
        PRIMARY KEY(revision_id,vlan,mac),
        FOREIGN KEY(revision_id,port_id) REFERENCES port_states(revision_id,port_id) ON DELETE CASCADE)""",
    """CREATE TABLE saved_ports (
        revision_id INTEGER NOT NULL, port_id TEXT NOT NULL,
        vlan INTEGER NOT NULL, enabled INTEGER NOT NULL, security INTEGER NOT NULL, sticky INTEGER NOT NULL,
        maximum INTEGER NOT NULL, violation TEXT NOT NULL,
        PRIMARY KEY(revision_id,port_id),
        FOREIGN KEY(revision_id,port_id) REFERENCES port_states(revision_id,port_id) ON DELETE CASCADE)""",
    """CREATE TABLE saved_sticky_macs (
        revision_id INTEGER NOT NULL REFERENCES revisions(id) ON DELETE CASCADE, mac TEXT NOT NULL,
        PRIMARY KEY(revision_id,mac))""",
    """CREATE TABLE messages (
        revision_id INTEGER NOT NULL REFERENCES revisions(id) ON DELETE CASCADE,
        kind TEXT NOT NULL CHECK(kind IN ('trace','event')),
        position INTEGER NOT NULL CHECK(position >= 0), text TEXT NOT NULL,
        PRIMARY KEY(revision_id,kind,position))""",
)


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        # HTTP worker threads share this connection only while App.lock serializes requests.
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        try:
            self._migrate()
        except Exception:
            self.db.close()
            raise

    def close(self) -> None:
        self.db.close()

    def _migrate(self) -> None:
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION or version < 0:
            raise PersistenceError(f"Unsupported SQLite schema version {version}; expected <= {SCHEMA_VERSION}")
        if version == 0:
            # BEGIN/COMMIT keeps schema migration atomic even if DDL fails. No executescript implicit commit.
            self.db.execute("BEGIN IMMEDIATE")
            try:
                for statement in DDL:
                    self.db.execute(statement)
                self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                self.db.commit()
            except sqlite3.DatabaseError:
                self.db.rollback()
                raise
        result = self.db.execute("PRAGMA quick_check").fetchone()[0]
        if result != "ok":
            raise PersistenceError(f"SQLite integrity check failed: {result}")

    def _write(self, lab: Lab, kind: str) -> int:
        # Caller wraps this and optional deletion in a single transaction.
        cursor = self.db.execute(
            "INSERT INTO revisions(kind,created_at,last_ping,last_source,last_target,cli_mode,cli_selected,has_saved) VALUES(?,?,?,?,?,?,?,?)",
            (kind, datetime.now(timezone.utc).isoformat(), int(lab.last_ping), lab.last_ping_source,
             lab.last_ping_target, lab.cli.mode, lab.cli.selected, int(lab.saved_config is not None)))
        rid = cursor.lastrowid
        for p in lab.ports.values():
            self.db.execute("INSERT INTO port_states VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (rid, p.id, p.device, p.mac, p.address, int(p.enabled), p.vlan, p.mode,
                             int(p.security), int(p.sticky), p.maximum, p.violation, int(p.violated)))
        for link in lab.links:
            self.db.execute("INSERT INTO links VALUES(?,?,?,?)", (rid, link.a, link.b, link.media))
        for p in lab.ports.values():
            for mac in sorted(p.learned):
                self.db.execute("INSERT INTO learned_macs VALUES(?,?,?)", (rid, p.id, mac))
        for (vlan, mac), port_id in sorted(lab.mac_table.items()):
            self.db.execute("INSERT INTO mac_entries VALUES(?,?,?,?)", (rid, vlan, mac, port_id))
        if lab.saved_config is not None:
            for port_id, saved in lab.saved_config["interfaces"].items():
                self.db.execute("INSERT INTO saved_ports VALUES(?,?,?,?,?,?,?,?)",
                                (rid, port_id, saved["vlan"], int(saved["enabled"]), int(saved["security"]),
                                 int(saved["sticky"]), saved["maximum"], saved["violation"]))
            for mac in lab.saved_config["sticky_macs"]:
                self.db.execute("INSERT INTO saved_sticky_macs VALUES(?,?)", (rid, mac))
        for kind_name, entries in (("trace", lab.traces[-80:]), ("event", lab.events[-80:])):
            for position, text in enumerate(entries):
                self.db.execute("INSERT INTO messages VALUES(?,?,?,?)", (rid, kind_name, position, text))
        return rid

    def save_active(self, lab: Lab) -> None:
        with self.db:
            self.db.execute("DELETE FROM revisions WHERE kind='active'")
            self._write(lab, "active")

    def save_checkpoint(self, lab: Lab) -> int:
        with self.db:
            count = self.db.execute("SELECT COUNT(*) FROM revisions WHERE kind='checkpoint'").fetchone()[0]
            if count >= MAX_CHECKPOINTS:
                raise PersistenceError(f"Checkpoint limit reached ({MAX_CHECKPOINTS}); delete one first")
            return self._write(lab, "checkpoint")

    def list_checkpoints(self) -> list[dict]:
        return [{"id": row["id"], "created_at": row["created_at"]} for row in self.db.execute(
            "SELECT id,created_at FROM revisions WHERE kind='checkpoint' ORDER BY id DESC")]

    def delete_checkpoint(self, checkpoint_id: int) -> None:
        if type(checkpoint_id) is not int or checkpoint_id < 1:
            raise PersistenceError("Invalid checkpoint ID")
        with self.db:
            cursor = self.db.execute("DELETE FROM revisions WHERE id=? AND kind='checkpoint'", (checkpoint_id,))
            if cursor.rowcount != 1:
                raise PersistenceError("Checkpoint not found")

    def load_active(self) -> Lab | None:
        row = self.db.execute("SELECT id FROM revisions WHERE kind='active'").fetchone()
        return self._load(row[0]) if row else None

    def load_checkpoint(self, checkpoint_id: int) -> Lab:
        if type(checkpoint_id) is not int or checkpoint_id < 1:
            raise PersistenceError("Invalid checkpoint ID")
        row = self.db.execute("SELECT id FROM revisions WHERE id=? AND kind='checkpoint'", (checkpoint_id,)).fetchone()
        if row is None:
            raise PersistenceError("Checkpoint not found")
        return self._load(row[0])

    def _load(self, rid: int) -> Lab:
        row = self.db.execute("SELECT * FROM revisions WHERE id=?", (rid,)).fetchone()
        if row is None:
            raise PersistenceError("Revision not found")
        lab = Lab(durable=True)
        lab.events = []
        lab.traces = []
        ports = {}
        for p in self.db.execute("SELECT * FROM port_states WHERE revision_id=?", (rid,)):
            ports[p["port_id"]] = Port(p["port_id"], p["device"], p["mac"], p["address"],
                                  bool(p["enabled"]), p["vlan"], p["mode"], bool(p["security"]),
                                  bool(p["sticky"]), p["maximum"], p["violation"],
                                  {m[0] for m in self.db.execute(
                                      "SELECT mac FROM learned_macs WHERE revision_id=? AND port_id=?", (rid, p["port_id"]))},
                                  bool(p["violated"]))
        if set(ports) != set(lab.ports) or any(p.device != lab.ports[k].device for k, p in ports.items()):
            raise PersistenceError("Stored interfaces do not match built-in topology")
        for p in ports.values():
            if p.address:
                try:
                    ipaddress.IPv4Interface(p.address)
                except ValueError as exc:
                    raise PersistenceError("Invalid stored IPv4 address") from exc
            if p.mode != "access" or p.violation not in ("shutdown", "restrict", "protect"):
                raise PersistenceError("Unsupported stored switch configuration")
        lab.ports = ports
        lab.links = [Link(l["a"], l["b"], l["media"]) for l in self.db.execute(
            "SELECT a,b,media FROM links WHERE revision_id=? ORDER BY a,b", (rid,))]
        # Schema v1 previously persisted either orientation from the API. Accept
        # those valid old saves, but normalize before enforcing the topology.
        for link in lab.links:
            if link.a not in ports or link.b not in ports:
                raise PersistenceError("Stored links reference unknown interfaces")
            if ports[link.a].device == "sw1":
                link.a, link.b = link.b, link.a
        pairs = {(l.a, l.b) for l in lab.links}
        if len(pairs) != len(lab.links):
            raise PersistenceError("Stored links contain duplicate cables")
        if not {("pc-a:eth0", "sw1:fa0/1")} <= pairs or not pairs <= {
                ("pc-a:eth0", "sw1:fa0/1"), ("pc-b:eth0", "sw1:fa0/3")}:
            raise PersistenceError("Stored links do not match built-in topology")
        lab.mac_table = {(m["vlan"], m["mac"]): m["port_id"] for m in self.db.execute(
            "SELECT * FROM mac_entries WHERE revision_id=?", (rid,))}
        if row["has_saved"]:
            saved = {}
            for p in self.db.execute("SELECT * FROM saved_ports WHERE revision_id=?", (rid,)):
                saved[p["port_id"]] = {"vlan": p["vlan"], "enabled": bool(p["enabled"]),
                                       "security": bool(p["security"]), "sticky": bool(p["sticky"]),
                                       "maximum": p["maximum"], "violation": p["violation"]}
            if set(saved) != {"sw1:fa0/1", "sw1:fa0/3"}:
                raise PersistenceError("Stored switch configuration is incomplete")
            lab.saved_config = {"interfaces": saved, "sticky_macs": [m[0] for m in self.db.execute(
                "SELECT mac FROM saved_sticky_macs WHERE revision_id=? ORDER BY mac", (rid,))]}
        for message in self.db.execute("SELECT kind,text FROM messages WHERE revision_id=? ORDER BY kind,position", (rid,)):
            (lab.traces if message["kind"] == "trace" else lab.events).append(message["text"])
        lab.last_ping, lab.last_ping_source, lab.last_ping_target = bool(row["last_ping"]), row["last_source"], row["last_target"]
        lab.cli.mode, lab.cli.selected = row["cli_mode"], row["cli_selected"]
        if lab.cli.mode not in ("user", "privileged", "config", "interface") or (
            lab.cli.mode == "interface" and lab.cli.selected not in ("sw1:fa0/1", "sw1:fa0/3")) or (
            lab.cli.mode != "interface" and lab.cli.selected):
            raise PersistenceError("Invalid stored CLI mode")
        return lab
