# Networking curriculum and protocol backlog
Reviewed 2026-10-15. Each topic below has educational context but **planned** behavior unless marked tested. Consult `PROTOCOL_FIDELITY.md` for exact behavior. Relevant authoritative sources: [IETF RFC index](https://www.rfc-editor.org/rfc-index.html), [IEEE 802.3](https://www.ieee802.org/3/), [IEEE 802.1](https://www.ieee802.org/1/), [IANA protocol registries](https://www.iana.org/protocols). References are links for future per-feature reviews; not all standards have been validated in this environment.

| Register | Topics | Fidelity / next gate |
|---|---|---|
| Fundamentals | OSI/TCP-IP, number bases, Ethernet framing, unicast/broadcast/multicast, IPv4/IPv6 CIDR and special ranges, MTU/fragmentation, duplex/speed | IPv4 same-subnet comparison SIMULATED; rest PLANNED |
| L2 | MAC learning/flooding, aging, ARP/ND, VLAN/802.1Q/access/trunk, STP/RSTP, aggregation/LACP, storm prevention, security, shutdown/counters | subset SIMULATED; tagging, aging, loop handling PLANNED |
| Routing | route lookup/LPM, static/default, IPv4/v6/inter-VLAN, OSPF/BGP, convergence/policy, NAT/PAT, HA gateway/PBR | PLANNED, router VISUAL ONLY |
| Services | DHCP/v6, DNS, ICMPv6, TCP/UDP, HTTP(S)/TLS, SSH, FTP/SFTP, SMTP/IMAP/POP3, SMB, LDAP/Kerberos, NTP/SNMP/syslog, SIP, REST/WebSockets/JSON/discovery | basic modeled ARP + ICMPv4 SIMULATED; rest PLANNED |
| Wireless | SSID/association, channels/RSSI/interference, WPA2/3, enterprise 802.1X, guest segmentation | PLANNED |
| Secure/performance | ACL/stateful firewall/DMZ, VPN/IPsec/WireGuard, QoS, throughput/latency/jitter/loss/congestion/telemetry/HA | PLANNED |
| Modern/provider | vNIC/vSwitch/bridges/namespaces/containers/SDN/overlays/cloud/groups/policies, MPLS/ISP/automation/ICS | PLANNED |

Teaching progression: physical path -> Ethernet decisions -> addresses/subnets -> ARP/ICMP -> VLAN -> routing -> services -> filtering -> observability -> wireless/modern. For a new protocol: link standard and reviewed date, specify state machine, deviations, supported commands/packets, positive/negative tests and fidelity. A named diagram is never evidence of implementation.
