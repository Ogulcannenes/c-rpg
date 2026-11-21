from __future__ import annotations

import atexit
import json
import os
import re
from collections import OrderedDict
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import hashlib
import hmac
import secrets
import uuid
import platform
import sys
from contextlib import contextmanager
import time
import webbrowser
import urllib.request
import urllib.error
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from curriculum import CURRICULUM
from secret_store import delete_secret, read_secret, write_secret
from db_migrations import backup_database, migrate as migrate_database
from sandbox import SandboxBusy, assembly_policy_violation, build_slot, isolation_status, normalize_output, run_limited, run_tool, source_policy_violation
from concept_checker import check_cpp_concept
from visual_labs import LABS, simulate as simulate_visual_lab, public_result as public_lab_result
from lesson_scenes import scenes_for as lesson_scenes_for
from workshop_projects import extend_projects, TEMPLATES as WORKSPACE_TEMPLATES
from devtools import initial_state as initial_devtool_state, apply as apply_devtool_action
from learning_engine import learning_insights
from project_workshop import validate_files as validate_project_files, build_project as build_project_workspace, resolve_cmake
from career_system import CAREER_LEVELS, INTERVIEW_BANK, career_summary, select_interview_questions
from rpg_system import SECRET_QUESTS, guild_summary, quest_by_id
from advanced_cpp import assembly_outputs, simulate_counter
from arena_system import CHALLENGES, daily_challenge
from plugin_system import MAX_PLUGIN_BYTES, discover_plugins, install_plugin, remove_plugin

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA_ROOT = (Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "CppAdventure") if getattr(sys, "frozen", False) else ROOT
DB_PATH = DATA_ROOT / "data" / "adventure.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
COMPILER = shutil.which("g++") or shutil.which("clang++")
DB_LOCK = threading.Lock()
MAX_SOURCE = 20_000
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}
# Per-route request body caps; everything else is limited to 30 KB.
POST_BODY_LIMITS = {
    "/api/plugins/install": MAX_PLUGIN_BYTES + 2048,  # manifest + JSON envelope
    "/api/import": 8 * 1024 * 1024,  # a full save: code, workspaces, up to 5,000 learning events
}
OPENAI_MODEL = os.environ.get("CPP_ADVENTURE_OPENAI_MODEL", "gpt-6-astra")
OLLAMA_URL = os.environ.get("CPP_ADVENTURE_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("CPP_ADVENTURE_OLLAMA_MODEL", "qwen2.5-coder:3b")
# Claude: the small, inexpensive Haiku model is enough for short tutoring hints.
CLAUDE_MODEL = os.environ.get("CPP_ADVENTURE_CLAUDE_MODEL", "claude-haiku-5-5")
CLAUDE_PRICES = {"claude-haiku-5-5": (0.10, 0.50)}  # USD per million input/output tokens (prompts up to 100k tokens)
# The key lives outside the project and outside the database, so it is never exported, committed or sent to the page.
SECRETS_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config")) / "CppAdventure" / "secrets"
CLAUDE_KEY_FILE = SECRETS_DIR / "anthropic_api_key"
TUTOR_SYSTEM = "You are a patient C++ tutor inside a cat-themed learning app. Reply in the requested language. Diagnose the learner's actual mistake, explain the cause, then give one progressive hint. Do not provide the complete solution unless the learner explicitly asks for a detailed explanation. Keep it under 160 words."


# Free online tutor: Groq's free plan needs no card and returns HTTP 429 instead of charging when its limits are hit.
GROQ_MODEL = os.environ.get("CPP_ADVENTURE_GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODEL = os.environ.get("CPP_ADVENTURE_GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")
API_KEYS = {
    "claude": {"env": "ANTHROPIC_API_KEY", "file": "anthropic_api_key", "pattern": r"sk-ant-[A-Za-z0-9_\-]{20,300}", "error": "Bu bir Claude API anahtarına benzemiyor (sk-ant- ile başlamalı)."},
    "groq": {"env": "GROQ_API_KEY", "file": "groq_api_key", "pattern": r"gsk_[A-Za-z0-9]{20,200}", "error": "Bu bir Groq API anahtarına benzemiyor (gsk_ ile başlamalı)."},
}


def provider_key(provider):
    spec = API_KEYS[provider]
    key = os.environ.get(spec["env"], "").strip()
    if key:
        return key
    return read_secret(SECRETS_DIR, spec["file"])  # DPAPI-encrypted on Windows


def provider_key_from_env(provider):
    return bool(os.environ.get(API_KEYS[provider]["env"], "").strip())


def save_provider_key(provider, key):
    spec, key = API_KEYS[provider], (key or "").strip()
    if not key:
        delete_secret(SECRETS_DIR, spec["file"])
        return
    if not re.fullmatch(spec["pattern"], key):
        raise ValueError(spec["error"])
    write_secret(SECRETS_DIR, spec["file"], key)


def claude_api_key():
    return provider_key("claude")


def save_claude_api_key(key):
    save_provider_key("claude", key)


APP_VERSION = "0.4.0"


@contextmanager
def temporary_directory(prefix: str):
    """Clean compiler scratch dirs reliably when Windows briefly locks an exe."""
    folder = tempfile.TemporaryDirectory(prefix=prefix)
    try:
        yield folder.name
    finally:
        for attempt in range(5):
            try:
                folder.cleanup()
                break
            except PermissionError:
                if os.name != "nt" or attempt == 4:
                    raise
                time.sleep(0.05 * (attempt + 1))
SHOP = {
    "yarn": {"cost": 250, "icon": "🧶", "slot": "toy", "name": {"tr": "Balıkçı kedinin yumağı", "ru": "Клубок кота-рыбака"}, "description": {"tr": "Pati altında taşınan yumuşak oyuncak.", "ru": "Мягкая игрушка у лапки."}},
    "scarf": {"cost": 450, "icon": "🧣", "slot": "neck", "name": {"tr": "Kışlık pati atkısı", "ru": "Зимний шарфик"}, "description": {"tr": "Soğuk kodlama gecelerine sıcaklık.", "ru": "Согревает в холодные ночи кода."}},
    "wizard": {"cost": 700, "icon": "🧙", "slot": "head", "name": {"tr": "Bilge büyücü şapkası", "ru": "Шляпа мудрого волшебника"}, "description": {"tr": "Yeni konuları sihirle çöz.", "ru": "Решай новые темы с помощью магии."}},
    "shades": {"cost": 800, "icon": "🕶️", "slot": "face", "name": {"tr": "Piksel güneş gözlüğü", "ru": "Пиксельные солнечные очки"}, "description": {"tr": "Parlak ekranlara karşı kod modu.", "ru": "Режим кода против яркого экрана."}},
    "moon": {"cost": 950, "icon": "🌙", "slot": "back", "name": {"tr": "Ay ışığı pelerini", "ru": "Лунный плащ"}, "description": {"tr": "Gece vardiyasının parıltılı pelerini.", "ru": "Сияющий плащ ночной смены."}},
    "bowtie": {"cost": 1000, "icon": "🤵", "slot": "neck", "name": {"tr": "Kod papyonu", "ru": "Бабочка программиста"}, "description": {"tr": "Sunum günlerinin şık dokunuşu.", "ru": "Элегантный штрих для дней презентаций."}},
    "bow": {"cost": 1200, "icon": "🎀", "slot": "head", "name": {"tr": "Pembe pati fiyonk", "ru": "Розовый бантик лапки"}, "description": {"tr": "Kedinin kulakları arasına takılır.", "ru": "Украшает ушки кота."}},
    "mug": {"cost": 1400, "icon": "☕", "slot": "toy", "name": {"tr": "Kod kupası", "ru": "Кружка для кода"}, "description": {"tr": "Uzun debug gecelerinin sıcak dostu.", "ru": "Тёплый друг долгих ночей отладки."}},
    "headset": {"cost": 1550, "icon": "🎧", "slot": "ears", "name": {"tr": "Neon oyun kulaklığı", "ru": "Неоновые игровые наушники"}, "description": {"tr": "Odaklanma modu: mırlama açık.", "ru": "Режим фокуса: мурчание включено."}},
    "raincoat": {"cost": 1900, "icon": "🧥", "slot": "body", "name": {"tr": "Kod yağmurluğu", "ru": "Плащ программиста"}, "description": {"tr": "Hataları üzerinden kaydırıp atar.", "ru": "Ошибки скатываются, как капли."}},
    "cape": {"cost": 2100, "icon": "🦸", "slot": "back", "name": {"tr": "Kahraman pelerini", "ru": "Плащ героя"}, "description": {"tr": "Her derlemeyi kahramanca karşıla.", "ru": "Встречай каждую сборку как герой."}},
    "fish": {"cost": 2300, "icon": "🐟", "slot": "toy", "name": {"tr": "Altın balık oyuncağı", "ru": "Золотая рыбка-игрушка"}, "description": {"tr": "Boss savaşlarından kalan ganimet.", "ru": "Трофей после битвы с боссом."}},
    "wings": {"cost": 2600, "icon": "👼", "slot": "back", "name": {"tr": "Melek kanatları", "ru": "Ангельские крылья"}, "description": {"tr": "Hatasız derlemelerin hafif kanatları.", "ru": "Лёгкие крылья безошибочных сборок."}},
    "backpack": {"cost": 2800, "icon": "🎒", "slot": "back", "name": {"tr": "Gezgin kedi sırt çantası", "ru": "Рюкзак кота-путешественника"}, "description": {"tr": "Bütün macera notları yanında.", "ru": "Все заметки о приключениях рядом."}},
    "aura": {"cost": 3000, "icon": "✨", "slot": "aura", "name": {"tr": "Yıldız tozu aurası", "ru": "Аура звёздной пыли"}, "description": {"tr": "Seni bir seviye parlak gösterir.", "ru": "Делает тебя ярче на целый уровень."}},
    "crown": {"cost": 3400, "icon": "👑", "slot": "head", "name": {"tr": "C++ kralı tacı", "ru": "Корона короля C++"}, "description": {"tr": "Efsane seviyeye yakışan ödül.", "ru": "Награда для настоящей легенды."}}
}
PROFILE_AVATARS = ("🐱","🐈","😺","😸","😼","🐈‍⬛","🦊","🐯","🐻","🐼","c:buddy","c:prof","c:teach","c:hack","c:debug","c:wiz","c:boss")
PROJECTS = [
    {"id":"cat_greeting","xp":70,"title":{"tr":"Kedi selamlama botu","ru":"Кот-бот приветствия"},"description":{"tr":"Bir isim oku ve kişiye özel kedi selamı yazdır.","ru":"Прочитай имя и выведи персональное кошачье приветствие."},"starter":"#include <iostream>\n#include <string>\nint main() {\n    std::string ad;\n    std::cin >> ad;\n    // selamla\n    return 0;\n}","requires":["std::string","std::cin","std::cout"],"tests":[{"input":"Luna","expected":"Merhaba, Luna!"},{"input":"Mavi","expected":"Merhaba, Mavi!"}]},
    {"id":"score_tracker","xp":100,"title":{"tr":"Pati puan takipçisi","ru":"Счётчик очков лапки"},"description":{"tr":"Üç görev puanını oku ve toplamı hesapla. Negatif ve sıfır değerleri de dene.","ru":"Прочитай три результата и вычисли сумму. Проверь отрицательные и нулевые значения."},"starter":"#include <iostream>\nint main() {\n    int a, b, c;\n    std::cin >> a >> b >> c;\n    // toplamı yazdır\n    return 0;\n}","requires":["std::cin","std::cout","+"],"tests":[{"input":"3 4 5","expected":"12"},{"input":"-2 2 0","expected":"0"},{"input":"7 7 7","expected":"21"}]},
    {"id":"algorithm_sort","xp":140,"title":{"tr":"Balık pazarını sırala","ru":"Сортировка рыбного рынка"},"description":{"tr":"N sayısını ve ardından N tam sayı oku; sayıları küçükten büyüğe sırala. Big O düşün: std::sort O(N log N) çalışır.","ru":"Прочитай N и затем N целых чисел; отсортируй их по возрастанию. Подумай о Big O: std::sort работает за O(N log N)."},"starter":"#include <iostream>\n#include <vector>\n#include <algorithm>\nint main() {\n    int n; std::cin >> n;\n    std::vector<int> v(n);\n    for (int& x : v) std::cin >> x;\n    // sırala ve yazdır\n    return 0;\n}","requires":["std::sort","vector","std::cout"],"tests":[{"input":"5 4 1 3 2 0","expected":"0 1 2 3 4 "},{"input":"1 -7","expected":"-7 "},{"input":"0","expected":""}]},
]
extend_projects(PROJECTS)


@contextmanager
def db(immediate=False):
    """Open a connection; commit on success, roll back on any exception.

    immediate=True takes SQLite's write lock (BEGIN IMMEDIATE) before the first
    read, so read-then-award paths cannot both see "not yet awarded" when two
    requests race. Never nest an immediate block inside another db() block.
    """
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    # journal_mode=WAL is persistent and set once by the migration runner.
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA foreign_keys=ON")
    if immediate:
        con.execute("BEGIN IMMEDIATE")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def migrate_legacy_database(source_path, target_path=None):
    """Copy existing profile data into the desktop app's data folder without replacing progress."""
    source = Path(source_path).expanduser()
    target = Path(target_path or DB_PATH)
    if not source.is_file() or source.resolve() == target.resolve():
        return False

    def profile_count(connection):
        table = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='profiles'").fetchone()
        return connection.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] if table else 0

    old_db = current_db = None
    try:
        old_db = sqlite3.connect(str(source), timeout=10)
        if profile_count(old_db) == 0:
            return False
        current_profiles = 0
        if target.is_file():
            current_db = sqlite3.connect(str(target), timeout=10)
            current_profiles = profile_count(current_db)
            current_db.close()
            current_db = None
        if current_profiles:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = target.with_suffix(target.suffix + ".pre-migration.bak")
            if not backup.exists():
                shutil.copy2(target, backup)
        current_db = sqlite3.connect(str(target), timeout=10)
        old_db.backup(current_db)
        current_db.commit()
        return True
    except (OSError, sqlite3.Error):
        return False
    finally:
        if current_db is not None:
            current_db.close()
        if old_db is not None:
            old_db.close()


def init_db():
    legacy_path = os.environ.get("CPP_ADVENTURE_LEGACY_DB", "")
    if not legacy_path and getattr(sys, "frozen", False):
        pointer = DATA_ROOT / "legacy_db_path.txt"
        if pointer.exists():
            try:
                legacy_path = pointer.read_text(encoding="utf-8").strip()
            except OSError:
                legacy_path = ""
    if legacy_path and migrate_legacy_database(legacy_path):
        os.environ.pop("CPP_ADVENTURE_LEGACY_DB", None)
        try:
            (DATA_ROOT / "legacy_db_path.txt").unlink(missing_ok=True)
        except OSError:
            pass
    # Versioned migrations (db_migrations.py): one transaction per step, verified backup of
    # an existing database before it is upgraded, backfills run exactly once.
    migrate_database(DB_PATH, context={"shop": SHOP, "task_chapter": TASK_CHAPTER}, backup_dir=DATA_ROOT / "backups")


def all_tasks():
    return [task for chapter in CURRICULUM for task in chapter["tasks"]]


TASK_XP = {task["id"]: int(task["xp"]) for chapter in CURRICULUM for task in chapter["tasks"]}
TASK_CHAPTER = {task["id"]: chapter["id"] for chapter in CURRICULUM for task in chapter["tasks"]}
LAB_XP = {lab["id"]: int(lab.get("xp", 0)) for lab in LABS}
MAX_IMPORTED_XP = 1_000_000
SAVE_FORMAT_VERSION = 2  # v2: adds ai_usage
SUPPORTED_SAVE_VERSIONS = (1, 2)


def clamp_int(value, low: int, high: int, default: int = 0) -> int:
    """Coerce untrusted numbers (e.g. from an imported save) into [low, high]."""
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        number = default
    return max(low, min(high, number))


def plugin_directories():
    bundled = ROOT / "plugins"
    user = DATA_ROOT / "plugins"
    try:
        if bundled.resolve() == user.resolve():
            user = DATA_ROOT / "user-plugins"
    except OSError:
        user = DATA_ROOT / "user-plugins"
    return [bundled, user]


def record_learning_event(profile_id, task_id, correct, error_kind="", hint_used=False):
    chapter = next((c for c in CURRICULUM if any(t["id"] == task_id for t in c["tasks"])), None)
    if not chapter:
        return
    with db() as con:
        if valid_profile(con, profile_id):
            con.execute("INSERT INTO learning_events(profile_id,task_id,chapter_id,correct,error_kind,hint_used) VALUES(?,?,?,?,?,?)", (profile_id, task_id, chapter["id"], int(bool(correct)), str(error_kind)[:40], int(bool(hint_used))))
            task = next((item for item in chapter["tasks"] if item["id"] == task_id), {})
            if task.get("kind") != "quiz":
                prior = con.execute("SELECT interval_days FROM review_schedule WHERE profile_id=? AND task_id=?", (profile_id, task_id)).fetchone()
                interval = min(30, max(3, int(prior[0]) * 2)) if correct and prior else 3 if correct else 1
                con.execute("INSERT INTO review_schedule(profile_id,task_id,due_at,interval_days) VALUES(?,?,datetime('now','+' || ? || ' days'),?) ON CONFLICT(profile_id,task_id) DO UPDATE SET due_at=datetime('now','+' || excluded.interval_days || ' days'),interval_days=excluded.interval_days", (profile_id, task_id, interval, interval))


def sync_achievements(con, profile_id):
    done = {row[0] for row in con.execute("SELECT task_id FROM completions WHERE profile_id=?", (profile_id,))}
    tasks = {task["id"]: task for task in all_tasks()}
    earned = set()
    if done: earned.add("first_steps")
    if len(done) >= 10: earned.add("cat_coder")
    if len(done) >= 25: earned.add("quest_hunter")
    if len(done) >= len(tasks): earned.add("legend")
    completed_chapters = [chapter for chapter in CURRICULUM if all(task["id"] in done for task in chapter["tasks"])]
    if completed_chapters: earned.add("chapter_clear")
    if len(completed_chapters) >= 3: earned.add("world_explorer")
    if sum(1 for task_id in done if tasks.get(task_id, {}).get("kind") == "fix") >= 5: earned.add("bug_squasher")
    if sum(1 for task_id in done if tasks.get(task_id, {}).get("kind") == "quiz") >= 5: earned.add("quiz_whiz")
    if sum(1 for task_id in done if tasks.get(task_id, {}).get("kind") == "code") >= 3: earned.add("code_runner")
    if any(task_id in done and task.get("kind") == "boss" for task_id, task in tasks.items()): earned.add("first_boss")
    if sum(1 for task_id in done if tasks.get(task_id, {}).get("kind") == "boss") >= 3: earned.add("boss_hunter")
    profile = valid_profile(con, profile_id)
    if profile and profile["streak"] >= 3: earned.add("streak_keeper")
    if con.execute("SELECT COUNT(*) FROM daily_quests WHERE profile_id=? AND completed=1", (profile_id,)).fetchone()[0] >= 5: earned.add("daily_star")
    projects = {row[0] for row in con.execute("SELECT project_id FROM project_submissions WHERE profile_id=? AND completed=1", (profile_id,))}
    if projects: earned.add("project_builder")
    if "algorithm_sort" in projects: earned.add("algorithmist")
    if con.execute("SELECT COUNT(*) FROM shop_items WHERE profile_id=?", (profile_id,)).fetchone()[0] >= 3: earned.add("shop_lover")
    if profile and profile["active_item"]: earned.add("stylish_cat")
    con.executemany("INSERT OR IGNORE INTO achievements(profile_id,id) VALUES(?,?)", [(profile_id, item) for item in earned])


def valid_profile(con, profile_id):
    if not isinstance(profile_id, str):
        return None
    return con.execute("SELECT * FROM profiles WHERE id=?", (profile_id,)).fetchone()


def companion_equipment_map(con, profile_id):
    return {row["slot"]: row["item_id"] for row in con.execute(
        "SELECT slot,item_id FROM companion_equipment WHERE profile_id=? ORDER BY slot", (profile_id,)
    )}


def companion_loadouts(con, profile_id):
    result = []
    for row in con.execute("SELECT loadout_id,name,equipment_json,created_at,updated_at FROM companion_loadouts WHERE profile_id=? ORDER BY updated_at DESC,created_at DESC", (profile_id,)):
        try:
            equipment = json.loads(row["equipment_json"])
        except (TypeError, ValueError):
            equipment = {}
        result.append({"loadout_id": row["loadout_id"], "name": row["name"], "equipment": equipment, "created_at": row["created_at"], "updated_at": row["updated_at"]})
    return result


def companion_payload(con, profile_id):
    profile = valid_profile(con, profile_id)
    if not profile:
        return None
    owned = [row[0] for row in con.execute("SELECT item_id FROM shop_items WHERE profile_id=? ORDER BY bought_at,item_id", (profile_id,))]
    return {
        "profile_id": profile_id,
        "active_item": profile["active_item"],
        "equipped_items": companion_equipment_map(con, profile_id),
        "owned_items": owned,
        "loadouts": companion_loadouts(con, profile_id),
    }


def equip_companion_item(con, profile_id, item_id, slot=None):
    if item_id:
        item = SHOP.get(item_id)
        if not item:
            return "item_not_found"
        if slot and slot != item["slot"]:
            return "slot_mismatch"
        if not con.execute("SELECT 1 FROM shop_items WHERE profile_id=? AND item_id=?", (profile_id, item_id)).fetchone():
            return "not_owned"
        con.execute("INSERT INTO companion_equipment(profile_id,slot,item_id) VALUES(?,?,?) ON CONFLICT(profile_id,slot) DO UPDATE SET item_id=excluded.item_id,equipped_at=CURRENT_TIMESTAMP", (profile_id, item["slot"], item_id))
        con.execute("UPDATE profiles SET active_item=? WHERE id=?", (item_id, profile_id))
        return None
    if slot:
        if slot not in {item["slot"] for item in SHOP.values()}:
            return "invalid_slot"
        con.execute("DELETE FROM companion_equipment WHERE profile_id=? AND slot=?", (profile_id, slot))
    else:
        con.execute("DELETE FROM companion_equipment WHERE profile_id=?", (profile_id,))
    current = con.execute("SELECT item_id FROM companion_equipment WHERE profile_id=? ORDER BY equipped_at DESC,rowid DESC LIMIT 1", (profile_id,)).fetchone()
    con.execute("UPDATE profiles SET active_item=? WHERE id=?", (current[0] if current else "", profile_id))
    return None


def base_level_xp(con, profile_id):
    """XP that counts toward the companion level: tasks, daily quests and workshop projects."""
    done = {row[0] for row in con.execute("SELECT task_id FROM completions WHERE profile_id=?", (profile_id,))}
    earned = sum(t["xp"] for t in all_tasks() if t["id"] in done)
    earned += con.execute("SELECT COALESCE(SUM(reward),0) FROM daily_quests WHERE profile_id=? AND completed=1", (profile_id,)).fetchone()[0]
    done_projects = {row[0] for row in con.execute("SELECT project_id FROM project_submissions WHERE profile_id=? AND awarded=1", (profile_id,))}
    return earned + sum(project["xp"] for project in PROJECTS if project["id"] in done_projects)


def admin_level_bonus(con, profile_id):
    row = con.execute("SELECT level_xp FROM admin_bonus WHERE profile_id=?", (profile_id,)).fetchone()
    return int(row[0]) if row else 0


def xp_for_level(level):
    """Total level XP needed to reach `level` (level n costs n*120)."""
    return 60 * level * (level - 1)


def admin_enabled_from_env(environ):
    """The XP/level test panel is opt-in: only CPP_ADVENTURE_ADMIN=1 enables it."""
    return str(environ.get("CPP_ADVENTURE_ADMIN", "")).strip() == "1"


ADMIN_ENABLED = admin_enabled_from_env(os.environ)
ADMIN_BADGES = ("first_steps","cat_coder","quest_hunter","legend","project_builder","first_boss","bug_squasher","quiz_whiz","code_runner","chapter_clear","world_explorer","boss_hunter","streak_keeper","daily_star","shop_lover","stylish_cat","algorithmist")


def _admin_int(value, low, high):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError("Geçerli bir sayı gir.")
    if number < low or number > high:
        raise ValueError(f"Değer {low} ile {high} arasında olmalı.")
    return number


def admin_action(con, profile_id, action, value=None):
    """Test-panel actions. Only the active local profile is changed."""
    if action == "add_xp":
        amount = _admin_int(value, -10_000_000, 10_000_000)
        con.execute("UPDATE profiles SET xp=MAX(0,xp+?) WHERE id=?", (amount, profile_id))
    elif action == "set_xp":
        con.execute("UPDATE profiles SET xp=? WHERE id=?", (_admin_int(value, 0, 10_000_000), profile_id))
    elif action == "set_level":
        level = _admin_int(value, 1, 60)
        bonus = xp_for_level(level) - base_level_xp(con, profile_id)
        con.execute("INSERT INTO admin_bonus(profile_id,level_xp) VALUES(?,?) ON CONFLICT(profile_id) DO UPDATE SET level_xp=excluded.level_xp", (profile_id, bonus))
    elif action == "set_streak":
        streak = _admin_int(value, 0, 3650)
        con.execute("UPDATE profiles SET streak=?,last_day=? WHERE id=?", (streak, time.strftime("%Y-%m-%d") if streak else "", profile_id))
    elif action == "grant_items":
        con.executemany("INSERT OR IGNORE INTO shop_items(profile_id,item_id) VALUES(?,?)", [(profile_id, item_id) for item_id in SHOP])
    elif action == "clear_items":
        con.execute("DELETE FROM companion_equipment WHERE profile_id=?", (profile_id,))
        con.execute("DELETE FROM companion_loadouts WHERE profile_id=?", (profile_id,))
        con.execute("DELETE FROM shop_items WHERE profile_id=?", (profile_id,))
        con.execute("UPDATE profiles SET active_item='' WHERE id=?", (profile_id,))
    elif action in ("complete_chapter", "complete_all"):
        if action == "complete_chapter":
            chapters = [CURRICULUM[_admin_int(value, 0, len(CURRICULUM) - 1)]]
        else:
            chapters = CURRICULUM
        con.executemany("INSERT OR IGNORE INTO completions(profile_id,task_id,xp) VALUES(?,?,?)", [(profile_id, task["id"], task["xp"]) for chapter in chapters for task in chapter["tasks"]])
    elif action == "grant_badges":
        con.executemany("INSERT OR IGNORE INTO achievements(profile_id,id) VALUES(?,?)", [(profile_id, badge) for badge in ADMIN_BADGES])
    elif action == "reset_progress":
        for table in ("completions", "quiz_results", "review_schedule", "daily_quests", "learning_events", "achievements", "admin_bonus", "project_submissions", "lab_awards"):
            con.execute(f"DELETE FROM {table} WHERE profile_id=?", (profile_id,))
        con.execute("UPDATE profiles SET xp=0,streak=0,last_day='' WHERE id=?", (profile_id,))
    else:
        raise ValueError("Bilinmeyen test paneli işlemi.")
    if action not in ("reset_progress", "grant_badges"):
        sync_achievements(con, profile_id)


def state(profile_id):
    with db() as con:
        row = valid_profile(con, profile_id)
        if not row:
            return {"error": "Profil seçilmedi veya artık bulunamıyor."}
        profile = dict(row)
        done = {row[0] for row in con.execute("SELECT task_id FROM completions WHERE profile_id=?", (profile_id,))}
        achievements = {row[0] for row in con.execute("SELECT id FROM achievements WHERE profile_id=?", (profile_id,))}
        profile["pin_protected"] = bool(profile.pop("pin_hash", ""))
    tasks = all_tasks()
    with db() as con:
        earned = max(0, base_level_xp(con, profile_id) + admin_level_bonus(con, profile_id))
    lvl = 1
    while earned >= lvl * 120:
        earned -= lvl * 120
        lvl += 1
    profile["level"] = lvl
    profile["level_xp"] = earned
    profile["next_level_xp"] = lvl * 120
    profile["completed"] = sorted(done)
    profile["achievements"] = sorted(achievements)
    with db() as con:
        profile["quiz_results"] = [dict(row) for row in con.execute("SELECT task_id,attempts,correct,last_answer,updated_at FROM quiz_results WHERE profile_id=?", (profile_id,))]
        profile["owned_items"] = [row[0] for row in con.execute("SELECT item_id FROM shop_items WHERE profile_id=?", (profile_id,))]
        profile["equipped_items"] = companion_equipment_map(con, profile_id)
        profile["companion_loadouts"] = companion_loadouts(con, profile_id)
        profile["ai_usage"] = [dict(row) for row in con.execute("SELECT provider,model,input_tokens,output_tokens,requests,estimated_usd,updated_at FROM ai_usage WHERE profile_id=? ORDER BY updated_at DESC", (profile_id,))]
        day = time.strftime("%Y-%m-%d")
        daily = con.execute("SELECT task_id,reward,completed FROM daily_quests WHERE profile_id=? AND day=?", (profile_id, day)).fetchone()
        if not daily:
            due_ids = [row[0] for row in con.execute("SELECT task_id FROM review_schedule WHERE profile_id=? AND due_at<=datetime('now') ORDER BY due_at LIMIT 20", (profile_id,))]
            task_by_id = {task["id"]: task for task in all_tasks()}
            candidates = [task_by_id[task_id] for task_id in due_ids if task_id in task_by_id]
            for idx, chapter in enumerate(CURRICULUM):
                if candidates: break
                if idx and CURRICULUM[idx-1]["tasks"][-1]["id"] not in done:
                    break
                nxt = next((t for t in chapter["tasks"] if t["id"] not in done), None)
                if nxt: candidates.append(nxt)
            if not candidates: candidates = all_tasks()
            seed = uuid.uuid5(uuid.NAMESPACE_URL, profile_id + day).int
            selected = candidates[seed % len(candidates)]
            con.execute("INSERT OR IGNORE INTO daily_quests(profile_id,day,task_id,reward) VALUES(?,?,?,15)", (profile_id, day, selected["id"]))
            daily = con.execute("SELECT task_id,reward,completed FROM daily_quests WHERE profile_id=? AND day=?", (profile_id, day)).fetchone()
        daily_task = next(t for t in all_tasks() if t["id"] == daily["task_id"])
        profile["daily_quest"] = {"task_id": daily_task["id"], "title": daily_task["title"], "prompt": daily_task["prompt"], "reward": daily["reward"], "completed": bool(daily["completed"])}
        profile["review_due"] = [dict(row) for row in con.execute("SELECT task_id,interval_days,due_at FROM review_schedule WHERE profile_id=? AND due_at<=datetime('now') ORDER BY due_at", (profile_id,))]
        task_to_chapter = {t["id"]: c["number"] for c in CURRICULUM for t in c["tasks"]}
        weak = []
        for row in profile["quiz_results"]:
            attempts = row["attempts"]
            if attempts >= 2 and row["correct"] < attempts:
                wrong_rate = (attempts-row["correct"])/attempts
                weak.append({"chapter": task_to_chapter[row["task_id"]], "wrong_rate": round(wrong_rate,2)})
        profile["weak_topics"] = weak
    profile["total_tasks"] = len(tasks)
    return {"profile": profile, "curriculum": CURRICULUM}



_ANSWER_TRANSLATION = str.maketrans({"ç": "c", "ş": "s", "ğ": "g", "ı": "i", "ö": "o", "ü": "u", "İ": "i", "Ç": "c", "Ş": "s", "Ğ": "g", "Ö": "o", "Ü": "u"})


def normalize_answer(value) -> str:
    """Forgiving quiz comparison: case, Turkish diacritics, spacing, `std::` and end punctuation."""
    text = str(value if value is not None else "").translate(_ANSWER_TRANSLATION).casefold().strip()
    text = re.sub(r"\s+", " ", text).rstrip(".!;")
    return text[5:] if text.startswith("std::") else text


def compile_and_run(source: str, input_text: str = ""):
    if not COMPILER:
        return {"ok": False, "phase": "compiler_missing", "compile_ok": False, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "elapsed_ms": 0, "error": "G++/Clang++ bulunamadı. MSYS2 UCRT64 G++ kurulumu gerekli."}
    if not isinstance(source, str) or not source.strip():
        return {"ok": False, "phase": "validate", "compile_ok": False, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "elapsed_ms": 0, "error": "Kod boş olamaz."}
    if len(source) > MAX_SOURCE:
        return {"ok": False, "phase": "validate", "compile_ok": False, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "elapsed_ms": 0, "error": "Kod 20.000 karakter sınırını aşıyor."}
    if not isinstance(input_text, str) or len(input_text) > 2000:
        return {"ok": False, "phase": "validate", "compile_ok": False, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "elapsed_ms": 0, "error": "Program girdisi metin olmalı ve 2.000 karakteri aşmamalı."}
    policy_error = source_policy_violation(source)
    if policy_error:
        return {"ok": False, "phase": "validate", "compile_ok": False, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "elapsed_ms": 0, "error": policy_error}
    started = time.perf_counter()
    try:
        with build_slot():
            build = _compile_source(source)
            if build["timed_out"]:
                return {"ok": False, "phase": "compile_timeout", "compile_ok": False, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "compile_ms": build["compile_ms"], "run_ms": None, "elapsed_ms": round((time.perf_counter() - started) * 1000), "error": "Derleme 15 saniyede tamamlanmadı; güvenli biçimde durduruldu."}
            compile_ms = build["compile_ms"]
            if not build["ok"]:
                compiler_output = build["output"][-6000:] or "Derleme başarısız."
                return {"ok": False, "phase": "compile", "compile_ok": False, "compile_output": compiler_output, "stdout": "", "output": "", "stderr": "", "exit_code": None, "compile_ms": compile_ms, "run_ms": None, "elapsed_ms": round((time.perf_counter() - started) * 1000), "error": compiler_output}
            warnings = build["output"][-6000:]
            run_started = time.perf_counter()
            run, timed_out, overflowed = run_limited([str(build["exe"])], input_text, 3)
    except SandboxBusy as exc:
        return {"ok": False, "phase": "busy", "compile_ok": False, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "elapsed_ms": round((time.perf_counter() - started) * 1000), "error": str(exc)}
    except OSError as exc:  # isolation could not be applied: the program was not run (fail closed)
        return {"ok": False, "phase": "sandbox_error", "compile_ok": True, "compile_output": "", "stdout": "", "output": "", "stderr": "", "exit_code": None, "elapsed_ms": round((time.perf_counter() - started) * 1000), "error": f"Güvenli çalıştırma ortamı hazırlanamadı; program çalıştırılmadı. / Не удалось подготовить безопасную среду. ({exc})"}
    run_ms = round((time.perf_counter() - run_started) * 1000)
    elapsed = round((time.perf_counter() - started) * 1000)
    common = {"compile_ok": True, "compile_output": warnings, "compile_ms": compile_ms, "run_ms": run_ms, "elapsed_ms": elapsed, "sandbox": run.isolation, "compile_cached": build["cached"]}
    if timed_out and not overflowed:
        return {"ok": False, "phase": "run_timeout", "stdout": "", "output": "", "stderr": "", "exit_code": None, **common, "error": "Program 3 saniyede tamamlanmadı; güvenli biçimde durduruldu."}
    if overflowed:
        return {"ok": False, "phase": "output_limit", "stdout": run.stdout[-6000:], "output": run.stdout[-6000:], "stderr": "", "exit_code": None, **common, "error": "Program çok fazla çıktı üretti (64 KB sınırı); güvenli biçimde durduruldu."}
    stdout = run.stdout[-6000:]
    stderr = run.stderr[-3000:]
    return {"ok": run.returncode == 0, "phase": "complete" if run.returncode == 0 else "runtime", "stdout": stdout, "output": stdout, "stderr": stderr, "exit_code": run.returncode, **common, "error": "" if run.returncode == 0 else f"Program {run.returncode} çıkış koduyla sonlandı."}


# Learner binaries are statically linked on Windows so they run inside the AppContainer,
# which cannot read the MinGW runtime DLLs next to the compiler.
COMPILE_FLAGS = ("-std=c++20", "-O0", "-Wall", "-Wextra", "-pipe")
LINK_FLAGS = ("-pipe",) + (("-static",) if os.name == "nt" else ())
COMPILE_CACHE_SIZE = 24
_COMPILE_CACHE: "OrderedDict[str, dict]" = OrderedDict()
_COMPILE_CACHE_LOCK = threading.Lock()
_COMPILE_KEY_LOCKS: dict = {}
_COMPILE_CACHE_DIR: list = []


def _compile_cache_dir() -> Path:
    if not _COMPILE_CACHE_DIR or not _COMPILE_CACHE_DIR[0].exists():
        folder = Path(tempfile.mkdtemp(prefix="cpp-adventure-build-"))
        atexit.register(shutil.rmtree, folder, True)
        _COMPILE_CACHE_DIR[:] = [folder]
    return _COMPILE_CACHE_DIR[0]


def _compile_source(source: str) -> dict:
    """Compile each distinct source once (several test inputs reuse the same binary).

    Returns {"ok", "exe", "output", "compile_ms", "timed_out", "cached"}. Timeouts are not cached.
    """
    key = hashlib.sha256("\0".join((COMPILER, *COMPILE_FLAGS, *LINK_FLAGS, source)).encode("utf-8")).hexdigest()
    with _COMPILE_CACHE_LOCK:
        key_lock = _COMPILE_KEY_LOCKS.setdefault(key, threading.Lock())
    with key_lock:
        with _COMPILE_CACHE_LOCK:
            hit = _COMPILE_CACHE.get(key)
            if hit and (hit["exe"] is None or hit["exe"].exists()):
                _COMPILE_CACHE.move_to_end(key)
                return {**hit, "compile_ms": 0, "cached": True}
        folder = _compile_cache_dir() / key[:32]
        folder.mkdir(exist_ok=True)
        src, asm, exe = folder / "main.cpp", folder / "main.s", folder / ("main.exe" if os.name == "nt" else "main")
        src.write_text(source, encoding="utf-8")
        compile_started = time.perf_counter()
        # Step 1: C++ -> assembly. Step 2 (assemble + link) only runs if the expanded assembly
        # contains no .incbin/.include, so inline asm cannot read files at build time.
        build = run_tool([COMPILER, *COMPILE_FLAGS, "-S", str(src), "-o", str(asm)], 15, str(folder))
        output = build.stderr or build.stdout
        if build.returncode == 0 and not build.timed_out:
            violation = assembly_policy_violation(asm.read_text(encoding="utf-8", errors="replace"))
            if violation:
                build.returncode, output = 1, violation
            else:
                link = run_tool([COMPILER, *LINK_FLAGS, str(asm), "-o", str(exe)], 15, str(folder))
                build.returncode, build.timed_out = link.returncode, link.timed_out
                output = output + (link.stderr or link.stdout)
        ok = build.returncode == 0 and not build.timed_out and exe.exists()
        entry = {"ok": ok, "exe": exe if ok else None, "output": output, "timed_out": build.timed_out,
                 "compile_ms": round((time.perf_counter() - compile_started) * 1000)}
        if not build.timed_out:
            with _COMPILE_CACHE_LOCK:
                _COMPILE_CACHE[key] = entry
                while len(_COMPILE_CACHE) > COMPILE_CACHE_SIZE:
                    old_key, _ = _COMPILE_CACHE.popitem(last=False)
                    _COMPILE_KEY_LOCKS.pop(old_key, None)
                    shutil.rmtree(_compile_cache_dir() / old_key[:32], ignore_errors=True)
        return {**entry, "cached": False}


def diagnose_locally(task, source, input_text="", language="tr"):
    if not source.strip():
        return {"kind": "empty", "message": "Kod alanı boş; önce kendi çözümünü yaz.", "message_ru": "Поле кода пустое — сначала напиши своё решение."}
    missing = [] if task.get("concept_rule") else [term for term in task.get("requires", []) if term.casefold() not in source.casefold()]
    if missing:
        return {"kind": "requirement", "missing": missing, "message": "Görevin istediği C++ öğeleri kodunda görünmüyor. Önce bu yapıları ekleyip yeniden çalıştır.", "message_ru": "В коде не найдены обязательные элементы задания. Добавь эти конструкции и запусти программу снова."}
    cases = task.get("tests") or [{"input": input_text, "expected": task.get("expected", "")}]
    for index, case in enumerate(cases, 1):
        result = compile_and_run(source, case.get("input", input_text))
        if not result.get("ok"):
            error = result.get("error") or result.get("stderr") or "Program başarısız çıktı koduyla kapandı."
            match = re.search(r"main\.cpp:(\d+):\d+: (?:fatal )?error: ([^\n]+)", error)
            return {"kind": "compile" if result.get("error") else "runtime", "test": index, "line": int(match.group(1)) if match else None, "detail": error[-2400:], "message": "Derleyici kodu bu satırda okuyamadı. Noktalı virgül, parantez ve değişken adlarını kontrol et." if result.get("error") else "Program derlendi, ancak çalışırken hata verdi. Değerlerin hangi durumda kullanıldığını kontrol et.", "message_ru": "Компилятор не смог прочитать код. Проверь точку с запятой, скобки и имена переменных." if result.get("error") else "Код скомпилировался, но завершился с ошибкой. Проверь, при каких условиях используются значения."}
        expected = normalize_output(case.get("expected", task.get("expected", "")))
        actual = normalize_output(result.get("output", ""))
        if actual != expected:
            return {"kind": "output", "test": index, "input": case.get("input", ""), "expected": expected, "actual": actual, "message": "Program çalışıyor; bu sınamada ürettiği değer beklenenden farklı. İşlem sırasını, koşul sınırını ve yazdırdığın değişkeni izle.", "message_ru": "Программа запускается, но результат этого теста отличается от ожидаемого. Проверь порядок операций, границы условия и выводимую переменную."}
    if task.get("concept_rule"):
        concept = check_cpp_concept(source, task["concept_rule"], language)
        if not concept["passed"]:
            other_language = "ru" if language == "tr" else "tr"
            other = check_cpp_concept(source, task["concept_rule"], other_language)
            return {"kind": "concept", "message": concept["message"], "message_ru": other["message"], "criteria": concept["label"]}
    return {"kind": "passed", "message": "Tüm mevcut örnek testler geçti. Göndermeden önce kod koşullarını ve sınır durumlarını da gözden geçir.", "message_ru": "Все текущие тесты пройдены. Перед отправкой проверь требования к коду и граничные случаи."}


def analyze_code_quality(source, language="tr"):
    if not isinstance(source, str) or len(source) > MAX_SOURCE:
        raise ValueError("Kod boş olmalı ve 20.000 karakteri aşmamalı." if language == "tr" else "Код должен содержать не более 20 000 символов.")
    lines = source.splitlines()
    meaningful = [line.strip() for line in lines if line.strip() and not line.strip().startswith("//")]
    issues = []
    def issue(code, severity, tr_text, ru_text=None):
        issues.append({"code": code, "severity": severity, "message": tr_text if language == "tr" else (ru_text or tr_text)})
    if not source.strip():
        issue("empty", "error", "Kod alanı boş; önce incelenecek C++ kodunu yaz.", "Поле кода пустое — сначала введи код C++ для анализа.")
    if "using namespace std;" in source:
        issue("namespace", "suggestion", "using namespace std yerine kullandığın adları std:: ile açıkça yaz; bu ad çakışmalarını azaltır.", "Вместо using namespace std явно указывай std:: — так меньше конфликтов имён.")
    if "std::endl" in source or "endl" in source:
        issue("flush", "suggestion", "Sadece yeni satır gerekiyorsa '\\n' kullan; std::endl ayrıca çıktıyı boşaltır.", "Если нужен только перевод строки, используй '\\n': std::endl дополнительно сбрасывает буфер.")
    long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 100]
    if long_lines:
        issue("long_line", "readability", ("100 karakterden uzun satırlar var: " + ", ".join(map(str, long_lines[:5])) + ". Satırları bölerek okunabilirliği artır.") if language == "tr" else ("Есть строки длиннее 100 символов: " + ", ".join(map(str, long_lines[:5])) + ". Разбей их для удобства чтения."))
    repeated = [line for line, count in __import__("collections").Counter(meaningful).items() if count > 1 and len(line) > 8 and line not in ("}", "};")]
    if repeated:
        issue("duplicate", "readability", "Aynı kod satırları tekrar ediyor. Tekrarlanan işi bir fonksiyona taşımayı düşün.", "Одинаковые строки повторяются. Подумай, можно ли вынести повтор в функцию.")
    if re.search(r"\b(?:foo|bar|temp\d*|data\d+)\b", source, re.IGNORECASE):
        issue("names", "readability", "foo, bar veya temp gibi geçici adları görevi anlatan adlarla değiştir.", "Замени foo, bar или temp на имена, которые объясняют назначение переменной.")
    numbers = [x for x in re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", source) if x not in ("0", "1", "2")]
    if numbers:
        issue("magic_number", "suggestion", "Kodda açıklamasız sayısal sabitler var. Anlamlı bir const isim kullanmayı değerlendir.", "В коде есть необъяснённые числовые константы. Подумай о понятной константе const.")
    branches = len(re.findall(r"\b(if|for|while|case|catch)\b|\?", source))
    function_count = len(re.findall(r"\b[A-Za-z_]\w*\s*\([^;{}]*\)\s*(?:const\s*)?\{", source))
    score = max(0, 100 - sum({"empty": 100, "namespace": 8, "flush": 3, "long_line": 8, "duplicate": 12, "names": 8, "magic_number": 5}[item["code"]] for item in issues))
    return {"score": score, "metrics": {"characters": len(source), "lines": len(lines), "nonempty_lines": len(meaningful), "functions": function_count, "branch_points": branches, "long_lines": len(long_lines), "duplicate_lines": len(repeated)}, "issues": issues, "basis": "static_heuristics"}


def public_interview_question(question, language):
    public={"id":question["id"],"kind":question["kind"],"topic":question["topic"],"prompt":question["prompt"][language]}
    if question["kind"]=="choice": public["options"]=question["options"][language]
    else: public["starter"]=question["starter"]
    return public


def _response_text(data):
    for item in data.get("output", []):
        if item.get("type") == "message":
            text = "".join(part.get("text", "") for part in item.get("content", []) if part.get("type") == "output_text")
            if text:
                return text
    return ""


def call_ai_provider(provider, prompt):
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            return {"error": "OPENAI_API_KEY ayarlı değil.", "unconfigured": True}
        payload = {"model": OPENAI_MODEL, "store": False, "instructions": "You are a patient C++ tutor. Reply in the requested language. Diagnose the learner's actual mistake, explain the cause, then give one progressive hint. Do not provide the complete solution unless the learner explicitly asks for detailed explanation.", "input": prompt, "max_output_tokens": 450}
        request = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.loads(response.read())
        usage = data.get("usage", {})
        return {"text": _response_text(data), "model": OPENAI_MODEL, "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}
    if provider == "groq":
        key = provider_key("groq")
        if not key:
            return {"error": "Groq API anahtarı ayarlı değil.", "unconfigured": True}
        for model in dict.fromkeys([GROQ_MODEL, GROQ_FALLBACK_MODEL]):
            payload = {"model": model, "temperature": 0.3, "max_completion_tokens": 900, "reasoning_effort": "low", "include_reasoning": False, "messages": [{"role": "system", "content": TUTOR_SYSTEM}, {"role": "user", "content": prompt}]}
            request = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = json.loads(response.read())
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    continue  # limits are per model, so the smaller model may still have quota
                raise
            usage = data.get("usage", {})
            text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            return {"text": text, "model": data.get("model", model), "input_tokens": usage.get("prompt_tokens", 0), "output_tokens": usage.get("completion_tokens", 0)}
        return {"error": "Groq ücretsiz kullanım sınırı doldu; biraz sonra tekrar dene. Bu sırada çevrimdışı ipucu gösteriliyor."}
    if provider == "claude":
        key = claude_api_key()
        if not key:
            return {"error": "Claude API anahtarı ayarlı değil.", "unconfigured": True}
        # Haiku 5.5 rejects non-default temperature/top_p/top_k (HTTP 400) and thinks by
        # default; a short hint needs no thinking, and "disabled" is allowed at low effort.
        payload = {"model": CLAUDE_MODEL, "max_tokens": 450, "thinking": {"type": "disabled"}, "output_config": {"effort": "low"}, "system": TUTOR_SYSTEM, "messages": [{"role": "user", "content": prompt}]}
        request = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(payload).encode(), headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read())
        usage = data.get("usage", {})
        if data.get("stop_reason") == "refusal":
            return {"error": "Claude bu isteği yanıtlamadı; çevrimdışı ipucu gösteriliyor.", "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}
        text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        if not text.strip():
            return {"error": "Claude boş yanıt döndürdü; çevrimdışı ipucu gösteriliyor.", "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}
        if data.get("stop_reason") == "max_tokens":
            text = text.rstrip() + " …"
        return {"text": text, "model": data.get("model", CLAUDE_MODEL), "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}
    if provider == "ollama":
        payload = {"model": OLLAMA_MODEL, "stream": False, "messages": [{"role": "system", "content": "You are a patient C++ tutor. Reply in the requested language. Explain the real error, then offer one progressive hint. Do not give the full solution unless asked."}, {"role": "user", "content": prompt}], "options": {"temperature": 0.25}}
        request = urllib.request.Request(OLLAMA_URL + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=50) as response:
            data = json.loads(response.read())
        message = data.get("message", {}).get("content", "")
        return {"text": message, "model": OLLAMA_MODEL, "input_tokens": data.get("prompt_eval_count", 0), "output_tokens": data.get("eval_count", 0)}
    return {"error": "AI sağlayıcısı kapalı."}


# ---------------------------------------------------------------- local API security

# 'unsafe-inline' scripts are still required by ~60 inline onclick handlers in the current
# frontend; everything else (remote scripts, frames, plugins, form posts, foreign
# connections) is blocked. Tighten script-src once the inline handlers are removed.
CONTENT_SECURITY_POLICY = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                           "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; "
                           "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
}
AUTH_ERROR = {"error": "Oturum geçersiz; uygulamayı yeniden başlat. / Сессия недействительна, перезапусти приложение.", "code": "auth_required"}
PIN_ERROR = {"error": "Bu profil kilitli; önce PIN ile aç. / Профиль заблокирован, сначала введи PIN.", "code": "pin_required", "pin_required": True}
# Endpoints that check the PIN themselves or never act on a profile's data.
PIN_EXEMPT_PATHS = {"/api/select", "/api/profiles", "/api/profile/update", "/api/profile/delete", "/api/import"}


class LaunchAuth:
    """Per-launch secret for the local API.

    Browser-origin checks stop web pages, not other programs on the PC: anything that can
    reach 127.0.0.1 could call /api/run. The window receives a one-time bootstrap code in its
    start URL; redeeming it sets an HttpOnly, SameSite=Strict cookie that every /api/* call
    must present. The token never appears in the page, so local processes cannot read it.
    """

    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self._codes: dict[str, float] = {}
        self._lock = threading.Lock()

    def new_bootstrap_code(self, ttl: float = 120.0) -> str:
        code = secrets.token_urlsafe(24)
        with self._lock:
            self._codes[code] = time.monotonic() + ttl
        return code

    def redeem(self, code: str) -> bool:
        with self._lock:
            expires = self._codes.pop(code, None) if isinstance(code, str) else None
        return expires is not None and expires >= time.monotonic()

    def cookie_matches(self, header: str | None, name: str) -> bool:
        if not header:
            return False
        jar = SimpleCookie()
        try:
            jar.load(header)
        except Exception:
            return False
        morsel = jar.get(name)
        return morsel is not None and hmac.compare_digest(morsel.value, self.token)


_UNLOCK_LOCK = threading.Lock()
UNLOCKED_PROFILES: set = set()


def valid_profile_name(name: str) -> bool:
    """Letters in any script, digits, spaces and common punctuation; no markup or control characters."""
    return not re.search(r"[\x00-\x1f\x7f<>`]", name)


def unlock_profile(profile_id: str) -> None:
    """Only the active profile stays unlocked; switching profiles locks the previous one."""
    with _UNLOCK_LOCK:
        UNLOCKED_PROFILES.clear()
        UNLOCKED_PROFILES.add(profile_id)


def lock_profile(profile_id: str) -> None:
    with _UNLOCK_LOCK:
        UNLOCKED_PROFILES.discard(profile_id)


def profile_requires_unlock(profile_id) -> bool:
    if not isinstance(profile_id, str) or not profile_id:
        return False
    with _UNLOCK_LOCK:
        if profile_id in UNLOCKED_PROFILES:
            return False
    with db() as con:
        row = con.execute("SELECT pin_hash FROM profiles WHERE id=?", (profile_id,)).fetchone()
    return bool(row and row["pin_hash"])


class Handler(SimpleHTTPRequestHandler):
    auth: "LaunchAuth | None" = None  # set on app servers (create_app_server); None for in-process test servers

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def log_message(self, fmt, *args):
        print("[C++ Adventure] " + fmt % args)

    def end_headers(self):
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        super().end_headers()

    @property
    def session_cookie_name(self) -> str:
        # Cookies ignore the port, so the name carries it: two app windows never clobber each other.
        return f"cppadv_session_{self.server.server_address[1]}"

    def _authorized(self, path: str) -> bool:
        if self.auth is None or not path.startswith("/api/"):
            return True
        return self.auth.cookie_matches(self.headers.get("Cookie"), self.session_cookie_name)

    def _start_session(self):
        code = parse_qs(urlparse(self.path).query).get("code", [""])[0]
        if self.auth is not None and not self.auth.redeem(code):
            body = "Bu oturum bağlantısı kullanıldı veya süresi doldu; uygulamayı yeniden başlat. / Ссылка сессии устарела, перезапусти приложение.".encode("utf-8")
            self.send_response(403)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(302)
        self.send_header("Location", "/")
        if self.auth is not None:
            self.send_header("Set-Cookie", f"{self.session_cookie_name}={self.auth.token}; HttpOnly; SameSite=Strict; Path=/")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self, max_bytes=30_000):
        """Read a JSON object body. Raises ValueError (-> 400) on anything else."""
        raw_size = (self.headers.get("Content-Length") or "0").strip()
        if not raw_size.isdigit():
            raise ValueError("Geçersiz istek uzunluğu. / Неверная длина запроса.")
        size = int(raw_size)
        if size > max_bytes:
            raise ValueError("İstek çok büyük.")
        body = json.loads(self.rfile.read(size) or b"{}")
        if not isinstance(body, dict):
            raise ValueError("İstek gövdesi bir JSON nesnesi olmalı. / Тело запроса должно быть JSON-объектом.")
        return body

    def _request_allowed(self, mutating=False):
        """Reject DNS-rebinding and cross-site requests to the local API."""
        host = (self.headers.get("Host") or "").strip()
        hostname = urlparse("//" + host).hostname if host else None
        if hostname not in ALLOWED_HOSTS:
            return False
        if self.headers.get("Sec-Fetch-Site", "").lower() == "cross-site":
            return False
        origin = self.headers.get("Origin")
        if origin:
            parsed = urlparse(origin)
            if parsed.hostname not in ALLOWED_HOSTS or parsed.netloc.lower() != host.lower():
                return False
        elif mutating and self.headers.get("Sec-Fetch-Site", "").lower() not in ("", "same-origin", "none"):
            return False
        if mutating and not (self.headers.get("Content-Type", "").lower().startswith("application/json")):
            return False
        return True

    def do_HEAD(self):
        if not self._request_allowed(False):
            return self.send_json({"error": "İstek reddedildi."}, 403)
        if not self._authorized(urlparse(self.path).path):
            return self.send_json(AUTH_ERROR, 401)
        return super().do_HEAD()

    def do_GET(self):
        """GET dispatcher with the same error policy as do_POST: always answer in JSON."""
        try:
            return self._route_get()
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_json({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return None  # client went away; nothing left to answer
        except Exception as exc:
            return self.send_json({"error": f"Yerel sunucu hatası: {exc}"}, 500)

    def _route_get(self):
        if not self._request_allowed(False):
            return self.send_json({"error": "İstek reddedildi."}, 403)
        path = urlparse(self.path).path
        if path == "/__session":
            return self._start_session()
        if not self._authorized(path):
            return self.send_json(AUTH_ERROR, 401)
        if path not in PIN_EXEMPT_PATHS and profile_requires_unlock(parse_qs(urlparse(self.path).query).get("profile_id", [""])[0]):
            return self.send_json(PIN_ERROR, 403)
        if path == "/api/meta":
            return self.send_json({"app_version": APP_VERSION, "database_ready": DB_PATH.exists(), "compiler_ready": bool(COMPILER), "admin": ADMIN_ENABLED})
        if path == "/api/health":
            compiler_version = ""
            if COMPILER:
                try: compiler_version = subprocess.run([COMPILER,"--version"],capture_output=True,text=True,timeout=3).stdout.splitlines()[0]
                except Exception: compiler_version = "G++/Clang++ detected"
            memory_gb = None
            try:
                class MEMORYSTATUSEX(__import__("ctypes").Structure):
                    _fields_=[("dwLength",__import__("ctypes").c_ulong),("dwMemoryLoad",__import__("ctypes").c_ulong),("ullTotalPhys",__import__("ctypes").c_ulonglong),("ullAvailPhys",__import__("ctypes").c_ulonglong),("ullTotalPageFile",__import__("ctypes").c_ulonglong),("ullAvailPageFile",__import__("ctypes").c_ulonglong),("ullTotalVirtual",__import__("ctypes").c_ulonglong),("ullAvailVirtual",__import__("ctypes").c_ulonglong),("ullAvailExtendedVirtual",__import__("ctypes").c_ulonglong)]
                status=MEMORYSTATUSEX();status.dwLength=__import__("ctypes").sizeof(status)
                if __import__("ctypes").windll.kernel32.GlobalMemoryStatusEx(__import__("ctypes").byref(status)): memory_gb=round(status.ullTotalPhys/1024**3,1)
            except Exception: pass
            return self.send_json({"python":platform.python_version(),"os":platform.platform(),"is_windows_11":platform.system()=="Windows" and int(platform.release())>=10,"cpu_threads":os.cpu_count(),"ram_gb":memory_gb,"compiler":COMPILER,"compiler_version":compiler_version,"sqlite":sqlite3.sqlite_version,"vscode":shutil.which("code"),"offline_assets":(ROOT/"web"/"vendor"/"vs"/"editor"/"editor.main.js").exists(),"sandbox":isolation_status()})
        if path == "/api/ai/status":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                profile = valid_profile(con, profile_id)
                if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                usage = [dict(row) for row in con.execute("SELECT provider,model,input_tokens,output_tokens,requests,estimated_usd FROM ai_usage WHERE profile_id=?", (profile_id,))]
                selected = profile["ai_provider"]
            ollama_models = []
            try:
                request = urllib.request.Request(OLLAMA_URL + "/api/tags", method="GET")
                with urllib.request.urlopen(request, timeout=1.5) as response:
                    ollama_models = [item.get("name", "") for item in json.loads(response.read()).get("models", [])]
            except Exception: pass
            return self.send_json({"provider": selected, "openai_configured": bool(os.environ.get("OPENAI_API_KEY", "").strip()), "openai_model": OPENAI_MODEL, "ollama_url": OLLAMA_URL, "ollama_models": ollama_models, "ollama_model": OLLAMA_MODEL, "claude_configured": bool(claude_api_key()), "claude_key_from_env": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()), "claude_key_hint": ("…" + claude_api_key()[-4:]) if claude_api_key() else "", "claude_model": CLAUDE_MODEL, "groq_configured": bool(provider_key("groq")), "groq_key_from_env": provider_key_from_env("groq"), "groq_key_hint": ("…" + provider_key("groq")[-4:]) if provider_key("groq") else "", "groq_model": GROQ_MODEL, "usage": usage})
        if path == "/api/shop":
            return self.send_json({"items": SHOP})
        if path == "/api/projects":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                if not valid_profile(con,profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                saves = {row["project_id"]: dict(row) for row in con.execute("SELECT project_id,code,score,completed,updated_at FROM project_submissions WHERE profile_id=?", (profile_id,))}
                workspaces = [dict(row) for row in con.execute("SELECT workspace_id,name,files_json,updated_at FROM project_workspaces WHERE profile_id=? ORDER BY updated_at DESC", (profile_id,))]
            for workspace in workspaces:
                workspace["files"] = json.loads(workspace.pop("files_json"))
            return self.send_json({"projects": PROJECTS, "saves": saves, "workspaces": workspaces, "cmake_available": bool(resolve_cmake()), "templates": [{"id": t["id"], "name": t["name"], "files": sorted(t["files"])} for t in WORKSPACE_TEMPLATES]})
        if path == "/api/career":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                profile = valid_profile(con,profile_id)
                if not profile: return self.send_json({"error":"Profil bulunamadı."},404)
                completed_tasks = con.execute("SELECT COUNT(*) FROM completions WHERE profile_id=?",(profile_id,)).fetchone()[0]
                rows = [dict(row) for row in con.execute("SELECT project_id,code,score,completed,awarded,updated_at FROM project_submissions WHERE profile_id=?",(profile_id,))]
                notes = {row["project_id"]:dict(row) for row in con.execute("SELECT project_id,description,technologies,updated_at FROM portfolio_notes WHERE profile_id=?",(profile_id,))}
                sessions = [dict(row) for row in con.execute("SELECT session_id,lang,score,completed,started_at,completed_at,questions_json,answers_json FROM interview_sessions WHERE profile_id=? ORDER BY started_at DESC LIMIT 20",(profile_id,))]
                language=profile["lang"]
            saved={row["project_id"]:row for row in rows}
            portfolio=[]
            for project in PROJECTS:
                row=saved.get(project["id"],{})
                note=notes.get(project["id"],{})
                if project["id"] not in saved: continue
                portfolio.append({"project_id":project["id"],"title":project["title"][language],"mission_description":project["description"][language],"description":note.get("description","") or project["description"][language],"technologies":note.get("technologies","C++, G++, C++20"),"score":row.get("score",0),"completed":bool(row.get("completed")),"code":row.get("code","")[:4000],"updated_at":row.get("updated_at",""),"awarded":bool(row.get("awarded"))})
            career=career_summary(completed_tasks,len(all_tasks()),portfolio,language,len(PROJECTS))
            interview_history=[]
            for session in sessions:
                questions=json.loads(session["questions_json"]); answers=json.loads(session["answers_json"])
                interview_history.append({"session_id":session["session_id"],"score":session["score"],"completed":bool(session["completed"]),"started_at":session["started_at"],"completed_at":session["completed_at"],"question_count":len(questions),"answered":len(answers),"topics":[next((q["topic"] for q in INTERVIEW_BANK if q["id"]==qid),"") for qid in questions]})
            attempted=[json.loads(row["answers_json"]) for row in sessions if row["completed"]]
            strengths={}; misses={}
            for answer_set in attempted:
                for item in answer_set:
                    bucket=strengths if item.get("correct") else misses
                    topic=item.get("topic","C++")
                    bucket[topic]=bucket.get(topic,0)+1
            return self.send_json({"career":career,"portfolio":portfolio,"interviews":interview_history,"strengths":sorted(strengths.items(),key=lambda item:-item[1]),"review_topics":sorted(misses.items(),key=lambda item:-item[1])})
        if path == "/api/interview":
            params=__import__("urllib.parse",fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id=params.get("profile_id",[""])[0]; session_id=params.get("session_id",[""])[0]
            with db() as con:
                if not valid_profile(con,profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                session=con.execute("SELECT *,MAX(0,CAST(900-(julianday('now')-julianday(started_at))*86400 AS INTEGER)) AS remaining_seconds FROM interview_sessions WHERE profile_id=? AND session_id=?",(profile_id,session_id)).fetchone()
            if not session: return self.send_json({"error":"Mülakat oturumu bulunamadı. / Сессия собеседования не найдена."},404)
            ids=json.loads(session["questions_json"]); answers=json.loads(session["answers_json"]); index=len(answers)
            q=next((item for item in INTERVIEW_BANK if item["id"]==ids[index]),None) if index<len(ids) and not session["completed"] else None
            if session["remaining_seconds"]<=0 and not session["completed"]:
                with db() as con: con.execute("UPDATE interview_sessions SET completed=1,completed_at=CURRENT_TIMESTAMP WHERE profile_id=? AND session_id=?",(profile_id,session_id))
                return self.send_json({"session_id":session_id,"index":index,"total":len(ids),"score":session["score"],"completed":True,"question":None,"remaining_seconds":0})
            return self.send_json({"session_id":session_id,"index":index,"total":len(ids),"score":session["score"],"completed":bool(session["completed"]),"question":public_interview_question(q,session["lang"]) if q else None,"remaining_seconds":session["remaining_seconds"]})
        if path == "/api/state":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            return self.send_json(state(params.get("profile_id", [""])[0]))
        if path == "/api/companion":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                payload = companion_payload(con, profile_id)
            if not payload: return self.send_json({"error": "Profil bulunamadı. / Профиль не найден."}, 404)
            return self.send_json(payload)
        if path == "/api/lesson-scenes":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            chapter_id, language = params.get("chapter", [""])[0], params.get("lang", ["tr"])[0]
            if not any(chapter["id"] == chapter_id for chapter in CURRICULUM): return self.send_json({"error": "Bölüm bulunamadı. / Глава не найдена."}, 404)
            return self.send_json({"scenes": lesson_scenes_for(chapter_id, language)})
        if path == "/api/labs":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                awards = {row[0]: row[1] for row in con.execute("SELECT lab_id,xp FROM lab_awards WHERE profile_id=?", (profile_id,))}
            return self.send_json({"labs": [{**lab, "earned_xp": awards.get(lab["id"], 0), "completed": lab["id"] in awards} for lab in LABS]})
        if path == "/api/devtools":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id, module = params.get("profile_id", [""])[0], params.get("module", ["git"])[0]
            if module not in {"git", "conflict", "cmake", "testing", "terminal"}: return self.send_json({"error": "Developer lab not found."}, 404)
            with db() as con:
                if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                row = con.execute("SELECT data FROM devtools_state WHERE profile_id=? AND module=?", (profile_id, module)).fetchone()
            data = json.loads(row[0]) if row else initial_devtool_state(module)
            if module == "cmake": data["cmake_available"] = bool(resolve_cmake())
            return self.send_json({"module": module, "state": data})
        if path == "/api/rpg":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                profile = valid_profile(con, profile_id)
                if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                bosses = [task["id"] for task in all_tasks() if task.get("kind") == "boss"]
                return self.send_json(guild_summary(con, profile_id, profile["lang"], bosses))
        if path == "/api/advanced/concurrency":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            lang = params.get("lang", ["tr"])[0]
            try:
                simulation = simulate_counter(int(params.get("workers", [2])[0]), int(params.get("increments", [3])[0]), params.get("mutex", ["0"])[0] == "1")
            except (TypeError, ValueError):
                return self.send_json({"error": "Geçersiz simülasyon ayarı." if lang == "tr" else "Некорректные параметры симуляции."}, 400)
            return self.send_json(simulation)
        if path == "/api/arena":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                profile = valid_profile(con, profile_id)
                if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                challenge = daily_challenge()
                current = con.execute("SELECT attempts,best_score,best_elapsed_ms,awarded_xp FROM arena_attempts WHERE profile_id=? AND day=? AND challenge_id=?", (profile_id,challenge["day"],challenge["id"])).fetchone()
                personal = con.execute("SELECT COALESCE(MAX(best_score),0) AS best_score,MIN(CASE WHEN best_score=100 AND best_elapsed_ms>0 THEN best_elapsed_ms END) AS best_elapsed_ms FROM arena_attempts WHERE profile_id=? AND challenge_id=?", (profile_id,challenge["id"])).fetchone()
            lang = profile["lang"]
            return self.send_json({"day": challenge["day"], "challenge_id": challenge["id"], "title": challenge["title"][lang], "description": challenge["description"][lang], "starter": challenge["starter"], "xp": challenge["xp"], "tests": len(challenge["tests"]), "attempts_today": current["attempts"] if current else 0, "today_best": current["best_score"] if current else 0, "personal_best": personal["best_score"], "personal_fastest_ms": personal["best_elapsed_ms"], "reward_claimed": bool(current and current["awarded_xp"])})
        if path == "/api/plugins":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                enabled = {row[0]: bool(row[1]) for row in con.execute("SELECT plugin_id,enabled FROM plugin_settings WHERE profile_id=?", (profile_id,))}
            directories = plugin_directories()
            plugins, errors = discover_plugins(directories)
            bundled_ids = {item["id"] for item in discover_plugins(directories[:1])[0]}
            return self.send_json({"plugins": [{**item, "source": "bundled" if item["id"] in bundled_ids else "local", "enabled": enabled.get(item["id"], False)} for item in plugins], "errors": errors, "permissions": ["lessons.read"], "user_directory": str(directories[1]), "policy": {"tr": "Eklentiler yalnızca doğrulanmış yerel ders JSON verisi yükler; kod çalıştırma ve sistem erişimi yoktur.", "ru": "Плагины загружают только проверенные локальные уроки JSON; выполнение кода и доступ к системе запрещены."}})
        if path == "/api/stats":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                profile = valid_profile(con, profile_id)
                if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                daily = [dict(row) for row in con.execute("SELECT day,SUM(seconds) AS seconds FROM study_sessions WHERE profile_id=? AND day>=date('now','-29 day') GROUP BY day ORDER BY day", (profile_id,))]
                errors = [dict(row) for row in con.execute("SELECT error_kind,COUNT(*) AS count FROM learning_events WHERE profile_id=? AND correct=0 AND error_kind!='' GROUP BY error_kind ORDER BY count DESC", (profile_id,))]
                topics = [dict(row) for row in con.execute("SELECT chapter_id,COUNT(*) AS attempts,SUM(correct) AS correct,SUM(CASE WHEN correct=0 THEN 1 ELSE 0 END) AS errors FROM learning_events WHERE profile_id=? GROUP BY chapter_id", (profile_id,))]
                completed = con.execute("SELECT COUNT(*) FROM completions WHERE profile_id=?", (profile_id,)).fetchone()[0]
                project_count = con.execute("SELECT COUNT(*) FROM project_submissions WHERE profile_id=? AND completed=1", (profile_id,)).fetchone()[0]
                badges = con.execute("SELECT COUNT(*) FROM achievements WHERE profile_id=?", (profile_id,)).fetchone()[0]
                xp = int(profile["xp"])
                streak = int(profile["streak"])
            by_chapter = {item["chapter_id"]: item for item in topics}
            topic_stats = []
            for chapter in CURRICULUM:
                item = by_chapter.get(chapter["id"], {})
                attempts, correct = int(item.get("attempts") or 0), int(item.get("correct") or 0)
                topic_stats.append({"chapter_id": chapter["id"], "title": chapter["title"], "attempts": attempts, "correct": correct, "errors": int(item.get("errors") or 0), "accuracy": round(correct / attempts, 3) if attempts else None})
            total_seconds = sum(int(day["seconds"] or 0) for day in daily)
            return self.send_json({"xp": xp, "streak": streak, "completed_tasks": completed, "total_tasks": len(all_tasks()), "projects": project_count, "achievements": badges, "study_seconds_30d": total_seconds, "study_days_30d": len(daily), "daily": daily, "topics": topic_stats, "errors": errors, "attempts": sum(x["attempts"] for x in topic_stats), "correct": sum(x["correct"] for x in topic_stats)})
        if path == "/api/journal":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            with db() as con:
                if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                profile = valid_profile(con, profile_id)
                language = profile["lang"]
                events = [dict(row) for row in con.execute("SELECT id,task_id,chapter_id,correct,error_kind,hint_used,created_at FROM learning_events WHERE profile_id=? ORDER BY id DESC LIMIT 100", (profile_id,))]
                aggregate = {row["chapter_id"]: dict(row) for row in con.execute("SELECT chapter_id,COUNT(*) AS attempts,SUM(correct) AS correct,SUM(CASE WHEN correct=0 THEN 1 ELSE 0 END) AS errors,MAX(created_at) AS last_seen FROM learning_events WHERE profile_id=? GROUP BY chapter_id", (profile_id,))}
                daily = [dict(row) for row in con.execute("SELECT date(created_at) AS day,COUNT(*) AS attempts,SUM(correct) AS correct FROM learning_events WHERE profile_id=? GROUP BY date(created_at) ORDER BY day DESC LIMIT 14", (profile_id,))]
                completed_ids = {row[0] for row in con.execute("SELECT task_id FROM completions WHERE profile_id=?", (profile_id,))}
                due_ids = [row["task_id"] for row in con.execute("SELECT task_id FROM review_schedule WHERE profile_id=? AND due_at<=datetime('now') ORDER BY due_at LIMIT 20", (profile_id,))]
            topic_rows = []
            for chapter in CURRICULUM:
                stats = aggregate.get(chapter["id"], {})
                attempts = int(stats.get("attempts") or 0)
                correct = int(stats.get("correct") or 0)
                task_count = sum(1 for task in chapter["tasks"] if task["id"] in completed_ids)
                topic_rows.append({"id": chapter["id"], "number": chapter["number"], "title": chapter["title"], "attempts": attempts, "correct": correct, "errors": int(stats.get("errors") or 0), "accuracy": round(correct / attempts, 3) if attempts else None, "completed": task_count, "total": len(chapter["tasks"]), "last_seen": stats.get("last_seen")})
            weak = sorted((topic for topic in topic_rows if topic["attempts"] >= 2 and topic["accuracy"] is not None and topic["accuracy"] < 0.75), key=lambda topic: (topic["accuracy"], -topic["attempts"]))
            suggestions = [{"kind": "review", "chapter_id": topic["id"], "title": topic["title"], "reason": "low_accuracy", "accuracy": topic["accuracy"]} for topic in weak[:3]]
            if not suggestions:
                next_topic = next((topic for topic in topic_rows if topic["completed"] < topic["total"]), None)
                if next_topic:
                    suggestions.append({"kind": "continue", "chapter_id": next_topic["id"], "title": next_topic["title"], "reason": "next_step", "accuracy": next_topic["accuracy"]})
            task_map = {task["id"]: task for task in all_tasks()}
            review_queue = [{"task_id": task_id, "chapter_id": next(c["id"] for c in CURRICULUM if any(t["id"] == task_id for t in c["tasks"])), "title": task_map[task_id]["title"], "kind": task_map[task_id]["kind"]} for task_id in due_ids if task_id in task_map]
            insights = learning_insights(topic_rows, events, review_queue, language)
            return self.send_json({"topics": topic_rows, "weak_topics": weak, "suggestions": suggestions, "recent": events, "daily": daily, "review_queue": review_queue, **insights, "attempts": sum(topic["attempts"] for topic in topic_rows), "correct": sum(topic["correct"] for topic in topic_rows), "completed": len(completed_ids), "total_tasks": len(all_tasks())})
        if path == "/api/profiles":
            with db() as con:
                users = [dict(row) for row in con.execute("SELECT id,name,avatar,lang,xp,created_at,pin_hash!='' AS has_pin FROM profiles ORDER BY created_at")]
            return self.send_json({"profiles": users})
        if path == "/api/leaderboard":
            with db() as con:
                rows = [dict(row) for row in con.execute("SELECT id,name,avatar,xp FROM profiles ORDER BY xp DESC,name COLLATE NOCASE LIMIT 50")]
            return self.send_json({"leaderboard": rows})
        if path == "/api/export":
            params = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(urlparse(self.path).query)
            profile_id = params.get("profile_id", [""])[0]
            return self.send_json(self.export_profile(profile_id))
        return super().do_GET()

    def export_profile(self, profile_id):
        with db() as con:
            row = valid_profile(con, profile_id)
            if not row: raise ValueError("Profil bulunamadı.")
            profile = dict(row)
            profile.pop("pin_hash", None)
            profile["pin_protected"] = bool(row["pin_hash"])
            profile["completed"] = [dict(r) for r in con.execute("SELECT task_id,xp,completed_at FROM completions WHERE profile_id=?", (profile_id,))]
            profile["achievements"] = [dict(r) for r in con.execute("SELECT id,unlocked_at FROM achievements WHERE profile_id=?", (profile_id,))]
            profile["quiz_results"] = [dict(r) for r in con.execute("SELECT task_id,attempts,correct,last_answer,updated_at FROM quiz_results WHERE profile_id=?", (profile_id,))]
            profile["reviews"] = [dict(r) for r in con.execute("SELECT task_id,due_at,interval_days FROM review_schedule WHERE profile_id=?", (profile_id,))]
            profile["daily_quests"] = [dict(r) for r in con.execute("SELECT day,task_id,reward,completed FROM daily_quests WHERE profile_id=? ORDER BY day", (profile_id,))]
            profile["shop_items"] = [dict(r) for r in con.execute("SELECT item_id,bought_at FROM shop_items WHERE profile_id=?", (profile_id,))]
            profile["equipped_items"] = companion_equipment_map(con, profile_id)
            profile["companion_loadouts"] = companion_loadouts(con, profile_id)
            profile["project_submissions"] = [dict(r) for r in con.execute("SELECT project_id,code,score,completed,awarded,updated_at FROM project_submissions WHERE profile_id=?", (profile_id,))]
            profile["project_workspaces"] = [dict(r) for r in con.execute("SELECT workspace_id,name,files_json,updated_at FROM project_workspaces WHERE profile_id=?", (profile_id,))]
            profile["interview_sessions"] = [dict(r) for r in con.execute("SELECT session_id,lang,questions_json,answers_json,score,completed,started_at,completed_at FROM interview_sessions WHERE profile_id=?", (profile_id,))]
            profile["portfolio_notes"] = [dict(r) for r in con.execute("SELECT project_id,description,technologies,updated_at FROM portfolio_notes WHERE profile_id=?", (profile_id,))]
            profile["learning_events"] = [dict(r) for r in con.execute("SELECT task_id,correct,error_kind,hint_used,created_at FROM learning_events WHERE profile_id=? ORDER BY id DESC LIMIT 5000", (profile_id,))]
            profile["lab_awards"] = [dict(r) for r in con.execute("SELECT lab_id,xp,created_at FROM lab_awards WHERE profile_id=?", (profile_id,))]
            profile["devtools_state"] = [dict(r) for r in con.execute("SELECT module,data,updated_at FROM devtools_state WHERE profile_id=?", (profile_id,))]
            profile["study_sessions"] = [dict(r) for r in con.execute("SELECT session_id,day,seconds,updated_at FROM study_sessions WHERE profile_id=? ORDER BY day DESC", (profile_id,))]
            profile["arena_attempts"] = [dict(r) for r in con.execute("SELECT day,challenge_id,attempts,best_score,best_elapsed_ms,awarded_xp,updated_at FROM arena_attempts WHERE profile_id=? ORDER BY day DESC", (profile_id,))]
            profile["plugin_settings"] = [dict(r) for r in con.execute("SELECT plugin_id,version,enabled,updated_at FROM plugin_settings WHERE profile_id=?", (profile_id,))]
            profile["ai_usage"] = [dict(r) for r in con.execute("SELECT provider,model,input_tokens,output_tokens,requests,estimated_usd,updated_at FROM ai_usage WHERE profile_id=?", (profile_id,))]
        # Save format v2 adds ai_usage. admin_bonus (test-panel level XP) is deliberately not exported.
        return {"format": "cpp-adventure-save", "version": SAVE_FORMAT_VERSION, "profile": profile}

    def verify_profile_pin(self, profile, pin):
        stored = profile["pin_hash"]
        if not stored: return True
        try:
            salt, digest = stored.split(":", 1)
            return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", str(pin).encode(), bytes.fromhex(salt), 150_000).hex(), digest)
        except Exception: return False

    def do_POST(self):
        if not self._request_allowed(True):
            return self.send_json({"error": "İstek reddedildi."}, 403)
        path = urlparse(self.path).path
        if not self._authorized(path):
            return self.send_json(AUTH_ERROR, 401)
        try:
            body = self.read_json(POST_BODY_LIMITS.get(path, 30_000))
            if path not in PIN_EXEMPT_PATHS and profile_requires_unlock(body.get("profile_id")):
                return self.send_json(PIN_ERROR, 403)
            if path == "/api/arena/submit":
                profile_id = body.get("profile_id", "")
                challenge = daily_challenge()
                if body.get("challenge_id") != challenge["id"]:
                    return self.send_json({"error": "Günlük görev değişmiş; Arena'yı yenile."}, 409)
                source = body.get("code", "")
                if not isinstance(source, str) or not source.strip(): return self.send_json({"error": "Önce C++ çözümünü yaz."}, 400)
                started = time.monotonic()
                cases = []
                for index, case in enumerate(challenge["tests"], 1):
                    run = compile_and_run(source, case["input"])
                    passed = bool(run.get("ok")) and normalize_output(run.get("stdout", run.get("output", ""))) == normalize_output(case["expected"])
                    cases.append({"name": f"Test {index}", "passed": passed, "phase": run.get("phase"), "error": run.get("error", "")[:300]})
                    if not run.get("compile_ok"):
                        cases.extend({"name": f"Test {later}", "passed": False, "phase": "compile", "error": ""} for later in range(index + 1, len(challenge["tests"]) + 1))
                        break
                compile_elapsed = max(1, int((time.monotonic() - started) * 1000))
                try: elapsed = max(1, min(3_600_000, int(body.get("solve_ms", compile_elapsed))))
                except (TypeError, ValueError): elapsed = compile_elapsed
                passed = sum(item["passed"] for item in cases)
                total = len(challenge["tests"])
                score = round(passed * 100 / total)
                with db(immediate=True) as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    old = con.execute("SELECT attempts,best_score,best_elapsed_ms,awarded_xp FROM arena_attempts WHERE profile_id=? AND day=? AND challenge_id=?", (profile_id,challenge["day"],challenge["id"])).fetchone()
                    award = challenge["xp"] if score == 100 and not (old and old["awarded_xp"]) else 0
                    old_score = old["best_score"] if old else 0
                    old_ms = old["best_elapsed_ms"] if old else 0
                    best_score = max(old_score, score)
                    best_ms = elapsed if not old_ms or score > old_score else min(old_ms, elapsed) if score == old_score else old_ms
                    con.execute("INSERT INTO arena_attempts(profile_id,day,challenge_id,attempts,best_score,best_elapsed_ms,awarded_xp) VALUES(?,?,?,?,?,?,?) ON CONFLICT(profile_id,day,challenge_id) DO UPDATE SET attempts=excluded.attempts,best_score=excluded.best_score,best_elapsed_ms=excluded.best_elapsed_ms,awarded_xp=excluded.awarded_xp,updated_at=CURRENT_TIMESTAMP", (profile_id,challenge["day"],challenge["id"],(old["attempts"] if old else 0)+1,best_score,best_ms,(old["awarded_xp"] if old else 0)+award))
                    if award: con.execute("UPDATE profiles SET xp=xp+? WHERE id=?", (award, profile_id))
                    personal = con.execute("SELECT MAX(best_score),MIN(CASE WHEN best_score=100 AND best_elapsed_ms>0 THEN best_elapsed_ms END) FROM arena_attempts WHERE profile_id=? AND challenge_id=?", (profile_id,challenge["id"])).fetchone()
                return self.send_json({"score": score, "passed": passed, "total": total, "cases": cases, "elapsed_ms": elapsed, "compile_elapsed_ms": compile_elapsed, "awarded_xp": award, "best_score": best_score, "personal_best": personal[0] or 0, "personal_fastest_ms": personal[1]})
            if path == "/api/plugins/install":
                profile_id = body.get("profile_id", "")
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "profile_not_found"}, 404)
                directories = plugin_directories()
                if len(directories) < 2: return self.send_json({"error": "plugin_directory_unavailable"}, 500)
                plugin, result = install_plugin(body.get("manifest"), directories[0], directories[1])
                if not plugin:
                    return self.send_json({"error": result or "plugin_write_failed"}, 400 if result not in ("version_not_newer", "bundled_plugin_reserved") else 409)
                return self.send_json({"ok": True, "result": result, "plugin": plugin}, 201 if result == "installed" else 200)
            if path == "/api/plugins/remove":
                profile_id, plugin_id = body.get("profile_id", ""), body.get("plugin_id", "")
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "profile_not_found"}, 404)
                directories = plugin_directories()
                if len(directories) < 2: return self.send_json({"error": "plugin_directory_unavailable"}, 500)
                error = remove_plugin(str(plugin_id), directories[0], directories[1])
                if error: return self.send_json({"error": error}, 404 if error == "plugin_not_found" else 400)
                with db() as con:
                    con.execute("DELETE FROM plugin_settings WHERE plugin_id=?", (plugin_id,))
                return self.send_json({"ok": True, "plugin_id": plugin_id})
            if path == "/api/plugins/toggle":
                profile_id, plugin_id = body.get("profile_id", ""), str(body.get("plugin_id", ""))
                enabled = body.get("enabled")
                if not isinstance(enabled, bool): return self.send_json({"error": "Eklenti durumu geçersiz."}, 400)
                plugins, _ = discover_plugins(plugin_directories())
                plugin = next((item for item in plugins if item["id"] == plugin_id), None)
                if not plugin: return self.send_json({"error": "Eklenti bulunamadı veya manifest güvenli değil."}, 404)
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    con.execute("INSERT INTO plugin_settings(profile_id,plugin_id,version,enabled) VALUES(?,?,?,?) ON CONFLICT(profile_id,plugin_id) DO UPDATE SET version=excluded.version,enabled=excluded.enabled,updated_at=CURRENT_TIMESTAMP", (profile_id,plugin_id,plugin["version"],int(enabled)))
                return self.send_json({"ok": True, "plugin_id": plugin_id, "enabled": enabled})
            if path == "/api/compiler/assembly":
                profile_id = body.get("profile_id", "")
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                result = assembly_outputs(body.get("code", ""), COMPILER, MAX_SOURCE)
                return self.send_json(result, 200 if result.get("ok") else 400)
            if path == "/api/profiles":
                name = str(body.get("name", "")).strip()[:24]
                avatar = str(body.get("avatar", "🐱"))
                if avatar not in PROFILE_AVATARS: avatar = "🐱"
                pin = str(body.get("pin", ""))
                lang = body.get("lang") if body.get("lang") in ("tr", "ru") else "tr"
                if not name or len(name) < 2: return self.send_json({"error": "Имя должно содержать не менее 2 символов." if lang == "ru" else "İsim en az 2 karakter olmalı."}, 400)
                if not valid_profile_name(name): return self.send_json({"error": "Имя содержит недопустимые символы." if lang == "ru" else "İsim izin verilmeyen karakterler içeriyor."}, 400)
                if pin and not re.fullmatch(r"\d{4,8}", pin): return self.send_json({"error": "PIN должен содержать 4–8 цифр." if lang == "ru" else "PIN 4-8 rakam olmalı."}, 400)
                profile_id = str(uuid.uuid4())
                pin_hash = ""
                if pin:
                    salt = secrets.token_bytes(16)
                    pin_hash = salt.hex() + ":" + hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 150_000).hex()
                with db() as con:
                    con.execute("INSERT INTO profiles(id,name,avatar,pin_hash,lang) VALUES(?,?,?,?,?)", (profile_id, name, avatar, pin_hash, lang))
                return self.send_json({"ok": True, "profile_id": profile_id})
            if path == "/api/profile/update":
                profile_id = body.get("profile_id")
                name = str(body.get("name", "")).strip()[:24]
                avatar = body.get("avatar")
                pin = str(body.get("pin", ""))
                with db() as con:
                    current = valid_profile(con, profile_id)
                    if not current: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    if not self.verify_profile_pin(current, body.get("current_pin", "")): return self.send_json({"error": "Mevcut PIN hatalı. / Текущий PIN неверен.", "pin_required": True}, 403)
                    if name and len(name) < 2: return self.send_json({"error": "İsim en az 2 karakter olmalı. / Имя должно содержать не менее 2 символов."}, 400)
                    if name and not valid_profile_name(name): return self.send_json({"error": "İsim izin verilmeyen karakterler içeriyor. / Имя содержит недопустимые символы."}, 400)
                    # Validate everything before the first write: an early return inside
                    # `with db()` commits, so a late 400 would persist earlier changes.
                    if pin not in ("", "REMOVE") and not re.fullmatch(r"\d{4,8}", pin):
                        return self.send_json({"error": "PIN 4-8 rakam olmalı. / PIN должен содержать 4–8 цифр."}, 400)
                    if name:
                        con.execute("UPDATE profiles SET name=? WHERE id=?", (name, profile_id))
                    if avatar in PROFILE_AVATARS:
                        con.execute("UPDATE profiles SET avatar=? WHERE id=?", (avatar, profile_id))
                    if pin == "":
                        pass
                    elif pin == "REMOVE":
                        con.execute("UPDATE profiles SET pin_hash='' WHERE id=?", (profile_id,))
                    elif re.fullmatch(r"\d{4,8}", pin):
                        salt = secrets.token_bytes(16)
                        ph = salt.hex() + ":" + hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 150_000).hex()
                        con.execute("UPDATE profiles SET pin_hash=? WHERE id=?", (ph, profile_id))
                    else:
                        return self.send_json({"error": "PIN 4-8 rakam olmalı."}, 400)
                return self.send_json({"ok": True})
            if path == "/api/profile/delete":
                profile_id, pin = body.get("profile_id"), body.get("pin", "")
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile or not self.verify_profile_pin(profile, pin): return self.send_json({"error": "Profil veya PIN hatalı."}, 403)
                    con.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
                    lock_profile(profile_id)
                return self.send_json({"ok": True})
            if path == "/api/select":
                with db() as con: profile = valid_profile(con, body.get("profile_id"))
                if not profile or not self.verify_profile_pin(profile, body.get("pin", "")):
                    return self.send_json({"error": "Profil veya PIN hatalı."}, 403)
                unlock_profile(profile["id"])
                return self.send_json({"ok": True, "profile_id": profile["id"]})
            if path == "/api/import":
                profile_id = body.get("profile_id")
                data = body.get("save", {})
                if not isinstance(data, dict) or not isinstance(data.get("profile", {}), dict):
                    return self.send_json({"error": "Yedek dosyası biçimi desteklenmiyor."}, 400)
                if data.get("format") != "cpp-adventure-save" or data.get("version") not in SUPPORTED_SAVE_VERSIONS:
                    return self.send_json({"error": "Yedek dosyası biçimi desteklenmiyor."}, 400)
                allowed = {t["id"] for t in all_tasks()}
                saved = data.get("profile", {})
                done = saved.get("completed", [])
                badges = saved.get("achievements", [])
                quiz_results = saved.get("quiz_results", [])
                reviews = saved.get("reviews", [])
                daily_quests = saved.get("daily_quests", [])
                shop_items = saved.get("shop_items", [])
                equipped_items = saved.get("equipped_items")
                saved_loadouts = saved.get("companion_loadouts", [])
                project_submissions = saved.get("project_submissions", [])
                project_workspaces = saved.get("project_workspaces", [])
                interview_sessions = saved.get("interview_sessions", [])
                portfolio_notes = saved.get("portfolio_notes", [])
                learning_events = saved.get("learning_events", [])
                lab_awards = saved.get("lab_awards", [])
                devtools_state = saved.get("devtools_state", [])
                study_sessions = saved.get("study_sessions", [])
                arena_attempts = saved.get("arena_attempts", [])
                plugin_settings = saved.get("plugin_settings", [])
                ai_usage_rows = saved.get("ai_usage", []) if isinstance(saved.get("ai_usage", []), list) else []  # v2+; absent in v1 saves
                if len(done) > len(allowed) or any(item.get("task_id") not in allowed for item in done):
                    return self.send_json({"error": "Yedekte geçersiz görev kaydı var."}, 400)
                with db() as con:
                    target = valid_profile(con, profile_id)
                    if not target: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    # Import replaces the whole profile, so a PIN-protected profile must be unlocked.
                    if not self.verify_profile_pin(target, body.get("pin", "")):
                        return self.send_json({"error": "PIN hatalı. / Неверный PIN.", "pin_required": True}, 403)
                    last_day = str(saved.get("last_day", ""))
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", last_day): last_day = ""
                    con.execute("UPDATE profiles SET xp=?,lang=?,streak=?,last_day=?,ai_provider=? WHERE id=?", (clamp_int(saved.get("xp"), 0, MAX_IMPORTED_XP), saved.get("lang") if saved.get("lang") in ("tr","ru") else "tr", clamp_int(saved.get("streak"), 0, 3650), last_day, saved.get("ai_provider") if saved.get("ai_provider") in ("offline","ollama","openai","claude","groq","off") else "offline", profile_id))
                    con.execute("DELETE FROM completions WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM achievements WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM quiz_results WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM review_schedule WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM daily_quests WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM shop_items WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM companion_equipment WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM companion_loadouts WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM project_submissions WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM project_workspaces WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM interview_sessions WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM portfolio_notes WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM learning_events WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM lab_awards WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM devtools_state WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM study_sessions WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM arena_attempts WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM plugin_settings WHERE profile_id=?", (profile_id,))
                    con.execute("DELETE FROM ai_usage WHERE profile_id=?", (profile_id,))
                    con.executemany("INSERT OR REPLACE INTO ai_usage(profile_id,provider,model,input_tokens,output_tokens,requests,estimated_usd,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                                    [(profile_id, row["provider"], str(row.get("model", ""))[:80], clamp_int(row.get("input_tokens"), 0, 10**10), clamp_int(row.get("output_tokens"), 0, 10**10),
                                      clamp_int(row.get("requests"), 0, 10**7), max(0.0, min(10_000.0, float(row.get("estimated_usd") or 0) if isinstance(row.get("estimated_usd"), (int, float)) else 0.0)), str(row.get("updated_at", "restored"))[:40])
                                     for row in ai_usage_rows[:200] if isinstance(row, dict) and row.get("provider") in ("openai", "ollama", "claude", "groq")])
                    con.executemany("INSERT INTO completions(profile_id,task_id,xp,completed_at) VALUES(?,?,?,?)", [(profile_id, x["task_id"], clamp_int(x.get("xp"), 0, TASK_XP[x["task_id"]]), str(x.get("completed_at","restored"))[:40]) for x in done])
                    valid_badges = {"first_steps","cat_coder","quest_hunter","legend","project_builder","first_boss","bug_squasher","quiz_whiz","code_runner","chapter_clear","world_explorer","boss_hunter","streak_keeper","daily_star","shop_lover","stylish_cat","algorithmist", *(quest["id"] for quest in SECRET_QUESTS)}
                    con.executemany("INSERT INTO achievements(profile_id,id) VALUES(?,?)", [(profile_id, x["id"]) for x in badges if x.get("id") in valid_badges])
                    con.executemany("INSERT INTO quiz_results(profile_id,task_id,attempts,correct,last_answer,updated_at) VALUES(?,?,?,?,?,?)", [(profile_id, x["task_id"], int(x.get("attempts",0)), int(x.get("correct",0)), str(x.get("last_answer",""))[:200], str(x.get("updated_at","restored"))) for x in quiz_results if x.get("task_id") in allowed and next((t for t in all_tasks() if t["id"]==x.get("task_id")),{}).get("kind")=="quiz"])
                    con.executemany("INSERT INTO review_schedule(profile_id,task_id,due_at,interval_days) VALUES(?,?,?,?)", [(profile_id, x["task_id"], str(x.get("due_at","2099-01-01 00:00:00")), int(x.get("interval_days",1))) for x in reviews if x.get("task_id") in allowed])
                    con.executemany("INSERT INTO daily_quests(profile_id,day,task_id,reward,completed) VALUES(?,?,?,?,?)", [(profile_id, str(x["day"])[:10], x["task_id"], clamp_int(x.get("reward"), 0, 50, 15), int(bool(x.get("completed")))) for x in daily_quests if isinstance(x, dict) and x.get("task_id") in allowed and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(x.get("day", "")))])
                    con.executemany("INSERT INTO shop_items(profile_id,item_id,bought_at) VALUES(?,?,?)", [(profile_id, x["item_id"], str(x.get("bought_at","restored"))) for x in shop_items if x.get("item_id") in SHOP])
                    active_item = saved.get("active_item", "")
                    if active_item and active_item not in {x.get("item_id") for x in shop_items}:
                        active_item = ""
                    con.execute("UPDATE profiles SET active_item=? WHERE id=?", (active_item,profile_id))
                    owned_item_ids = {x.get("item_id") for x in shop_items if isinstance(x, dict)}
                    if isinstance(equipped_items, dict):
                        equipment_to_restore = equipped_items.items()
                    elif isinstance(equipped_items, list):
                        equipment_to_restore = ((x.get("slot"), x.get("item_id")) for x in equipped_items if isinstance(x, dict))
                    else:
                        legacy_item = saved.get("active_item", "")
                        legacy_slot = SHOP.get(legacy_item, {}).get("slot")
                        equipment_to_restore = [(legacy_slot, legacy_item)] if legacy_slot else []
                    restored_equipment = {}
                    valid_slots = {item["slot"] for item in SHOP.values()}
                    for slot, item_id in equipment_to_restore:
                        item = SHOP.get(item_id)
                        if slot in valid_slots and item and item["slot"] == slot and item_id in owned_item_ids:
                            restored_equipment[slot] = item_id
                    for slot, item_id in restored_equipment.items():
                        con.execute("INSERT INTO companion_equipment(profile_id,slot,item_id) VALUES(?,?,?)", (profile_id, slot, item_id))
                    if restored_equipment:
                        con.execute("UPDATE profiles SET active_item=? WHERE id=?", (next(reversed(list(restored_equipment.values()))), profile_id))
                    for loadout in saved_loadouts[:20] if isinstance(saved_loadouts, list) else []:
                        if not isinstance(loadout, dict): continue
                        loadout_id = str(loadout.get("loadout_id", ""))
                        name = str(loadout.get("name", "")).strip()[:32]
                        raw_equipment = loadout.get("equipment", {})
                        if not re.fullmatch(r"[0-9a-fA-F-]{16,64}", loadout_id) or not name or not isinstance(raw_equipment, dict): continue
                        clean_equipment = {slot: item_id for slot, item_id in raw_equipment.items() if slot in valid_slots and SHOP.get(item_id, {}).get("slot") == slot and item_id in owned_item_ids}
                        con.execute("INSERT INTO companion_loadouts(profile_id,loadout_id,name,equipment_json,created_at,updated_at) VALUES(?,?,?,?,?,?)", (profile_id, loadout_id, name, json.dumps(clean_equipment, ensure_ascii=False), str(loadout.get("created_at", "restored"))[:40], str(loadout.get("updated_at", "restored"))[:40]))
                    project_ids={p["id"] for p in PROJECTS}
                    con.executemany("INSERT INTO project_submissions(profile_id,project_id,code,score,completed,awarded,updated_at) VALUES(?,?,?,?,?,?,?)", [(profile_id,x["project_id"],str(x.get("code",""))[:MAX_SOURCE],clamp_int(x.get("score"),0,100),int(bool(x.get("completed"))),int(bool(x.get("awarded"))),str(x.get("updated_at","restored"))[:40]) for x in project_submissions if isinstance(x, dict) and x.get("project_id") in project_ids])
                    for workspace in project_workspaces[:8]:
                        raw_files = workspace.get("files")
                        if raw_files is None:
                            try: raw_files = json.loads(workspace.get("files_json", "{}"))
                            except (TypeError, ValueError): continue
                        files, file_error = validate_project_files(raw_files)
                        workspace_id = str(workspace.get("workspace_id", ""))
                        name = str(workspace.get("name", "C++ Project"))[:80]
                        if file_error or not re.fullmatch(r"[0-9a-fA-F-]{16,64}", workspace_id): continue
                        con.execute("INSERT INTO project_workspaces(profile_id,workspace_id,name,files_json,updated_at) VALUES(?,?,?,?,?)", (profile_id, workspace_id, name, json.dumps(files, ensure_ascii=False), str(workspace.get("updated_at", "restored"))))
                    for session in interview_sessions[:100]:
                        if not isinstance(session,dict) or not re.fullmatch(r"[0-9a-fA-F-]{16,64}",str(session.get("session_id",""))): continue
                        try:
                            question_ids=json.loads(session.get("questions_json","[]")); answers=json.loads(session.get("answers_json","[]"))
                            valid_question_ids={q["id"] for q in INTERVIEW_BANK}
                            if not isinstance(question_ids,list) or not isinstance(answers,list) or len(question_ids)>5 or any(qid not in valid_question_ids for qid in question_ids): continue
                            # Rebuild answers from known fields instead of truncating serialized JSON
                            # (a cut string is invalid JSON and broke /api/career and /api/interview).
                            answers=[{"question_id":str(a.get("question_id",""))[:40],"topic":str(a.get("topic",""))[:40],"kind":"code" if a.get("kind")=="code" else "choice","correct":bool(a.get("correct"))} for a in answers[:len(question_ids)] if isinstance(a,dict)]
                            started_at=str(session.get("started_at",""))
                            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?", started_at): started_at="2000-01-01 00:00:00"  # unknown start = long expired
                            score=sum(1 for a in answers if a["correct"])
                            con.execute("INSERT INTO interview_sessions(profile_id,session_id,lang,questions_json,answers_json,score,completed,started_at,completed_at) VALUES(?,?,?,?,?,?,?,?,?)",(profile_id,session["session_id"],session.get("lang") if session.get("lang") in ("tr","ru") else "tr",json.dumps(question_ids),json.dumps(answers),score,int(bool(session.get("completed"))),started_at,str(session.get("completed_at",""))[:40]))
                        except (TypeError,ValueError,KeyError): continue
                    valid_portfolio_ids={p["id"] for p in PROJECTS}
                    con.executemany("INSERT INTO portfolio_notes(profile_id,project_id,description,technologies,updated_at) VALUES(?,?,?,?,?)",[(profile_id,item["project_id"],str(item.get("description",""))[:1000],str(item.get("technologies",""))[:200],str(item.get("updated_at","restored"))) for item in portfolio_notes if isinstance(item,dict) and item.get("project_id") in valid_portfolio_ids])
                    chapter_ids = {task["id"]: chapter["id"] for chapter in CURRICULUM for task in chapter["tasks"]}
                    con.executemany("INSERT INTO learning_events(profile_id,task_id,chapter_id,correct,error_kind,hint_used,created_at) VALUES(?,?,?,?,?,?,?)", [(profile_id,x["task_id"],chapter_ids[x["task_id"]],int(bool(x.get("correct",0))),str(x.get("error_kind",""))[:40],int(bool(x.get("hint_used",0))),str(x.get("created_at","restored"))[:40]) for x in learning_events[:5000] if x.get("task_id") in chapter_ids])
                    lab_ids = {lab["id"] for lab in LABS}
                    con.executemany("INSERT INTO lab_awards(profile_id,lab_id,xp,created_at) VALUES(?,?,?,?)", [(profile_id,x["lab_id"],clamp_int(x.get("xp"),0,LAB_XP.get(x["lab_id"],0)),str(x.get("created_at","restored"))[:40]) for x in lab_awards if isinstance(x, dict) and x.get("lab_id") in lab_ids])
                    allowed_modules = {"git", "conflict", "cmake", "testing", "terminal"}
                    for item in devtools_state:
                        if not isinstance(item, dict) or item.get("module") not in allowed_modules: continue
                        raw_state = item.get("data", {})
                        if isinstance(raw_state, str):
                            try: raw_state = json.loads(raw_state)
                            except (TypeError, ValueError): continue
                        if not isinstance(raw_state, dict): continue
                        serialized = json.dumps(raw_state, ensure_ascii=False)
                        if len(serialized) <= 30_000:
                            con.execute("INSERT INTO devtools_state(profile_id,module,data,updated_at) VALUES(?,?,?,?)", (profile_id, item["module"], serialized, str(item.get("updated_at", "restored"))[:40]))
                    for item in study_sessions:
                        if not isinstance(item, dict) or not re.fullmatch(r"[0-9a-fA-F-]{16,64}", str(item.get("session_id", ""))): continue
                        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(item.get("day", ""))): continue
                        seconds = max(0, min(43_200, int(item.get("seconds", 0))))
                        con.execute("INSERT INTO study_sessions(profile_id,session_id,day,seconds,updated_at) VALUES(?,?,?,?,?)", (profile_id, item["session_id"], item["day"], seconds, str(item.get("updated_at", "restored"))[:40]))
                    valid_challenges = {item["id"] for item in CHALLENGES}
                    for item in arena_attempts:
                        if item.get("challenge_id") not in valid_challenges or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(item.get("day", ""))): continue
                        con.execute("INSERT INTO arena_attempts(profile_id,day,challenge_id,attempts,best_score,best_elapsed_ms,awarded_xp,updated_at) VALUES(?,?,?,?,?,?,?,?)", (profile_id,item["day"],item["challenge_id"],max(0,min(10000,int(item.get("attempts",0)))),max(0,min(100,int(item.get("best_score",0)))),max(0,min(3_600_000,int(item.get("best_elapsed_ms",0)))),max(0,min(500,int(item.get("awarded_xp",0)))),str(item.get("updated_at","restored"))[:40]))
                    available_plugins, _ = discover_plugins(plugin_directories())
                    available_versions = {item["id"]: item["version"] for item in available_plugins}
                    for item in plugin_settings:
                        plugin_id = item.get("plugin_id")
                        if plugin_id not in available_versions: continue
                        con.execute("INSERT INTO plugin_settings(profile_id,plugin_id,version,enabled,updated_at) VALUES(?,?,?,?,?)", (profile_id,plugin_id,available_versions[plugin_id],int(bool(item.get("enabled"))),str(item.get("updated_at","restored"))[:40]))
                return self.send_json({"ok": True})
            if path == "/api/backup/database":
                # Whole database (all profiles), consistent online copy, verified with integrity_check.
                with db() as con:
                    if not valid_profile(con, body.get("profile_id")): return self.send_json({"error": "Profil bulunamadı."}, 404)
                target = backup_database(DB_PATH, DATA_ROOT / "backups", "manual")
                return self.send_json({"ok": True, "path": str(target)})
            if path == "/api/backup":
                profile_id = body.get("profile_id")
                save = self.export_profile(profile_id)
                folder = DATA_ROOT / "backups"
                folder.mkdir(exist_ok=True)
                safe_name = re.sub(r"[^\w-]+", "_", save["profile"]["name"]).strip("_") or "profile"
                dest = folder / f"{safe_name}_{time.strftime('%Y%m%d_%H%M%S')}.json"
                dest.write_text(json.dumps(save, ensure_ascii=False, indent=2), encoding="utf-8")
                return self.send_json({"ok": True, "path": str(dest)})
            if path == "/api/settings":
                profile_id = body.get("profile_id")
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    if body.get("lang") in ("tr", "ru"):
                        con.execute("UPDATE profiles SET lang=? WHERE id=?", (body["lang"], profile_id))
                    if body.get("ai_provider") in ("offline", "ollama", "openai", "claude", "groq", "off"):
                        con.execute("UPDATE profiles SET ai_provider=? WHERE id=?", (body["ai_provider"], profile_id))
                    if body.get("avatar") in PROFILE_AVATARS:
                        con.execute("UPDATE profiles SET avatar=? WHERE id=?", (body["avatar"], profile_id))
                return self.send_json({"ok": True})
            if path == "/api/companion/equip":
                profile_id = body.get("profile_id")
                item_id = str(body.get("item_id", ""))
                slot = str(body.get("slot", "")) or None
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı. / Профиль не найден."}, 404)
                    error = equip_companion_item(con, profile_id, item_id, slot)
                    if error:
                        lang = profile["lang"]
                        messages = {
                            "item_not_found": ("Aksesuar bulunamadı.", "Аксессуар не найден."),
                            "slot_mismatch": ("Bu aksesuar seçilen yuvaya takılamaz.", "Этот аксессуар нельзя надеть в выбранный слот."),
                            "not_owned": ("Önce bu aksesuarı satın almalısın.", "Сначала купи этот аксессуар."),
                            "invalid_slot": ("Geçersiz aksesuar yuvası.", "Недопустимый слот аксессуара."),
                        }
                        return self.send_json({"error": messages[error][0 if lang == "tr" else 1]}, 400)
                    sync_achievements(con, profile_id)
                    result = companion_payload(con, profile_id)
                return self.send_json({"ok": True, "companion": result})
            if path == "/api/companion/loadout/save":
                profile_id = body.get("profile_id")
                name = str(body.get("name", "")).strip()
                if not name or len(name) > 32:
                    return self.send_json({"error": "Kombinasyon adı 1–32 karakter olmalı. / Название комплекта должно содержать 1–32 символа."}, 400)
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı. / Профиль не найден."}, 404)
                    if con.execute("SELECT COUNT(*) FROM companion_loadouts WHERE profile_id=?", (profile_id,)).fetchone()[0] >= 20:
                        return self.send_json({"error": "En fazla 20 kombinasyon kaydedebilirsin. / Можно сохранить не более 20 комплектов."}, 409)
                    loadout_id = str(uuid.uuid4())
                    equipment = companion_equipment_map(con, profile_id)
                    con.execute("INSERT INTO companion_loadouts(profile_id,loadout_id,name,equipment_json) VALUES(?,?,?,?)", (profile_id, loadout_id, name, json.dumps(equipment, ensure_ascii=False)))
                    result = companion_payload(con, profile_id)
                return self.send_json({"ok": True, "loadout_id": loadout_id, "companion": result})
            if path == "/api/companion/loadout/apply":
                profile_id, loadout_id = body.get("profile_id"), str(body.get("loadout_id", ""))
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı. / Профиль не найден."}, 404)
                    loadout = con.execute("SELECT equipment_json FROM companion_loadouts WHERE profile_id=? AND loadout_id=?", (profile_id, loadout_id)).fetchone()
                    if not loadout: return self.send_json({"error": "Kombinasyon bulunamadı. / Комплект не найден."}, 404)
                    try: equipment = json.loads(loadout["equipment_json"])
                    except (TypeError, ValueError): equipment = None
                    valid_slots = {item["slot"] for item in SHOP.values()}
                    if not isinstance(equipment, dict) or any(slot not in valid_slots or SHOP.get(item_id, {}).get("slot") != slot or not con.execute("SELECT 1 FROM shop_items WHERE profile_id=? AND item_id=?", (profile_id, item_id)).fetchone() for slot, item_id in equipment.items()):
                        return self.send_json({"error": "Kombinasyondaki ürünler artık bu profilde mevcut değil. / Аксессуары комплекта больше не принадлежат этому профилю."}, 400)
                    con.execute("DELETE FROM companion_equipment WHERE profile_id=?", (profile_id,))
                    for slot, item_id in equipment.items():
                        con.execute("INSERT INTO companion_equipment(profile_id,slot,item_id) VALUES(?,?,?)", (profile_id, slot, item_id))
                    con.execute("UPDATE profiles SET active_item=? WHERE id=?", (next(reversed(list(equipment.values())), ""), profile_id))
                    con.execute("UPDATE companion_loadouts SET updated_at=CURRENT_TIMESTAMP WHERE profile_id=? AND loadout_id=?", (profile_id, loadout_id))
                    sync_achievements(con, profile_id)
                    result = companion_payload(con, profile_id)
                return self.send_json({"ok": True, "companion": result})
            if path == "/api/companion/loadout/delete":
                profile_id, loadout_id = body.get("profile_id"), str(body.get("loadout_id", ""))
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı. / Профиль не найден."}, 404)
                    deleted = con.execute("DELETE FROM companion_loadouts WHERE profile_id=? AND loadout_id=?", (profile_id, loadout_id)).rowcount
                    if not deleted: return self.send_json({"error": "Kombinasyon bulunamadı. / Комплект не найден."}, 404)
                    result = companion_payload(con, profile_id)
                return self.send_json({"ok": True, "companion": result})
            if path in ("/api/ai/key", "/api/ai/claude-key"):
                profile_id = body.get("profile_id")
                provider = "claude" if path == "/api/ai/claude-key" else str(body.get("provider", ""))
                if provider not in API_KEYS: return self.send_json({"error": "Bilinmeyen AI servisi."}, 400)
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                try:
                    save_provider_key(provider, str(body.get("key", "")))
                except ValueError as exc:
                    return self.send_json({"error": str(exc)}, 400)
                configured = bool(provider_key(provider))
                with db() as con:
                    if configured and body.get("key"):
                        con.execute("UPDATE profiles SET ai_provider=? WHERE id=?", (provider, profile_id))
                    elif not configured:
                        # Removing the key returns the tutor to offline hints instead of failing on every request.
                        con.execute("UPDATE profiles SET ai_provider='offline' WHERE id=? AND ai_provider=?", (profile_id, provider))
                hint = ("…" + provider_key(provider)[-4:]) if configured else ""
                return self.send_json({"ok": True, "provider": provider, "configured": configured, "key_hint": hint, f"{provider}_configured": configured, f"{provider}_key_hint": hint})
            if path == "/api/admin":
                if not ADMIN_ENABLED:
                    return self.send_json({"error": "Test paneli kapalı."}, 403)
                profile_id = body.get("profile_id")
                with DB_LOCK, db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    try:
                        admin_action(con, profile_id, str(body.get("action", "")), body.get("value"))
                    except ValueError as exc:
                        return self.send_json({"error": str(exc)}, 400)
                return self.send_json({"ok": True, **state(profile_id)})
            if path == "/api/rpg/equip":
                profile_id, item_id = body.get("profile_id"), str(body.get("item_id", ""))
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    error = equip_companion_item(con, profile_id, item_id)
                    if error:
                        message = "Aksesuar bulunamadı." if error == "item_not_found" else ("Önce bu aksesuarı satın almalısın." if profile["lang"] == "tr" else "Сначала купи этот аксессуар.")
                        return self.send_json({"error": message}, 400)
                    sync_achievements(con, profile_id)
                return self.send_json({"ok": True})
            if path == "/api/rpg/secret/claim":
                profile_id, quest_id = body.get("profile_id"), str(body.get("quest_id", ""))
                quest = quest_by_id(quest_id)
                if not quest: return self.send_json({"error": "Gizli görev bulunamadı."}, 404)
                with db(immediate=True) as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    lang = profile["lang"]
                    if con.execute("SELECT 1 FROM achievements WHERE profile_id=? AND id=?", (profile_id, quest_id)).fetchone():
                        return self.send_json({"error": "Bu ödül zaten alındı." if lang == "tr" else "Эта награда уже получена."}, 409)
                    bosses = [task["id"] for task in all_tasks() if task.get("kind") == "boss"]
                    current = guild_summary(con, profile_id, lang, bosses)
                    status = next(item for item in current["secret_quests"] if item["id"] == quest_id)
                    if not status["unlocked"]:
                        return self.send_json({"error": "Önce görev koşulunu tamamla." if lang == "tr" else "Сначала выполни условие задания."}, 400)
                    con.execute("UPDATE profiles SET xp=xp+? WHERE id=?", (quest["reward"], profile_id))
                    con.execute("INSERT INTO achievements(profile_id,id) VALUES(?,?)", (profile_id, quest_id))
                    sync_achievements(con, profile_id)
                    updated = guild_summary(con, profile_id, lang, bosses)
                return self.send_json({"ok": True, "reward": quest["reward"], "rpg": updated})
            if path == "/api/shop/buy":
                profile_id, item_id = body.get("profile_id"), body.get("item_id")
                if item_id not in SHOP: return self.send_json({"error": "Ürün bulunamadı."}, 404)
                with db(immediate=True) as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    if con.execute("SELECT 1 FROM shop_items WHERE profile_id=? AND item_id=?", (profile_id,item_id)).fetchone(): return self.send_json({"error": "Bu ürün zaten sende."}, 409)
                    cost = SHOP[item_id]["cost"]
                    if profile["xp"] < cost: return self.send_json({"error": "Bu ürün için yeterli XP yok."}, 400)
                    con.execute("UPDATE profiles SET xp=xp-? WHERE id=?", (cost,profile_id))
                    con.execute("INSERT INTO shop_items(profile_id,item_id) VALUES(?,?)", (profile_id,item_id))
                    sync_achievements(con, profile_id)
                return self.send_json({"ok": True})
            if path == "/api/shop/use":
                profile_id, item_id = body.get("profile_id"), body.get("item_id", "")
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    error = equip_companion_item(con, profile_id, str(item_id))
                    if error:
                        message = "Ürün bulunamadı." if error == "item_not_found" else ("Önce bu ürünü satın al." if profile["lang"] == "tr" else "Сначала купи этот предмет.")
                        return self.send_json({"error": message}, 400)
                    sync_achievements(con, profile_id)
                return self.send_json({"ok": True})
            if path == "/api/project/save":
                project_id, profile_id, code = body.get("project_id"), body.get("profile_id"), body.get("code", "")
                if project_id not in {p["id"] for p in PROJECTS}: return self.send_json({"error":"Proje bulunamadı."},404)
                if not isinstance(code,str) or len(code)>MAX_SOURCE: return self.send_json({"error":"Kod sınırı aşıldı."},400)
                with db() as con:
                    if not valid_profile(con,profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                    con.execute("INSERT INTO project_submissions(profile_id,project_id,code) VALUES(?,?,?) ON CONFLICT(profile_id,project_id) DO UPDATE SET code=excluded.code,updated_at=CURRENT_TIMESTAMP",(profile_id,project_id,code))
                return self.send_json({"ok":True})
            if path == "/api/workspace/create":
                profile_id, name = body.get("profile_id"), str(body.get("name", "C++ Project")).strip()[:80]
                if not name: return self.send_json({"error":"Proje adı boş olamaz. / Название проекта не может быть пустым."},400)
                workspace_id = str(uuid.uuid4())
                files = {"main.cpp": "#include <iostream>\n#include \"message.hpp\"\n\nint main() {\n    std::cout << make_message();\n    return 0;\n}\n", "include/message.hpp": "#pragma once\n#include <string>\nstd::string make_message();\n", "src/message.cpp": "#include \"message.hpp\"\nstd::string make_message() { return \"Hello, C++ Adventure!\\n\"; }\n"}
                template = next((t for t in WORKSPACE_TEMPLATES if t["id"] == body.get("template")), None)
                if template: files = dict(template["files"])
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                    if con.execute("SELECT COUNT(*) FROM project_workspaces WHERE profile_id=?",(profile_id,)).fetchone()[0] >= 8: return self.send_json({"error":"En fazla 8 çalışma alanı oluşturulabilir. / Можно создать не более 8 проектов."},400)
                    con.execute("INSERT INTO project_workspaces(profile_id,workspace_id,name,files_json) VALUES(?,?,?,?)",(profile_id,workspace_id,name,json.dumps(files,ensure_ascii=False)))
                return self.send_json({"ok":True,"workspace":{"workspace_id":workspace_id,"name":name,"files":files}})
            if path == "/api/workspace/save":
                profile_id, workspace_id = body.get("profile_id"), body.get("workspace_id")
                files, file_error = validate_project_files(body.get("files"))
                name = str(body.get("name", "C++ Project")).strip()[:80]
                if file_error: return self.send_json({"error":file_error},400)
                if not name: return self.send_json({"error":"Proje adı boş olamaz. / Название проекта не может быть пустым."},400)
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                    changed=con.execute("UPDATE project_workspaces SET name=?,files_json=?,updated_at=CURRENT_TIMESTAMP WHERE profile_id=? AND workspace_id=?",(name,json.dumps(files,ensure_ascii=False),profile_id,workspace_id)).rowcount
                    if not changed: return self.send_json({"error":"Çalışma alanı bulunamadı. / Проект не найден."},404)
                return self.send_json({"ok":True})
            if path == "/api/workspace/delete":
                with db() as con:
                    if not valid_profile(con,body.get("profile_id")): return self.send_json({"error":"Profil bulunamadı."},404)
                    con.execute("DELETE FROM project_workspaces WHERE profile_id=? AND workspace_id=?",(body.get("profile_id"),body.get("workspace_id")))
                return self.send_json({"ok":True})
            if path == "/api/portfolio/note":
                profile_id, project_id = body.get("profile_id"), body.get("project_id")
                description, technologies = body.get("description", ""), body.get("technologies", "")
                if not isinstance(description,str) or len(description)>1000 or not isinstance(technologies,str) or len(technologies)>200:
                    return self.send_json({"error":"Açıklama en çok 1.000, teknoloji listesi 200 karakter olabilir. / Описание — до 1 000, список технологий — до 200 символов."},400)
                if project_id not in {project["id"] for project in PROJECTS}: return self.send_json({"error":"Proje bulunamadı."},404)
                with db() as con:
                    if not valid_profile(con,profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                    if not con.execute("SELECT 1 FROM project_submissions WHERE profile_id=? AND project_id=?",(profile_id,project_id)).fetchone(): return self.send_json({"error":"Önce projede bir çalışma kaydet. / Сначала сохрани работу над проектом."},400)
                    con.execute("INSERT INTO portfolio_notes(profile_id,project_id,description,technologies) VALUES(?,?,?,?) ON CONFLICT(profile_id,project_id) DO UPDATE SET description=excluded.description,technologies=excluded.technologies,updated_at=CURRENT_TIMESTAMP",(profile_id,project_id,description,technologies))
                return self.send_json({"ok":True})
            if path == "/api/interview/start":
                profile_id=body.get("profile_id")
                session_id=str(uuid.uuid4())
                with db() as con:
                    profile=valid_profile(con,profile_id)
                    if not profile: return self.send_json({"error":"Profil bulunamadı."},404)
                    language=profile["lang"]
                    question_ids=[question["id"] for question in select_interview_questions(session_id,5)]
                    con.execute("INSERT INTO interview_sessions(profile_id,session_id,lang,questions_json) VALUES(?,?,?,?)",(profile_id,session_id,language,json.dumps(question_ids)))
                return self.send_json({"session_id":session_id,"index":0,"total":len(question_ids),"deadline_seconds":900,"question":public_interview_question(next(question for question in INTERVIEW_BANK if question["id"]==question_ids[0]),language)})
            if path == "/api/interview/answer":
                profile_id,session_id,index,answer=body.get("profile_id"),body.get("session_id"),body.get("index"),body.get("answer")
                if type(index) is not int or index<0: return self.send_json({"error":"Soru sırası geçersiz. / Неверный номер вопроса."},400)
                with db() as con:
                    if not valid_profile(con,profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                    session=con.execute("SELECT * FROM interview_sessions WHERE profile_id=? AND session_id=?",(profile_id,session_id)).fetchone()
                    if not session: return self.send_json({"error":"Mülakat oturumu bulunamadı. / Сессия собеседования не найдена."},404)
                    question_ids=json.loads(session["questions_json"]); answers=json.loads(session["answers_json"]); language=session["lang"]
                    if session["completed"]: return self.send_json({"error":"Bu mülakat tamamlandı. / Это собеседование уже завершено."},409)
                    elapsed=con.execute("SELECT (julianday('now')-julianday(started_at))*86400 FROM interview_sessions WHERE profile_id=? AND session_id=?",(profile_id,session_id)).fetchone()[0]
                    if elapsed is not None and elapsed>900:
                        con.execute("UPDATE interview_sessions SET completed=1,completed_at=CURRENT_TIMESTAMP WHERE profile_id=? AND session_id=?",(profile_id,session_id))
                        return self.send_json({"error":"15 dakikalık süre doldu. Bu oturum sonuçlarına bakabilirsin. / Время 15 минут истекло. Посмотри результаты сессии."},408)
                    if index!=len(answers) or index>=len(question_ids): return self.send_json({"error":"Bu soruyu sırayla yanıtla. / Ответь на вопросы по порядку."},409)
                    question=next((item for item in INTERVIEW_BANK if item["id"]==question_ids[index]),None)
                    if not question: return self.send_json({"error":"Mülakat sorusu bulunamadı."},500)
                checks=[]
                if question["kind"]=="choice":
                    correct=type(answer) is int and answer==question["answer"]
                else:
                    if not isinstance(answer,str) or len(answer)>MAX_SOURCE: return self.send_json({"error":"Kod boş olmalı ve 20.000 karakteri aşmamalı."},400)
                    correct=bool(answer.strip())
                    for test_index,case in enumerate(question["tests"],1):
                        result=compile_and_run(answer,case["input"])
                        passed=bool(result.get("ok") and normalize_output(result.get("output",""))==normalize_output(case["expected"]))
                        checks.append({"name":f"Test {test_index}","passed":passed,"output":result.get("output",""),"error":result.get("error","")})
                        correct=correct and passed
                answer_record={"question_id":question["id"],"topic":question["topic"],"kind":question["kind"],"correct":bool(correct)}
                with db(immediate=True) as con:
                    # Compilation ran outside the transaction; re-check under the write lock so
                    # two submissions for the same question cannot both be recorded.
                    current=con.execute("SELECT answers_json,completed FROM interview_sessions WHERE profile_id=? AND session_id=?",(profile_id,session_id)).fetchone()
                    answers=json.loads(current["answers_json"]) if current else []
                    if not current or current["completed"] or len(answers)!=index:
                        return self.send_json({"error":"Bu soruyu sırayla yanıtla. / Ответь на вопросы по порядку."},409)
                    answers.append(answer_record)
                    score=sum(1 for item in answers if item["correct"])
                    complete=len(answers)>=len(question_ids)
                    con.execute("UPDATE interview_sessions SET answers_json=?,score=?,completed=?,completed_at=CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE completed_at END WHERE profile_id=? AND session_id=?",(json.dumps(answers),score,int(complete),int(complete),profile_id,session_id))
                return self.send_json({"correct":bool(correct),"explanation":question.get("explanation",{}).get(language,""),"hint":("İpucu: çıktıyı ve her test girdisini ayrı ayrı izle." if language=="tr" else "Подсказка: проверь вывод для каждого тестового ввода отдельно." ) if question["kind"]=="code" and not correct else "","checks":checks,"score":score,"answered":len(answers),"total":len(question_ids),"complete":complete,"next_question":None if complete else public_interview_question(next(item for item in INTERVIEW_BANK if item["id"]==question_ids[len(answers)]),language)})
            if path == "/api/workspace/build":
                profile_id, workspace_id, mode = body.get("profile_id"),body.get("workspace_id"),body.get("mode","g++")
                submitted_files, file_error = validate_project_files(body.get("files")) if "files" in body else (None, None)
                if file_error: return self.send_json({"error":file_error},400)
                with db() as con:
                    if not valid_profile(con,profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                    row=con.execute("SELECT files_json FROM project_workspaces WHERE profile_id=? AND workspace_id=?",(profile_id,workspace_id)).fetchone()
                if not row: return self.send_json({"error":"Çalışma alanı bulunamadı. / Проект не найден."},404)
                files = submitted_files if submitted_files is not None else json.loads(row["files_json"])
                if submitted_files is not None:
                    with db() as con:
                        con.execute("UPDATE project_workspaces SET files_json=?,updated_at=CURRENT_TIMESTAMP WHERE profile_id=? AND workspace_id=?",(json.dumps(files,ensure_ascii=False),profile_id,workspace_id))
                result=build_project_workspace(files,body.get("input",""),mode)
                if result.get("phase")=="validate": return self.send_json(result,400)
                return self.send_json(result)
            if path == "/api/project/submit":
                project_id, profile_id, code = body.get("project_id"), body.get("profile_id"), body.get("code", "")
                project = next((p for p in PROJECTS if p["id"]==project_id),None)
                if not project: return self.send_json({"error":"Proje bulunamadı."},404)
                if not isinstance(code,str) or len(code)>MAX_SOURCE: return self.send_json({"error":"Kod sınırı aşıldı."},400)
                missing=[term for term in project["requires"] if term.casefold() not in code.casefold()]
                checks=[]
                for idx,case in enumerate(project["tests"],1):
                    result=compile_and_run(code,case["input"])
                    passed=result["ok"] and normalize_output(result.get("output",""))==normalize_output(case["expected"])
                    checks.append({"name":f"Test {idx}","passed":passed,"expected":case["expected"],"actual":result.get("output","").strip(),"error":result.get("error","")})
                    if not passed: break
                passed=not missing and len(checks)==len(project["tests"]) and all(c["passed"] for c in checks)
                score=int(100*sum(1 for c in checks if c["passed"])/len(project["tests"]))
                with db(immediate=True) as con:
                    if not valid_profile(con,profile_id): return self.send_json({"error":"Profil bulunamadı."},404)
                    existing=con.execute("SELECT awarded FROM project_submissions WHERE profile_id=? AND project_id=?",(profile_id,project_id)).fetchone()
                    awarded=bool(existing["awarded"]) if existing else False
                    grant=project["xp"] if passed and not awarded else 0
                    con.execute("INSERT INTO project_submissions(profile_id,project_id,code,score,completed,awarded) VALUES(?,?,?,?,?,?) ON CONFLICT(profile_id,project_id) DO UPDATE SET code=excluded.code,score=MAX(project_submissions.score,excluded.score),completed=MAX(project_submissions.completed,excluded.completed),awarded=MAX(project_submissions.awarded,excluded.awarded),updated_at=CURRENT_TIMESTAMP",(profile_id,project_id,code,score,int(passed),int(awarded or passed)))
                    if grant: con.execute("UPDATE profiles SET xp=xp+? WHERE id=?",(grant,profile_id))
                    if passed: con.execute("INSERT OR IGNORE INTO achievements(profile_id,id) VALUES(?,'project_builder')",(profile_id,))
                    sync_achievements(con, profile_id)
                return self.send_json({"ok":passed,"score":score,"checks":checks,"missing":missing,"xp":grant,"already_awarded":awarded})
            if path == "/api/labs/simulate":
                profile_id, lab_id = body.get("profile_id"), body.get("lab_id")
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    language = profile["lang"]
                try: result = simulate_visual_lab(lab_id, body.get("values", {}), language)
                except ValueError: return self.send_json({"error": "Laboratuvar bulunamadı."}, 404)
                return self.send_json(public_lab_result(result))
            if path == "/api/labs/submit":
                profile_id, lab_id = body.get("profile_id"), body.get("lab_id")
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    language = profile["lang"]
                try: result = simulate_visual_lab(lab_id, body.get("values", {}), language)
                except ValueError: return self.send_json({"error": "Laboratuvar bulunamadı."}, 404)
                answer = normalize_answer(body.get("answer", ""))
                if not answer or answer != normalize_answer(result["answer_key"]):
                    message = "Sonucu yeniden incele ve adımları tek tek ilerlet." if language == "tr" else "Проверь результат и пройди шаги по одному."
                    return self.send_json({"correct": False, "hint": message})
                lab = next(x for x in LABS if x["id"] == lab_id)
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    inserted = con.execute("INSERT OR IGNORE INTO lab_awards(profile_id,lab_id,xp) VALUES(?,?,?)", (profile_id, lab_id, lab["xp"])).rowcount
                    if inserted: con.execute("UPDATE profiles SET xp=xp+? WHERE id=?", (lab["xp"], profile_id))
                return self.send_json({"correct": True, "xp": lab["xp"] if inserted else 0, "already_completed": not bool(inserted)})
            if path == "/api/run":
                return self.send_json(compile_and_run(body.get("code", ""), body.get("input", "")))
            if path == "/api/devtools/action":
                profile_id, module, action = body.get("profile_id"), body.get("module"), body.get("action")
                if module not in {"git", "conflict", "cmake", "testing", "terminal"} or not isinstance(action, str):
                    return self.send_json({"error": "Invalid developer lab action."}, 400)
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    row = con.execute("SELECT data FROM devtools_state WHERE profile_id=? AND module=?", (profile_id, module)).fetchone()
                state_data = json.loads(row[0]) if row else initial_devtool_state(module)
                data = {key: value for key, value in body.items() if key not in {"profile_id", "module", "action"}}
                result = None
                if module == "testing" and action == "run":
                    code = data.get("code", state_data.get("code", ""))
                    stdin = data.get("input", state_data.get("input", ""))
                    expected = str(data.get("expected", state_data.get("expected", "")))
                    if len(str(code)) > MAX_SOURCE: return self.send_json({"error": "Kod sınırı aşıldı."}, 400)
                    state_data = apply_devtool_action(module, state_data, "save", {"code": code, "input": stdin, "expected": expected}, COMPILER)
                    result = compile_and_run(code, stdin)
                    result["expected"] = expected
                    result["tests_passed"] = bool(result.get("ok") and normalize_output(result.get("output", "")) == normalize_output(expected))
                    state_data["runs"] = int(state_data.get("runs", 0)) + 1
                    if result["tests_passed"]: state_data["passed"] = int(state_data.get("passed", 0)) + 1
                    state_data["last"] = "C++ test passed." if result["tests_passed"] else "C++ test failed. Compare expected output and compiler/run details."
                else:
                    state_data = apply_devtool_action(module, state_data, action, data, COMPILER, bool(resolve_cmake()))
                with db() as con:
                    con.execute("INSERT INTO devtools_state(profile_id,module,data) VALUES(?,?,?) ON CONFLICT(profile_id,module) DO UPDATE SET data=excluded.data,updated_at=CURRENT_TIMESTAMP", (profile_id, module, json.dumps(state_data, ensure_ascii=False)))
                return self.send_json({"state": state_data, "result": result})
            if path == "/api/study/pulse":
                profile_id, session_id = body.get("profile_id"), str(body.get("session_id", ""))
                day, seconds = str(body.get("day", "")), body.get("seconds")
                if not re.fullmatch(r"[0-9a-fA-F-]{16,64}", session_id) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) or type(seconds) is not int or seconds < 0 or seconds > 43_200:
                    return self.send_json({"error": "Oturum süresi geçersiz."}, 400)
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    con.execute("INSERT INTO study_sessions(profile_id,session_id,day,seconds) VALUES(?,?,?,?) ON CONFLICT(profile_id,session_id) DO UPDATE SET day=excluded.day,seconds=MAX(study_sessions.seconds,excluded.seconds),updated_at=CURRENT_TIMESTAMP", (profile_id, session_id, day, seconds))
                return self.send_json({"ok": True})
            if path == "/api/quality/analyze":
                profile_id, source = body.get("profile_id"), body.get("code", "")
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    language = profile["lang"]
                try: return self.send_json(analyze_code_quality(source, language))
                except ValueError as exc: return self.send_json({"error": str(exc)}, 400)
            if path == "/api/code-golf/compare":
                profile_id = body.get("profile_id")
                sources = [body.get("code_a", ""), body.get("code_b", "")]
                input_text = body.get("input", "")
                if any(not isinstance(source, str) or not source.strip() or len(source) > MAX_SOURCE for source in sources):
                    return self.send_json({"error": "İki çözüm de boş olmamalı ve 20.000 karakteri aşmamalı. / Оба решения должны быть непустыми и не длиннее 20 000 символов."}, 400)
                if not isinstance(input_text, str) or len(input_text) > 2000:
                    return self.send_json({"error": "Program girdisi 2.000 karakteri aşamaz."}, 400)
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    language = profile["lang"]
                variants = []
                for source in sources:
                    started = time.perf_counter()
                    run = compile_and_run(source, input_text)
                    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                    variants.append({"run": run, "elapsed_ms": elapsed_ms, "characters": len(source), "lines": len(source.splitlines()), "quality": analyze_code_quality(source, language)})
                matched = all(item["run"].get("ok") for item in variants) and normalize_output(variants[0]["run"].get("output", "")) == normalize_output(variants[1]["run"].get("output", ""))
                return self.send_json({"equivalent_output": matched, "variants": variants, "timing_note": "Compilation and one run are timed together; timings vary by machine and are not a complexity proof."})
            if path == "/api/ai/diagnose":
                profile_id, task_id, source = body.get("profile_id"), body.get("task_id"), body.get("code", "")
                if not isinstance(source, str) or len(source) > MAX_SOURCE: return self.send_json({"error": "Kod sınırı aşıldı."}, 400)
                task = next((item for item in all_tasks() if item["id"] == task_id), None)
                if not task: return self.send_json({"error": "Görev bulunamadı."}, 404)
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    provider, language = profile["ai_provider"], body.get("lang") if body.get("lang") in ("tr", "ru") else profile["lang"]
                    recent = [dict(row) for row in con.execute("SELECT task_id,attempts,correct,last_answer FROM quiz_results WHERE profile_id=? ORDER BY updated_at DESC LIMIT 8", (profile_id,))]
                local = diagnose_locally(task, source, body.get("input", ""), language)
                if provider in ("offline", "off"):
                    return self.send_json({"ok": True, "provider": provider, "diagnostic": local, "text": local["message" if language == "tr" else "message_ru"]})
                if provider in ("openai", "claude", "groq") and body.get("consent") is not True:
                    return self.send_json({"error": "Kodun çevrimiçi AI servisine gönderilmesi için onay gerekiyor.", "consent_required": True}, 403)
                course = next((chapter for chapter in CURRICULUM if any(item["id"] == task_id for item in chapter["tasks"])), {})
                prompt = json.dumps({"language": language, "topic": course.get("title", {}).get(language, "C++"), "lesson": course.get("lesson", {}).get(language, ""), "task": task.get("prompt", {}).get(language, ""), "concept_criteria": task.get("concept_criteria", {}).get(language, ""), "expected_output": task.get("expected", ""), "learner_code": source[:MAX_SOURCE], "program_input": body.get("input", "")[:2000], "compiler_and_test_diagnosis": local, "recent_quiz_history": recent}, ensure_ascii=False)
                try:
                    answer = call_ai_provider(provider, prompt)
                    if answer.get("error"):
                        return self.send_json({"ok": True, "provider": "offline-fallback", "diagnostic": local, "text": local["message" if language == "tr" else "message_ru"], "ai_unavailable": answer.get("unconfigured", False), "ai_error": answer["error"]})
                    in_tokens, out_tokens = int(answer.get("input_tokens", 0)), int(answer.get("output_tokens", 0))
                    in_rate = float(os.environ.get("CPP_ADVENTURE_INPUT_USD_PER_MILLION", "0"))
                    out_rate = float(os.environ.get("CPP_ADVENTURE_OUTPUT_USD_PER_MILLION", "0"))
                    if provider == "claude" and not (in_rate or out_rate):
                        in_rate, out_rate = CLAUDE_PRICES.get(str(answer.get("model") or CLAUDE_MODEL), (0, 0))
                    estimate = in_tokens * in_rate / 1_000_000 + out_tokens * out_rate / 1_000_000
                    with db() as con:
                        con.execute("INSERT INTO ai_usage(profile_id,provider,model,input_tokens,output_tokens,requests,estimated_usd) VALUES(?,?,?,?,?,1,?) ON CONFLICT(profile_id,provider,model) DO UPDATE SET input_tokens=input_tokens+excluded.input_tokens,output_tokens=output_tokens+excluded.output_tokens,requests=requests+1,estimated_usd=estimated_usd+excluded.estimated_usd,updated_at=CURRENT_TIMESTAMP", (profile_id, provider, answer.get("model", ""), in_tokens, out_tokens, estimate))
                    return self.send_json({"ok": True, "provider": provider, "model": answer.get("model"), "text": answer.get("text") or local["message" if language == "tr" else "message_ru"], "diagnostic": local, "input_tokens": in_tokens, "output_tokens": out_tokens, "estimated_usd": estimate, "cost_estimate_configured": in_rate > 0 or out_rate > 0})
                except urllib.error.HTTPError as exc:
                    return self.send_json({"ok": True, "provider": "offline-fallback", "diagnostic": local, "text": local["message" if language == "tr" else "message_ru"], "ai_error": f"AI HTTP {exc.code}"})
                except Exception as exc:
                    return self.send_json({"ok": True, "provider": "offline-fallback", "diagnostic": local, "text": local["message" if language == "tr" else "message_ru"], "ai_error": str(exc)[:240]})
            if path == "/api/language":
                lang = body.get("lang")
                if lang not in ("tr", "ru"):
                    return self.send_json({"error": "Dil desteklenmiyor."}, 400)
                profile_id = body.get("profile_id")
                with db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    con.execute("UPDATE profiles SET lang=? WHERE id=?", (lang, profile_id))
                return self.send_json({"ok": True})
            if path == "/api/submit":
                task_id, answer = body.get("task_id"), body.get("answer", "")
                profile_id = body.get("profile_id")
                task = next((t for t in all_tasks() if t["id"] == task_id), None)
                if not task:
                    return self.send_json({"error": "Görev bulunamadı."}, 404)
                chapter = next(c for c in CURRICULUM if any(t["id"] == task_id for t in c["tasks"]))
                with db() as con:
                    profile = valid_profile(con, profile_id)
                    if not profile: return self.send_json({"error": "Profil bulunamadı."}, 404)
                    prerequisites = chapter.get("prerequisites", [])
                    if prerequisites:
                        required_bosses = [next(c["tasks"][-1]["id"] for c in CURRICULUM if c["id"] == prereq) for prereq in prerequisites]
                        placeholders = ",".join("?" for _ in required_bosses)
                        opened = {row[0] for row in con.execute(f"SELECT task_id FROM completions WHERE profile_id=? AND task_id IN ({placeholders})", [profile_id, *required_bosses])}
                        if len(opened) != len(required_bosses):
                            message = "Önce bilgi haritasındaki ön koşul bölümlerinin Boss görevlerini tamamla." if profile["lang"] == "tr" else "Сначала заверши битвы с боссами в темах, указанных на карте знаний."
                            return self.send_json({"error": message, "code": "chapter_locked", "prerequisites": prerequisites}, 403)
                if not isinstance(answer, str) or len(answer) > MAX_SOURCE:
                    return self.send_json({"error": "Yanıt sınırı aşıldı."}, 400)
                if task["kind"] in ("code", "boss", "fix"):
                    missing = [] if task.get("concept_rule") else [term for term in task.get("requires", []) if term.casefold() not in answer.casefold()]
                    if missing:
                        record_learning_event(profile_id, task_id, False, "requirement", body.get("hint_used"))
                        return self.send_json({"correct": False, "result": {"error": "Görev şartı eksik / Требование не выполнено", "missing": missing}})
                    checks = []
                    for idx, case in enumerate(task.get("tests", [{"input": task.get("input", ""), "expected": task["expected"]}]), 1):
                        result = compile_and_run(answer, case.get("input", ""))
                        passed = result["ok"] and normalize_output(result.get("output", "")) == normalize_output(case["expected"])
                        checks.append({"name": f"Test {idx}", "passed": passed, "expected": case["expected"], "actual": result.get("output", "").strip(), "error": result.get("error", "")})
                        if not passed:
                            result["checks"] = checks
                            error_kind = "compile" if result.get("error") else "runtime" if result.get("exit_code") not in (None, 0) else "output"
                            record_learning_event(profile_id, task_id, False, error_kind, body.get("hint_used"))
                            return self.send_json({"correct": False, "result": result})
                    concept = None
                    if task.get("concept_rule"):
                        language = profile["lang"]
                        concept = check_cpp_concept(answer, task["concept_rule"], language)
                        if not concept["passed"]:
                            record_learning_event(profile_id, task_id, False, "concept", body.get("hint_used"))
                            return self.send_json({"correct": False, "result": {"kind": "concept", "error": concept["message"], "criteria": concept["label"], "checks": checks + [{"name": concept["label"], "passed": False, "kind": "concept"}]}})
                        checks.append({"name": concept["label"], "passed": True, "kind": "concept"})
                    correct = True
                    feedback = {"checks": checks, "concept": concept}
                else:
                    answer_key = task["answer"].get("tr" if (state(profile_id).get("profile",{}).get("lang","tr")=="tr") else "ru", "tr") if isinstance(task["answer"],dict) else task["answer"]
                    correct = normalize_answer(answer) == normalize_answer(answer_key)
                    feedback = None
                if not correct:
                    record_learning_event(profile_id, task_id, False, "wrong_answer", body.get("hint_used"))
                    if task["kind"] == "quiz":
                        with db() as con:
                            if valid_profile(con, profile_id):
                                con.execute("INSERT INTO quiz_results(profile_id,task_id,attempts,correct,last_answer) VALUES(?,?,1,0,?) ON CONFLICT(profile_id,task_id) DO UPDATE SET attempts=attempts+1,last_answer=excluded.last_answer,updated_at=CURRENT_TIMESTAMP", (profile_id, task_id, answer[:200]))
                                con.execute("INSERT INTO review_schedule(profile_id,task_id,due_at,interval_days) VALUES(?,?,datetime('now','+1 day'),1) ON CONFLICT(profile_id,task_id) DO UPDATE SET due_at=datetime('now','+1 day'),interval_days=1", (profile_id, task_id))
                    return self.send_json({"correct": False, "result": feedback})
                daily_bonus = 0
                with DB_LOCK, db() as con:
                    if not valid_profile(con, profile_id): return self.send_json({"error": "Profil bulunamadı."}, 404)
                    reward = max(1, int(task["xp"] * (0.9 if body.get("hint_used") else 1)))
                    inserted = con.execute("INSERT OR IGNORE INTO completions(profile_id,task_id,xp) VALUES(?,?,?)", (profile_id, task_id, reward)).rowcount
                    if inserted:
                        con.execute("UPDATE profiles SET xp=xp+? WHERE id=?", (reward, profile_id))
                    count = con.execute("SELECT COUNT(*) FROM completions WHERE profile_id=?", (profile_id,)).fetchone()[0]
                    if count >= 1: con.execute("INSERT OR IGNORE INTO achievements(profile_id,id) VALUES(?,'first_steps')", (profile_id,))
                    if count >= 10: con.execute("INSERT OR IGNORE INTO achievements(profile_id,id) VALUES(?,'cat_coder')", (profile_id,))
                    if count >= 25: con.execute("INSERT OR IGNORE INTO achievements(profile_id,id) VALUES(?,'quest_hunter')", (profile_id,))
                    if count >= len(all_tasks()): con.execute("INSERT OR IGNORE INTO achievements(profile_id,id) VALUES(?,'legend')", (profile_id,))
                    if task["kind"] == "quiz":
                        con.execute("INSERT INTO quiz_results(profile_id,task_id,attempts,correct,last_answer) VALUES(?,?,1,1,?) ON CONFLICT(profile_id,task_id) DO UPDATE SET attempts=attempts+1,correct=1,last_answer=excluded.last_answer,updated_at=CURRENT_TIMESTAMP", (profile_id, task_id, answer[:200]))
                        con.execute("INSERT INTO review_schedule(profile_id,task_id,due_at,interval_days) VALUES(?,?,datetime('now','+1 day'),1) ON CONFLICT(profile_id,task_id) DO UPDATE SET interval_days=MIN(interval_days*3,30),due_at=datetime('now','+' || MIN(interval_days*3,30) || ' days')", (profile_id, task_id))
                    if inserted:
                        today = time.strftime("%Y-%m-%d")
                        yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))
                        con.execute("UPDATE profiles SET streak=CASE WHEN last_day=? THEN streak WHEN last_day=? THEN streak+1 ELSE 1 END,last_day=? WHERE id=?", (today, yesterday, today, profile_id))
                    daily = con.execute("SELECT reward,completed FROM daily_quests WHERE profile_id=? AND day=? AND task_id=?", (profile_id, time.strftime("%Y-%m-%d"), task_id)).fetchone()
                    if daily and not daily["completed"]:
                        daily_bonus = daily["reward"]
                        con.execute("UPDATE profiles SET xp=xp+? WHERE id=?", (daily_bonus, profile_id))
                        con.execute("UPDATE daily_quests SET completed=1 WHERE profile_id=? AND day=?", (profile_id, time.strftime("%Y-%m-%d")))
                    sync_achievements(con, profile_id)
                record_learning_event(profile_id, task_id, True, "", body.get("hint_used"))
                return self.send_json({"correct": True, "xp": reward if inserted else 0, "daily_bonus": daily_bonus, "already_done": not inserted, "tests": feedback.get("checks", []) if isinstance(feedback, dict) else [], "criteria": task.get("requires", [])})
            if path == "/api/vscode":
                code = body.get("code", "")
                if not isinstance(code, str) or len(code) > MAX_SOURCE:
                    return self.send_json({"error": "Kod sınırı aşıldı."}, 400)
                folder = DATA_ROOT / "student-work"
                folder.mkdir(exist_ok=True)
                file = folder / "adventure.cpp"
                file.write_text(code, encoding="utf-8")
                vscode = shutil.which("code")
                if not vscode: return self.send_json({"error": "VS Code PATH içinde bulunamadı."}, 500)
                subprocess.Popen([vscode, str(file)], cwd=str(folder), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return self.send_json({"ok": True, "path": str(file)})
            if path == "/api/vscode/read":
                file = DATA_ROOT / "student-work" / "adventure.cpp"
                if not file.exists(): return self.send_json({"error": "Önce VS Code ile kod dosyasını aç."}, 404)
                return self.send_json({"ok": True, "code": file.read_text(encoding="utf-8",errors="replace")})
            return self.send_json({"error": "Bilinmeyen uç nokta."}, 404)
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_json({"error": str(exc)}, 400)
        except Exception as exc:
            return self.send_json({"error": f"Yerel sunucu hatası: {exc}"}, 500)


def create_app_server(port: int = 0):
    """HTTP server for the real app: loopback only, per-launch API secret, fresh PIN locks.

    Binding port 0 lets the OS pick a free port atomically (no probe-then-rebind race).
    Returns (server, auth, start_url); open start_url in the window to establish the session.
    """
    auth = LaunchAuth()
    handler = type("AppHandler", (Handler,), {"auth": auth})
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    with _UNLOCK_LOCK:
        UNLOCKED_PROFILES.clear()
    start_url = f"http://127.0.0.1:{httpd.server_address[1]}/__session?code={auth.new_bootstrap_code()}"
    return httpd, auth, start_url


def main():
    init_db()
    server, _auth, start_url = create_app_server(8765)
    print("C++ Adventure hazır: http://127.0.0.1:8765")
    print("Kapatmak için bu pencereyi kapatın veya Ctrl+C kullanın.")
    threading.Timer(0.8, lambda: webbrowser.open(start_url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
