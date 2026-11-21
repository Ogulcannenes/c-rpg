import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

import server


class LocalApiGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls._saved_paths = (server.DB_PATH, server.DATA_ROOT)  # backups/logs must not land in the repo
        server.DB_PATH = Path(cls.temp.name) / "test.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        server.DB_PATH, server.DATA_ROOT = cls._saved_paths
        cls.http.shutdown()
        cls.http.server_close()
        cls.temp.cleanup()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        conn.request(method, path, body, headers or {})
        response = conn.getresponse()
        response.read()
        status = response.status
        conn.close()
        return status

    def test_same_origin_requests_are_allowed(self):
        self.assertEqual(self.call("GET", "/api/meta"), 200)
        origin = f"http://127.0.0.1:{self.port}"
        status = self.call("POST", "/api/profiles", json.dumps({"name": "Test"}), {"Content-Type": "application/json", "Origin": origin})
        self.assertNotEqual(status, 403)

    def test_foreign_host_header_is_rejected(self):
        self.assertEqual(self.call("GET", "/api/meta", headers={"Host": "evil.example:8765"}), 403)

    def test_cross_origin_post_is_rejected(self):
        headers = {"Content-Type": "application/json", "Origin": "https://evil.example"}
        self.assertEqual(self.call("POST", "/api/compile", "{}", headers), 403)

    def test_null_origin_and_cross_site_fetch_are_rejected(self):
        self.assertEqual(self.call("POST", "/api/compile", "{}", {"Content-Type": "application/json", "Origin": "null"}), 403)
        self.assertEqual(self.call("GET", "/api/meta", headers={"Sec-Fetch-Site": "cross-site"}), 403)

    def test_post_without_json_content_type_is_rejected(self):
        self.assertEqual(self.call("POST", "/api/compile", "{}", {"Content-Type": "text/plain"}), 403)
        self.assertEqual(self.call("POST", "/api/compile", "{}"), 403)


@unittest.skipUnless(server.COMPILER, "C++ compiler is required")
class ProgramLimitTests(unittest.TestCase):
    def test_runaway_output_is_stopped(self):
        source = '#include <iostream>\nint main(){while(true) std::cout << "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";}'
        result = server.compile_and_run(source)
        self.assertFalse(result["ok"])
        self.assertEqual(result["phase"], "output_limit")

    def test_crlf_and_trailing_spaces_do_not_fail_comparison(self):
        self.assertEqual(server.normalize_output("1 2 3 \r\n"), server.normalize_output("1 2 3"))
        self.assertEqual(server.normalize_output("a  \r\nb\r\n"), "a\nb")
        self.assertNotEqual(server.normalize_output("1 2"), server.normalize_output("1  2"))

    def test_compiler_warnings_are_reported(self):
        result = server.compile_and_run("int main(){int unused; return 0;}")
        self.assertTrue(result["ok"])
        self.assertIn("warning", result["compile_output"])

    def test_quiz_answers_forgive_case_diacritics_and_std_prefix(self):
        norm = server.normalize_answer
        self.assertEqual(norm("Çarpma"), norm("carpma"))
        self.assertEqual(norm("  Küçükten   büyüğe "), norm("kucukten buyuge"))
        self.assertEqual(norm("std::map"), norm("map"))
        self.assertNotEqual(norm("main"), norm("mail"))

    def test_normal_program_still_runs_with_input(self):
        result = server.compile_and_run('#include <iostream>\nint main(){int n; std::cin >> n; std::cout << n * 2;}', "21")
        self.assertTrue(result["ok"])
        self.assertEqual(result["output"], "42")


if __name__ == "__main__":
    unittest.main()
