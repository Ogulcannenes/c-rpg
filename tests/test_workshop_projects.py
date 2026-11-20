import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from sandbox import normalize_output
from workshop_projects import EXTRA, CLARIFY, TEMPLATES
from project_workshop import validate_files

GXX = shutil.which("g++") or shutil.which("clang++")

SOLUTIONS = {
    "cat_inventory": r'''#include <iostream>
#include <string>
#include <vector>
struct Kedi { std::string ad; int yas; };
int main() {
    int n; std::cin >> n;
    std::vector<Kedi> v;
    for (int i = 0; i < n; ++i) { Kedi k; std::cin >> k.ad >> k.yas; v.push_back(k); }
    int best = 0, toplam = 0;
    for (int i = 0; i < n; ++i) { toplam += v[i].yas; if (v[i].yas > v[best].yas) best = i; }
    std::cout << v[best].ad << " " << toplam / n;
}''',
    "grade_report": r'''#include <iostream>
#include <string>
#include <vector>
int ortalama(const std::vector<int>& notlar) { int t = 0; for (int x : notlar) t += x; return t / (int)notlar.size(); }
std::string harf(int ort) { if (ort >= 85) return "AA"; else if (ort >= 70) return "BB"; else if (ort >= 50) return "CC"; return "FF"; }
int main() { int n; std::cin >> n; std::vector<int> v(n); for (int& x : v) std::cin >> x; int o = ortalama(v); std::cout << o << " " << harf(o); }''',
    "palindrome": r'''#include <iostream>
#include <string>
int main() { std::string k; std::cin >> k; std::string t; for (int i = (int)k.size() - 1; i >= 0; --i) t += k[i]; std::cout << t << " " << (t == k ? "EVET" : "HAYIR"); }''',
    "bank_account": r'''#include <iostream>
class Hesap {
private:
    int bakiye;
public:
    Hesap(int b) : bakiye(b) {}
    void yatir(int t) { bakiye += t; }
    bool cek(int t) { if (t > bakiye) return false; bakiye -= t; return true; }
    int durum() const { return bakiye; }
};
int main() { int b, q; std::cin >> b >> q; Hesap h(b); int hata = 0; for (int i = 0; i < q; ++i) { char c; int t; std::cin >> c >> t; if (c == 'Y') h.yatir(t); else if (!h.cek(t)) ++hata; } std::cout << h.durum() << " " << hata; }''',
    "prime_hunter": r'''#include <iostream>
bool asalMi(int x) { if (x < 2) return false; for (int i = 2; i * i <= x; ++i) if (x % i == 0) return false; return true; }
int main() { int n; std::cin >> n; int c = 0; for (int i = 2; i <= n; ++i) if (asalMi(i)) { std::cout << (c ? " " : "") << i; ++c; } std::cout << "\n" << c; }''',
}


@unittest.skipUnless(GXX, "C++ derleyicisi yok")
class WorkshopProjectTests(unittest.TestCase):
    def run_cpp(self, code, stdin):
        with tempfile.TemporaryDirectory() as folder:
            src, exe = Path(folder) / "p.cpp", Path(folder) / "p"
            src.write_text(code, encoding="utf-8")
            subprocess.run([GXX, "-std=c++20", str(src), "-o", str(exe)], check=True, capture_output=True, timeout=60)
            return subprocess.run([str(exe)], input=stdin, capture_output=True, text=True, timeout=10).stdout

    def test_reference_solutions_pass_every_test_and_meet_requirements(self):
        for project in EXTRA:
            code = SOLUTIONS[project["id"]]
            for term in project["requires"]:
                self.assertIn(term.casefold(), code.casefold(), (project["id"], term))
            for case in project["tests"]:
                with self.subTest(project=project["id"], input=case["input"]):
                    self.assertEqual(normalize_output(self.run_cpp(code, case["input"])), normalize_output(case["expected"]))

    def test_starters_compile(self):
        for project in EXTRA:
            with self.subTest(project=project["id"]):
                self.run_cpp(project["starter"], "")

    def test_templates_are_valid_workspaces_that_build(self):
        for template in TEMPLATES:
            with self.subTest(template=template["id"]):
                files, error = validate_files(template["files"])
                self.assertIsNone(error)
                with tempfile.TemporaryDirectory() as folder:
                    for name, text in files.items():
                        (Path(folder) / name).write_text(text, encoding="utf-8")
                    sources = [str(Path(folder) / n) for n in files if n.endswith(".cpp")]
                    subprocess.run([GXX, "-std=c++20", *sources, "-o", str(Path(folder) / "app")], check=True, capture_output=True, timeout=60)

    def test_every_project_explains_its_output_and_has_steps(self):
        import server
        for project in server.PROJECTS:
            with self.subTest(project=project["id"]):
                self.assertTrue(project.get("steps"))
                self.assertIn(project.get("difficulty"), (1, 2, 3))
                self.assertIn("`", project["description"]["tr"])
                self.assertIn("`", project["description"]["ru"])
                self.assertGreaterEqual(len(project["tests"]), 2)


if __name__ == "__main__":
    unittest.main()
