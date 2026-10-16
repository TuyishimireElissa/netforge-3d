"""Browser companion serves only ephemeral, allowlisted simulated operations."""
import http.client
import json
from http.server import ThreadingHTTPServer
import threading
import unittest

from backend.preview import handler_for
from backend.server import App


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App("internal-test-token")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(cls.app))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.app.close()

    def request(self, method, path, payload=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request(method, path, json.dumps(payload) if payload is not None else None, headers or {})
        result = conn.getresponse()
        response = result.status, result.getheaders(), result.read()
        conn.close()
        return response

    def test_static_page_and_relative_endpoints(self):
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"not the Godot 3D game", body)
        self.assertIn("connect-src 'self'", dict(headers)["Content-Security-Policy"])
        self.assertEqual(self.request("HEAD", "/")[0], 200)
        self.assertEqual(self.request("GET", "/api/state")[0], 200)
        self.assertEqual(self.request("GET", "/api/missions")[0], 200)
        self.assertEqual(self.request("GET", "/unknown")[0], 404)

    def test_only_simulated_json_actions_and_no_external_tools(self):
        connect = {"action": "connect", "a": "pc-b:eth0", "b": "sw1:fa0/3"}
        self.assertEqual(self.request("POST", "/api/action", connect)[0], 403)
        headers = {"Content-Type": "application/json", "X-NetForge-Preview": "1"}
        self.assertEqual(self.request("POST", "/api/action", {"action": "shell", "line": "whoami"}, headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/action", {"action": []}, headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/action", {"action": {"reset": True}}, headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/action", {"action": "checkpoint"}, headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/action", {"action": "reset"}, headers)[0], 200)
        self.assertEqual(self.request("POST", "/api/action", connect, headers)[0], 200)
        status, _, raw = self.request("POST", "/api/action", {"action": "ping", "source": "pc-b:eth0", "target": "pc-a:eth0"}, headers)
        self.assertEqual(status, 200)
        body = json.loads(raw)
        self.assertEqual(body["state"]["fidelity"], "SIMULATED")
        self.assertTrue(body["state"]["assessment"]["mission_a"]["complete"])
        self.assertEqual(body["state"]["storage"], "memory")

    def test_mission_b_via_browser_api(self):
        headers = {"Content-Type": "application/json", "X-NetForge-Preview": "1"}
        def perform(data):
            status, _, raw = self.request("POST", "/api/action", data, headers)
            self.assertEqual(status, 200, raw)
            return json.loads(raw)

        perform({"action": "reset"})
        perform({"action": "connect", "a": "pc-b:eth0", "b": "sw1:fa0/3"})
        for line in ("enable", "configure terminal", "interface fastethernet 0/3", "switchport port-security", "switchport port-security mac-address sticky", "end"):
            perform({"action": "command", "device": "sw1", "line": line})
        perform({"action": "ping", "source": "pc-b:eth0", "target": "pc-a:eth0"})
        perform({"action": "command", "device": "sw1", "line": "write memory"})
        result = perform({"action": "assess"})
        self.assertTrue(result["state"]["assessment"]["mission_b"]["complete"])
        self.assertEqual(result["state"]["assessment"]["mission_b"]["score"], 5)
        self.assertEqual(result["state"]["storage"], "memory")
        perform({"action": "reset"})
