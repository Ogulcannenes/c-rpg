"""Phase 6: the knowledge map's skill tree is derived from real chapter prerequisites."""
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
sys.path.insert(0, str(ROOT))

import content_index  # noqa: E402


def find_node():
    fallback = Path(r"C:\Program Files\nodejs\node.exe")
    return shutil.which("node") or (str(fallback) if fallback.exists() else None)


class SkillTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (WEB / "skill-tree.js").read_text(encoding="utf-8")
        cls.copy = json.loads((WEB / "locales.json").read_text(encoding="utf-8"))["modules"]["skillTree"]

    def test_loaded_after_app_and_hooked_on_render_map(self):
        scripts = re.findall(r'<script src="/([^"]+)"', (WEB / "index.html").read_text(encoding="utf-8"))
        self.assertGreater(scripts.index("skill-tree.js"), scripts.index("app.js"))
        self.assertGreater(scripts.index("skill-tree.js"), scripts.index("core.js"))
        self.assertIn("App.after('renderMap', render)", self.source)

    def test_copy_keys_exist_in_both_languages(self):
        used = set(re.findall(r"\bc\.([A-Za-z]+)", self.source))
        self.assertTrue(used)
        for language in ("tr", "ru"):
            self.assertEqual(sorted(used - set(self.copy[language])), [], language)

    def test_nodes_are_buttons_with_labels_and_titles_are_escaped(self):
        self.assertIn('<button type="button" class="skill-node', self.source)
        self.assertIn('aria-label="${esc(label)}"', self.source)
        self.assertIn("esc(tx(chapter.title))", self.source)
        self.assertIn('aria-hidden="true" focusable="false"', self.source)

    def test_map_card_titles_are_keyboard_buttons(self):
        app = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertIn('<h3><button type="button" class="map-open" data-chapter="${i}">', app)

    def test_layout_of_the_real_curriculum_points_every_edge_forward(self):
        node = find_node()
        if not node:
            self.skipTest("node is not installed")
        chapters = [{"id": c["id"], "prerequisites": c.get("prerequisites", [])} for c in content_index.CHAPTER_BY_ID.values()]
        script = ("const window = globalThis; window.App = {esc: s => String(s), after() {}};\n"
                  + self.source
                  + f"\nconst chapters = {json.dumps(chapters)};\n"
                  "const out = window.SkillTree.layout(chapters);\n"
                  "console.log(JSON.stringify({depth: out.depth, position: out.position, width: out.width, height: out.height}));\n")
        result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout.strip().splitlines()[-1])
        index = {c["id"]: i for i, c in enumerate(chapters)}
        for i, chapter in enumerate(chapters):
            for parent in chapter["prerequisites"]:
                self.assertGreater(data["depth"][i], data["depth"][index[parent]], f"{chapter['id']} <- {parent}")
                self.assertGreater(data["position"][i]["x"], data["position"][index[parent]]["x"])
        spots = {(p["x"], p["y"]) for p in data["position"]}
        self.assertEqual(len(spots), len(chapters), "two chapters share a position")
        for p in data["position"]:
            self.assertGreaterEqual(p["y"], 0)
            self.assertLessEqual(p["y"] + 66, data["height"])
            self.assertLessEqual(p["x"] + 184, data["width"])


if __name__ == "__main__":
    unittest.main()
