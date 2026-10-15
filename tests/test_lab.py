import unittest

from simulation.core import Lab, LabError
from providers.builtin import BuiltinProvider
from providers.base import UnsupportedOperation
from backend.server import App


class LabTests(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def repair(self):
        self.lab.connect("pc-b:eth0", "sw1:fa0/3")

    def configure_security(self):
        cli = self.lab.cli
        self.assertEqual(cli.execute("enable"), "Mode: privileged")
        self.assertEqual(cli.execute("configure terminal"), "Mode: config")
        self.assertEqual(cli.execute("interface fastethernet 0/3"), "Selected sw1:fa0/3")
        self.assertEqual(cli.execute("switchport port-security"), "Port security enabled")
        self.assertEqual(cli.execute("switchport port-security mac-address sticky"), "Sticky learning enabled")

    def test_initial_disconnected_and_trace(self):
        self.assertFalse(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertIn("disconnected", " ".join(self.lab.traces))
        self.assertFalse(self.lab.assess()["mission_a"]["complete"])

    def test_link_repair_arp_icmp_mac_and_assessment(self):
        self.repair()
        self.assertTrue(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertTrue(self.lab.assess()["mission_a"]["complete"])
        self.assertFalse(self.lab.assess()["mission_b"]["complete"])
        self.assertTrue(any("ARP request" in x for x in self.lab.traces))
        self.assertTrue(any("ICMP echo reply" in x for x in self.lab.traces))
        self.assertEqual(self.lab.mac_table[(1, self.lab.ports["pc-b:eth0"].mac)], "sw1:fa0/3")

    def test_sticky_exercise_requires_evidence_and_save(self):
        self.repair()
        self.configure_security()
        self.assertFalse(self.lab.assess()["mission_b"]["complete"])
        self.assertTrue(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertIn(self.lab.ports["pc-b:eth0"].mac, self.lab.ports["sw1:fa0/3"].learned)
        self.assertFalse(self.lab.assess()["mission_b"]["complete"])
        self.lab.cli.execute("end")
        self.lab.cli.execute("write memory")
        self.assertTrue(self.lab.assess()["mission_b"]["complete"])
        self.lab.reset()
        self.assertFalse(self.lab.assess()["mission_b"]["complete"])

    def test_invalid_connections_and_media(self):
        with self.assertRaises(LabError): self.lab.connect("pc-b:eth0", "sw1:fa0/3", "fiber")
        with self.assertRaises(LabError): self.lab.connect("pc-a:eth0", "sw1:fa0/3")
        with self.assertRaises(LabError): self.lab.connect("pc-b:eth0", "pc-a:eth0")
        self.repair()
        with self.assertRaises(LabError): self.repair()
        self.lab.disconnect("pc-b:eth0")
        self.assertFalse(self.lab.ping("pc-b:eth0", "pc-a:eth0"))

    def test_vlan_isolation(self):
        self.repair()
        self.lab.ports["sw1:fa0/3"].vlan = 20
        self.assertFalse(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertIn("VLAN mismatch", " ".join(self.lab.traces))

    def test_duplicate_address_rejected(self):
        self.repair()
        self.lab.configure_ip("pc-b:eth0", "192.168.10.10/24")
        self.assertFalse(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertIn("duplicate", " ".join(self.lab.traces))

    def test_subnet_and_missing_router(self):
        self.repair()
        self.lab.configure_ip("pc-b:eth0", "10.0.0.2/24")
        self.assertFalse(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertIn("no router", " ".join(self.lab.traces))
        with self.assertRaises(LabError): self.lab.configure_ip("pc-b:eth0", "not an ip")

    def test_disabled_interface(self):
        self.repair()
        self.lab.ports["sw1:fa0/3"].enabled = False
        self.assertFalse(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertIn("disabled", " ".join(self.lab.traces))

    def test_security_violation_and_recovery(self):
        self.repair()
        self.configure_security()
        self.assertTrue(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.lab.ports["pc-b:eth0"].mac = "02:00:00:00:00:ff"
        self.assertFalse(self.lab.ping("pc-b:eth0", "pc-a:eth0"))
        self.assertTrue(self.lab.ports["sw1:fa0/3"].violated)
        self.assertIn("port-security violation", " ".join(self.lab.traces))
        self.assertEqual(self.lab.cli.execute("clear port-security violation"), "Security shutdown cleared")
        self.assertFalse(self.lab.ports["sw1:fa0/3"].violated)

    def test_cli_modes_negative_cases(self):
        cli = self.lab.cli
        self.assertIn("Invalid command", cli.execute("configure terminal"))
        cli.execute("enable")
        cli.execute("configure terminal")
        self.assertIn("Unknown interface", cli.execute("interface fastethernet 0/2"))
        cli.execute("interface fastethernet 0/3")
        self.assertIn("Enable port-security first", cli.execute("switchport port-security mac-address sticky"))
        self.assertIn("Trunking is not implemented", cli.execute("switchport mode trunk"))
        self.assertIn("VLAN ID", cli.execute("switchport access vlan 4095"))
        self.assertIn("Invalid command", cli.execute("unsupported operation"))
        self.assertIn("Invalid command", cli.execute("write memory"))

    def test_provider_capability_and_unsupported(self):
        provider = BuiltinProvider()
        self.assertFalse(provider.capabilities()["real_tools"])
        with self.assertRaises(UnsupportedOperation): provider.capture_packets()
        with self.assertRaises(UnsupportedOperation): provider.execute_command("host", "ls")


class ApiTests(unittest.TestCase):
    def setUp(self): self.app = App("secret-test-token")

    def call(self, method, path, payload=None, token="secret-test-token"):
        return self.app.handle(method, path, token, payload)

    def test_auth_and_dispatch(self):
        self.assertEqual(self.call("GET", "/state", token="wrong")[0], 401)
        self.assertEqual(self.call("POST", "/action", {"action":"shell", "line":"rm -rf /"})[0], 400)
        self.assertEqual(self.call("POST", "/action", {"action":"command", "device":"host", "line":"ls"})[0], 400)
        status, body = self.call("GET", "/state")
        self.assertEqual(status, 200)
        self.assertEqual(body["state"]["fidelity"], "SIMULATED")
        self.assertFalse(body["capabilities"]["real_capture"])

    def test_api_mission_round_trip(self):
        for payload in [
            {"action":"connect", "a":"pc-b:eth0", "b":"sw1:fa0/3"},
            *({"action":"command", "device":"sw1", "line":line} for line in
              ("enable", "configure terminal", "interface fastethernet 0/3", "switchport port-security", "switchport port-security mac-address sticky")),
            {"action":"ping", "source":"pc-b:eth0", "target":"pc-a:eth0"},
            {"action":"command", "device":"sw1", "line":"end"},
            {"action":"command", "device":"sw1", "line":"write memory"},
        ]:
            status, body = self.call("POST", "/action", payload)
            self.assertEqual(status, 200, body)
        self.assertTrue(body["state"]["assessment"]["mission_b"]["complete"])
        self.call("POST", "/action", {"action":"reset"})
        self.assertFalse(self.call("GET", "/state")[1]["state"]["assessment"]["mission_b"]["complete"])


if __name__ == "__main__": unittest.main()
