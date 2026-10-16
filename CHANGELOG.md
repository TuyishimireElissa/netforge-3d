# Changelog

## Unreleased — verification automation (2026-10-15)
- Added cross-platform report/log-generating verifier, pinned Godot 4.2.2 download attempt, strict engine gates and Windows GitHub Actions workflow.
- Authored headless Godot lab mission integration smoke; hosted run 38756303805 passed Linux import/startup/mission and Windows startup/mission. Windows headless editor import remains explicitly BLOCKED.
- Fixed cross-platform SQLite test fixture connections, used Godot Windows console binary, preserved collider/state checks under the headless dummy renderer, and retained structured GitHub failure annotations.
- Rejected duplicate mission JSON fields, invalidated stale ping evidence when modeled path changes, and added verifier/mission regression tests.

## Persistence and mission follow-up (2026-10-15)
- Bundled versioned mission JSON now validates all fields, restricts criterion IDs and evaluates weighted evidence/prerequisites without expression execution.
- Local bridge defaults to normalized SQLite v1 with transactional active state, CLI/config/trace persistence, bounded checkpoints, reset/restore/delete and `/missions` metadata; console stays ephemeral.
- Added migration, rollback, restart, checkpoint, schema and negative tests; Godot checkpoint buttons remain unverified without Godot executable.

## First foundation milestone (2026-10-15)
- Added Python standard-library simulation with two hosts, switch, repair cable, L2 learning/VLAN checks, simplified ARP/ICMP, switch CLI/port security, outcome assessment and reset.
- Added built-in provider capability boundary, token-protected loopback JSON bridge, headless console, scenario definitions and Godot prototype school lab.
- Added automated simulation/API dispatcher tests, project setup, fidelity registers and full-scope backlog documentation.
- Godot runtime smoke, persistence, real lab isolation and tool integrations remain unverified or unimplemented.

## Browser companion preview (2026-10-15)
- Added an ephemeral, shared browser companion for the simulated Python lab: topology, cable repair, ping, missions, switch CLI and synthetic packet journal. Not a Godot 3D export or a real networking tool.
- Added an allowlisted HTTP preview adapter with no persistent storage, OS command access or exposed desktop session token; documented its deployment limits and added API mission/safety checks.

## Development readiness pass (2026-10-16; local, not yet published)
- Preserved the existing two-mission architecture and added Godot scene controls for simulated PC IPv4 addresses, selected checkpoint restore/delete confirmation, responsive HUD dimensions, weighted evidence and next-step feedback; updated headless integration assertions. New scene behavior remains engine/GUI unverified on this revision.
- Prevented rejected ping requests from erasing prior mission evidence; rejected non-string browser action names; added regression tests.
- Added repeatable PowerShell/Bash bridge and verification wrappers, packaged the browser companion static assets in the Python wheel, tested that installed copy serves the UI, and extended verification to inspect untracked source whitespace and optional GDScript grammar (gdtoolkit 4.2.2).
- Added prioritized readiness checklist, refreshed setup/architecture/limitations/roadmap and documented local versus remote Git history and blocked engine checks.
