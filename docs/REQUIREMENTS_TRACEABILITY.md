# Requirements traceability register

Reviewed 2026-10-15. Status vocabulary: Planned, Specified, In progress, Implemented, Tested, Verified, Blocked, Deferred. **Tested** means identified tests passed in this environment, not GUI or real-network validation. None of the features is marked Verified yet. Group IDs cover all major domains; split groups into granular protocol/device/tool requirements before implementing them. `—` indicates no evidence/dependency. Complete queues in linked catalogues and roadmap.

| ID | Requirement | Priority | Dependencies | Status | Linked code/docs | Test evidence | Unresolved |
|---|---|---|---|---|---|---|---|
| CORE-001 | Independent deterministic networking core | P0 | — | Tested | simulation/core.py | tests/test_lab.py:LabTests | Only tiny topology |
| CORE-002 | Unique shared equipment/interface IDs in 3D and core | P0 | CORE-001 | In progress | game/school_lab.gd; simulation/core.py | CI run 38756303805 headless equipment IDs and cable sync | Real rendered geometry still not inspected |
| CORE-003 | Configurable working product name | P1 | CORE-001 | In progress | simulation/core.py | — | Godot title static |
| CORE-004 | Fidelity/capability register for each implemented feature | P0 | — | Specified | docs/PROTOCOL_FIDELITY.md; providers/builtin.py | tests/test_lab.py:test_provider_capability_and_unsupported | Need per-feature machine-readable catalogue |
| CORE-005 | Versioned durable SQLite persistence and migrations | P1 | CORE-001 | Tested | database/store.py; docs/DATA_MODEL.md | tests/test_persistence.py: migration, rollback, restart | SQLite v1 local built-in lab only; no v2 upgrade path or profiles |
| CORE-006 | Profiles/progress/checkpoints/reset with durability | P1 | CORE-005 | In progress | database/store.py; providers/builtin.py; backend/server.py | tests/test_persistence.py:test_round_trip_mission_b_restart_reset_restore | Checkpoints/reset durable on bridge; learner profiles and console durability absent |
| CORE-007 | Bounded event history and auditable changes | P1 | CORE-001 | In progress | simulation/core.py; database/store.py | tests/test_persistence.py:test_cli_mode_and_persistence_of_failed_ping | 80 messages bounded; local DB not tamper-resistant or multi-user audit |
| CORE-008 | Desktop loopback JSON bridge token and validation | P0 | CORE-001 | Tested | backend/server.py; tests/test_http.py | tests/test_lab.py:ApiTests; tests/test_http.py | Not remote-grade auth; Godot not tested |
| CORE-009 | Multi-user remote service with TLS and roles | P2 | CORE-005; LAB-003 | Planned | docs/ARCHITECTURE.md | — | Local bridge not suitable |
| CORE-010 | Bounded memory/performance and Windows 8 GB support | P1 | CORE-001; GAME-001 | Specified | docs/MASTER_SPEC.md | — | No benchmarks |
| GAME-001 | Godot 4 school lab scene and first-person controls | P0 | CORE-002 | In progress | game/project.godot; game/school_lab.gd; game/tests/startup.gd | CI run 38756303805: Linux/Windows headless startup | Rendered GUI and Windows 10/8 GB behavior not verified |
| GAME-002 | Crosshair equipment inspection with live status | P0 | GAME-001; CORE-002 | In progress | game/school_lab.gd; game/tests/smoke.gd | CI run 38756303805 headless ray/inspection tests | Real graphical pointer selection not verified |
| GAME-003 | Interactive copper repair mirrored to backend link | P0 | GAME-001; EQUIP-003 | In progress | game/school_lab.gd; game/tests/smoke.gd | CI run 38756303805 headless scene/HTTP/cable-state test | Actual rendered cable appearance not verified |
| GAME-004 | Switch terminal, notifications, mission/rubric UI | P0 | GAME-001; CLI-001 | In progress | game/school_lab.gd; game/tests/smoke.gd | CI run 38756303805 headless CLI/mission/checkpoint script | Visible UI usability not verified |
| GAME-005 | Topology map, animated packet flow, diffs and history | P1 | GAME-001; NET-001 | Planned | docs/MASTER_SPEC.md | — | Only text trace/events |
| GAME-006 | Settings, audio, input remap, accessibility, readable UI | P1 | GAME-001 | Planned | docs/MASTER_SPEC.md | — | Minimal prototype HUD |
| GAME-007 | Data center/NOC/SOC/school/corporate/home/server/range/forensics/wireless/cloud/ISP/industrial environments | P2 | GAME-001 | In progress | docs/MASTER_SPEC.md | — | Only school room authored |
| EQUIP-001 | Endpoint device inventory and model-specific interfaces | P1 | CORE-002 | In progress | docs/EQUIPMENT_CATALOG.md; simulation/core.py | tests/test_lab.py:test_link_repair_arp_icmp_mac_and_assessment | Two PCs only |
| EQUIP-002 | L2/L3 switches, management/console, access/trunk inventory | P1 | CORE-002 | In progress | docs/EQUIPMENT_CATALOG.md | tests/test_lab.py:test_vlan_isolation | Two access ports only |
| EQUIP-003 | Cable types, occupancy, compatibility, patch panels, fiber/transceivers | P1 | CORE-002 | In progress | simulation/core.py; docs/EQUIPMENT_CATALOG.md | tests/test_lab.py:test_invalid_connections_and_media | Only one copper repair link |
| EQUIP-004 | Routers/gateways and redundancy | P2 | CORE-002 | Planned | docs/EQUIPMENT_CATALOG.md | — | No functional models; router visual only |
| EQUIP-005 | Firewall/VPN/IDS/IPS/NAC/monitoring appliances | P2 | CORE-002 | Planned | docs/EQUIPMENT_CATALOG.md | — | No model |
| EQUIP-006 | Wi-Fi AP/controller/client and radio environment | P2 | CORE-002 | Planned | docs/EQUIPMENT_CATALOG.md | — | No model |
| EQUIP-007 | Servers, storage, virtualization, identity, web and databases | P2 | CORE-002 | Planned | docs/EQUIPMENT_CATALOG.md | — | No model |
| EQUIP-008 | Racks, UPS/PDU, cooling and power/environment | P2 | CORE-002 | Planned | docs/EQUIPMENT_CATALOG.md | — | No model |
| EQUIP-009 | ISP/cloud/industrial/forensics equipment | P2 | CORE-002 | Planned | docs/EQUIPMENT_CATALOG.md | — | No model |
| NET-001 | Ethernet access switching MAC learn/flood/forward decisions | P0 | CORE-001 | Tested | simulation/core.py | test_link_repair_arp_icmp_mac_and_assessment | No aging, frames or loops |
| NET-002 | IPv4 CIDR/subnet checks and address conflict handling | P0 | CORE-001 | In progress | simulation/core.py | test_subnet_and_missing_router | Only pairwise duplicate detection |
| NET-003 | Modeled ARP and ICMPv4 echo with failure trace | P0 | NET-001; NET-002 | Tested | simulation/core.py | test_initial_disconnected_and_trace; test_link_repair_arp_icmp_mac_and_assessment | No wire format/cache/timing |
| NET-004 | Access VLAN isolation/assignment | P0 | NET-001 | Tested | simulation/core.py | test_vlan_isolation | No tags/trunks |
| NET-005 | IPv6 address/ND/ICMPv6 and IPv4/v6 fundamentals | P2 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-006 | MAC aging, STP/RSTP, LACP, storm control, speed/duplex/MTU | P2 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-007 | Routing LPM/static/default/inter-VLAN/OSPF/BGP/policy/convergence/HA | P1 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-008 | NAT/PAT, ACL/stateful firewall/zones/DMZ | P1 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-009 | DHCP/v6, DNS, TCP/UDP, HTTP(S)/TLS, SSH, FTP/SFTP | P1 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-010 | SMTP/IMAP/POP3, SMB, LDAP/Kerberos, NTP/SNMP/syslog, SIP, REST/WebSocket/discovery | P2 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-011 | Wireless SSID/association/channel/interference/WPA2/3/802.1X | P2 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-012 | VPN/IPsec/WireGuard, QoS/performance/telemetry | P2 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-013 | vNIC/vSwitch/bridges/namespaces/containers/SDN/overlays/cloud/policies | P2 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| NET-014 | MPLS, ISP, automation and industrial protocols | P2 | CORE-001 | Planned | docs/NETWORKING_CATALOG.md | — | No behavior implemented |
| CLI-001 | Switch mode-specific parser + errors + show commands | P0 | CORE-001 | Tested | simulation/core.py:SwitchCLI | test_cli_modes_negative_cases | Vendor-inspired subset only |
| CLI-002 | Port security max/violation/sticky learn and save | P0 | CLI-001; NET-001 | Tested | simulation/core.py:SwitchCLI; database/store.py | test_security_violation_and_recovery; tests/test_persistence.py:test_round_trip_mission_b_restart_reset_restore | Durable only via SQLite bridge; not vendor-equivalent CLI |
| CLI-003 | Separate endpoint/router/firewall command profiles | P1 | CLI-001; NET-007 | Planned | docs/MASTER_SPEC.md | — | Only switch CLI |
| MISSION-001 | Versioned mission schema, objectives/hints/rubric/evidence | P0 | CORE-001 | Tested | simulation/missions.py; scenarios/mission_a.json; scenarios/mission_b.json | tests/test_missions.py:MissionTests (includes stale-path regression) | Rubric and prerequisites executable; narrative failure/report and topology not automated |
| MISSION-002 | Mission A cable repair + evidence ping + reset | P0 | NET-003; GAME-003 | Tested | simulation/missions.py; scenarios/mission_a.json | tests/test_missions.py:test_bundle_and_weighted_outcome_not_commands; CI 38756303805 headless | Rendered GUI not verified |
| MISSION-003 | Mission B sticky security + saved config + traffic evidence | P0 | CLI-002; MISSION-001 | Tested | simulation/missions.py; scenarios/mission_b.json | tests/test_persistence.py:test_round_trip_mission_b_restart_reset_restore; CI 38756303805 headless | Rendered GUI not verified; vendor CLI not emulated |
| MISSION-004 | Campaign C-H routes/firewall/PCAP/alert/app remediation/IR | P1 | NET-007; CYBER-002; LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No range or content |
| MISSION-005 | Graded correctness/evidence/safety/troubleshooting report | P1 | MISSION-001 | In progress | simulation/missions.py | tests/test_missions.py:test_changed_rubric_weights_are_executed | Weighted criteria supported; safety/troubleshooting and professional report pending |
| CYBER-001 | Network security/segmentation/firewall/VPN/config auditing | P1 | LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No isolated real range; only simulated switch security |
| CYBER-002 | Authorized discovery/vulnerability/web/API/auth testing and fix validation | P1 | LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No isolated real range; only simulated switch security |
| CYBER-003 | SOC logging/detection/hunting/correlation/triage | P1 | LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No isolated real range; only simulated switch security |
| CYBER-004 | Linux/Windows host and identity/AD/MFA/hardening | P2 | LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No isolated real range; only simulated switch security |
| CYBER-005 | Application and API security, injection/session/access/upload/supply-chain | P2 | LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No isolated real range; only simulated switch security |
| CYBER-006 | Forensics/evidence integrity/host+packet+memory/IR | P2 | LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No isolated real range; only simulated switch security |
| CYBER-007 | Cloud/container/ICS/malware/phishing/email/threat intel/crypto/SDLC/AI/BCP | P2 | LAB-003 | Planned | docs/CYBERSECURITY_CATALOG.md | — | No isolated real range; only simulated switch security |
| LAB-001 | LabProvider capabilities and explicit unsupported operations | P0 | CORE-001 | Tested | providers/base.py; providers/builtin.py | test_provider_capability_and_unsupported; tests/test_persistence.py:test_invalid_checkpoint_id_and_ephemeral_rejection | Real provider operations unsupported |
| LAB-002 | Linux namespace/veth/bridge real provider | P1 | LAB-001; LAB-003 | Blocked | docs/ROADMAP.md | — | Privileges/isolation/runtime unverified |
| LAB-003 | Isolated range deny egress/host, resource/time limits and allowlisted targets | P1 | LAB-001 | Specified | docs/SECURITY_MODEL.md | — | No real range built |
| LAB-004 | Real provider start/stop/reset/checkpoint/destroy/cleanup alarms | P1 | LAB-002; CORE-005 | Planned | docs/SECURITY_MODEL.md | — | No real runtime |
| LAB-005 | Docker/containerlab/GNS3/QEMU/KVM/licensed NOS adapters | P2 | LAB-003 | Blocked | docs/ROADMAP.md | — | No runtimes or image rights checked |
| LAB-006 | Windows/Linux guest and approved remote provider | P2 | LAB-003; CORE-009 | Planned | docs/MASTER_SPEC.md | — | No guest/remote infrastructure |
| TOOL-001 | Network diagnostics ping/traceroute/ip/ss/dig/curl/ethtool/iperf3 | P1 | LAB-003 | Planned | docs/TOOLS_CATALOG.md | — | No tool adapters or real execution |
| TOOL-002 | Packet Wireshark/TShark/tcpdump/Scapy | P1 | LAB-003 | Planned | docs/TOOLS_CATALOG.md | — | No tool adapters or real execution |
| TOOL-003 | Nmap discovery, namespace/bridge/nftables/iptables | P2 | LAB-003 | Planned | docs/TOOLS_CATALOG.md | — | No tool adapters or real execution |
| TOOL-004 | Greenbone/Burp/ZAP vulnerability/app testing | P2 | LAB-003 | Planned | docs/TOOLS_CATALOG.md | — | No tool adapters or real execution |
| TOOL-005 | Suricata/Zeek/Wazuh/Windows logs/Sysmon/auditd/osquery detection | P2 | LAB-003 | Planned | docs/TOOLS_CATALOG.md | — | No tool adapters or real execution |
| TOOL-006 | Autopsy/Sleuth Kit/Volatility/YARA forensics | P2 | LAB-003 | Planned | docs/TOOLS_CATALOG.md | — | No tool adapters or real execution |
| TOOL-007 | Identity/PKI/container/dependency/code/cloud scanners | P2 | LAB-003 | Planned | docs/TOOLS_CATALOG.md | — | No tool adapters or real execution |
| TEST-001 | Core switching/address/negative/mission unit suite | P0 | CORE-001 | Tested | docs/TEST_PLAN.md | tests/test_lab.py | Small topology only |
| TEST-002 | API auth/validation/socket end-to-end tests | P0 | CORE-008 | Tested | tests/test_lab.py; tests/test_http.py; docs/TEST_PLAN.md | test_auth_and_dispatch; BridgeHttpTests; DurableSocketTests; CI headless Godot token flow | Browser-origin and fuzz tests pending |
| TEST-003 | Godot startup, UX and state-synchronization smoke | P0 | GAME-001 | In progress | game/tests/startup.gd; game/tests/smoke.gd; docs/TEST_PLAN.md | CI run 38756303805: Linux+Windows headless startup/integration | Rendered UX/manual GUI still pending; Windows editor import BLOCKED |
| TEST-004 | Migration/checkpoint reproducibility tests | P1 | CORE-005 | Tested | database/store.py; tests/test_persistence.py | PersistenceTests (7 tests) | V2 migration fixture, corruption/power-loss tests pending |
| TEST-005 | Real provider isolation/teardown/permission tests | P1 | LAB-003 | Blocked | docs/TEST_PLAN.md | — | No runtime |
| TEST-006 | Benchmarks/performance and Windows 8 GB tests | P1 | CORE-010 | Planned | docs/TEST_PLAN.md | — | Not measured |
| TEST-007 | CI/static checks, warnings, docs-fidelity review | P1 | CORE-001 | In progress | tools/verify.py; .github/workflows/verify.yml; docs/TEST_PLAN.md | CI run 38756303805 success with Windows import BLOCKED warning | Broader lint and GUI checks pending |
| TEST-008 | Structured verification entry point with fail/block/skip logs | P0 | TEST-001 | Tested | tools/verify.py; tests/test_verify.py | tests/test_verify.py; CI run 38756303805; local strict exit 1 without engine | Local engine unavailable; Windows import exception explicitly reported |
| TEST-009 | SHA-verified pinned Windows Godot CI run | P0 | TEST-008; GAME-001 | In progress | .github/workflows/verify.yml; game/tests/smoke.gd | CI run 38756303805: both jobs success, Linux import strict pass | Windows editor import exits 1 without diagnostics and is BLOCKED, not passed |
| DOC-001 | Spec, backlog, traceability, inventories, fidelity and setup | P0 | — | Specified | docs/; README.md; CHANGELOG.md | — | Updates required each increment |
| SHIP-001 | Versioned installer/diagnostics/upgrade and low-memory packaging | P2 | GAME-001; CORE-005 | Planned | docs/ROADMAP.md | — | No release artifacts |

## Change procedure
When changing a capability: update its ID and catalogue entry, linked implementation and test, fidelity/support limits, roadmap issue and changelog. New granular IDs may be added under the corresponding group. No group row authorizes declaring all subtopics complete.
