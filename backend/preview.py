"""Disposable browser preview of the SAME simulated core, not a Godot/web export.

Public preview has no OS command adapter, persistence, real tools or credentials.
Only its allowlisted Lab actions are reachable. Do not deploy as a production service.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets

from backend.server import App

STATIC = Path(__file__).resolve().parent.parent / "web_preview"
FILES = {"/": ("index.html", "text/html; charset=utf-8"),
         "/style.css": ("style.css", "text/css; charset=utf-8"),
         "/app.js": ("app.js", "text/javascript; charset=utf-8")}
# Explicitly no checkpoints: this preview is ephemeral, shared and disposable.
ACTIONS = frozenset({"connect", "disconnect", "ping", "command", "assess", "reset"})


def handler_for(app: App):
    class PreviewHandler(BaseHTTPRequestHandler):
        def respond(self, status: int, data: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def do_HEAD(self) -> None:
            self.do_GET()

        def reply(self, status: int, data: dict) -> None:
            self.respond(status, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self) -> None:
            if self.path in FILES:
                filename, mime = FILES[self.path]
                self.respond(200, (STATIC / filename).read_bytes(), mime)
            elif self.path == "/api/state":
                status, result = app.handle("GET", "/state", app.token)
                self.reply(status, result)
            elif self.path == "/api/missions":
                status, result = app.handle("GET", "/missions", app.token)
                self.reply(status, result)
            else:
                self.reply(404, {"error": "Unknown path"})

        def do_POST(self) -> None:
            if self.path != "/api/action":
                self.reply(404, {"error": "Unknown path"})
                return
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json" or self.headers.get("X-NetForge-Preview") != "1":
                self.reply(403, {"error": "Same-origin JSON preview request required"})
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if length < 0 or length > 2048:
                    self.reply(413, {"error": "Request too large"})
                    return
                payload = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                self.reply(400, {"error": "Invalid JSON"})
                return
            if (not isinstance(payload, dict) or not isinstance(payload.get("action"), str)
                    or payload["action"] not in ACTIONS):
                self.reply(400, {"error": "Unsupported simulated action"})
                return
            status, result = app.handle("POST", "/action", app.token, payload)
            if status == 200 and payload["action"] == "reset":
                result["result"] = "Lab reset (browser preview is ephemeral; no checkpoints)"
            self.reply(status, result)

        def log_message(self, format: str, *args) -> None:
            # Do not print arbitrary user commands into the server's access logs.
            pass

    return PreviewHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="NetForge simulated lab browser preview (not Godot)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app = App(secrets.token_urlsafe(24))  # in-memory only, internal to server
    server = ThreadingHTTPServer(("0.0.0.0", args.port), handler_for(app))
    print(f"SIMULATED browser companion listening on 0.0.0.0:{args.port}; no real lab tools or persistent data", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
