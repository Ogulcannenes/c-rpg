"""Phase 6: dashboard wiring, translations, plural forms, and design-system loading order."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (WEB / "index.html").read_text(encoding="utf-8")
        cls.source = (WEB / "dashboard.js").read_text(encoding="utf-8")
        cls.copy = json.loads((WEB / "locales.json").read_text(encoding="utf-8"))["modules"]["dashboard"]

    def test_scripts_and_styles_load_in_the_right_order(self):
        scripts = re.findall(r'<script src="/([^"]+)"', self.page)
        self.assertEqual(scripts.index("dashboard.js"), scripts.index("app.js") + 1)
        styles = re.findall(r'<link rel="stylesheet" href="/([^"]+)"', self.page)
        self.assertEqual(styles[-1], "theme.css")
        self.assertEqual(len(styles), len(set(styles)), "a stylesheet is linked twice")

    def test_home_delegates_to_the_dashboard(self):
        self.assertIn("function renderHome(){if(window.Dashboard){window.Dashboard.render();return}", (WEB / "app.js").read_text(encoding="utf-8"))

    def test_every_copy_key_used_exists_in_both_languages(self):
        used = set(re.findall(r"\bc\.([A-Za-z]+)", self.source)) | set(re.findall(r"copy\(\)\.([A-Za-z]+)", self.source))
        self.assertTrue(used)
        for language in ("tr", "ru"):
            self.assertEqual(sorted(used - set(self.copy[language])), [], language)

    def test_russian_plurals_cover_one_few_many(self):
        for key in ("days", "topics"):
            forms = self.copy["ru"][key]
            self.assertEqual(set(forms), {"one", "few", "many", "other"})
            self.assertNotEqual(forms["one"], forms["many"])
            self.assertTrue(all("{n}" in value for value in forms.values()))
            self.assertEqual(set(self.copy["tr"][key]), set(forms))

    def test_interactive_elements_are_buttons_and_user_text_is_escaped(self):
        self.assertNotIn("<article", self.source)
        self.assertNotRegex(self.source, r"<div[^>]*data-dash-action")
        self.assertIn("esc(p.name)", self.source)
        self.assertIn('role="progressbar"', self.source)


class ThemeTests(unittest.TestCase):
    def test_tokens_focus_ring_and_reduced_motion_exist(self):
        css = (WEB / "theme.css").read_text(encoding="utf-8")
        for token in ("--ds-bg", "--ds-primary", "--ds-text-muted", "--ds-space-4", "--ds-radius-md", "--ds-z-modal", "--ds-focus"):
            self.assertIn(token, css)
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion: reduce", css)


if __name__ == "__main__":
    unittest.main()
