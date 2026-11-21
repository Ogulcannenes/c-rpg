"""Phase 7: answers stay on the server, level XP is separate from the spendable balance,
and timing-based rewards use what the server observed."""
import http.client
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import server

SECRET_FIELDS = {"answer", "expected", "concept_rule", "concept_criteria"}


class Phase7EconomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db, cls.old_root = server.DB_PATH, server.DATA_ROOT
        server.DB_PATH = Path(cls.temp.name) / "phase7.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.DB_PATH, server.DATA_ROOT = cls.old_db, cls.old_root
        cls.temp.cleanup()

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        body = json.dumps(data).encode() if data is not None else None
        conn.request(method, path, body, {"Content-Type": "application/json"} if body else {})
        response = conn.getresponse()
        status, payload = response.status, json.loads(response.read() or b"null")
        conn.close()
        return status, payload

    def profile(self, name):
        return self.request("POST", "/api/profiles", {"name": name})[1]["profile_id"]

    def test_state_never_ships_answers_or_hidden_tests(self):
        pid = self.profile("No Spoilers")
        _, data = self.request("GET", f"/api/state?profile_id={pid}")
        tasks = [task for chapter in data["curriculum"] for task in chapter["tasks"]]
        self.assertEqual(len(tasks), len(server.all_tasks()))
        for task in tasks:
            self.assertFalse(SECRET_FIELDS & set(task), task["id"])
            if task["kind"] in ("quiz", "predict"):
                self.assertNotIn("tests", task, task["id"])
                self.assertNotIn("hints", task, task["id"])
            if task["kind"] == "predict":
                self.assertNotIn("starter", task, "a prediction's starter is its answer")
            elif "tests" in task:
                self.assertEqual(len(task["tests"]), 1, task["id"])
                self.assertEqual(task["test_count"], len(server.content_index.task(task["id"])["tests"]))
        self.assertIn("answer", server.content_index.task(tasks[0]["id"]), "the server keeps the real answers")

    def test_quiz_is_still_graded_on_the_server(self):
        pid = self.profile("Still Graded")
        quiz = next(task for task in server.all_tasks() if task["kind"] == "quiz")
        answer = quiz["answer"]["tr"] if isinstance(quiz["answer"], dict) else quiz["answer"]
        _, result = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": quiz["id"], "answer": answer})
        self.assertTrue(result.get("correct"), result)

    def test_spending_lowers_the_balance_but_never_the_level(self):
        pid = self.profile("Shopper")
        quiz = next(task for task in server.all_tasks() if task["kind"] == "quiz")
        answer = quiz["answer"]["tr"] if isinstance(quiz["answer"], dict) else quiz["answer"]
        self.request("POST", "/api/submit", {"profile_id": pid, "task_id": quiz["id"], "answer": answer})
        con = sqlite3.connect(server.DB_PATH)
        try:
            with con:
                con.execute("UPDATE profiles SET xp=xp+5000 WHERE id=?", (pid,))
        finally:
            con.close()
        before = self.request("GET", f"/api/state?profile_id={pid}")[1]["profile"]
        item, spec = min(server.SHOP.items(), key=lambda kv: kv[1]["cost"])
        self.assertEqual(self.request("POST", "/api/shop/buy", {"profile_id": pid, "item_id": item})[0], 200)
        after = self.request("GET", f"/api/state?profile_id={pid}")[1]["profile"]
        self.assertEqual(after["balance"], before["balance"] - spec["cost"])
        self.assertEqual(after["lifetime_xp"], before["lifetime_xp"])
        self.assertEqual((after["level"], after["level_xp"]), (before["level"], before["level_xp"]))

    def test_static_files_revalidate_so_updates_are_not_hidden_by_cache(self):
        def cache_header(path):
            conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
            conn.request("GET", path)
            response = conn.getresponse()
            response.read()
            conn.close()
            return response.status, response.getheader("Cache-Control")
        self.assertEqual(cache_header("/app.js"), (200, "no-cache"))
        self.assertEqual(cache_header("/vendor/vs/loader.js"), (200, "public, max-age=86400"))
        self.assertEqual(cache_header("/api/health")[1], "no-store")

    def test_interview_options_are_shuffled_and_graded_by_meaning(self):
        choice = [q for q in server.INTERVIEW_BANK if q["kind"] == "choice"]
        orders = {tuple(server.interview_option_order(f"s{i}", q)) for i in range(20) for q in choice}
        self.assertGreater(len(orders), 1, "the first option must not always be the right one")
        for q in choice:
            self.assertEqual(server.interview_option_order("same", q), server.interview_option_order("same", q))
        pid = self.profile("Interviewee")
        first_choice = [q["id"] for q in choice]
        with patch.object(server, "select_interview_questions", lambda session_id, n: [q for q in server.INTERVIEW_BANK if q["id"] in first_choice][:n]):
            _, started = self.request("POST", "/api/interview/start", {"profile_id": pid})
        question = started["question"]
        self.assertEqual(question["kind"], "choice")
        bank = next(q for q in server.INTERVIEW_BANK if q["id"] == question["id"])
        right = question["options"].index(bank["options"]["tr"][bank["answer"]])
        wrong = (right + 1) % len(question["options"])
        _, result = self.request("POST", "/api/interview/answer", {"profile_id": pid, "session_id": started["session_id"], "index": 0, "answer": right})
        self.assertTrue(result["correct"], result)
        _, bad = self.request("POST", "/api/interview/answer", {"profile_id": pid, "session_id": started["session_id"], "index": 1, "answer": 99})
        self.assertFalse(bad.get("correct"), bad)
        self.assertNotEqual(right, wrong)

    def test_hints_are_revealed_by_the_server_and_cost_xp_even_if_the_client_hides_it(self):
        pid = self.profile("Hint Taker")
        _, data = self.request("GET", f"/api/state?profile_id={pid}")
        public = next(t for ch in data["curriculum"] for t in ch["tasks"] if t["kind"] == "quiz" and t.get("hint_count"))
        self.assertNotIn("hints", public)
        task = server.content_index.task(public["id"])
        self.assertEqual(self.request("POST", "/api/hint", {"profile_id": pid, "task_id": task["id"], "level": 1})[0], 409, "hints open in order")
        status, hint = self.request("POST", "/api/hint", {"profile_id": pid, "task_id": task["id"], "level": 0, "lang": "ru"})
        self.assertEqual(status, 200)
        self.assertEqual(hint["hint"], task["hints"]["ru"][0])
        self.assertEqual(self.request("POST", "/api/hint", {"profile_id": pid, "task_id": task["id"], "level": 99})[0], 404)
        self.assertEqual(self.request("POST", "/api/hint", {"profile_id": "nobody", "task_id": task["id"], "level": 0})[0], 404)
        answer = task["answer"]["tr"] if isinstance(task["answer"], dict) else task["answer"]
        _, result = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": task["id"], "answer": answer, "hint_used": False})
        self.assertTrue(result["correct"], result)
        self.assertEqual(result["xp"], max(1, int(task["xp"] * 0.9)))

    def test_arena_cannot_claim_a_faster_time_than_the_server_saw(self):
        pid = self.profile("Speedrunner")
        _, arena = self.request("GET", f"/api/arena?profile_id={pid}")
        time.sleep(0.4)
        fake = {"ok": False, "compile_ok": False, "phase": "compile", "error": "x", "output": ""}
        with patch.object(server, "compile_and_run", return_value=fake):
            _, result = self.request("POST", "/api/arena/submit", {"profile_id": pid, "challenge_id": arena["challenge_id"], "code": "int main(){}", "solve_ms": 1})
        self.assertGreaterEqual(result["elapsed_ms"], 400)


if __name__ == "__main__":
    unittest.main()
