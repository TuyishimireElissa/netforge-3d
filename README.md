# NetForge 3D (prototype)

An offline-first **SIMULATED** school networking lab with optional local SQLite persistence. The headless Python simulation models an Ethernet switch, two hosts, a cable repair, same-subnet ARP/ICMP exchange and a limited vendor-inspired switch CLI. A Godot 4 desktop scene provides first-person inspection, virtual cable repair, terminal and mission feedback. **Godot has not been run in this development environment.** No real packet capture, operating-system networking, appliance emulation or isolated attack range is included.

## Quick start

Requires Python 3.11+ (standard library only); optional Godot 4.2+ for the 3D scene.

```sh
python -m tools.verify                 # tests/config checks + report; Godot unavailable is BLOCKED
python -m unittest discover -s tests -v
python -m tools.console                 # fully headless interactive lab
python -m backend.server               # local API + SQLite (~/.netforge-3d/labs.sqlite3); prints token
```

In Godot, import `game/project.godot`, run the project, paste the printed local session token and click **Connect to local simulator**. The bridge runs on `127.0.0.1:8765`; never use it as a remote or Internet-facing service. `--ephemeral` disables SQLite; `--db PATH` selects a local file. The Godot panel can save and restore up to 20 explicit checkpoints. Scenario A/B JSON now drives weighted, evidence-based grading (not actual network tests). On Windows use `py -3 -m ...` if `python` is unavailable. See [development setup](docs/DEVELOPMENT_SETUP.md), [user guide](docs/USER_GUIDE.md) and [limitations](docs/KNOWN_LIMITATIONS.md).

## Structure

- `simulation/`: deterministic model, validated mission rubrics and switch CLI, independent of engine/UI.
- `providers/`: capability declaration and built-in simulated provider; real providers not implemented.
- `backend/`: token-protected loopback JSON bridge (Python standard library).
- `database/`: SQLite v1 migration, normalized state and checkpoints.
- `game/`: Godot 4 scene and modularization starting point.
- `scenarios/`: validated executable rubrics for the first two machine-readable missions.
- `tests/`: Python unit and API dispatcher tests.
- `docs/`: scope, architecture, inventories, fidelity, risks, backlog and setup.
- `tools/`: safe headless manual console; `integrations/`, `database/`, `assets/`: future module boundaries.

**No live previews:** Godot desktop requires installation on the player's computer. The bridge is a local-only service intentionally bound to loopback.

Verification: `python -m tools.verify --download-godot --require-godot` attempts official Godot 4.2.2 and requires its headless import/startup/mission tests; logs and JSON report are in `artifacts/verification/`. GitHub Actions runs the strict suite on a pinned Windows runner. A passing headless test is not a full graphical usability test.
