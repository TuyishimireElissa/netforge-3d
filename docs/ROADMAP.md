# Development roadmap / structured backlog
Each row has an acceptance gate. Priority P0 now, P1 next, P2 later. No phase is a promise of complete standards coverage.

| Phase | Priority | Deliverables | Exit gate / current state |
|---|---|---|---|
| 0 foundation | P0 | inventories, unique IDs, architecture, risk, test plan, source/licensing review | Major domains recorded; initial docs specified |
| 1 playable lab | P0 | Godot school room, first-person, equipment inspection, shared cable state, CLI | Project and scripted headless mission smoke authored; local engine BLOCKED; Windows workflow run pending |
| 2 networking core | P0 | two hosts/switch, L2 learning, basic ARP/ICMP, traces | Implemented + Python unit tested; limited model |
| 3 switch/mission | P0 | CLI modes, VLAN access isolation, sticky MAC, evidence-based assess/reset | Python tests now cover JSON-driven weighted assessment, CLI and reset; GUI verification blocked |
| 4 routing/services | P1 | router/static/default routes, DHCP/DNS, firewall, mission C/D | Route/firewall/address negative tests; planned |
| 5 real lab provider | P1 | namespace/veth/bridge isolated lab, scoped ping/tcpdump/ss, safe teardown | Runtime capability, no-egress verification, timeout/audit and real-output tests; blocked here |
| 6 detection/IR | P1 | normalized telemetry, safe alert mission, evidence report | Scenario F/H, reproducible alert, report tests; planned |
| 7 protocol breadth | P2 | IPv6, L2 loops/STP/LACP, wireless, VPN, QoS, cloud/identity | protocol-by-protocol fidelity tests; planned |
| 8 emulation | P2 | licensed images, QEMU/GNS3/containerlab adapters | license and emulator evidence + isolation; planned |
| 9 campaign breadth | P2 | scenarios C-H, app fixes, forensics and industry content | per-mission evidence/rubric/reset tests; planned |
| 10 distribution | P1 | migration/checkpoint, diagnostics, accessibility/settings, CI, performance and Windows packaging | SQLite v1/checkpoint and automated verification entry point added; installer and measured GUI smoke still planned |

**Completed unblocked slice:** bundled mission JSON drives validated weighted outcome criteria and prerequisite checks; SQLite v1 persists the local simulated lab and explicit checkpoints, tested across restart/reset/restore and rollback. **Next complete slice:** run the pinned Windows CI workflow on this branch and fix actual Godot import/startup/headless integration failures; then perform full graphical mouse/rendering smoke on a supported machine. If hosted engine acquisition is blocked, record exact CI blocker and continue with independently tested routing/static-route Mission C without GUI claims. Security tools stay disabled until isolated provider gates are met.

Cross-cutting task queues: networking topics in `NETWORKING_CATALOG.md`, cybersecurity in `CYBERSECURITY_CATALOG.md`, hardware in `EQUIPMENT_CATALOG.md`, tools in `TOOLS_CATALOG.md`, environments in `MASTER_SPEC.md`, persistence in `DATA_MODEL.md`, controls in `SECURITY_MODEL.md`, tests in `TEST_PLAN.md`. These are backlog items, not claims of implementations.
