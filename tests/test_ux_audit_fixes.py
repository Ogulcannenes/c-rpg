"""Fixes from the 2026-11-21 UI/UX, accessibility and code review audit (docs/UX_AUDIT.md)."""
import http.client
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import db_migrations
import server

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
# Passes the visible example (21 -> 42) but not the hidden cases (-4, 0).
HALF_RIGHT = "#include <iostream>\nint main(){int n;std::cin>>n;if(n==21)std::cout<<42;else std::cout<<7;}"


class ServerFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.saved = server.DB_PATH, server.DATA_ROOT
        server.DB_PATH = Path(cls.temp.name) / "audit.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.DB_PATH, server.DATA_ROOT = cls.saved
        cls.temp.cleanup()

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        body = json.dumps(data).encode() if data is not None else None
        conn.request(method, path, body, {"Content-Type": "application/json"} if body else {})
        response = conn.getresponse()
        status, payload = response.status, json.loads(response.read() or b"null")
        conn.close()
        return status, payload

    def profile(self, name):
        return self.request("POST", "/api/profiles", {"name": name})[1]["profile_id"]

    @unittest.skipUnless(server.COMPILER, "a C++ compiler is required")
    def test_failing_hidden_tests_do_not_reveal_their_input_or_expected_output(self):
        pid = self.profile("Leak Check")
        con = sqlite3.connect(server.DB_PATH)
        try:
            with con:  # unlock chapter 3 (its prerequisites' bosses are done)
                for boss in ("c01-boss", "c02-boss"):
                    con.execute("INSERT INTO completions(profile_id,task_id,xp) VALUES(?,?,0)", (pid, boss))
        finally:
            con.close()
        _, submitted = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c03-04", "answer": HALF_RIGHT})
        self.assertFalse(submitted["correct"])
        checks = submitted["result"]["checks"]
        self.assertEqual(checks[0]["expected"], "42", "the visible example may be shown")
        self.assertTrue(checks[1]["hidden"])
        self.assertNotIn("expected", checks[1])
        _, diagnosed = self.request("POST", "/api/ai/diagnose", {"profile_id": pid, "task_id": "c03-04", "code": HALF_RIGHT, "lang": "tr"})
        diag = diagnosed["diagnostic"]
        self.assertEqual((diag["kind"], diag["test"], diag.get("hidden")), ("output", 2, True))
        self.assertNotIn("expected", diag)
        self.assertNotIn("input", diag)

    def test_import_keeps_a_verified_copy_of_the_database_first(self):
        pid = self.profile("Restorer")
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        backups = Path(server.DATA_ROOT) / "backups"
        before = set(backups.glob("adventure-before-import-*.db")) if backups.exists() else set()
        status, result = self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        self.assertEqual(status, 200, result)
        created = set(backups.glob("adventure-before-import-*.db")) - before
        self.assertEqual(len(created), 1)
        copy = created.pop()
        self.assertFalse(Path(str(copy) + "-wal").exists(), "a backup is one self-contained file")
        con = sqlite3.connect(copy)
        try:
            self.assertEqual(con.execute("PRAGMA journal_mode").fetchone()[0], "delete")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM profiles WHERE id=?", (pid,)).fetchone()[0], 1)
        finally:
            con.close()

    def test_malformed_save_lists_are_rejected_as_bad_requests(self):
        pid = self.profile("Bad Save")
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        for field, bad in (("completed", ["not-an-object"]), ("arena_attempts", [1, 2]), ("study_sessions", "x"), ("equipped_items", [])):
            broken = json.loads(json.dumps(save))
            broken["profile"][field] = bad
            status, result = self.request("POST", "/api/import", {"profile_id": pid, "save": broken})
            self.assertEqual(status, 400, (field, result))
            self.assertEqual(result.get("error_code"), "backup_format_unsupported")

    def test_unexpected_errors_are_logged_and_hide_internals(self):
        with patch.object(server.Handler, "_get_shop", side_effect=RuntimeError("secret path C:\\Users\\x")):
            status, result = self.request("GET", "/api/shop")
        self.assertEqual(status, 500)
        self.assertEqual(result["error_code"], "internal_error")
        self.assertNotIn("secret path", result["error"])
        log = (Path(server.DATA_ROOT) / "logs" / "server-errors.log").read_text(encoding="utf-8")
        self.assertIn(result["incident"], log)
        self.assertIn("RuntimeError", log)


