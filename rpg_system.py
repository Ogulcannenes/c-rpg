"""Local, profile-scoped RPG progression derived from real learning activity."""
from __future__ import annotations


GUILD_RANKS = (
    {"id": "kitten", "xp": 0, "tr": "Yeni Patili", "ru": "Новичок с лапками"},
    {"id": "scout", "xp": 300, "tr": "Kod İzci Kedisi", "ru": "Кот-разведчик кода"},
    {"id": "debugger", "xp": 1000, "tr": "Hata Avcısı", "ru": "Охотник за ошибками"},
    {"id": "architect", "xp": 2500, "tr": "Pati Mimarı", "ru": "Архитектор лап"},
    {"id": "master", "xp": 5000, "tr": "C++ Lonca Ustası", "ru": "Мастер гильдии C++"},
)

SECRET_QUESTS = (
    {"id": "secret_bosses", "tr": "Boss Koleksiyoncusu", "ru": "Коллекционер боссов", "desc_tr": "Üç farklı bölüm boss'unu yen.", "desc_ru": "Победи боссов в трёх разных главах.", "reward": 160, "kind": "bosses", "target": 3},
    {"id": "secret_projects", "tr": "Atölye Gezgini", "ru": "Исследователь мастерской", "desc_tr": "İki gerçek proje teslimini tamamla.", "desc_ru": "Заверши два настоящих проекта.", "reward": 220, "kind": "projects", "target": 2},
    {"id": "secret_style", "tr": "Kedi Stilisti", "ru": "Кошачий стилист", "desc_tr": "Kedi dükkânından üç farklı aksesuar al.", "desc_ru": "Купи три разных аксессуара в магазине котов.", "reward": 100, "kind": "items", "target": 3},
    {"id": "secret_study", "tr": "Sessiz Kütüphane", "ru": "Тихая библиотека", "desc_tr": "Toplam 30 dakika öğrenme kaydı biriktir.", "desc_ru": "Набери 30 минут учёбы.", "reward": 140, "kind": "minutes", "target": 30},
)


def guild_summary(con, profile_id: str, lang: str = "tr", boss_task_ids=()) -> dict:
    profile = con.execute("SELECT xp,active_item FROM profiles WHERE id=?", (profile_id,)).fetchone()
    if not profile:
        raise ValueError("Profil bulunamadı.")
    xp = int(profile["xp"])
    rank_index = max(i for i, rank in enumerate(GUILD_RANKS) if xp >= rank["xp"])
    rank = GUILD_RANKS[rank_index]
    next_rank = GUILD_RANKS[rank_index + 1] if rank_index + 1 < len(GUILD_RANKS) else None
    completed_tasks = {r[0] for r in con.execute("SELECT task_id FROM completions WHERE profile_id=?", (profile_id,))}
    bosses = sum(task_id in completed_tasks for task_id in boss_task_ids)
    projects = con.execute("SELECT COUNT(*) FROM project_submissions WHERE profile_id=? AND completed=1", (profile_id,)).fetchone()[0]
    items = con.execute("SELECT COUNT(*) FROM shop_items WHERE profile_id=?", (profile_id,)).fetchone()[0]
    minutes = con.execute("SELECT COALESCE(SUM(seconds),0) FROM study_sessions WHERE profile_id=?", (profile_id,)).fetchone()[0] // 60
    metrics = {"bosses": min(3, int(bosses)), "projects": int(projects), "items": int(items), "minutes": int(minutes)}
    claimed = {r[0] for r in con.execute("SELECT id FROM achievements WHERE profile_id=?", (profile_id,))}
    secret = []
    for quest in SECRET_QUESTS:
        progress = min(quest["target"], metrics[quest["kind"]])
        secret.append({"id": quest["id"], "title": quest["tr" if lang == "tr" else "ru"],
                       "description": quest["desc_tr" if lang == "tr" else "desc_ru"],
                       "reward": quest["reward"], "progress": progress, "target": quest["target"],
                       "unlocked": progress >= quest["target"], "claimed": quest["id"] in claimed})
    return {"xp": xp, "rank": {"id": rank["id"], "title": rank["tr" if lang == "tr" else "ru"], "index": rank_index + 1,
                                 "count": len(GUILD_RANKS)},
            "next_rank": ({"title": next_rank["tr" if lang == "tr" else "ru"], "xp": next_rank["xp"],
                           "progress": min(100, round((xp - rank["xp"]) * 100 / (next_rank["xp"] - rank["xp"]))) }
                          if next_rank else None),
            "companion_stage": min(5, 1 + xp // 1000), "active_item": profile["active_item"],
            "owned_items": [r[0] for r in con.execute("SELECT item_id FROM shop_items WHERE profile_id=? ORDER BY bought_at", (profile_id,))],
            "metrics": metrics, "secret_quests": secret}


def quest_by_id(quest_id: str):
    return next((q for q in SECRET_QUESTS if q["id"] == quest_id), None)
