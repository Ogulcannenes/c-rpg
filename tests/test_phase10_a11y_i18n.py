"""Phase 10: keyboard/screen-reader basics and Turkish/Russian correctness."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import server
import visual_labs

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
# Turkish-slot strings that are deliberately Russian: the language switch shows the target language.
ALLOWED_RUSSIAN_IN_TR = {"modules.ui.tr.app.languageRussian"}


def leaves(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from leaves(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from leaves(value, f"{path}[{index}]")
    else:
        yield path, node


class TurkishRussianTests(unittest.TestCase):
    def test_no_russian_text_sits_in_a_turkish_slot(self):
        data = json.loads((WEB / "locales.json").read_text(encoding="utf-8"))
        bad = [path for path, value in leaves(data) if isinstance(value, str) and CYRILLIC.search(value)
               and (path.startswith("tr.") or ".tr." in path or path.endswith(".tr") or ".tr[" in path)
               and path not in ALLOWED_RUSSIAN_IN_TR]
        self.assertEqual(bad, [])

    def test_russian_yo_and_ye_grade_the_same(self):
        self.assertEqual(server.normalize_answer("Ёлка"), server.normalize_answer("елка"))
        self.assertEqual(server.normalize_answer("ЁЖ"), server.normalize_answer("еж"))
        self.assertEqual(server.normalize_answer("Işık"), server.normalize_answer("isik"))

    def test_class_lab_turns_any_name_into_a_valid_cpp_identifier(self):
        cases = {"Işık Pati": "isik_pati", "Şeker": "seker", "7 Kedi": "luna_7_kedi", "class": "class_", "!!!": "luna", "Мурка": "luna"}
        for name, expected in cases.items():
            self.assertEqual(visual_labs.cpp_identifier(name), expected, name)
        result = visual_labs.simulate("oop", {"name": 'Işık "Pati"', "level": 2}, "tr")
        code = "\n".join(result["code"]) if isinstance(result["code"], list) else result["code"]
        self.assertIn('Cat isik_pati{"Işık \\"Pati\\"", 2};', code)
        self.assertIn("isik_pati.levelUp();", code)


class ServerErrorLanguageTests(unittest.TestCase):
    def test_every_turkish_only_server_error_has_a_code_and_russian_text(self):
        import error_catalog
        source = (ROOT / "server.py").read_text(encoding="utf-8")
        messages = set(re.findall(r'"error":\s*"([^"]+)"', source))
        missing = [m for m in messages if not CYRILLIC.search(m) and m not in error_catalog.CATALOG]
        self.assertEqual(missing, [], "new Turkish-only errors need a catalog entry")
        for message, (code, russian) in error_catalog.CATALOG.items():
            self.assertRegex(code, r"^[a-z_]+$")
            self.assertRegex(russian, "[А-Яа-я]", message)

    def test_responses_carry_both_languages(self):
        import error_catalog
        payload = error_catalog.localize({"error": "Profil bulunamadı."})
        self.assertEqual((payload["error_code"], payload["error_tr"], payload["error_ru"]), ("profile_not_found", "Profil bulunamadı.", "Профиль не найден."))
        split = error_catalog.localize({"error": "15 dakikalık süre doldu. / Время 15 минут истекло."})
        self.assertEqual((split["error_tr"], split["error_ru"]), ("15 dakikalık süre doldu.", "Время 15 минут истекло."))
        nested = error_catalog.localize({"correct": False, "result": {"error": "Kod boş olamaz."}})
        self.assertEqual(nested["result"]["error_ru"], "Код не может быть пустым.")
        untouched = error_catalog.localize({"ok": True, "code": "int main(){}"})
        self.assertEqual(untouched, {"ok": True, "code": "int main(){}"})
        app = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertIn("return localizeError(await r.json())", app)


class AccessibilityTests(unittest.TestCase):
    def test_skip_link_is_first_and_targets_the_main_landmark(self):
        index = (WEB / "index.html").read_text(encoding="utf-8")
        body = index[index.index("<body>") + len("<body>"):].lstrip()
        self.assertTrue(body.startswith('<a class="skip-link" href="#main-content" data-i="skipToContent">'))
        self.assertIn('<main class="main" id="main-content" tabindex="-1">', index)
        data = json.loads((WEB / "locales.json").read_text(encoding="utf-8"))
        self.assertEqual((data["tr"]["skipToContent"], data["ru"]["skipToContent"]), ("İçeriğe geç", "Перейти к содержимому"))

    def test_active_navigation_item_is_announced_as_current_page(self):
        app = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertIn("b.setAttribute('aria-current','page')", app)
        self.assertIn("!document.querySelector('[aria-modal=\"true\"],#onboard-overlay'))renderProfiles()", app,
                      "Escape inside a dialog must not jump to the profile screen")
        self.assertIn("App.trapFocus(layer.querySelector('.save-modal'),{onEscape:close})", app)

    def test_focus_trap_cycles_and_restores_focus(self):
        node = shutil.which("node") or (r"C:\Program Files\nodejs\node.exe" if Path(r"C:\Program Files\nodejs\node.exe").exists() else None)
        if not node:
            self.skipTest("node is not installed")
        harness = r"""
const listeners = [];
let active = null;
class El {
  constructor(name, parent) { this.name = name; this.parent = parent; this.kids = []; this.offsetParent = {}; this.isConnected = true; if (parent) parent.kids.push(this); }
  focus() { active = this; }
  contains(el) { for (let e = el; e; e = e.parent) if (e === this) return true; return false; }
  querySelectorAll() { const out = []; const walk = e => { e.kids.forEach(k => { if (k.name !== 'div') out.push(k); walk(k); }); }; walk(this); return out; }
}
global.window = global;
global.document = { get activeElement() { return active; }, addEventListener: (t, f) => listeners.push(f), removeEventListener: (t, f) => listeners.splice(listeners.indexOf(f), 1) };
global.setTimeout = f => f();
""" + (WEB / "core.js").read_text(encoding="utf-8") + r"""
const page = new El('page'); const opener = new El('opener', page); opener.focus();
const dialog = new El('div', page); const a = new El('a', dialog); const b = new El('b', dialog);
let closed = 0;
const release = App.trapFocus(dialog, { onEscape: () => { closed++; release(); } });
const order = [opener, a, b];
const key = (k, shift = false) => {
  const ev = { key: k, shiftKey: shift, prevented: false, preventDefault() { this.prevented = true; }, stopPropagation() {} };
  listeners.slice().forEach(f => f(ev));
  // What the browser does when the trap lets a Tab through: move to the next/previous element.
  if (k === 'Tab' && !ev.prevented) { const i = order.indexOf(active); order[(i + (shift ? -1 : 1) + order.length) % order.length].focus(); }
  return ev;
};
const r = { start: active.name };
key('Tab'); r.afterTab = active.name;
key('Tab'); r.wrap = active.name;
key('Tab', true); r.back = active.name;
key('Escape'); r.closed = closed; r.restored = active.name; r.listeners = listeners.length;
console.log(JSON.stringify(r));
"""
        result = subprocess.run([node, "-e", harness], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        r = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(r["start"], "a", "focus moves into the dialog")
        self.assertEqual(r["afterTab"], "b")
        self.assertEqual(r["wrap"], "a", "Tab on the last item wraps to the first")
        self.assertEqual(r["back"], "b", "Shift+Tab on the first item wraps to the last")
        self.assertEqual((r["closed"], r["restored"], r["listeners"]), (1, "opener", 0))


if __name__ == "__main__":
    unittest.main()
