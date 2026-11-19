"""Offline, profile-scoped adaptive review and evidence-based predictions."""
from __future__ import annotations


def learning_insights(topics: list[dict], recent: list[dict], review_due: list[dict], language: str) -> dict:
    lang = language if language in ("tr", "ru") else "tr"
    events_by_chapter: dict[str, list[dict]] = {}
    for event in recent:
        events_by_chapter.setdefault(event["chapter_id"], []).append(event)

    predictions = []
    for topic in topics:
        attempts = int(topic.get("attempts", 0))
        if attempts < 3:
            continue
        events = events_by_chapter.get(topic["id"], [])
        recent_events = events[:5]
        recent_accuracy = (sum(int(item["correct"]) for item in recent_events) / len(recent_events)) if recent_events else topic.get("accuracy")
        if recent_accuracy is None:
            continue
        accuracy = float(topic.get("accuracy") or 0)
        risk = "high" if recent_accuracy < .5 or (accuracy < .6 and recent_accuracy < .7) else "watch" if recent_accuracy < .8 else "low"
        if risk == "low":
            continue
        predictions.append({
            "chapter_id": topic["id"], "title": topic["title"], "attempts": attempts,
            "accuracy": round(accuracy, 3), "recent_accuracy": round(recent_accuracy, 3),
            "risk": risk, "confidence": "medium" if attempts < 6 else "high",
            "basis": "last_five_attempts" if len(recent_events) >= 3 else "all_attempts",
        })
    predictions.sort(key=lambda item: (item["risk"] != "high", item["recent_accuracy"], -item["attempts"]))

    if review_due:
        adaptive = {"kind": "review", "task_id": review_due[0]["task_id"], "chapter_id": review_due[0]["chapter_id"], "reason": "due", "confidence": "high"}
    elif predictions:
        weak_id = predictions[0]["chapter_id"]
        adaptive = {"kind": "strengthen", "task_id": None, "chapter_id": weak_id, "reason": "recent_errors", "confidence": predictions[0]["confidence"]}
    else:
        adaptive = {"kind": "continue", "task_id": None, "chapter_id": next((topic["id"] for topic in topics if topic.get("completed", 0) < topic.get("total", 0)), None), "reason": "next_unfinished_topic", "confidence": "low"}

    if lang == "tr":
        texts = {"review": "Zamanı gelen kısa tekrar", "strengthen": "Son denemelerde zorlanılan konuyu pekiştir", "continue": "Sıradaki açık konuya devam et", "empty": "Henüz yeterli deneme yok; tahmin üretmiyoruz.", "high": "Yüksek tekrar ihtiyacı", "watch": "Yakın takip önerilir"}
    else:
        texts = {"review": "Пора повторить тему", "strengthen": "Закрепи тему с недавними ошибками", "continue": "Продолжай следующую открытую тему", "empty": "Пока недостаточно попыток для прогноза.", "high": "Высокая потребность в повторении", "watch": "Рекомендуется повторение"}
    adaptive["label"] = texts[adaptive["kind"]]
    for item in predictions:
        item["risk_label"] = texts[item["risk"]]
    return {"predictions": predictions, "adaptive_path": adaptive, "prediction_note": texts["empty"] if not predictions else ""}
