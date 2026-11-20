import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

import server


class ProfileOnboardingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db = server.DB_PATH
        server.DB_PATH = Path(cls.temp.name) / "test.db"
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close(); cls.temp.cleanup()
        server.DB_PATH = cls.old_db

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=40)
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        conn.request(method, path, payload, {"Content-Type": "application/json"} if data is not None else {})
        response = conn.getresponse(); result = json.loads(response.read()); status = response.status; conn.close()
        return status, result

    def avatar_of(self, pid):
        return next(p for p in self.request("GET", "/api/profiles")[1]["profiles"] if p["id"] == pid)["avatar"]

    def test_character_avatars_are_accepted_and_unknown_values_fall_back(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Karakter", "avatar": "c:hack"})
        self.assertEqual(self.avatar_of(a["profile_id"]), "c:hack")
        _, b = self.request("POST", "/api/profiles", {"name": "Garip", "avatar": "<script>"})
        self.assertEqual(self.avatar_of(b["profile_id"]), "🐱")
        status, _ = self.request("POST", "/api/profile/update", {"profile_id": a["profile_id"], "avatar": "c:wiz"})
        self.assertEqual(status, 200)
        self.assertEqual(self.avatar_of(a["profile_id"]), "c:wiz")

    def test_pin_protected_profile_cannot_be_edited_without_current_pin(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Kilitli", "avatar": "c:boss", "pin": "4321"})
        pid = created["profile_id"]
        status, reply = self.request("POST", "/api/profile/update", {"profile_id": pid, "pin": "REMOVE"})
        self.assertEqual(status, 403)
        self.assertTrue(reply["pin_required"])
        self.assertTrue(next(p for p in self.request("GET", "/api/profiles")[1]["profiles"] if p["id"] == pid)["has_pin"])
        status, _ = self.request("POST", "/api/profile/update", {"profile_id": pid, "name": "Kilitli2", "current_pin": "4321"})
        self.assertEqual(status, 200)

    def test_profile_name_must_have_two_characters_when_renamed(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Uzunca"})
        status, _ = self.request("POST", "/api/profile/update", {"profile_id": created["profile_id"], "name": "X"})
        self.assertEqual(status, 400)

    def test_workspace_can_start_from_a_template(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Atolye"})
        status, reply = self.request("POST", "/api/workspace/create", {"profile_id": created["profile_id"], "name": "Kedi", "template": "cat_library"})
        self.assertEqual(status, 200)
        self.assertEqual(sorted(reply["workspace"]["files"]), ["kedi.cpp", "kedi.h", "main.cpp"])
        projects = self.request("GET", f"/api/projects?profile_id={created['profile_id']}")[1]
        self.assertEqual(len(projects["projects"]), 8)
        self.assertTrue(projects["templates"])


if __name__ == "__main__":
    unittest.main()
