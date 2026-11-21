"""Regression tests for the Phase-1 critical bugs found in the 2026-11 audit.

Each test reproduces one verified defect; see DEVELOPMENT_LOG.md for details.
"""
import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Phase1RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db, cls.old_root = server.DB_PATH, server.DATA_ROOT
        server.DB_PATH = Path(cls.temp.name) / "phase1.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.DB_PATH, server.DATA_ROOT = cls.old_db, cls.old_root
        cls.temp.cleanup()

    def request(self, method, path, data=None, raw_body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        body = raw_body if raw_body is not None else (json.dumps(data, ensure_ascii=False).encode() if data is not None else None)
        hdrs = {"Content-Type": "application/json"} if body is not None else {}
        hdrs.update(headers or {})
        conn.request(method, path, body, hdrs)
        response = conn.getresponse()
        status, payload = response.status, json.loads(response.read() or b"null")
        conn.close()
        return status, payload

    def make_profile(self, name="Tester", pin=""):
        status, created = self.request("POST", "/api/profiles", {"name": name, "pin": pin, "lang": "tr"})
        self.assertEqual(status, 200, created)
        return created["profile_id"]

    # 1. server.py:1787 mis-indented return made every later POST route unreachable.
    def test_unknown_post_route_returns_404_not_500(self):
        status, result = self.request("POST", "/api/does-not-exist", {})
        self.assertEqual(status, 404, result)

    def test_vscode_read_route_is_reachable(self):
        status, result = self.request("POST", "/api/vscode/read", {})
        self.assertEqual(status, 404, result)  # "open the file in VS Code first", not a 500 crash
        self.assertNotIn("reward", result.get("error", ""))

    # 2. do_GET had no error handling: a bad export id dropped the connection.
    def test_get_errors_return_json_instead_of_dropping_connection(self):
        status, result = self.request("GET", "/api/export?profile_id=missing")
        self.assertEqual(status, 400)
        self.assertIn("error", result)

    # 3. read_json accepted non-object bodies and negative Content-Length.
    def test_non_object_json_body_is_a_400(self):
        status, result = self.request("POST", "/api/select", raw_body=b"[1,2]")
        self.assertEqual(status, 400, result)

    def test_negative_content_length_is_rejected_quickly(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.putrequest("POST", "/api/select")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Content-Length", "-1")
        conn.endheaders()
        response = conn.getresponse()
        self.assertEqual(response.status, 400)
        conn.close()

    # 4. Restoring a realistic save failed: every request was capped at 30 KB.
    def test_import_accepts_saves_larger_than_30kb(self):
        pid = self.make_profile("BigSave")
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        save["profile"]["portfolio_notes"] = [{"project_id": "x", "description": "d" * 50_000, "technologies": ""}]
        status, result = self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        self.assertNotEqual(result.get("error"), "İstek çok büyük.")
        self.assertEqual(status, 200, result)

    # 5. Import overwrote PIN-protected profiles without asking for the PIN.
    def test_import_requires_pin_for_protected_profile(self):
        pid = self.make_profile("Locked", pin="4321")
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        status, _ = self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        self.assertEqual(status, 403)
        status, result = self.request("POST", "/api/import", {"profile_id": pid, "save": save, "pin": "4321"})
        self.assertEqual(status, 200, result)

    # 6. Profile update wrote name/avatar, then returned 400 for a bad PIN — and committed.
    def test_profile_update_with_invalid_pin_changes_nothing(self):
        pid = self.make_profile("Before")
        status, _ = self.request("POST", "/api/profile/update", {"profile_id": pid, "name": "After", "pin": "12"})
        self.assertEqual(status, 400)
        _, listing = self.request("GET", "/api/profiles")
        name = next(p["name"] for p in listing["profiles"] if p["id"] == pid)
        self.assertEqual(name, "Before")

    # 7. Daily bonus was credited for an already-completed task but reported as 0.
    def test_daily_bonus_is_reported_when_credited(self):
        pid = self.make_profile("Daily")
        quiz = next(t for c in server.CURRICULUM for t in c["tasks"] if t["kind"] == "quiz" and isinstance(t["answer"], str))
        today = time.strftime("%Y-%m-%d")
        with server.db() as con:
            con.execute("INSERT INTO completions(profile_id,task_id,xp) VALUES(?,?,?)", (pid, quiz["id"], quiz["xp"]))
            con.execute("INSERT OR REPLACE INTO daily_quests(profile_id,day,task_id,reward) VALUES(?,?,?,15)", (pid, today, quiz["id"]))
            before = con.execute("SELECT xp FROM profiles WHERE id=?", (pid,)).fetchone()[0]
        status, result = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": quiz["id"], "answer": quiz["answer"]})
        self.assertEqual(status, 200, result)
        with server.db() as con:
            after = con.execute("SELECT xp FROM profiles WHERE id=?", (pid,)).fetchone()[0]
        self.assertEqual(after - before, result["xp"] + result["daily_bonus"])
        self.assertEqual(result["daily_bonus"], 15)

    # 8. Read-then-award paths could double-credit under concurrent requests.
    def test_immediate_transactions_serialize_read_then_award(self):
        pid = self.make_profile("Race")
        barrier = threading.Barrier(2)

        def award_once():
            barrier.wait()
            with server.db(immediate=True) as con:
                xp = con.execute("SELECT xp FROM profiles WHERE id=?", (pid,)).fetchone()[0]
                time.sleep(0.2)
                if xp == 0:
                    con.execute("UPDATE profiles SET xp=xp+100 WHERE id=?", (pid,))

        workers = [threading.Thread(target=award_once) for _ in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        with server.db() as con:
            self.assertEqual(con.execute("SELECT xp FROM profiles WHERE id=?", (pid,)).fetchone()[0], 100)

    # 9. The XP/level test panel shipped enabled.
    def test_admin_panel_is_off_unless_explicitly_enabled(self):
        self.assertFalse(server.admin_enabled_from_env({}))
        self.assertFalse(server.admin_enabled_from_env({"CPP_ADVENTURE_ADMIN": "0"}))
        self.assertTrue(server.admin_enabled_from_env({"CPP_ADVENTURE_ADMIN": "1"}))

    # 10. claude-haiku-5-5 rejects non-default temperature with HTTP 400.
    def test_claude_payload_uses_supported_parameters(self):
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["body"] = json.loads(request.data)
            return FakeResponse({"model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": "İpucu"}], "usage": {"input_tokens": 1, "output_tokens": 1}})

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-0000000000000000000000"}), patch.object(server.urllib.request, "urlopen", fake_urlopen):
            answer = server.call_ai_provider("claude", "{}")
        body = captured["body"]
        for sampling in ("temperature", "top_p", "top_k"):
            self.assertNotIn(sampling, body)
        self.assertEqual(body["output_config"], {"effort": "low"})
        self.assertEqual(body["thinking"], {"type": "disabled"})
        self.assertEqual(answer["text"], "İpucu")

    def test_claude_refusal_and_empty_truncation_are_errors(self):
        for stop_reason, content in (("refusal", []), ("max_tokens", [])):
            def fake_urlopen(request, timeout=0, _s=stop_reason, _c=content):
                return FakeResponse({"model": "claude-haiku-5-5", "stop_reason": _s, "content": _c, "usage": {}})

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-0000000000000000000000"}), patch.object(server.urllib.request, "urlopen", fake_urlopen):
                answer = server.call_ai_provider("claude", "{}")
            self.assertIn("error", answer, stop_reason)


if __name__ == "__main__":
    unittest.main()
