# Development readiness checklist (2026-10-16)

This is a **prioritized implementation queue**, not a claim that the full roadmap is finished. The complete long-term inventories remain in `ROADMAP.md`, `MASTER_SPEC.md`, and the networking, cybersecurity, equipment and tools catalogues. “Automated” does not mean “graphically verified.”

## P0 — integrated simulated learning core
- [x] Deterministic two-host/switch lab, cable repair, simplified ARP/ICMP, VLAN and sticky MAC, CLI modes. Python suite + hosted headless Godot integration at published `1929402`.
- [x] Versioned mission A/B JSON, prerequisites, weighted evidence and state-driven assessment. Schema/mission tests + HTTP/scene integration.
- [x] Loopback token-protected desktop bridge; SQLite active lab and bounded checkpoint save/restart/restore/delete. Python socket/file tests + hosted headless scene integration (delete UI still pending).
- [x] Headless integrated scene flow: responsive HUD, mission criterion feedback, PC address control, checkpoint lifecycle, reset confirmation and clear recovery instructions are implemented in source and grammar-parsed. Hosted Linux/Windows scene and mission integration passed on commit `9dd8ce1`; graphical legibility and pointer interaction remain open.
- [x] Re-ran exact-revision pinned Godot 4.2.2 hosted CI: [push run 38925703927](https://github.com/TuyishimireElissa/netforge-3d/actions/runs/38925703927) and [PR run 38925711385](https://github.com/TuyishimireElissa/netforge-3d/actions/runs/38925711385) succeeded on `9dd8ce1`. Linux strict editor import/startup/integration passed; Windows startup/integration passed but **editor import is still BLOCKED** (exit 1/no diagnostic, warning). Not a GUI test.
- [ ] Real graphical desktop acceptance on supported hardware, only after code/readiness handover; do not ask the user to launch during development.

## P1 — important reliability and distribution
- [ ] Malformed input and crash-resistance checks for both browser companion and desktop API; browser non-string actions and rejected-ping evidence are covered, but broader API fuzz/limits and corrupt-state recovery remain.
- [ ] Reproducible Windows/Linux startup scripts, installation and data-backup guidance; Bash wrappers and installed wheel have been tested, PowerShell wrappers remain unexecuted here.
- [ ] Persisted learner profiles/progress history, migrations beyond SQLite v1, backups and corruption handling. A checkpoint is **not** an OS/VM snapshot.
- [ ] Accessibility/input remapping, responsive scaling, settings and low-resource performance measurement (Windows 10 / 8 GB remains unmeasured).
- [ ] Routing/services, DHCP/DNS/firewall and Mission C onward, with new fidelity registers and tests before claiming support. Router currently **visual only**.
- [ ] Packaged Godot desktop export/installer; wheel contains the backend and simulated browser assets but **not** Godot game files. Export is blocked without a compatible engine in this sandbox.

## P2 — optional breadth / requires external systems
- [ ] Wider protocol/equipment/environment catalogue, advanced missions, topology editor, animated frames and reports — see `ROADMAP.md` and domain catalogues for full scope.
- [ ] Real isolated networking/cyber range, device emulation, licensed images, cloud services, multiplayer, VM snapshots, PCAP and real tools: **not implemented**. Require explicit authorization, egress isolation, licensing, resource budgets and target-scoped tests before enabling anything. Never substitute synthetic traces for evidence of real traffic.

## Evidence and Git state
- The sandbox originally opened `arena/2f68430a-netforge-3d` at grafted local base `b972ceb` with files untracked while the remote PR #1 pointed to `1929402`. We preserved the files, fetched remote history, committed the work locally as `1484ade`, then merged the remote branch history on **the same fixed branch** without reset, force push or changing any resulting source content. The resulting branch is a fast-forward descendant of prior remote and was pushed with explicit authorization. PR #1 is open; no merge. Use `git log -1` for current hash; the hosted `9dd8ce1` run validates source before this documentation update.
- `python -m tools.verify --report-dir artifacts/verification-final` locally: 38 Python tests/config/mission/static checks passed; all three local Godot engine stages BLOCKED (no Godot binary). The hosted exact-revision runs above passed with the documented Windows import BLOCKED warning.
- Readiness handover must give actual new test results, remaining graphical checks, precise Godot 4.2.2/Python 3.11+ launch procedure and the true local vs remote revision. No real GUI launch has been requested of the user.
