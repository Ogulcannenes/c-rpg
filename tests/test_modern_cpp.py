"""Phase 8: the modern C++ track (c21-c24) is real, gradeable and bilingual.

Every code mission has a reference solution here that is compiled and run against all of
its hidden tests and the structural concept check, exactly like POST /api/submit does.
Each starter must fail at least one test (no mission is pre-solved), every prediction is
verified by running it, and the concurrency missions run real std::thread code.
"""
import re
import unittest

import server
from concept_checker import check_cpp_concept
from curriculum import CURRICULUM
from modern_cpp import CHAPTERS, predict_program

MODERN = [chapter for chapter in CURRICULUM if chapter["id"] in {"c21", "c22", "c23", "c24"}]
CYRILLIC = re.compile(r"[А-Яа-яЁё]")

SOLUTIONS = {
    "c21-03": r'''#include <iostream>
#include <vector>
#include <utility>
struct Kutu {
    std::vector<int> veri;
    static inline int kopya = 0;
    explicit Kutu(int n) : veri(n, 1) {}
    Kutu(const Kutu& o) : veri(o.veri) { ++kopya; }
    Kutu(Kutu&& o) noexcept : veri(std::move(o.veri)) {}
};
int main() {
    int n; std::cin >> n;
    Kutu a(n);
    Kutu b(std::move(a));
    std::cout << b.veri.size() << " " << a.veri.size() << " " << Kutu::kopya;
}''',
    "c21-w1": r'''#include <iostream>
#include <string>
#include <vector>
#include <utility>
int main() {
    int n; std::cin >> n;
    std::vector<std::string> kelimeler(n);
    for (auto& k : kelimeler) std::cin >> k;
    std::vector<std::string> yeni = std::move(kelimeler);
    std::cout << yeni.size() << " " << kelimeler.size();
}''',
    "c21-04": r'''#include <iostream>
#include <vector>
#include <utility>
struct Torba {
    std::vector<int> veri;
    static inline int tasima = 0;
    Torba() = default;
    Torba(Torba&& o) noexcept : veri(std::move(o.veri)) { ++tasima; }
};
int main() {
    int n; std::cin >> n;
    Torba a;
    a.veri.resize(n);
    for (int& x : a.veri) std::cin >> x;
    Torba b = std::move(a);
    Torba c = std::move(b);
    long long s = 0;
    for (int x : c.veri) s += x;
    std::cout << s << " " << a.veri.size() << " " << Torba::tasima;
}''',
    "c21-boss": r'''#include <iostream>
#include <utility>
class Envanter {
    int* veri = nullptr;
    int boyut = 0;
public:
    explicit Envanter(int n) : veri(new int[n]{}), boyut(n) {}
    ~Envanter() { delete[] veri; }
    Envanter(const Envanter& o) : veri(new int[o.boyut]{}), boyut(o.boyut) { for (int i = 0; i < boyut; ++i) veri[i] = o.veri[i]; }
    Envanter(Envanter&& o) noexcept : veri(std::exchange(o.veri, nullptr)), boyut(std::exchange(o.boyut, 0)) {}
    Envanter& operator=(const Envanter&) = delete;
    Envanter& operator=(Envanter&&) = delete;
    int& operator[](int i) { return veri[i]; }
    int size() const { return boyut; }
    long long sum() const { long long s = 0; for (int i = 0; i < boyut; ++i) s += veri[i]; return s; }
};
int main() {
    int n; std::cin >> n;
    Envanter a(n);
    for (int i = 0; i < n; ++i) std::cin >> a[i];
    Envanter b = a;
    Envanter c = std::move(a);
    if (b.size() > 0) b[0] += 100;
    std::cout << b.sum() << " " << c.sum() << " " << a.size();
}''',
    "c22-03": r'''#include <iostream>
#include <optional>
#include <string>
std::optional<int> yasOku(const std::string& s) {
    if (s.empty() || s.size() > 3 || s.find_first_not_of("0123456789") != std::string::npos) return std::nullopt;
    return std::stoi(s);
}
int main() {
    std::string s; std::cin >> s;
    std::optional<int> yas = yasOku(s);
    if (yas) std::cout << *yas + 1; else std::cout << "none";
}''',
    "c22-w1": r'''#include <iostream>
#include <optional>
#include <string>
#include <string_view>
std::optional<char> ilkSesli(std::string_view s) {
    for (char c : s) if (std::string_view("aeiou").find(c) != std::string_view::npos) return c;
    return std::nullopt;
}
int main() {
    std::string kelime; std::cin >> kelime;
    auto r = ilkSesli(kelime);
    if (r) std::cout << *r; else std::cout << '-';
}''',
    "c22-04": r'''#include <iostream>
#include <string>
#include <variant>
#include <vector>
int main() {
    int n; std::cin >> n;
    std::vector<std::variant<int, std::string>> ogeler;
    for (int i = 0; i < n; ++i) {
        std::string t; std::cin >> t;
        std::size_t start = (t.size() > 1 && t[0] == '-') ? 1 : 0;
        bool sayi = !t.empty() && t.find_first_not_of("0123456789", start) == std::string::npos;
        if (sayi) ogeler.emplace_back(std::stoi(t)); else ogeler.emplace_back(t);
    }
    long long toplam = 0; int adet = 0;
    for (const auto& o : ogeler) {
        if (std::holds_alternative<int>(o)) toplam += std::get<int>(o); else ++adet;
    }
    std::cout << toplam << " " << adet;
}''',
    "c22-boss": r'''#include <iostream>
#include <optional>
#include <string>
#include <string_view>
std::optional<std::string_view> deger(std::string_view metin, std::string_view anahtar) {
    while (!metin.empty()) {
        std::size_t son = metin.find(';');
        std::string_view parca = metin.substr(0, son);
        std::size_t esit = parca.find('=');
        if (esit != std::string_view::npos && parca.substr(0, esit) == anahtar) return parca.substr(esit + 1);
        if (son == std::string_view::npos) break;
        metin.remove_prefix(son + 1);
    }
    return std::nullopt;
}
int main() {
    std::string ayar; std::getline(std::cin, ayar);
    int q; std::cin >> q;
    for (int i = 0; i < q; ++i) {
        std::string k; std::cin >> k;
        auto r = deger(ayar, k);
        std::cout << (r ? std::string(*r) : std::string("none")) << "\n";
    }
}''',
    "c23-03": r'''#include <iostream>
#include <concepts>
#include <vector>
template <std::integral T>
T topla(const std::vector<T>& v) {
    T s{};
    for (T x : v) s += x;
    return s;
}
int main() {
    int n; std::cin >> n;
    std::vector<int> v(n);
    for (int& x : v) std::cin >> x;
    std::cout << topla(v);
}''',
    "c23-w1": r'''#include <algorithm>
#include <iostream>
#include <vector>
int main() {
    int n; std::cin >> n;
    std::vector<int> v(n);
    for (int& x : v) std::cin >> x;
    std::ranges::sort(v);
    for (std::size_t i = 0; i < v.size(); ++i) { if (i) std::cout << ' '; std::cout << v[i]; }
}''',
    "c23-04": r'''#include <iostream>
#include <ranges>
#include <vector>
int main() {
    int n; std::cin >> n;
    std::vector<int> v(n);
    for (int& x : v) std::cin >> x;
    bool ilk = true;
    for (int x : v | std::views::filter([](int x) { return x % 2 != 0; }) | std::views::transform([](int x) { return x * x; })) {
        if (!ilk) std::cout << ' ';
        ilk = false;
        std::cout << x;
    }
}''',
    "c23-boss": r'''#include <concepts>
#include <iostream>
#include <vector>
struct Kare { long long a; long long alan() const { return a * a; } };
struct Dikdortgen { long long a, b; long long alan() const { return a * b; } };
template <typename T>
concept Alanli = requires(const T& t) {
    { t.alan() } -> std::convertible_to<long long>;
};
template <Alanli T>
long long toplamAlan(const std::vector<T>& v) {
    long long s = 0;
    for (const auto& x : v) s += x.alan();
    return s;
}
int main() {
    int n; std::cin >> n;
    std::vector<Kare> kareler(n);
    for (auto& k : kareler) std::cin >> k.a;
    int m; std::cin >> m;
    std::vector<Dikdortgen> dikler(m);
    for (auto& d : dikler) std::cin >> d.a >> d.b;
    std::cout << toplamAlan(kareler) << "\n" << toplamAlan(dikler);
}''',
    "c24-03": r'''#include <iostream>
#include <thread>
#include <vector>
int main() {
    int n; std::cin >> n;
    std::vector<long long> parca(2, 0);
    std::thread a([&] { for (int i = 1; i <= n; i += 2) parca[0] += i; });
    std::thread b([&] { for (int i = 2; i <= n; i += 2) parca[1] += i; });
    a.join();
    b.join();
    std::cout << parca[0] + parca[1];
}''',
    "c24-w1": r'''#include <functional>
#include <iostream>
#include <thread>
void topla(int n, long long& sonuc) {
    for (int i = 1; i <= n; ++i) sonuc += i;
}
int main() {
    int n; std::cin >> n;
    long long sonuc = 0;
    std::thread t(topla, n, std::ref(sonuc));
    t.join();
    std::cout << sonuc;
}''',
    "c24-04": r'''#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
int main() {
    int n, k; std::cin >> n >> k;
    int sayac = 0;
    std::mutex m;
    std::vector<std::thread> ts;
    for (int t = 0; t < k; ++t)
        ts.emplace_back([&] { for (int i = 0; i < n; ++i) { std::lock_guard<std::mutex> kilit(m); ++sayac; } });
    for (auto& t : ts) t.join();
    std::cout << sayac;
}''',
    "c24-boss": r'''#include <algorithm>
#include <iostream>
#include <thread>
#include <vector>
int main() {
    int n; std::cin >> n;
    std::vector<long long> v(n);
    for (auto& x : v) std::cin >> x;
    int k; std::cin >> k;
    std::vector<long long> parca(k, 0);
    std::vector<std::thread> ts;
    for (int i = 0; i < k; ++i)
        ts.emplace_back([&, i] { for (int j = i * n / k; j < (i + 1) * n / k; ++j) parca[i] += v[j]; });
    for (auto& t : ts) t.join();
    long long toplam = 0;
    for (long long p : parca) toplam += p;
    std::cout << toplam << "\n" << *std::max_element(parca.begin(), parca.end());
}''',
}

