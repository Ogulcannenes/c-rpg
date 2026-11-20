"""Bilingual, offline-first C++ curriculum. Every mission is checked locally."""
from lesson_content import GUIDES
from mission_contracts import apply_mission_contracts
from lesson_extra import extra_guide, extra_tasks

def task(id_, kind, xp, title_tr, title_ru, prompt_tr, prompt_ru, starter, expected, answer=""):
    prompt = prompt_tr if isinstance(prompt_tr, dict) else {"tr": prompt_tr, "ru": prompt_ru}
    return {"id": id_, "kind": kind, "xp": xp, "title": {"tr": title_tr, "ru": title_ru}, "prompt": prompt, "starter": starter, "expected": expected, "answer": answer, "tests": [{"input": "", "expected": expected}]}


topics = [
("İlk Programın", "Первая программа", "C++ programının iskeletini, main fonksiyonunu ve cout ile çıktı vermeyi öğren.", "Изучи каркас программы C++, функцию main и вывод с помощью cout.", "#include <iostream>\nint main() {\n    // buraya yaz\n    return 0;\n}", 'std::cout << "Merhaba, C++!";'),
("Değişkenler ve Türler", "Переменные и типы", "int, double, char, bool ve string ile verileri doğru türde sakla.", "Храни данные в правильном типе: int, double, char, bool и string.", "#include <iostream>\n#include <string>\nint main() {\n    // değişkenlerini tanımla\n    return 0;\n}", 'std::cout << "Mırmır 7";'),
('Girdi ve Çıktı', 'Ввод и вывод', 'cin ile kullanıcı girdisi al, cout ile sonucu göster.', 'Получай ввод через cin и показывай результат через cout.', '#include <iostream>\nint main() {\n    int n;\n    std::cin >> n;\n    // n değerini göster\n    return 0;\n}', 'std::cout << n * 2;'),
("Operatörler", "Операторы", "Aritmetik, karşılaştırma ve mantıksal operatörleri kullan.", "Используй арифметические, сравнительные и логические операторы.", "#include <iostream>\nint main() {\n    // hesapla\n    return 0;\n}", 'std::cout << (8 + 4) * 2;'),
("Koşullar", "Условия", "if, else if ve else ile programa karar vermeyi öğret.", "Научи программу принимать решения с помощью if, else if и else.", "#include <iostream>\nint main() {\n    int puan = 72;\n    // 50 ve üstüyse Gecti yaz\n    return 0;\n}", 'if (puan >= 50) std::cout << "Gecti"; else std::cout << "Kaldi";'),
("Döngüler", "Циклы", "for ve while döngüleriyle tekrarlanan işleri otomatikleştir.", "Автоматизируй повторяющиеся действия с помощью for и while.", "#include <iostream>\nint main() {\n    // 1'den 5'e kadar yazdır\n    return 0;\n}", 'for (int i = 1; i <= 5; ++i) std::cout << i << " ";'),
("Fonksiyonlar", "Функции", "Tekrar kullanılabilir fonksiyonlar yaz, parametre ve dönüş değerlerini öğren.", "Создавай функции, изучай параметры и возвращаемые значения.", "#include <iostream>\n// fonksiyonunu yaz\nint main() {\n    std::cout << ikiKat(6);\n    return 0;\n}", 'int ikiKat(int x) { return x * 2; }'),
("Diziler ve vector", "Массивы и vector", "Birden fazla değeri diziler ve esnek vector koleksiyonlarında tut.", "Храни несколько значений в массивах и гибких коллекциях vector.", "#include <iostream>\n#include <vector>\nint main() {\n    std::vector<int> sayilar{3, 5, 8};\n    // elemanları yazdır\n    return 0;\n}", 'for (int n : sayilar) std::cout << n << " ";'),
('Metinler', 'Строки', 'std::string ile metinleri birleştir, uzunluklarını ve karakterlerini incele.', 'Работай с текстом через std::string: объединяй строки и изучай их длину.', '#include <iostream>\n#include <string>\nint main() {\n    std::string kedi = "Mavi";\n    // selam ver\n    return 0;\n}', 'std::cout << "Merhaba " + kedi;'),
("Bellek ve Referanslar", "Память и ссылки", "Referansları ve pointer temellerini güvenli örneklerle keşfet.", "Изучи ссылки и основы указателей на безопасных примерах.", "#include <iostream>\nint main() {\n    int can = 9;\n    int& ref = can;\n    // referansla değeri artır\n    return 0;\n}", 'ref += 1; std::cout << can;'),
('Struct ve Sınıflar', 'Структуры и классы', 'İlgili verileri struct içinde grupla ve kendi türlerini oluştur.', 'Группируй данные в struct и создавай собственные типы.', '#include <iostream>\nstruct Kedi { std::string ad; int yas; };\nint main() {\n    Kedi k{"Luna", 3};\n    // adı ve yaşı yazdır\n    return 0;\n}', 'std::cout << k.ad << " " << k.yas;'),
("Nesne Yönelimli C++", "ООП в C++", "Sınıflar, kurucular ve kapsülleme ile nesne yönelimli tasarıma giriş yap.", "Познакомься с классами, конструкторами и инкапсуляцией.", "#include <iostream>\nclass Kahraman {\npublic:\n    int guc = 12;\n};\nint main() {\n    Kahraman k;\n    // gücü göster\n    return 0;\n}", 'std::cout << k.guc;'),
("STL ve Algoritmalar", "STL и алгоритмы", "STL algoritmalarıyla sıralama ve arama işlerini kısa, güvenli kodla yap.", "Сортируй и ищи с помощью алгоритмов STL.", "#include <iostream>\n#include <vector>\n#include <algorithm>\nint main() {\n    std::vector<int> v{4, 1, 3};\n    // sırala ve ilk değeri yaz\n    return 0;\n}", 'std::sort(v.begin(), v.end()); std::cout << v[0];'),
('Dosyalar ve Hata Yönetimi', 'Файлы и обработка ошибок', 'Dosya akışlarını ve istisnaları tanı; hatalara dayanıklı program kur.', 'Познакомься с потоками файлов и исключениями.', '#include <iostream>\n#include <stdexcept>\nint main() {\n    try { throw std::runtime_error("oops"); }\n    catch (...) { /* hatayı yakala */ }\n    return 0;\n}', 'std::cout << "Hata yakalandi";'),
('Final Projesi', 'Финальный проект', 'Öğrendiklerini bir araya getir: küçük, etkileşimli bir C++ kedi macerası kur.', 'Объедини знания и создай небольшое интерактивное приключение про кота.', '#include <iostream>\n#include <string>\nint main() {\n    // kahramanını tanıt ve puanını göster\n    return 0;\n}', 'std::cout << "Pati maceraya basliyor! Puan: 100";'),
('Pointer ve Dinamik Bellek', 'Указатели и динамическая память', "Bir işaretçi başka bir değişkenin adresini tutar. new heap'te bellek ayırır, delete ile geri verirsin.", 'Указатель хранит адрес другой переменной. new выделяет память в куче, а delete возвращает её.', "#include <iostream>\nint main() {\n    // heap'te bir int oluştur, yazdır ve serbest bırak\n    return 0;\n}", 'int* p = new int(42); std::cout << *p; delete p;'),
('Akıllı İşaretçiler ve RAII', 'Умные указатели и RAII', 'unique_ptr ve shared_ptr belleği senin yerine serbest bırakır. Kaynağı nesneye bağlamaya RAII denir.', 'unique_ptr и shared_ptr сами освобождают память. Привязка ресурса к объекту называется RAII.', '#include <iostream>\n#include <memory>\nint main() {\n    // make_unique ile bir int oluştur ve yazdır\n    return 0;\n}', 'auto p = std::make_unique<int>(15); std::cout << *p;'),
('Kalıtım ve Polimorfizm', 'Наследование и полиморфизм', 'Türetilmiş sınıf taban sınıfın özelliklerini devralır. virtual metotlar, taban referansıyla çağrılsa bile doğru sınıfın kodunu çalıştırır.', 'Производный класс наследует возможности базового. virtual-методы вызывают код нужного класса даже через ссылку на базовый.', '#include <iostream>\nclass Hayvan { public: virtual void sesCikar() const { std::cout << "..."; } };\nclass Kedi : public Hayvan { public: void sesCikar() const override { std::cout << "Miyav"; } };\nint main() {\n    Kedi k;\n    // taban sınıf referansıyla çağır\n    return 0;\n}', 'const Hayvan& h = k; h.sesCikar();'),
('Şablonlar ve Lambda', 'Шаблоны и лямбды', 'template ile her türle çalışan genel kod yazarsın. Lambda, yerinde tanımlanan küçük isimsiz fonksiyondur ve [ ] ile dış değişkenleri yakalar.', 'template позволяет писать код для любых типов. Лямбда — маленькая безымянная функция на месте; [ ] захватывает внешние переменные.', '#include <iostream>\ntemplate <typename T>\nT enBuyuk(T a, T b) { return a > b ? a : b; }\nint main() {\n    // şablonu çağır\n    return 0;\n}', 'std::cout << enBuyuk(3, 9);'),
('map, set ve Konteynerler', 'map, set и контейнеры', 'std::map anahtar-değer çiftlerini anahtara göre sıralı tutar; std::set tekrarsız ve sıralı değerler saklar.', 'std::map хранит пары ключ-значение, упорядоченные по ключу; std::set хранит уникальные упорядоченные значения.', '#include <iostream>\n#include <map>\n#include <string>\nint main() {\n    std::map<std::string, int> puan{{"Luna", 7}, {"Momo", 5}};\n    // Luna\'nın puanını yaz\n    return 0;\n}', 'std::cout << puan["Luna"];'),
]

