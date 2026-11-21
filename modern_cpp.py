"""Modern C++ track: move semantics, C++17 vocabulary types, C++20 concepts/ranges and
real concurrency (std::thread, std::mutex, std::atomic).

Each chapter is complete on its own (lesson, five guide sections, eight missions in the
usual order: quiz, predict, quiz, predict, fix, warm-up, practice, boss) so the older,
index-aligned chapter tables do not need to grow. Every code mission is graded by
compiling and running hidden test cases plus a structural concept check; reference
solutions live in tests/test_modern_cpp.py and are compiled by the test suite.
"""
from concept_checker import RULES

TITLES = {
    "quiz": ("Hızlı Bilgi", "Блиц-вопрос"),
    "predict": ("Çıktıyı Tahmin Et", "Предскажи вывод"),
    "quiz2": ("Kavram Sorusu", "Вопрос на понимание"),
    "predict2": ("Kodu Zihninde Çalıştır", "Выполни код в уме"),
    "fix": ("Kedi Hatasını Düzelt", "Исправь ошибку кота"),
    "warm": ("Isınma Görevi", "Разминка"),
    "practice": ("Pratik Görevi", "Практическое задание"),
    "boss": ("Bölüm Boss'u", "Битва с боссом"),
}
XP = {"quiz": 15, "predict": 20, "quiz2": 15, "predict2": 20, "fix": 30, "warm": 35, "practice": 45, "boss": 80}
# Headers the prediction snippets need; tests wrap each snippet in a full program with these.
PREDICT_HEADERS = ("#include <iostream>\n#include <string>\n#include <string_view>\n#include <vector>\n#include <utility>\n"
                   "#include <optional>\n#include <variant>\n#include <concepts>\n#include <ranges>\n#include <thread>\n"
                   "#include <mutex>\n#include <atomic>\n")


def _case(input_text, expected):
    return {"input": input_text, "expected": expected}


def _quiz(tr, ru, answer):
    return {"tr": tr, "ru": ru, "answer": answer}


def _code(tr, ru, starter, cases, rule=None, requires=(), bug_type=None):
    return {"tr": tr, "ru": ru, "starter": starter, "tests": [_case(i, o) for i, o in cases],
            "rule": rule, "requires": list(requires), "bug_type": bug_type}


