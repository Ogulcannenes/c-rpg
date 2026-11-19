import unittest

from career_system import career_summary, select_interview_questions


class CareerSystemTests(unittest.TestCase):
    def test_career_levels_follow_task_and_completed_project_milestones(self):
        beginner = career_summary(14, 75, [{"completed": True}], "tr", 3)
        self.assertEqual(beginner["level_id"], "beginner")
        intermediate = career_summary(15, 75, [{"completed": True}], "ru", 3)
        self.assertEqual(intermediate["level_id"], "intermediate")
        advanced = career_summary(45, 75, [{"completed": True}]*2, "tr", 3)
        self.assertEqual(advanced["level_id"], "advanced")
        self.assertEqual(advanced["projects_total"], 3)

    def test_interview_is_mixed_bilingual_and_seeded(self):
        first = select_interview_questions("profile-session", 5)
        again = select_interview_questions("profile-session", 5)
        self.assertEqual([q["id"] for q in first], [q["id"] for q in again])
        self.assertEqual(sum(q["kind"] == "code" for q in first), 1)
        self.assertEqual(sum(q["kind"] == "choice" for q in first), 4)
        self.assertTrue(all(q.get("prompt", {}).get("tr") and q.get("prompt", {}).get("ru") for q in first))


if __name__ == "__main__":
    unittest.main()
