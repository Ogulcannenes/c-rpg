"""Proje atölyesi: proje açıklamalarının netleştirilmesi, adım planları ve yeni projeler.

Her proje; zorluk, kullanılan kavramlar, adım adım plan (milestones) ve beklenen çıktı
biçimini açıkça söyleyen bir açıklama içerir. Yeni projelerin referans çözümleri
``tests/test_workshop_projects.py`` içinde gerçek g++ ile doğrulanır.
"""
from __future__ import annotations


def _t(tr, ru):
    return {"tr": tr, "ru": ru}


CLARIFY = {
    "cat_greeting": {
        "description": _t("Bir isim oku ve tam olarak `Merhaba, <isim>!` biçiminde selam yazdır. Örnek: `Luna` → `Merhaba, Luna!` (virgül ve ünlem işaretine dikkat).",
                          "Прочитай имя и выведи приветствие ровно в виде `Merhaba, <имя>!`. Пример: `Luna` → `Merhaba, Luna!` (обрати внимание на запятую и восклицательный знак)."),
        "difficulty": 1, "concepts": ["string", "cin", "cout"],
        "steps": [_t("İsmi std::string değişkene oku", "Прочитай имя в переменную std::string"), _t("`Merhaba, ` metnini, ismi ve `!` işaretini art arda yazdır", "Выведи подряд `Merhaba, `, имя и `!`"), _t("Farklı isimlerle Çalıştır'a basıp dene", "Проверь кнопкой «Запустить» с разными именами")],
    },
    "score_tracker": {
        "description": _t("Üç tam sayı (görev puanı) oku ve toplamlarını yazdır. Puanlar negatif ya da sıfır olabilir. Örnek: `3 4 5` → `12`.",
                          "Прочитай три целых числа (очки за задания) и выведи их сумму. Очки могут быть отрицательными или нулевыми. Пример: `3 4 5` → `12`."),
        "difficulty": 1, "concepts": ["int", "cin", "+"],
        "steps": [_t("Üç int değişkeni tek satırda oku", "Прочитай три переменные int"), _t("Toplamı hesapla ve yazdır", "Посчитай и выведи сумму"), _t("`-2 2 0` gibi sınır durumlarını dene", "Проверь граничные случаи вроде `-2 2 0`")],
    },
    "algorithm_sort": {
        "description": _t("Önce N'i, sonra N tam sayıyı oku. Sayıları bir std::vector'e koy, std::sort ile küçükten büyüğe sırala ve aralarında boşluk bırakarak yazdır. Örnek: `5` ve `4 1 3 2 0` → `0 1 2 3 4`. std::sort O(N log N) zamanda çalışır.",
                          "Сначала прочитай N, затем N целых чисел. Положи их в std::vector, отсортируй std::sort по возрастанию и выведи через пробел. Пример: `5` и `4 1 3 2 0` → `0 1 2 3 4`. std::sort работает за O(N log N)."),
        "difficulty": 2, "concepts": ["vector", "sort", "for"],
        "steps": [_t("N'i oku ve N elemanlı bir vector oluştur", "Прочитай N и создай vector из N элементов"), _t("Döngüyle N sayıyı vector'e oku", "В цикле прочитай N чисел в vector"), _t("std::sort(v.begin(), v.end()) ile sırala", "Отсортируй через std::sort(v.begin(), v.end())"), _t("Elemanları aralarında boşlukla yazdır", "Выведи элементы через пробел")],
    },
}

