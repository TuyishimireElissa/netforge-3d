"""Loopback-only, token-protected JSON API for the Godot desktop client."""
import argparse
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import RLock

from database.store import SQLiteStore, PersistenceError
from providers.builtin import BuiltinProvider
from providers.base import UnsupportedOperation
from simulation.core import LabError
from simulation.missions import MISSIONS


class App:
    def __init__(self, token: str, db_path: str | Path | None = None):
        if not isinstance(token, str) or not token or not token.isascii():
            raise ValueError("A non-empty ASCII session token is required")
        self.token = token
        self.store = SQLiteStore(db_path) if db_path is not None else None
        self.provider = BuiltinProvider(self.store)
        self.lock = RLock()

    def close(self) -> None:
        if self.store:
            self.store.close()

    def handle(self, method: str, path: str, token: str, payload: dict | None = None) -> tuple[int, dict]:
        # compare_digest(str, str) raises on non-ASCII input. Malformed header
        # values must get a normal 401 response, not terminate the HTTP worker.
        if not isinstance(token, str) or not token.isascii() or not hmac.compare_digest(token, self.token):
            return 401, {"error": "Invalid session token"}
        with self.lock:
            if method == "GET" and path == "/state":
                return 200, {"state": self.provider.read_device_state(), "capabilities": self.provider.capabilities()}
            if method == "GET" and path == "/missions":
                return 200, {"missions": [mission.describe() for mission in MISSIONS]}
            if method != "POST" or path != "/action":
                return 404, {"error": "Unknown endpoint"}
            if not isinstance(payload, dict):
                return 400, {"error": "Action requires a JSON object"}
            lab = self.provider.lab
            try:
                action = payload.get("action")
                persist = True
                if action == "connect":
                    lab.connect(payload.get("a"), payload.get("b"), payload.get("media", "copper"))
                    result = "Cable connected"
                elif action == "disconnect":
                    lab.disconnect(payload.get("port"))
                    result = "Cable disconnected"
                elif action == "ping":
                    result = "Simulated ping succeeded" if lab.ping(payload.get("source"), payload.get("target")) else "Simulated ping failed; inspect trace"
                elif action == "command":
                    if payload.get("device") != "sw1" or not isinstance(payload.get("line"), str):
                        raise LabError("Only sw1 simulated CLI commands are accepted")
                    result = lab.cli.execute(payload["line"])
                    lab._event(f"CLI input: {payload['line'][:160]}")
                elif action == "ip":
                    lab.configure_ip(payload.get("port"), payload.get("cidr"))
                    result = "Simulated address updated"
                elif action == "assess":
                    result = lab.assess()
                    persist = False
                elif action == "reset":
                    self.provider.create_lab()
                    result = "Lab reset; checkpoints retained"
                    persist = False
                elif action == "checkpoint":
                    checkpoint_id = self.provider.save_checkpoint()
                    result = {"checkpoint_id": checkpoint_id, "message": "Simulated lab checkpoint saved to SQLite"}
                    persist = False
                elif action == "restore":
                    self.provider.restore_checkpoint(payload.get("checkpoint_id"))
                    result = "Simulated lab checkpoint restored"
                    persist = False
                elif action == "delete_checkpoint":
                    self.provider.delete_checkpoint(payload.get("checkpoint_id"))
                    result = "Checkpoint deleted"
                    persist = False
                else:
                    raise LabError("Unsupported action")
                if persist:
                    self.provider.persist()
                return 200, {"result": result, "state": self.provider.read_device_state()}
            except (LabError, UnsupportedOperation, TypeError, ValueError) as exc:
                return 400, {"error": str(exc), "state": self.provider.read_device_state()}
            except sqlite3.DatabaseError:
                # Rollback is performed by the SQLite transaction context. Do not claim a save succeeded.
                if self.store:
                    self.provider.lab = self.store.load_active()
                return 500, {"error": "SQLite storage failure; action not confirmed"}


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, obj):
            data = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            status, obj = app.handle("GET", self.path, self.headers.get("X-NetForge-Token", ""))
            self.respond(status, obj)

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if length < 0 or length > 4096:
                    self.respond(413, {"error": "Invalid request size"})
                    return
                data = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                self.respond(400, {"error": "Malformed JSON"})
                return
            status, obj = app.handle("POST", self.path, self.headers.get("X-NetForge-Token", ""), data)
            self.respond(status, obj)

    return Handler


def main():
    parser = argparse.ArgumentParser(description="NetForge local simulation bridge")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", type=Path, default=Path.home() / ".netforge-3d" / "labs.sqlite3",
                        help="SQLite lab path (default: ~/.netforge-3d/labs.sqlite3)")
    parser.add_argument("--ephemeral", action="store_true", help="Disable SQLite; session data will be lost on exit")
    args = parser.parse_args()
    token = os.environ.get("NETFORGE_TOKEN") or secrets.token_urlsafe(24)
    app = App(token, None if args.ephemeral else args.db)
    print(f"NetForge local session token: {token}\nListening on 127.0.0.1:{args.port}\n"
          f"Storage: {'in-memory only' if args.ephemeral else args.db}", flush=True)
    try:
        ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(app)).serve_forever()
    finally:
        app.close()


if __name__ == "__main__":
    main()
