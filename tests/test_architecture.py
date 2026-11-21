"""Phase-4 structure: route tables, content index, and lookups that used to raise."""
import ast
import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

import content_index
import server

ROOT = Path(__file__).resolve().parents[1]


class RouteTableTests(unittest.TestCase):
    def test_every_route_points_at_an_existing_handler_method(self):
        for table, params in ((server.GET_ROUTES, 2), (server.POST_ROUTES, 3)):
            for path, name in table.items():
                self.assertTrue(path.startswith("/api/"), path)
                method = getattr(server.Handler, name, None)
                self.assertTrue(callable(method), f"{path} -> {name}")
                self.assertEqual(method.__code__.co_argcount, params, name)

    def test_no_route_if_chains_left_in_the_dispatchers(self):
        tree = ast.parse((ROOT / "server.py").read_text(encoding="utf-8"))
        handler = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Handler")
        for method in (m for m in handler.body if isinstance(m, ast.FunctionDef) and m.name in ("do_POST", "_route_get")):
            route_ifs = [n for n in ast.walk(method) if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name)
                         and n.left.id == "path" and isinstance(n.ops[0], ast.Eq) and isinstance(n.comparators[0], ast.Constant)
                         and str(n.comparators[0].value).startswith("/api/")]
            self.assertEqual(route_ifs, [], method.name)


class StrictScriptPolicyTests(unittest.TestCase):
    def test_csp_forbids_inline_scripts(self):
        script_src = next(part for part in server.CONTENT_SECURITY_POLICY.split(";") if part.strip().startswith("script-src"))
        self.assertNotIn("unsafe-inline", script_src)
        self.assertNotIn("unsafe-eval", script_src)

    def test_no_inline_scripts_or_event_attributes_in_the_shell_or_generated_markup(self):
        import re
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertNotRegex(page, r"<script(?![^>]*\bsrc=)[^>]*>")
        for path in [ROOT / "web" / "index.html", *(ROOT / "web").glob("*.js")]:
            self.assertIsNone(re.search(r"""\son[a-z]{3,20}=["'`$]""", path.read_text(encoding="utf-8")), path.name)


class ContentIndexTests(unittest.TestCase):
    def test_curriculum_invariants_hold(self):
        self.assertEqual(content_index.validate(), [])

    def test_lookups_match_the_curriculum(self):
        for chapter in server.CURRICULUM:
            self.assertEqual(content_index.boss_of(chapter["id"]), chapter["tasks"][-1]["id"])
            for task in chapter["tasks"]:
                self.assertIs(content_index.task(task["id"]), task)
                self.assertIs(content_index.chapter_of(task["id"]), chapter)
        self.assertIsNone(content_index.task("no-such-task"))

    def test_validation_reports_a_missing_boss(self):
        broken = [{"id": "x1", "tasks": [{"id": "t1", "kind": "quiz"}], "prerequisites": ["nope"]}]
        errors = content_index.validate(broken)
        self.assertTrue(any("boss" in e for e in errors))
        self.assertTrue(any("unknown prerequisite" in e for e in errors))


class StaleContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old = server.DB_PATH
        server.DB_PATH = Path(cls.temp.name) / "arch.db"
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.DB_PATH = cls.old
        cls.temp.cleanup()

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.http.server_address[1], timeout=30)
        conn.request(method, path, json.dumps(data).encode() if data is not None else None, {"Content-Type": "application/json"} if data is not None else {})
        response = conn.getresponse()
        result = response.status, json.loads(response.read())
        conn.close()
        return result

    def test_daily_quest_pointing_at_removed_content_does_not_break_state(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Eski"})
        pid = created["profile_id"]
        with server.db() as con:
            con.execute("INSERT INTO daily_quests(profile_id,day,task_id) VALUES(?,?,?)", (pid, time.strftime("%Y-%m-%d"), "removed-task"))
        status, state = self.request("GET", f"/api/state?profile_id={pid}")
        self.assertEqual(status, 200, state)
        self.assertIn(state["profile"]["daily_quest"]["task_id"], content_index.TASK_BY_ID)

    def test_unknown_api_paths_answer_in_json(self):
        self.assertEqual(self.request("GET", "/api/does-not-exist"), (404, {"error": "Bilinmeyen uç nokta. / Неизвестный адрес API."}))


if __name__ == "__main__":
    unittest.main()
