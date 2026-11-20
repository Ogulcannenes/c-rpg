import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisualPolishTests(unittest.TestCase):
    def test_every_chapter_has_its_own_icon_and_no_emoji_index_is_left(self):
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        import curriculum
        for number in range(1, len(curriculum.CURRICULUM) + 1):
            self.assertIn(f'<symbol id="ch-{number}"', index)
        self.assertIn('<symbol id="ch-lock"', index)
        self.assertIn("function chapterIcon(", app)
        self.assertNotRegex(app, r"EMOJIS\[")

    def test_world_map_fills_viewport_and_clamps_panning(self):
        rpg = (ROOT / "web" / "rpg-ui.js").read_text(encoding="utf-8")
        self.assertIn("cover=Math.max(viewport.clientWidth/W,viewport.clientHeight/H)", rpg)
        self.assertIn("tx=Math.min(0,Math.max(viewport.clientWidth-W*scale,tx))", rpg)
        self.assertIn('id="world-focus"', rpg)
        self.assertEqual(len(re.findall(r"WORLD_ROWS=\[[^\]]+\]", rpg)), 1)


if __name__ == "__main__":
    unittest.main()
