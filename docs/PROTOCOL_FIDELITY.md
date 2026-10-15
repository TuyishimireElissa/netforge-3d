# Protocol support register: actual behavior and limits
Standards pointers for future fidelity reviews (reviewed 2026-10-15): [RFC 826 ARP](https://www.rfc-editor.org/rfc/rfc826), [RFC 791 IPv4](https://www.rfc-editor.org/rfc/rfc791), [RFC 792 ICMP](https://www.rfc-editor.org/rfc/rfc792), [RFC 4632 CIDR](https://www.rfc-editor.org/rfc/rfc4632), [IEEE 802.1 working group](https://www.ieee802.org/1/). The implementation below is *not* a conformant realization of these standards.
| Feature | Status/fidelity | Model / deviations | Test evidence |
|---|---|---|---|
| Copper link | SIMULATED | Occupancy, allowed endpoints and interface enable state; no negotiation/errors or electric signaling | `test_invalid_connections_and_media`, `test_initial_disconnected_and_trace` |
| Ethernet L2 | SIMULATED | Two access ports, VLAN-scoped MAC learning, flood unknown/broadcast, known unicast; no actual frames, TTL, aging, STP, 802.1Q tag, dynamic topology breadth | `test_link_repair_arp_icmp_mac_and_assessment`, `test_vlan_isolation` |
| IPv4 CIDR | SIMULATED | `ipaddress` same-subnet check; no default gateway, route, ARP cache, address conflict detection beyond duplicate endpoint check | `test_subnet_and_missing_router` |
| ARP | SIMULATED | Ping sends modeled request broadcast and reply; no ARP cache, retries, gratuitous ARP or real serialization | `test_link_repair_arp_icmp_mac_and_assessment` |
| ICMPv4 | SIMULATED | Ping requires delivery of request+reply after modeled ARP; no TTL, checksum, timing, ICMP error types or OS ping | `test_initial_disconnected_and_trace`, `test_link_repair_arp_icmp_mac_and_assessment` |
| VLAN access | SIMULATED | Interfaces have VLAN IDs and different VLANs cannot exchange; no tag frames/trunking, VLAN creation or L3 | `test_vlan_isolation`, `test_cli_modes_negative_cases` |
| Port security | SIMULATED | Source-MAC set, max 1..4, shutdown/restrict/protect policies; sticky remembers learned address in memory, write memory persists through the default SQLite bridge but only in-process via headless console/--ephemeral; no Cisco compatibility | `test_security_violation_and_recovery`, `test_sticky_exercise_requires_evidence_and_save` |
| Routing, firewall, DHCP, DNS, IPv6, Wi-Fi, real capture | PLANNED | no behavior implemented | None |

The event trace is a list of synthetic decisions, **not** PCAP, real traffic or a wire-format packet. `write memory` is not vendor NVRAM; it persists only via the default SQLite-backed bridge. Reset clears the active config, but explicit checkpoints can restore it; `--ephemeral` and the console lose it on process exit. Do not rely on this model to verify production networks.
