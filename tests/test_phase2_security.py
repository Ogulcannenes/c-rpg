"""Phase-2 security: per-launch API session, PIN locks, headers, input validation, secrets."""
import http.client
import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path

import secret_store
import server

ROOT = Path(__file__).resolve().parents[1]


class _ServerCase(unittest.TestCase):
    app_server = False

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db = server.DB_PATH
        cls._saved_paths = (server.DB_PATH, server.DATA_ROOT)  # backups/logs must not land in the repo
        server.DB_PATH = Path(cls.temp.name) / "phase2.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        if cls.app_server:
            cls.http, cls.auth, cls.start_url = server.create_app_server(0)
        else:
            cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        server.DB_PATH, server.DATA_ROOT = cls._saved_paths
        cls.http.shutdown()
        cls.http.server_close()
        server.DB_PATH = cls.old_db
        cls.temp.cleanup()

    def raw(self, method, path, data=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        body = json.dumps(data).encode() if data is not None else None
        hdrs = {"Content-Type": "application/json"} if body is not None else {}
        hdrs.update(headers or {})
        conn.request(method, path, body, hdrs)
        response = conn.getresponse()
        payload = response.read()
        conn.close()
        return response, payload

    def request(self, method, path, data=None, headers=None):
        response, payload = self.raw(method, path, data, headers)
        try:
            return response.status, json.loads(payload or b"null")
        except ValueError:
            return response.status, payload


class LaunchSessionTests(_ServerCase):
    app_server = True

    def test_api_requires_the_launch_session(self):
        self.assertEqual(self.request("GET", "/api/meta")[0], 401)
        self.assertEqual(self.request("POST", "/api/run", {"code": "int main(){}"})[0], 401)
        self.assertEqual(self.request("GET", "/api/meta", headers={"Cookie": f"cppadv_session_{self.port}=forged"})[0], 401)

    def test_bootstrap_code_works_once_and_grants_access(self):
        code = self.auth.new_bootstrap_code()
        first, _ = self.raw("GET", f"/__session?code={code}")
        self.assertEqual(first.status, 302)
        cookie_header = first.getheader("Set-Cookie")
        self.assertIn("HttpOnly", cookie_header)
        self.assertIn("SameSite=Strict", cookie_header)
        second, _ = self.raw("GET", f"/__session?code={code}")
        self.assertEqual(second.status, 403)
        cookie = cookie_header.split(";", 1)[0]
        status, meta = self.request("GET", "/api/meta", headers={"Cookie": cookie})
        self.assertEqual(status, 200, meta)

    def test_static_shell_loads_without_session_and_token_is_not_in_page(self):
        response, page = self.raw("GET", "/")
        self.assertEqual(response.status, 200)
        self.assertNotIn(self.auth.token.encode(), page)

    def test_start_url_points_at_the_bootstrap_route(self):
        self.assertRegex(self.start_url, rf"^http://127\.0\.0\.1:{self.port}/__session\?code=")


class HeaderAndPinTests(_ServerCase):
    def test_security_headers_on_json_and_static_responses(self):
        for path in ("/api/meta", "/"):
            response, _ = self.raw("GET", path)
            csp = response.getheader("Content-Security-Policy") or ""
            self.assertIn("default-src 'self'", csp)
            self.assertIn("object-src 'none'", csp)
            self.assertIn("frame-ancestors 'none'", csp)
            self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")

    def create(self, name, pin=""):
        status, created = self.request("POST", "/api/profiles", {"name": name, "pin": pin})
        self.assertEqual(status, 200, created)
        return created["profile_id"]

    def test_locked_profile_needs_pin_on_every_endpoint_until_selected(self):
        pid = self.create("Kilit", "1357")
        for method, path, body in (("GET", f"/api/state?profile_id={pid}", None), ("GET", f"/api/export?profile_id={pid}", None),
                                   ("POST", "/api/settings", {"profile_id": pid, "lang": "ru"}), ("POST", "/api/shop/buy", {"profile_id": pid, "item_id": "bow"})):
            status, reply = self.request(method, path, body)
            self.assertEqual(status, 403, path)
            self.assertTrue(reply["pin_required"])
        self.assertEqual(self.request("POST", "/api/select", {"profile_id": pid, "pin": "1357"})[0], 200)
        self.assertEqual(self.request("GET", f"/api/state?profile_id={pid}")[0], 200)

    def test_selecting_another_profile_locks_the_previous_one(self):
        locked, other = self.create("Birinci", "2468"), self.create("Ikinci")
        self.request("POST", "/api/select", {"profile_id": locked, "pin": "2468"})
        self.request("POST", "/api/select", {"profile_id": other, "pin": ""})
        self.assertEqual(self.request("GET", f"/api/state?profile_id={locked}")[0], 403)
        self.assertEqual(self.request("GET", f"/api/state?profile_id={other}")[0], 200)

    def test_profiles_without_pin_are_not_affected(self):
        pid = self.create("Acik")
        self.assertEqual(self.request("GET", f"/api/state?profile_id={pid}")[0], 200)

    def test_profile_names_reject_markup_but_accept_turkish_and_cyrillic(self):
        self.assertEqual(self.request("POST", "/api/profiles", {"name": '"><img src=x onerror=alert(1)>'})[0], 400)
        self.assertEqual(self.request("POST", "/api/profiles", {"name": "Ölçü Şeyma"})[0], 200)
        self.assertEqual(self.request("POST", "/api/profiles", {"name": "Дмитрий"})[0], 200)

    def test_import_clamps_untrusted_numbers(self):
        pid = self.create("Clamp")
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        task = server.all_tasks()[0]
        lab = server.LABS[0]
        save["profile"].update({"xp": 10**12, "streak": -5, "last_day": "not-a-day",
                                "completed": [{"task_id": task["id"], "xp": 999999}],
                                "lab_awards": [{"lab_id": lab["id"], "xp": 999999}],
                                "interview_sessions": [{"session_id": "a" * 32, "lang": "ru", "questions_json": "[]", "answers_json": json.dumps([{"x": "y" * 50000}] * 3), "started_at": "restored"}]})
        status, result = self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        self.assertEqual(status, 200, result)
        with server.db() as con:
            profile = con.execute("SELECT xp,streak,last_day FROM profiles WHERE id=?", (pid,)).fetchone()
            completion_xp = con.execute("SELECT xp FROM completions WHERE profile_id=?", (pid,)).fetchone()[0]
            lab_xp = con.execute("SELECT xp FROM lab_awards WHERE profile_id=?", (pid,)).fetchone()[0]
            answers = con.execute("SELECT answers_json FROM interview_sessions WHERE profile_id=?", (pid,)).fetchone()[0]
        self.assertEqual((profile["xp"], profile["streak"], profile["last_day"]), (server.MAX_IMPORTED_XP, 0, ""))
        self.assertEqual(completion_xp, task["xp"])
        self.assertEqual(lab_xp, lab["xp"])
        self.assertEqual(json.loads(answers), [])  # valid JSON, no oversized junk
        self.assertEqual(self.request("GET", f"/api/career?profile_id={pid}")[0], 200)


class SecretStoreTests(unittest.TestCase):
    def test_secret_round_trips_and_is_not_plaintext_on_windows(self):
        with tempfile.TemporaryDirectory() as folder:
            secret_store.write_secret(Path(folder), "groq_api_key", "gsk_" + "x" * 40)
            self.assertEqual(secret_store.read_secret(Path(folder), "groq_api_key"), "gsk_" + "x" * 40)
            if os.name == "nt":
                stored = (Path(folder) / "groq_api_key.dpapi").read_bytes()
                self.assertNotIn(b"gsk_", stored)
                self.assertFalse((Path(folder) / "groq_api_key").exists())
            secret_store.delete_secret(Path(folder), "groq_api_key")
            self.assertEqual(secret_store.read_secret(Path(folder), "groq_api_key"), "")

    @unittest.skipUnless(os.name == "nt", "DPAPI migration is Windows-only")
    def test_legacy_plaintext_key_is_migrated_to_dpapi(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "anthropic_api_key").write_text("sk-ant-legacy-" + "y" * 30, encoding="utf-8")
            self.assertEqual(secret_store.read_secret(Path(folder), "anthropic_api_key"), "sk-ant-legacy-" + "y" * 30)
            self.assertFalse((Path(folder) / "anthropic_api_key").exists())
            self.assertTrue((Path(folder) / "anthropic_api_key.dpapi").exists())


class FrontendTranslationCollisionTests(unittest.TestCase):
    def test_dynamic_markup_never_uses_the_translation_attribute(self):
        """app.js rewrites the text of every [data-i] element on language change; index attributes
        named data-i wiped the onboarding character cards (found in the Phase 2 browser check)."""
        for path in (ROOT / "web").glob("*.js"):
            source = path.read_text(encoding="utf-8")
            self.assertNotRegex(source, r'data-i="\$\{', path.name)


class FrontendXssTests(unittest.TestCase):
    def test_cat_companion_label_is_escaped(self):
        source = (ROOT / "web" / "cat-companion-ui.js").read_text(encoding="utf-8")
        self.assertIn('aria-label="${escAttr(label)}"', source)
        self.assertNotRegex(source, re.escape('aria-label="${label}"'))


if __name__ == "__main__":
    unittest.main()
