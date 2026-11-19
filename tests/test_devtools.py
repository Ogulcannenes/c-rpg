import unittest

import devtools


class DeveloperLabTests(unittest.TestCase):
    def test_git_lesson_requires_init_and_stages_before_commit(self):
        state = devtools.initial_state("git")
        state = devtools.apply("git", state, "commit", {"message": "early"})
        self.assertIn("git init", state["last"])
        state = devtools.apply("git", state, "init", {})
        state = devtools.apply("git", state, "write", {"name": "notes.txt", "content": "Study"})
        state = devtools.apply("git", state, "add", {"name": "notes.txt"})
        state = devtools.apply("git", state, "commit", {"message": "Add notes"})
        self.assertEqual(len(state["commits"]), 1)
        self.assertEqual(state["branches"]["main"], "001")

    def test_git_rejects_path_traversal(self):
        state = devtools.initial_state("git")
        devtools.apply("git", state, "init", {})
        devtools.apply("git", state, "write", {"name": "../outside", "content": "bad"})
        self.assertNotIn("../outside", state["files"])

    def test_git_branch_merge_push_and_pull_use_virtual_remote(self):
        state = devtools.initial_state("git")
        for action, values in [("init", {}), ("write", {"name": "guide.txt", "content": "Branch notes"}), ("add", {"name": "guide.txt"}), ("commit", {"message": "Add guide"}), ("branch", {"name": "feature"}), ("write", {"name": "feature.txt", "content": "Feature"}), ("add", {"name": "feature.txt"}), ("commit", {"message": "Add feature"}), ("checkout", {"name": "main"}), ("merge", {"name": "feature"})]:
            state = devtools.apply("git", state, action, values)
        self.assertEqual(state["branch"], "main")
        self.assertIn("feature.txt", state["files"])
        state = devtools.apply("git", state, "push", {})
        self.assertIn("simulated remote", state["last"])
        state["files"]["guide.txt"] = "local edit"
        state = devtools.apply("git", state, "pull", {})
        self.assertEqual(state["files"]["guide.txt"], "Branch notes")

    def test_conflict_requires_a_valid_branch_choice(self):
        state = devtools.initial_state("conflict")
        state = devtools.apply("conflict", state, "start", {})
        state = devtools.apply("conflict", state, "resolve", {"resolved": "invented"})
        self.assertTrue(state["conflict"])
        state = devtools.apply("conflict", state, "resolve", {"resolved": state["left"]})
        self.assertTrue(state["complete"])
        self.assertFalse(state["conflict"])

    def test_cmake_steps_must_be_completed_in_order(self):
        state = devtools.initial_state("cmake")
        state = devtools.apply("cmake", state, "step", {"step": 2})
        self.assertEqual(state["step"], 0)
        for step in range(1, 5):
            state = devtools.apply("cmake", state, "step", {"step": step})
        self.assertTrue(state["complete"])

    def test_cmake_status_uses_detected_host_dependency(self):
        state = devtools.initial_state("cmake")
        state = devtools.apply("cmake", state, "status", {}, "C:/fake/compiler.exe", True)
        self.assertIn("detected", state["last"])
        state = devtools.apply("cmake", state, "status", {}, "C:/fake/compiler.exe", False)
        self.assertIn("not detected", state["last"])

    def test_virtual_terminal_blocks_host_commands(self):
        state = devtools.initial_state("terminal")
        state = devtools.apply("terminal", state, "terminal", {"command": "echo safe > note.txt"})
        self.assertEqual(state["files"]["/adventure/note.txt"], "safe")
        state = devtools.apply("terminal", state, "terminal", {"command": "python -c import os"})
        self.assertIn("Blocked", state["last"])
        self.assertNotIn("/adventure/os", state["files"])


if __name__ == "__main__":
    unittest.main()
