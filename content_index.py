"""Constant-time lookups over the curriculum, plus invariants checked once at import.

The curriculum is fully built (and reordered) by ``curriculum.py`` at import time and never
mutated afterwards, so these indexes are always current. Callers previously re-scanned
``CURRICULUM`` with ``next(...)`` on every request, which was slow and raised StopIteration
for unknown ids.
"""
from __future__ import annotations

from curriculum import CURRICULUM

TASKS = [task for chapter in CURRICULUM for task in chapter["tasks"]]
TASK_BY_ID = {task["id"]: task for task in TASKS}
CHAPTER_BY_ID = {chapter["id"]: chapter for chapter in CURRICULUM}
CHAPTER_OF_TASK = {task["id"]: chapter for chapter in CURRICULUM for task in chapter["tasks"]}
BOSS_OF_CHAPTER = {chapter["id"]: chapter["tasks"][-1]["id"] for chapter in CURRICULUM}
CHAPTER_INDEX = {chapter["id"]: index for index, chapter in enumerate(CURRICULUM)}


def task(task_id):
    """The task dict, or None for unknown ids (e.g. removed content still referenced in old saves)."""
    return TASK_BY_ID.get(task_id)


def chapter_of(task_id):
    return CHAPTER_OF_TASK.get(task_id)


def boss_of(chapter_id):
    return BOSS_OF_CHAPTER.get(chapter_id)


def validate(curriculum=CURRICULUM) -> list[str]:
    """Return a list of broken invariants (empty when the content is consistent)."""
    errors, seen_tasks, chapter_ids = [], set(), [chapter["id"] for chapter in curriculum]
    if len(chapter_ids) != len(set(chapter_ids)):
        errors.append("duplicate chapter ids")
    for chapter in curriculum:
        if not chapter.get("tasks"):
            errors.append(f"{chapter['id']}: no tasks")
            continue
        if chapter["tasks"][-1].get("kind") != "boss":
            errors.append(f"{chapter['id']}: last task must be the boss (prerequisite gating relies on it)")
        for item in chapter["tasks"]:
            if item["id"] in seen_tasks:
                errors.append(f"duplicate task id {item['id']}")
            seen_tasks.add(item["id"])
        for prerequisite in chapter.get("prerequisites", []):
            if prerequisite not in chapter_ids:
                errors.append(f"{chapter['id']}: unknown prerequisite {prerequisite}")
    return errors


_ERRORS = validate()
if _ERRORS:  # fail loudly at startup instead of mis-gating chapters at runtime
    raise ValueError("Curriculum invariant violated: " + "; ".join(_ERRORS))
