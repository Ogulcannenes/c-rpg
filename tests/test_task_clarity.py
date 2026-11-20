import re
import unittest

from curriculum import CURRICULUM
from task_clarity import PROMPTS

TASKS = {task["id"]: task for chapter in CURRICULUM for task in chapter["tasks"]}


class TaskClarityTests(unittest.TestCase):
    def test_clarified_prompts_are_applied_in_both_languages(self):
        for task_id, (tr, ru) in PROMPTS.items():
            with self.subTest(task=task_id):
                self.assertEqual(TASKS[task_id]["prompt"], {"tr": tr, "ru": ru})
                self.assertNotEqual(tr, ru)

    def test_literal_outputs_named_in_prompts_match_the_tests(self):
        # Metinde `...` ile verilen tek kelimelik çıktılar gerçekten beklenen çıktılarda geçmeli.
        for task_id in ("c05-boss", "c11-boss", "c15-04", "c15-boss"):
            expected = " ".join(case["expected"] for case in TASKS[task_id]["tests"])
            for word in re.findall(r"`([A-Za-z]+)`", PROMPTS[task_id][0]):
                if word[0].isupper() and word not in {"Quest", "Hero"}:
                    with self.subTest(task=task_id, word=word):
                        self.assertIn(word, expected + " Bronze")

    def test_every_code_task_has_a_visible_example(self):
        for task in TASKS.values():
            if task["kind"] in {"quiz", "predict"}:
                continue
            with self.subTest(task=task["id"]):
                self.assertTrue(task["tests"])
                self.assertTrue(any(str(case["expected"]).strip() for case in task["tests"]))

    def test_quiz_and_predict_hints_are_about_the_question_not_code_writing(self):
        for task in TASKS.values():
            if task["kind"] not in {"quiz", "predict"}:
                continue
            with self.subTest(task=task["id"]):
                self.assertEqual(len(task["hints"]["tr"]), 3)
                self.assertEqual(len(task["hints"]["ru"]), 3)
                self.assertNotIn("std::cout << \"Merhaba", " ".join(task["hints"]["tr"]))


if __name__ == "__main__":
    unittest.main()
