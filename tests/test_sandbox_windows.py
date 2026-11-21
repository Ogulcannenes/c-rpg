"""End-to-end isolation tests for learner programs (real compiler, real Windows sandbox).

These tests run actual C++ programs through server.compile_and_run and check what the
sandbox really enforces on this machine. AppContainer-only guarantees are skipped (not
faked) when the OS cannot create an AppContainer.
"""
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import sandbox
import server

WINDOWS = os.name == "nt"


def run(source, stdin=""):
    return server.compile_and_run(source, stdin)


@unittest.skipUnless(server.COMPILER, "C++ compiler is required")
class LearnerProgramIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = sandbox.isolation_status()
        cls.outside = Path(tempfile.mkdtemp(prefix="cpp-adventure-outside-"))
        cls.secret = cls.outside / "secret.txt"
        cls.secret.write_text("TOP-SECRET", encoding="utf-8")

    def require_appcontainer(self):
        if self.status["mode"] != "appcontainer":
            self.skipTest(f"AppContainer unavailable here: {self.status}")

    def test_normal_program_with_input_still_works(self):
        result = run('#include <iostream>\nint main(){int n; std::cin >> n; std::cout << n * 2;}', "21")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["output"], "42")
        if WINDOWS:
            self.assertIn(result["sandbox"], ("appcontainer", "job"))

    def test_program_cannot_read_user_files(self):
        self.require_appcontainer()
        source = f'#include <fstream>\n#include <iostream>\n#include <string>\nint main(){{std::ifstream f(R"({self.secret})"); std::string s; std::cout << (f >> s ? "LEAK:" + s : std::string("blocked"));}}'
        self.assertEqual(run(source)["output"], "blocked")

    def test_program_cannot_write_outside_its_folder(self):
        self.require_appcontainer()
        target = self.outside / "written.txt"
        source = f'#include <fstream>\n#include <iostream>\nint main(){{std::ofstream f(R"({target})"); f << "x"; std::cout << (f.good() ? "WROTE" : "blocked");}}'
        self.assertEqual(run(source)["output"], "blocked")
        self.assertFalse(target.exists())

    def test_program_can_use_files_in_its_own_working_folder(self):
        source = '#include <fstream>\n#include <iostream>\n#include <string>\nint main(){std::ofstream("data.txt") << "hello"; std::ifstream in("data.txt"); std::string s; in >> s; std::cout << s;}'
        self.assertEqual(run(source)["output"], "hello")

    def test_program_cannot_start_child_processes(self):
        result = run('#include <cstdlib>\n#include <iostream>\nint main(){int r = std::system("cmd /c echo SPAWNED"); std::cout << "rc=" << r;}')
        self.assertNotIn("SPAWNED", result["output"])

    def test_program_does_not_inherit_api_keys(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-should-not-leak", "OPENAI_API_KEY": "sk-should-not-leak"}):
            result = run('#include <cstdlib>\n#include <iostream>\nint main(){const char* a = std::getenv("ANTHROPIC_API_KEY"); const char* o = std::getenv("OPENAI_API_KEY"); std::cout << (a ? a : "none") << "," << (o ? o : "none");}')
        self.assertEqual(result["output"], "none,none")

    @unittest.skipUnless(WINDOWS, "uses the Winsock API")
    def test_program_cannot_reach_loopback_services(self):
        self.require_appcontainer()
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(0.2)
        port = listener.getsockname()[1]
        accepted = []

        def accept_loop():
            deadline = time.time() + 6
            while time.time() < deadline and not accepted:
                try:
                    accepted.append(listener.accept())
                except OSError:
                    pass

        watcher = threading.Thread(target=accept_loop, daemon=True)
        watcher.start()
        source = ('#include <windows.h>\n#include <iostream>\n'
                  'typedef int (WINAPI *startup_t)(WORD, void*); typedef unsigned long long (WINAPI *socket_t)(int, int, int);\n'
                  'typedef int (WINAPI *connect_t)(unsigned long long, const void*, int);\n'
                  'struct addr_t { short family; unsigned short port; unsigned long ip; char zero[8]; };\n'
                  'int main(){ HMODULE m = LoadLibraryA("ws2_32.dll"); if(!m){ std::cout << "blocked"; return 0; } char data[512];\n'
                  '((startup_t)GetProcAddress(m, "WSAStartup"))(0x202, data); unsigned long long s = ((socket_t)GetProcAddress(m, "socket"))(2, 1, 6);\n'
                  f'addr_t a{{2, (unsigned short)((({port}) >> 8) | ((({port}) & 255) << 8)), 0x0100007F, {{0}}}};\n'
                  'int r = ((connect_t)GetProcAddress(m, "connect"))(s, &a, sizeof(a)); std::cout << (r == 0 ? "CONNECTED" : "blocked"); }')
        result = run(source)
        watcher.join()
        listener.close()
        self.assertNotIn("CONNECTED", result["output"])
        self.assertEqual(accepted, [])

    def test_infinite_loop_is_stopped(self):
        started = time.perf_counter()
        result = run("int main(){ volatile unsigned long long i = 0; while(true) ++i; }")
        self.assertEqual(result["phase"], "run_timeout")
        self.assertLess(time.perf_counter() - started, 20)

    def test_crash_returns_quickly_without_a_dialog(self):
        started = time.perf_counter()
        result = run("int main(){ volatile int* p = nullptr; return *p; }")
        self.assertEqual(result["phase"], "runtime")
        self.assertLess(result["run_ms"], 2500)
        self.assertLess(time.perf_counter() - started, 20)

    def test_memory_is_capped(self):
        source = ('#include <iostream>\n#include <vector>\nint main(){ std::vector<char*> v; try { for(;;){ char* p = new char[64*1024*1024];'
                  ' for(int i = 0; i < 64*1024*1024; i += 4096) p[i] = 1; v.push_back(p); } } catch(...) { std::cout << v.size() * 64; } }')
        result = run(source)
        self.assertTrue(result["output"].isdigit(), result)
        self.assertLessEqual(int(result["output"]), sandbox.PROGRAM_MEMORY_LIMIT // (1024 * 1024))

    def test_job_only_fallback_still_limits_processes_and_environment(self):
        with patch.dict(os.environ, {"CPP_ADVENTURE_SANDBOX": "job", "OPENAI_API_KEY": "sk-should-not-leak"}):
            spawned = run('#include <cstdlib>\n#include <iostream>\nint main(){ std::system("cmd /c echo SPAWNED"); const char* k = std::getenv("OPENAI_API_KEY"); std::cout << (k ? k : "none"); }')
        self.assertNotIn("SPAWNED", spawned["output"])
        self.assertIn("none", spawned["output"])
        if WINDOWS:
            self.assertEqual(spawned["sandbox"], "job")

    def test_identical_source_is_compiled_once(self):
        source = '#include <iostream>\nint main(){ int x; std::cin >> x; std::cout << x + 1; }  // cache-probe-7f3a'
        first, second = run(source, "1"), run(source, "2")
        self.assertEqual((first["output"], second["output"]), ("2", "3"))
        self.assertFalse(first["compile_cached"])
        self.assertTrue(second["compile_cached"])


class SourcePolicyTests(unittest.TestCase):
    def assertBlocked(self, source):
        self.assertIsNotNone(sandbox.source_policy_violation(source), source)

    def assertAllowed(self, source):
        self.assertIsNone(sandbox.source_policy_violation(source), source)

    def test_standard_and_project_relative_includes_are_allowed(self):
        self.assertAllowed('#include <iostream>\n#include <vector>\n#include "kedi.h"\n#include "include/util/math.hpp"\nint main(){}')

    def test_absolute_parent_and_computed_includes_are_blocked(self):
        self.assertBlocked('#include "C:/Users/user/AppData/Local/CppAdventure/secrets/key"\n')
        self.assertBlocked('#include </etc/passwd>\n')
        self.assertBlocked('#include "../../secret.txt"\n')
        self.assertBlocked('#define P "C:/x"\n#include P\n')
        self.assertBlocked('#if __has_include("C:/Windows/win.ini")\n#endif\n')

    def test_embed_incbin_and_preprocessor_tricks_are_blocked(self):
        self.assertBlocked('const char d[] = {\n#embed "data.bin"\n};')
        self.assertBlocked('asm(".incbin \\"C:/x\\"");')
        self.assertBlocked('#inc\\\nlude "C:/x"\n')  # line splice
        self.assertBlocked('%:include "C:/x"\n')  # digraph
        self.assertBlocked('#pragma GCC dependency "C:/x"\n')

    def test_compile_and_run_refuses_blocked_sources(self):
        result = server.compile_and_run('#include "C:/Windows/win.ini"\nint main(){}')
        self.assertEqual(result["phase"], "validate")
        self.assertIn("#include", result["error"])

    @unittest.skipUnless(server.COMPILER, "C++ compiler is required")
    def test_hidden_inline_asm_cannot_read_files_at_build_time(self):
        """String concatenation hides the directive from text scans; the -S output check catches it."""
        secret = Path(tempfile.mkdtemp(prefix="cpp-adventure-asm-secret-")) / "secret.txt"
        secret.write_text("TOP-SECRET-LINE", encoding="utf-8")
        path = str(secret).replace("\\", "/")
        for directive in ("bin", "ude"):
            source = (f'#define Q(x) #x\nasm(".inc" "{directive} \\"{path}\\"");\n'
                      '#include <iostream>\nint main(){ std::cout << "ran"; }')
            result = server.compile_and_run(source)
            self.assertFalse(result["ok"], result)
            self.assertNotEqual(result.get("output"), "ran")
            self.assertNotIn("TOP-SECRET-LINE", result.get("compile_output", "") + result.get("error", "") + result.get("output", ""))


class BuildConcurrencyTests(unittest.TestCase):
    def test_build_slots_are_bounded(self):
        held = []
        try:
            for _ in range(sandbox.MAX_PARALLEL_BUILDS):
                self.assertTrue(sandbox._BUILD_SLOTS.acquire(timeout=1))
                held.append(1)
            with self.assertRaises(sandbox.SandboxBusy):
                with sandbox.build_slot(wait=0.1):
                    pass
        finally:
            for _ in held:
                sandbox._BUILD_SLOTS.release()

    def test_tool_timeout_terminates_the_process(self):
        started = time.perf_counter()
        result = sandbox.run_tool([sys.executable, "-c", "import time; time.sleep(30)"], 1, None)
        self.assertTrue(result.timed_out)
        self.assertLess(time.perf_counter() - started, 10)


if __name__ == "__main__":
    unittest.main()
