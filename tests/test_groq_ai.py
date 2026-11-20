import io
import json
import tempfile
import unittest
import urllib.error
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


class GroqTutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_dir = server.SECRETS_DIR
        server.SECRETS_DIR = Path(self.temp.name) / "secrets"

    def tearDown(self):
        server.SECRETS_DIR = self.old_dir
        self.temp.cleanup()

    def test_request_uses_free_gpt_oss_model_with_hidden_low_reasoning(self):
        seen = []

        def fake_urlopen(request, timeout=0):
            seen.append((request.full_url, dict((k.lower(), v) for k, v in request.header_items()), json.loads(request.data)))
            return FakeResponse({"model": "openai/gpt-oss-120b", "choices": [{"message": {"content": "cout satırında ; eksik."}}], "usage": {"prompt_tokens": 300, "completion_tokens": 80}})

        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_" + "x" * 40}), patch.object(server.urllib.request, "urlopen", fake_urlopen):
            answer = server.call_ai_provider("groq", "{}")
        url, headers, body = seen[0]
        self.assertEqual(url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(headers["authorization"], "Bearer gsk_" + "x" * 40)
        self.assertEqual(body["model"], "openai/gpt-oss-120b")
        self.assertEqual(body["reasoning_effort"], "low")
        self.assertIs(body["include_reasoning"], False)
        self.assertEqual(answer["text"], "cout satırında ; eksik.")
        self.assertEqual((answer["input_tokens"], answer["output_tokens"]), (300, 80))

    def test_rate_limit_falls_back_to_smaller_model_then_reports_without_raising(self):
        models = []

        def limited(request, timeout=0):
            models.append(json.loads(request.data)["model"])
            raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests", {}, io.BytesIO(b"{}"))

        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_" + "y" * 40}), patch.object(server.urllib.request, "urlopen", limited):
            answer = server.call_ai_provider("groq", "{}")
        self.assertEqual(models, ["openai/gpt-oss-120b", "openai/gpt-oss-20b"])
        self.assertIn("sınır", answer["error"])

    def test_key_is_validated_and_stored_outside_the_project(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
            with self.assertRaises(ValueError):
                server.save_provider_key("groq", "sk-ant-wrong-kind-of-key-000000000")
            server.save_provider_key("groq", "gsk_" + "z" * 40)
            self.assertEqual(server.provider_key("groq"), "gsk_" + "z" * 40)
            self.assertFalse((server.ROOT / "secrets").exists())
            server.save_provider_key("groq", "")
            self.assertEqual(server.provider_key("groq"), "")

    def test_missing_key_is_reported_as_unconfigured(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
            answer = server.call_ai_provider("groq", "{}")
        self.assertTrue(answer.get("unconfigured"))


if __name__ == "__main__":
    unittest.main()
