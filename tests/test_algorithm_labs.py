import unittest

from visual_labs import public_result, simulate


class AlgorithmAndMemoryLabsTests(unittest.TestCase):
    def test_sorting_visualizers_return_ordered_frames_and_complexity(self):
        for algorithm in ("bubble_sort", "selection_sort", "insertion_sort"):
            result = simulate("algorithms", {"algorithm": algorithm, "values": "4,1,3,2"}, "tr")
            self.assertEqual(result["answer_key"], "1, 2, 3, 4")
            self.assertGreater(len(result["steps"]), 3)
            self.assertIn("O(n²)", result["final"])
            self.assertEqual(result["steps"][-1]["cells"][-1]["value"], 4)

    def test_linear_and_binary_search_report_found_and_missing_indices(self):
        linear = simulate("algorithms", {"algorithm": "linear_search", "values": "8,3,6,1", "target": 6}, "tr")
        binary = simulate("algorithms", {"algorithm": "binary_search", "values": "8,3,6,1", "target": 6}, "ru")
        missing = simulate("algorithms", {"algorithm": "binary_search", "values": "1,3,6,8", "target": 5}, "tr")
        self.assertEqual(linear["answer_key"], "2")
        self.assertEqual(binary["answer_key"], "2")
        self.assertEqual(missing["answer_key"], "-1")
        self.assertIn("O(log n)", binary["final"])
        self.assertIn("середина", binary["steps"][2]["text"].lower())

    def test_recursion_shows_safe_call_stack_and_factorial(self):
        result = simulate("algorithms", {"algorithm": "recursion", "target": 5}, "tr")
        self.assertEqual(result["answer_key"], "120")
        self.assertTrue(any(cell["region"] == "stack" for step in result["steps"] for cell in step["cells"]))
        self.assertEqual(public_result(result).get("answer_key"), None)

    def test_memory_playground_models_stack_queue_linked_list_and_heap(self):
        cases = {"stack": "LIFO", "queue": "FIFO", "linked_list": "4 → 9 → nullptr", "dynamic": "freed", "leak": "leak", "dangling": "dangling"}
        for scenario, answer in cases.items():
            result = simulate("memory", {"scenario": scenario}, "tr")
            self.assertEqual(result["answer_key"], answer)
            self.assertGreaterEqual(len(result["steps"]), 3)
        leak = simulate("memory", {"scenario": "leak"}, "ru")
        self.assertTrue(any(cell.get("status") == "leak" for step in leak["steps"] for cell in step["cells"]))


if __name__ == "__main__":
    unittest.main()
