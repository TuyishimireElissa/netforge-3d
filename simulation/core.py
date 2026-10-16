"""Small documented Ethernet/IPv4 lab model; NOT a packet stack or PCAP capture."""
from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
import os
from typing import Optional


class LabError(ValueError):
    pass


@dataclass
class Port:
    id: str
    device: str
    mac: str
    address: str = ""
    enabled: bool = True
    vlan: int = 1
    mode: str = "access"
    security: bool = False
    sticky: bool = False
    maximum: int = 1
    violation: str = "shutdown"
    learned: set[str] = field(default_factory=set)
    violated: bool = False

    @property
    def up(self) -> bool:
        return self.enabled and not self.violated


@dataclass
class Link:
    a: str
    b: str
    media: str = "copper"

    def peer(self, port: str) -> Optional[str]:
        return self.b if self.a == port else self.a if self.b == port else None


class Lab:
    """Finite toy lab: two PCs, one access switch, no real OS networking."""

    def __init__(self, durable: bool = False) -> None:
        self.durable = durable
        self.reset()

    def reset(self) -> None:
        self.ports = {
            "pc-a:eth0": Port("pc-a:eth0", "pc-a", "02:00:00:00:00:0a", "192.168.10.10/24"),
            "pc-b:eth0": Port("pc-b:eth0", "pc-b", "02:00:00:00:00:0b", "192.168.10.11/24"),
            "sw1:fa0/1": Port("sw1:fa0/1", "sw1", "02:00:00:00:01:01"),
            "sw1:fa0/3": Port("sw1:fa0/3", "sw1", "02:00:00:00:01:03"),
        }
        self.links: list[Link] = [Link("pc-a:eth0", "sw1:fa0/1")]
        self.mac_table: dict[tuple[int, str], str] = {}
        self.traces: list[str] = []
        self.events: list[str] = []
        self.saved_config: Optional[dict] = None
        self.last_ping = False
        self.last_ping_source = ""
        self.last_ping_target = ""
        self.cli = SwitchCLI(self)
        self._event("Lab reset: PC-B cable is disconnected")

    def _event(self, message: str) -> None:
        self.events.append(message)
        self.events = self.events[-80:]

    def _trace(self, message: str) -> None:
        self.traces.append(message)
        self.traces = self.traces[-80:]

    def link_of(self, port: str) -> Optional[Link]:
        return next((link for link in self.links if link.peer(port) is not None), None)

    def connect(self, a: str, b: str, media: str = "copper") -> None:
        if a not in self.ports or b not in self.ports or a == b:
            raise LabError("Unknown or identical interface")
        if self.ports[a].device == self.ports[b].device:
            raise LabError("Cannot cable interfaces on the same device in this lab")
        if {self.ports[a].device, self.ports[b].device} != {"sw1", "pc-b"}:
            raise LabError("Only the PC-B to switch repair cable is available")
        if media != "copper":
            raise LabError("These RJ45 interfaces require copper")
        if self.link_of(a) or self.link_of(b):
            raise LabError("An interface is already occupied")
        self.links.append(Link(a, b, media))
        self._event(f"Copper cable connected: {a} <-> {b}")

    def disconnect(self, port: str) -> None:
        link = self.link_of(port)
        if not link or link.a == "pc-a:eth0" or link.b == "pc-a:eth0":
            raise LabError("Only the repair cable can be disconnected")
        self.links.remove(link)
        self.mac_table.clear()
        self.last_ping = False
        self._event(f"Cable disconnected from {port}")

    def _switch_receive(self, switch_port: str, source_mac: str, target_mac: str, kind: str) -> bool:
        port = self.ports[switch_port]
        if not port.up:
            self._trace(f"DROP {kind}: {switch_port} disabled or security shutdown")
            return False
        if port.security and source_mac not in port.learned:
            if len(port.learned) >= port.maximum:
                self._trace(f"DROP {kind}: port-security violation on {switch_port} ({port.violation})")
                self._event(f"Port-security violation on {switch_port}")
                if port.violation == "shutdown":
                    port.violated = True
                return False
            port.learned.add(source_mac)
            self._trace(f"Port-security learned {source_mac} on {switch_port}" + (" (sticky)" if port.sticky else ""))
        self.mac_table[(port.vlan, source_mac)] = switch_port
        self._trace(f"LEARN VLAN {port.vlan}: {source_mac} on {switch_port}")
        candidates = [p for p in ("sw1:fa0/1", "sw1:fa0/3") if p != switch_port and self.ports[p].up and self.ports[p].vlan == port.vlan and self.link_of(p)]
        known = self.mac_table.get((port.vlan, target_mac))
        if known:
            candidates = [p for p in candidates if p == known]
            self._trace(f"FORWARD {kind}: known destination via {known}" if candidates else f"DROP {kind}: destination {known} unavailable")
        else:
            self._trace(f"FLOOD {kind}: unknown/broadcast destination to {candidates}")
        return bool(candidates)

    def _send(self, source: str, target: str, kind: str, broadcast: bool = False) -> bool:
        src = self.ports[source]
        dst = self.ports[target]
        slink = self.link_of(source)
        dlink = self.link_of(target)
        if not src.up or not slink:
            self._trace(f"DROP {kind}: {source} down or disconnected")
            return False
        if not dst.up or not dlink:
            self._trace(f"DROP {kind}: {target} down or disconnected")
            return False
        ingress = slink.peer(source)
        egress = dlink.peer(target)
        if ingress is None or egress is None or ingress == egress:
            self._trace(f"DROP {kind}: invalid switch path")
            return False
        if self.ports[ingress].vlan != self.ports[egress].vlan:
            self._trace(f"DROP {kind}: VLAN mismatch between {ingress} and {egress}")
            return False
        if not self._switch_receive(ingress, src.mac, "ff:ff:ff:ff:ff:ff" if broadcast else dst.mac, kind):
            return False
        self._trace(f"DELIVER {kind}: {source} -> {target} via {egress}")
        return True

    def ping(self, source: str, target: str) -> bool:
        # A rejected request must not erase valid mission evidence or the previous trace.
        if source not in ("pc-a:eth0", "pc-b:eth0") or target not in ("pc-a:eth0", "pc-b:eth0") or source == target:
            raise LabError("Ping requires two distinct lab computers")
        self.traces = []
        self.last_ping = False
        self.last_ping_source, self.last_ping_target = source, target
        a = ipaddress.ip_interface(self.ports[source].address)
        b = ipaddress.ip_interface(self.ports[target].address)
        if a.ip == b.ip:
            self._trace("DROP IPv4: duplicate endpoint address")
            return False
        if b.ip not in a.network or a.ip not in b.network:
            self._trace("DROP IPv4: destination outside source subnet; no router or route implemented")
            return False
        if not self._send(source, target, "ARP request", broadcast=True):
            return False
        if not self._send(target, source, "ARP reply"):
            return False
        if not self._send(source, target, "ICMP echo request"):
            return False
        if not self._send(target, source, "ICMP echo reply"):
            return False
        self.last_ping = True
        self._event(f"Simulated ICMP success: {source} -> {target}")
        return True

    def configure_ip(self, port: str, cidr: str) -> None:
        if port not in ("pc-a:eth0", "pc-b:eth0"):
            raise LabError("Only PC addresses are configurable")
        try:
            address = ipaddress.IPv4Interface(cidr)
        except (ValueError, ipaddress.AddressValueError) as exc:
            raise LabError("Invalid IPv4 CIDR address") from exc
        self.ports[port].address = str(address)
        self.last_ping = False
        self._event(f"Address changed: {port} = {address}")

    def assess(self) -> dict:
        from simulation.missions import assess
        return assess(self)

    def state(self) -> dict:
        return {"product_name": os.environ.get("NETFORGE_NAME", "NetForge 3D"), "fidelity": "SIMULATED", "provider": "builtin", "storage": "SQLite" if self.durable else "memory",
                "devices": {"pc-a": "computer", "pc-b": "computer", "sw1": "managed-switch", "r1": "VISUAL ONLY router"},
                "ports": {key: {"device": p.device, "mac": p.mac, "address": p.address, "enabled": p.enabled,
                                "up": p.up, "vlan": p.vlan, "mode": p.mode, "security": p.security, "sticky": p.sticky,
                                "learned": sorted(p.learned), "violated": p.violated, "linked": bool(self.link_of(key))}
                          for key, p in self.ports.items()},
                "links": [{"a": l.a, "b": l.b, "media": l.media} for l in self.links],
                "mac_table": [{"vlan": vlan, "mac": mac, "interface": iface} for (vlan, mac), iface in sorted(self.mac_table.items())],
                "trace": self.traces, "events": self.events, "assessment": self.assess(),
                "cli_mode": self.cli.mode, "saved": self.saved_config is not None}