CHAPTERS = [
    # ------------------------------------------------------------------ c21
    {
        "id": "c21", "prerequisites": ["c17", "c12"],
        "title": ("Taşıma Semantiği ve Beşler Kuralı", "Семантика перемещения и правило пяти"),
        "lesson": (
            "Kopyalamak pahalı olabilir: büyük bir vector'ü kopyalamak tüm elemanları çoğaltır. Taşıma (move), kaynağın sahipliğini yeni nesneye devreder; eski nesne geçerli ama içeriği belirsiz (çoğu zaman boş) kalır. std::move hiçbir şeyi taşımaz, yalnızca ifadeyi rvalue'ya çevirerek taşımaya izin verir.",
            "Копирование бывает дорогим: копия большого vector дублирует все элементы. Перемещение (move) передаёт владение ресурсом новому объекту; старый объект остаётся корректным, но с неопределённым (обычно пустым) содержимым. std::move сам ничего не перемещает — он лишь приводит выражение к rvalue и тем самым разрешает перемещение."),
        "example": '#include <iostream>\n#include <string>\n#include <utility>\nint main() {\n    std::string a = "kedi";\n    std::string b = std::move(a); // kaynak b\'ye devredildi\n    std::cout << b;\n    return 0;\n}',
        "guide": [
            ("lvalue, rvalue ve T&&",
             "lvalue adı olan ve adresi alınabilen nesnedir; rvalue ise geçici bir değerdir (2 + 3, bir fonksiyonun döndürdüğü geçici nesne). T&& bir rvalue referansıdır: yalnızca geçicilere ya da std::move ile rvalue'ya çevrilmiş nesnelere bağlanır.",
             "lvalue, rvalue и T&&",
             "lvalue — объект с именем, у которого можно взять адрес; rvalue — временное значение (2 + 3, временный объект, возвращённый функцией). T&& — rvalue-ссылка: она связывается только с временными объектами или с объектами, приведёнными к rvalue через std::move.",
             "int a = 5;               // a: lvalue\nint&& r = a + 1;         // a + 1: rvalue\n// int&& x = a;          // ✗ lvalue'ya bağlanmaz\nint&& y = std::move(a);  // ✓"),
            ("Taşıyıcı kurucu",
             "Taşıyıcı kurucunun imzası Buffer(Buffer&&) şeklindedir: diğer nesnenin iç kaynağını alır ve onu boş bırakır. noexcept yazmak önemlidir: std::vector büyürken elemanlarını yalnızca taşıma noexcept ise taşır, değilse güvenli olsun diye kopyalar.",
             "Перемещающий конструктор",
             "Сигнатура перемещающего конструктора — Buffer(Buffer&&): он забирает внутренний ресурс другого объекта и оставляет его пустым. Важно писать noexcept: при росте std::vector перемещает элементы, только если перемещение noexcept, иначе для надёжности копирует.",
             "struct Buffer {\n    std::vector<int> data;\n    Buffer(Buffer&& other) noexcept\n        : data(std::move(other.data)) {}  // other.data artık boş\n};"),
            ("Sıfır, Üç ve Beş Kuralı",
             "Bir sınıf yıkıcıya, kopya kurucuya veya kopya atamaya ihtiyaç duyuyorsa büyük olasılıkla beşine de ihtiyaç duyar: yıkıcı, kopya kurucu, kopya atama, taşıyıcı kurucu ve taşıyıcı atama (Beşler Kuralı). En iyisi Sıfır Kuralı'dır: kaynakları std::vector, std::string, std::unique_ptr gibi üyelere bırakırsan derleyicinin ürettiği beş fonksiyon zaten doğru olur.",
             "Правила нуля, трёх и пяти",
             "Если классу нужен деструктор, копирующий конструктор или копирующее присваивание, скорее всего, ему нужны все пять: деструктор, копирующие конструктор и присваивание, перемещающие конструктор и присваивание (правило пяти). Лучше всего правило нуля: доверь ресурсы членам вроде std::vector, std::string, std::unique_ptr — тогда пять функций, созданных компилятором, уже корректны.",
             "class Image {               // Sıfır Kuralı:\n    std::vector<unsigned char> pixels;\n    std::string name;      // kopya, taşıma ve yıkıcı otomatik\n};"),
            ("Sık yapılan hatalar",
             "Taşınmış nesneyi okumaya devam etmek (ona yalnızca yeni değer atayabilir veya onu yok edebilirsin). const bir nesneyi std::move etmek: const T&& taşıyıcı kurucuya uymaz, nesne sessizce kopyalanır. return std::move(yerel); yazmak: derleyicinin kopya atlamasını engeller; return yerel; yeterlidir.",
             "Частые ошибки",
             "Продолжать читать перемещённый объект (ему можно только присвоить новое значение или уничтожить его). Делать std::move константного объекта: const T&& не подходит перемещающему конструктору, и объект молча копируется. Писать return std::move(local); — это мешает компилятору убрать копию; достаточно return local;.",
             'std::string s = "pati";\nstd::string t = std::move(s);  // s geçerli ama boş olabilir\ns = "yeni";                    // ✓ yeniden atamak güvenli\nconst std::string c = "x";\nstd::string u = std::move(c);  // ✗ sessizce KOPYALAR'),
            ("Kendini kontrol et",
             "Şunları yapabiliyorsan bu bölüm tamam: lvalue ile rvalue'yu ayırt etmek, std::move'un yalnızca bir tür dönüşümü olduğunu açıklamak, noexcept bir taşıyıcı kurucu yazmak ve bir sınıf için Sıfır Kuralı'nın mı Beşler Kuralı'nın mı gerektiğine karar vermek.",
             "Проверь себя",
             "Глава пройдена, если ты можешь: отличить lvalue от rvalue, объяснить, что std::move — лишь приведение типа, написать noexcept-перемещающий конструктор и решить, нужно ли классу правило нуля или правило пяти.",
             ""),
        ],
        "quiz": _quiz("std::move tek başına ne yapar? (tür dönüşümü yapar / belleği kopyalar / nesneyi siler)",
                      "Что делает std::move сам по себе? (приведение типа / копирует память / удаляет объект)",
                      {"tr": "tür dönüşümü yapar", "ru": "приведение типа"}),
        "predict": ('std::string a = "kedi";\nstd::string b = std::move(a);\nstd::cout << b << " " << b.size();', "kedi 4"),
        "quiz2": _quiz("Taşıyıcı kurucunun parametre türü hangisidir? (T&& / const T& / T*)",
                       "Какой тип параметра у перемещающего конструктора? (T&& / const T& / T*)", "T&&"),
        "predict2": ("std::vector<int> v{1, 2, 3};\nstd::vector<int> w = std::move(v);\nv = {9};\nstd::cout << w.size() << v[0];", "39"),
        "fix": _code(
            "Kutu'nun taşıyıcı kurucusu veriyi taşımıyor, kopyalıyor. Düzelt: n oku; `b` taşındıktan sonra `b'nin boyutu a'nın boyutu kopya_sayısı` yazılmalı (ör. 3 için `3 0 0`).",
            "Перемещающий конструктор Kutu не перемещает данные, а копирует их. Исправь: прочитай n; после перемещения нужно вывести `размер_b размер_a число_копий` (например, для 3 — `3 0 0`).",
            "#include <iostream>\n#include <vector>\n#include <utility>\nstruct Kutu {\n    std::vector<int> veri;\n    static inline int kopya = 0;\n    explicit Kutu(int n) : veri(n, 1) {}\n    Kutu(const Kutu& o) : veri(o.veri) { ++kopya; }\n    Kutu(Kutu&& o) noexcept : veri(o.veri) {}\n};\nint main() {\n    int n; std::cin >> n;\n    Kutu a(n);\n    Kutu b(std::move(a));\n    std::cout << b.veri.size() << \" \" << a.veri.size() << \" \" << Kutu::kopya;\n}",
            [("3", "3 0 0"), ("5", "5 0 0"), ("0", "0 0 0")], "move_semantics", bug_type="ownership"),
        "warm": _code(
            "n ve ardından n kelime oku, bir std::vector<std::string> içinde sakla. Vector'ü std::move ile yeni bir vector'e taşı; `yeni_boyut eski_boyut` yazdır.",
            "Прочитай n и затем n слов, сохрани их в std::vector<std::string>. Перемести vector в новый через std::move и выведи `новый_размер старый_размер`.",
            "#include <iostream>\n#include <string>\n#include <vector>\n#include <utility>\nint main() {\n    int n; std::cin >> n;\n    std::vector<std::string> kelimeler(n);\n    for (auto& k : kelimeler) std::cin >> k;\n    // kelimeler'i yeni bir vector'e taşı ve boyutları yazdır\n    return 0;\n}",
            [("3 a b c", "3 0"), ("1 kedi", "1 0"), ("0", "0 0")], requires=["std::move"]),
        "practice": _code(
            "`Torba` yapısı bir std::vector<int> tutar. noexcept bir taşıyıcı kurucu yaz; her çağrıldığında statik `tasima` sayacını 1 artırsın. n sayı oku, `Torba a` oluştur, `b = std::move(a)` ve `c = std::move(b)` yap; `c'nin_toplamı a'nın_boyutu tasima` yazdır.",
            "Структура `Torba` хранит std::vector<int>. Напиши noexcept-перемещающий конструктор, который при каждом вызове увеличивает статический счётчик `tasima`. Прочитай n чисел, создай `Torba a`, сделай `b = std::move(a)` и `c = std::move(b)`; выведи `сумма_c размер_a tasima`.",
            "#include <iostream>\n#include <vector>\n#include <utility>\nstruct Torba {\n    std::vector<int> veri;\n    static inline int tasima = 0;\n    Torba() = default;\n    // noexcept taşıyıcı kurucuyu yaz\n};\nint main() {\n    int n; std::cin >> n;\n    Torba a;\n    a.veri.resize(n);\n    for (int& x : a.veri) std::cin >> x;\n    // a -> b -> c taşı, sonucu yazdır\n    return 0;\n}",
            [("3 1 2 3", "6 0 2"), ("4 5 5 5 5", "20 0 2"), ("0", "0 0 2")], "move_semantics"),
        "boss": _code(
            "Boss: `Envanter` ham bir `int*` dizisini yönetiyor ama kopyalama ve taşıma yanlış. Beşler Kuralı'nı uygula: yıkıcı `delete[]` yapsın, kopya kurucu derin kopyalasın, taşıyıcı kurucu kaynağı alıp kaynağı boşaltsın (boyut 0). main değişmeden `b'nin_toplamı c'nin_toplamı a'nın_boyutu` yazmalı.",
            "Босс: `Envanter` управляет сырым массивом `int*`, но копирование и перемещение неверны. Примени правило пяти: деструктор делает `delete[]`, копирующий конструктор копирует глубоко, перемещающий забирает ресурс и опустошает источник (размер 0). Без изменений main должен вывести `сумма_b сумма_c размер_a`.",
            "#include <iostream>\n#include <utility>\nclass Envanter {\n    int* veri = nullptr;\n    int boyut = 0;\npublic:\n    explicit Envanter(int n) : veri(new int[n]{}), boyut(n) {}\n    // yıkıcı, kopya kurucu ve taşıyıcı kurucuyu yaz (atamaları silebilirsin)\n    int& operator[](int i) { return veri[i]; }\n    int size() const { return boyut; }\n    long long sum() const { long long s = 0; for (int i = 0; i < boyut; ++i) s += veri[i]; return s; }\n};\nint main() {\n    int n; std::cin >> n;\n    Envanter a(n);\n    for (int i = 0; i < n; ++i) std::cin >> a[i];\n    Envanter b = a;\n    Envanter c = std::move(a);\n    if (b.size() > 0) b[0] += 100;\n    std::cout << b.sum() << \" \" << c.sum() << \" \" << a.size();\n}",
            [("3 1 2 3", "106 6 0"), ("2 -5 5", "100 0 0"), ("0", "0 0 0")], "rule_of_five"),
    },
    # ------------------------------------------------------------------ c22
    {
        "id": "c22", "prerequisites": ["c09", "c19"],
        "title": ("optional, variant ve string_view", "optional, variant и string_view"),
        "lesson": (
            "C++17 üç küçük ama güçlü tür getirdi. std::optional<T> 'belki bir değer' demektir: -1 gibi sihirli değerler yerine değerin yokluğunu açıkça gösterir. std::variant<A, B> aynı anda türlerden yalnızca birini tutan güvenli bir birleşimdir. std::string_view bir metne sahip olmadan ve onu kopyalamadan bakmanı sağlar.",
            "C++17 добавил три небольших, но мощных типа. std::optional<T> означает «значения может не быть»: вместо магических чисел вроде -1 отсутствие выражается явно. std::variant<A, B> — безопасное объединение, которое хранит ровно один из типов. std::string_view позволяет смотреть на текст, не владея им и не копируя его."),
        "example": '#include <iostream>\n#include <optional>\nstd::optional<int> bol(int a, int b) {\n    if (b == 0) return std::nullopt;\n    return a / b;\n}\nint main() {\n    std::cout << bol(8, 2).value_or(-1) << " " << bol(1, 0).value_or(-1);\n    return 0;\n}',
        "guide": [
            ("std::optional: değer olmayabilir",
             "Bir fonksiyon her zaman sonuç üretemiyorsa std::optional<T> döndür. Sonuç varsa return değer;, yoksa return std::nullopt; yazarsın. if (sonuc) ile kontrol eder, *sonuc ile okursun; value_or(varsayılan) değer yoksa varsayılanı verir.",
             "std::optional: значения может не быть",
             "Если функция не всегда может вернуть результат, верни std::optional<T>. При наличии результата пишешь return значение;, иначе — return std::nullopt;. Проверяешь через if (result), читаешь через *result; value_or(по_умолчанию) вернёт запасное значение, если результата нет.",
             "std::optional<int> bul(const std::vector<int>& v, int x) {\n    for (int i = 0; i < (int)v.size(); ++i)\n        if (v[i] == x) return i;\n    return std::nullopt;\n}\nauto r = bul({4, 7}, 7);\nif (r) std::cout << *r;                 // 1\nstd::cout << bul({4}, 9).value_or(-1);  // -1"),
            ("std::variant ve std::visit",
             "variant her an tam olarak bir alternatif tutar; index() hangisinin tutulduğunu söyler. std::get<T> yanlış türle çağrılırsa std::bad_variant_access fırlatır; emin değilsen std::holds_alternative<T> veya std::get_if kullan. std::visit tüm alternatifleri tek bir fonksiyonla işler.",
             "std::variant и std::visit",
             "variant в каждый момент хранит ровно одну альтернативу; index() говорит, какую. std::get<T> с неверным типом бросает std::bad_variant_access; если не уверен, используй std::holds_alternative<T> или std::get_if. std::visit обрабатывает все альтернативы одной функцией.",
             'std::variant<int, std::string> v = 42;\nv = std::string("pati");\nstd::cout << v.index();                 // 1\nstd::cout << std::get<std::string>(v);  // pati\nstd::visit([](const auto& x) { std::cout << x; }, v);'),
            ("std::string_view: kopyasız metin",
             "string_view yalnızca bir işaretçi ve bir uzunluktur; substr yeni metin kopyalamaz. Parametre olarak const std::string& yerine kullanırsan hem std::string hem de \"metin\" literali kopyasız geçer. Dikkat: baktığı metin yok olursa string_view sarkık (dangling) kalır.",
             "std::string_view: текст без копий",
             "string_view — это просто указатель и длина; substr не копирует текст. Если использовать его как параметр вместо const std::string&, без копии передаются и std::string, и литерал \"текст\". Осторожно: если исходный текст уничтожен, string_view становится висячим (dangling).",
             'int sesliSay(std::string_view s) {\n    int n = 0;\n    for (char c : s) n += (c == \'a\' || c == \'e\' || c == \'i\' || c == \'o\' || c == \'u\');\n    return n;\n}\nstd::cout << sesliSay("miyav");               // 2\nstd::string_view ilk = std::string_view("pati kedi").substr(0, 4); // "pati"'),
            ("Sık yapılan hatalar",
             "Değer yokken *opt okumak tanımsız davranıştır; opt.value() ise std::bad_optional_access fırlatır. Geçici bir std::string'den string_view döndürmek sarkık bir görünüm üretir. variant'tan yanlış türle std::get yapmak istisna fırlatır.",
             "Частые ошибки",
             "Чтение *opt при отсутствии значения — неопределённое поведение; opt.value() бросает std::bad_optional_access. Возврат string_view на временную std::string даёт висячее представление. std::get с неверным типом у variant бросает исключение.",
             'std::optional<int> o;\n// std::cout << *o;          // ✗ tanımsız davranış\nstd::cout << o.value_or(0);   // ✓\nstd::string_view kotu() { return std::string("gecici"); } // ✗ sarkık'),
            ("Kendini kontrol et",
             "Şunları yapabiliyorsan bu bölüm tamam: sonuç üretemeyebilen bir fonksiyondan std::optional döndürmek, variant'ın hangi türü tuttuğunu güvenle öğrenmek ve metni kopyalamadan string_view ile işlemek.",
             "Проверь себя",
             "Глава пройдена, если ты можешь: вернуть std::optional из функции, которая может не дать результата, безопасно узнать, какой тип хранит variant, и обработать текст через string_view без копирования.",
             ""),
        ],
        "quiz": _quiz("Değerin olmayabileceğini açıkça gösteren C++17 türü hangisidir? (optional / variant / any)",
                      "Какой тип C++17 явно показывает, что значения может не быть? (optional / variant / any)", "optional"),
        "predict": ("std::optional<int> o;\nstd::cout << o.has_value() << o.value_or(7);", "07"),
        "quiz2": _quiz("std::variant<int, std::string> v = 5; için v.index() kaçtır? (0 / 1 / 2)",
                       "Чему равен v.index() для std::variant<int, std::string> v = 5;? (0 / 1 / 2)", "0"),
        "predict2": ('std::string_view s = "kedi pati";\nstd::cout << s.substr(5) << s.size();', "pati9"),
        "fix": _code(
            "Program yaşı okuyup bir fazlasını yazmalı, ama geçersiz girdide boş optional'ı okuyor. Düzelt: geçerli girdide `yaş + 1`, geçersizde `yok` yazdır.",
            "Программа должна прочитать возраст и вывести его на 1 больше, но при неверном вводе читает пустой optional. Исправь: при верном вводе выведи `возраст + 1`, при неверном — `yok`.",
            "#include <iostream>\n#include <optional>\n#include <string>\nstd::optional<int> yasOku(const std::string& s) {\n    if (s.empty() || s.size() > 3 || s.find_first_not_of(\"0123456789\") != std::string::npos) return std::nullopt;\n    return std::stoi(s);\n}\nint main() {\n    std::string s; std::cin >> s;\n    std::optional<int> yas = yasOku(s);\n    std::cout << *yas + 1;\n}",
            [("7", "8"), ("abc", "yok"), ("0", "1"), ("12a", "yok")], "vocabulary_types", bug_type="logic"),
        "warm": _code(
            "Bir kelime oku. `std::optional<char> ilkSesli(std::string_view s)` yaz: ilk sesli harfi (a, e, i, o, u) döndürsün, yoksa std::nullopt. Harfi ya da `-` yazdır.",
            "Прочитай слово. Напиши `std::optional<char> ilkSesli(std::string_view s)`: пусть возвращает первую гласную (a, e, i, o, u) или std::nullopt. Выведи букву или `-`.",
            "#include <iostream>\n#include <optional>\n#include <string>\n#include <string_view>\n// ilkSesli fonksiyonunu yaz\nint main() {\n    std::string kelime; std::cin >> kelime;\n    // sonucu yazdır\n    return 0;\n}",
            [("kedi", "e"), ("xyz", "-"), ("ayna", "a")], requires=["std::optional"]),
        "practice": _code(
            "n ve ardından n belirteç oku; her biri ya tam sayı (başında - olabilir) ya da kelimedir. Hepsini `std::vector<std::variant<int, std::string>>` içinde sakla. Tam sayıların toplamını ve kelime sayısını `toplam adet` biçiminde yazdır.",
            "Прочитай n и затем n токенов; каждый — целое число (возможно, с минусом) или слово. Сохрани всё в `std::vector<std::variant<int, std::string>>`. Выведи сумму чисел и количество слов в виде `сумма количество`.",
            "#include <iostream>\n#include <string>\n#include <variant>\n#include <vector>\nint main() {\n    int n; std::cin >> n;\n    std::vector<std::variant<int, std::string>> ogeler;\n    // belirteçleri oku, türüne göre sakla, sonra say\n    return 0;\n}",
            [("4 3 kedi 5 pati", "8 2"), ("2 -4 mavi", "-4 1"), ("0", "0 0")], "vocabulary_types"),
        "boss": _code(
            "Boss: ilk satırda `anahtar=değer;anahtar=değer` biçiminde bir ayar metni, sonra q ve q anahtar gelir. `std::optional<std::string_view> deger(std::string_view metin, std::string_view anahtar)` yaz; metni kopyalamadan tam eşleşen anahtarın değerini bulsun. Her anahtar için değeri ya da `yok` yazdır, her biri ayrı satırda.",
            "Босс: в первой строке — настройки вида `ключ=значение;ключ=значение`, затем q и q ключей. Напиши `std::optional<std::string_view> deger(std::string_view metin, std::string_view anahtar)`, который без копирования находит значение точно совпадающего ключа. Для каждого ключа выведи значение или `yok`, каждое с новой строки.",
            "#include <iostream>\n#include <optional>\n#include <string>\n#include <string_view>\n// deger fonksiyonunu yaz\nint main() {\n    std::string ayar; std::getline(std::cin, ayar);\n    int q; std::cin >> q;\n    // her anahtarı oku ve sonucu yazdır\n    return 0;\n}",
            [("ad=Luna;yas=3;renk=gri\n3\nyas\nrenk\nboy", "3\ngri\nyok"), ("renkad=x;ad=Luna\n1\nad", "Luna"), ("kedi=pati;pati=kedi\n2\npati\nkedi", "kedi\npati")], "string_view_parse"),
    },
    # ------------------------------------------------------------------ c23
    {
        "id": "c23", "prerequisites": ["c19", "c13"],
        "title": ("Concepts ve Ranges (C++20)", "Концепты и ranges (C++20)"),
        "lesson": (
            "C++20 kavramları (concepts) şablon parametrelerine okunabilir şartlar koyar: template<std::integral T> yalnızca tam sayı türlerini kabul eder ve hata mesajı sayfalarca değil tek satır olur. Ranges kütüphanesi algoritmaları doğrudan kapsayıcıya uygular (std::ranges::sort(v)) ve görünümleri (views) | ile zincirleyerek tembel, kopyasız veri hatları kurar.",
            "Концепты C++20 задают читаемые требования к параметрам шаблона: template<std::integral T> принимает только целые типы, а ошибка занимает одну строку, а не страницы. Библиотека ranges применяет алгоритмы прямо к контейнеру (std::ranges::sort(v)) и соединяет представления (views) через |, создавая ленивые конвейеры без копирования."),
        "example": '#include <iostream>\n#include <concepts>\ntemplate <std::integral T>\nT kare(T x) { return x * x; }\nint main() {\n    std::cout << kare(7);\n    return 0;\n}',
        "guide": [
            ("Hazır concept'lerle kısıtlama",
             "<concepts> başlığı std::integral, std::floating_point, std::same_as, std::convertible_to gibi hazır kavramlar sunar. template<std::integral T> yazınca kare(2.5) çağrısı derlenmez ve derleyici hangi şartın sağlanmadığını açıkça söyler. Kısa yazım da vardır: void yaz(std::integral auto x).",
             "Ограничение готовыми концептами",
             "Заголовок <concepts> даёт готовые концепты: std::integral, std::floating_point, std::same_as, std::convertible_to и другие. С template<std::integral T> вызов kare(2.5) не скомпилируется, и компилятор прямо скажет, какое требование нарушено. Есть и краткая запись: void yaz(std::integral auto x).",
             "#include <concepts>\ntemplate <std::integral T>\nT kare(T x) { return x * x; }\nkare(7);       // ✓ 49\n// kare(2.5);  // ✗ double integral değil: net hata"),
            ("Kendi concept'in ve requires",
             "concept, derleme zamanında doğru ya da yanlış olan adlandırılmış bir şarttır. requires ifadesi, bir türle hangi ifadelerin derlenmesi gerektiğini listeler; { t.ses() } -> std::convertible_to<std::string> 'ses() çağrılabilmeli ve sonucu string'e dönüşebilmeli' demektir.",
             "Свой концепт и requires",
             "concept — именованное условие, истинное или ложное на этапе компиляции. Выражение requires перечисляет, какие выражения должны компилироваться для типа; { t.ses() } -> std::convertible_to<std::string> значит «ses() должен вызываться, а результат — приводиться к string».",
             'template <typename T>\nconcept Sesli = requires(const T& t) {\n    { t.ses() } -> std::convertible_to<std::string>;\n};\nstruct Kedi { std::string ses() const { return "miyav"; } };\ntemplate <Sesli T> void konus(const T& t) { std::cout << t.ses(); }'),
            ("Ranges ve görünümler",
             "std::ranges::sort(v) begin/end yazmadan sıralar. Görünümler tembeldir: elemanlar ancak döngüde istendiğinde hesaplanır ve yeni bir vector oluşturulmaz. filter, transform, take, reverse ve iota en sık kullanılan görünümlerdir; | ile zincirlenirler.",
             "Ranges и представления",
             "std::ranges::sort(v) сортирует без begin/end. Представления ленивы: элементы вычисляются только при запросе в цикле, новый vector не создаётся. Чаще всего используются filter, transform, take, reverse и iota; их соединяют через |.",
             "std::vector<int> v{5, 2, 8, 1, 6};\nstd::ranges::sort(v);                      // 1 2 5 6 8\nauto ciftKare = v | std::views::filter([](int x) { return x % 2 == 0; })\n                  | std::views::transform([](int x) { return x * x; });\nfor (int x : ciftKare) std::cout << x << \" \";  // 4 36 64"),
            ("Sık yapılan hatalar",
             "Görünümün baktığı kapsayıcı yok olursa görünüm sarkık kalır: geçici bir vector'den görünüm döndürme. Görünüm üzerinde döngü sürerken kapsayıcıya eleman eklemek tanımsız davranıştır. Yanlış concept seçmek (std::integral yerine std::floating_point) çağrıyı derleme hatasına çevirir; bu iyidir: hata çalışırken değil derlerken yakalanır.",
             "Частые ошибки",
             "Если контейнер, на который смотрит представление, уничтожен, представление становится висячим: не возвращай представление на временный vector. Добавлять элементы в контейнер во время обхода представления — неопределённое поведение. Неверный концепт (std::floating_point вместо std::integral) превращает вызов в ошибку компиляции — и это хорошо: ошибка ловится при сборке, а не при запуске.",
             "auto kotu() {\n    std::vector<int> v{1, 2, 3};\n    return v | std::views::take(2);   // ✗ v yok olur, görünüm sarkar\n}"),
            ("Kendini kontrol et",
             "Şunları yapabiliyorsan bu bölüm tamam: bir şablonu hazır bir concept ile kısıtlamak, requires ile kendi concept'ini yazmak, std::ranges::sort kullanmak ve filter/transform görünümlerini | ile zincirlemek.",
             "Проверь себя",
             "Глава пройдена, если ты можешь: ограничить шаблон готовым концептом, написать свой концепт через requires, использовать std::ranges::sort и соединить представления filter/transform через |.",
             ""),
        ],
        "quiz": _quiz("template<std::integral T> T kare(T x) için kare(2.5) çağrısı ne olur? (derleme hatası / 6.25 döner / 6 döner)",
                      "Что будет с вызовом kare(2.5) для template<std::integral T> T kare(T x)? (ошибка компиляции / вернёт 6.25 / вернёт 6)",
                      {"tr": "derleme hatası", "ru": "ошибка компиляции"}),
        "predict": ("std::vector<int> v{1, 2, 3, 4, 5, 6};\nfor (int x : v | std::views::filter([](int x) { return x % 3 == 0; })) std::cout << x;", "36"),
        "quiz2": _quiz("Bir türün hangi ifadeleri desteklemesi gerektiğini listeleyen C++20 ifadesi hangisidir? (requires / typename / decltype)",
                       "Какое выражение C++20 перечисляет, какие операции должен поддерживать тип? (requires / typename / decltype)", "requires"),
        "predict2": ("for (int x : std::views::iota(1, 6) | std::views::reverse | std::views::take(3)) std::cout << x;", "543"),
        "fix": _code(
            "`topla` şablonu yanlış concept ile kısıtlanmış, bu yüzden tam sayılarla derlenmiyor. Concept'i düzelt; n sayı oku ve toplamı yazdır.",
            "Шаблон `topla` ограничен неверным концептом, поэтому не компилируется с целыми числами. Исправь концепт; прочитай n чисел и выведи сумму.",
            "#include <iostream>\n#include <concepts>\n#include <vector>\ntemplate <std::floating_point T>\nT topla(const std::vector<T>& v) {\n    T s{};\n    for (T x : v) s += x;\n    return s;\n}\nint main() {\n    int n; std::cin >> n;\n    std::vector<int> v(n);\n    for (int& x : v) std::cin >> x;\n    std::cout << topla(v);\n}",
            [("3 1 2 3", "6"), ("2 -5 5", "0"), ("0", "0")], "constrained_template", bug_type="constraint"),
        "warm": _code(
            "n sayı oku, std::ranges::sort ile sırala ve aralarında boşlukla yazdır.",
            "Прочитай n чисел, отсортируй через std::ranges::sort и выведи через пробел.",
            "#include <algorithm>\n#include <iostream>\n#include <vector>\nint main() {\n    int n; std::cin >> n;\n    std::vector<int> v(n);\n    for (int& x : v) std::cin >> x;\n    // std::ranges::sort ile sırala ve yazdır\n    return 0;\n}",
            [("4 3 1 4 2", "1 2 3 4"), ("1 7", "7"), ("3 -1 -3 -2", "-3 -2 -1")], requires=["std::ranges::sort"]),
        "practice": _code(
            "n sayı oku. std::views::filter ve std::views::transform zinciriyle tek sayıların karelerini sırayla, aralarında boşlukla yazdır.",
            "Прочитай n чисел. Цепочкой std::views::filter и std::views::transform выведи по порядку квадраты нечётных чисел через пробел.",
            "#include <iostream>\n#include <ranges>\n#include <vector>\nint main() {\n    int n; std::cin >> n;\n    std::vector<int> v(n);\n    for (int& x : v) std::cin >> x;\n    // filter | transform zincirini kur ve yazdır\n    return 0;\n}",
            [("5 1 2 3 4 5", "1 9 25"), ("3 2 4 6", ""), ("2 -3 7", "9 49")], "ranges_pipeline"),
        "boss": _code(
            "Boss: `alan()` metodu long long'a dönüşebilen türler için `Alanli` concept'ini requires ile tanımla ve `template <Alanli T> long long toplamAlan(const std::vector<T>& v)` yaz. main kareleri ve dikdörtgenleri okuyup iki satırda toplam alanları yazdırıyor.",
            "Босс: определи через requires концепт `Alanli` для типов, у которых `alan()` приводится к long long, и напиши `template <Alanli T> long long toplamAlan(const std::vector<T>& v)`. main читает квадраты и прямоугольники и выводит суммарные площади в двух строках.",
            "#include <concepts>\n#include <iostream>\n#include <vector>\nstruct Kare { long long a; long long alan() const { return a * a; } };\nstruct Dikdortgen { long long a, b; long long alan() const { return a * b; } };\n// Alanli concept'ini ve toplamAlan şablonunu yaz\nint main() {\n    int n; std::cin >> n;\n    std::vector<Kare> kareler(n);\n    for (auto& k : kareler) std::cin >> k.a;\n    int m; std::cin >> m;\n    std::vector<Dikdortgen> dikler(m);\n    for (auto& d : dikler) std::cin >> d.a >> d.b;\n    std::cout << toplamAlan(kareler) << \"\\n\" << toplamAlan(dikler);\n}",
            [("2 3 4 1 2 5", "25\n10"), ("0 2 1 1 2 2", "0\n5"), ("1 10 0", "100\n0")], "custom_concept"),
    },
    # ------------------------------------------------------------------ c24
    {
        "id": "c24", "prerequisites": ["c21", "c19"],
        "title": ("Eşzamanlılık: thread, mutex, atomic", "Многопоточность: thread, mutex, atomic"),
        "lesson": (
            "std::thread bir fonksiyonu ayrı bir iş parçacığında çalıştırır; join() o iş bitene kadar bekler. İki thread aynı veriyi kilitsiz değiştirirse veri yarışı (data race) olur ve sonuç tanımsızdır. std::mutex ile std::lock_guard veya std::scoped_lock kritik bölgeyi korur; tek bir sayaç için std::atomic daha hafif bir çözümdür. C++20'deki std::jthread yok edilirken kendiliğinden join eder.",
            "std::thread запускает функцию в отдельном потоке; join() ждёт её завершения. Если два потока без синхронизации меняют одни данные, возникает гонка данных (data race), и поведение не определено. std::mutex вместе с std::lock_guard или std::scoped_lock защищает критическую секцию; для одного счётчика легче std::atomic. std::jthread из C++20 сам вызывает join при уничтожении."),
        "example": '#include <iostream>\n#include <thread>\nint main() {\n    int sonuc = 0;\n    std::thread t([&] { sonuc = 6 * 7; });\n    t.join();              // bitmesini bekle\n    std::cout << sonuc;    // 42\n    return 0;\n}',
        "guide": [
            ("std::thread ve join",
             "std::thread t(fonksiyon, argümanlar...) yeni bir iş parçacığı başlatır ve hemen döner. join() o iş bitene kadar bekler. Bir std::thread nesnesi join() veya detach() çağrılmadan yok edilirse program std::terminate ile sonlanır.",
             "std::thread и join",
             "std::thread t(функция, аргументы...) запускает новый поток и сразу возвращается. join() ждёт, пока поток закончит работу. Если объект std::thread уничтожается без вызова join() или detach(), программа завершается через std::terminate.",
             "#include <thread>\nvoid selam(int id) { /* ... */ }\nstd::thread t(selam, 1);   // yeni iş parçacığı başlar\nt.join();                  // bitmesini bekle\n// join/detach unutulursa: std::terminate!"),
            ("Veri yarışı ve mutex",
             "++sayac aslında oku, artır, yaz adımlarından oluşur; iki thread bu adımları iç içe geçirirse artışlar kaybolur. std::lock_guard kurulurken mutex'i kilitler, kapsamdan çıkarken açar (RAII); böylece istisna olsa bile kilit açık kalmaz.",
             "Гонка данных и mutex",
             "++counter на самом деле состоит из шагов «прочитать, увеличить, записать»; если два потока перемешают эти шаги, увеличения теряются. std::lock_guard захватывает mutex при создании и освобождает при выходе из области видимости (RAII), поэтому блокировка снимается даже при исключении.",
             "int sayac = 0;\nstd::mutex m;\nauto is = [&] {\n    for (int i = 0; i < 1000; ++i) {\n        std::lock_guard<std::mutex> kilit(m);\n        ++sayac;\n    }\n};\nstd::thread a(is), b(is);\na.join(); b.join();\nstd::cout << sayac;   // her zaman 2000"),
            ("std::atomic ve std::jthread",
             "std::atomic<int> üzerindeki ++ tek ve bölünmez bir işlemdir; tek bir sayaç için mutex'ten hafiftir. std::jthread kapsam sonunda kendiliğinden join eder, böylece join'i unutma riski kalmaz. Thread'lerin çalışma ve çıktı sırası garanti değildir: sonucu join'den sonra yazdır.",
             "std::atomic и std::jthread",
             "++ для std::atomic<int> — одна неделимая операция; для одного счётчика это легче mutex. std::jthread сам вызывает join в конце области видимости, так что забыть join невозможно. Порядок работы и вывода потоков не гарантирован: печатай результат после join.",
             "std::atomic<int> sayac{0};\n{\n    std::jthread a([&] { for (int i = 0; i < 1000; ++i) ++sayac; });\n    std::jthread b([&] { for (int i = 0; i < 1000; ++i) ++sayac; });\n}   // jthread'ler burada kendiliğinden join eder\nstd::cout << sayac.load();   // 2000"),
            ("Sık yapılan hatalar",
             "join() çağırmadan thread nesnesini yok etmek std::terminate'e yol açar. Thread'e referans geçirmek için std::ref gerekir. Kilidi elle lock()/unlock() ile yönetmek istisna olunca kilidi kapalı bırakır; lock_guard kullan. İki mutex'i farklı sırayla kilitlemek kilitlenmeye (deadlock) yol açar; std::scoped_lock(m1, m2) ikisini güvenle alır.",
             "Частые ошибки",
             "Уничтожение потока без join() приводит к std::terminate. Чтобы передать потоку ссылку, нужен std::ref. Ручные lock()/unlock() оставляют mutex захваченным при исключении — используй lock_guard. Захват двух mutex в разном порядке ведёт к взаимной блокировке (deadlock); std::scoped_lock(m1, m2) безопасно берёт оба.",
             "void artir(int& x) { ++x; }\nint deger = 0;\n// std::thread t(artir, deger);         // ✗ derlenmez\nstd::thread t(artir, std::ref(deger));  // ✓\nt.join();"),
            ("Kendini kontrol et",
             "Şunları yapabiliyorsan bu bölüm tamam: thread başlatıp join etmek, veri yarışının neden sonucu bozduğunu açıklamak, ortak veriyi lock_guard veya atomic ile korumak ve işi thread'ler arasında, her thread kendi sonucunu yazacak şekilde bölmek.",
             "Проверь себя",
             "Глава пройдена, если ты можешь: запустить поток и вызвать join, объяснить, почему гонка данных портит результат, защитить общие данные через lock_guard или atomic и разделить работу между потоками так, чтобы каждый писал свой результат.",
             ""),
        ],
        "quiz": _quiz("Bir std::thread nesnesi join() veya detach() çağrılmadan yok edilirse ne olur? (std::terminate çağrılır / thread kendiliğinden biter / hiçbir şey olmaz)",
                      "Что будет, если объект std::thread уничтожить без join() или detach()? (вызывается std::terminate / поток сам завершится / ничего не произойдёт)",
                      {"tr": "std::terminate çağrılır", "ru": "вызывается std::terminate"}),
        "predict": ("std::atomic<int> a{0};\nstd::thread t([&] { a += 5; });\nt.join();\na += 2;\nstd::cout << a.load();", "7"),
        "quiz2": _quiz("Tek bir tam sayı sayacını kilit kullanmadan güvenle artırmak için en hafif araç hangisidir? (std::atomic / std::vector / std::string)",
                       "Какой самый лёгкий инструмент для безопасного увеличения одного счётчика без блокировок? (std::atomic / std::vector / std::string)", "std::atomic"),
        "predict2": ("int x = 0;\nstd::mutex m;\nstd::vector<std::thread> ts;\nfor (int i = 1; i <= 3; ++i)\n    ts.emplace_back([&, i] { std::lock_guard<std::mutex> g(m); x += i; });\nfor (auto& t : ts) t.join();\nstd::cout << x;", "6"),
        "fix": _code(
            "İki thread 1..n aralığının tek ve çift sayılarını ayrı ayrı topluyor, ama program çöküyor. Hatayı bul ve düzelt; toplamı yazdır.",
            "Два потока отдельно суммируют нечётные и чётные числа из 1..n, но программа падает. Найди и исправь ошибку; выведи сумму.",
            "#include <iostream>\n#include <thread>\n#include <vector>\nint main() {\n    int n; std::cin >> n;\n    std::vector<long long> parca(2, 0);\n    std::thread a([&] { for (int i = 1; i <= n; i += 2) parca[0] += i; });\n    std::thread b([&] { for (int i = 2; i <= n; i += 2) parca[1] += i; });\n    a.join();\n    std::cout << parca[0] + parca[1];\n}",
            [("10", "55"), ("1", "1"), ("0", "0")], "thread_join", bug_type="lifetime"),
        "warm": _code(
            "n oku. Bir std::thread başlat; 1'den n'e kadar toplamı std::ref ile verdiğin bir değişkene yazsın. join et ve toplamı yazdır.",
            "Прочитай n. Запусти std::thread, который запишет сумму от 1 до n в переменную, переданную через std::ref. Вызови join и выведи сумму.",
            "#include <functional>\n#include <iostream>\n#include <thread>\nvoid topla(int n, long long& sonuc) {\n    // 1..n toplamını sonuc'a yaz\n}\nint main() {\n    int n; std::cin >> n;\n    long long sonuc = 0;\n    // thread başlat, join et, yazdır\n    return 0;\n}",
            [("10", "55"), ("0", "0"), ("100", "5050")], requires=["std::thread", "join"]),
        "practice": _code(
            "n ve k (1-4) oku. k thread başlat; her biri ortak sayacı n kez 1 artırsın. Sayacı std::mutex + std::lock_guard veya std::atomic ile koru; hepsini join et ve sayacı yazdır.",
            "Прочитай n и k (1–4). Запусти k потоков; каждый увеличивает общий счётчик на 1 n раз. Защити счётчик через std::mutex + std::lock_guard или std::atomic; дождись всех и выведи счётчик.",
            "#include <iostream>\n#include <mutex>\n#include <thread>\n#include <vector>\nint main() {\n    int n, k; std::cin >> n >> k;\n    // k thread başlat, ortak sayacı koru, join et ve yazdır\n    return 0;\n}",
            [("1000 4", "4000"), ("0 3", "0"), ("250 2", "500")], "shared_counter"),
        "boss": _code(
            "Boss: n, ardından n sayı, en son k (1-4) oku. Diziyi k parçaya böl: i. parça [i*n/k, (i+1)*n/k) indekslerini kapsar. Her parçayı ayrı bir thread kendi `std::vector<long long>` hücresine toplasın (ortak yazma yok). Hepsini join et; ilk satıra toplamı, ikinci satıra en büyük parça toplamını yazdır.",
            "Босс: прочитай n, затем n чисел и в конце k (1–4). Раздели массив на k частей: часть i охватывает индексы [i*n/k, (i+1)*n/k). Каждую часть суммирует отдельный поток в свою ячейку `std::vector<long long>` (без общих записей). Дождись всех; в первой строке выведи общую сумму, во второй — наибольшую сумму части.",
            "#include <algorithm>\n#include <iostream>\n#include <thread>\n#include <vector>\nint main() {\n    int n; std::cin >> n;\n    std::vector<long long> v(n);\n    for (auto& x : v) std::cin >> x;\n    int k; std::cin >> k;\n    // k thread ile parçaları topla, join et, sonuçları yazdır\n    return 0;\n}",
            [("6 1 2 3 4 5 6 2", "21\n15"), ("5 5 5 5 5 5 3", "25\n10"), ("1 7 1", "7\n7"), ("0 2", "0\n0")], "thread_join"),
    },
]

