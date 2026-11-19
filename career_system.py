"""Offline career milestones and bilingual C++ interview question bank."""
from __future__ import annotations

import random


CAREER_LEVELS = [
    {"id": "beginner", "tasks": 0, "projects": 0, "title": {"tr": "Başlangıç Programcısı", "ru": "Начинающий программист"}},
    {"id": "intermediate", "tasks": 15, "projects": 1, "title": {"tr": "Orta Seviye Geliştirici", "ru": "Разработчик среднего уровня"}},
    {"id": "advanced", "tasks": 45, "projects": 2, "title": {"tr": "İleri C++ Geliştirici", "ru": "Продвинутый C++ разработчик"}},
    {"id": "professional", "tasks": 75, "projects": 3, "title": {"tr": "Profesyonel Geliştirici", "ru": "Профессиональный разработчик"}},
]

INTERVIEW_BANK = [
    {"id":"value_ref","kind":"choice","topic":"References","prompt":{"tr":"Bir int değişkenine bağlanmış lvalue reference için hangisi doğrudur?","ru":"Что верно для lvalue-ссылки на переменную int?"},"options":{"tr":["Bağlandıktan sonra başka bir değişkene yeniden bağlanamaz.","Her erişimde yeni bir kopya oluşturur.","Mutlaka nullptr olabilir."],"ru":["После привязки её нельзя перенаправить на другую переменную.","При каждом обращении создаётся копия.","Она обязательно может быть nullptr."]},"answer":0,"explanation":{"tr":"Reference başlatılırken bir nesneye bağlanır ve sonradan başka nesneye yönelmez.","ru":"Ссылка привязывается к объекту при создании и не перенаправляется на другой объект."}},
    {"id":"vector_growth","kind":"choice","topic":"STL","prompt":{"tr":"std::vector sona eleman eklediğinde ne olabilir?","ru":"Что может произойти при добавлении элемента в конец std::vector?"},"options":{"tr":["Kapasite yetmezse bellek yeniden ayrılır ve eski iterator/reference geçersizleşebilir.","Her zaman tüm elemanlar linked list'e taşınır.","Boyut hiçbir zaman değişmez."],"ru":["Если ёмкости недостаточно, память выделяется заново и старые итераторы/ссылки могут стать недействительными.","Все элементы всегда перемещаются в связный список.","Размер никогда не меняется."]},"answer":0,"explanation":{"tr":"Vector bitişik bellek tutar; kapasite büyümesi yeniden ayırma ve iterator geçersizleşmesine yol açabilir.","ru":"Вектор хранит элементы подряд; рост ёмкости может перевыделить память и инвалидировать итераторы."}},
    {"id":"unique_ptr","kind":"choice","topic":"Memory Management","prompt":{"tr":"std::unique_ptr'ın temel amacı nedir?","ru":"Какова основная цель std::unique_ptr?"},"options":{"tr":["Sahipliği tek tutup kaynak ömrünü otomatik yönetmek.","Bir nesneyi sınırsız sayıda kopyalamak.","Belleği elle free etmek."],"ru":["Единолично владеть ресурсом и автоматически управлять его временем жизни.","Копировать объект неограниченное число раз.","Освобождать память вручную через free." ]},"answer":0,"explanation":{"tr":"unique_ptr tek sahiplik taşır; kapsamdan çıkınca sahip olduğu nesneyi yok eder.","ru":"unique_ptr обеспечивает единоличное владение и удаляет объект при выходе из области видимости."}},
    {"id":"virtual_dtor","kind":"choice","topic":"OOP","prompt":{"tr":"Polymorphic base sınıf pointer'ı üzerinden türetilmiş nesne silinirken sanal destructor neden gerekir?","ru":"Зачем нужен виртуальный деструктор при удалении производного объекта через указатель на базовый класс?"},"options":{"tr":["Türetilmiş destructor'ın da çağrılmasını sağlamak için.","Virtual fonksiyonları hızlandırmak için.","Nesneyi stack'e taşımak için."],"ru":["Чтобы также вызвался деструктор производного класса.","Чтобы ускорить виртуальные функции.","Чтобы переместить объект в стек."]},"answer":0,"explanation":{"tr":"Base destructor sanal değilse base pointer üzerinden silme, türetilmiş yıkıcıyı çağırmayabilir.","ru":"Без виртуального деструктора удаление через базовый указатель может не вызвать деструктор производного класса."}},
    {"id":"binary_complexity","kind":"choice","topic":"Algorithms","prompt":{"tr":"Sıralı bir dizide binary search'in zaman karmaşıklığı nedir?","ru":"Какова временная сложность бинарного поиска в отсортированном массиве?"},"options":{"tr":["O(log n)","O(n²)","O(1) her durumda"],"ru":["O(log n)","O(n²)","O(1) всегда"]},"answer":0,"explanation":{"tr":"Her adımda arama aralığı yarıya iner.","ru":"На каждом шаге диапазон поиска уменьшается вдвое."}},
    {"id":"const_correct","kind":"choice","topic":"C++ Basics","prompt":{"tr":"Bir fonksiyon parametresini değiştirmeden büyük bir nesneyi kopyalamadan geçirmek için yaygın tercih hangisidir?","ru":"Как обычно передают большой объект в функцию без копирования и изменения?"},"options":{"tr":["const T&", "T**", "volatile T"],"ru":["const T&", "T**", "volatile T"]},"answer":0,"explanation":{"tr":"const reference kopyayı önler ve fonksiyon içinde değişikliği engeller.","ru":"Константная ссылка избегает копирования и запрещает изменение в функции."}},
    {"id":"raii","kind":"choice","topic":"Resource Management","prompt":{"tr":"RAII hangi fikri uygular?","ru":"Какую идею реализует RAII?"},"options":{"tr":["Kaynak ömrünü bir nesnenin ömrüne bağlamak.","Her kaynağı global yapmak.","Destructor'ları hiç çağırmamak."],"ru":["Связывать время жизни ресурса со временем жизни объекта.","Делать каждый ресурс глобальным.","Никогда не вызывать деструкторы."]},"answer":0,"explanation":{"tr":"Nesne oluşturulurken kaynağı edinir, yok edilirken bırakır; RAII hata yollarında da güvenli temizleme sağlar.","ru":"Объект получает ресурс при создании и освобождает при уничтожении, в том числе при ошибках."}},
    {"id":"reverse_values","kind":"code","topic":"Arrays and Loops","prompt":{"tr":"Önce N (0–100), sonra N tamsayı oku. Değerleri ters sırayla, aralarında boşlukla yazdır. En az iki farklı girdi sınamasını geç.","ru":"Сначала прочитай N (0–100), затем N целых чисел. Выведи их в обратном порядке через пробел. Пройди не менее двух разных тестов."},"starter":"#include <iostream>\n#include <vector>\nint main() {\n    int n;\n    std::cin >> n;\n    std::vector<int> values(n);\n    for (int& value : values) std::cin >> value;\n    // Print the values in reverse order.\n}\n","tests":[{"input":"4 3 8 -1 5","expected":"5 -1 8 3"},{"input":"1 42","expected":"42"},{"input":"0","expected":""}]},
    {"id":"running_sum","kind":"code","topic":"Vectors and Algorithms","prompt":{"tr":"N (1–100) ve ardından N tamsayı oku. Her elemanın dahil olduğu önek toplamlarını tek satırda yazdır. Örnek: 2 4 -1 → 2 6 5.","ru":"Прочитай N (1–100) и затем N целых чисел. Выведи префиксные суммы в одну строку. Пример: 2 4 -1 → 2 6 5."},"starter":"#include <iostream>\n#include <vector>\nint main() {\n    int n;\n    std::cin >> n;\n    std::vector<int> values(n);\n    for (int& value : values) std::cin >> value;\n    // Print the running sums.\n}\n","tests":[{"input":"3 2 4 -1","expected":"2 6 5"},{"input":"4 0 0 3 -2","expected":"0 0 3 1"},{"input":"1 -7","expected":"-7"}]},
]


