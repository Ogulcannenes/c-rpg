import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectWorkshopUiTests(unittest.TestCase):
    def test_multifile_editor_is_integrated_bilingually_and_uses_inline_dialogs(self):
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "project-workshop.js").read_text(encoding="utf-8")
        styles = (ROOT / "web" / "project-workshop.css").read_text(encoding="utf-8")
        locales = (ROOT / "web" / "locales.json").read_text(encoding="utf-8")
        self.assertIn('/project-workshop.js', page)
        self.assertIn('/project-workshop.css', page)
        self.assertIn('monaco.editor.create', script)
        self.assertIn('"title": "Мастерская многомодульных проектов"', locales)
        self.assertIn("cpp-adventure-language-changed", script)
        self.assertIn("'/api/workspace/build'", script)
        self.assertIn('id="ws-create-box"', script)
        self.assertNotIn('prompt(', script)
        self.assertNotIn('confirm(', script)
        self.assertIn('.workspace-grid', styles)


if __name__ == "__main__":
    unittest.main()
