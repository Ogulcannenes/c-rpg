"""Görev metinlerinin netleştirilmiş sürümleri.

Bazı görevler, testlerin beklediği kuralı (çıktı biçimi, eşik değerleri, girdi sırası) metinde
söylemiyordu. Buradaki metinler testlerle birebir uyumludur; ``apply`` müfredat yüklenirken
eski metnin yerine geçer. Kavram ve tahmin sorularına da göreve özel ipuçları eklenir.
"""
from __future__ import annotations

PROMPTS = {
    "c01-03": ("Bu programda bir sözdizimi hatası var: bir komutun sonunda bir işaret eksik. Hatayı bul ve düzelt; program aşağıdaki örnekteki üç satırı yazdırmalı.",
               "В программе синтаксическая ошибка: в конце одной команды не хватает знака. Найди и исправь её; программа должна вывести три строки из примера ниже."),
    "c01-04": ("Şu üç satırı aynen ve bu sırayla yazdır (her biri ayrı satırda):\nC++ ADVENTURE\nHello, C++!\nAdventure begins!",
               "Выведи ровно эти три строки в таком порядке (каждую с новой строки):\nC++ ADVENTURE\nHello, C++!\nAdventure begins!"),
    "c01-boss": ("Boss: Şu üç satırı aynen ve bu sırayla yazdır:\n=== CAT GUILD ===\nHello, traveler!\nMay the code be with you!",
                 "Босс: выведи ровно эти три строки в таком порядке:\n=== CAT GUILD ===\nHello, traveler!\nMay the code be with you!"),
    "c04-boss": ("Boss: iki tam sayı a ve b oku; (a + b) * (a - b) sonucunu yazdır. Negatif sayılarda ve a = b olduğunda da doğru çalışmalı.",
                 "Босс: прочитай два целых числа a и b; выведи (a + b) * (a - b). Программа должна работать и с отрицательными числами, и при a = b."),
    "c05-boss": ("Boss: bir puan oku. 80 veya üzeriyse `Master`, 50–79 arasındaysa `Explorer`, 50'nin altındaysa `Apprentice` yazdır (Türkçe karakter kullanmadan).",
                 "Босс: прочитай баллы. 80 и больше — выведи `Master`, от 50 до 79 — `Explorer`, меньше 50 — `Apprentice`."),
    "c06-03": ("Döngü n'i atlıyor: n = 4 için yalnızca `1 2 3` yazıyor. Düzelt; 1'den n'e kadar (n dahil) sayıları aralarında boşlukla yazdırsın. n = 0 ise hiçbir şey yazmasın.",
               "Цикл пропускает n: при n = 4 выводит только `1 2 3`. Исправь его, чтобы выводились числа от 1 до n включительно через пробел. При n = 0 ничего не выводить."),
    "c06-04": ("n oku ve 1'den n'e kadar (n dahil) sayıları aralarında boşlukla yazdır. n = 0 ise hiçbir şey yazma.",
               "Прочитай n и выведи числа от 1 до n включительно через пробел. При n = 0 ничего не выводи."),
    "c06-boss": ("Boss: n oku; 1'den n'e kadar (n dahil) olan çift sayıların toplamını bir döngüyle bul ve yazdır. Örnek: n = 6 → 2 + 4 + 6 = 12.",
                 "Босс: прочитай n; циклом найди сумму чётных чисел от 1 до n включительно и выведи её. Пример: n = 6 → 2 + 4 + 6 = 12."),
    "c07-boss": ("Boss: üç tam sayı a, b ve c oku. `int gorevPuani(int a, int b, int c)` fonksiyonu a + 2*b - c değerini döndürsün; main'de çağırıp sonucu yazdır.",
                 "Босс: прочитай три целых числа a, b и c. Функция `int gorevPuani(int a, int b, int c)` должна возвращать a + 2*b - c; вызови её в main и выведи результат."),
    "c08-03": ("Toplama döngüsü son elemanı atlıyor. Girdi: önce n, sonra n tam sayı. Düzelt; n sayının hepsinin toplamını yazdırsın.",
               "Цикл суммирования пропускает последний элемент. Ввод: сначала n, затем n целых чисел. Исправь, чтобы выводилась сумма всех n чисел."),
    "c08-04": ("Önce n'i, sonra n tam sayıyı oku; değerleri bir std::vector'e koy ve toplamlarını döngüyle hesaplayıp yazdır.",
               "Сначала прочитай n, затем n целых чисел; положи их в std::vector, посчитай сумму в цикле и выведи её."),
    "c08-boss": ("Boss: önce n'i, sonra n tam sayıyı oku; en büyük değeri döngüyle bulup yazdır. Sayıların hepsi negatif olabilir ya da yalnızca tek sayı olabilir.",
                 "Босс: сначала прочитай n, затем n целых чисел; найди циклом наибольшее и выведи его. Все числа могут быть отрицательными, а число может быть всего одно."),
    "c09-03": ("Program adı selamla bitişik yazıyor (`MerhabaMavi`). Araya boşluk koyarak `Hello <ad>` biçiminde yazdır.",
               "Программа пишет имя слитно с приветствием (`MerhabaMavi`). Добавь пробел, чтобы выводилось `Hello <имя>`."),
    "c09-04": ("Bir satırı (boşluk içerebilir) std::getline ile oku ve `Merhaba <satır>` yazdır. Örnek: `Luna Pati` → `Hello Luna Pati`.",
               "Прочитай строку целиком (в ней могут быть пробелы) через std::getline и выведи `Merhaba <строка>`. Пример: `Luna Pati` → `Hello Luna Pati`."),
    "c09-boss": ("Boss: bir ad ve bir soyad oku. Aralarında boşluk olan tam adı oluştur; tam adı ve boşluk dahil karakter sayısını yazdır. Örnek: `Mira Star` → `Mira Star 8`.",
                 "Босс: прочитай имя и фамилию. Собери полное имя с пробелом между ними; выведи его и число символов вместе с пробелом. Пример: `Mira Star` → `Mira Star 8`."),
    "c10-03": ("Program sayıyı referans üzerinden azaltıyor (`ref--`). Düzelt; referans üzerinden 1 artırsın ve asıl değişkeni yazdırsın.",
               "Программа уменьшает число через ссылку (`ref--`). Исправь: увеличь его через ссылку на 1 и выведи исходную переменную."),
    "c10-boss": ("Boss: iki sayı a ve b oku. Referans parametreli bir fonksiyonla (örneğin `void degistir(int& x, int& y)`) değerlerini yer değiştir ve `a b` biçiminde yazdır.",
                 "Босс: прочитай два числа a и b. Поменяй их значения функцией с параметрами-ссылками (например, `void degistir(int& x, int& y)`) и выведи `a b`."),
    "c11-04": ("Kedi adını ve yaşını oku. `struct Kedi` tanımla, okunan değerleri nesnenin alanlarına koy ve alanları `ad yaş` biçiminde yazdır.",
               "Прочитай имя и возраст кота. Объяви `struct Kedi`, запиши значения в поля объекта и выведи поля как `имя возраст`."),
    "c11-boss": ("Boss: ad, XP ve tamamlandı bilgisini (1 ya da 0) oku. Bunları `Quest` struct'ının alanlarında tut ve `ad XP durum` yazdır; durum 1 ise `Done`, 0 ise `Open` olsun.",
                 "Босс: прочитай название, XP и признак выполнения (1 или 0). Сохрани их в полях struct `Quest` и выведи `название XP статус`; статус `Done` для 1 и `Open` для 0."),
    "c12-03": ("`boosted()` metodu gücün 2 fazlasını döndürmeli, ama şu an yalnızca 1 fazlasını döndürüyor. Metodu düzelt.",
               "Метод `boosted()` должен возвращать силу плюс 2, а сейчас возвращает только плюс 1. Исправь метод."),
    "c12-04": ("Bir güç değeri oku. Kurucusu gücü saklayan `class Hero` yaz; `boosted()` metodu gücün 2 fazlasını döndürsün. main'deki hazır kod nesneyi oluşturup sonucu yazdırıyor.",
               "Прочитай значение силы. Напиши `class Hero`, конструктор которого сохраняет силу; метод `boosted()` возвращает силу плюс 2. Готовый код в main создаёт объект и выводит результат."),
    "c12-boss": ("Boss: güç ve bonus oku. `Hero` sınıfı kurucuda gücü saklasın; `train(int bonus)` metodu bonusu güce ekleyip yeni gücü döndürsün. main'deki hazır kod sonucu yazdırıyor.",
                 "Босс: прочитай силу и бонус. Класс `Hero` хранит силу из конструктора; метод `train(int bonus)` прибавляет бонус к силе и возвращает новую силу. Готовый код в main выводит результат."),
    "c13-03": ("Sıralama ters yönde yapılıyor. Girdi: önce n, sonra n sayı. Düzelt; sayıları küçükten büyüğe sıralayıp aralarında boşlukla yazdırsın.",
               "Сортировка идёт в обратную сторону. Ввод: сначала n, затем n чисел. Исправь, чтобы числа выводились по возрастанию через пробел."),
    "c13-04": ("Önce n'i, sonra n sayıyı oku; std::vector içinde sakla, std::sort ile küçükten büyüğe sırala ve aralarında boşlukla yazdır.",
               "Сначала прочитай n, затем n чисел; сохрани их в std::vector, отсортируй std::sort по возрастанию и выведи через пробел."),
    "c13-boss": ("Boss: önce n'i, sonra n sayıyı oku; sırala ve en küçük ile en büyük değeri `min max` biçiminde yazdır. Tekrar eden ve negatif sayılar olabilir.",
                 "Босс: сначала прочитай n, затем n чисел; отсортируй и выведи наименьшее и наибольшее как `min max`. Числа могут повторяться и быть отрицательными."),
    "c14-03": ("Bu program yalnızca hata fırlatıyor. Yeniden yaz: ad ve XP oku; try bloğunda bunları bir dosyaya yaz, aynı dosyadan geri oku ve `ad XP` yazdır. Hata olursa catch içinde mesaj yazdır.",
               "Эта программа только бросает ошибку. Перепиши её: прочитай имя и XP; в блоке try запиши их в файл, прочитай из того же файла и выведи `имя XP`. При ошибке выведи сообщение в catch."),
    "c14-04": ("Kedi adı ve XP oku. try bloğu içinde bunları bir dosyaya yaz, aynı dosyadan geri oku ve okunanı `ad XP` biçiminde yazdır; olası hatayı catch ile yakala.",
               "Прочитай имя кота и XP. В блоке try запиши их в файл, прочитай из того же файла и выведи прочитанное как `имя XP`; возможную ошибку перехвати в catch."),
    "c14-boss": ("Boss: önce n'i, sonra n puanı oku. Puanları bir dosyaya yaz, dosyadan geri oku ve toplamlarını yazdır. Dosya işlemlerini try/catch içine al. n = 0 ise toplam 0'dır.",
                 "Босс: сначала прочитай n, затем n результатов. Запиши их в файл, прочитай обратно и выведи сумму. Работу с файлом оберни в try/catch. При n = 0 сумма равна 0."),
    "c15-03": ("Program okunan değerler yerine hep `Pati 100` yazıyor. Okunan ad ve puanı kullanarak `ad puan` yazdır.",
               "Программа всегда пишет `Pati 100` вместо прочитанных значений. Выведи `имя очки`, используя прочитанные имя и очки."),
    "c15-04": ("Kahraman adını, görev sayısını (n) ve n görev puanını oku. Puanları döngüyle topla; 25 veya üzeri olan her puana 5 bonus ekle. `rankFor(toplam)` fonksiyonu toplam 50 veya üzeriyse `Gold`, değilse `Silver` döndürsün. `ad toplam rütbe` yazdır.",
               "Прочитай имя героя, число заданий (n) и n результатов. Сложи их в цикле; к каждому результату от 25 и выше добавь бонус 5. Функция `rankFor(сумма)` возвращает `Gold`, если сумма 50 и больше, иначе `Silver`. Выведи `имя сумма ранг`."),
    "c15-boss": ("Boss: mini RPG. Kahraman adı, başlangıç XP'si, ödül sayısı (n) ve n ödülü oku. Her ödülü XP'ye ekle; 30 veya üzeri ödüllere ayrıca 5 bonus ekle. `rankFor(xp)`: 70 ve üzeri `Gold`, 20–69 `Silver`, 20'nin altı `Bronze`. `ad xp rütbe` yazdır.",
                 "Босс: мини-RPG. Прочитай имя героя, начальный XP, число наград (n) и n наград. Прибавь каждую награду к XP; к наградам от 30 и выше добавь ещё 5. `rankFor(xp)`: 70 и больше — `Gold`, 20–69 — `Silver`, меньше 20 — `Bronze`. Выведи `имя xp ранг`."),
    "c18-04": ("`Sekil` taban sınıfında sanal `alan()` metodu olsun; `Dikdortgen(a, b)` ve `Kare(a)` onu override etsin. İki sayı a ve b oku: dikdörtgenin kenarları a ve b, karenin kenarı a. Taban sınıf referanslarıyla iki alanı `dikdörtgen kare` sırasıyla yaz.",
               "В базовом классе `Sekil` сделай виртуальный метод `alan()`; `Dikdortgen(a, b)` и `Kare(a)` переопределяют его. Прочитай два числа a и b: стороны прямоугольника — a и b, сторона квадрата — a. Через ссылки на базовый класс выведи две площади: `прямоугольник квадрат`."),
    "c20-03": ("Sayaç her kelimeyi görünce sayıyı artırmak yerine 1'e eşitliyor. Girdi: önce n, sonra n kelime. Düzelt; farklı kelime sayısını ve `kedi` kelimesinin kaç kez geçtiğini aralarında boşlukla yazdır.",
               "Счётчик при каждой встрече слова присваивает 1 вместо увеличения. Ввод: сначала n, затем n слов. Исправь и выведи через пробел число разных слов и сколько раз встретилось `kedi`."),
}

