import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CareerUiTests(unittest.TestCase):
    def test_career_interview_and_portfolio_screens_are_wired_and_bilingual(self):
        page=(ROOT/"web"/"index.html").read_text(encoding="utf-8")
        script=(ROOT/"web"/"career-ui.js").read_text(encoding="utf-8")
        styles=(ROOT/"web"/"career.css").read_text(encoding="utf-8")
        locales=(ROOT/"web"/"locales.json").read_text(encoding="utf-8")
        self.assertIn('data-view="career"',page)
        self.assertIn('data-view="interview"',page)
        self.assertIn('id="view-career"',page)
        self.assertIn('/career-ui.js',page)
        self.assertIn('"career": "Карьера C++"',locales)
        self.assertIn("cpp-adventure-language-changed",script)
        self.assertIn("'/api/interview/answer'",script)
        self.assertIn("'/api/portfolio/note'",script)
        self.assertIn("URL.createObjectURL",script)
        self.assertIn('.interview-editor',styles)


if __name__ == "__main__":
    unittest.main()
