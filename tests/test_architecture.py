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


class FrontendHookTests(unittest.TestCase):
    """Phase 5: feature modules extend app.js through core.js hooks instead of reassigning globals."""

    @classmethod
    def setUpClass(cls):
        import re
        cls.web = ROOT / "web"
        app = (cls.web / "app.js").read_text(encoding="utf-8")
        cls.installed = set(re.findall(r"'([A-Za-z]+)'", re.search(r"App\.install\(\[([^\]]*)\]\)", app).group(1)))

    def test_core_loads_before_app_and_every_module(self):
        import re
        order = re.findall(r'<script src="/([^"]+)"', (self.web / "index.html").read_text(encoding="utf-8"))
        self.assertLess(order.index("core.js"), order.index("app.js"))
        self.assertEqual(order.index("core.js"), min(i for i, name in enumerate(order) if not name.startswith(("vendor/", "monaco-boot"))))

    def test_hooks_target_installed_extension_points_and_nothing_reassigns_them(self):
        import re
        for path in self.web.glob("*.js"):
            if path.name in ("core.js", "app.js"):
                continue
            source = path.read_text(encoding="utf-8")
            for name in re.findall(r"App\.(?:before|after)\('([A-Za-z]+)'", source):
                self.assertIn(name, self.installed, f"{path.name} hooks {name}, which app.js does not install")
            for name in self.installed:
                self.assertNotRegex(source, rf"(?:window\.)?\b{name}\s*=\s*(?:async\s*)?(?:function|\()", f"{path.name} reassigns {name}")

    def test_core_hook_semantics_in_node(self):
        import shutil
        import subprocess
        node = shutil.which("node") or (r"C:\Program Files\nodejs\node.exe" if Path(r"C:\Program Files\nodejs\node.exe").exists() else None)
        if not node:
            self.skipTest("node is not installed")
        script = (self.web / "core.js").read_text(encoding="utf-8") + r"""
const log = [];
window.render = function (x) { log.push('core:' + x); return x * 2; };
window.load = async function () { log.push('core-async'); return 'v'; };
App.before('render', ([x]) => log.push('before:' + x));
App.after('render', ([x], out) => log.push('after:' + out));
App.after('render', () => { throw new Error('broken hook'); });
App.after('render', () => log.push('still-runs'));
App.after('load', async (args, value) => { await null; log.push('after-async:' + value); });
App.install(['render', 'load', 'missing']);
App.install(['render']);  // idempotent
const out = window.render(3);
window.load().then(v => { log.push('resolved:' + v); console.log(JSON.stringify({out, log, esc: App.esc(`<a href="x">'&`)})); });
"""
        result = subprocess.run([node, "-e", "const window = globalThis; const console_error = console.error; console.error = () => {};\n" + script],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(data["out"], 6)
        self.assertEqual(data["log"], ["before:3", "core:3", "after:6", "still-runs", "core-async", "after-async:v", "resolved:v"])
        self.assertEqual(data["esc"], "&lt;a href=&quot;x&quot;&gt;&#39;&amp;")


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
        cls._saved_paths = (server.DB_PATH, server.DATA_ROOT)  # backups/logs must not land in the repo
        server.DB_PATH = Path(cls.temp.name) / "arch.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        server.DB_PATH, server.DATA_ROOT = cls._saved_paths
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
        # Phase 10: the bilingual message is also split into error_tr / error_ru for the page.
        self.assertEqual(self.request("GET", "/api/does-not-exist"), (404, {"error": "Bilinmeyen uç nokta. / Неизвестный адрес API.",
                                                                           "error_tr": "Bilinmeyen uç nokta.", "error_ru": "Неизвестный адрес API."}))


if __name__ == "__main__":
    unittest.main()