HINTS_QUIZ = {"tr": ["Ders notlarındaki ilk bölümü yeniden oku.", "Seçeneklerden birine tıklayabilirsin; önce kesin yanlış olanları ele.", "Kodun derleme zamanında mı, çalışırken mi davrandığını düşün."],
              "ru": ["Перечитай первый раздел урока.", "Можно нажать на вариант; сначала отбрось заведомо неверные.", "Подумай, что происходит при компиляции, а что — при запуске."]}
HINTS_PREDICT = {"tr": ["Kodu satır satır izle ve her değişkenin değerini not al.", "Yalnızca ekrana yazılanı gir; araya boşluk ekleme.", "Thread'li kodda sonuç join'den sonra yazılır."],
                 "ru": ["Пройди код построчно, записывая значения переменных.", "Введи только то, что выводится, без лишних пробелов.", "В коде с потоками результат печатается после join."]}


def _hints_for(spec):
    rule = spec.get("rule")
    third_tr = RULES[rule]["tr"] + "." if rule else "Kodunda şunlar olmalı: " + ", ".join(spec["requires"]) + "."
    third_ru = RULES[rule]["ru"] + "." if rule else "В коде должны быть: " + ", ".join(spec["requires"]) + "."
    return {"tr": ["Ders notlarındaki kod örneği bu görevin iskeletine çok benziyor.", "Önce girdiyi oku, sonra hesapla, en son yazdır; her test girdisini ayrı düşün.", third_tr],
            "ru": ["Пример кода из урока очень похож на каркас задания.", "Сначала прочитай ввод, затем посчитай, в конце выведи; продумай каждый тестовый ввод.", third_ru]}


