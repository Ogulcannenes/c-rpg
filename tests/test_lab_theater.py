import unittest
from pathlib import Path

from visual_labs import LABS, public_result, simulate

ROOT = Path(__file__).resolve().parents[1]
CASES = [(lab["id"], {}) for lab in LABS] + [("memory", {"scenario": s}) for s in ("leak", "dangling", "dynamic", "stack", "queue", "linked_list")] + [("algorithms", {"algorithm": a}) for a in ("selection_sort", "insertion_sort", "linear_search", "binary_search", "recursion")]


class LabTheaterTests(unittest.TestCase):
    def test_every_simulation_carries_code_lines_and_a_visual(self):
        for lab_id, raw in CASES:
            for language in ("tr", "ru"):
                with self.subTest(lab=lab_id, raw=raw, language=language):
                    result = public_result(simulate(lab_id, raw, language))
                    self.assertTrue(result["code"])
                    self.assertIn(result["visual"], {"memory", "branch", "loop", "calls", "array", "bars", "lifo", "fifo", "object"})
                    for step in result["steps"]:
                        self.assertTrue(0 <= step["line"] <= len(result["code"]))
                        self.assertIn("output", step)
                    self.assertNotIn("answer_key", result)

    def test_pointer_lab_draws_the_pointer_to_its_target_and_dereferences_it(self):
        steps = simulate("pointers", {"a": 3, "b": 8, "target": "b"})["steps"]
        ptr = next(c for c in steps[1]["cells"] if c["name"] == "ptr")
        self.assertEqual(ptr["points_to"], "b")
        self.assertEqual(ptr["value"], "0x1004")
        self.assertEqual(next(c for c in steps[2]["cells"] if c["name"] == "b")["status"], "deref")
        self.assertEqual(steps[2]["output"], "8")

    def test_memory_scenarios_show_leaks_and_dangling_pointers(self):
        leak = simulate("memory", {"scenario": "leak"})["steps"][-1]["cells"]
        self.assertTrue(any(c.get("status") == "leak" for c in leak))
        self.assertFalse(any(c.get("points_to") for c in leak))
        dangling = simulate("memory", {"scenario": "dangling"})["steps"][-1]["cells"]
        self.assertTrue(any(c.get("status") == "dangling" and c.get("points_to") for c in dangling))

    def test_sorting_lines_follow_compare_and_swap(self):
        result = simulate("algorithms", {"values": "3,1", "algorithm": "bubble_sort"})
        self.assertEqual([s["line"] for s in result["steps"]], [0, 3, 4])

    def test_theater_assets_are_loaded(self):
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/lab-theater.js", index)
        self.assertIn("/lab-theater.css", index)


if __name__ == "__main__":
    unittest.main()