EXTRA = [
    {"id": "cat_inventory", "xp": 160, "difficulty": 2, "concepts": ["struct", "vector", "for"],
     "title": _t("Kedi barınağı envanteri", "Учёт кошачьего приюта"),
     "description": _t("Önce kedi sayısı N'i, sonra her satırda bir kedinin adını ve yaşını oku. `struct Kedi` ile verileri bir std::vector'de tut. En yaşlı kedinin adını ve tüm kedilerin yaş ortalamasını (tam sayı bölmesi) `ad ortalama` biçiminde yazdır. En yaşlı birden fazlaysa ilk okunanı seç. Örnek: `3`, `Luna 3`, `Pamuk 5`, `Mavi 2` → `Pamuk 3`.",
                       "Сначала прочитай число кошек N, затем в каждой строке имя и возраст кошки. Храни данные в std::vector из `struct Kedi`. Выведи имя самой старшей кошки и средний возраст (целочисленное деление) в виде `имя среднее`. Если старших несколько — выбери первую прочитанную. Пример: `3`, `Luna 3`, `Pamuk 5`, `Mavi 2` → `Pamuk 3`."),
     "steps": [_t("`struct Kedi { std::string ad; int yas; };` tanımla", "Объяви `struct Kedi { std::string ad; int yas; };`"), _t("N'i oku, döngüyle N kediyi vector'e ekle", "Прочитай N и в цикле добавь N кошек в vector"), _t("Döngüyle en büyük yaşı ve toplam yaşı bul", "Циклом найди наибольший возраст и сумму возрастов"), _t("`ad ortalama` yazdır", "Выведи `имя среднее`")],
     "starter": "#include <iostream>\n#include <string>\n#include <vector>\n\n// struct Kedi tanımla\n\nint main() {\n    int n;\n    std::cin >> n;\n    // kedileri oku, en yaşlıyı ve ortalamayı bul\n    return 0;\n}",
     "requires": ["struct", "vector", "std::cout"],
     "tests": [{"input": "3\nLuna 3\nPamuk 5\nMavi 2", "expected": "Pamuk 3"}, {"input": "1\nTek 7", "expected": "Tek 7"}, {"input": "4\nA 4\nB 9\nC 9\nD 1", "expected": "B 5"}]},
    {"id": "grade_report", "xp": 170, "difficulty": 2, "concepts": ["fonksiyon", "if", "for"],
     "title": _t("Not karnesi", "Табель оценок"),
     "description": _t("Önce not sayısı N'i, sonra N notu (0–100) oku. İki fonksiyon yaz: `int ortalama(const std::vector<int>& notlar)` ortalamayı (tam sayı bölmesi) döndürsün; `std::string harf(int ort)` 85 ve üzeri için `AA`, 70–84 için `BB`, 50–69 için `CC`, altı için `FF` döndürsün. `ortalama harf` yazdır. Örnek: `4`, `90 80 70 60` → `75 BB`.",
                       "Сначала прочитай число оценок N, затем N оценок (0–100). Напиши две функции: `int ortalama(const std::vector<int>& notlar)` возвращает среднее (целочисленное деление); `std::string harf(int ort)` возвращает `AA` для 85 и выше, `BB` для 70–84, `CC` для 50–69 и `FF` ниже. Выведи `среднее буква`. Пример: `4`, `90 80 70 60` → `75 BB`."),
     "steps": [_t("Notları bir vector'e oku", "Прочитай оценки в vector"), _t("ortalama fonksiyonunu yaz ve dene", "Напиши и проверь функцию ortalama"), _t("harf fonksiyonunda if / else if zincirini kur", "Построй цепочку if / else if в функции harf"), _t("`ortalama harf` yazdır", "Выведи `среднее буква`")],
     "starter": "#include <iostream>\n#include <string>\n#include <vector>\n\n// int ortalama(const std::vector<int>& notlar)\n// std::string harf(int ort)\n\nint main() {\n    int n;\n    std::cin >> n;\n    // notları oku ve karneyi yazdır\n    return 0;\n}",
     "requires": ["return", "if", "std::vector"],
     "tests": [{"input": "4\n90 80 70 60", "expected": "75 BB"}, {"input": "2\n100 85", "expected": "92 AA"}, {"input": "3\n10 20 30", "expected": "20 FF"}, {"input": "1\n69", "expected": "69 CC"}]},
    {"id": "palindrome", "xp": 150, "difficulty": 2, "concepts": ["string", "döngü", "indeks"],
     "title": _t("Palindrom dedektifi", "Детектив палиндромов"),
     "description": _t("Bir kelime oku. Kelimeyi tersine çevir ve `ters SONUÇ` yazdır: kelime tersten de aynı okunuyorsa SONUÇ `EVET`, değilse `HAYIR` olsun. Büyük/küçük harf fark eder. Örnek: `kayak` → `kayak EVET`, `kedi` → `idek HAYIR`.",
                       "Прочитай слово. Разверни его и выведи `перевёрнутое РЕЗУЛЬТАТ`: если слово читается одинаково в обе стороны — РЕЗУЛЬТАТ `EVET`, иначе `HAYIR`. Регистр букв важен. Пример: `kayak` → `kayak EVET`, `kedi` → `idek HAYIR`."),
     "steps": [_t("Kelimeyi std::string olarak oku", "Прочитай слово в std::string"), _t("Sondan başa doğru dönen bir döngüyle ters metni oluştur", "Собери перевёрнутую строку циклом с конца"), _t("Ters metni asılla karşılaştır", "Сравни перевёрнутую строку с исходной"), _t("`ters EVET` ya da `ters HAYIR` yazdır", "Выведи `перевёрнутое EVET` или `перевёрнутое HAYIR`")],
     "starter": "#include <iostream>\n#include <string>\n\nint main() {\n    std::string kelime;\n    std::cin >> kelime;\n    // ters çevir ve karşılaştır\n    return 0;\n}",
     "requires": ["std::string", "for", "std::cout"],
     "tests": [{"input": "kayak", "expected": "kayak EVET"}, {"input": "kedi", "expected": "idek HAYIR"}, {"input": "a", "expected": "a EVET"}, {"input": "Ana", "expected": "anA HAYIR"}]},
    {"id": "bank_account", "xp": 190, "difficulty": 3, "concepts": ["class", "private", "metot"],
     "title": _t("Kedi bankası hesabı", "Кошачий банковский счёт"),
     "description": _t("Başlangıç bakiyesini ve işlem sayısı Q'yu oku. Sonra Q işlem gelir: `Y tutar` para yatırır, `C tutar` para çeker. `class Hesap` yaz: bakiye private olsun; `yatir(int)` ve `cek(int)` metotları olsun. Bakiye yetmiyorsa `cek` false döndürsün ve bakiye değişmesin. Sonunda `bakiye başarısızİşlemSayısı` yazdır. Örnek: `100`, `3`, `Y 50`, `C 200`, `C 30` → `120 1`.",
                       "Прочитай начальный баланс и число операций Q. Затем идут Q операций: `Y сумма` — пополнение, `C сумма` — снятие. Напиши `class Hesap`: баланс private, методы `yatir(int)` и `cek(int)`. Если денег не хватает, `cek` возвращает false и баланс не меняется. В конце выведи `баланс числоНеудачныхОпераций`. Пример: `100`, `3`, `Y 50`, `C 200`, `C 30` → `120 1`."),
     "steps": [_t("`class Hesap` yaz; bakiye private, kurucu başlangıç bakiyesini alsın", "Напиши `class Hesap`: баланс private, конструктор принимает начальный баланс"), _t("`yatir` ve `cek` metotlarını ekle; cek bool döndürsün", "Добавь методы `yatir` и `cek`; cek возвращает bool"), _t("Q işlemi döngüyle oku ve uygula", "Прочитай и выполни Q операций в цикле"), _t("Başarısız çekimleri say ve sonucu yazdır", "Посчитай неудачные снятия и выведи результат")],
     "starter": "#include <iostream>\n\n// class Hesap { ... };\n\nint main() {\n    int baslangic, q;\n    std::cin >> baslangic >> q;\n    // işlemleri oku ve uygula\n    return 0;\n}",
     "requires": ["class", "private", "bool"],
     "tests": [{"input": "100\n3\nY 50\nC 200\nC 30", "expected": "120 1"}, {"input": "0\n2\nC 1\nC 2", "expected": "0 2"}, {"input": "10\n1\nY 5", "expected": "15 0"}]},
    {"id": "prime_hunter", "xp": 180, "difficulty": 3, "concepts": ["iç içe döngü", "fonksiyon", "%"],
     "title": _t("Asal sayı avcısı", "Охотник за простыми числами"),
     "description": _t("Bir N oku. 2'den N'e kadar (N dahil) asal sayıları ilk satıra aralarında boşlukla, kaç tane olduklarını ikinci satıra yazdır. `bool asalMi(int x)` fonksiyonu yaz; x'i 2'den √x'e kadar bölenlerle dene. N < 2 ise ilk satır boş, ikinci satır 0 olsun. Örnek: `20` → `2 3 5 7 11 13 17 19` ve `8`.",
                       "Прочитай N. В первой строке выведи через пробел простые числа от 2 до N включительно, во второй — их количество. Напиши функцию `bool asalMi(int x)`, проверяющую делители от 2 до √x. Если N < 2, первая строка пустая, а во второй 0. Пример: `20` → `2 3 5 7 11 13 17 19` и `8`."),
     "steps": [_t("`bool asalMi(int x)` fonksiyonunu yaz (x < 2 ise false)", "Напиши `bool asalMi(int x)` (false при x < 2)"), _t("İç döngüde `i * i <= x` koşuluyla bölenleri dene", "Во внутреннем цикле проверяй делители при `i * i <= x`"), _t("2'den N'e kadar asal olanları yazdır ve say", "Выведи и посчитай простые от 2 до N"), _t("İkinci satıra sayıyı yaz", "Во второй строке выведи количество")],
     "starter": "#include <iostream>\n\n// bool asalMi(int x)\n\nint main() {\n    int n;\n    std::cin >> n;\n    // asalları yazdır ve say\n    return 0;\n}",
     "requires": ["bool", "for", "%"],
     "tests": [{"input": "20", "expected": "2 3 5 7 11 13 17 19\n8"}, {"input": "2", "expected": "2\n1"}, {"input": "1", "expected": "\n0"}, {"input": "30", "expected": "2 3 5 7 11 13 17 19 23 29\n10"}]},
]

