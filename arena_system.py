"""Offline single-player coding arena challenges."""
from __future__ import annotations

from datetime import date


CHALLENGES = (
    {"id": "fish_sort", "xp": 100, "title": {"tr": "Balık Pazarını Sırala", "ru": "Сортировка рыбного рынка"},
     "description": {"tr": "N sayısını ve ardından N tam sayı oku; küçükten büyüğe sırala. Birden çok senaryo gizlice denetlenir.", "ru": "Прочитай N и затем N целых чисел; отсортируй их по возрастанию. Решение проверяется на нескольких скрытых сценариях."},
     "starter": "#include <algorithm>\n#include <iostream>\n#include <vector>\nint main() {\n    int n; std::cin >> n;\n    std::vector<int> values(n);\n    for (int& value : values) std::cin >> value;\n    // Sırala ve yazdır\n}\n",
     "tests": [{"input": "5 4 1 3 2 0", "expected": "0 1 2 3 4"}, {"input": "1 -7", "expected": "-7"}, {"input": "0", "expected": ""}, {"input": "4 9 9 -1 0", "expected": "-1 0 9 9"}]},
    {"id": "score_total", "xp": 110, "title": {"tr": "Pati Skorunu Hesapla", "ru": "Подсчёт очков лапки"},
     "description": {"tr": "Satır sonuna kadar gelen tam sayıları topla ve toplamı yazdır. Girdi boş olabilir.", "ru": "Сложи целые числа до конца ввода и выведи сумму. Ввод может быть пустым."},
     "starter": "#include <iostream>\nint main() {\n    int value, total = 0;\n    // Tüm girdiyi oku ve topla\n    std::cout << total << '\\n';\n}\n",
     "tests": [{"input": "3 4 5", "expected": "12"}, {"input": "-2 2 0", "expected": "0"}, {"input": "", "expected": "0"}, {"input": "100", "expected": "100"}]},
    {"id": "word_count", "xp": 120, "title": {"tr": "Kelime Sayacı", "ru": "Счётчик слов"},
     "description": {"tr": "Bir satır oku ve boşlukla ayrılan kelime sayısını yazdır. Birden fazla boşluğu da doğru ele al.", "ru": "Прочитай строку и выведи число слов, разделённых пробелами. Корректно обработай повторяющиеся пробелы."},
     "starter": "#include <iostream>\n#include <sstream>\n#include <string>\nint main() {\n    std::string line; std::getline(std::cin, line);\n    // Kelimeleri say\n}\n",
     "tests": [{"input": "red blue", "expected": "2"}, {"input": "one", "expected": "1"}, {"input": "  two   words  ", "expected": "2"}, {"input": "", "expected": "0"}]},
)


def daily_challenge(day: str | None = None) -> dict:
    selected_day = day or date.today().isoformat()
    try:
        ordinal = date.fromisoformat(selected_day).toordinal()
    except ValueError:
        selected_day = date.today().isoformat()
        ordinal = date.today().toordinal()
    challenge = CHALLENGES[ordinal % len(CHALLENGES)]
    return {**challenge, "day": selected_day}