QUIZ_HINTS = (
    ("Ders notlarında bu kavramın anlatıldığı bölüme bak.", "Посмотри раздел урока, где объясняется это понятие."),
    ("Seçeneklerden birine tıklayabilirsin; önce kesin yanlış olanları ele.", "Можно нажать на вариант; сначала отбрось заведомо неверные."),
)
PREDICT_HINTS = (
    ("Kodu satır satır izle ve her değişkenin değerini kâğıda not al.", "Пройди код построчно и записывай значение каждой переменной."),
    ("Yalnızca ekrana yazılanı gir; araya kendin boşluk ya da satır ekleme.", "Вводи только то, что появится на экране; не добавляй своих пробелов и переносов."),
)


def _answer(task, lang):
    answer = task.get("answer", "")
    return answer.get(lang, answer.get("tr", "")) if isinstance(answer, dict) else str(answer)


def _hints(task):
    if task["kind"] == "quiz":
        third = {lang: (f"Doğru cevap '{_answer(task, lang)[:1]}' ile başlıyor." if lang == "tr" else f"Правильный ответ начинается с «{_answer(task, lang)[:1]}».") for lang in ("tr", "ru")}
        base = QUIZ_HINTS
    else:
        third = {lang: (f"Çıktı {len(_answer(task, lang))} karakterden oluşuyor." if lang == "tr" else f"Длина вывода в символах: {len(_answer(task, lang))}.") for lang in ("tr", "ru")}
        base = PREDICT_HINTS
    return {lang: [pair[0 if lang == "tr" else 1] for pair in base] + [third[lang]] for lang in ("tr", "ru")}


def apply(curriculum):
    for chapter in curriculum:
        for task in chapter["tasks"]:
            if task["id"] in PROMPTS:
                tr, ru = PROMPTS[task["id"]]
                task["prompt"] = {"tr": tr, "ru": ru}
            if task["kind"] in {"quiz", "predict"}:
                task["hints"] = _hints(task)
    return curriculum