TEMPLATES = [
    {"id": "cat_library", "name": _t("Kedi kütüphanesi (header + kaynak)", "Кошачья библиотека (заголовок + исходник)"),
     "files": {
         "main.cpp": "#include <iostream>\n#include \"kedi.h\"\n\nint main() {\n    Kedi luna{\"Luna\", 3};\n    std::cout << tanit(luna) << \"\\n\";\n    std::cout << \"Insan yasi: \" << insanYasi(luna) << \"\\n\";\n}\n",
         "kedi.h": "#pragma once\n#include <string>\n\nstruct Kedi {\n    std::string ad;\n    int yas;\n};\n\nstd::string tanit(const Kedi& k);\nint insanYasi(const Kedi& k);\n",
         "kedi.cpp": "#include \"kedi.h\"\n\nstd::string tanit(const Kedi& k) {\n    return k.ad + \" (\" + std::to_string(k.yas) + \" yas)\";\n}\n\nint insanYasi(const Kedi& k) {\n    return k.yas <= 2 ? k.yas * 12 : 24 + (k.yas - 2) * 4;\n}\n",
     }},
    {"id": "calculator", "name": _t("Hesap makinesi modülü", "Модуль калькулятора"),
     "files": {
         "main.cpp": "#include <iostream>\n#include \"hesap.h\"\n\nint main() {\n    int a, b;\n    char op;\n    std::cin >> a >> op >> b;\n    std::cout << hesapla(a, op, b) << \"\\n\";\n}\n",
         "hesap.h": "#pragma once\n\nint hesapla(int a, char op, int b);\n",
         "hesap.cpp": "#include \"hesap.h\"\n\nint hesapla(int a, char op, int b) {\n    switch (op) {\n        case '+': return a + b;\n        case '-': return a - b;\n        case '*': return a * b;\n        case '/': return b != 0 ? a / b : 0;\n    }\n    return 0;\n}\n",
     }},
]


def extend_projects(projects: list) -> list:
    for project in projects:
        project.update(CLARIFY.get(project["id"], {}))
    known = {project["id"] for project in projects}
    projects.extend(project for project in EXTRA if project["id"] not in known)
    return projects