def _mission(prefix, suffix, kind, slot, spec):
    task = {"id": f"{prefix}-{suffix}", "kind": kind, "xp": XP[slot],
            "title": {"tr": TITLES[slot][0], "ru": TITLES[slot][1]},
            "prompt": {"tr": spec["tr"], "ru": spec["ru"]}, "starter": spec["starter"],
            "tests": spec["tests"], "expected": spec["tests"][0]["expected"], "input": spec["tests"][0]["input"],
            "answer": "", "hints": _hints_for(spec)}
    if spec["rule"]:
        task["concept_rule"] = spec["rule"]
        task["concept_criteria"] = RULES[spec["rule"]]
        task["requires"] = [RULES[spec["rule"]]["tr"]]
    else:
        task["requires"] = spec["requires"]
    if spec["bug_type"]:
        task["bug_type"] = spec["bug_type"]
    return task


def _question(prefix, suffix, slot, spec):
    return {"id": f"{prefix}-{suffix}", "kind": "quiz", "xp": XP[slot], "title": {"tr": TITLES[slot][0], "ru": TITLES[slot][1]},
            "prompt": {"tr": spec["tr"], "ru": spec["ru"]}, "starter": {"tr": "Doğru yanıtı seç veya yaz.", "ru": "Выбери или напиши правильный ответ."},
            "expected": "", "answer": spec["answer"], "tests": [_case("", "")], "hints": HINTS_QUIZ}


