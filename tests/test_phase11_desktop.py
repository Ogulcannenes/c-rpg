"""Phase 11: Windows desktop packaging - single instance, WebView2 check, uninstall helper,
version resource, pinned dependencies and a safe legacy-database pointer."""
import os
import re
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import desktop
import server

ROOT = Path(__file__).resolve().parents[1]


class FakeRegistry:
    HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER = "HKLM", "HKCU"

    def __init__(self, values):
        self.values = values  # {(hive, path): version}

    class _Key:
        def __init__(self, ident):
            self.ident = ident

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def OpenKey(self, hive, path):
        if (hive, path) not in self.values:
            raise OSError("missing")
        return self._Key((hive, path))

    def QueryValueEx(self, key, name):
        return self.values[key.ident], 1


class WebView2Tests(unittest.TestCase):
    def test_missing_runtime_is_detected(self):
        self.assertEqual(desktop.webview2_version(FakeRegistry({})), "")
        placeholder = {("HKLM", "SOFTWARE\\WOW6432Node\\" + desktop.WEBVIEW2_CLIENT): "0.0.0.0"}
        self.assertEqual(desktop.webview2_version(FakeRegistry(placeholder)), "", "0.0.0.0 means not installed")

    def test_per_user_install_counts(self):
        per_user = {("HKCU", "Software\\" + desktop.WEBVIEW2_CLIENT): "131.0.2903.70"}
        self.assertEqual(desktop.webview2_version(FakeRegistry(per_user)), "131.0.2903.70")

    @unittest.skipUnless(os.name == "nt", "Windows only")
    def test_this_machine_reports_a_runtime_from_the_real_registry(self):
        self.assertRegex(desktop.webview2_version(), r"^\d+\.\d+")

    def test_missing_runtime_stops_before_the_window_with_a_bilingual_message(self):
        shown = []
        with patch.object(desktop, "acquire_single_instance", return_value=True), \
                patch.object(desktop, "webview2_version", return_value=""), \
                patch.object(desktop, "message_box", lambda text, flags=0: shown.append(text)), \
                patch.object(desktop, "log_startup", lambda message: None):
            self.assertEqual(desktop.main([]), 2)
        self.assertIn("WebView2", shown[0])
        self.assertRegex(shown[0], "[А-Яа-я]")
        self.assertIn(desktop.WEBVIEW2_DOWNLOAD, shown[0])


@unittest.skipUnless(os.name == "nt", "Windows only")
class SingleInstanceTests(unittest.TestCase):
    def test_second_copy_is_refused_while_the_first_holds_the_mutex(self):
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        with patch.object(desktop, "SINGLE_INSTANCE_MUTEX", f"Local\\CppAdventure.Test.{os.getpid()}"):
            first = desktop.acquire_single_instance(kernel32)
            self.assertTrue(first)
            try:
                self.assertIsNone(desktop.acquire_single_instance(kernel32))
                # In another process, too.
                code = ("import ctypes,sys;k=ctypes.WinDLL('kernel32',use_last_error=True);"
                        f"h=k.CreateMutexW(None,False,r'Local\\CppAdventure.Test.{os.getpid()}');"
                        "sys.exit(7 if ctypes.get_last_error()==183 else 0)")
                self.assertEqual(subprocess.run([os.sys.executable, "-c", code], timeout=30).returncode, 7)
            finally:
                kernel32.CloseHandle(first)
            again = desktop.acquire_single_instance(kernel32)
            self.assertTrue(again, "after the first copy exits, a new one may start")
            kernel32.CloseHandle(again)

    def test_second_launch_focuses_the_running_window_and_exits(self):
        focused = []
        with patch.object(desktop, "acquire_single_instance", return_value=None), \
                patch.object(desktop, "focus_existing_window", lambda: focused.append(True) or True), \
                patch.object(desktop, "log_startup", lambda message: None):
            self.assertEqual(desktop.main([]), 0)
        self.assertEqual(focused, [True])


