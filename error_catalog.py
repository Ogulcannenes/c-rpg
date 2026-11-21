"""Stable codes and Russian text for the server's error messages (Phase 10).

Handlers still write the Turkish message; ``localize`` adds ``code``, ``error_tr`` and
``error_ru`` so the page can show the learner's language and tests can match on codes.
Messages already written as "Türkçe / Русский" are split instead of looked up.
"""
from __future__ import annotations

CATALOG = {
    "Profil bulunamadı.": ("profile_not_found", "Профиль не найден."),
    "profile_not_found": ("profile_not_found", "Профиль не найден."),
    "Kod sınırı aşıldı.": ("code_too_long", "Превышен лимит размера кода."),
    "İstek reddedildi.": ("request_rejected", "Запрос отклонён."),
    "Proje bulunamadı.": ("project_not_found", "Проект не найден."),
    "plugin_directory_unavailable": ("plugin_directory_unavailable", "Папка плагинов недоступна."),
    "Profil veya PIN hatalı.": ("profile_or_pin_wrong", "Неверный профиль или PIN."),
    "Yedek dosyası biçimi desteklenmiyor.": ("backup_format_unsupported", "Формат файла резервной копии не поддерживается."),
    "Laboratuvar bulunamadı.": ("lab_not_found", "Лаборатория не найдена."),
    "Görev bulunamadı.": ("task_not_found", "Задание не найдено."),
    "Profil seçilmedi veya artık bulunamıyor.": ("profile_not_selected", "Профиль не выбран или больше не существует."),
    "G++/Clang++ bulunamadı. MSYS2 UCRT64 G++ kurulumu gerekli.": ("compiler_missing", "G++/Clang++ не найден. Нужна установка G++ из MSYS2 UCRT64."),
    "Kod boş olamaz.": ("code_empty", "Код не может быть пустым."),
    "Kod 20.000 karakter sınırını aşıyor.": ("code_too_long", "Код превышает лимит в 20 000 символов."),
    "Program girdisi metin olmalı ve 2.000 karakteri aşmamalı.": ("input_invalid", "Ввод программы должен быть текстом не длиннее 2000 символов."),
    "Derleme 15 saniyede tamamlanmadı; güvenli biçimde durduruldu.": ("compile_timeout", "Компиляция не завершилась за 15 секунд и была безопасно остановлена."),
    "Program 3 saniyede tamamlanmadı; güvenli biçimde durduruldu.": ("run_timeout", "Программа не завершилась за 3 секунды и была безопасно остановлена."),
    "Program çok fazla çıktı üretti (64 KB sınırı); güvenli biçimde durduruldu.": ("output_too_large", "Программа вывела слишком много данных (лимит 64 КБ) и была безопасно остановлена."),
    "Günlük görev değişmiş; Arena'yı yenile.": ("arena_challenge_changed", "Ежедневное задание изменилось; обнови Арену."),
    "Önce C++ çözümünü yaz.": ("code_empty", "Сначала напиши решение на C++."),
    "Eklenti durumu geçersiz.": ("plugin_state_invalid", "Недопустимое состояние плагина."),
    "Eklenti bulunamadı veya manifest güvenli değil.": ("plugin_unsafe", "Плагин не найден или его манифест небезопасен."),
    "PIN 4-8 rakam olmalı.": ("pin_invalid", "PIN должен состоять из 4–8 цифр."),
    "Yedekte geçersiz görev kaydı var.": ("backup_invalid_task", "В резервной копии есть недопустимая запись задания."),
    "Test paneli kapalı.": ("admin_disabled", "Тестовая панель выключена."),
    "Gizli görev bulunamadı.": ("secret_quest_not_found", "Секретное задание не найдено."),
    "Bu ödül zaten alındı.": ("reward_already_claimed", "Эта награда уже получена."),
    "Önce görev koşulunu tamamla.": ("quest_condition_unmet", "Сначала выполни условие задания."),
    "Ürün bulunamadı.": ("item_not_found", "Товар не найден."),
    "Bu ürün zaten sende.": ("item_already_owned", "Этот товар у тебя уже есть."),
    "Bu ürün için yeterli XP yok.": ("not_enough_xp", "Недостаточно XP для этого товара."),
    "Mülakat sorusu bulunamadı.": ("interview_question_missing", "Вопрос собеседования не найден."),
    "Kod boş olmalı ve 20.000 karakteri aşmamalı.": ("code_invalid", "Код не должен быть пустым и превышать 20 000 символов."),
    "Invalid developer lab action.": ("devtools_action_invalid", "Недопустимое действие лаборатории разработчика."),
    "Oturum süresi geçersiz.": ("session_time_invalid", "Недопустимая длительность сессии."),
    "Program girdisi 2.000 karakteri aşamaz.": ("input_too_long", "Ввод программы не может превышать 2000 символов."),
    "Kodun çevrimiçi AI servisine gönderilmesi için onay gerekiyor.": ("ai_consent_required", "Для отправки кода онлайн-ИИ нужно твоё согласие."),
    "Dil desteklenmiyor.": ("language_unsupported", "Язык не поддерживается."),
    "Yanıt sınırı aşıldı.": ("answer_too_long", "Превышен лимит длины ответа."),
    "VS Code PATH içinde bulunamadı.": ("vscode_missing", "VS Code не найден в PATH."),
    "Önce VS Code ile kod dosyasını aç.": ("vscode_not_opened", "Сначала открой файл кода в VS Code."),
    "Developer lab not found.": ("devtools_lab_not_found", "Лаборатория разработчика не найдена."),
    "Geçersiz simülasyon ayarı.": ("simulation_invalid", "Недопустимые параметры симуляции."),
    "Bilinmeyen uç nokta.": ("unknown_endpoint", "Неизвестный адрес API."),
}
# English-only internal messages also get a Turkish text for the Turkish page.
TURKISH_FOR = {
    "profile_not_found": "Profil bulunamadı.",
    "plugin_directory_unavailable": "Eklenti klasörüne erişilemiyor.",
    "Invalid developer lab action.": "Geçersiz geliştirici laboratuvarı işlemi.",
    "Developer lab not found.": "Geliştirici laboratuvarı bulunamadı.",
}


def _localize_one(container):
    message = container.get("error")
    if not isinstance(message, str) or not message:
        return
    if message in CATALOG:
        code, russian = CATALOG[message]
        container.setdefault("error_code", code)  # "code" already means source code in some responses
        container["error_tr"] = TURKISH_FOR.get(message, message)
        container["error_ru"] = russian
    elif " / " in message:
        turkish, _, russian = message.partition(" / ")
        container["error_tr"], container["error_ru"] = turkish.strip(), russian.strip()


def localize(payload):
    """Add language variants to a JSON response (top level and a nested ``result``)."""
    if isinstance(payload, dict):
        _localize_one(payload)
        if isinstance(payload.get("result"), dict):
            _localize_one(payload["result"])
    return payload