def career_summary(tasks_completed: int, total_tasks: int, project_rows: list[dict], language: str = "tr", total_projects: int = 3) -> dict:
    completed_projects = sum(bool(project.get("completed")) for project in project_rows)
    current_index = 0
    for index, level in enumerate(CAREER_LEVELS):
        if tasks_completed >= level["tasks"] and completed_projects >= level["projects"]:
            current_index = index
    current = CAREER_LEVELS[current_index]
    next_level = CAREER_LEVELS[current_index + 1] if current_index + 1 < len(CAREER_LEVELS) else None
    goals = []
    if next_level:
        if tasks_completed < next_level["tasks"]:
            goals.append({"key": "tasks", "current": tasks_completed, "target": next_level["tasks"]})
        if completed_projects < next_level["projects"]:
            goals.append({"key": "projects", "current": completed_projects, "target": next_level["projects"]})
    else:
        if tasks_completed < total_tasks: goals.append({"key": "tasks", "current": tasks_completed, "target": total_tasks})
        if completed_projects < total_projects: goals.append({"key": "projects", "current": completed_projects, "target": total_projects})
    return {"level_id": current["id"], "level": current["title"][language], "next_level": next_level["title"][language] if next_level else None, "tasks_completed": tasks_completed, "total_tasks": total_tasks, "projects_completed": completed_projects, "projects_total": total_projects, "goals": goals, "career_levels": [{"id": level["id"], "title": level["title"][language], "tasks": level["tasks"], "projects": level["projects"], "unlocked": index <= current_index} for index, level in enumerate(CAREER_LEVELS)]}


def select_interview_questions(seed: str, count: int = 5) -> list[dict]:
    rng = random.Random(seed)
    concepts = [item for item in INTERVIEW_BANK if item["kind"] == "choice"]
    coding = [item for item in INTERVIEW_BANK if item["kind"] == "code"]
    chosen = rng.sample(concepts, min(count - 1, len(concepts))) + rng.sample(coding, 1)
    rng.shuffle(chosen)
    return chosen