class SwitchCLI:
    """Documented vendor-inspired subset, not a Cisco or other vendor OS."""

    def __init__(self, lab: Lab) -> None:
        self.lab = lab
        self.mode = "user"
        self.selected = ""

    def execute(self, line: str) -> str:
        line = line.strip().lower()
        if len(line) > 160:
            return "% Command too long"
        if not line:
            return ""
        if line == "exit":
            if self.mode == "interface":
                self.mode, self.selected = "config", ""
            elif self.mode == "config":
                self.mode = "privileged"
            elif self.mode == "privileged":
                self.mode = "user"
            return f"Mode: {self.mode}"
        if line == "end" and self.mode in ("config", "interface"):
            self.mode, self.selected = "privileged", ""
            return "Mode: privileged"
        if line == "enable" and self.mode == "user":
            self.mode = "privileged"
            return "Mode: privileged"
        if line == "configure terminal" and self.mode == "privileged":
            self.mode = "config"
            return "Mode: config"
        if line.startswith("show ") and self.mode in ("privileged", "config", "interface"):
            return self._show(line)
        if line == "write memory" and self.mode == "privileged":
            self.lab.saved_config = {"sticky_macs": sorted(m for p in self.lab.ports.values() if p.sticky for m in p.learned),
                                     "interfaces": {k: {"vlan": p.vlan, "enabled": p.enabled, "security": p.security, "sticky": p.sticky,
                                                        "maximum": p.maximum, "violation": p.violation} for k, p in self.lab.ports.items() if p.device == "sw1"}}
            self.lab._event("Switch configuration saved (provider durability applies)")
            return "Configuration saved (SQLite-backed session)" if self.lab.durable else "Configuration saved (this session only)"
        if self.mode == "config" and line.startswith("interface "):
            interface = line.removeprefix("interface ").replace("fastethernet 0/", "fa0/")
            port = f"sw1:{interface}"
            if port not in self.lab.ports or self.lab.ports[port].device != "sw1":
                return "% Unknown interface; supported: fastethernet 0/1, 0/3"
            self.selected, self.mode = port, "interface"
            return f"Selected {port}"
        if self.mode == "interface":
            port = self.lab.ports[self.selected]
            if line in ("shutdown", "no shutdown"):
                port.enabled = line == "no shutdown"
                self.lab.last_ping = False
                return f"{self.selected} {'up' if port.enabled else 'administratively down'}"
            if line in ("switchport port-security", "no switchport port-security"):
                port.security = not line.startswith("no ")
                if not port.security:
                    port.learned.clear()
                    port.violated = False
                return f"Port security {'enabled' if port.security else 'disabled'}"
            if line in ("switchport port-security mac-address sticky", "no switchport port-security mac-address sticky"):
                if not port.security and not line.startswith("no "):
                    return "% Enable port-security first"
                port.sticky = not line.startswith("no ")
                return f"Sticky learning {'enabled' if port.sticky else 'disabled'}"
            if line.startswith("switchport port-security maximum "):
                if not port.security:
                    return "% Enable port-security first"
                value = line.rsplit(" ", 1)[-1]
                if value not in ("1", "2", "3", "4"):
                    return "% Maximum must be 1..4"
                port.maximum = int(value)
                return f"Maximum: {value}"
            if line.startswith("switchport port-security violation "):
                if not port.security:
                    return "% Enable port-security first"
                value = line.rsplit(" ", 1)[-1]
                if value not in ("shutdown", "restrict", "protect"):
                    return "% Supported policies: shutdown, restrict, protect"
                port.violation = value
                return f"Violation policy: {value}"
            if line.startswith("switchport access vlan "):
                if port.mode != "access":
                    return "% VLAN assignment requires access mode"
                value = line.rsplit(" ", 1)[-1]
                if not value.isdecimal() or not 1 <= int(value) <= 4094:
                    return "% VLAN ID must be 1..4094"
                port.vlan = int(value)
                self.lab.mac_table.clear()
                self.lab.last_ping = False
                return f"Access VLAN: {value}"
            if line == "switchport mode access":
                port.mode = "access"
                return "Access mode enabled"
            if line == "switchport mode trunk":
                return "% Trunking is not implemented"
            if line == "clear port-security violation":
                port.violated = False
                return "Security shutdown cleared"
        return f"% Invalid command in {self.mode} mode: {line}"

    def _show(self, line: str) -> str:
        if line == "show mac address-table":
            return "\n".join(f"VLAN {v} {m} {p}" for (v, m), p in sorted(self.lab.mac_table.items())) or "MAC table empty"
        if line == "show interfaces":
            return "\n".join(f"{k}: {'up' if p.up else 'down'}, VLAN {p.vlan}, linked={bool(self.lab.link_of(k))}" for k, p in self.lab.ports.items() if p.device == "sw1")
        if line == "show port-security":
            return "\n".join(f"{k}: enabled={p.security}, sticky={p.sticky}, max={p.maximum}, policy={p.violation}, violated={p.violated}, learned={sorted(p.learned)}" for k, p in self.lab.ports.items() if p.device == "sw1")
        if line == "show running-config":
            return "\n".join(f"interface {k}\n switchport mode {p.mode}\n switchport access vlan {p.vlan}\n {'shutdown' if not p.enabled else 'no shutdown'}\n {'switchport port-security' if p.security else 'no switchport port-security'}\n {'switchport port-security mac-address sticky' if p.sticky else 'no switchport port-security mac-address sticky'}\n switchport port-security maximum {p.maximum}\n switchport port-security violation {p.violation}" for k, p in self.lab.ports.items() if p.device == "sw1")
        if line == "show startup-config":
            return str(self.lab.saved_config) if self.lab.saved_config else "% No saved configuration"
        return "% Unsupported show command"
