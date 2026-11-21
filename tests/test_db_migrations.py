"""Schema migrations: fresh DB, old-version DB, realistic progress, interrupted upgrade, newer DB."""
import hashlib
import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

import db_migrations
import server

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = {"shop": server.SHOP, "task_chapter": server.TASK_CHAPTER}
EXPECTED_INDEXES = {"idx_learning_events_profile_task", "idx_learning_events_profile_time", "idx_review_schedule_due", "idx_study_sessions_day"}


def make_v0_database(path: Path) -> None:
    """A database as the app wrote it before schema versioning (older profiles table, fewer tables)."""
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE profiles(id TEXT PRIMARY KEY, name TEXT NOT NULL, avatar TEXT NOT NULL DEFAULT '🐱', pin_hash TEXT NOT NULL DEFAULT '',
                              xp INTEGER NOT NULL DEFAULT 0, lang TEXT NOT NULL DEFAULT 'tr', streak INTEGER NOT NULL DEFAULT 0,
                              last_day TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE completions(profile_id TEXT NOT NULL, task_id TEXT NOT NULL, completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 xp INTEGER NOT NULL, PRIMARY KEY(profile_id, task_id));
        CREATE TABLE quiz_results(profile_id TEXT NOT NULL, task_id TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, correct INTEGER NOT NULL DEFAULT 0,
                                  last_answer TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,task_id));
        CREATE TABLE shop_items(profile_id TEXT NOT NULL, item_id TEXT NOT NULL, bought_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,item_id));
    """)
    tasks = server.all_tasks()[:6]
    con.execute("INSERT INTO profiles(id,name,xp,streak,last_day) VALUES('p1','Ada',140,3,'2026-11-10')")
    con.execute("INSERT INTO profiles(id,name,xp) VALUES('p2','Борис',0)")
    con.executemany("INSERT INTO completions(profile_id,task_id,xp,completed_at) VALUES('p1',?,?,'2026-11-0' || ?)",
                    [(task["id"], task["xp"], str(i + 1)) for i, task in enumerate(tasks)])
    con.execute("INSERT INTO quiz_results(profile_id,task_id,attempts,correct,last_answer) VALUES('p1',?,2,1,'main')", (tasks[0]["id"],))
    item = next(iter(server.SHOP))
    con.execute("INSERT INTO shop_items(profile_id,item_id) VALUES('p1',?)", (item,))
    con.execute("ALTER TABLE profiles ADD COLUMN active_item TEXT NOT NULL DEFAULT ''")
    con.execute("UPDATE profiles SET active_item=? WHERE id='p1'", (item,))
    con.commit()
    con.close()


def table_names(path):
    con = sqlite3.connect(path)
    try:
        return {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}, \
               {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}
    finally:
        con.close()


def version_of(path):
    con = sqlite3.connect(path)
    try:
        return con.execute("PRAGMA user_version").fetchone()[0]
    finally:
        con.close()


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.db = self.dir / "adventure.db"
        self.backups = self.dir / "backups"

    def tearDown(self):
        self.temp.cleanup()

    def test_fresh_database_gets_full_schema_and_no_backup(self):
        applied = db_migrations.migrate(self.db, context=CONTEXT, backup_dir=self.backups)
        self.assertEqual(applied, [m[0] for m in db_migrations.MIGRATIONS])
        tables, indexes = table_names(self.db)
        # Baseline tables plus the ones later migrations add (m4: hint_reveals).
        self.assertEqual(len(tables - {"sqlite_sequence", "hint_reveals"}), len(db_migrations.BASELINE_TABLES))
        self.assertIn("hint_reveals", tables)
        self.assertTrue(EXPECTED_INDEXES <= indexes)
        self.assertEqual(version_of(self.db), db_migrations.LATEST_VERSION)
        self.assertFalse(self.backups.exists())

    def test_old_database_is_upgraded_without_losing_progress(self):
        make_v0_database(self.db)
        db_migrations.migrate(self.db, context=CONTEXT, backup_dir=self.backups)
        con = sqlite3.connect(self.db)
        con.row_factory = sqlite3.Row
        p1 = con.execute("SELECT * FROM profiles WHERE id='p1'").fetchone()
        self.assertEqual((p1["name"], p1["xp"], p1["streak"], p1["ai_provider"]), ("Ada", 140, 3, "offline"))
        self.assertEqual(con.execute("SELECT name FROM profiles WHERE id='p2'").fetchone()[0], "Борис")
        self.assertEqual(con.execute("SELECT COUNT(*) FROM completions WHERE profile_id='p1'").fetchone()[0], 6)
        self.assertEqual(con.execute("SELECT attempts FROM quiz_results").fetchone()[0], 2)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM learning_events WHERE profile_id='p1' AND correct=1").fetchone()[0], 6)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM companion_equipment WHERE profile_id='p1'").fetchone()[0], 1)
        con.close()
        self.assertEqual(version_of(self.db), db_migrations.LATEST_VERSION)
        backups = list(self.backups.glob("adventure-before-schema-*.db"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(version_of(backups[0]), 0)  # the backup is the untouched original
        old = sqlite3.connect(backups[0])
        self.assertEqual(old.execute("SELECT xp FROM profiles WHERE id='p1'").fetchone()[0], 140)
        old.close()

    def test_second_run_changes_nothing_and_does_not_repeat_the_backfill(self):
        make_v0_database(self.db)
        db_migrations.migrate(self.db, context=CONTEXT, backup_dir=self.backups)
        self.assertEqual(db_migrations.migrate(self.db, context=CONTEXT, backup_dir=self.backups), [])
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0], 6)
        con.close()
        self.assertEqual(len(list(self.backups.glob("*.db"))), 1)

    def test_interrupted_migration_rolls_back_and_can_be_retried(self):
        make_v0_database(self.db)

        def broken(con, ctx):
            con.execute("CREATE TABLE half_done(x INTEGER)")
            raise RuntimeError("power loss")

        steps = (db_migrations.MIGRATIONS[0], (2, "broken", broken))
        with self.assertRaises(RuntimeError):
            db_migrations.migrate(self.db, context=CONTEXT, backup_dir=self.backups, migrations=steps)
        self.assertEqual(version_of(self.db), 1)
        tables, _ = table_names(self.db)
        self.assertNotIn("half_done", tables)
        db_migrations.migrate(self.db, context=CONTEXT, backup_dir=self.backups)  # the real chain resumes from v1
        self.assertEqual(version_of(self.db), db_migrations.LATEST_VERSION)
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT xp FROM profiles WHERE id='p1'").fetchone()[0], 140)
        con.close()

    def test_database_from_a_newer_app_is_left_untouched(self):
        db_migrations.migrate(self.db, context=CONTEXT)
        con = sqlite3.connect(self.db)
        con.execute("PRAGMA user_version=99")
        con.commit()
        con.close()
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        with self.assertRaises(db_migrations.NewerDatabaseError):
            db_migrations.migrate(self.db, context=CONTEXT, backup_dir=self.backups)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), before)

    def test_real_local_database_copy_upgrades_cleanly(self):
        source = ROOT / "data" / "adventure.db"
        if not source.is_file():
            self.skipTest("no local development database present")
        copy = self.dir / "copy.db"
        src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)  # read-only: the real file is never modified
        dst = sqlite3.connect(copy)
        src.backup(dst)
        counts = {t: src.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("profiles", "completions")}
        src.close()
        dst.close()
        db_migrations.migrate(copy, context=CONTEXT, backup_dir=self.backups)
        con = sqlite3.connect(copy)
        for table, count in counts.items():
            self.assertEqual(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], count, table)
        self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        con.close()


class SaveRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old = (server.DB_PATH, server.DATA_ROOT)
        server.DB_PATH = Path(cls.temp.name) / "roundtrip.db"
        server.DATA_ROOT = Path(cls.temp.name)
        server.init_db()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        server.DB_PATH, server.DATA_ROOT = cls.old
        cls.temp.cleanup()

    def request(self, method, path, data=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.http.server_address[1], timeout=30)
        conn.request(method, path, json.dumps(data).encode() if data is not None else None, {"Content-Type": "application/json"} if data is not None else {})
        response = conn.getresponse()
        result = response.status, json.loads(response.read())
        conn.close()
        return result

    def test_export_v2_round_trips_ai_usage_and_v1_saves_still_import(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Yedek"})
        pid = created["profile_id"]
        with server.db() as con:
            con.execute("INSERT INTO ai_usage(profile_id,provider,model,input_tokens,output_tokens,requests,estimated_usd) VALUES(?,?,?,?,?,?,?)", (pid, "claude", "claude-haiku-5-5", 1200, 300, 4, 0.00027))
        _, save = self.request("GET", f"/api/export?profile_id={pid}")
        self.assertEqual(save["version"], 2)
        self.assertEqual(save["profile"]["ai_usage"][0]["requests"], 4)
        with server.db() as con:
            con.execute("DELETE FROM ai_usage WHERE profile_id=?", (pid,))
        self.assertEqual(self.request("POST", "/api/import", {"profile_id": pid, "save": save})[0], 200)
        with server.db() as con:
            self.assertEqual(con.execute("SELECT requests FROM ai_usage WHERE profile_id=?", (pid,)).fetchone()[0], 4)
        legacy = json.loads(json.dumps(save))
        legacy["version"] = 1
        legacy["profile"].pop("ai_usage")
        self.assertEqual(self.request("POST", "/api/import", {"profile_id": pid, "save": legacy})[0], 200)
        self.assertEqual(self.request("POST", "/api/import", {"profile_id": pid, "save": {**save, "version": 3}})[0], 400)

    def test_whole_database_backup_is_a_verified_copy(self):
        _, created = self.request("POST", "/api/profiles", {"name": "Tam Yedek"})
        status, result = self.request("POST", "/api/backup/database", {"profile_id": created["profile_id"]})
        self.assertEqual(status, 200, result)
        backup = Path(result["path"])
        self.assertTrue(backup.is_file())
        con = sqlite3.connect(backup)
        self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertGreaterEqual(con.execute("SELECT COUNT(*) FROM profiles").fetchone()[0], 1)
        con.close()


if __name__ == "__main__":
    unittest.main()
