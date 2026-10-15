# Architecture and risk register

## Current data flow
`Godot scene -> HTTPRequest JSON on 127.0.0.1:8765 + X-NetForge-Token -> backend.server.App -> BuiltinProvider -> simulation.core.Lab / SwitchCLI`. Response contains authoritative state, modeled trace and rubric; Godot updates the cable and text based on response, never optimistic UI success. `tools.console` calls the same model directly for headless use. Default bridge state and up to 20 explicit simulated checkpoints are persisted in local SQLite v1 (`database/store.py`); `--ephemeral` and `tools.console` remain process-local. Scenario JSON definitions drive weighted rubrics via registered criteria, never eval. Godot input is never interpreted as OS commands. Every action is serialized behind a reentrant lock; HTTP has no CORS headers. Token is printed to console and kept in memory; do not screen-share it.

Endpoints: `GET /state`, `GET /missions`, `POST /action` with action `connect`, `disconnect`, `ping`, `ip`, `command`, `assess`, `reset`, `checkpoint`, `restore`, `delete_checkpoint`. Checkpoint IDs are positive integers returned by the provider; reset keeps checkpoints. Auth is required on both GET endpoints and POST. POST length <= 4096 bytes; CLI <= 160 characters. Other methods/routes are rejected. Bridge is local desktop transport, **not** remote-service-grade auth. No automatic backend startup yet; script expects port 8765 and Godot client to be on same computer. The SQLite store is local and normalized; there is no trace exporter or persistent learner profile. `r1` object is VISUAL ONLY.

## Target boundaries
Godot equipment entity/components and UI -> typed client API -> session/mission service -> simulation engine OR provider capability adapter -> (isolated local/remote range controller, never unrestricted shell). Persistence layer: SQLite v1 transactionally stores one active revision/checkpoint revisions in normalized tables with FKs; further schema migrations, profiles and cross-provider snapshots remain planned. Tool adapters use fixed allowlisted argv, explicit targets/scopes, deadlines and bounded streams, job/audit IDs; container/VM providers enforce egress-denied networks, budgets and cleanup verification. Remote access requires authenticated TLS service, per-user authorization and lab-bound capability tokens; not this loopback bridge.

## Risk register
| ID | Risk | Mitigation / gate | Status |
|---|---|---|---|
| R1 | Local malicious process obtains session token / CSRF-like local access | Loopback and custom header, unguessable token, no CORS; future origin+auth hardening | Residual local trust; do not expose remotely |
| R2 | User mistakes synthetic trace/CLI for actual packets/vendor OS | Label all screens, docs and providers; never export synthetic PCAP | Current labeling; continue audits |
| R3 | Container-based range escapes or reaches host/Internet | No real range yet; VM isolation, deny egress, resource controls and teardown tests required before enabling | BLOCKED |
| R4 | RAM/graphics overload on 8 GB Windows device | Lightweight geometry/GL compatibility, optional advanced provider; benchmark before claims | Not measured |
| R5 | Godot scene syntax/physics incompatibility | Run editor import and scene smoke on Godot 4.2+ Windows/Linux | BLOCKED: binary unavailable here |
| R6 | Saved work lost on restart or DB corruption | Local SQLite v1 and checkpoint round-trip tests; backups, corruption recovery and learner profiles still needed | Partially mitigated for default bridge only |
| R7 | Simplified learning/ping misteaches real behavior | Explicit protocol limits, packet decision tests, curriculum review | Current traces simplified |
| R8 | Ambiguous proprietary NOS/tool redistribution | Never bundle image or invasive tools without rights review | Planned |

## Verification architecture
`tools.verify` drives stdlib Python tests, AST/compileall, mission JSON schema, manifest and Godot project config checks, then Godot 4.2.2 editor import, main-scene startup and an engine-scripted local HTTP/SQLite fixture. Results/logs remain under ignored `artifacts/verification`. Strict mode makes missing/skipped Godot checks fail CI. `.github/workflows/verify.yml` uses a Windows 2022 runner, SHA-pinned official actions, Godot 4.2.2 ZIP plus its SHA512-SUMS.txt and read-only repository permissions; only real workflow execution can validate it. Engine-scripted checks never run OS networking commands or cyber tools.