# Correct output, wrong idea: the concept check must still say no.
CONCEPT_COUNTEREXAMPLES = {
    "shared_counter": r'''#include <iostream>
#include <thread>
#include <vector>
int main() { int n, k; std::cin >> n >> k; int c = 0; std::vector<std::thread> ts;
for (int t = 0; t < k; ++t) ts.emplace_back([&] { for (int i = 0; i < n; ++i) ++c; });
for (auto& t : ts) t.join(); std::cout << c; }''',
    "thread_join": r'''#include <iostream>
#include <thread>
int main() { int n; std::cin >> n; long long s = 0; for (int i = 1; i <= n; ++i) s += i; std::cout << s; }''',
    "custom_concept": r'''#include <iostream>
template <typename T> long long f(const T& t) { return t.alan(); }
int main() { std::cout << 1; }''',
    "ranges_pipeline": r'''#include <iostream>
#include <vector>
int main() { std::vector<int> v{1, 3}; for (int x : v) if (x % 2) std::cout << x * x << ' '; }''',
}


def grade(task, source):
    """The same checks POST /api/submit runs for a code mission."""
    if not task.get("concept_rule"):
        missing = [term for term in task.get("requires", []) if term.casefold() not in source.casefold()]
        if missing:
            return False, f"missing {missing}"
    for case in task["tests"]:
        result = server.compile_and_run(source, case["input"])
        if not (result["ok"] and server.normalize_output(result.get("output", "")) == server.normalize_output(case["expected"])):
            return False, f"input {case['input']!r}: {result.get('output', '')!r} {result.get('error', '')[:300]}"
    if task.get("concept_rule"):
        concept = check_cpp_concept(source, task["concept_rule"], "tr")
        if not concept["passed"]:
            return False, f"concept {task['concept_rule']}"
    return True, ""


