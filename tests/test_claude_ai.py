import http.client
import json
import tempfile
import threading
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


class ClaudeTutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(cls.temp.name) / "claude.db"
        cls.old_dir, cls.old_file = server.SECRETS_DIR, server.CLAUDE_KEY_FILE
        server.SECRETS_DIR = Path(cls.temp.name) / "secrets"
        server.CLAUDE_KEY_FILE = server.SECRETS_DIR / "anthropic_api_key"
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.SECRETS_DIR, server.CLAUDE_KEY_FILE = cls.old_dir, cls.old_file
        cls.temp.cleanup()

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        conn.request(method, path, json.dumps(data).encode() if data is not None else None, {"Content-Type": "application/json"} if data is not None else {})
        response = conn.getresponse()
        result = json.loads(response.read())
        conn.close()
        return response.status, result

    def test_default_model_is_the_small_haiku_model(self):
        self.assertEqual(server.CLAUDE_MODEL, "claude-haiku-5-5")
        self.assertIn(server.CLAUDE_MODEL, server.CLAUDE_PRICES)

    def test_messages_api_request_and_response_parsing(self):
        captured = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            captured["headers"] = {k.lower(): v for k, v in request.header_items()}
            captured["body"] = json.loads(request.data)
            return FakeResponse({"model": "claude-haiku-5-5", "content": [{"type": "text", "text": "Noktalı virgül eksik."}], "usage": {"input_tokens": 120, "output_tokens": 30}})

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-0000000000000000000000"}), patch.object(server.urllib.request, "urlopen", fake_urlopen):
            answer = server.call_ai_provider("claude", "{}")
        self.assertEqual(captured["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(captured["headers"]["anthropic-version"], "2023-06-01")
        self.assertEqual(captured["body"]["model"], "claude-haiku-5-5")
        self.assertLessEqual(captured["body"]["max_tokens"], 500)
        self.assertEqual(answer["text"], "Noktalı virgül eksik.")
        self.assertEqual((answer["input_tokens"], answer["output_tokens"]), (120, 30))

    def test_key_is_stored_outside_the_database_and_never_returned(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Claude"})
        pid = created["profile_id"]
        status, _ = self.request("POST", "/api/ai/claude-key", {"profile_id": pid, "key": "not-a-key"})
        self.assertEqual(status, 400)
        key = "sk-ant-api03-" + "a" * 40 + "WXYZ"
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
            status, saved = self.request("POST", "/api/ai/claude-key", {"profile_id": pid, "key": key})
            self.assertEqual(status, 200)
            self.assertTrue(saved["claude_configured"])
            _, info = self.request("GET", f"/api/ai/status?profile_id={pid}")
            self.assertEqual(info["provider"], "claude")
            self.assertTrue(info["claude_configured"])
            self.assertNotIn(key, json.dumps(info))
            self.assertEqual(info["claude_key_hint"], "…WXYZ")
            self.assertEqual(server.CLAUDE_KEY_FILE.read_text(encoding="utf-8"), key)
            self.assertNotIn(key.encode(), server.DB_PATH.read_bytes())
            status, removed = self.request("POST", "/api/ai/claude-key", {"profile_id": pid, "key": ""})
            self.assertFalse(removed["claude_configured"])

    def test_claude_review_requires_consent(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Consent"})
        pid = created["profile_id"]
        self.request("POST", "/api/settings", {"profile_id": pid, "ai_provider": "claude"})
        task = server.all_tasks()[0]
        status, data = self.request("POST", "/api/ai/diagnose", {"profile_id": pid, "task_id": task["id"], "code": "int main(){}"})
        self.assertEqual(status, 403)
        self.assertTrue(data.get("consent_required"))


if __name__ == "__main__":
    unittest.main()
