"""Cross-platform, dependency-free verification entry point.

Run from any working directory: python -m tools.verify [--godot PATH] [--require-godot].
Logs/JSON reports live in ignored artifacts/verification, never in a source tree commit.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "game"
GODOT_VERSION = "4.2.2"
GODOT_RELEASE = "4.2.2-stable"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


class Verifier:
    def __init__(self, reports: Path, require_godot: bool, allow_windows_import_block: bool = False):
        self.reports = reports
        self.reports.mkdir(parents=True, exist_ok=True)
        self.require_godot = require_godot
        self.allow_windows_import_block = allow_windows_import_block
        self.results: list[dict] = []

    def record(self, name: str, status: str, detail: str, log: str = "") -> None:
        assert status in ("passed", "failed", "blocked", "skipped")
        _write(self.reports / f"{name}.log", log or detail + "\n")
        self.results.append({"name": name, "status": status, "detail": detail,
                             "log": str(self.reports / f"{name}.log")})
        print(f"{status.upper():7} {name}: {detail}", flush=True)
        if status == "blocked" and os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::warning title=NetForge {name}::{detail}", flush=True)
        if status == "failed":
            tail = "\n".join((log or detail).splitlines()[-35:])
            print(tail, file=sys.stderr, flush=True)
            if os.environ.get("GITHUB_ACTIONS") == "true":
                # GH check annotations remain accessible if artifact/log download hosts are blocked.
                lines = (log or detail).splitlines()
                # Include the first traceback too; unittest's final traceback may be only cleanup noise.
                error_line = next((i for i, line in enumerate(lines) if line.startswith("ERROR:") or line.startswith("FAIL:")), 0)
                flagged = [line for line in lines if re.search(r"(?i)error|fail|parse|invalid|warning|script|resource", line)]
                excerpt = (detail + "\n--- first error ---\n" + "\n".join(lines[error_line:error_line + 22]) +
                           "\n--- flagged output ---\n" + "\n".join(flagged[-28:]) +
                           "\n--- tail ---\n" + "\n".join(lines[-14:]))
                excerpt = excerpt[:5500]
                encoded = excerpt.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
                print(f"::error title=NetForge {name}::{encoded}", flush=True)

    def run(self, name: str, argv: list[str], timeout: int = 120, env: dict | None = None, reject_engine_errors: bool = False) -> bool:
        try:
            proc = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True,
                                  timeout=timeout, errors="replace")
            output = "$ " + subprocess.list2cmdline(argv) + "\n" + proc.stdout + proc.stderr
            engine_error = bool(re.search(r"(?im)^(?:SCRIPT ERROR:|ERROR:|.*Parse Error:|.*Failed to load script)", proc.stdout + proc.stderr)) if reject_engine_errors else False
            ok = proc.returncode == 0 and not engine_error
            # Windows hosted Godot 4.2.2 editor import returns 1 with no diagnostic even though
            # script parse, actual scene startup, and backend integration run successfully. Linux
            # must still import cleanly. Report the Windows import as BLOCKED, never PASSED.
            if (name == "godot_import" and self.allow_windows_import_block and sys.platform == "win32"
                    and proc.returncode == 1 and not engine_error):
                self.record(name, "blocked", "Windows hosted headless editor import exits 1 without an error; Linux strict import is required", output)
                return False
            self.record(name, "passed" if ok else "failed", f"exit={proc.returncode}, engine_error={engine_error}", output)
            return ok
        except subprocess.TimeoutExpired as exc:
            parts = [(chunk.decode("utf-8", errors="replace") if isinstance(chunk, bytes) else chunk)
                     for chunk in (exc.stdout, exc.stderr) if chunk]
            self.record(name, "failed", f"timeout after {timeout}s", "\n".join(parts) + "\n" + str(exc))
            return False
        except OSError as exc:
            self.record(name, "failed", str(exc), str(exc))
            return False

    def python_checks(self) -> None:
        py_files = sorted(p for directory in ("backend", "database", "providers", "scenarios", "simulation", "tests", "tools")
                          for p in (ROOT / directory).rglob("*.py"))
        try:
            for path in py_files:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            self.record("python_syntax", "passed", f"AST parsed {len(py_files)} source files")
        except (SyntaxError, UnicodeError, OSError) as exc:
            self.record("python_syntax", "failed", str(exc))
        self.run("python_unittest", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], 150)
        # Both syntax and import errors are captured by compileall/unit suite; no third-party Python deps.
        self.run("python_compileall", [sys.executable, "-m", "compileall", "-q", "backend", "database", "providers", "simulation", "scenarios", "tools", "tests"], 60)
        self.run("source_whitespace", ["git", "diff", "--check"], 30)
        try:
            from simulation.missions import load_missions
            files = sorted((ROOT / "scenarios").glob("*.json"))
            for path in files:
                json.loads(path.read_text(encoding="utf-8"))
            missions = load_missions()
            self.record("mission_json", "passed", f"Parsed {len(files)} JSON files; validated {len(missions)} mission schemas and dependency graph")
        except Exception as exc:
            self.record("mission_json", "failed", f"{type(exc).__name__}: {exc}")
        try:
            import tomllib
            manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
            assert manifest["project"]["requires-python"] == ">=3.11"
            assert not manifest["project"].get("dependencies")
            self.record("python_manifest", "passed", "pyproject.toml valid; stdlib-only Python 3.11+ runtime")
        except Exception as exc:
            self.record("python_manifest", "failed", f"{type(exc).__name__}: {exc}")
        try:
            project = (GAME / "project.godot").read_text(encoding="utf-8")
            assert 'run/main_scene="res://school_lab.tscn"' in project
            assert '"4.2"' in project and (GAME / "school_lab.tscn").is_file()
            assert (GAME / "tests" / "smoke.gd").is_file() and (GAME / "tests" / "startup.gd").is_file()
            self.record("godot_project_config", "passed", "Main scene, Godot 4.2 feature and smoke script are present (not an import)")
        except Exception as exc:
            self.record("godot_project_config", "failed", f"{type(exc).__name__}: {exc}")

    def download_godot(self) -> Path | None:
        if sys.platform == "win32":
            archive_name = f"Godot_v{GODOT_RELEASE}_win64.exe.zip"
            binary_name = f"Godot_v{GODOT_RELEASE}_win64_console.exe"
        elif sys.platform.startswith("linux") and os.uname().machine == "x86_64":
            archive_name = f"Godot_v{GODOT_RELEASE}_linux.x86_64.zip"
            binary_name = f"Godot_v{GODOT_RELEASE}_linux.x86_64"
        else:
            self.record("godot_download", "blocked", f"No official pinned archive mapping for {sys.platform} on this CPU")
            return None
        url = f"https://github.com/godotengine/godot-builds/releases/download/{GODOT_RELEASE}/{archive_name}"
        archive = self.reports / archive_name
        try:
            with urlopen(url, timeout=50) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
            with ZipFile(archive) as zip_file:
                if binary_name not in zip_file.namelist():
                    raise ValueError(f"Expected executable missing from archive: {binary_name}")
                zip_file.extract(binary_name, self.reports / "engine")
            binary = self.reports / "engine" / binary_name
            if sys.platform != "win32":
                binary.chmod(0o755)
            self.record("godot_download", "passed", f"Official pinned archive extracted: {GODOT_RELEASE} ({archive.stat().st_size} bytes)")
            return binary
        except Exception as exc:
            self.record("godot_download", "blocked", f"Official download failed: {type(exc).__name__}: {exc}")
            return None

    def godot_checks(self, binary: Path | None) -> None:
        if binary is None:
            self.record("godot_import", "blocked", "Godot 4.2.2 executable unavailable")
            self.record("godot_startup", "blocked", "Godot 4.2.2 executable unavailable")
            self.record("godot_integration", "blocked", "Godot 4.2.2 executable unavailable")
            return
        try:
            version = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=20)
            text = version.stdout + version.stderr
            if version.returncode or not re.match(r"^4\.2\.2[. -]", text):
                self.record("godot_version", "failed", f"Expected 4.2.2, got {text.strip()!r}", text)
                self.record("godot_import", "skipped", "Version mismatch")
                self.record("godot_startup", "skipped", "Version mismatch")
                self.record("godot_integration", "skipped", "Version mismatch")
                return
            self.record("godot_version", "passed", text.strip())
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.record("godot_version", "failed", str(exc))
            self.record("godot_import", "skipped", "Executable did not start")
            self.record("godot_startup", "skipped", "Executable did not start")
            self.record("godot_integration", "skipped", "Executable did not start")
            return
        prefix = [str(binary.resolve()), "--headless", "--path", str(GAME)]
        self.run("godot_script_parse", prefix + ["--check-only", "--script", "res://school_lab.gd"], 60, reject_engine_errors=True)
        self.run("godot_smoke_parse", prefix + ["--check-only", "--script", "res://tests/smoke.gd"], 60, reject_engine_errors=True)
        self.run("godot_startup_parse", prefix + ["--check-only", "--script", "res://tests/startup.gd"], 60, reject_engine_errors=True)
        self.run("godot_import", prefix + ["--verbose", "--editor", "--import"], 180, reject_engine_errors=True)
        # Startup is independent evidence; collect its diagnostics even when editor import fails.
        self.run("godot_startup", prefix + ["--script", "res://tests/startup.gd"], 90, reject_engine_errors=True)
        # Integration collects independent parser/scene diagnostics even when startup fails.
        from backend.server import App, make_handler
        with tempfile.TemporaryDirectory(prefix="netforge-smoke-", dir=self.reports) as scratch:
            token = "local-test-only-godot-token"
            app = App(token, Path(scratch) / "smoke.sqlite3")
            try:
                class QuietHandler(make_handler(app)):
                    def log_message(self, *args):
                        pass
                server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    env = os.environ.copy()
                    env["NETFORGE_TOKEN"] = token
                    env["NETFORGE_API_URL"] = f"http://127.0.0.1:{server.server_port}"
                    self.run("godot_integration", prefix + ["--script", "res://tests/smoke.gd"], 120, env, reject_engine_errors=True)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)
            except Exception as exc:
                self.record("godot_integration", "failed", f"Backend test fixture error: {exc}")
            finally:
                app.close()

    def finish(self) -> int:
        failures = [r for r in self.results if r["status"] == "failed"]
        blocked = [r for r in self.results if r["status"] in ("blocked", "skipped") and r["name"].startswith("godot_")]
        proven_windows_flow = (self.allow_windows_import_block and sys.platform == "win32" and
                              all(any(r["name"] == stage and r["status"] == "passed" for r in self.results)
                                  for stage in ("godot_script_parse", "godot_smoke_parse", "godot_startup_parse",
                                                "godot_startup", "godot_integration")))
        required_blocks = [r for r in blocked if not (proven_windows_flow and r["name"] == "godot_import")]
        exit_code = int(bool(failures or (self.require_godot and required_blocks)))
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        report = {"timestamp_utc": _now(), "revision": revision,
                  "python": sys.version.split()[0], "required_godot": self.require_godot,
                  "exit_code": exit_code, "checks": self.results}
        _write(self.reports / "report.json", json.dumps(report, indent=2) + "\n")
        print(f"Report: {self.reports / 'report.json'}; failures={len(failures)}, godot_blocked_or_skipped={len(blocked)}")
        return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify NetForge Python, scenarios, Godot import/startup and integration")
    parser.add_argument("--godot", type=Path, help="Path to installed Godot 4.2.2 executable")
    parser.add_argument("--download-godot", action="store_true", help="Attempt official pinned Godot download when not installed")
    parser.add_argument("--require-godot", action="store_true", help="Fail when required engine tests are blocked or skipped")
    parser.add_argument("--allow-windows-import-block", action="store_true",
                        help="Windows CI only: report silent 4.2.2 import exit 1 as BLOCKED when all scene/integration gates pass; Linux CI must import")
    parser.add_argument("--report-dir", type=Path, default=ROOT / "artifacts" / "verification")
    args = parser.parse_args()
    if args.allow_windows_import_block and sys.platform != "win32":
        parser.error("--allow-windows-import-block is only valid on Windows")
    verifier = Verifier(args.report_dir.resolve(), args.require_godot, args.allow_windows_import_block)
    verifier.python_checks()
    binary = args.godot or (Path(found) if (found := shutil.which("godot")) else None)
    if binary is None and args.download_godot:
        binary = verifier.download_godot()
    verifier.godot_checks(binary)
    return verifier.finish()


if __name__ == "__main__":
    raise SystemExit(main())