class ModernTrackShapeTests(unittest.TestCase):
    def test_four_chapters_follow_the_mission_order_and_unlock_from_existing_chapters(self):
        self.assertEqual([c["id"] for c in MODERN], ["c21", "c22", "c23", "c24"])
        known = {c["id"] for c in CURRICULUM}
        for chapter in MODERN:
            self.assertEqual([t["kind"] for t in chapter["tasks"]], ["quiz", "predict", "quiz", "predict", "fix", "code", "code", "boss"])
            self.assertTrue(set(chapter["prerequisites"]) <= known, chapter["id"])
            self.assertEqual(len(chapter["guide"]["tr"]), len(chapter["guide"]["ru"]))
        self.assertEqual(server.content_index.validate(), [])

    def test_every_text_exists_in_turkish_and_russian(self):
        for chapter in MODERN:
            texts = [(chapter["title"], chapter["id"]), (chapter["lesson"], chapter["id"])]
            texts += [(task["title"], task["id"]) for task in chapter["tasks"]] + [(task["prompt"], task["id"]) for task in chapter["tasks"]]
            texts += [(task["hints"], task["id"]) for task in chapter["tasks"]]
            for value, where in texts:
                tr, ru = value["tr"], value["ru"]
                tr, ru = (" ".join(tr), " ".join(ru)) if isinstance(tr, list) else (tr, ru)
                self.assertTrue(tr.strip() and ru.strip(), where)
                self.assertFalse(CYRILLIC.search(tr), f"Russian text in the Turkish slot of {where}")
            for task in chapter["tasks"]:
                self.assertTrue(CYRILLIC.search(task["prompt"]["ru"]), f"{task['id']} Russian prompt is not Russian")
            for (title_tr, text_tr, _), (title_ru, text_ru, _) in zip(chapter["guide"]["tr"], chapter["guide"]["ru"]):
                self.assertFalse(CYRILLIC.search(title_tr + text_tr))
                self.assertTrue(CYRILLIC.search(text_ru), title_ru)

    def test_quiz_answers_are_among_the_offered_options(self):
        for chapter in MODERN:
            for task in (t for t in chapter["tasks"] if t["kind"] == "quiz"):
                for lang in ("tr", "ru"):
                    answer = task["answer"][lang] if isinstance(task["answer"], dict) else task["answer"]
                    options = [o.strip() for o in re.search(r"\(([^()]*)\)\s*$", task["prompt"][lang]).group(1).split("/")]
                    self.assertIn(answer, options, f"{task['id']} {lang}")

    def test_new_concept_rules_reject_correct_output_without_the_idea(self):
        for rule, source in CONCEPT_COUNTEREXAMPLES.items():
            self.assertFalse(check_cpp_concept(source, rule, "tr")["passed"], rule)
        self.assertFalse(check_cpp_concept("#include <thread>\n#include <mutex>\nint main(){std::cout<<1;}", "shared_counter", "tr")["passed"],
                         "an #include is not a use")