class UninstallAndPackagingTests(unittest.TestCase):
    def test_uninstall_switch_only_removes_the_sandbox_profile(self):
        calls = []
        with patch("sandbox_windows.remove_appcontainer_profile", lambda: calls.append(1) or True):
            self.assertEqual(desktop.main(["--remove-sandbox-profile"]), 0)
        self.assertEqual(calls, [1])

    def test_inno_script_matches_the_app(self):
        raw = (ROOT / "installer" / "CppAdventure.iss").read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"), "Inno Setup needs a UTF-8 BOM for Turkish/Russian text")
        iss = raw.decode("utf-8-sig")
        self.assertIn(f"AppMutex={desktop.SINGLE_INSTANCE_MUTEX}", iss)
        self.assertIn("PrivilegesRequired=lowest", iss)
        self.assertIn('Parameters: "--remove-sandbox-profile"', iss)
        self.assertIn("compiler:Languages\\Turkish.isl", iss)
        self.assertIn("compiler:Languages\\Russian.isl", iss)
        self.assertRegex(iss, r"AppId=\{\{[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\}")
        self.assertNotIn("[UninstallDelete]", iss, "uninstall must never delete learner data")
        self.assertIn("{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}", iss)

    def test_spec_disables_upx_and_embeds_the_version(self):
        spec = (ROOT / "CppAdventure.spec").read_text(encoding="utf-8")
        self.assertEqual(spec.count("upx=False"), 2)
        self.assertNotIn("upx=True", spec)
        self.assertIn("version=version_info", spec)
        self.assertRegex(server.APP_VERSION, r"^\d+\.\d+\.\d+$")
        result = subprocess.run([os.sys.executable, str(ROOT / "installer" / "app_version.py")], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.stdout.strip(), server.APP_VERSION)

    def test_desktop_dependencies_are_pinned(self):
        direct = [line for line in (ROOT / "requirements-desktop.txt").read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
        self.assertTrue(direct and all(re.fullmatch(r"[A-Za-z0-9_.\-]+==[\w.]+", line) for line in direct), direct)
        lock = [line for line in (ROOT / "requirements-desktop.lock.txt").read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
        self.assertTrue(all("==" in line for line in lock))
        for line in direct:
            self.assertIn(line.lower(), [entry.lower() for entry in lock])
        self.assertIn("requirements-desktop.lock.txt", (ROOT / "setup-desktop.bat").read_text(encoding="utf-8"))

    def test_launcher_no_longer_prefers_stale_stage_builds(self):
        launcher = (ROOT / "start-desktop.bat").read_text(encoding="utf-8")
        self.assertNotIn("dist-stage", launcher)
        self.assertNotIn("dist-audit", launcher)


class CompilerDetectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def fake_msys(self, env="ucrt64", name="g++.exe"):
        tool = self.root / "msys64" / env / "bin" / name
        tool.parent.mkdir(parents=True)
        tool.write_bytes(b"MZ")
        return tool

    def test_msys2_outside_path_is_found_and_its_folder_put_on_path(self):
        tool = self.fake_msys()
        environ = {"PATH": str(self.root / "empty")}
        self.assertEqual(server.find_compiler(environ, roots=(str(self.root / "msys64"),)), str(tool))
        self.assertTrue(environ["PATH"].startswith(str(tool.parent) + os.pathsep), "cc1plus needs the MSYS2 DLL folder")
        server.find_compiler(environ, roots=(str(self.root / "msys64"),))
        self.assertEqual(environ["PATH"].lower().count(str(tool.parent).lower()), 1, "not added twice")

    def test_explicit_override_wins_and_missing_compiler_is_none(self):
        custom = self.root / "custom" / "clang++.exe"
        custom.parent.mkdir()
        custom.write_bytes(b"MZ")
        environ = {"PATH": "", "CPP_ADVENTURE_COMPILER": f'"{custom}"'}
        self.assertEqual(server.find_compiler(environ, roots=()), str(custom))
        self.assertIsNone(server.find_compiler({"PATH": str(self.root / "nothing")}, roots=(str(self.root / "none"),)))


class RememberedStateTests(unittest.TestCase):
    """Reported bug: after installing, the sidebar was missing on the first launches. pywebview's
    private mode forgot localStorage, so every start showed the profile picker, and picking a profile
    there never removed body.no-profile (the class that hides the sidebar)."""

    def test_window_keeps_its_storage_and_picking_a_profile_shows_the_sidebar(self):
        source = (ROOT / "desktop.py").read_text(encoding="utf-8")
        self.assertIn("private_mode=False", source)
        self.assertIn("storage_path=str(webview_storage_path())", source)
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        select = app[app.index("async function selectProfile("):]
        select = select[:select.index(chr(10))]
        self.assertIn("document.body.classList.remove('no-profile')", select)

    def test_stable_port_with_fallback_when_it_is_taken(self):
        import socket
        blocker = socket.socket()
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        taken = blocker.getsockname()[1]
        try:
            httpd, _auth, url = desktop.bind_app_server(taken)
            try:
                self.assertNotEqual(httpd.server_address[1], taken, "falls back to a free port")
                self.assertIn(f":{httpd.server_address[1]}/__session?code=", url)
            finally:
                httpd.server_close()
        finally:
            blocker.close()
        httpd, _auth, _url = desktop.bind_app_server(taken)  # free again: the preferred port is used
        try:
            self.assertEqual(httpd.server_address[1], taken)
        finally:
            httpd.server_close()

    def test_storage_folder_lives_with_the_user_data(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(server, "DATA_ROOT", Path(folder)):
            path = desktop.webview_storage_path()
            self.assertEqual(path, Path(folder) / "webview")
            self.assertTrue(path.is_dir())


class LegacyPointerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_db(self, path):
        con = sqlite3.connect(path)
        try:
            with con:
                con.execute("CREATE TABLE profiles(id TEXT PRIMARY KEY, name TEXT)")
                con.execute("INSERT INTO profiles VALUES('p1','Mira')")
        finally:
            con.close()

    def test_pointer_must_name_a_real_sqlite_file(self):
        target = self.dir / "new.db"
        fake = self.dir / "notes.db"
        fake.write_text("not a database", encoding="utf-8")
        self.assertFalse(server.migrate_legacy_database(fake, target))
        self.assertFalse(server.migrate_legacy_database("relative\\old.db", target))
        self.assertFalse(target.exists())

    def test_old_copy_is_opened_read_only_and_left_unchanged(self):
        old, target = self.dir / "old.db", self.dir / "new.db"
        self.make_db(old)
        before = old.read_bytes()
        self.assertTrue(server.migrate_legacy_database(str(old) + "  ", target), "surrounding whitespace from the pointer file is ignored")
        self.assertEqual(old.read_bytes(), before)
        con = sqlite3.connect(target)
        try:
            self.assertEqual(con.execute("SELECT name FROM profiles").fetchall(), [("Mira",)])
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