class BackupPathTests(unittest.TestCase):
    def test_backup_works_with_url_special_characters_in_the_path(self):
        with tempfile.TemporaryDirectory() as folder:
            odd = Path(folder) / "C# 100% &x"  # "?" is not a valid Windows file name character
            odd.mkdir()
            db = odd / "live.db"
            con = sqlite3.connect(db)
            try:
                with con:
                    con.execute("PRAGMA journal_mode=WAL")
                    con.execute("CREATE TABLE t(x)")
                    con.execute("INSERT INTO t VALUES(1)")
            finally:
                con.close()
            copy = db_migrations.backup_database(db, odd / "backups", "test")
            check = sqlite3.connect(copy)
            try:
                self.assertEqual(check.execute("SELECT x FROM t").fetchall(), [(1,)])
                self.assertEqual(check.execute("PRAGMA journal_mode").fetchone()[0], "delete")
            finally:
                check.close()


class EnglishTaskOutputTests(unittest.TestCase):
    """Owner's request: task prompts are Turkish/Russian, but what a program must print is English."""
    TURKISH_WORDS = {"merhaba", "gecti", "kaldi", "tekrar", "miyav", "kedi", "yok", "usta", "gezgin", "cirak",
                     "tamam", "acik", "sicak", "soguk", "ilik", "hata", "puan", "macera", "yakalandi", "negatif",
                     "mama", "kus", "ari", "gri", "pati9"}

    def test_every_expected_program_output_is_english_ascii(self):
        problems = []
        for task in server.content_index.TASKS:
            if task["kind"] == "predict":
                answer = task["answer"]
                outputs = [answer if isinstance(answer, str) else answer.get("tr", "")]
            elif task["kind"] in ("code", "fix", "boss"):
                outputs = [case["expected"] for case in task.get("tests", [])]
            else:
                continue
            for output in outputs:
                words = {w.lower() for w in re.findall(r"[^\W\d_]+", output)}
                if any(ord(ch) > 127 for ch in output) or words & self.TURKISH_WORDS:
                    problems.append((task["id"], output))
        self.assertEqual(problems, [])


