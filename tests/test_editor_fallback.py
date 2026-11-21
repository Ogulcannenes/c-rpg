"""Phase 6: code tasks stay usable when Monaco cannot load, and the success flow keeps focus."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

# A tiny DOM: just enough for monaco-boot.js's textarea editor.
FAKE_DOM = r"""
const window = globalThis;
class Element {
  constructor(tag) { this.tag = tag; this.attrs = {}; this.handlers = {}; this.value = ''; this.selectionStart = 0; this.selectionEnd = 0; this.children = []; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener(type, fn) { (this.handlers[type] = this.handlers[type] || []).push(fn); }
  fire(type, event = {}) { (this.handlers[type] || []).forEach(fn => fn(Object.assign({ preventDefault() { event.prevented = true; } }, event))); return event; }
  replaceChildren(...kids) { this.children = kids; }
  setRangeText(text, start, end) { this.value = this.value.slice(0, start) + text + this.value.slice(end); this.selectionStart = this.selectionEnd = start + text.length; }
  remove() { this.removed = true; }
  focus() {}
}
window.document = { createElement: tag => new Element(tag), documentElement: { lang: 'tr' } };
const errors = [];
console.error = (...args) => errors.push(args.map(String).join(' '));
"""

PROBE = r"""
window.MonacoReady.then(monaco => {
  const host = new Element('div');
  const editor = monaco.editor.create(host, { value: 'int main(){}' });
  const area = host.children[0];
  let changes = 0, saves = 0;
  editor.onDidChangeModelContent(() => changes++);
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => saves++);
  area.value = 'int main(){return 0;}'; area.fire('input');
  area.selectionStart = area.selectionEnd = 0; area.fire('keydown', { key: 'Tab' });
  area.fire('keydown', { key: 's', ctrlKey: true });
  editor.setValue('x');
  const decorations = editor.deltaDecorations([], [{ range: new monaco.Range(1, 1, 1, 1), options: {} }]);
  const provider = monaco.languages.registerCompletionItemProvider('cpp', {});
  provider.dispose();
  editor.dispose();
  console.log(JSON.stringify({ fallback: monaco.isFallback, tag: area.tag, cls: area.className, label: area.attrs['aria-label'],
    changes, saves, value: editor.getValue(), decorations, removed: !!area.removed, errors: errors.length }));
});
"""


class EditorFallbackTests(unittest.TestCase):
    def test_textarea_stand_in_implements_the_monaco_subset_the_app_uses(self):
        node = shutil.which("node") or (r"C:\Program Files\nodejs\node.exe" if Path(r"C:\Program Files\nodejs\node.exe").exists() else None)
        if not node:
            self.skipTest("node is not installed")
        boot = (WEB / "monaco-boot.js").read_text(encoding="utf-8")
        # No AMD loader at all -> fallback.
        result = subprocess.run([node, "-e", FAKE_DOM + boot + PROBE], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(data["fallback"])
        self.assertEqual((data["tag"], data["cls"]), ("textarea", "code-fallback"))
        self.assertEqual(data["label"], "C++ kod düzenleyicisi")
        self.assertEqual(data["saves"], 1, "Ctrl+S command must fire")
        self.assertGreaterEqual(data["changes"], 3, "input, Tab and setValue must notify listeners")
        self.assertEqual(data["value"], "x")
        self.assertEqual(data["decorations"], [])
        self.assertTrue(data["removed"])
        self.assertEqual(data["errors"], 1, "the load failure is logged once")

    def test_loader_error_also_falls_back(self):
        node = shutil.which("node") or (r"C:\Program Files\nodejs\node.exe" if Path(r"C:\Program Files\nodejs\node.exe").exists() else None)
        if not node:
            self.skipTest("node is not installed")
        # `var` shadows Node's own CommonJS require, standing in for the AMD loader that fails to fetch.
        loader = ("var require = function (deps, ok) { setTimeout(() => require.onError(new Error('404')), 0); };\n"
                  "require.config = () => {};\n")
        boot = (WEB / "monaco-boot.js").read_text(encoding="utf-8")
        result = subprocess.run([node, "-e", FAKE_DOM + loader + boot + PROBE], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout.strip().splitlines()[-1])["fallback"])

    def test_success_flow_moves_focus_and_results_are_announced(self):
        app = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertIn('<h2 id="task-title" tabindex="-1">', app)
        self.assertIn("renderLesson();document.querySelector('#task-title')?.focus(", app)
        self.assertIn('<div id="task-result" role="status" aria-live="polite"></div>', app)
        self.assertIn('id="console" role="log" aria-live="polite"', app)


if __name__ == "__main__":
    unittest.main()
