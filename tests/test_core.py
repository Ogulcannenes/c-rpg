import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import server
from advanced_cpp import assembly_outputs, simulate_counter
from plugin_system import discover_plugins, validate_manifest


class CoreSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        # DATA_ROOT too: migrations and imports write backups there (they used to land in the repo).
        cls.saved_paths = server.DB_PATH, server.DATA_ROOT
        server.DB_PATH = Path(cls.temp.name) / "test.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.DB_PATH, server.DATA_ROOT = cls.saved_paths
        cls.temp.cleanup()

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=40)
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json; charset=utf-8"} if data is not None else {}
        conn.request(method, path, payload, headers)
        response = conn.getresponse()
        result = json.loads(response.read())
        status = response.status
        conn.close()
        return status, result

    def test_compiler_temp_cleanup_retries_a_transient_windows_exe_lock(self):
        class TempFolder:
            name = "unused-test-folder"

            def __init__(self):
                self.calls = 0

            def cleanup(self):
                self.calls += 1
                if self.calls == 1:
                    raise PermissionError("temporary Windows executable lock")

        folder = TempFolder()
        with patch.object(server.tempfile, "TemporaryDirectory", return_value=folder), \
             patch.object(server.os, "name", "nt"), \
             patch.object(server.time, "sleep"):
            with server.temporary_directory("test-") as path:
                self.assertEqual(path, folder.name)
        self.assertEqual(folder.calls, 2)

    def unlock_chapter_prerequisites(self, profile_id, chapter_number):
        chapter = server.CURRICULUM[chapter_number - 1]
        with server.db() as con:
            for prerequisite_id in chapter.get("prerequisites", []):
                prerequisite = next(c for c in server.CURRICULUM if c["id"] == prerequisite_id)
                for task in prerequisite["tasks"]:
                    con.execute("INSERT OR IGNORE INTO completions(profile_id,task_id,xp) VALUES(?,?,0)", (profile_id, task["id"]))

    def test_compiler_real_gpp_with_stdin_and_output(self):
        result = server.compile_and_run("#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2;}", "21")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["output"].strip(), "42")
        self.assertTrue(result["compile_ok"])
        self.assertEqual(result["stdout"].strip(), "42")
        self.assertEqual(result["phase"], "complete")
        self.assertIsInstance(result["elapsed_ms"], int)
        self.assertEqual(result["exit_code"], 0)

    def test_compiler_supports_string_input_and_multiline_output(self):
        source = '#include <iostream>\n#include <string>\nint main(){std::string name;std::getline(std::cin,name);std::cout<<"Hello "<<name<<"\\nReady";} '
        result = server.compile_and_run(source, "Luna\n")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["stdout"], "Hello Luna\nReady")

    def test_compiler_timeout_and_missing_compiler_are_reported(self):
        infinite = server.compile_and_run("int main(){while(true){}}")
        self.assertFalse(infinite["ok"])
        self.assertEqual(infinite["phase"], "run_timeout")
        self.assertTrue(infinite["compile_ok"])
        with patch.object(server, "COMPILER", None):
            missing = server.compile_and_run("int main(){return 0;}")
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["phase"], "compiler_missing")
        self.assertIn("G++", missing["error"])

    def test_runner_repeated_runs_and_empty_input_validation(self):
        code = "#include <iostream>\nint main(){int n=0;std::cin>>n;std::cout<<n+1;}"
        first = server.compile_and_run(code, "4")
        second = server.compile_and_run(code, "9")
        self.assertEqual(first["stdout"], "5")
        self.assertEqual(second["stdout"], "10")
        self.assertFalse(server.compile_and_run("  ")["ok"])

    def test_run_api_returns_structured_output_and_compiler_errors(self):
        code = "#include <iostream>\nint main(){std::cout<<\"line one\\nline two\";}"
        _, result = self.request("POST", "/api/run", {"code": code, "input": ""})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["stdout"], "line one\nline two")
        self.assertIn("compile_ok", result)
        _, failed = self.request("POST", "/api/run", {"code": "int main( {", "input": ""})
        self.assertFalse(failed["ok"])
        self.assertEqual(failed["phase"], "compile")
        self.assertIn("error", failed["compile_output"].lower())

    def test_compiler_returns_syntax_errors(self):
        result = server.compile_and_run("int main( {")
        self.assertFalse(result["ok"])
        self.assertIn("error", result)
        self.assertFalse(result["compile_ok"])
        self.assertTrue(result["compile_output"])

    def test_checker_applies_concept_rule_and_all_edge_cases(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Checker"})
        pid = created["profile_id"]
        self.unlock_chapter_prerequisites(pid, 3)
        code = "#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2;}"
        _, blocked = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c03-04", "answer": "#include <iostream>\nint main(){std::cout<<42;}"})
        self.assertFalse(blocked["correct"])
        self.assertFalse(blocked["result"]["checks"][-1]["passed"])
        _, accepted = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c03-04", "answer": code})
        self.assertTrue(accepted["correct"], accepted)
        self.assertEqual(len(accepted["tests"]), 4)  # three G++ cases plus the concept criterion
        self.assertTrue(all(case["passed"] for case in accepted["tests"]))

    def test_hardcoded_expected_output_does_not_complete_variable_mission_or_award_xp(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Concept Gate"})
        pid = created["profile_id"]
        self.unlock_chapter_prerequisites(pid, 2)
        fixed_output = '#include <iostream>\nint main(){std::cout<<"Pati 4";}'
        _, rejected = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c02-04", "answer": fixed_output})
        self.assertFalse(rejected["correct"])
        self.assertEqual(rejected["result"]["kind"], "concept")
        self.assertIn("string", rejected["result"]["criteria"])
        after_rejection = self.request("GET", f"/api/state?profile_id={pid}")[1]["profile"]
        self.assertEqual(after_rejection["xp"], 0)
        self.assertNotIn("c02-04", after_rejection["completed"])
        real_variables = '#include <iostream>\n#include <string>\nint main(){std::string name="Pati";int paws=4;std::cout<<name<<" "<<paws;}'
        _, accepted = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c02-04", "answer": real_variables})
        self.assertTrue(accepted["correct"], accepted)
        self.assertEqual(accepted["xp"], 35)
        self.assertTrue(any(item.get("kind") == "concept" and item["passed"] for item in accepted["tests"]))

    def test_debugging_arena_has_syntax_and_runtime_bugs(self):
        syntax = server.compile_and_run(server.CURRICULUM[0]["tasks"][4]["starter"])
        runtime = server.compile_and_run(server.CURRICULUM[13]["tasks"][4]["starter"])
        self.assertFalse(syntax["ok"])
        self.assertIn("error", syntax)
        self.assertFalse(runtime["ok"])
        self.assertNotEqual(runtime.get("exit_code"), 0)

    def test_profiles_are_isolated_xp_is_once_and_quiz_attempt_persists(self):
        status, a = self.request("POST", "/api/profiles", {"name": "Ada", "avatar": "😺", "pin": "2468"})
        self.assertEqual(status, 200)
        _, b = self.request("POST", "/api/profiles", {"name": "Boris", "avatar": "🐈", "pin": ""})
        aid, bid = a["profile_id"], b["profile_id"]
        self.assertNotEqual(aid, bid)
        self.assertEqual(self.request("POST", "/api/select", {"profile_id": aid, "pin": "0000"})[0], 403)
        self.assertEqual(self.request("POST", "/api/select", {"profile_id": aid, "pin": "2468"})[0], 200)
        wrong = self.request("POST", "/api/submit", {"profile_id": aid, "task_id": "c01-01", "answer": "nope"})
        self.assertFalse(wrong[1]["correct"])
        correct = self.request("POST", "/api/submit", {"profile_id": aid, "task_id": "c01-01", "answer": "main"})
        self.assertIn("correct", correct[1], correct[1])
        self.assertTrue(correct[1]["correct"])
        self.assertEqual(correct[1]["xp"], 15)
        repeated = self.request("POST", "/api/submit", {"profile_id": aid, "task_id": "c01-01", "answer": "main"})
        self.assertEqual(repeated[1]["xp"], 0)
        sa = self.request("GET", f"/api/state?profile_id={aid}")[1]["profile"]
        sb = self.request("GET", f"/api/state?profile_id={bid}")[1]["profile"]
        self.assertEqual(sa["xp"], 15)
        self.assertEqual(sb["xp"], 0)
        self.assertEqual(sa["quiz_results"][0]["attempts"], 3)
        self.assertEqual(len(sb["completed"]), 0)

    def test_learning_journal_tracks_attempts_and_is_profile_isolated(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Journal Ada"})
        _, b = self.request("POST", "/api/profiles", {"name": "Journal Boris"})
        aid, bid = a["profile_id"], b["profile_id"]
        for _ in range(2):
            status, result = self.request("POST", "/api/submit", {"profile_id": aid, "task_id": "c01-01", "answer": "wrong", "hint_used": True})
            self.assertEqual(status, 200)
            self.assertFalse(result["correct"])
        status, result = self.request("POST", "/api/submit", {"profile_id": aid, "task_id": "c01-01", "answer": "main"})
        self.assertEqual(status, 200)
        self.assertTrue(result["correct"])
        _, journal_a = self.request("GET", f"/api/journal?profile_id={aid}")
        _, journal_b = self.request("GET", f"/api/journal?profile_id={bid}")
        topic_a = next(t for t in journal_a["topics"] if t["number"] == 1)
        topic_b = next(t for t in journal_b["topics"] if t["number"] == 1)
        self.assertEqual((topic_a["attempts"], topic_a["correct"], topic_a["errors"]), (3, 1, 2))
        self.assertEqual(topic_a["accuracy"], round(1 / 3, 3))
        self.assertEqual(topic_b["attempts"], 0)
        self.assertEqual(journal_a["attempts"], 3)
        self.assertEqual(journal_a["completed"], 1)
        self.assertEqual(len(journal_a["recent"]), 3)
        self.assertTrue(all(event["hint_used"] for event in journal_a["recent"] if not event["correct"]))
        self.assertEqual(journal_a["weak_topics"][0]["number"], 1)
        self.assertEqual(journal_b["recent"], [])

    def test_startup_metadata_reports_current_version_and_initialized_database(self):
        status, meta = self.request("GET", "/api/meta")
        self.assertEqual(status, 200)
        self.assertEqual(meta["app_version"], server.APP_VERSION)
        self.assertTrue(meta["database_ready"])

    def test_learning_journal_requires_a_valid_profile(self):
        status, result = self.request("GET", "/api/journal?profile_id=missing")
        self.assertEqual(status, 404)
        self.assertIn("error", result)

    def test_profile_creation_persists_selected_language(self):
        status, created = self.request("POST", "/api/profiles", {"name": "Русский", "lang": "ru"})
        self.assertEqual(status, 200)
        profiles = self.request("GET", "/api/profiles")[1]["profiles"]
        profile = next(p for p in profiles if p["id"] == created["profile_id"])
        self.assertEqual(profile["lang"], "ru")

    def test_json_export_import_restores_progress_and_quiz(self):
        _, c = self.request("POST", "/api/profiles", {"name": "Import"})
        pid = c["profile_id"]
        self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c01-01", "answer": "wrong"})
        self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c01-01", "answer": "main"})
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c01-02", "answer": "5"})
        status, _ = self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        self.assertEqual(status, 200)
        state = self.request("GET", f"/api/state?profile_id={pid}")[1]["profile"]
        self.assertEqual(state["completed"], ["c01-01"])
        self.assertEqual(state["xp"], 15)
        journal = self.request("GET", f"/api/journal?profile_id={pid}")[1]
        topic = next(t for t in journal["topics"] if t["number"] == 1)
        self.assertEqual(topic["attempts"], 2)
        self.assertEqual(topic["errors"], 1)

    def test_desktop_legacy_database_migration_preserves_existing_user_data(self):
        old_db = Path(self.temp.name) / "legacy.db"
        new_db = Path(self.temp.name) / "desktop" / "adventure.db"
        new_db.parent.mkdir(parents=True)
        con = server.sqlite3.connect(old_db)
        try:
            con.execute("CREATE TABLE profiles(id TEXT, name TEXT)")
            con.executemany("INSERT INTO profiles VALUES(?,?)", [("p1", "Ada"), ("p2", "Mira")])
            con.commit()
        finally:
            con.close()
        con = server.sqlite3.connect(new_db)
        try:
            con.execute("CREATE TABLE profiles(id TEXT, name TEXT)")
        finally:
            con.close()
        self.assertTrue(server.migrate_legacy_database(old_db, new_db))
        con = server.sqlite3.connect(new_db)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM profiles").fetchone()[0], 2)
        finally:
            con.close()
        self.assertTrue(Path(str(new_db) + ".pre-migration.bak").exists())
        self.assertFalse(server.migrate_legacy_database(old_db, new_db))
        con = server.sqlite3.connect(new_db)
        try:
            con.execute("INSERT INTO profiles VALUES('p3','Boris')")
            con.commit()
        finally:
            con.close()
        self.assertFalse(server.migrate_legacy_database(old_db, new_db))
        con = server.sqlite3.connect(new_db)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM profiles").fetchone()[0], 3)
        finally:
            con.close()

    def test_curriculum_is_bilingual_and_chapter_gated(self):
        self.assertEqual(len(server.CURRICULUM), 24)  # 20 core chapters + the modern C++ track
        self.assertTrue(all(len(c["tasks"]) == 8 for c in server.CURRICULUM))
        self.assertTrue(all(set(c["title"]) == {"tr", "ru"} and set(c["lesson"]) == {"tr", "ru"} for c in server.CURRICULUM))
        self.assertTrue(all(set(c["guide"]) == {"tr", "ru"} and len(c["guide"]["tr"]) >= 5 and len(c["guide"]["ru"]) >= 5 for c in server.CURRICULUM))
        self.assertEqual(len({c["tasks"][0]["prompt"]["tr"] for c in server.CURRICULUM}), len(server.CURRICULUM))
        self.assertEqual(len({c["tasks"][4]["starter"] for c in server.CURRICULUM}), len(server.CURRICULUM))
        known = {c["id"] for c in server.CURRICULUM}
        self.assertTrue(all(set(c["prerequisites"]) <= known for c in server.CURRICULUM))
        self.assertEqual(server.CURRICULUM[0]["prerequisites"], [])
        self.assertEqual(server.CURRICULUM[14]["prerequisites"], ["c12", "c13", "c14"])

    def test_prerequisite_chapters_are_enforced_by_server(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Map locked"})
        pid = created["profile_id"]
        status, locked = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c03-01", "answer": "main"})
        self.assertEqual(status, 403)
        self.assertEqual(locked["code"], "chapter_locked")
        self.unlock_chapter_prerequisites(pid, 3)
        status, accepted = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c03-01", "answer": "girdi alır"})
        self.assertEqual(status, 200)
        self.assertTrue(accepted["correct"])

    def test_local_code_quality_analyzer_reports_readability_issues(self):
        source = "using namespace std;\nint main(){std::cout << 42 << std::endl;}"
        report = server.analyze_code_quality(source, "tr")
        self.assertEqual(report["basis"], "static_heuristics")
        self.assertLess(report["score"], 100)
        self.assertEqual(report["metrics"]["functions"], 1)
        self.assertEqual({item["code"] for item in report["issues"]}, {"namespace", "flush", "magic_number"})
        russian = server.analyze_code_quality("", "ru")
        self.assertEqual(russian["score"], 0)
        self.assertIn("ПОЛЕ", russian["issues"][0]["message"].upper())
        _, created = self.request("POST", "/api/profiles", {"name": "Quality"})
        status, via_api = self.request("POST", "/api/quality/analyze", {"profile_id": created["profile_id"], "code": source})
        self.assertEqual(status, 200)
        self.assertEqual(via_api["score"], report["score"])

    def test_code_golf_compares_real_compiler_outputs(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Golf"})
        pid = created["profile_id"]
        code_a = "#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2;}"
        code_b = "#include <iostream>\nint main(){int value=0;std::cin>>value;int doubled=value+value;std::cout<<doubled;}"
        status, result = self.request("POST", "/api/code-golf/compare", {"profile_id": pid, "code_a": code_a, "code_b": code_b, "input": "21"})
        self.assertEqual(status, 200)
        self.assertTrue(result["equivalent_output"])
        self.assertEqual([item["run"]["output"].strip() for item in result["variants"]], ["42", "42"])
        self.assertLess(result["variants"][0]["characters"], result["variants"][1]["characters"])
        status, invalid = self.request("POST", "/api/code-golf/compare", {"profile_id": pid, "code_a": code_a, "code_b": "int main( {"})
        self.assertEqual(status, 200)
        self.assertFalse(invalid["equivalent_output"])

    def test_rpg_guild_secret_quests_equipment_and_profile_isolation(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Guild A"})
        _, b = self.request("POST", "/api/profiles", {"name": "Guild B"})
        aid, bid = a["profile_id"], b["profile_id"]
        boss_ids = [task["id"] for task in server.all_tasks() if task.get("kind") == "boss"][:3]
        with server.db() as con:
            for task_id in boss_ids:
                con.execute("INSERT INTO completions(profile_id,task_id,xp) VALUES(?,?,0)", (aid, task_id))
            for project_id in [item["id"] for item in server.PROJECTS[:2]]:
                con.execute("INSERT INTO project_submissions(profile_id,project_id,completed,score) VALUES(?,?,1,100)", (aid, project_id))
            con.execute("INSERT INTO shop_items(profile_id,item_id) VALUES(?,?)", (aid, "scarf"))
            con.execute("UPDATE profiles SET xp=1200 WHERE id=?", (aid,))
        status, view = self.request("GET", f"/api/rpg?profile_id={aid}")
        self.assertEqual(status, 200)
        self.assertEqual(view["rank"]["id"], "debugger")
        self.assertTrue(next(q for q in view["secret_quests"] if q["id"] == "secret_bosses")["unlocked"])
        self.assertTrue(next(q for q in view["secret_quests"] if q["id"] == "secret_projects")["unlocked"])
        status, equipped = self.request("POST", "/api/rpg/equip", {"profile_id": aid, "item_id": "scarf"})
        self.assertEqual(status, 200)
        status, denied = self.request("POST", "/api/rpg/equip", {"profile_id": bid, "item_id": "scarf"})
        self.assertEqual(status, 400)
        status, claimed = self.request("POST", "/api/rpg/secret/claim", {"profile_id": aid, "quest_id": "secret_projects"})
        self.assertEqual(status, 200)
        self.assertEqual(claimed["reward"], 220)
        status, duplicate = self.request("POST", "/api/rpg/secret/claim", {"profile_id": aid, "quest_id": "secret_projects"})
        self.assertEqual(status, 409)
        _, other = self.request("GET", f"/api/rpg?profile_id={bid}")
        self.assertEqual(other["owned_items"], [])
        self.assertFalse(any(q["claimed"] for q in other["secret_quests"]))

    def test_companion_slots_loadouts_and_export_are_profile_scoped(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Companion A"})
        _, b = self.request("POST", "/api/profiles", {"name": "Companion B"})
        aid, bid = a["profile_id"], b["profile_id"]
        with server.db() as con:
            con.executemany("INSERT INTO shop_items(profile_id,item_id) VALUES(?,?)", [(aid, item_id) for item_id in ("scarf", "wizard", "headset", "crown")])
        for item_id in ("scarf", "wizard", "headset"):
            status, result = self.request("POST", "/api/companion/equip", {"profile_id": aid, "item_id": item_id})
            self.assertEqual(status, 200, result)
        companion = self.request("GET", f"/api/companion?profile_id={aid}")[1]
        self.assertEqual(companion["equipped_items"], {"ears": "headset", "head": "wizard", "neck": "scarf"})
        state = self.request("GET", f"/api/state?profile_id={aid}")[1]["profile"]
        self.assertEqual(state["active_item"], "headset")
        self.assertEqual(state["equipped_items"], companion["equipped_items"])
        self.assertEqual(state["xp"], 0, "equipping must not spend XP")

        status, saved = self.request("POST", "/api/companion/loadout/save", {"profile_id": aid, "name": "Günlük"})
        self.assertEqual(status, 200, saved)
        loadout_id = saved["loadout_id"]
        self.assertEqual(saved["companion"]["loadouts"][0]["equipment"], companion["equipped_items"])

        status, denied = self.request("POST", "/api/companion/equip", {"profile_id": bid, "item_id": "scarf"})
        self.assertEqual(status, 400)
        status, denied = self.request("POST", "/api/companion/loadout/apply", {"profile_id": bid, "loadout_id": loadout_id})
        self.assertEqual(status, 404)
        self.assertEqual(self.request("GET", f"/api/companion?profile_id={bid}")[1]["equipped_items"], {})

        status, unequipped = self.request("POST", "/api/companion/equip", {"profile_id": aid, "item_id": "", "slot": "neck"})
        self.assertEqual(status, 200, unequipped)
        self.assertNotIn("neck", unequipped["companion"]["equipped_items"])
        status, applied = self.request("POST", "/api/companion/loadout/apply", {"profile_id": aid, "loadout_id": loadout_id})
        self.assertEqual(status, 200, applied)
        self.assertEqual(applied["companion"]["equipped_items"], companion["equipped_items"])

        _, backup = self.request("GET", f"/api/export?profile_id={aid}")
        self.assertEqual(backup["profile"]["equipped_items"], companion["equipped_items"])
        self.request("POST", "/api/companion/equip", {"profile_id": aid, "item_id": "", "slot": "head"})
        status, restored = self.request("POST", "/api/import", {"profile_id": aid, "save": backup})
        self.assertEqual(status, 200, restored)
        restored_companion = self.request("GET", f"/api/companion?profile_id={aid}")[1]
        self.assertEqual(restored_companion["equipped_items"], companion["equipped_items"])
        self.assertEqual(restored_companion["loadouts"][0]["name"], "Günlük")
        status, deleted = self.request("POST", "/api/companion/loadout/delete", {"profile_id": aid, "loadout_id": loadout_id})
        self.assertEqual(status, 200, deleted)
        self.assertEqual(deleted["companion"]["loadouts"], [])
        status, denied_delete = self.request("POST", "/api/companion/loadout/delete", {"profile_id": bid, "loadout_id": loadout_id})
        self.assertEqual(status, 404)

    def test_companion_migration_backfills_owned_legacy_accessory(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(server, "DB_PATH", Path(folder) / "legacy.db"):
            with server.db() as con:
                con.execute("CREATE TABLE profiles(id TEXT PRIMARY KEY,name TEXT NOT NULL,avatar TEXT NOT NULL,pin_hash TEXT NOT NULL DEFAULT '',xp INTEGER NOT NULL DEFAULT 0,lang TEXT NOT NULL DEFAULT 'tr',streak INTEGER NOT NULL DEFAULT 0,last_day TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,active_item TEXT NOT NULL DEFAULT '',ai_provider TEXT NOT NULL DEFAULT 'offline')")
                con.execute("CREATE TABLE shop_items(profile_id TEXT NOT NULL,item_id TEXT NOT NULL,bought_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(profile_id,item_id))")
                con.execute("INSERT INTO profiles(id,name,avatar,active_item) VALUES('legacy-profile','Legacy','🐱','scarf')")
                con.execute("INSERT INTO shop_items(profile_id,item_id) VALUES('legacy-profile','scarf')")
            server.init_db()
            with server.db() as con:
                row = con.execute("SELECT slot,item_id FROM companion_equipment WHERE profile_id='legacy-profile'").fetchone()
                self.assertEqual((row["slot"], row["item_id"]), ("neck", "scarf"))
                self.assertEqual(con.execute("SELECT active_item FROM profiles WHERE id='legacy-profile'").fetchone()[0], "scarf")

    def test_rpg_view_is_local_bilingual_and_uses_cat_art_not_emoji_placeholder(self):
        page = (Path(server.ROOT) / "web" / "index.html").read_text(encoding="utf-8")
        script = (Path(server.ROOT) / "web" / "rpg-ui.js").read_text(encoding="utf-8")
        locales = json.loads((Path(server.ROOT) / "web" / "locales.json").read_text(encoding="utf-8"))
        world_art = Path(server.ROOT) / "web" / "assets" / "cpp-world-map.svg"
        self.assertIn('data-view="rpg"', page)
        self.assertIn('/rpg-ui.js', page)
        self.assertIn('/assets/cat-companion.png', script)
        self.assertIn("Снаряжение кота", locales["modules"]["pairs"]["rpg.043"]["ru"])
        self.assertIn("Гильдия и кот-компаньон", locales["modules"]["pairs"]["rpg.012"]["ru"])
        self.assertIn("cpp-adventure-language-changed", script)
        self.assertIn("C++ Dünya Haritası", locales["modules"]["pairs"]["rpg.025"]["tr"])
        self.assertIn("Карта мира C++", locales["modules"]["pairs"]["rpg.025"]["ru"])
        self.assertIn("Variables Forest", locales["modules"]["worldZones"]["tr"])
        self.assertTrue(any(zone.startswith("Pointer Abyss") for zone in locales["modules"]["worldZones"]["tr"]))
        self.assertIn("OOP Castle", locales["modules"]["worldZones"]["tr"])
        self.assertIn("STL Kingdom", locales["modules"]["worldZones"]["tr"])
        self.assertTrue(world_art.is_file())
        self.assertIn('class="world-map-art" src="/assets/cpp-world-map.svg"', script)
        self.assertIn("setupWorldMap()", script)
        self.assertIn("world-zoom-in", script)
        self.assertIn("world-zoom-out", script)
        self.assertIn("world-zoom-reset", script)
        self.assertIn("data-world-chapter", script)
        self.assertIn("data-world-boss", script)
        self.assertIn("chapters.map((chapter,index)", script)
        self.assertIn("chapterUnlocked(index)", script)
        self.assertIn("completed.has(boss.id)", script)
        self.assertIn("window.CppAdventureWorldMap", script)

    def test_advanced_concurrency_simulation_shows_race_and_mutex_outcomes(self):
        race = simulate_counter(3, 4, False)
        safe = simulate_counter(3, 4, True)
        self.assertEqual(race["expected"], 12)
        self.assertLess(race["final"], race["expected"])
        self.assertGreater(race["lost_updates"], 0)
        self.assertEqual(safe["final"], safe["expected"])
        self.assertEqual(len(safe["steps"]), 12)
        self.assertIn("реальные потоки", safe["notice_ru"])

    def test_compiler_explorer_generates_real_o0_and_o2_assembly(self):
        result = assembly_outputs("#include <iostream>\nint main(){std::cout<<7*7;}\n", server.COMPILER)
        self.assertTrue(result["ok"], result)
        self.assertEqual([item["optimization"] for item in result["outputs"]], ["O0", "O2"])
        self.assertTrue(all(item["ok"] and item["assembly"] for item in result["outputs"]))
        missing = assembly_outputs("int main(){}", None)
        self.assertFalse(missing["ok"])

    def test_advanced_compiler_api_requires_profile_and_ui_is_bilingual(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Compiler"})
        status, result = self.request("POST", "/api/compiler/assembly", {"profile_id": created["profile_id"], "code": "int main(){return 0;}"})
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        page = (Path(server.ROOT) / "web" / "index.html").read_text(encoding="utf-8")
        script = (Path(server.ROOT) / "web" / "advanced-cpp-ui.js").read_text(encoding="utf-8")
        locales = json.loads((Path(server.ROOT) / "web" / "locales.json").read_text(encoding="utf-8"))
        self.assertIn('data-view="advanced"', page)
        self.assertIn("/advanced-cpp-ui.js", page)
        self.assertIn("Потоки и обозреватель компилятора", locales["modules"]["pairs"]["advanced-cpp.008"]["ru"])
        self.assertIn("Code Golf / качество", locales["modules"]["pairs"]["advanced-cpp.012"]["ru"])
        self.assertIn("cpp-adventure-language-changed", script)

    def test_offline_arena_runs_cases_awards_once_and_keeps_records_per_profile(self):
        _, player = self.request("POST", "/api/profiles", {"name": "Arena A"})
        _, other = self.request("POST", "/api/profiles", {"name": "Arena B"})
        pid, other_id = player["profile_id"], other["profile_id"]
        _, arena = self.request("GET", f"/api/arena?profile_id={pid}")
        solutions = {
            "fish_sort": "#include <algorithm>\n#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> a(n);for(int&x:a)std::cin>>x;std::sort(a.begin(),a.end());for(int i=0;i<n;i++)std::cout<<a[i]<<(i+1<n?' ':'\\n');}",
            "score_total": "#include <iostream>\nint main(){int n,s=0;while(std::cin>>n)s+=n;std::cout<<s;}",
            "word_count": "#include <iostream>\n#include <sstream>\n#include <string>\nint main(){std::string line,w;std::getline(std::cin,line);std::istringstream in(line);int n=0;while(in>>w)++n;std::cout<<n;}"
        }
        payload = {"profile_id": pid, "challenge_id": arena["challenge_id"], "code": solutions[arena["challenge_id"]], "solve_ms": 12345}
        status, solved = self.request("POST", "/api/arena/submit", payload)
        self.assertEqual(status, 200, solved)
        self.assertEqual(solved["score"], 100, solved)
        self.assertEqual(solved["awarded_xp"], arena["xp"])
        status, repeat = self.request("POST", "/api/arena/submit", payload)
        self.assertEqual(status, 200)
        self.assertEqual(repeat["awarded_xp"], 0)
        self.assertEqual(repeat["personal_best"], 100)
        _, exported = self.request("GET", f"/api/export?profile_id={pid}")
        self.assertEqual(exported["profile"]["arena_attempts"][0]["best_score"], 100)
        self.assertEqual(exported["profile"]["arena_attempts"][0]["best_elapsed_ms"], 12345)
        with server.db() as con:
            con.execute("DELETE FROM arena_attempts WHERE profile_id=?", (pid,))
        restored_status, _ = self.request("POST", "/api/import", {"profile_id": pid, "save": exported})
        self.assertEqual(restored_status, 200)
        _, restored_arena = self.request("GET", f"/api/arena?profile_id={pid}")
        self.assertEqual(restored_arena["attempts_today"], 2)
        self.assertEqual(restored_arena["today_best"], 100)
        _, other_arena = self.request("GET", f"/api/arena?profile_id={other_id}")
        self.assertEqual(other_arena["attempts_today"], 0)

    def test_data_only_plugins_validate_and_toggle_per_profile(self):
        _, first = self.request("POST", "/api/profiles", {"name": "Plugin A"})
        _, second = self.request("POST", "/api/profiles", {"name": "Plugin B"})
        pid, other_id = first["profile_id"], second["profile_id"]
        _, listing = self.request("GET", f"/api/plugins?profile_id={pid}")
        self.assertFalse(listing["errors"], listing)
        plugin = next(item for item in listing["plugins"] if item["id"] == "std_array_intro")
        self.assertFalse(plugin["enabled"])
        status, enabled = self.request("POST", "/api/plugins/toggle", {"profile_id": pid, "plugin_id": plugin["id"], "enabled": True})
        self.assertEqual(status, 200)
        _, after = self.request("GET", f"/api/plugins?profile_id={pid}")
        self.assertTrue(next(item for item in after["plugins"] if item["id"] == plugin["id"])["enabled"])
        _, other = self.request("GET", f"/api/plugins?profile_id={other_id}")
        self.assertFalse(next(item for item in other["plugins"] if item["id"] == plugin["id"])["enabled"])
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        self.request("POST", "/api/plugins/toggle", {"profile_id": pid, "plugin_id": plugin["id"], "enabled": False})
        restored_status, restored = self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        self.assertEqual(restored_status, 200, restored)
        _, restored_plugins = self.request("GET", f"/api/plugins?profile_id={pid}")
        self.assertTrue(next(item for item in restored_plugins["plugins"] if item["id"] == plugin["id"])["enabled"])
        malicious = {"id": "unsafe_plugin", "version": "1.0.0", "title": {"tr":"Unsafe", "ru":"Unsafe"}, "description": {"tr":"x", "ru":"x"}, "permissions": ["filesystem.write"], "lessons": [], "script": "import os"}
        validated, reason = validate_manifest(malicious)
        self.assertIsNone(validated)
        self.assertEqual(reason, "manifest_fields")

    def test_arena_and_plugin_ui_are_offline_bilingual_and_script_free(self):
        page = (Path(server.ROOT) / "web" / "index.html").read_text(encoding="utf-8")
        script = (Path(server.ROOT) / "web" / "arena-ui.js").read_text(encoding="utf-8")
        locales = json.loads((Path(server.ROOT) / "web" / "locales.json").read_text(encoding="utf-8"))
        self.assertIn('data-view="arena"', page)
        self.assertIn("/arena-ui.js", page)
        self.assertIn("Ежедневное кодовое испытание", locales["modules"]["pairs"]["arena.004"]["ru"])
        self.assertIn("Плагины уроков", locales["modules"]["pairs"]["arena.016"]["ru"])
        self.assertIn("cpp-adventure-language-changed", script)
        self.assertIn("/api/arena/submit", script)
        self.assertIn("/api/plugins/install", script)
        self.assertIn("/api/plugins/remove", script)
        self.assertIn('id="plugin-file"', script)
        self.assertIn("Eklenti kodu çalıştırılmaz", locales["modules"]["pairs"]["arena.034"]["tr"])
        self.assertNotIn("eval(", script)

    def test_plugin_install_update_remove_and_permissions_are_profile_safe(self):
        _, profile_a = self.request("POST", "/api/profiles", {"name": "Plugin Owner"})
        _, profile_b = self.request("POST", "/api/profiles", {"name": "Plugin Guest"})
        pid, other_id = profile_a["profile_id"], profile_b["profile_id"]
        bundled = Path(server.ROOT) / "plugins"
        user_plugins = Path(self.temp.name) / "user-plugins"
        manifest = {
            "id": "lesson_pack", "version": "1.0.0",
            "title": {"tr": "Ders paketi", "ru": "Пакет уроков"},
            "description": {"tr": "Yerel ders", "ru": "Локальный урок"},
            "permissions": ["lessons.read"],
            "lessons": [{"id": "intro_lesson", "title": {"tr": "Giriş", "ru": "Введение"}, "content": {"tr": "Değişkenleri öğren.", "ru": "Изучи переменные."}}],
        }
        with patch.object(server, "plugin_directories", return_value=[bundled, user_plugins]):
            status, installed = self.request("POST", "/api/plugins/install", {"profile_id": pid, "manifest": manifest})
            self.assertEqual(status, 201, installed)
            self.assertEqual(installed["result"], "installed")
            self.assertTrue((user_plugins / "lesson_pack.json").is_file())
            _, listing = self.request("GET", f"/api/plugins?profile_id={pid}")
            custom = next(plugin for plugin in listing["plugins"] if plugin["id"] == "lesson_pack")
            self.assertEqual(custom["source"], "local")
            self.assertFalse(custom["enabled"])
            self.assertEqual(listing["permissions"], ["lessons.read"])

            status, enabled = self.request("POST", "/api/plugins/toggle", {"profile_id": pid, "plugin_id": "lesson_pack", "enabled": True})
            self.assertEqual(status, 200)
            _, other_listing = self.request("GET", f"/api/plugins?profile_id={other_id}")
            self.assertFalse(next(plugin for plugin in other_listing["plugins"] if plugin["id"] == "lesson_pack")["enabled"])

            updated_manifest = json.loads(json.dumps(manifest))
            updated_manifest["version"] = "1.2.0"
            updated_manifest["lessons"][0]["content"]["tr"] = "Ders içeriği güncellendi."
            status, updated = self.request("POST", "/api/plugins/install", {"profile_id": pid, "manifest": updated_manifest})
            self.assertEqual(status, 200, updated)
            self.assertEqual(updated["result"], "updated")
            status, stale = self.request("POST", "/api/plugins/install", {"profile_id": pid, "manifest": updated_manifest})
            self.assertEqual(status, 409)
            self.assertEqual(stale["error"], "version_not_newer")

            large_manifest = json.loads(json.dumps(manifest))
            large_manifest["id"] = "large_lessons"
            large_manifest["lessons"] = [
                {"id": f"lesson_{index}", "title": {"tr": f"Ders {index}", "ru": f"Урок {index}"},
                 "content": {"tr": "a" * 2000, "ru": "б" * 2000}}
                for index in range(1, 13)
            ]
            large_payload = json.dumps({"profile_id": pid, "manifest": large_manifest}, ensure_ascii=False).encode("utf-8")
            self.assertGreater(len(large_payload), 30_000)
            status, large_result = self.request("POST", "/api/plugins/install", {"profile_id": pid, "manifest": large_manifest})
            self.assertEqual(status, 201, large_result)

            status, builtin = self.request("POST", "/api/plugins/remove", {"profile_id": pid, "plugin_id": "std_array_intro"})
            self.assertEqual(status, 400)
            self.assertEqual(builtin["error"], "bundled_plugin_reserved")
            status, removed = self.request("POST", "/api/plugins/remove", {"profile_id": pid, "plugin_id": "lesson_pack"})
            self.assertEqual(status, 200, removed)
            self.assertFalse((user_plugins / "lesson_pack.json").exists())
            with server.db() as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM plugin_settings WHERE plugin_id=?", ("lesson_pack",)).fetchone()[0], 0)
        validated, error = validate_manifest({**manifest, "script": "__import__('os').system('whoami')"})
        self.assertIsNone(validated)
        self.assertEqual(error, "manifest_fields")

    def test_plugin_discovery_isolates_bad_json_from_valid_lesson_data(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "broken.json").write_text("{not-json", encoding="utf-8")
            valid = {
                "id": "safe_lesson", "version": "1.0.0", "title": {"tr": "Güvenli", "ru": "Безопасный"},
                "description": {"tr": "Yerel", "ru": "Локальный"}, "permissions": ["lessons.read"],
                "lessons": [{"id": "intro_step", "title": {"tr": "Giriş", "ru": "Введение"}, "content": {"tr": "Merhaba", "ru": "Привет"}}],
            }
            (folder / "safe_lesson.json").write_text(json.dumps(valid, ensure_ascii=False), encoding="utf-8")
            found, errors = discover_plugins([folder])
            self.assertEqual([item["id"] for item in found], ["safe_lesson"])
            self.assertEqual(errors, [{"file": "broken.json", "reason": "invalid_json"}])

    def test_visual_lab_simulations_are_safe_bilingual_and_stepwise(self):
        self.assertEqual(len(server.LABS), 9)
        for lab in server.LABS:
            tr = server.simulate_visual_lab(lab["id"], {}, "tr")
            ru = server.simulate_visual_lab(lab["id"], {}, "ru")
            self.assertGreaterEqual(len(tr["steps"]), 3, lab["id"])
            self.assertTrue(all("cells" in step and step["text"] for step in tr["steps"]))
            self.assertTrue(tr["answer_key"])
            self.assertTrue(ru["challenge"]["prompt"])
            self.assertNotIn("answer_key", server.public_lab_result(tr))
        safe = server.simulate_visual_lab("memory", {"scenario":"dangling"})
        self.assertEqual(safe["answer_key"], "dangling")
        self.assertEqual(safe["cells"][0]["region"], "heap")
        empty_loop = server.simulate_visual_lab("loops", {"start":5,"end":1})
        self.assertEqual(empty_loop["answer_key"], "0")
        sorting = server.simulate_visual_lab("algorithms", {"values":"5,2,4,1","algorithm":"bubble_sort"})
        searching = server.simulate_visual_lab("algorithms", {"values":"3,9,2","algorithm":"linear_search","target":9}, "ru")
        self.assertEqual(sorting["answer_key"], "1, 2, 4, 5")
        self.assertGreater(len(sorting["steps"]), 3)
        self.assertEqual(searching["answer_key"], "1")

    def test_visual_lab_award_is_real_persisted_and_once_per_profile(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Lab Ada"})
        _, b = self.request("POST", "/api/profiles", {"name": "Lab Mira"})
        aid,bid=a["profile_id"],b["profile_id"]
        values={"start":10,"add":7}
        _, preview = self.request("POST", "/api/labs/simulate", {"profile_id":aid,"lab_id":"variables","values":values})
        self.assertNotIn("answer_key", preview)
        status, wrong = self.request("POST", "/api/labs/submit", {"profile_id":aid,"lab_id":"variables","values":values,"answer":"16"})
        self.assertEqual(status,200)
        self.assertFalse(wrong["correct"])
        _, award = self.request("POST", "/api/labs/submit", {"profile_id":aid,"lab_id":"variables","values":values,"answer":"17"})
        self.assertTrue(award["correct"])
        self.assertEqual(award["xp"],12)
        _, repeated = self.request("POST", "/api/labs/submit", {"profile_id":aid,"lab_id":"variables","values":values,"answer":"17"})
        self.assertEqual(repeated["xp"],0)
        pa=self.request("GET",f"/api/state?profile_id={aid}")[1]["profile"]
        pb=self.request("GET",f"/api/state?profile_id={bid}")[1]["profile"]
        self.assertEqual(pa["xp"],12)
        self.assertEqual(pb["xp"],0)
        self.assertEqual(self.request("GET",f"/api/labs?profile_id={aid}")[1]["labs"][0]["earned_xp"],12)
        _, save = self.request("GET",f"/api/export?profile_id={aid}")
        status, restored = self.request("POST","/api/import",{"profile_id":bid,"save":save})
        self.assertEqual(status,200,restored)
        self.assertTrue(self.request("GET",f"/api/labs?profile_id={bid}")[1]["labs"][0]["completed"])

    def test_quiz_answers_follow_each_profiles_language_and_review_schedule(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Russian learner"})
        pid = created["profile_id"]
        self.unlock_chapter_prerequisites(pid, 3)
        self.request("POST", "/api/settings", {"profile_id": pid, "lang": "ru"})
        self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c03-01", "answer": "неправильно"})
        _, accepted = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": "c03-01", "answer": "читает ввод"})
        self.assertTrue(accepted["correct"])
        with server.db() as con:
            row = con.execute("SELECT interval_days FROM review_schedule WHERE profile_id=? AND task_id='c03-01'", (pid,)).fetchone()
        self.assertEqual(row[0], 3)

    def test_daily_quest_bonus_and_cosmetics_are_per_profile(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Daily"})
        pid = created["profile_id"]
        profile = self.request("GET", f"/api/state?profile_id={pid}")[1]["profile"]
        quest = profile["daily_quest"]
        self.assertEqual(quest["task_id"], "c01-01")
        _, award = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": quest["task_id"], "answer": "main"})
        self.assertEqual(award["daily_bonus"], 15)
        _, repeat = self.request("POST", "/api/submit", {"profile_id": pid, "task_id": quest["task_id"], "answer": "main"})
        self.assertEqual(repeat["daily_bonus"], 0)
        with server.db() as con: con.execute("UPDATE profiles SET xp=300 WHERE id=?", (pid,))
        _, purchased = self.request("POST", "/api/shop/buy", {"profile_id": pid, "item_id": "yarn"})
        self.assertTrue(purchased["ok"])
        _, used = self.request("POST", "/api/shop/use", {"profile_id": pid, "item_id": "yarn"})
        self.assertTrue(used["ok"])
        state = self.request("GET", f"/api/state?profile_id={pid}")[1]["profile"]
        self.assertEqual(state["active_item"], "yarn")
        self.assertIn("yarn", state["owned_items"])

    def test_shop_has_progressive_local_prices_and_badges_are_importable(self):
        self.assertEqual(len(server.SHOP), 16)
        costs = [item["cost"] for item in server.SHOP.values()]
        self.assertEqual(costs, sorted(costs))
        _, created = self.request("POST", "/api/profiles", {"name": "Badge import"})
        pid = created["profile_id"]
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        save["profile"]["achievements"] = [{"id": "first_boss"}, {"id": "algorithmist"}]
        status, _ = self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        self.assertEqual(status, 200)
        profile = self.request("GET", f"/api/state?profile_id={pid}")[1]["profile"]
        self.assertIn("first_boss", profile["achievements"])
        self.assertIn("algorithmist", profile["achievements"])

    def test_ai_diagnosis_is_local_by_default_and_groq_requires_consent(self):
        _, created = self.request("POST", "/api/profiles", {"name": "AI learner"})
        pid = created["profile_id"]
        code = "#include <iostream>\nint main(){std::cout << 42;}"
        status, local = self.request("POST", "/api/ai/diagnose", {"profile_id": pid, "task_id": "c03-04", "code": code, "lang": "tr"})
        self.assertEqual(status, 200)
        self.assertEqual(local["provider"], "offline")
        self.assertIn("diagnostic", local)
        self.request("POST", "/api/settings", {"profile_id": pid, "ai_provider": "groq"})
        status, denied = self.request("POST", "/api/ai/diagnose", {"profile_id": pid, "task_id": "c03-04", "code": code, "lang": "tr", "consent": False})
        self.assertEqual(status, 403)
        self.assertTrue(denied["consent_required"])

    def test_workshop_projects_run_multiple_cases_and_award_once(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Workshop A"})
        _, b = self.request("POST", "/api/profiles", {"name": "Workshop B"})
        pid = a["profile_id"]
        code = "#include <iostream>\n#include <string>\nint main(){std::string ad;std::cin>>ad;std::cout<<\"Merhaba, \"<<ad<<\"!\";}"
        self.request("POST", "/api/project/save", {"profile_id": pid, "project_id": "cat_greeting", "code": code})
        _, result = self.request("POST", "/api/project/submit", {"profile_id": pid, "project_id": "cat_greeting", "code": code})
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(result["checks"]), 2)
        self.assertEqual(result["xp"], 70)
        _, repeated = self.request("POST", "/api/project/submit", {"profile_id": pid, "project_id": "cat_greeting", "code": code})
        self.assertEqual(repeated["xp"], 0)
        _, other = self.request("GET", f"/api/projects?profile_id={b['profile_id']}")
        self.assertEqual(other["saves"], {})

    def test_multifile_workspaces_build_persist_export_and_remain_profile_scoped(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Workspace A"})
        _, b = self.request("POST", "/api/profiles", {"name": "Workspace B"})
        aid, bid = a["profile_id"], b["profile_id"]
        _, created = self.request("POST", "/api/workspace/create", {"profile_id": aid, "name": "Header project"})
        workspace = created["workspace"]
        workspace_id = workspace["workspace_id"]
        files = {
            "main.cpp": '#include <iostream>\n#include "message.hpp"\nint main(){ std::cout << message(); }',
            "include/message.hpp": "#pragma once\n#include <string>\nstd::string message();",
            "src/message.cpp": '#include "message.hpp"\nstd::string message(){ return "saved project\\n"; }',
        }
        _, saved = self.request("POST", "/api/workspace/save", {"profile_id": aid, "workspace_id": workspace_id, "name": "Header project", "files": files})
        self.assertTrue(saved["ok"])
        _, built = self.request("POST", "/api/workspace/build", {"profile_id": aid, "workspace_id": workspace_id, "files": files, "mode": "g++"})
        self.assertTrue(built["ok"], built)
        self.assertEqual(built["stdout"], "saved project\n")
        from project_workshop import resolve_cmake
        if resolve_cmake():
            _, cmake_build = self.request("POST", "/api/workspace/build", {"profile_id": aid, "workspace_id": workspace_id, "files": files, "mode": "cmake"})
            self.assertTrue(cmake_build["ok"], cmake_build)
            self.assertEqual(cmake_build["stdout"], "saved project\n")
        _, own = self.request("GET", f"/api/projects?profile_id={aid}")
        _, other = self.request("GET", f"/api/projects?profile_id={bid}")
        self.assertEqual(own["workspaces"][0]["files"], files)
        from project_workshop import resolve_cmake
        self.assertEqual(own["cmake_available"], bool(resolve_cmake()))
        self.assertEqual(other["workspaces"], [])
        _, cmake_status = self.request("POST", "/api/devtools/action", {"profile_id": aid, "module": "cmake", "action": "status"})
        self.assertIn("detected" if resolve_cmake() else "not detected", cmake_status["state"]["last"])
        save = self.request("GET", f"/api/export?profile_id={aid}")[1]
        self.request("POST", "/api/import", {"profile_id": aid, "save": save})
        _, restored = self.request("GET", f"/api/projects?profile_id={aid}")
        self.assertEqual(restored["workspaces"][0]["files"], files)

    def test_career_interview_portfolio_are_real_and_profile_scoped(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Career A"})
        _, b = self.request("POST", "/api/profiles", {"name": "Career B"})
        aid, bid = a["profile_id"], b["profile_id"]
        self.request("POST", "/api/settings", {"profile_id": bid, "lang": "ru"})
        _, initial = self.request("GET", f"/api/career?profile_id={aid}")
        self.assertEqual(initial["career"]["level_id"], "beginner")
        self.assertEqual(initial["portfolio"], [])
        _, started = self.request("POST", "/api/interview/start", {"profile_id": aid})
        session_id = started["session_id"]
        self.assertNotIn("answer", started["question"])
        self.assertNotIn("tests", started["question"])
        _, first = self.request("GET", f"/api/interview?profile_id={aid}&session_id={session_id}")
        self.assertGreater(first["remaining_seconds"], 0)
        question = started["question"]
        index = 0
        completed = False
        while not completed:
            if question["kind"] == "choice":
                # Options are shuffled per session; answer by the correct option's text.
                bank = next(q for q in server.INTERVIEW_BANK if q["id"] == question["id"])
                answer = next(question["options"].index(bank["options"][lang][bank["answer"]]) for lang in ("tr", "ru") if bank["options"][lang][bank["answer"]] in question["options"])
            elif question["id"] == "reverse_values":
                answer = "#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> a(n);for(int& x:a)std::cin>>x;for(int i=n-1;i>=0;--i){if(i<n-1)std::cout<<' ';std::cout<<a[i];}}"
            else:
                answer = "#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;int sum=0,x;for(int i=0;i<n;++i){std::cin>>x;sum+=x;if(i)std::cout<<' ';std::cout<<sum;}}"
            _, result = self.request("POST", "/api/interview/answer", {"profile_id": aid, "session_id": session_id, "index": index, "answer": answer})
            completed = result["complete"]
            if not completed:
                question = result["next_question"]
                index += 1
        self.assertEqual(result["score"], 5, result)
        self.assertEqual(result["total"], 5)
        code = "#include <iostream>\n#include <string>\nint main(){std::string ad;std::cin>>ad;std::cout<<\"Merhaba, \"<<ad<<\"!\";}"
        self.request("POST", "/api/project/save", {"profile_id": aid, "project_id": "cat_greeting", "code": code})
        _, note = self.request("POST", "/api/portfolio/note", {"profile_id": aid, "project_id": "cat_greeting", "description": "A small C++ console project.", "technologies": "C++, string, G++"})
        self.assertTrue(note["ok"])
        _, career_a = self.request("GET", f"/api/career?profile_id={aid}")
        _, career_b = self.request("GET", f"/api/career?profile_id={bid}")
        self.assertEqual(career_a["interviews"][0]["score"], 5)
        self.assertFalse(career_a["interviews"][0]["completed"] is False)
        self.assertEqual(career_a["portfolio"][0]["description"], "A small C++ console project.")
        self.assertEqual(career_b["interviews"], [])
        self.assertEqual(career_b["portfolio"], [])
        exported = self.request("GET", f"/api/export?profile_id={aid}")[1]
        self.request("POST", "/api/import", {"profile_id": aid, "save": exported})
        _, restored = self.request("GET", f"/api/career?profile_id={aid}")
        self.assertEqual(restored["interviews"][0]["score"], 5)
        self.assertEqual(restored["portfolio"][0]["technologies"], "C++, string, G++")

    def test_developer_lab_state_is_persistent_and_profile_isolated(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Tools A"})
        _, b = self.request("POST", "/api/profiles", {"name": "Tools B"})
        aid, bid = a["profile_id"], b["profile_id"]
        status, result = self.request("POST", "/api/devtools/action", {"profile_id": aid, "module": "git", "action": "init"})
        self.assertEqual(status, 200)
        self.assertTrue(result["state"]["initialized"])
        state_a = self.request("GET", f"/api/devtools?profile_id={aid}&module=git")[1]["state"]
        state_b = self.request("GET", f"/api/devtools?profile_id={bid}&module=git")[1]["state"]
        self.assertTrue(state_a["initialized"])
        self.assertFalse(state_b["initialized"])

    def test_developer_lab_data_is_included_in_profile_save(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Tools Export"})
        pid = created["profile_id"]
        self.request("POST", "/api/devtools/action", {"profile_id": pid, "module": "terminal", "action": "terminal", "command": "touch lab.txt"})
        saved = self.request("GET", f"/api/export?profile_id={pid}")[1]
        self.assertEqual(saved["profile"]["devtools_state"][0]["module"], "terminal")
        self.request("POST", "/api/devtools/action", {"profile_id": pid, "module": "terminal", "action": "terminal", "command": "mkdir temp"})
        self.request("POST", "/api/import", {"profile_id": pid, "save": saved})
        restored = self.request("GET", f"/api/devtools?profile_id={pid}&module=terminal")[1]["state"]
        self.assertIn("/adventure/lab.txt", restored["files"])
        self.assertNotIn("/adventure/temp", restored["dirs"])

    def test_testing_lab_uses_real_cpp_runner_and_reports_assertion(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Tools Test"})
        pid = created["profile_id"]
        code = "#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2;}"
        status, passed = self.request("POST", "/api/devtools/action", {"profile_id": pid, "module": "testing", "action": "run", "code": code, "input": "21", "expected": "42"})
        self.assertEqual(status, 200)
        self.assertTrue(passed["result"]["tests_passed"], passed)
        _, failed = self.request("POST", "/api/devtools/action", {"profile_id": pid, "module": "testing", "action": "run", "code": code, "input": "21", "expected": "41"})
        self.assertFalse(failed["result"]["tests_passed"])
        self.assertEqual(failed["state"]["runs"], 2)

    def test_knowledge_prediction_uses_minimum_profile_data_and_local_language(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Prediction RU", "lang": "ru"})
        _, b = self.request("POST", "/api/profiles", {"name": "Prediction TR"})
        aid, bid = a["profile_id"], b["profile_id"]
        for _ in range(3):
            self.request("POST", "/api/submit", {"profile_id": aid, "task_id": "c01-01", "answer": "wrong"})
        predicted = self.request("GET", f"/api/journal?profile_id={aid}")[1]
        empty = self.request("GET", f"/api/journal?profile_id={bid}")[1]
        self.assertEqual(predicted["predictions"][0]["risk"], "high")
        self.assertTrue(predicted["predictions"][0]["risk_label"].startswith("Высокая"))
        self.assertEqual(predicted["adaptive_path"]["kind"], "strengthen")
        self.assertEqual(empty["predictions"], [])
        self.assertIn("yeterli", empty["prediction_note"])

    def test_failed_code_mission_is_added_to_spaced_review(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Review Code"})
        pid = created["profile_id"]
        server.record_learning_event(pid, "c01-04", False, "compile")
        with server.db() as con:
            row = con.execute("SELECT interval_days,due_at<=datetime('now','+1 day') FROM review_schedule WHERE profile_id=? AND task_id='c01-04'", (pid,)).fetchone()
        self.assertEqual(row[0], 1)
        self.assertTrue(row[1])
        server.record_learning_event(pid, "c01-04", True)
        with server.db() as con:
            interval = con.execute("SELECT interval_days FROM review_schedule WHERE profile_id=? AND task_id='c01-04'", (pid,)).fetchone()[0]
        self.assertEqual(interval, 3)

    def test_study_time_is_idempotent_and_profile_scoped(self):
        _, a = self.request("POST", "/api/profiles", {"name": "Study Stats A"})
        _, b = self.request("POST", "/api/profiles", {"name": "Study Stats B"})
        aid, bid = a["profile_id"], b["profile_id"]
        session = "8d04995a-37cc-46a8-9c7d-450dc47d74b9"
        pulse = {"profile_id": aid, "session_id": session, "day": "2026-11-14", "seconds": 30}
        self.assertEqual(self.request("POST", "/api/study/pulse", pulse)[0], 200)
        self.request("POST", "/api/study/pulse", {**pulse, "seconds": 70})  # within the pulse slack
        self.request("POST", "/api/study/pulse", pulse)  # stale retries must not add time
        stats_a = self.request("GET", f"/api/stats?profile_id={aid}")[1]
        stats_b = self.request("GET", f"/api/stats?profile_id={bid}")[1]
        self.assertEqual(stats_a["study_seconds_30d"], 70)
        self.assertEqual(stats_b["study_seconds_30d"], 0)
        self.assertEqual(stats_a["study_days_30d"], 1)

    def test_study_pulse_validates_session_limits(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Study Validation"})
        pid = created["profile_id"]
        invalid = self.request("POST", "/api/study/pulse", {"profile_id": pid, "session_id": "bad", "day": "2026-11-14", "seconds": 50_000})
        self.assertEqual(invalid[0], 400)

    def test_study_time_cannot_grow_faster_than_the_clock(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Study Clock"})
        pid = created["profile_id"]
        pulse = {"profile_id": pid, "session_id": "5b0e3f4c-9d55-4f8e-8b36-1f7f4c2a9e01", "day": "2026-11-14"}
        self.request("POST", "/api/study/pulse", {**pulse, "seconds": 40_000})  # first pulse is capped
        first = self.request("GET", f"/api/stats?profile_id={pid}")[1]["study_seconds_30d"]
        self.assertEqual(first, server.STUDY_FIRST_PULSE_MAX_SECONDS)
        self.request("POST", "/api/study/pulse", {**pulse, "seconds": 40_000})  # an instant 11-hour jump
        second = self.request("GET", f"/api/stats?profile_id={pid}")[1]["study_seconds_30d"]
        self.assertLessEqual(second, first + server.STUDY_PULSE_SLACK_SECONDS + 2)

    def test_study_time_survives_profile_export_and_import(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Study Backup"})
        pid = created["profile_id"]
        self.request("POST", "/api/study/pulse", {"profile_id": pid, "session_id": "82ecf4bb-01ce-4c44-87bd-41f3a531b9b9", "day": "2026-11-14", "seconds": 120})
        save = self.request("GET", f"/api/export?profile_id={pid}")[1]
        self.request("POST", "/api/study/pulse", {"profile_id": pid, "session_id": "927bf938-0b1c-45dc-aed7-1420e427e161", "day": "2026-11-14", "seconds": 30})
        self.request("POST", "/api/import", {"profile_id": pid, "save": save})
        stats = self.request("GET", f"/api/stats?profile_id={pid}")[1]
        self.assertEqual(stats["study_seconds_30d"], 120)

    def test_advanced_statistics_are_aggregated_from_learning_events(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Stats Accuracy"})
        pid = created["profile_id"]
        server.record_learning_event(pid, "c01-04", False, "compile")
        server.record_learning_event(pid, "c01-04", True)
        stats = self.request("GET", f"/api/stats?profile_id={pid}")[1]
        topic = next(item for item in stats["topics"] if item["chapter_id"] == "c01")
        self.assertEqual((topic["attempts"], topic["correct"], topic["accuracy"]), (2, 1, 0.5))
        self.assertEqual(stats["errors"][0], {"error_kind": "compile", "count": 1})

    def test_algorithm_and_memory_visual_lab_awards_are_profiled_once(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Algorithm Lab"})
        pid = created["profile_id"]
        _, simulation = self.request("POST", "/api/labs/simulate", {"profile_id": pid, "lab_id": "algorithms", "values": {"algorithm": "selection_sort", "values": "4,1,3,2"}})
        self.assertEqual(simulation["steps"][-1]["cells"][-1]["value"], 4)
        _, award = self.request("POST", "/api/labs/submit", {"profile_id": pid, "lab_id": "algorithms", "values": {"algorithm": "selection_sort", "values": "4,1,3,2"}, "answer": "1, 2, 3, 4"})
        self.assertTrue(award["correct"])
        self.assertEqual(award["xp"], 18)
        _, repeat = self.request("POST", "/api/labs/submit", {"profile_id": pid, "lab_id": "algorithms", "values": {"algorithm": "selection_sort", "values": "4,1,3,2"}, "answer": "1, 2, 3, 4"})
        self.assertEqual(repeat["xp"], 0)
        _, memory = self.request("POST", "/api/labs/submit", {"profile_id": pid, "lab_id": "memory", "values": {"scenario": "stack"}, "answer": "LIFO"})
        self.assertTrue(memory["correct"])


if __name__ == "__main__":
    unittest.main()
