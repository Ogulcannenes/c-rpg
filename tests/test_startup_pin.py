import unittest
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StartupAndPinUiTests(unittest.TestCase):
    def test_splash_has_local_bilingual_startup_and_exact_credit(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        splash = (ROOT / "web" / "splash.js").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        locales = __import__("json").loads((ROOT / "web" / "locales.json").read_text(encoding="utf-8"))
        self.assertIn("Created by Ogulcanenes", html)
        self.assertIn("/startup-pin.css", html)
        self.assertIn("/splash.js", html)
        self.assertIn("/pin-cat.js", html)
        self.assertIn("/api/meta", app)
        self.assertIn("APP_VERSION", server)
        self.assertTrue({"meta", "profiles", "progress", "screen", "ready", "failed"}.issubset(locales["modules"]["splash"]["tr"]))
        self.assertIn("CppAdventureI18n.module('splash'", splash)
        self.assertIn("role=\"progressbar\"", html)
        self.assertIn("aria-valuenow", splash)

    def test_pin_uses_animated_custom_cat_and_accessible_two_language_controls(self):
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        pin = (ROOT / "web" / "pin-cat.js").read_text(encoding="utf-8")
        css = (ROOT / "web" / "startup-pin.css").read_text(encoding="utf-8")
        locales = __import__("json").loads((ROOT / "web" / "locales.json").read_text(encoding="utf-8"))
        self.assertNotIn("pin=prompt(", app)
        self.assertIn("window.CatPinDialog.open", app)
        for state in ("is-hidden", "is-visible", "is-wrong", "is-success"):
            self.assertIn(state, pin)
            self.assertIn(f".pin-cat.{state}", css)
        for text in ("aria-pressed", "Escape", "event.key !== 'Tab'", "type=\"password\""):
            self.assertIn(text, pin)
        self.assertTrue(locales["modules"]["pin"]["ru"]["wrong"])
        self.assertTrue(locales["modules"]["pin"]["tr"]["wrong"])
        self.assertIn("@keyframes pin-cat-no", css)
        self.assertIn("@keyframes pin-cat-yes", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_splash_stays_up_for_three_and_a_half_seconds_after_boot_is_ready(self):
        harness = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const locales = JSON.parse(fs.readFileSync('web/locales.json', 'utf8'));
let now = 1000;
const timers = [];
const classes = new Set();
const elements = {
  '#splash-status': { textContent: '' },
  '#splash-percent': { textContent: '' },
  '#splash-progress-bar': { style: {}, classList: { add() {}, remove() {} } },
  '.splash-progress': { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } },
  '#splash-retry': { hidden: true },
  '#startup-splash': { classList: { add(name) { classes.add(name); } }, remove() { classes.add('removed'); } }
};
const context = {
  document: { querySelector(selector) { return elements[selector] || null; }, documentElement: { lang: '' } },
  localStorage: { getItem() { return 'tr'; } },
  Date: { now() { return now; } },
  window: { CppAdventureI18n: { module(name, lang) { return locales.modules[name][lang]; } }, setTimeout(fn, delay) { timers.push({ fn, delay }); return timers.length; } }
};
vm.runInNewContext(fs.readFileSync('web/splash.js', 'utf8'), context);
if (context.window.CppSplash.MIN_VISIBLE_MS !== 3500) throw new Error('minimum duration is not 3.5 seconds');
now = 1200;
context.window.CppSplash.hide();
if (elements['#splash-percent'].textContent !== '100%') throw new Error('real boot completion did not reach 100%');
if (timers[0]?.delay !== 3300) throw new Error(`expected remaining delay 3300ms, got ${timers[0]?.delay}`);
if (classes.has('is-leaving')) throw new Error('splash left before minimum visible duration');
timers[0].fn();
if (!classes.has('is-leaving')) throw new Error('splash did not begin leaving after delay');
"""
        result = subprocess.run(["node", "-e", harness], cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
