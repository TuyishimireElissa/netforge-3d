# Equipment and environment catalogue
| Equipment IDs / group | Fidelity | Interfaces / behavior |
|---|---|---|
| pc-a, pc-b | SIMULATED + 3D placeholder | eth0 each, modeled MAC/IPv4, interface up; PC A prelinked, PC B repair target |
| sw1 | SIMULATED + 3D placeholder | fa0/1, fa0/3 copper RJ45; access VLAN, MAC learn, port security, shutdown; limited CLI |
| copper-repair-cable | SIMULATED + 3D placeholder | one occupied/free port check, only PC B to SW1, no cable length or connector physics |
| r1 | VISUAL ONLY | no registered ports or routing; interaction explicitly disclaims functionality |
| endpoints | PLANNED | desktop, laptop, workstation, printer, NAS, IP phone, camera, IoT, Wi-Fi client, test node |
| switching | PLANNED | unmanaged, L2/L3 managed, access/distribution/core, virtual, management/console/trunk |
| routing/security | PLANNED | edge/virtual/wireless routers, gateway/HA, firewall/VPN/NAC/IDS/IPS/sensors |
| media | PLANNED | fiber, optics/SFP/SFP+, panels, wall outlets, keystones, trays, negotiation, duplex |
| wireless | PLANNED | AP/controller/antennas, simulated radio and channels |
| compute/DC | PLANNED | rack/tower/blade servers, virtualization/backup/directory/web/db, racks, UPS/PDU, cooling/power/environmental |
| specialized | PLANNED | ISP/cloud/industrial and forensic devices |

Visual consistency contract: backend's `ports` and `links` determine displayed cable and text. Godot ray targets use ID strings, not a second mutable topology. Present port buttons are small placeholder boxes; neither connectors nor speed negotiation is realistic. Scene list and remaining environments: see `MASTER_SPEC.md`.
