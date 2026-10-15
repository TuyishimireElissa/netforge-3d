"""Real loopback HTTP socket tests; still not Godot or a real network lab."""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from backend.server import App, make_handler


class BridgeHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class QuietHandler(make_handler(App("local-test-token"))):
            def log_message(self, *args): pass
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path, body=None, token="local-test-token"):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        headers = {"X-NetForge-Token": token}
        if body is not None: headers["Content-Type"] = "application/json"
        conn.request(method, path, body, headers)
        response = conn.getresponse()
        result = response.status, json.loads(response.read()), response.getheader("Access-Control-Allow-Origin")
        conn.close()
        return result

    def test_no_token_and_no_cors(self):
        status, body, cors = self.request("GET", "/state", token="")
        self.assertEqual(status, 401)
        self.assertIsNone(cors)
        self.assertIn("error", body)

    def test_non_ascii_token_returns_401_without_changing_state(self):
        before = self.request("GET", "/state")[1]["state"]
        for method, path, body in (
            ("GET", "/state", None),
            ("POST", "/action", json.dumps({"action": "reset"})),
        ):
            status, result, cors = self.request(method, path, body, token="invalid-é")
            self.assertEqual(status, 401)
            self.assertEqual(result, {"error": "Invalid session token"})
            self.assertIsNone(cors)
        self.assertEqual(self.request("GET", "/state")[1]["state"], before)

    def test_session_token_configuration_validated(self):
        for token in (None, b"bytes", "", "non-ascii-é"):
            with self.assertRaisesRegex(ValueError, "ASCII session token"):
                App(token)

    def test_socket_round_trip_and_bad_body(self):
        self.assertEqual(self.request("GET", "/state")[0], 200)
        self.assertEqual(self.request("POST", "/action", "not json")[0], 400)
        self.assertEqual(self.request("POST", "/action", " " * 4097)[0], 413)
        status, body, _ = self.request("POST", "/action", json.dumps({"action":"ping", "source":"pc-b:eth0", "target":"pc-a:eth0"}))
        self.assertEqual(status, 200)
        self.assertIn("disconnected", " ".join(body["state"]["trace"]))


class DurableSocketTests(unittest.TestCase):
    def test_authenticated_checkpoint_round_trip_over_http(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            app = App("socket-secret", Path(directory) / "state.sqlite3")
            class QuietHandler(make_handler(app)):
                def log_message(self, *args): pass
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def send(method, path, payload=None):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
                connection.request(method, path, json.dumps(payload) if payload else None,
                                   {"X-NetForge-Token": "socket-secret", "Content-Type": "application/json"})
                response = connection.getresponse()
                status, data = response.status, json.loads(response.read())
                connection.close()
                return status, data
            try:
                status, missions = send("GET", "/missions")
                self.assertEqual(status, 200)
                self.assertEqual(len(missions["missions"]), 2)
                self.assertEqual(send("POST", "/action", {"action": "connect", "a": "pc-b:eth0", "b": "sw1:fa0/3"})[0], 200)
                status, result = send("POST", "/action", {"action": "checkpoint"})
                self.assertEqual(status, 200)
                checkpoint_id = result["result"]["checkpoint_id"]
                send("POST", "/action", {"action": "reset"})
                self.assertFalse(send("GET", "/state")[1]["state"]["ports"]["pc-b:eth0"]["linked"])
                self.assertEqual(send("POST", "/action", {"action": "restore", "checkpoint_id": checkpoint_id})[0], 200)
                self.assertTrue(send("GET", "/state")[1]["state"]["ports"]["pc-b:eth0"]["linked"])
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=4) as executor:
                    statuses = list(executor.map(lambda _: send("POST", "/action", {
                        "action": "ping", "source": "pc-b:eth0", "target": "pc-a:eth0"})[0], range(8)))
                self.assertEqual(statuses, [200] * 8)
                self.assertEqual(sum("Simulated ICMP success" in event for event in send("GET", "/state")[1]["state"]["events"]), 8)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                app.close()
            reopened = App("socket-secret", Path(directory) / "state.sqlite3")
            self.assertTrue(reopened.provider.lab.link_of("pc-b:eth0"))
            reopened.close()