def _prediction(prefix, suffix, slot, pair):
    code, output = pair
    return {"id": f"{prefix}-{suffix}", "kind": "predict", "xp": XP[slot], "title": {"tr": TITLES[slot][0], "ru": TITLES[slot][1]},
            "prompt": {"tr": f"Aşağıdaki kodun konsol çıktısını yaz. Yalnızca çıktıyı gir:\n{code}", "ru": f"Напиши вывод этого кода. Введи только результат:\n{code}"},
            "starter": output, "expected": output, "answer": output, "tests": [_case("", output)], "hints": HINTS_PREDICT}


def predict_program(snippet):
    """A full program around a prediction snippet (used by tests to verify the answer)."""
    return PREDICT_HEADERS + "int main() {\n" + snippet + "\nreturn 0;\n}\n"


def modern_chapters(first_number):
    chapters = []
    for offset, data in enumerate(CHAPTERS):
        p = data["id"]
        tasks = [
            _question(p, "01", "quiz", data["quiz"]),
            _prediction(p, "02", "predict", data["predict"]),
            _question(p, "q2", "quiz2", data["quiz2"]),
            _prediction(p, "p2", "predict2", data["predict2"]),
            _mission(p, "03", "fix", "fix", data["fix"]),
            _mission(p, "w1", "code", "warm", data["warm"]),
            _mission(p, "04", "code", "practice", data["practice"]),
            _mission(p, "boss", "boss", "boss", data["boss"]),
        ]
        guide = {lang: [[s[0], s[1], s[4]] if lang == "tr" else [s[2], s[3], s[4]] for s in data["guide"]] for lang in ("tr", "ru")}
        chapters.append({"id": p, "number": first_number + offset, "prerequisites": list(data["prerequisites"]),
                         "title": {"tr": data["title"][0], "ru": data["title"][1]},
                         "lesson": {"tr": data["lesson"][0], "ru": data["lesson"][1]},
                         "guide": guide, "example": data["example"], "tasks": tasks})
    return chapters
