import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

import server

ROOT = Path(__file__).resolve().parents[1]


class AdminPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(cls.temp.name) / "admin.db"
        # The panel is opt-in (CPP_ADVENTURE_ADMIN=1); these tests exercise it explicitly.
        cls.old_admin = server.ADMIN_ENABLED
        server.ADMIN_ENABLED = True
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.ADMIN_ENABLED = cls.old_admin
        cls.temp.cleanup()

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=40)
        payload = json.dumps(data).encode("utf-8") if data is not None else None
        conn.request(method, path, payload, {"Content-Type": "application/json"} if data is not None else {})
        response = conn.getresponse()
        result = json.loads(response.read())
        conn.close()
        return response.status, result

    def profile(self, name):
        _, created = self.request("POST", "/api/profiles", {"name": name})
        return created["profile_id"]

    def admin(self, pid, action, value=None):
        return self.request("POST", "/api/admin", {"profile_id": pid, "action": action, "value": value})

    def test_xp_level_and_streak_can_be_set_for_testing(self):
        pid = self.profile("Admin A")
        status, data = self.admin(pid, "add_xp", 750)
        self.assertEqual(status, 200)
        self.assertEqual(data["profile"]["xp"], 750)
        _, data = self.admin(pid, "set_xp", 42)
        self.assertEqual(data["profile"]["xp"], 42)
        _, data = self.admin(pid, "set_level", 11)
        self.assertEqual(data["profile"]["level"], 11)
        self.assertEqual(data["profile"]["level_xp"], 0)
        _, data = self.admin(pid, "set_level", 1)
        self.assertEqual(data["profile"]["level"], 1)
        _, data = self.admin(pid, "set_streak", 5)
        self.assertEqual(data["profile"]["streak"], 5)

    def test_items_chapters_badges_and_reset(self):
        pid = self.profile("Admin B")
        _, data = self.admin(pid, "grant_items")
        self.assertEqual(sorted(data["profile"]["owned_items"]), sorted(server.SHOP))
        _, data = self.admin(pid, "complete_chapter", 0)
        first = [task["id"] for task in server.CURRICULUM[0]["tasks"]]
        self.assertTrue(set(first) <= set(data["profile"]["completed"]))
        _, data = self.admin(pid, "grant_badges")
        self.assertIn("legend", data["profile"]["achievements"])
        _, data = self.admin(pid, "clear_items")
        self.assertEqual(data["profile"]["owned_items"], [])
        _, data = self.admin(pid, "reset_progress")
        self.assertEqual(data["profile"]["completed"], [])
        self.assertEqual(data["profile"]["xp"], 0)
        self.assertEqual(data["profile"]["level"], 1)

    def test_invalid_input_and_unknown_profile_are_rejected(self):
        pid = self.profile("Admin C")
        status, data = self.admin(pid, "set_level", 999)
        self.assertEqual(status, 400)
        status, _ = self.admin(pid, "drop_tables")
        self.assertEqual(status, 400)
        status, _ = self.admin("missing", "add_xp", 10)
        self.assertEqual(status, 404)

    def test_panel_can_be_switched_off(self):
        pid = self.profile("Admin D")
        old = server.ADMIN_ENABLED
        server.ADMIN_ENABLED = False
        try:
            status, _ = self.admin(pid, "add_xp", 10)
            self.assertEqual(status, 403)
            _, meta = self.request("GET", "/api/meta")
            self.assertFalse(meta["admin"])
        finally:
            server.ADMIN_ENABLED = old

    def test_panel_and_motion_scripts_are_loaded(self):
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        for asset in ("/motion.js", "/motion.css", "/admin-panel.js", "/admin-panel.css"):
            self.assertIn(asset, index)
        motion = (ROOT / "web" / "motion.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", motion)
        panel = (ROOT / "web" / "admin-panel.js").read_text(encoding="utf-8")
        self.assertIn("/api/admin", panel)


if __name__ == "__main__":
    unittest.main()