class FrontEndFixTests(unittest.TestCase):
    def test_no_text_smaller_than_11px_in_app_styles(self):
        # Both font-size and the font: shorthand ("font:600 10px var(--mono)").
        tiny = re.compile(r"font(?:-size)?:[^;}]*?(\d+(?:\.\d+)?)px")
        offenders = []
        for css in WEB.glob("*.css"):
            for size in tiny.findall(css.read_text(encoding="utf-8")):
                if float(size) < 11:
                    offenders.append((css.name, size))
        self.assertEqual(offenders, [])

    def test_lesson_and_keyboard_fixes_are_in_place(self):
        app = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("${tr('locked')} · ${appState.profile.xp} XP", app, "chapter 1 said 'complete the previous boss'")
        self.assertIn("${tr('taskOrder')}", app)
        self.assertEqual(app.count("ariaLabel:codeEditorLabel()"), 2)
        self.assertIn('aria-current="step"', app)
        self.assertNotIn("setTimeout(()=>el.classList.remove('show'),2500)", app)
        theme = (WEB / "theme.css").read_text(encoding="utf-8")
        self.assertIn(".achievement-card.locked :is(h3, p) { opacity: 1;", theme)
        self.assertIn(".lesson-cat-card { align-self: start;", theme)
        self.assertIn(".editor-actions { position: sticky;", theme)
        index = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertLess(index.index("/app.js"), index.index("/ux-a11y.js"))
        self.assertIn('data-i-aria="profilesTitle"', index)
        locales = json.loads((WEB / "locales.json").read_text(encoding="utf-8"))
        for key in ("taskOrder", "appearance", "textSize", "reduceMotion"):
            self.assertTrue(locales["tr"][key] and locales["ru"][key], key)
        self.assertEqual(locales["tr"]["boss"], "Bölüm Boss'u")
        self.assertEqual(locales["tr"]["taskTypes"]["boss"], "Bölüm Boss'u")
        for module in ("arena-ui.js", "career-ui.js", "project-workshop.js"):
            self.assertIn("ariaLabel:", (WEB / module).read_text(encoding="utf-8"), module)
        for module in ("motion.js", "advanced-cpp-ui.js", "lab-theater.js", "lesson-scenes.js", "onboarding.js", "rpg-ui.js"):
            self.assertIn("classList.contains('reduce-motion')", (WEB / module).read_text(encoding="utf-8"), module)
        self.assertIn("renderSettings(){if(!profileId||!appState)return toast(L('ui.app.profileRequired'));setView('settings')", app)

    def test_text_size_and_view_focus_behave(self):
        node = shutil.which("node") or (r"C:\Program Files\nodejs\node.exe" if Path(r"C:\Program Files\nodejs\node.exe").exists() else None)
        if not node:
            self.skipTest("node is not installed")
        harness = r"""
const store = {}; const listeners = []; const hooks = {}; let focused = null; const timers = [];
global.window = global;
global.localStorage = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
global.setTimeout = f => timers.push(f);
const heading = { tabIndex: 0, focus() { focused = 'h1'; } };
const view = { querySelector: s => (s === 'h1' ? heading : null), contains: () => false };
const classes = new Set();
global.document = {
  documentElement: { style: {} }, body: { classList: { toggle: (c, on) => (on ? classes.add(c) : classes.delete(c)), contains: c => classes.has(c) } },
  activeElement: null, title: '',
  addEventListener: (type, fn) => listeners.push(fn),
  getElementById: id => (id === 'view-map' ? view : id === 'crumb-current' ? { textContent: 'Yolculuk' } : null),
};
global.scrollTo = () => {};
global.App = { after: (name, fn) => { hooks[name] = fn; } };
""" + (WEB / "ux-a11y.js").read_text(encoding="utf-8") + r"""
const press = key => { const ev = { key, ctrlKey: true, altKey: false, preventDefault() { this.prevented = true; } }; listeners.forEach(f => f(ev)); return ev; };
const out = {};
press('+'); out.afterPlus = document.documentElement.style.zoom;
press('+'); press('+'); press('+'); out.capped = document.documentElement.style.zoom;
press('-'); out.afterMinus = document.documentElement.style.zoom;
press('0'); out.reset = document.documentElement.style.zoom; out.stored = store['cpp-adventure-ui-scale'];
UxPrefs.setReducedMotion(true); out.motion = classes.has('reduce-motion') && store['cpp-adventure-reduce-motion'] === '1';
hooks.setView([ 'map' ]); timers.forEach(f => f()); out.title = document.title; out.focused = focused; out.tabIndex = heading.tabIndex;
console.log(JSON.stringify(out));
"""
        result = subprocess.run([node, "-e", harness], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual((out["afterPlus"], out["capped"], out["afterMinus"]), ("1.15", "1.5", "1.3"))
        self.assertEqual((out["reset"], out["stored"]), ("", "1"))
        self.assertTrue(out["motion"])
        self.assertEqual((out["title"], out["focused"], out["tabIndex"]), ("Yolculuk · C++ Adventure", "h1", -1))


if __name__ == "__main__":
    unittest.main()
