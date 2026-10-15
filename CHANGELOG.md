# Changelog

## Unreleased — verification automation (2026-10-15)
- Added cross-platform report/log-generating verifier, pinned Godot 4.2.2 download attempt, strict engine gates and Windows GitHub Actions workflow.
- Authored headless Godot lab mission integration smoke; hosted run 38756303805 passed Linux import/startup/mission and Windows startup/mission. Windows headless editor import remains explicitly BLOCKED.
- Fixed cross-platform SQLite test fixture connections, used Godot Windows console binary, preserved collider/state checks under the headless dummy renderer, and retained structured GitHub failure annotations.
- Rejected duplicate mission JSON fields and added verifier regression tests.

## Persistence and mission follow-up (2026-10-15)
- Bundled versioned mission JSON now validates all fields, restricts criterion IDs and evaluates weighted evidence/prerequisites without expression execution.
- Local bridge defaults to normalized SQLite v1 with transactional active state, CLI/config/trace persistence, bounded checkpoints, reset/restore/delete and `/missions` metadata; console stays ephemeral.
- Added migration, rollback, restart, checkpoint, schema and negative tests; Godot checkpoint buttons remain unverified without Godot executable.

## First foundation milestone (2026-10-15)
- Added Python standard-library simulation with two hosts, switch, repair cable, L2 learning/VLAN checks, simplified ARP/ICMP, switch CLI/port security, outcome assessment and reset.
- Added built-in provider capability boundary, token-protected loopback JSON bridge, headless console, scenario definitions and Godot prototype school lab.
- Added automated simulation/API dispatcher tests, project setup, fidelity registers and full-scope backlog documentation.
- Godot runtime smoke, persistence, real lab isolation and tool integrations remain unverified or unimplemented.
