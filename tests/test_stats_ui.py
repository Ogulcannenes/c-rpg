import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StatisticsUiTests(unittest.TestCase):
    def test_statistics_screen_is_connected_and_bilingual(self):
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        stats = (ROOT / "web" / "stats-ui.js").read_text(encoding="utf-8")
        import json
        locales = json.loads((ROOT / "web" / "locales.json").read_text(encoding="utf-8"))
        self.assertIn('data-view="stats"', index)
        self.assertIn('id="view-stats"', index)
        self.assertIn('/stats-ui.js', index)
        self.assertTrue(locales["modules"]["stats"]["tr"]["title"])
        self.assertTrue(locales["modules"]["stats"]["ru"]["title"])
        self.assertIn("cpp-adventure-language-changed", stats)
        self.assertIn("/api/stats?profile_id=", stats)

    def test_knowledge_map_uses_data_based_mastery_states(self):
        stats = (ROOT / "web" / "stats-ui.js").read_text(encoding="utf-8")
        self.assertIn("topic.attempts>=3&&topic.accuracy>=.85", stats)
        self.assertIn("topic.attempts>=2&&topic.accuracy<.6", stats)
        self.assertIn("map-legend", stats)

    def test_active_study_tracker_pauses_when_app_is_hidden(self):
        tracker = (ROOT / "web" / "study-tracker.js").read_text(encoding="utf-8")
        self.assertIn("document.visibilityState === 'visible'", tracker)
        self.assertIn("/api/study/pulse", tracker)
        self.assertIn("pagehide", tracker)


if __name__ == "__main__":
    unittest.main()
