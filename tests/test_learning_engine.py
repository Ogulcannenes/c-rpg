import unittest

from learning_engine import learning_insights


class AdaptiveLearningTests(unittest.TestCase):
    def setUp(self):
        self.topic = {"id": "c01", "number": 1, "title": {"tr": "İlk program", "ru": "Первая программа"}, "attempts": 0, "correct": 0, "errors": 0, "accuracy": None, "completed": 0, "total": 5}

    def test_prediction_is_withheld_until_three_observations(self):
        result = learning_insights([{**self.topic, "attempts": 2, "accuracy": 0.0}], [], [], "tr")
        self.assertEqual(result["predictions"], [])
        self.assertIn("yeterli", result["prediction_note"])

    def test_recent_errors_create_bilingual_risk_and_adaptive_recommendation(self):
        topic = {**self.topic, "attempts": 4, "correct": 1, "errors": 3, "accuracy": 0.25}
        events = [{"chapter_id": "c01", "correct": 0} for _ in range(3)] + [{"chapter_id": "c01", "correct": 1}]
        result = learning_insights([topic], events, [], "ru")
        self.assertEqual(result["predictions"][0]["risk"], "high")
        self.assertEqual(result["adaptive_path"]["kind"], "strengthen")
        self.assertTrue(result["predictions"][0]["risk_label"].startswith("Высокая"))

    def test_due_reviews_take_priority_over_weak_topic_guess(self):
        topic = {**self.topic, "attempts": 3, "correct": 0, "errors": 3, "accuracy": 0}
        due = [{"task_id": "c01-01", "chapter_id": "c01"}]
        result = learning_insights([topic], [], due, "tr")
        self.assertEqual(result["adaptive_path"]["kind"], "review")
        self.assertEqual(result["adaptive_path"]["task_id"], "c01-01")


if __name__ == "__main__":
    unittest.main()
