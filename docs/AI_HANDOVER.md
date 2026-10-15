# AI handover — 2026-10-15

Read PROJECT_STATUS.md, ARCHITECTURE.md, KNOWN_LIMITATIONS.md and DEVELOPMENT_SETUP.md first. Work only on session branch `arena/748721bb-netforge-3d`. Never overwrite owner changes.

## Recovery
Initial checkout `b972ceb` was README-only and clean. `git ls-remote` / `gh pr list` found existing implementation in open PR #1, head `1929402`. Fetched its branch and fast-forwarded this session branch; PR #1 itself was NOT merged or closed. Commit `1df3623` was absent from available history. Do not start over or treat missing files on main as proof the project does not exist.

## Changes this session
- `simulation/core.py`: normalize undirected cable connections to endpoint-first order.
- `database/store.py`: normalize valid legacy reversed cables on load; reject duplicate/invalid links. Keep SQLite schema v1 and user data intact.
- `backend/server.py`: reject invalid configured tokens and return 401 for non-ASCII request tokens (previously compare_digest raised TypeError).
- Five new regression tests in test_persistence.py/test_http.py, plus status/architecture/test/setup notes.

## Evidence
Before edits, reproduced API connect 200 followed by restart `PersistenceError: Stored links do not match built-in topology`; also reproduced non-ASCII token TypeError. Baseline 33 tests passed. After fixes, `python3 -m tools.verify` passed 38 tests and every non-engine stage; `git diff --check` passed. Strict `--download-godot --require-godot` failed with TLS EOF; no local engine executable exists. Logs/report under ignored artifacts/verification. Existing PR #1 had successful hosted checks; that is NOT evidence for the new revision. Windows hosted import is explicitly blocked in its special policy, not passed. Never claim GUI verification.

## Next task
Inspect hosted CI for this session branch/revision after push and address any new failures. Then review stalled HTTP request/resource behavior with socket regression tests. Improve Godot checkpoint selection/deletion and rubric feedback next; preserve backend authority. A rendered Windows smoke is still needed, with exact instructions in DEVELOPMENT_SETUP.md. Real tools/providers, routing, profiles and VM snapshots remain unimplemented. Keep all cybersecurity actions simulated and local-only.

## Hosted verification completed
Code commit `2a11f7c` was pushed on the session branch. [Actions run 38772833150](https://github.com/TuyishimireElissa/netforge-3d/actions/runs/38772833150) completed successfully for Linux strict headless and Windows jobs. Windows check annotation explicitly confirms editor import remains BLOCKED (exit 1 without diagnostic); the independent startup/integration gates succeeded under the existing policy. Job conclusions, steps and annotation were read via GitHub API. Full log download failed because the redirected Actions log host was inaccessible, so artifacts were not inspected locally. No GUI verification. No PR created/merged; existing PR #1 remains unchanged. Next autonomous task: bounded stalled-request handling and HTTP resource tests.
