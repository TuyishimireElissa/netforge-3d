# Project status — 2026-10-15

## Recovery and verified baseline
- Session branch: `arena/748721bb-netforge-3d`. Initial checkout `b972ceb` contained only README; working tree was clean.
- Recovered existing implementation by fast-forwarding this branch to `1929402` from open PR #1 (`arena/2f68430a-netforge-3d`). No branch switch, PR merge/closure, or rewrite. Historical commit `1df3623` is not in the fetched history; its exact identity remains unverified.
- Stack: Python >=3.11, standard library HTTP and SQLite; Godot 4 project, CI pinned to 4.2.2. No Python runtime dependencies.
- Architecture: desktop Godot scene -> token-protected loopback HTTP -> serialized App actions -> built-in Python simulation -> normalized SQLite v1. Console uses the same simulation without persistence. See ARCHITECTURE.md.
- Implemented in source and exercised by tests: two-host/access-switch cable repair, limited vendor-inspired CLI, modeled same-subnet ARP/ICMP, VLAN isolation and port-security, allowlisted JSON weighted missions A/B, active-state persistence and up to 20 checkpoints with reset/restore/delete.
- Baseline `python3 -m tools.verify --download-godot --require-godot`: 33 Python tests passed, AST/compile/whitespace/schema/manifest/static Godot config passed. Strict verifier exits nonzero because official download failed (TLS EOF) and local Godot import/startup/integration are BLOCKED. Logs under ignored `artifacts/verification/`.
- GitHub PR #1 check results inspected at `1929402`: Linux and Windows jobs successful. Existing documentation records Windows editor import as BLOCKED despite successful separate startup/integration gates. Hosted checks are not local GUI verification.

## Confirmed gaps / current work
- Fixed reproduced switch-first cable restart failure: model canonicalizes endpoint order; loader accepts and normalizes valid older v1 saves without a schema migration, while rejecting invalid topology. Three new tests cover restart/checkpoints, legacy rows and invalid links.
- Graphical selection, rendering, resizing and Windows 10 performance unverified. Router is visual-only; no routing, real tools, virtual machines, profiles or multi-user system. See KNOWN_LIMITATIONS.md.
- Fixed reproduced non-ASCII token crash: invalid request tokens now return 401; configured session tokens must be non-empty ASCII strings. Two new tests cover real GET/POST requests, unchanged state and configuration errors. Stalled requests/resource limits still need review; no remote service capability is claimed.

## Next five priorities
1. Inspect hosted checks for this session revision; resolve new engine regressions if any.
2. Harden stalled-request/resource handling with real HTTP regression tests.
3. Verify rendered Windows cable/CLI/mission/checkpoint flow; investigate Windows headless editor import separately.
4. Expose checkpoint selection/deletion and criterion-level mission feedback in Godot, with headless tests.
5. Add tested router/static-route simulation incrementally before adding Mission C.

## Owner-only actions
No credentials or authorization needed for local code/test work. A Windows GUI smoke is still required: use the precise steps in DEVELOPMENT_SETUP.md (Godot 4.2.2, `game/project.godot`). Do not expose the loopback bridge or grant public inbound firewall access. No PR has been merged.

## Milestone verification after fixes
`python3 -m tools.verify` passed **38 tests** and all Python syntax/compile, mission schema, manifest, whitespace and static Godot checks. Three local engine stages remain BLOCKED (no executable). `git diff --check` passed. Strict download attempt earlier failed with TLS EOF; it is not a passing engine check. New tests use actual SQLite files and loopback HTTP, not a mock persistence layer. See AI_HANDOVER.md for continuation.