CURRICULUM = []
# Chapter dependencies form a directed acyclic learning map. A completed
# chapter (including its boss mission) unlocks its dependent topics.
PREREQUISITES = {1: (), 2: (1,), 3: (1, 2), 4: (2,), 5: (3, 4), 6: (5,), 7: (4,), 8: (6, 7), 9: (2, 3), 10: (8, 7), 11: (7,), 12: (11,), 13: (8,), 14: (11,), 15: (12, 13, 14), 16: (10, 8), 17: (16, 12), 18: (12, 16), 19: (7, 13), 20: (13, 8)}
for ci, (tr, ru, lesson_tr, lesson_ru, starter, snippet) in enumerate(topics, 1):
    prefix = f"c{ci:02}"
    outputs = ["Merhaba, C++!", "Mırmır 7", "42", "24", "Gecti", "1 2 3 4 5 ", "12", "3 5 8 ", "Merhaba Mavi", "10", "Luna 3", "12", "1", "Hata yakalandi", "Pati maceraya basliyor! Puan: 100", '42', '15', 'Miyav', '9', '7']
    output = outputs[ci-1]
    required = [["std::cout"], ["int", "string"], ["std::cin", "std::cout"], ["+", "*"], ["if", ">="], ["for"], ["ikiKat", "return"], ["vector", "for"], ["std::string"], ["&"], ["struct", "Kedi"], ["class"], ["std::sort"], ["catch"], ["std::string", "puan"], ['new', 'delete'], ['make_unique'], ['virtual', 'override'], ['template'], ['map']][ci-1]
    # Stable, deliberately varied sequence: quiz, prediction, debugging, practice, boss.
    tasks = [
        task(prefix+"-01", "quiz", 15, "Hızlı Bilgi", "Блиц-вопрос", {"tr": f"{tr}: C++ programında çalışmanın başladığı standart fonksiyon hangisidir? (main / start / begin)", "ru": f"{ru}: Какая стандартная функция является точкой входа программы C++? (main / start / begin)"}, {"tr": "Doğru yanıtı yaz.", "ru": "Напиши правильный ответ."}, "main", "", "main"),
        task(prefix+"-02", "predict", 20, "Çıktıyı Tahmin Et", "Предскажи вывод", {"tr": f"Bu bölümdeki temel fikri kullanarak konsolun çıktısını tahmin et: std::cout << 2 + 3; (yalnızca sonucu yaz)", "ru": f"Используя идею раздела «{ru}», предскажи вывод: std::cout << 2 + 3; (напиши только результат)"}, {"tr": "Beklenen çıktı: 5", "ru": "Ожидаемый вывод: 5"}, "5", "", "5"),
        task(prefix+"-03", "fix", 25, "Kedi Hatasını Düzelt", "Исправь ошибку кота", {"tr": f"Kedi şu kodun çıktısının 42 olmasını istiyor. Derlenen kodu düzenleyip doğru çıktıyı üret:\n#include <iostream>\nint main() {{ std::cout << 40 + 1; return 0; }}", "ru": f"Кот хочет получить вывод 42. Исправь код так, чтобы он компилировался и выводил нужное число:\n#include <iostream>\nint main() {{ std::cout << 40 + 1; return 0; }}"}, {"tr": "Kodunu derleyip çalıştıracağız. İstenen çıktı: 42", "ru": "Код будет скомпилирован и запущен. Нужный вывод: 42"}, "#include <iostream>\nint main() { std::cout << 40 + 1; return 0; }", "42"),
        task(prefix+"-04", "code", 35, "Pratik Görevi", "Практическое задание", {"tr": f"{tr} konusunu kullan. Aşağıdaki iskeleti tamamla veya kendi kodunu yaz. Programın çıktısı tam olarak şu olmalı:\n{output}", "ru": f"Примени тему «{ru}». Дополни шаблон или напиши свой код. Программа должна вывести ровно:\n{output}"}, {"tr": "Derle ve görevini gönder.", "ru": "Скомпилируй и отправь решение."}, starter, output),
        task(prefix+"-boss", "boss", 60, "Boss Challenge", "Битва с боссом", {"tr": f"Bölüm sonu boss'u! {tr} fikrini kullanarak aşağıdaki çıktıyı üret. Kendi çözümünü yazıp çalıştır:\n{output}", "ru": f"Финальный босс! Используй тему «{ru}», чтобы получить вывод:\n{output}"}, {"tr": "Boss için kod yaz; derleyici çıktıyı denetler.", "ru": "Напиши код для босса; компилятор проверит вывод."}, starter, output),
    ]
    quiz_specs = [
        ("C++ programının standart giriş noktası nedir? (main / start / begin)", "Как называется стандартная точка входа программы C++? (main / start / begin)", "main"),
        ("Tam sayı türünün adı hangisidir? (int / text / decimal)", "Как называется тип целого числа? (int / text / decimal)", "int"),
        ("cin >> yas; ifadesindeki >> ne yapar? (girdi alır / çıktı verir)", "Что делает оператор >> в cin >> yas? (читает ввод / выводит текст)", {"tr":"girdi alır","ru":"читает ввод"}),
        ("8 + 4 * 2 ifadesinde önce hangisi hesaplanır? (toplama / çarpma)", "Что вычисляется первым в 8 + 4 * 2? (сложение / умножение)", {"tr":"çarpma","ru":"умножение"}),
        ("Bir koşul doğruysa çalışacak C++ anahtar sözcüğü nedir? (if / loop / case)", "Какое ключевое слово запускает код при истинном условии? (if / loop / case)", "if"),
        ("Tekrar sayısı belli olduğunda hangi döngü sık kullanılır? (for / catch / class)", "Какой цикл часто используют, когда число повторов известно? (for / catch / class)", "for"),
        ("int ikiKat(int x) fonksiyonunda x ne olarak adlandırılır? (parametre / namespace / sınıf)", "Как называется x в int ikiKat(int x)? (параметр / namespace / класс)", {"tr":"parametre","ru":"параметр"}),
        ("vector içindeki ilk elemana hangi indeksle erişilir? (0 / 1 / -1)", "Какой индекс у первого элемента vector? (0 / 1 / -1)", "0"),
        ("std::string metin uzunluğunu hangi metot verir? (size / sort / push)", "Какой метод std::string возвращает длину? (size / sort / push)", "size"),
        ("int& ref bir referanstır. ref değişince ne olur? (asıl değer değişir / kopya oluşur)", "Что происходит при изменении ссылки int& ref? (меняется исходное значение / создаётся копия)", {"tr":"asıl değer değişir","ru":"меняется исходное значение"}),
        ("struct Kedi { int yas; }; içindeki yas neyi temsil eder? (üye alan / döngü / fonksiyon)", "Что означает yas внутри struct Kedi? (поле / цикл / функция)", {"tr":"üye alan","ru":"поле"}),
        ("Nesne üretmek için hangi C++ yapısını tanımlarsın? (class / include / return)", "Какую конструкцию C++ объявляют для создания объектов? (class / include / return)", "class"),
        ("std::sort varsayılan olarak hangi sırada düzenler? (küçükten büyüğe / büyükten küçüğe)", "В каком порядке std::sort сортирует по умолчанию? (по возрастанию / по убыванию)", {"tr":"küçükten büyüğe","ru":"по возрастанию"}),
        ("Bir istisnayı yakalayan anahtar sözcük nedir? (catch / throw / try)", "Какое ключевое слово перехватывает исключение? (catch / throw / try)", "catch"),
        ("Bir C++ dosyasının standart uzantısı hangisidir? (.cpp / .py / .html)", "Какое стандартное расширение у файла C++? (.cpp / .py / .html)", ".cpp"),        ('new ile ayrılan belleği serbest bırakmak için hangi anahtar sözcük kullanılır? (delete / free / remove)', 'Какое ключевое слово освобождает память, выделенную через new? (delete / free / remove)', 'delete'),
        ('Tek sahipli akıllı işaretçinin adı nedir? (unique_ptr / shared_ptr / weak_ref)', 'Как называется умный указатель с единственным владельцем? (unique_ptr / shared_ptr / weak_ref)', 'unique_ptr'),
        ('Taban sınıf referansıyla türemiş sınıfın metodunu çağırmak için taban metot nasıl işaretlenir? (virtual / static / const)', 'Как пометить метод базового класса, чтобы через ссылку вызывался метод производного? (virtual / static / const)', 'virtual'),
        ('Her türle çalışan genel bir fonksiyon yazmak için hangi anahtar sözcük kullanılır? (template / virtual / typedef)', 'Какое ключевое слово нужно для обобщённой функции, работающей с любым типом? (template / virtual / typedef)', 'template'),
        ('Anahtar-değer çiftlerini anahtara göre sıralı tutan konteyner hangisidir? (map / vector / array)', 'Какой контейнер хранит пары ключ-значение, упорядоченные по ключу? (map / vector / array)', 'map'),
    ]
    prompt_tr, prompt_ru, answer = quiz_specs[ci-1]
    tasks[0]["prompt"] = {"tr": prompt_tr, "ru": prompt_ru}
    tasks[0]["answer"] = answer
    prediction_specs = [
        ('std::cout << 2 + 3;', '5'), ('int yas=7; std::cout << yas + 1;', '8'), ('int n=4; std::cout << n * 2;', '8'), ('std::cout << 8 + 4 * 2;', '16'), ('int puan=50; if(puan>=50) std::cout << "Gecti";', 'Gecti'), ('int s=0; for(int i=1;i<=3;i++) s+=i; std::cout << s;', '6'), ('int ikiKat(int x){return x*2;} std::cout << ikiKat(6);', '12'), ('std::vector<int> v{3,5,8}; std::cout << v[0] + v[2];', '11'), ('std::string k="Mavi"; std::cout << "Merhaba " + k;', 'Merhaba Mavi'), ('int x=9; int& r=x; r++; std::cout << x;', '10'), ('struct K{int yas;}; K k{3}; std::cout << k.yas;', '3'), ('class K{public:int guc=12;}; K k; std::cout << k.guc;', '12'), ('std::vector<int> v{4,1,3}; std::sort(v.begin(),v.end()); std::cout << v[0];', '1'), ('try { throw 1; } catch(...) { std::cout << "Yakalandi"; }', 'Yakalandi'), ('int puan=100; std::cout << "Puan: " << puan;', 'Puan: 100'),        ('int x=5; int* p=&x; *p=9; std::cout << x;', '9'),
        ('auto a=std::make_shared<int>(4); auto b=a; std::cout << a.use_count();', '2'),
        ('struct A{virtual void f(){std::cout<<"A";}}; struct B:A{void f() override{std::cout<<"B";}}; B b; A& r=b; r.f();', 'B'),
        ('auto kare=[](int x){return x*x;}; std::cout << kare(7);', '49'),
        ('std::set<int> s{3,1,3,2}; std::cout << s.size();', '3'),
    ]
    code, predicted = prediction_specs[ci-1]
    tasks[1]["prompt"] = {"tr": f"Aşağıdaki C++ satırının konsol çıktısını yaz. Yalnızca çıktıyı gir:\n{code}", "ru": f"Напиши вывод следующего фрагмента C++. Введи только результат:\n{code}"}
    tasks[1]["starter"] = predicted
    tasks[1]["answer"] = predicted
    fix_specs = [
        ('#include <iostream>\nint main(){std::cout << "Merhaba C++!" return 0;}', 'Merhaba C++!'),
        ('#include <iostream>\n#include <string>\nint main(){int yas=6;std::cout << "Mırmır " << yas;}', 'Mırmır 7'),
        ('#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n+1;}', '42'),
        ('#include <iostream>\nint main(){std::cout << (8+4)*2;}', '16'),
        ('#include <iostream>\nint main(){int puan=50;if(puan>50)std::cout<<"Gecti";else std::cout<<"Kaldi";}', 'Gecti'),
        ('#include <iostream>\nint main(){for(int i=1;i<5;i++)std::cout<<i<<" ";}', '1 2 3 4 5 '),
        ('#include <iostream>\nint ikiKat(int x){return x+1;}\nint main(){std::cout<<ikiKat(6);}', '12'),
        ('#include <iostream>\n#include <vector>\nint main(){std::vector<int> v{3,5,8};int s=0;for(int i=0;i<2;i++)s+=v[i];std::cout<<s;}', '16'),
        ('#include <iostream>\n#include <string>\nint main(){std::string k="Mavi";std::cout<<"Merhaba"+k;}', 'Merhaba Mavi'),
        ('#include <iostream>\nint main(){int can=9;int& ref=can;ref--;std::cout<<can;}', '10'),
        ('#include <iostream>\n#include <string>\nstruct Kedi{std::string ad;int yas;};int main(){Kedi k{"Luna",3};std::cout<<k.ad;}', 'Luna 3'),
        ('#include <iostream>\nclass Kahraman{public:int guc=10;};int main(){Kahraman k;std::cout<<k.guc;}', '12'),
        ('#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){std::vector<int> v{4,1,3};std::sort(v.begin(),v.end(),std::greater<int>());for(int n:v)std::cout<<n<<" ";}', '1 3 4 '),
        ('#include <iostream>\n#include <stdexcept>\nint main(){throw std::runtime_error("oops");}', 'Hata yakalandi'),
        ('#include <iostream>\n#include <string>\nint main(){std::string k="Pati";int puan=0;std::cout<<"Pati maceraya basliyor. Puan: "<<puan;}', 'Pati maceraya basliyor! Puan: 100'),
        ('#include <iostream>\nint main(){int* p=new int(7);std::cout<<p;delete p;}', '7'),
        ('#include <iostream>\n#include <memory>\nint main(){auto a=std::make_unique<int>(4);auto b=a;std::cout<<*b;}', '4'),
        ('#include <iostream>\nclass A{public:void f()const{std::cout<<"A";}};class B:public A{public:void f()const{std::cout<<"B";}};\nint main(){B b;const A& r=b;r.f();}', 'B'),
        ('#include <iostream>\nint main(){int k=3;auto f=[](int x){return x*k;};std::cout<<f(2);}', '6'),
        ('#include <iostream>\n#include <map>\nint main(){std::map<int,int> m;m[1]=1;m[1]=1;std::cout<<m[1];}', '2'),
    ]
    buggy, fix_expected = fix_specs[ci-1]
    tasks[2]["starter"] = buggy
    tasks[2]["expected"] = fix_expected
    tasks[2]["prompt"] = {"tr": f"Kedi bu bölümün konusuyla ilgili bir hata yaptı. Kodu düzelt; beklenen çıktı: {fix_expected}", "ru": f"Кот допустил ошибку по теме этой главы. Исправь код; ожидаемый вывод: {fix_expected}"}
    tasks[2]["tests"] = [{"input":"21","expected":"42"},{"input":"-4","expected":"-8"},{"input":"0","expected":"0"}] if ci == 3 else [{"input":"","expected":fix_expected}]
    tasks[2]["requires"] = required
    tasks[2]["bug_type"] = ["syntax","logic","logic","logic","boundary","off_by_one","logic","logic","logic","logic","data","logic","ordering","exception","logic", 'pointer', 'ownership', 'dispatch', 'capture', 'counting'][ci-1]
    # Chapter-specific extra input challenge, genuinely reads stdin.
    if ci == 3:
        tasks[3] = task(prefix+"-04", "code", 35, "Girdiyi İki Katına Çıkar", "Удвой ввод", {"tr": "Kullanıcıdan bir tam sayı oku ve iki katını yazdır. Örnek girdi: 21", "ru": "Прочитай целое число и выведи его удвоенное значение. Пример ввода: 21"}, {"tr": "Program girdisi 21, beklenen çıktı 42.", "ru": "Ввод: 21, ожидаемый вывод: 42."}, "#include <iostream>\nint main() { int n; std::cin >> n; // sonucu yazdır\n return 0; }", "42", "21")
        tasks[3]["tests"] = [{"input": "21", "expected": "42"}, {"input": "-4", "expected": "-8"}, {"input": "0", "expected": "0"}]
    hint_tr = [f"{tr}: ders örneğindeki temel sözdizimini anımsa.", "Beklenen çıktıya ulaşmak için gerekli C++ yapısını ekle.", f"Kodunda şu öğeler bulunmalı: {', '.join(required)}."]
    hint_ru = [f"Тема «{ru}»: вспомни синтаксис из примера урока.", "Добавь нужную конструкцию C++, чтобы получить ожидаемый вывод.", f"В коде должны быть элементы: {', '.join(required)}."]
    if ci == 1:
        hint_tr = ["main fonksiyonu giriş noktasıdır.", "Çıktı için iostream ve std::cout kullan.", "main içine std::cout << \"Merhaba, C++!\"; ekle."]
        hint_ru = ["Функция main — точка входа.", "Для вывода нужны iostream и std::cout.", "Добавь в main: std::cout << \"Merhaba, C++!\";"]
    if ci == 2:
        hint_tr = ["Her veri türüne uygun değişken seç.", "Metin için string, tam sayı için int kullan.", "std::string ad ve int yas değişkenleri tanımla."]
        hint_ru = ["Выбери тип для каждого значения.", "Для текста используй string, для целых чисел — int.", "Создай переменные std::string ad и int yas."]
    if ci == 3:
        hint_tr = ["cin girdi okur, cout çıktı verir.", "Tam sayıyı cin >> n ile oku.", "Okuduktan sonra cout ile n * 2 yazdır."]
        hint_ru = ["cin читает ввод, cout выводит результат.", "Прочитай число через cin >> n.", "После чтения выведи n * 2 через cout."]
    for item in tasks:
        item["hints"] = {"tr": hint_tr, "ru": hint_ru}
        if item["kind"] in ("code", "boss"):
            item["requires"] = required
        elif item["kind"] == "fix":
            item["requires"] = ["std::cout"]
    import re
    example = re.sub(r"//[^\n]*", lambda _: snippet, starter, count=1)
    CURRICULUM.append({"id": prefix, "number": ci, "prerequisites": [f"c{num:02}" for num in PREREQUISITES[ci]], "title": {"tr": tr, "ru": ru}, "lesson": {"tr": lesson_tr, "ru": lesson_ru}, "guide": GUIDES[ci-1], "example": example, "tasks": tasks})

apply_mission_contracts(CURRICULUM)

# Deeper lessons and more practice: each chapter gets three more lesson sections and
# three more missions, so the order becomes quiz, predict, quiz, predict, fix, warm-up,
# practice and boss. The boss stays last because chapter unlocking depends on it.
for _index, _chapter in enumerate(CURRICULUM):
    _chapter["guide"] = {lang: [list(item) for item in _chapter["guide"][lang]] + [list(item) for item in extra_guide(_index, lang)] for lang in ("tr", "ru")}
    _quiz, _predict, _warm = extra_tasks(_index, _chapter["id"])
    _t = _chapter["tasks"]
    _chapter["tasks"] = [_t[0], _t[1], _quiz, _predict, _t[2], _warm, _t[3], _t[4]]

from task_clarity import apply as _clarify_tasks
_clarify_tasks(CURRICULUM)
