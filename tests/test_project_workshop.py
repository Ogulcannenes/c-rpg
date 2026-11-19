import shutil
import unittest

from project_workshop import build_project, resolve_cmake, validate_files


class ProjectWorkshopTests(unittest.TestCase):
    def starter_files(self):
        return {
            "main.cpp": '#include <iostream>\n#include "message.hpp"\nint main(){ std::cout << message(); }\n',
            "include/message.hpp": "#pragma once\n#include <string>\nstd::string message();\n",
            "src/message.cpp": '#include "message.hpp"\nstd::string message(){ return "multi-file works\\n"; }\n',
        }

    def test_multi_file_workspace_compiles_and_runs_with_stdin(self):
        if not (shutil.which("g++") or shutil.which("clang++")):
            self.skipTest("No local C++ compiler")
        files = self.starter_files()
        result = build_project(files, mode="g++")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["stdout"], "multi-file works\n")

    def test_workspace_rejects_traversal_and_unapproved_extensions(self):
        files, error = validate_files({"../escape.cpp": "int main(){}"})
        self.assertIsNone(files)
        self.assertTrue(error)
        files, error = validate_files({"main.cpp": "int main(){}", "payload.bat": "echo unsafe"})
        self.assertIsNone(files)
        self.assertTrue(error)

    def test_workspace_limits_file_count_and_requires_cpp_source(self):
        files, error = validate_files({"readme.txt": "hello"})
        self.assertIsNone(files)
        self.assertTrue(error)
        oversized = {f"file{i}.cpp": "int main(){}" for i in range(25)}
        files, error = validate_files(oversized)
        self.assertIsNone(files)
        self.assertTrue(error)

    def test_cmake_mode_reports_missing_dependency_without_crashing(self):
        if not resolve_cmake():
            result = build_project(self.starter_files(), mode="cmake")
            self.assertEqual(result["phase"], "cmake_missing")
            return
        result = build_project(self.starter_files(), mode="cmake")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["stdout"], "multi-file works\n")


if __name__ == "__main__":
    unittest.main()
