"""Versioned SQLite schema migrations for C++ Adventure.

The schema version lives in ``PRAGMA user_version``. Each migration runs inside its own
``BEGIN IMMEDIATE`` transaction together with the version bump, so an interrupted upgrade
(crash, power loss, exception) leaves the database at the previous version and is retried
on the next start. Before upgrading a database that already holds profiles, a verified
copy is written with SQLite's online backup API. Databases written by a *newer* app version
are never downgraded; startup stops instead of risking data loss.

Adding a migration: append ``(next_number, "description", function)`` to ``MIGRATIONS``.
Never edit a migration that has shipped.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

BASELINE_TABLES = (
    "CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY, name TEXT NOT NULL, avatar TEXT NOT NULL DEFAULT '🐱', pin_hash TEXT NOT NULL DEFAULT '', xp INTEGER NOT NULL DEFAULT 0, lang TEXT NOT NULL DEFAULT 'tr', streak INTEGER NOT NULL DEFAULT 0, last_day TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, active_item TEXT NOT NULL DEFAULT '', ai_provider TEXT NOT NULL DEFAULT 'offline')",
    "CREATE TABLE IF NOT EXISTS completions(profile_id TEXT NOT NULL, task_id TEXT NOT NULL, completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, xp INTEGER NOT NULL, PRIMARY KEY(profile_id, task_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS achievements(profile_id TEXT NOT NULL, id TEXT NOT NULL, unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id, id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS quiz_results(profile_id TEXT NOT NULL, task_id TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, correct INTEGER NOT NULL DEFAULT 0, last_answer TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,task_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS review_schedule(profile_id TEXT NOT NULL, task_id TEXT NOT NULL, due_at TEXT NOT NULL, interval_days INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(profile_id,task_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS daily_quests(profile_id TEXT NOT NULL, day TEXT NOT NULL, task_id TEXT NOT NULL, reward INTEGER NOT NULL DEFAULT 15, completed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(profile_id,day), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS shop_items(profile_id TEXT NOT NULL, item_id TEXT NOT NULL, bought_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,item_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS companion_equipment(profile_id TEXT NOT NULL, slot TEXT NOT NULL, item_id TEXT NOT NULL, equipped_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,slot), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS companion_loadouts(profile_id TEXT NOT NULL, loadout_id TEXT NOT NULL, name TEXT NOT NULL, equipment_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,loadout_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS project_submissions(profile_id TEXT NOT NULL, project_id TEXT NOT NULL, code TEXT NOT NULL DEFAULT '', score INTEGER NOT NULL DEFAULT 0, completed INTEGER NOT NULL DEFAULT 0, awarded INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,project_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS project_workspaces(profile_id TEXT NOT NULL, workspace_id TEXT NOT NULL, name TEXT NOT NULL, files_json TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,workspace_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS interview_sessions(profile_id TEXT NOT NULL, session_id TEXT NOT NULL, lang TEXT NOT NULL, questions_json TEXT NOT NULL, answers_json TEXT NOT NULL DEFAULT '[]', score INTEGER NOT NULL DEFAULT 0, completed INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT NOT NULL DEFAULT '', PRIMARY KEY(profile_id,session_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS portfolio_notes(profile_id TEXT NOT NULL, project_id TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', technologies TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,project_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS ai_usage(profile_id TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0, requests INTEGER NOT NULL DEFAULT 0, estimated_usd REAL NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,provider,model), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS learning_events(id INTEGER PRIMARY KEY AUTOINCREMENT, profile_id TEXT NOT NULL, task_id TEXT NOT NULL, chapter_id TEXT NOT NULL, correct INTEGER NOT NULL DEFAULT 0, error_kind TEXT NOT NULL DEFAULT '', hint_used INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS lab_awards(profile_id TEXT NOT NULL, lab_id TEXT NOT NULL, xp INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,lab_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS devtools_state(profile_id TEXT NOT NULL, module TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,module), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS study_sessions(profile_id TEXT NOT NULL, session_id TEXT NOT NULL, day TEXT NOT NULL, seconds INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,session_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS arena_attempts(profile_id TEXT NOT NULL, day TEXT NOT NULL, challenge_id TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, best_score INTEGER NOT NULL DEFAULT 0, best_elapsed_ms INTEGER NOT NULL DEFAULT 0, awarded_xp INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,day,challenge_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS admin_bonus(profile_id TEXT PRIMARY KEY, level_xp INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
    "CREATE TABLE IF NOT EXISTS plugin_settings(profile_id TEXT NOT NULL, plugin_id TEXT NOT NULL, version TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,plugin_id), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)",
)


def _m1_baseline(con, ctx):
    """Every table the app had before versioning; safe on old databases (IF NOT EXISTS + column adds)."""
    for statement in BASELINE_TABLES:
        con.execute(statement)
    columns = {row[1] for row in con.execute("PRAGMA table_info(profiles)")}
    if "active_item" not in columns:
        con.execute("ALTER TABLE profiles ADD COLUMN active_item TEXT NOT NULL DEFAULT ''")
    if "ai_provider" not in columns:
        con.execute("ALTER TABLE profiles ADD COLUMN ai_provider TEXT NOT NULL DEFAULT 'offline'")
    # Old single-item appearance -> slot model, keeping profiles.active_item untouched.
    shop = ctx.get("shop", {})
    for row in con.execute("SELECT id,active_item FROM profiles WHERE active_item!=''").fetchall():
        item = shop.get(row["active_item"])
        owned = con.execute("SELECT 1 FROM shop_items WHERE profile_id=? AND item_id=?", (row["id"], row["active_item"])).fetchone()
        if item and owned:
            con.execute("INSERT OR IGNORE INTO companion_equipment(profile_id,slot,item_id) VALUES(?,?,?)", (row["id"], item["slot"], row["active_item"]))


def _m2_indexes(con, ctx):
    """Indexes for the per-profile history queries (journal, stats, review, learning insights)."""
    con.execute("CREATE INDEX IF NOT EXISTS idx_learning_events_profile_task ON learning_events(profile_id, task_id, correct)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_learning_events_profile_time ON learning_events(profile_id, created_at)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_review_schedule_due ON review_schedule(profile_id, due_at)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_study_sessions_day ON study_sessions(profile_id, day)")


def _m3_backfill_learning_events(con, ctx):
    """One-time backfill (previously re-run on every startup): a correct event per old completion."""
    chapter_of = ctx.get("task_chapter", {})
    seen = {(row[0], row[1]) for row in con.execute("SELECT profile_id, task_id FROM learning_events WHERE correct=1")}
    rows = [(row["profile_id"], row["task_id"], chapter_of[row["task_id"]], row["completed_at"])
            for row in con.execute("SELECT profile_id, task_id, completed_at FROM completions")
            if row["task_id"] in chapter_of and (row["profile_id"], row["task_id"]) not in seen]
    con.executemany("INSERT INTO learning_events(profile_id,task_id,chapter_id,correct,created_at) VALUES(?,?,?,1,?)", rows)


def _m4_hint_reveals(con, ctx):
    """Hints are revealed by the server so the reward penalty no longer depends on the client."""
    con.execute("CREATE TABLE IF NOT EXISTS hint_reveals(profile_id TEXT NOT NULL, task_id TEXT NOT NULL, level INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(profile_id,task_id,level), FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE)")


MIGRATIONS = (
    (1, "baseline schema", _m1_baseline),
    (2, "history indexes", _m2_indexes),
    (3, "learning event backfill", _m3_backfill_learning_events),
    (4, "server-side hint reveals", _m4_hint_reveals),
)
LATEST_VERSION = MIGRATIONS[-1][0]


class NewerDatabaseError(RuntimeError):
    """The database was written by a newer app version; refusing to touch it."""


def schema_version(con) -> int:
    return int(con.execute("PRAGMA user_version").fetchone()[0])


def backup_database(source: Path, backup_dir: Path, label: str) -> Path:
    """Copy a live database with SQLite's online backup API and verify the copy."""
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"adventure-{label}-{stamp}.db"
    counter = 1
    while target.exists():
        counter += 1
        target = backup_dir / f"adventure-{label}-{stamp}-{counter}.db"
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    check = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise sqlite3.DatabaseError(f"backup {target} failed integrity_check")
    finally:
        check.close()
    return target


