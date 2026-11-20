import unittest
from pathlib import Path

from curriculum import CURRICULUM
from lesson_scenes import SCENES, VISUALS, build, scenes_for

ROOT = Path(__file__).resolve().parents[1]


class LessonSceneTests(unittest.TestCase):
    def test_every_chapter_has_an_animated_walkthrough_for_its_step_by_step_section(self):
        for chapter in CURRICULUM:
            with self.subTest(chapter=chapter["id"]):
                sections = [scene["section"] for scene in SCENES if scene["chapter"] == chapter["id"]]
                self.assertIn(2, sections)
                self.assertEqual(len(sections), len(set(sections)))
                self.assertTrue(all(0 <= s < len(chapter["guide"]["tr"]) for s in sections))

    def test_scenes_build_in_both_languages_with_valid_steps(self):
        for scene in SCENES:
            tr, ru = build(scene, "tr"), build(scene, "ru")
            for result in (tr, ru):
                with self.subTest(chapter=scene["chapter"], section=scene["section"], title=result["title"]):
                    self.assertIn(result["visual"], VISUALS)
                    self.assertGreaterEqual(len(result["steps"]), 3)
                    for step in result["steps"]:
                        self.assertTrue(0 <= step["line"] <= len(result["code"]))
                        self.assertTrue(step["text"].strip())
                        names = {cell["name"] for cell in step["cells"]}
                        for cell in step["cells"]:
                            if cell.get("points_to"):
                                self.assertIn(cell["points_to"], names)
                                self.assertEqual(cell["value"], next(c["address"] for c in step["cells"] if c["name"] == cell["points_to"]))
                        if result["visual"] == "flow":
                            self.assertLess(step.get("stage", -1), len(result["stages"]))
                    outputs = [step["output"] for step in result["steps"]]
                    self.assertTrue(all(b.startswith(a) for a, b in zip(outputs, outputs[1:])))
            if scene["title"][0] != scene["title"][1]:
                self.assertNotEqual(tr["title"], ru["title"])
            for a, b in zip(tr["steps"], ru["steps"]):
                self.assertNotEqual(a["text"], b["text"], f"{scene['chapter']}: çeviri eksik")

    def test_memory_addresses_respect_type_sizes_and_alignment(self):
        types = next(scene for scene in SCENES if scene["chapter"] == "c02" and scene["section"] == 2)
        cells = {c["name"]: c for c in build(types)["steps"][-1]["cells"]}
        self.assertEqual(cells["can"]["address"], "0x1000")
        self.assertEqual(cells["hiz"]["address"], "0x1008")
        self.assertEqual(cells["harf"]["size"], 1)
        self.assertEqual(cells["MAX"]["status"], "error")

    def test_pointer_scene_dereferences_and_reference_is_an_alias(self):
        pointer, both = scenes_for("c10", "tr")
        deref = pointer["steps"][2]["cells"]
        self.assertEqual(next(c for c in deref if c["name"] == "x")["status"], "deref")
        self.assertEqual(next(c for c in deref if c["name"] == "p")["points_to"], "x")
        self.assertEqual(both["steps"][1]["cells"][0].get("alias"), "r")
        self.assertEqual(len(both["steps"][1]["cells"]), 1)

    def test_heap_scene_shows_dangling_pointer_after_delete(self):
        scene = scenes_for("c16", "ru")[0]
        after_delete = {c["name"]: c for c in scene["steps"][2]["cells"]}
        self.assertEqual(after_delete["heap#1"]["status"], "freed")
        self.assertEqual(after_delete["p"]["status"], "dangling")
        self.assertEqual(scene["steps"][-1]["cells"][0]["value"], "nullptr")

    def test_map_scene_keeps_keys_sorted(self):
        scene = scenes_for("c20", "tr")[0]
        self.assertEqual([c["label"] for c in scene["steps"][2]["cells"]], ["kedi", "mama"])

    def test_assets_and_endpoint_are_wired(self):
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/lesson-scenes.js", index)
        self.assertIn("/lesson-scenes.css", index)
        self.assertIn('"/api/lesson-scenes"', (ROOT / "server.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