@unittest.skipUnless(server.COMPILER, "a C++ compiler is required")
class ModernTrackCompilerTests(unittest.TestCase):
    def test_reference_solutions_pass_every_hidden_test_and_concept_check(self):
        missions = [t for c in MODERN for t in c["tasks"] if t["kind"] in ("code", "fix", "boss")]
        self.assertEqual(sorted(SOLUTIONS), sorted(t["id"] for t in missions))
        for task in missions:
            with self.subTest(task=task["id"]):
                ok, why = grade(task, SOLUTIONS[task["id"]])
                self.assertTrue(ok, f"{task['id']}: {why}")

    def test_no_starter_is_already_a_solution(self):
        for task in (t for c in MODERN for t in c["tasks"] if t["kind"] in ("code", "fix", "boss")):
            with self.subTest(task=task["id"]):
                self.assertFalse(grade(task, task["starter"])[0], f"{task['id']} starter passes as-is")

    def test_predictions_match_what_the_program_really_prints(self):
        for data in CHAPTERS:
            for key in ("predict", "predict2"):
                snippet, expected = data[key]
                with self.subTest(chapter=data["id"], key=key):
                    result = server.compile_and_run(predict_program(snippet), "")
                    self.assertTrue(result["ok"], result.get("error"))
                    self.assertEqual(server.normalize_output(result["output"]), expected)


if __name__ == "__main__":
    unittest.main()