def _has_profiles(con) -> bool:
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='profiles'").fetchone():
        return False
    return con.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] > 0


def migrate(db_path: Path, *, context: dict | None = None, backup_dir: Path | None = None, migrations=MIGRATIONS) -> list[int]:
    """Bring the database to the latest version. Returns the migration numbers applied."""
    context = context or {}
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, timeout=30, isolation_level=None)  # explicit transactions only
    con.row_factory = sqlite3.Row
    applied: list[int] = []
    try:
        con.execute("PRAGMA journal_mode=WAL")  # persistent; set once here, not on every connection
        con.execute("PRAGMA foreign_keys=ON")
        current = schema_version(con)
        latest = migrations[-1][0]
        if current > latest:
            raise NewerDatabaseError(
                f"Veritabanı daha yeni bir uygulama sürümüne ait (şema {current} > {latest}); veriyi korumak için açılmadı. "
                f"/ База данных от более новой версии (схема {current} > {latest}); открытие отменено ради сохранности данных.")
        pending = [m for m in migrations if m[0] > current]
        if pending and backup_dir is not None and _has_profiles(con):
            backup_database(db_path, backup_dir, f"before-schema-v{pending[-1][0]}-from-v{current}")
        for number, _description, step in pending:
            con.execute("BEGIN IMMEDIATE")
            try:
                step(con, context)
                con.execute(f"PRAGMA user_version={int(number)}")
                con.execute("COMMIT")
            except BaseException:
                con.execute("ROLLBACK")
                raise
            applied.append(number)
    finally:
        con.close()
    return applied
