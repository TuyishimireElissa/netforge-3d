# Development readiness checklist (2026-10-16)

This is a **prioritized implementation queue**, not a claim that the full roadmap is finished. The complete long-term inventories remain in `ROADMAP.md`, `MASTER_SPEC.md`, and the networking, cybersecurity, equipment and tools catalogues. “Automated” does not mean “graphically verified.”

## P0 — integrated simulated learning core
- [x] Deterministic two-host/switch lab, cable repair, simplified ARP/ICMP, VLAN and sticky MAC, CLI modes. Python suite + hosted headless Godot integration at published `1929402`.
- [x] Versioned mission A/B JSON, prerequisites, weighted evidence and state-driven assessment. Schema/mission tests + HTTP/scene integration.
- [x] Loopback token-protected desktop bridge; SQLite active lab and bounded checkpoint save/restart/restore/delete. Python socket/file tests + hosted headless scene integration (delete UI still pending).
- [ ] First-person scene usability: responsive HUD, mission criterion feedback, PC address control, checkpoint lifecycle and clear recovery instructions are implemented in source and grammar-parsed. **Not checked off** until this revision runs in a suitable Godot engine; graphical legibility and pointer interaction remain open.
- [ ] Re-run Windows/Linux headless editor/startup/integration checks against **this exact revision** in hosted CI (not the prior published revision). Sandbox lacks the executable; no results should be inferred from old checks.
- [ ] Real graphical desktop acceptance on supported hardware, only after code/readiness handover; do not ask the user to launch during development.

## P1 — important reliability and distribution
- [ ] Malformed input and crash-resistance checks for both browser companion and desktop API; browser non-string actions and rejected-ping evidence are covered, but broader API fuzz/limits and corrupt-state recovery remain.
- [ ] Reproducible Windows/Linux startup scripts, installation and data-backup guidance; Bash wrappers and installed wheel have been tested, PowerShell wrappers remain unexecuted here.
- [ ] Persisted learner profiles/progress history, migrations beyond SQLite v1, backups and corruption handling. A checkpoint is **not** an OS/VM snapshot.
- [ ] Accessibility/input remapping, responsive scaling, settings and low-resource performance measurement (Windows 10 / 8 GB remains unmeasured).
- [ ] Routing/services, DHCP/DNS/firewall and Mission C onward, with new fidelity registers and tests before claiming support. Router currently **visual only**.
- [ ] Packaged Godot desktop export/installer; wheel currently contains backend only. Export is blocked without a compatible engine in this sandbox.

## P2 — optional breadth / requires external systems
- [ ] Wider protocol/equipment/environment catalogue, advanced missions, topology editor, animated frames and reports — see `ROADMAP.md` and domain catalogues for full scope.
- [ ] Real isolated networking/cyber range, device emulation, licensed images, cloud services, multiplayer, VM snapshots, PCAP and real tools: **not implemented**. Require explicit authorization, egress isolation, licensing, resource budgets and target-scoped tests before enabling anything. Never substitute synthetic traces for evidence of real traffic.

## Evidence and Git state
- Current sandbox checkout is `arena/2f68430a-netforge-3d` at local `b972ceb` (grafted shallow base), with modified README and project files untracked. The remote branch/PR #1 instead points at published `1929402aea19de1b53fb1e4e5e85f52fa8230737`. Preserve both histories; **do not reset, force-push or interpret old CI as validation of new files**. New work here is not automatically published.
- `python -m tools.verify --report-dir artifacts/verification-current` before this pass: Python/config/mission checks passed; all three local Godot engine stages BLOCKED (no Godot binary). Previously published PR checks were successful with the documented Windows import BLOCKED warning.
- Readiness handover must give actual new test results, remaining graphical checks, precise Godot 4.2.2/Python 3.11+ launch procedure and the true local vs remote revision. No real GUI launch has been requested of the user.
