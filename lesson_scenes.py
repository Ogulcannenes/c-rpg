"""Konu anlatımlarındaki "canlı anlatım" sahneleri.

Her sahne bir konu anlatımı bölümüne bağlıdır ve kodu satır satır çalıştırarak gösterir:
değişkenler bellekte adresleriyle belirir, pointer okları çizilir, döngü turları ilerler,
koşul çatalında yol seçilir... Sahneler küçük bir tarif dilinde yazılır; ``build`` bunları
web/lab-theater.js motorunun anladığı adım listesine çevirir (görsel laboratuvarla aynı biçim).

Tarif dili (her adım bir sözlük):
  line   çalışan kod satırı (1'den başlar, 0 = hiçbiri)
  say    (tr, ru) anlatım cümlesi
  new    [(ad, tür, değer, {seçenekler})]  yeni hücreler; seçenekler: heap, frame, to, region,
         index, label, size, addr, fields, methods, kind, badge
  set    {ad: değer}          değer değişir (durum: changed)
  to     {ad: hedef|None}     pointer yeni hedefi gösterir (None = nullptr)
  type   {ad: tür}            hücrenin tür etiketi değişir
  alias  {ad: takma ad}       referans: aynı kutunun ikinci adı
  del    [ad]                 hücre silinir
  mark   {ad: durum}          yalnızca bu adımda geçerli durum (deref, active, error, found…)
  keep   {ad: durum|None}     kalıcı durum (freed, dangling…)
  out    ekrana eklenen metin
  bars / act / found          sıralama çubukları (bars görseli)
  branch, loop, expr, stage, payload, stage_state, note, rule  sahneye özel bilgiler
"""
from __future__ import annotations

from copy import deepcopy

VISUALS = {"memory", "branch", "loop", "calls", "array", "bars", "lifo", "fifo", "object", "flow", "expr"}
SIZES = {"int": 4, "double": 8, "char": 1, "bool": 1}


def tx(value, lang):
    if isinstance(value, tuple) and len(value) == 2 and all(isinstance(v, str) for v in value):
        return value[0] if lang == "tr" else value[1]
    if isinstance(value, list):
        return [tx(v, lang) for v in value]
    if isinstance(value, dict):
        return {k: tx(v, lang) for k, v in value.items()}
    return value


def _size(type_, explicit=None):
    if explicit:
        return explicit
    t = str(type_)
    if "*" in t or "ptr" in t:
        return 8
    if "string" in t:
        return 32
    for key, size in SIZES.items():
        if t.startswith(key):
            return size
    return 16 if t[:1].isupper() else 4


def _hex(n):
    return f"0x{n:04X}"


def build(scene, lang="tr"):
    """Tarifi, motorun çizebileceği tam adım listesine çevirir."""
    cells, order, keep, aliases = {}, [], {}, {}
    stack_next, heap_next = scene.get("stack_base", 0x1000), 0xA000
    output, steps = "", []

    def address(name):
        cell = cells.get(name)
        return cell.get("address") if cell else None

    for index, raw in enumerate(scene["steps"]):
        auto, keep_now = {}, {}
        for spec in raw.get("new", []):
            name, type_, value = spec[0], tx(spec[1], lang), tx(spec[2], lang)
            opts = spec[3] if len(spec) > 3 else {}
            cell = {"name": name, "type": type_, "value": value}
            region = opts.get("region") or ("heap" if opts.get("heap") else "stack")
            cell["region"] = region
            for key in ("frame", "index", "label", "fields", "methods", "kind", "badge"):
                if key in opts:
                    cell[key] = tx(opts[key], lang)
            size = _size(type_, opts.get("size"))
            if region not in {"blueprint", "map"} and opts.get("addr", True) is not None:
                if region == "heap":
                    at = heap_next
                    heap_next += max(16, (size + 15) // 16 * 16)
                else:
                    align = min(size, 8)
                    at = (stack_next + align - 1) // align * align
                    stack_next = at + size
                cell["address"] = _hex(at)
                cell["size"] = size
            if region == "map":
                cell["region"] = "array"
            if "to" in opts:
                target = opts["to"]
                if target:
                    cell["points_to"] = target
                if value is None:
                    cell["value"] = address(target) if target else "nullptr"
            cells[name] = cell
            order.append(name)
            auto[name] = "allocated" if region == "heap" else "new"
        for name, value in raw.get("set", {}).items():
            cells[name]["value"] = tx(value, lang)
            auto[name] = "changed"
        for name, type_ in raw.get("type", {}).items():
            cells[name]["type"] = tx(type_, lang)
            auto.setdefault(name, "changed")
        for name, target in raw.get("to", {}).items():
            cell = cells[name]
            if target:
                cell["points_to"], cell["value"] = target, address(target)
            else:
                cell.pop("points_to", None)
                cell["value"] = "nullptr"
            auto[name] = "changed"
        aliases.update(raw.get("alias", {}))
        for name, status in raw.get("keep", {}).items():
            if status:
                keep[name] = keep_now[name] = status
            else:
                keep.pop(name, None)
        for name in raw.get("del", []):
            cells.pop(name, None)
            order.remove(name)
            keep.pop(name, None)
            aliases.pop(name, None)
        if "bars" in raw:
            act, found, dim = set(raw.get("act", [])), set(raw.get("found", [])), set(raw.get("dim", []))
            current = [{"name": f"v[{i}]", "type": "int", "value": v, "region": "array", "index": i,
                        "status": "found" if i in found else "active" if i in act else "dim" if i in dim else ""}
                       for i, v in enumerate(raw["bars"])]
        else:
            mark = raw.get("mark", {})
            current = []
            names = order
            if scene.get("sorted"):
                names = sorted(order, key=lambda n: (cells[n].get("region") != "array", cells[n].get("label") or n))
            for name in names:
                cell = deepcopy(cells[name])
                cell["status"] = mark.get(name) or keep_now.get(name) or auto.get(name) or keep.get(name) or ""
                if name in aliases:
                    cell["alias"] = aliases[name]
                current.append({k: v for k, v in cell.items() if v is not None})
        output += tx(raw.get("out", ""), lang)
        step = {"index": index, "line": raw.get("line", 0), "text": tx(raw["say"], lang), "cells": current, "output": output}
        for key in ("branch", "loop", "stage", "payload", "stage_state", "note", "rule"):
            if key in raw:
                step[key] = tx(raw[key], lang)
        if "expr" in raw:
            step["expr"] = [{"t": tx(p, lang), "k": ""} if not isinstance(p, dict) else
                            {"t": tx(next(iter(p.values())), lang), "k": next(iter(p))} for p in raw["expr"]]
        steps.append(step)

    result = {"chapter": scene["chapter"], "section": scene["section"], "title": tx(scene["title"], lang),
              "visual": scene["visual"], "code": scene["code"], "steps": steps, "final": output, "no_found": True}
    for key in ("stages", "exits", "array_name", "class_name", "file"):
        if key in scene:
            result[key] = tx(scene[key], lang)
    return result


def S(chapter, section, title, visual, code, steps, **extra):
    return {"chapter": chapter, "section": section, "title": title, "visual": visual, "code": code, "steps": steps, **extra}


A = {"region": "array"}


def arr(i, **more):
    return {"region": "array", "index": i, **more}


def key(label):
    return {"region": "map", "label": label, "addr": None}


SCENES = [
    # ——— 1. İlk program ———
    S("c01", 0, ("Kod nasıl program olur?", "Как код становится программой?"), "flow",
      ["#include <iostream>", "int main() {", '    std::cout << "Merhaba";', "    return 0;", "}"],
      [
          {"line": 0, "stage": 0, "payload": "main.cpp", "say": ("Yazdığın kod, main.cpp adlı bir metin dosyasıdır. Bilgisayar onu henüz doğrudan çalıştıramaz.", "Твой код — это текстовый файл main.cpp. Компьютер пока не может выполнить его напрямую.")},
          {"line": 0, "stage": 1, "payload": "g++", "say": ("Derleyici (g++) dosyayı baştan sona okur, hataları denetler ve makine koduna çevirir.", "Компилятор (g++) читает файл целиком, проверяет ошибки и переводит его в машинный код.")},
          {"line": 0, "stage": 2, "payload": "0101…", "say": ("Sonuç, işlemcinin anladığı komutlardan oluşan çalıştırılabilir bir dosyadır.", "Результат — исполняемый файл из команд, понятных процессору.")},
          {"line": 2, "stage": 2, "payload": "main()", "say": ("Program çalışınca önce main() fonksiyonuna girilir; satırlar yukarıdan aşağı yürütülür.", "При запуске программа сначала входит в функцию main(); строки выполняются сверху вниз.")},
          {"line": 3, "stage": 3, "payload": "Merhaba", "out": "Merhaba", "say": ('std::cout << "Merhaba" metni ekrana gönderir.', 'std::cout << "Merhaba" отправляет текст на экран.')},
          {"line": 4, "stage": 3, "payload": "0 ✓", "say": ("return 0; programın sorunsuz bittiğini işletim sistemine bildirir.", "return 0; сообщает операционной системе, что программа завершилась успешно.")},
      ],
      stages=[{"icon": "📄", "label": "main.cpp", "sub": ("kaynak kod", "исходный код")}, {"icon": "⚙️", "label": ("derleyici", "компилятор"), "sub": "g++"},
              {"icon": "🧩", "label": "program.exe", "sub": ("makine kodu", "машинный код")}, {"icon": "🖥️", "label": ("ekran", "экран"), "sub": "console"}]),
    S("c01", 2, ("cout akışı", "Поток cout"), "flow",
      ["#include <iostream>", "int main() {", '    std::cout << "Merhaba" << "\\n";', '    std::cout << "C++" << std::endl;', "    return 0;", "}"],
      [
          {"line": 1, "stage": -1, "say": ("#include <iostream>, cout'u kullanabilmek için giriş/çıkış kütüphanesini ekler.", "#include <iostream> подключает библиотеку ввода-вывода, чтобы можно было использовать cout.")},
          {"line": 2, "stage": 0, "payload": "{ }", "say": ("Çalıştırma main()'in süslü parantezlerinin içinden başlar.", "Выполнение начинается внутри фигурных скобок main().")},
          {"line": 3, "stage": 1, "payload": '"Merhaba"', "say": ('<< okunu "akışa gönder" diye oku: "Merhaba" metni cout\'a akar.', 'Читай << как «отправить в поток»: текст "Merhaba" утекает в cout.')},
          {"line": 3, "stage": 2, "payload": "Merhaba ⏎", "out": "Merhaba\n", "say": ('Ardından "\\n" gelir: metin ekrana yazılır ve imleç alt satıra iner.', 'Затем идёт "\\n": текст печатается, а курсор переходит на новую строку.')},
          {"line": 4, "stage": 2, "payload": "C++ ⏎", "out": "C++\n", "say": ("std::endl de satırı bitirir; ikinci cout yeni satıra yazar.", "std::endl тоже завершает строку; второй cout печатает с новой строки.")},
          {"line": 5, "stage": 2, "payload": "0 ✓", "say": ("return 0; ile main biter ve program kapanır.", "На return 0; функция main заканчивается, программа закрывается.")},
      ],
      stages=[{"icon": "📝", "label": ("kod", "код"), "sub": "main()"}, {"icon": "➡️", "label": "std::cout", "sub": "<<"}, {"icon": "🖥️", "label": ("ekran", "экран"), "sub": "console"}]),

    # ——— 2. Değişkenler ———
    S("c02", 0, ("Değişken = adı olan bir kutu", "Переменная — коробка с именем"), "memory",
      ["int can = 9;", "can = can - 1;", "int yedek = can;", "std::cout << yedek;"],
      [
          {"line": 1, "new": [("can", "int", 9)], "say": ("int can = 9; bellekte 4 baytlık bir kutu açar, adını can koyar ve içine 9 yazar.", "int can = 9; выделяет в памяти коробку на 4 байта, называет её can и кладёт туда 9.")},
          {"line": 2, "set": {"can": 8}, "say": ('= "ata" demektir: önce sağ taraf hesaplanır (9 - 1), sonuç aynı kutuya yazılır.', "= означает «присвоить»: сначала вычисляется правая часть (9 - 1), результат записывается в ту же коробку.")},
          {"line": 3, "new": [("yedek", "int", 8)], "say": ("Yeni değişken kendi adresinde ayrı bir kutudur; can'ın değeri buraya kopyalanır.", "Новая переменная — отдельная коробка со своим адресом; значение can копируется сюда.")},
          {"line": 4, "out": "8", "mark": {"yedek": "active"}, "say": ("cout kutunun içindekini ekrana yazar: 8.", "cout печатает содержимое коробки: 8.")},
      ]),
    S("c02", 2, ("Türler ve kapladıkları yer", "Типы и сколько места они занимают"), "memory",
      ["int can = 9;", "double hiz = 2.5;", "char harf = 'A';", "bool tok = true;", "can = can - 1;", "const int MAX = 100;", "MAX = 5;   // ✗"],
      [
          {"line": 1, "new": [("can", "int", 9)], "say": ("int tam sayı tutar ve 4 bayt yer kaplar.", "int хранит целое число и занимает 4 байта.")},
          {"line": 2, "new": [("hiz", "double", 2.5)], "say": ("double kesirli sayı tutar; 8 bayt olduğu için bellek şeridinde daha geniştir. Aradaki boşluk hizalama içindir.", "double хранит дробное число; он занимает 8 байт, поэтому на ленте памяти шире. Промежуток перед ним — выравнивание.")},
          {"line": 3, "new": [("harf", "char", "'A'")], "say": ("char tek bir karakterdir; yalnızca 1 bayt.", "char — один символ; всего 1 байт.")},
          {"line": 4, "new": [("tok", "bool", "true")], "say": ("bool yalnızca true ya da false olabilir.", "bool может быть только true или false.")},
          {"line": 5, "set": {"can": 8}, "say": ("Atama kutunun içeriğini değiştirir; adres ve tür aynı kalır.", "Присваивание меняет содержимое коробки; адрес и тип остаются прежними.")},
          {"line": 6, "new": [("MAX", "const int", 100, {"badge": "const"})], "say": ("const bir değişkenin değeri bir kez verilir ve kilitlenir.", "Значение const-переменной задаётся один раз и блокируется.")},
          {"line": 7, "mark": {"MAX": "error"}, "say": ("MAX = 5; derleme hatası verir: sabit değiştirilemez.", "MAX = 5; даёт ошибку компиляции: константу нельзя изменить.")},
      ]),

    # ——— 3. Girdi ve çıktı ———
    S("c03", 2, ("cin: klavyeden kutulara", "cin: с клавиатуры в коробки"), "memory",
      ["int a, b;", "std::cin >> a >> b;", 'std::cout << a + b << "\\n";', "std::string ad;", "std::cin >> ad;", 'std::cout << "Selam " << ad;'],
      [
          {"line": 1, "new": [("a", "int", "?"), ("b", "int", "?")], "say": ("İki kutu açıldı ama henüz değer yok; içlerinde rastgele çöp olabilir.", "Открыты две коробки, но значений ещё нет; внутри может быть мусор.")},
          {"line": 2, "out": "⌨ 3 4\n", "say": ("Program durur ve klavyeyi bekler. Kullanıcı 3 4 yazıp Enter'a basar.", "Программа останавливается и ждёт клавиатуру. Пользователь вводит 3 4 и нажимает Enter.")},
          {"line": 2, "set": {"a": 3, "b": 4}, "say": (">> boşluğa kadar okur: ilk sayı a'ya, ikincisi b'ye gider.", ">> читает до пробела: первое число попадает в a, второе — в b.")},
          {"line": 3, "out": "7\n", "mark": {"a": "active", "b": "active"}, "say": ("a + b hesaplanır ve sonuç 7 ekrana yazılır.", "Вычисляется a + b, и результат 7 выводится на экран.")},
          {"line": 4, "new": [("ad", "std::string", '""')], "say": ("string metin tutar; başta boştur.", "string хранит текст; сначала он пуст.")},
          {"line": 5, "out": "⌨ Luna\n", "set": {"ad": '"Luna"'}, "say": ("cin >> ad bir kelime okur ve kutuya koyar.", "cin >> ad читает одно слово и кладёт его в коробку.")},
          {"line": 6, "out": "Selam Luna", "mark": {"ad": "active"}, "say": ("Metin ve değişken art arda << ile yazılır.", "Текст и переменная выводятся подряд через <<.")},
      ]),

    # ——— 4. Operatörler ———
    S("c04", 1, ("İşlem sırası", "Порядок операций"), "expr",
      ["int x = 2 + 3 * (4 - 1);", "std::cout << x;"],
      [
          {"line": 1, "expr": ["2 + 3 * ", {"hi": "(4 - 1)"}], "rule": ("1) Önce parantez", "1) Сначала скобки"), "say": ("İfade soldan sağa okunmaz; önce parantezin içi değerlendirilir.", "Выражение не считается просто слева направо: сначала то, что в скобках.")},
          {"line": 1, "expr": ["2 + 3 * ", {"new": "3"}], "rule": ("1) Önce parantez", "1) Сначала скобки"), "say": ("(4 - 1) yerini 3'e bırakır.", "(4 - 1) заменяется на 3.")},
          {"line": 1, "expr": ["2 + ", {"hi": "3 * 3"}], "rule": ("2) Sonra çarpma ve bölme", "2) Затем умножение и деление"), "say": ("Çarpma, toplamadan önce yapılır.", "Умножение выполняется раньше сложения.")},
          {"line": 1, "expr": ["2 + ", {"new": "9"}], "rule": ("2) Sonra çarpma ve bölme", "2) Затем умножение и деление"), "say": ("3 * 3 hesaplandı: 9.", "3 * 3 вычислено: 9.")},
          {"line": 1, "expr": [{"hi": "2 + 9"}], "rule": ("3) En son toplama ve çıkarma", "3) В конце сложение и вычитание"), "say": ("Geriye yalnızca toplama kaldı.", "Осталось только сложение.")},
          {"line": 1, "expr": ["x = ", {"new": "11"}], "new": [("x", "int", 11)], "say": ("Sonuç 11 olarak x'e atanır.", "Результат 11 присваивается x.")},
          {"line": 2, "expr": ["x = 11"], "out": "11", "say": ("cout << x; ekrana 11 yazar. Emin değilsen parantez kullan!", "cout << x; выводит 11. Если сомневаешься — ставь скобки!")},
      ]),
    S("c04", 2, ("Tam bölme ve kalan", "Целочисленное деление и остаток"), "expr",
      ["int toplam = 17;", "std::cout << toplam / 5;", "std::cout << toplam % 5;", "toplam += 3;", "std::cout << (toplam > 10 && toplam < 30);"],
      [
          {"line": 1, "new": [("toplam", "int", 17)], "expr": ["toplam = ", {"new": "17"}], "say": ("toplam kutusu 17 ile başlar.", "Коробка toplam начинается с 17.")},
          {"line": 2, "expr": ["17 / 5 → ", {"new": "3"}], "rule": ("int / int küsuratı atar", "int / int отбрасывает дробную часть"), "out": "3", "say": ("17 / 5 = 3.4 olurdu, ama iki int bölününce küsurat atılır: 3.", "17 / 5 было бы 3.4, но при делении двух int дробная часть отбрасывается: 3.")},
          {"line": 3, "expr": ["17 % 5 → ", {"new": "2"}], "rule": ("17 = 5 · 3 + 2", "17 = 5 · 3 + 2"), "out": "2", "say": ("% kalanı verir: 5, 17'nin içine 3 kez sığar, 2 artar.", "% даёт остаток: 5 помещается в 17 три раза, остаётся 2.")},
          {"line": 4, "set": {"toplam": 20}, "expr": ["toplam = 17 + 3 → ", {"new": "20"}], "rule": ("x += 3  ≡  x = x + 3", "x += 3  ≡  x = x + 3"), "say": ("+= mevcut değere ekler ve sonucu aynı kutuya yazar.", "+= прибавляет к текущему значению и записывает результат в ту же коробку.")},
          {"line": 5, "expr": [{"hi": "20 > 10"}, " && ", {"hi": "20 < 30"}], "rule": ("&&: iki taraf da doğru olmalı", "&&: обе стороны должны быть истинны"), "say": ("İki karşılaştırma ayrı ayrı denetlenir.", "Оба сравнения проверяются по отдельности.")},
          {"line": 5, "expr": ["true && true → ", {"new": "1"}], "out": "1", "say": ("İkisi de doğru; cout true değerini 1 olarak yazar.", "Оба истинны; cout выводит true как 1.")},
      ]),

    # ——— 5. Koşullar ———
    S("c05", 0, ("if: yol ayrımı", "if: развилка"), "branch",
      ["int yas = 20;", "if (yas >= 18)", '    std::cout << "yetiskin";', "else", '    std::cout << "cocuk";'],
      [
          {"line": 1, "new": [("yas", "int", 20)], "branch": {"left": "yas", "op": ">=", "right": "18", "state": "pending"}, "say": ("yas kutusuna 20 yazıldı.", "В коробку yas записано 20.")},
          {"line": 2, "branch": {"left": "20", "op": ">=", "right": "18", "state": "checking"}, "say": ("if parantezindeki koşul hesaplanır: 20 >= 18 mi?", "Вычисляется условие в скобках if: 20 >= 18?")},
          {"line": 2, "branch": {"left": "20", "op": ">=", "right": "18", "state": "true"}, "say": ("Koşul true: program sol yola, if bloğuna girer.", "Условие истинно: программа идёт по левому пути, в блок if.")},
          {"line": 3, "branch": {"left": "20", "op": ">=", "right": "18", "state": "true"}, "out": "yetiskin", "say": ('if bloğu çalışır ve "yetiskin" yazılır; else bloğu tamamen atlanır.', 'Выполняется блок if и печатается "yetiskin"; блок else полностью пропускается.')},
      ],
      exits=['cout << "yetiskin"', 'cout << "cocuk"']),
    S("c05", 2, ("else if zinciri", "Цепочка else if"), "branch",
      ["int puan = 85;", 'if (puan >= 90)      std::cout << "A";', 'else if (puan >= 70) std::cout << "B";', 'else if (puan >= 50) std::cout << "C";', 'else                 std::cout << "F";'],
      [
          {"line": 1, "new": [("puan", "int", 85)], "branch": {"left": "puan", "op": ">=", "right": "90", "state": "pending", "exits": ['cout << "A"', ("sonraki koşul ↓", "следующее условие ↓")]}, "say": ("puan = 85. Koşullar yukarıdan aşağı sırayla denenecek.", "puan = 85. Условия будут проверяться по очереди сверху вниз.")},
          {"line": 2, "branch": {"left": "85", "op": ">=", "right": "90", "state": "false", "exits": ['cout << "A"', ("sonraki koşul ↓", "следующее условие ↓")]}, "say": ('85 >= 90 yanlış; "A" atlanır, sıradaki else if denenir.', '85 >= 90 ложно; "A" пропускается, проверяется следующий else if.')},
          {"line": 3, "branch": {"left": "85", "op": ">=", "right": "70", "state": "checking", "exits": ['cout << "B"', ("sonraki koşul ↓", "следующее условие ↓")]}, "say": ("Şimdi 85 >= 70 kontrol ediliyor…", "Теперь проверяется 85 >= 70…")},
          {"line": 3, "branch": {"left": "85", "op": ">=", "right": "70", "state": "true", "exits": ['cout << "B"', ("sonraki koşul ↓", "следующее условие ↓")]}, "out": "B", "say": ('Doğru! "B" yazılır.', 'Истина! Печатается "B".')},
          {"line": 3, "branch": {"left": "85", "op": ">=", "right": "70", "state": "true", "exits": ['cout << "B"', ("atlandı", "пропущено")]}, "say": ("İlk doğru koşul çalıştı; zincirin geri kalanı (C ve F) hiç denetlenmez.", "Сработало первое истинное условие; остальная цепочка (C и F) даже не проверяется.")},
      ]),

    # ——— 6. Döngüler ———
    S("c06", 0, ("for döngüsünün turları", "Итерации цикла for"), "loop",
      ["for (int i = 1; i <= 3; ++i)", '    std::cout << i << " ";', "// ..."],
      [
          {"line": 1, "new": [("i", "int", 1)], "loop": {"values": [1, 2, 3], "done": 0, "check": "1 <= 3 ?"}, "say": ("Başlangıç: i = 1. Her turdan önce koşul (i <= 3) kontrol edilir.", "Начало: i = 1. Перед каждой итерацией проверяется условие (i <= 3).")},
          {"line": 2, "loop": {"values": [1, 2, 3], "done": 1}, "mark": {"i": "active"}, "out": "1 ", "say": ("1 <= 3 doğru → gövde çalışır ve 1 yazılır.", "1 <= 3 истинно → выполняется тело и печатается 1.")},
          {"line": 1, "set": {"i": 2}, "loop": {"values": [1, 2, 3], "done": 1, "check": "++i → 2 <= 3 ?"}, "say": ("Tur bitti: ++i ile i 2 olur, koşul yeniden denetlenir.", "Итерация окончена: ++i делает i равным 2, условие проверяется снова.")},
          {"line": 2, "loop": {"values": [1, 2, 3], "done": 2}, "mark": {"i": "active"}, "out": "2 ", "say": ("2 <= 3 doğru → 2 yazılır.", "2 <= 3 истинно → печатается 2.")},
          {"line": 2, "set": {"i": 3}, "loop": {"values": [1, 2, 3], "done": 3}, "out": "3 ", "say": ("i 3 olur; 3 <= 3 hâlâ doğru, 3 yazılır.", "i становится 3; 3 <= 3 всё ещё истинно, печатается 3.")},
          {"line": 1, "set": {"i": 4}, "loop": {"values": [1, 2, 3], "done": 3, "finished": True}, "say": ("i 4 olunca 4 <= 3 yanlış → döngü biter.", "Когда i = 4, условие 4 <= 3 ложно → цикл заканчивается.")},
          {"line": 3, "del": ["i"], "loop": {"values": [1, 2, 3], "done": 3, "finished": True}, "say": ("i yalnızca döngünün içinde yaşar; döngü bitince silinir.", "i живёт только внутри цикла; после цикла она удаляется.")},
      ]),
    S("c06", 2, ("Toplamı biriktirmek", "Накопление суммы"), "loop",
      ["int toplam = 0;", "for (int i = 1; i <= 4; ++i) {", "    toplam += i;", "}", "std::cout << toplam;"],
      [
          {"line": 1, "new": [("toplam", "int", 0)], "loop": {"values": [1, 2, 3, 4], "done": 0}, "say": ("toplam 0'dan başlar; biriktirici değişkenler hep böyle başlatılır.", "toplam начинается с 0; накопители всегда так инициализируют.")},
          {"line": 2, "new": [("i", "int", 1)], "loop": {"values": [1, 2, 3, 4], "done": 1, "check": "1 <= 4 ✓"}, "say": ("i = 1, koşul doğru, ilk tur başlıyor.", "i = 1, условие истинно, начинается первая итерация.")},
          {"line": 3, "set": {"toplam": 1}, "loop": {"values": [1, 2, 3, 4], "done": 1}, "say": ("1. tur: toplam += i → 0 + 1 = 1", "1-я итерация: toplam += i → 0 + 1 = 1")},
          {"line": 3, "set": {"i": 2, "toplam": 3}, "loop": {"values": [1, 2, 3, 4], "done": 2}, "say": ("2. tur: i = 2, toplam = 1 + 2 = 3", "2-я итерация: i = 2, toplam = 1 + 2 = 3")},
          {"line": 3, "set": {"i": 3, "toplam": 6}, "loop": {"values": [1, 2, 3, 4], "done": 3}, "say": ("3. tur: i = 3, toplam = 3 + 3 = 6", "3-я итерация: i = 3, toplam = 3 + 3 = 6")},
          {"line": 3, "set": {"i": 4, "toplam": 10}, "loop": {"values": [1, 2, 3, 4], "done": 4}, "say": ("4. tur: i = 4, toplam = 6 + 4 = 10", "4-я итерация: i = 4, toplam = 6 + 4 = 10")},
          {"line": 2, "set": {"i": 5}, "loop": {"values": [1, 2, 3, 4], "done": 4, "finished": True}, "say": ("i = 5 olunca 5 <= 4 yanlış; döngüden çıkılır.", "При i = 5 условие 5 <= 4 ложно; выход из цикла.")},
          {"line": 5, "del": ["i"], "loop": {"values": [1, 2, 3, 4], "done": 4, "finished": True}, "out": "10", "say": ("Döngü bitti; toplam 10 ekrana yazılır.", "Цикл окончен; toplam = 10 выводится на экран.")},
      ]),

    # ——— 7. Fonksiyonlar ———
    S("c07", 1, ("Fonksiyon çağrısı", "Вызов функции"), "calls",
      ["int kare(int x) {", "    return x * x;", "}", "int main() {", "    int s = kare(4);", "    std::cout << s;", "}"],
      [
          {"line": 5, "new": [("s", "int", "?", {"frame": "main()"})], "say": ("main çalışıyor; s için yer ayrıldı ama değeri kare(4)'ün sonucunu bekliyor.", "main работает; для s выделено место, но значение ждёт результата kare(4).")},
          {"line": 1, "new": [("x", "int", 4, {"frame": "kare(4)"})], "say": ("Çağrı yapılınca yığına yeni bir çerçeve eklenir; 4, x parametresine kopyalanır.", "При вызове в стек добавляется новый кадр; 4 копируется в параметр x.")},
          {"line": 2, "mark": {"x": "active"}, "say": ("kare'nin gövdesi çalışır: x * x = 16 hesaplanır.", "Выполняется тело kare: вычисляется x * x = 16.")},
          {"line": 5, "del": ["x"], "set": {"s": 16}, "say": ("return 16 değeri çağrının yerine geçer; kare'nin çerçevesi ve x silinir.", "return 16 подставляется на место вызова; кадр kare и x удаляются.")},
          {"line": 6, "out": "16", "mark": {"s": "active"}, "say": ("main kaldığı yerden devam eder ve 16'yı yazar.", "main продолжает с того же места и печатает 16.")},
      ]),
    S("c07", 2, ("Bir çağrının yolculuğu", "Путешествие одного вызова"), "calls",
      ["int kare(int x) { return x * x; }", "void selamla(std::string ad) {", '    std::cout << "Miyav " << ad;', "}", "int main() {", "    int s = kare(4);", '    selamla("Luna");', "}"],
      [
          {"line": 6, "new": [("s", "int", "?", {"frame": "main()"})], "say": ("main, kare(4) satırına gelince durur ve kare'yi çağırır.", "main доходит до kare(4), останавливается и вызывает kare.")},
          {"line": 1, "new": [("x", "int", 4, {"frame": "kare(4)"})], "say": ("x = 4 kopyası yeni çerçevede; return x * x hesaplanır.", "Копия x = 4 в новом кадре; вычисляется return x * x.")},
          {"line": 6, "del": ["x"], "set": {"s": 16}, "say": ("16 geri döner ve s'ye yazılır; kare'nin çerçevesi kaldırılır.", "Возвращается 16 и записывается в s; кадр kare удаляется.")},
          {"line": 2, "new": [("ad", "std::string", '"Luna"', {"frame": 'selamla("Luna")'})], "say": ('selamla çağrılır; "Luna" metni ad parametresine kopyalanır.', 'Вызывается selamla; текст "Luna" копируется в параметр ad.')},
          {"line": 3, "out": "Miyav Luna", "mark": {"ad": "active"}, "say": ('Fonksiyon ekrana "Miyav Luna" yazar.', 'Функция печатает "Miyav Luna".')},
          {"line": 4, "del": ["ad"], "say": ("void fonksiyon değer döndürmez; işi bitince çerçevesi silinir ve main'e dönülür.", "void-функция ничего не возвращает; после работы её кадр удаляется, и управление возвращается в main.")},
      ]),

    # ——— 8. Diziler ve vector ———
    S("c08", 0, ("Dizi bellekte yan yana", "Массив в памяти подряд"), "array",
      ["int dizi[3] = {4, 7, 1};", "std::cout << dizi[1];", "dizi[2] = 9;"],
      [
          {"line": 1, "new": [("dizi[0]", "int", 4, arr(0)), ("dizi[1]", "int", 7, arr(1)), ("dizi[2]", "int", 1, arr(2))], "say": ("Dizi 3 int'i bellekte yan yana tutar: her biri 4 bayt, adresler 4'er artar.", "Массив хранит 3 int подряд: каждый по 4 байта, адреса растут на 4.")},
          {"line": 2, "mark": {"dizi[1]": "active"}, "out": "7", "say": ("dizi[1] ikinci elemandır, çünkü indeksler 0'dan başlar.", "dizi[1] — второй элемент, потому что индексы начинаются с 0.")},
          {"line": 3, "set": {"dizi[2]": 9}, "say": ("dizi[2] = 9; son kutunun içeriğini değiştirir. Son indeks n - 1 = 2'dir.", "dizi[2] = 9; меняет содержимое последней ячейки. Последний индекс — n - 1 = 2.")},
          {"line": 3, "new": [("dizi[3]", "int", "??", arr(3))], "mark": {"dizi[3]": "error"}, "note": ("dizi[3] yok! Geçerli indeksler: 0, 1, 2", "dizi[3] не существует! Допустимые индексы: 0, 1, 2"), "say": ("Dikkat: dizi[3] diziye ait olmayan belleğe taşar.", "Осторожно: dizi[3] выходит за пределы массива в чужую память.")},
      ], array_name="int dizi[3]"),
    S("c08", 2, ("vector büyüyor", "vector растёт"), "array",
      ["std::vector<int> v;", "v.push_back(4);", "v.push_back(7);", "v.push_back(1);", "std::cout << v.size();", 'for (int x : v) std::cout << x << " ";', "std::cout << v[v.size() - 1];"],
      [
          {"line": 1, "note": "v.size() = 0", "say": ("Boş bir vector oluşturuldu; henüz hiç elemanı yok.", "Создан пустой vector; элементов пока нет.")},
          {"line": 2, "new": [("v[0]", "int", 4, arr(0))], "note": "v.size() = 1", "say": ("push_back(4) sona yeni bir kutu ekler.", "push_back(4) добавляет новую ячейку в конец.")},
          {"line": 3, "new": [("v[1]", "int", 7, arr(1))], "note": "v.size() = 2", "say": ("push_back(7): vector kendiliğinden büyür.", "push_back(7): vector растёт сам.")},
          {"line": 4, "new": [("v[2]", "int", 1, arr(2))], "note": "v.size() = 3", "say": ("push_back(1): artık {4, 7, 1}.", "push_back(1): теперь {4, 7, 1}.")},
          {"line": 5, "out": "3", "note": "v.size() = 3", "say": ("size() eleman sayısını verir: 3.", "size() возвращает количество элементов: 3.")},
          {"line": 6, "mark": {"v[0]": "active"}, "out": "4 ", "note": "x = 4", "say": ("Range-for elemanları sırayla x'e kopyalar: önce 4…", "Range-for по очереди копирует элементы в x: сначала 4…")},
          {"line": 6, "mark": {"v[1]": "active"}, "out": "7 ", "note": "x = 7", "say": ("…sonra 7…", "…затем 7…")},
          {"line": 6, "mark": {"v[2]": "active"}, "out": "1 ", "note": "x = 1", "say": ("…ve 1.", "…и 1.")},
          {"line": 7, "mark": {"v[2]": "found"}, "out": "1", "note": "v[3 - 1] = v[2] = 1", "say": ("Son eleman v[v.size() - 1] ile alınır: v[2] = 1.", "Последний элемент берётся как v[v.size() - 1]: v[2] = 1.")},
      ], array_name="std::vector<int> v"),

    # ——— 9. Metinler ———
    S("c09", 0, ("string: karakterlerin dizisi", "string: последовательность символов"), "array",
      ['std::string s = "Luna";', "std::cout << s.size();", "std::cout << s[0];", 's = s + "!";'],
      [
          {"line": 1, "new": [(f"s[{i}]", "char", f"'{ch}'", arr(i)) for i, ch in enumerate("Luna")], "say": ("string karakterleri sırayla tutar; her karakterin bir indeksi vardır.", "string хранит символы по порядку; у каждого символа есть индекс.")},
          {"line": 2, "out": "4", "note": "s.size() = 4", "say": ("size() karakter sayısını verir: 4.", "size() возвращает количество символов: 4.")},
          {"line": 3, "mark": {"s[0]": "active"}, "out": "L", "note": "s[0] = 'L'", "say": ("s[0] ilk karakterdir: 'L'.", "s[0] — первый символ: 'L'.")},
          {"line": 4, "new": [("s[4]", "char", "'!'", arr(4))], "note": '"Luna!"', "say": ('+ ile birleştirme sona yeni karakter ekler: "Luna!".', 'Сложение через + добавляет символ в конец: "Luna!".')},
      ], array_name="std::string s"),
    S("c09", 2, ("substr ve find", "substr и find"), "array",
      ['std::string s = "Kedicik";', "std::cout << s.size();", "std::cout << s.substr(0, 4);", 'std::cout << s.find("cik");'],
      [
          {"line": 1, "new": [(f"s[{i}]", "char", f"'{ch}'", arr(i)) for i, ch in enumerate("Kedicik")], "say": ('"Kedicik" 7 karakterdir; indeksler 0\'dan 6\'ya.', 'В "Kedicik" 7 символов; индексы от 0 до 6.')},
          {"line": 2, "out": "7", "note": "s.size() = 7", "say": ("size() 7 döndürür.", "size() возвращает 7.")},
          {"line": 3, "mark": {f"s[{i}]": "active" for i in range(4)}, "out": "Kedi", "note": 's.substr(0, 4) = "Kedi"', "say": ("substr(0, 4): 0. indeksten başla, 4 karakter al.", "substr(0, 4): начать с индекса 0 и взять 4 символа.")},
          {"line": 4, "mark": {f"s[{i}]": "found" for i in range(4, 7)}, "out": "4", "note": 's.find("cik") = 4', "say": ('find, aranan parçanın başladığı indeksi verir: "cik" 4\'te başlar.', 'find возвращает индекс начала найденного фрагмента: "cik" начинается с 4.')},
      ], array_name="std::string s"),

    # ——— 10. Bellek ve referanslar ———
    S("c10", 1, ("Pointer bir adres tutar", "Указатель хранит адрес"), "memory",
      ["int x = 5;", "int* p = &x;", "std::cout << *p;", "*p = 7;", "std::cout << x;"],
      [
          {"line": 1, "new": [("x", "int", 5)], "say": ("x için bellekte bir kutu açıldı; adresine bak: 0x1000.", "Для x в памяти открыта коробка; посмотри на её адрес: 0x1000.")},
          {"line": 2, "new": [("p", "int*", None, {"to": "x"})], "say": ("&x, x'in adresini verir. p bu adresi saklar ve böylece x'i gösterir.", "&x даёт адрес x. p хранит этот адрес и поэтому указывает на x.")},
          {"line": 3, "mark": {"p": "deref-from", "x": "deref"}, "out": "5", "say": ("*p: oku takip et ve adresteki değeri oku → 5.", "*p: пройди по стрелке и прочитай значение по адресу → 5.")},
          {"line": 4, "set": {"x": 7}, "mark": {"p": "deref-from"}, "say": ("*p = 7; oku takip edip x'in kutusuna 7 yazar. x'in adı hiç geçmedi!", "*p = 7; по стрелке записывает 7 в коробку x. Имя x даже не упоминалось!")},
          {"line": 5, "out": "7", "mark": {"x": "active"}, "say": ("x artık 7. Pointer, başka bir değişkeni uzaktan değiştirmenin yoludur.", "x теперь 7. Указатель позволяет менять другую переменную издалека.")},
      ]),
    S("c10", 2, ("Referans ve pointer birlikte", "Ссылка и указатель вместе"), "memory",
      ["int x = 5;", "int& r = x;", "int* p = &x;", "r = 8;", "*p = *p + 1;", "std::cout << x;"],
      [
          {"line": 1, "new": [("x", "int", 5)], "say": ("x = 5, bellekte 0x1000 adresinde.", "x = 5 в памяти по адресу 0x1000.")},
          {"line": 2, "alias": {"x": "r"}, "mark": {"x": "active"}, "say": ("int& r = x; yeni kutu açmaz! r, aynı kutunun ikinci adıdır.", "int& r = x; не создаёт новую коробку! r — второе имя той же коробки.")},
          {"line": 3, "new": [("p", "int*", None, {"to": "x"})], "say": ("int* p = &x; ise ayrı bir kutudur ve içinde x'in adresi vardır.", "int* p = &x; — это отдельная коробка, внутри которой адрес x.")},
          {"line": 4, "set": {"x": 8}, "say": ("r = 8; aslında x'e yazar, çünkü r ve x aynı kutu.", "r = 8; на самом деле пишет в x, ведь r и x — одна коробка.")},
          {"line": 5, "set": {"x": 9}, "mark": {"p": "deref-from"}, "say": ("*p = *p + 1; adresi takip eder: 8 okunur, 9 yazılır.", "*p = *p + 1; идёт по адресу: читается 8, записывается 9.")},
          {"line": 6, "out": "9", "mark": {"x": "active"}, "say": ("Üç yol, tek kutu: x, r ve *p hepsi 9'u görür.", "Три пути — одна коробка: x, r и *p видят 9.")},
      ]),

    # ——— 11. Struct ———
    S("c11", 2, ("struct: kendi veri türün", "struct: свой тип данных"), "object",
      ["struct Kedi {", "    std::string ad;", "    int yas;", "};", 'std::vector<Kedi> kediler{{"Luna", 3}, {"Pamuk", 5}};', "kediler[1].yas += 1;", 'std::cout << kediler[1].ad << " " << kediler[1].yas;'],
      [
          {"line": 1, "new": [("Kedi", "", "", {"region": "blueprint", "kind": "struct", "fields": ["std::string ad", "int yas"]})], "say": ("struct Kedi yeni bir tür tanımlar: her Kedi'nin bir adı ve yaşı olacak.", "struct Kedi определяет новый тип: у каждой Kedi будут имя и возраст.")},
          {"line": 5, "new": [("kediler[0].ad", "string", '"Luna"', {"region": "object", "frame": "kediler[0]"}), ("kediler[0].yas", "int", 3, {"region": "object", "frame": "kediler[0]"})], "say": ("Şablondan ilk nesne üretilir: Luna, 3.", "По шаблону создаётся первый объект: Luna, 3.")},
          {"line": 5, "new": [("kediler[1].ad", "string", '"Pamuk"', {"region": "object", "frame": "kediler[1]"}), ("kediler[1].yas", "int", 5, {"region": "object", "frame": "kediler[1]"})], "say": ("İkinci nesnenin alanları aynı, değerleri kendine ait: Pamuk, 5.", "У второго объекта те же поля, но свои значения: Pamuk, 5.")},
          {"line": 6, "set": {"kediler[1].yas": 6}, "say": ("kediler[1].yas += 1; yalnızca Pamuk'un yaşını değiştirir.", "kediler[1].yas += 1; меняет возраст только у Pamuk.")},
          {"line": 7, "out": "Pamuk 6", "mark": {"kediler[1].ad": "active", "kediler[1].yas": "active"}, "say": ("Nokta ile alanlara erişilir: Pamuk 6.", "Через точку обращаемся к полям: Pamuk 6.")},
      ], class_name="Kedi"),

    # ——— 12. Nesne yönelimli ———
    S("c12", 2, ("Kurucu ve private veri", "Конструктор и private-данные"), "object",
      ["class Kahraman {", "    int can;   // private", "public:", "    Kahraman(int b) : can(b) {}", "    void hasarAl(int h) { can = std::max(0, can - h); }", "    int durum() const { return can; }", "};", "Kahraman k(30);", "k.hasarAl(12);", "std::cout << k.durum();", "k.can = 999;   // ✗"],
      [
          {"line": 1, "new": [("Kahraman", "", "", {"region": "blueprint", "fields": ["- int can   (private)"], "methods": ["+ Kahraman(int)", "+ hasarAl(int)", "+ durum() const"]})], "say": ("class veriyi ve davranışı birlikte tanımlar. can private: dışarıdan görünmez.", "class описывает данные и поведение вместе. can — private: снаружи не виден.")},
          {"line": 8, "new": [("k.can", "int", 30, {"region": "object", "frame": "k", "badge": "private"})], "say": ("Kahraman k(30); nesne oluşur ve kurucu çalışır: can = 30.", "Kahraman k(30); создаётся объект и запускается конструктор: can = 30.")},
          {"line": 9, "set": {"k.can": 18}, "say": ("hasarAl(12) can'ı kontrollü biçimde azaltır: 30 - 12 = 18.", "hasarAl(12) уменьшает can контролируемо: 30 - 12 = 18.")},
          {"line": 10, "out": "18", "mark": {"k.can": "active"}, "say": ("durum() değeri okur ama değiştiremez (const): 18.", "durum() читает значение, но не может его изменить (const): 18.")},
          {"line": 11, "mark": {"k.can": "error"}, "say": ("k.can = 999; derlenmez: private alana sınıf dışından dokunulamaz.", "k.can = 999; не скомпилируется: к private-полю нельзя обратиться извне класса.")},
      ], class_name="Kahraman"),

    # ——— 13. STL ———
    S("c13", 1, ("std::sort sıralar", "std::sort сортирует"), "bars",
      ["std::vector<int> v{5, 1, 4, 2};", "std::sort(v.begin(), v.end());", 'for (int x : v) std::cout << x << " ";'],
      [
          {"line": 1, "bars": [5, 1, 4, 2], "say": ("Sırasız bir vector: 5, 1, 4, 2.", "Неупорядоченный vector: 5, 1, 4, 2.")},
          {"line": 2, "bars": [5, 1, 4, 2], "act": [0, 1], "say": ("sort elemanları karşılaştırır: 5 > 1, yerleri yanlış.", "sort сравнивает элементы: 5 > 1, они стоят не на своих местах.")},
          {"line": 2, "bars": [1, 5, 4, 2], "act": [0, 1], "say": ("Yer değiştirirler: küçük olan öne geçer.", "Они меняются местами: меньший идёт вперёд.")},
          {"line": 2, "bars": [1, 4, 5, 2], "act": [1, 2], "say": ("5 ile 4 de yer değiştirir.", "5 и 4 тоже меняются местами.")},
          {"line": 2, "bars": [1, 4, 2, 5], "act": [2, 3], "say": ("En büyük değer 5 sona ulaştı.", "Самое большое значение 5 дошло до конца.")},
          {"line": 2, "bars": [1, 2, 4, 5], "act": [1, 2], "say": ("Son düzeltme: 4 ile 2 yer değiştirir.", "Последняя поправка: 4 и 2 меняются местами.")},
          {"line": 3, "bars": [1, 2, 4, 5], "found": [0, 1, 2, 3], "out": "1 2 4 5 ", "say": ("v artık artan sırada. Gerçek std::sort bunu çok hızlı bir algoritmayla yapar.", "Теперь v отсортирован по возрастанию. Настоящий std::sort делает это очень быстрым алгоритмом.")},
      ]),
    S("c13", 2, ("Hazır algoritmalar", "Готовые алгоритмы"), "bars",
      ["std::vector<int> v{5, 1, 4, 1};", "std::sort(v.begin(), v.end());", "std::reverse(v.begin(), v.end());", "std::cout << *std::max_element(v.begin(), v.end());", "std::cout << std::count(v.begin(), v.end(), 1);"],
      [
          {"line": 1, "bars": [5, 1, 4, 1], "say": ("Başlangıç: v = {5, 1, 4, 1}.", "Начало: v = {5, 1, 4, 1}.")},
          {"line": 2, "bars": [1, 1, 4, 5], "say": ("sort artan sıraya dizer → 1 1 4 5.", "sort упорядочивает по возрастанию → 1 1 4 5.")},
          {"line": 3, "bars": [5, 4, 1, 1], "say": ("reverse sırayı tersine çevirir → 5 4 1 1.", "reverse переворачивает порядок → 5 4 1 1.")},
          {"line": 4, "bars": [5, 4, 1, 1], "found": [0], "dim": [1, 2, 3], "out": "5", "say": ("max_element en büyük elemanı gösteren bir iterator döndürür; * ile değeri alınır: 5.", "max_element возвращает итератор на наибольший элемент; через * берём значение: 5.")},
          {"line": 5, "bars": [5, 4, 1, 1], "found": [2, 3], "dim": [0, 1], "out": "2", "say": ("count, 1 değerinin kaç kez geçtiğini sayar: 2.", "count считает, сколько раз встречается 1: 2.")},
      ]),

    # ——— 14. Dosyalar ve hatalar ———
    S("c14", 1, ("try / throw / catch", "try / throw / catch"), "flow",
      ["int xp = -5;", "try {", '    if (xp < 0) throw std::runtime_error("negatif xp");', '    std::cout << "kaydedildi";', "} catch (const std::exception& e) {", '    std::cout << "Hata: " << e.what();', "}"],
      [
          {"line": 1, "new": [("xp", "int", -5)], "stage": -1, "say": ("xp hatalı bir değerle başlıyor: -5.", "xp начинается с ошибочного значения: -5.")},
          {"line": 2, "stage": 0, "payload": "xp = -5", "say": ("try bloğu, hata çıkabilecek kodu korumaya alır.", "Блок try берёт под защиту код, где может возникнуть ошибка.")},
          {"line": 3, "stage": 0, "payload": "-5 < 0 ?", "mark": {"xp": "active"}, "say": ("Koşul denetlenir: -5 < 0 doğru.", "Проверяется условие: -5 < 0 истинно.")},
          {"line": 3, "stage": 1, "stage_state": "error", "payload": "runtime_error", "say": ("throw bir istisna fırlatır; try'ın geri kalanı (\"kaydedildi\") hemen atlanır.", "throw выбрасывает исключение; остаток try (\"kaydedildi\") сразу пропускается.")},
          {"line": 5, "stage": 2, "payload": "e", "say": ("İstisna uygun catch bloğuna uçar ve yakalanır.", "Исключение летит в подходящий блок catch и перехватывается.")},
          {"line": 6, "stage": 2, "payload": "e.what()", "out": "Hata: negatif xp", "say": ("Program çökmez; anlaşılır bir mesaj yazılır.", "Программа не падает; выводится понятное сообщение.")},
      ],
      stages=[{"icon": "🧪", "label": "try", "sub": ("riskli kod", "рискованный код")}, {"icon": "💥", "label": "throw", "sub": ("hata fırlat", "бросить ошибку")}, {"icon": "🛟", "label": "catch", "sub": ("yakala", "поймать")}]),
    S("c14", 2, ("Dosyaya yaz, geri oku", "Записать в файл и прочитать"), "flow",
      ["{", '    std::ofstream out("kayit.txt");', '    out << "Luna " << 120;', "}   // ~out", 'std::ifstream in("kayit.txt");', "std::string ad; int xp;", "in >> ad >> xp;"],
      [
          {"line": 2, "stage": 1, "payload": "kayit.txt", "say": ("ofstream dosyayı yazmak için açar; dosya yoksa oluşturur.", "ofstream открывает файл для записи; если файла нет, создаёт его.")},
          {"line": 3, "stage": 2, "payload": '"Luna 120"', "say": ("<< ile yazılan veri cout'taki gibi akar, ama ekrana değil dosyaya.", "Данные через << текут как в cout, но не на экран, а в файл.")},
          {"line": 4, "stage": 2, "payload": "💾", "say": ("Kapsam bitince out yok olur ve dosya otomatik kapanır; veri diske kaydedilir.", "Когда область видимости заканчивается, out уничтожается и файл закрывается; данные сохранены на диск.")},
          {"line": 5, "stage": 3, "payload": "kayit.txt", "say": ("ifstream aynı dosyayı okumak için açar.", "ifstream открывает тот же файл для чтения.")},
          {"line": 6, "stage": 3, "payload": "kayit.txt", "new": [("ad", "string", '""'), ("xp", "int", "?")], "say": ("Okunan değerler için iki değişken hazırlanır.", "Готовим две переменные для прочитанных значений.")},
          {"line": 7, "stage": 4, "payload": "Luna 120", "set": {"ad": '"Luna"', "xp": 120}, "say": ('>> boşluğa kadar okur: "Luna" ad\'a, 120 xp\'ye gider.', '>> читает до пробела: "Luna" попадает в ad, 120 — в xp.')},
      ],
      stages=[{"icon": "🧠", "label": ("program", "программа"), "sub": "RAM"}, {"icon": "✍️", "label": "ofstream", "sub": ("yazma", "запись")}, {"icon": "📄", "label": "kayit.txt", "sub": ("disk", "диск")},
              {"icon": "📖", "label": "ifstream", "sub": ("okuma", "чтение")}, {"icon": "🧠", "label": "ad, xp", "sub": "RAM"}]),

    # ——— 15. Final projesi ———
    S("c15", 2, ("Projeyi fonksiyonlara böl", "Раздели проект на функции"), "calls",
      ["int toplamPuan(const std::vector<int>& puanlar) {", "    int t = 0;", "    for (int p : puanlar) t += p;", "    return t;", "}", "std::string rutbe(int puan) {", '    if (puan >= 100) return "Usta";', '    if (puan >= 50)  return "Gezgin";', '    return "Cirak";', "}", "int main() {", "    int toplam = toplamPuan({40, 30, 35});", "    std::cout << rutbe(toplam);", "}"],
      [
          {"line": 12, "new": [("toplam", "int", "?", {"frame": "main()"})], "say": ("main önce puanları toplamak için toplamPuan'ı çağırır.", "main сначала вызывает toplamPuan, чтобы сложить очки.")},
          {"line": 2, "new": [("t", "int", 0, {"frame": "toplamPuan({40,30,35})"})], "say": ("Yeni çerçevede t = 0 ile toplama başlar.", "В новом кадре сложение начинается с t = 0.")},
          {"line": 3, "set": {"t": 105}, "say": ("Döngü 40 + 30 + 35 ekler: t = 105.", "Цикл прибавляет 40 + 30 + 35: t = 105.")},
          {"line": 12, "del": ["t"], "set": {"toplam": 105}, "say": ("return t; sonucu main'e taşır: toplam = 105.", "return t; передаёт результат в main: toplam = 105.")},
          {"line": 7, "new": [("puan", "int", 105, {"frame": "rutbe(105)"})], "mark": {"puan": "active"}, "say": ("rutbe(105) çağrılır; puan >= 100 doğru.", "Вызывается rutbe(105); puan >= 100 истинно.")},
          {"line": 13, "del": ["puan"], "out": "Usta", "say": ('"Usta" döner ve ekrana yazılır. Her parça ayrı ayrı test edilebilir.', 'Возвращается "Usta" и выводится на экран. Каждую часть можно тестировать отдельно.')},
      ]),

    # ——— 16. Pointer ve dinamik bellek ———
    S("c16", 1, ("new: heap'te yer ayır", "new: выделить место в куче"), "memory",
      ["int* p = new int(5);", "*p = *p * 2;", "delete p;", "p = nullptr;"],
      [
          {"line": 1, "new": [("heap#1", "int", 5, {"heap": True}), ("p", "int*", None, {"to": "heap#1"})], "say": ("new int(5) heap'te isimsiz bir kutu açar; adresi p'ye verilir.", "new int(5) открывает в куче безымянную коробку; её адрес отдаётся p.")},
          {"line": 2, "set": {"heap#1": 10}, "mark": {"p": "deref-from"}, "say": ("*p ile heap'teki kutuya ulaşılır: 5 * 2 = 10.", "Через *p добираемся до коробки в куче: 5 * 2 = 10.")},
          {"line": 3, "keep": {"heap#1": "freed", "p": "dangling"}, "say": ("delete p; heap'teki kutuyu geri verir. Ama p hâlâ eski adresi tutuyor: sarkan pointer!", "delete p; возвращает коробку в куче. Но p всё ещё хранит старый адрес: висячий указатель!")},
          {"line": 4, "to": {"p": None}, "keep": {"p": None}, "del": ["heap#1"], "say": ("p = nullptr; artık p hiçbir yeri göstermiyor; bu güvenli.", "p = nullptr; теперь p никуда не указывает — это безопасно.")},
      ]),
    S("c16", 2, ("Stack ve heap", "Стек и куча"), "memory",
      ["int* p = new int(7);", "*p += 3;", "int* dizi = new int[3]{1, 2, 3};", "std::cout << *p + dizi[2];", "delete p;", "delete[] dizi;", "p = nullptr;"],
      [
          {"line": 1, "new": [("heap#1", "int", 7, {"heap": True}), ("p", "int*", None, {"to": "heap#1"})], "say": ("p stack'te, işaret ettiği int heap'te yaşar.", "p живёт в стеке, а int, на который он указывает, — в куче.")},
          {"line": 2, "set": {"heap#1": 10}, "mark": {"p": "deref-from"}, "say": ("*p += 3 → heap'teki değer 10 olur.", "*p += 3 → значение в куче становится 10.")},
          {"line": 3, "new": [("heap#2", "int[3]", "{1,2,3}", {"heap": True, "size": 12}), ("dizi", "int*", None, {"to": "heap#2"})], "say": ("new int[3] heap'te 3 int'lik bitişik bir blok ayırır.", "new int[3] выделяет в куче непрерывный блок из 3 int.")},
          {"line": 4, "out": "13", "mark": {"p": "deref-from", "heap#1": "deref", "dizi": "deref-from", "heap#2": "deref"}, "say": ("İki oku da takip et: 10 + 3 = 13.", "Пройди по обеим стрелкам: 10 + 3 = 13.")},
          {"line": 5, "keep": {"heap#1": "freed", "p": "dangling"}, "say": ("delete p; tek nesneyi serbest bırakır.", "delete p; освобождает одиночный объект.")},
          {"line": 6, "keep": {"heap#2": "freed", "dizi": "dangling"}, "say": ("new[] ile ayrılan dizi delete[] ile bırakılır.", "Массив, выделенный через new[], освобождается через delete[].")},
          {"line": 7, "to": {"p": None}, "keep": {"p": None}, "del": ["heap#1"], "say": ("p = nullptr; sarkan pointer kalmasın. dizi için de aynısını yapmak iyi bir alışkanlıktır.", "p = nullptr; чтобы не осталось висячего указателя. Для dizi стоит сделать так же.")},
      ]),

    # ——— 17. Akıllı işaretçiler ———
    S("c17", 0, ("unique_ptr: tek sahip", "unique_ptr: единственный владелец"), "memory",
      ["{", "    auto a = std::make_unique<int>(5);", "    auto b = std::move(a);", "    std::cout << *b;", "}   // ~b → delete"],
      [
          {"line": 2, "new": [("heap#1", "int", 5, {"heap": True}), ("a", "unique_ptr<int>", None, {"to": "heap#1"})], "say": ("make_unique heap'te bir int oluşturur; a onun tek sahibidir.", "make_unique создаёт int в куче; a — его единственный владелец.")},
          {"line": 3, "to": {"a": None}, "new": [("b", "unique_ptr<int>", None, {"to": "heap#1"})], "mark": {"a": "moved"}, "say": ("std::move sahipliği b'ye devreder; a artık nullptr. Kopya yok, nesne tek!", "std::move передаёт владение b; a теперь nullptr. Копии нет, объект один!")},
          {"line": 4, "mark": {"b": "deref-from", "heap#1": "deref"}, "out": "5", "say": ("*b ile değer okunur: 5.", "Через *b читаем значение: 5.")},
          {"line": 5, "del": ["a", "b"], "keep": {"heap#1": "auto"}, "say": ("Kapsam bitince b yok olur ve int'i kendisi siler. delete yazmadık, sızıntı yok!", "Когда область заканчивается, b уничтожается и сам удаляет int. Мы не писали delete — утечки нет!")},
          {"line": 5, "del": ["heap#1"], "say": ("Heap temiz. RAII: kaynak, sahibinin ömrüne bağlıdır.", "Куча чистая. RAII: ресурс привязан ко времени жизни владельца.")},
      ]),
    S("c17", 2, ("shared_ptr: paylaşılan sahiplik", "shared_ptr: совместное владение"), "memory",
      ["auto s1 = std::make_shared<int>(9);", "{", "    auto s2 = s1;", "    std::cout << s1.use_count();", "}", "std::cout << s1.use_count();"],
      [
          {"line": 1, "new": [("heap#1", ("int · 1 sahip", "int · 1 владелец"), 9, {"heap": True, "size": 4}), ("s1", "shared_ptr<int>", None, {"to": "heap#1"})], "say": ("make_shared int'i oluşturur; sayaç 1: tek sahip s1.", "make_shared создаёт int; счётчик 1: единственный владелец s1.")},
          {"line": 3, "new": [("s2", "shared_ptr<int>", None, {"to": "heap#1"})], "type": {"heap#1": ("int · 2 sahip", "int · 2 владельца")}, "say": ("s2 = s1 kopyalanınca iki ok aynı nesneyi gösterir; sayaç 2.", "После копирования s2 = s1 две стрелки указывают на один объект; счётчик 2.")},
          {"line": 4, "out": "2", "mark": {"heap#1": "active"}, "say": ("use_count() 2 der.", "use_count() показывает 2.")},
          {"line": 5, "del": ["s2"], "type": {"heap#1": ("int · 1 sahip", "int · 1 владелец")}, "say": ("s2 kapsamdan çıkar; nesne silinmez, yalnızca sayaç 1'e düşer.", "s2 выходит из области видимости; объект не удаляется, счётчик падает до 1.")},
          {"line": 6, "out": "1", "say": ("Son sahip s1 yok olduğunda int otomatik silinecek.", "Когда исчезнет последний владелец s1, int удалится автоматически.")},
      ]),

    # ——— 18. Kalıtım ve polimorfizm ———
    S("c18", 0, ("Kalıtım: miras alınan üyeler", "Наследование: унаследованные члены"), "object",
      ["struct Hayvan {", "    std::string ad;", '    virtual std::string ses() const { return "..."; }', "};", "struct Kedi : Hayvan {", '    std::string ses() const override { return "Miyav"; }', "};", 'Kedi luna; luna.ad = "Luna";', 'std::cout << luna.ad << ": " << luna.ses();'],
      [
          {"line": 1, "say": ("Hayvan taban sınıftır: bir ad alanı ve virtual bir ses() metodu var.", "Hayvan — базовый класс: у него есть поле ad и virtual-метод ses().")},
          {"line": 5, "new": [("Kedi : Hayvan", "", "", {"region": "blueprint", "kind": "struct", "fields": [("std::string ad   ← Hayvan", "std::string ad   ← Hayvan")], "methods": ['ses() override → "Miyav"']})], "say": ("Kedi : Hayvan, Hayvan'ın her şeyini devralır ve ses()'i kendi sürümüyle değiştirir (override).", "Kedi : Hayvan наследует всё от Hayvan и заменяет ses() своей версией (override).")},
          {"line": 8, "new": [("luna.ad", "string", '"Luna"', {"region": "object", "frame": "luna"})], "say": ("luna bir Kedi nesnesi; ad alanı Hayvan'dan miras geldi.", "luna — объект Kedi; поле ad унаследовано от Hayvan.")},
          {"line": 9, "out": "Luna: Miyav", "mark": {"luna.ad": "active"}, "say": ('luna.ses() Kedi\'nin sürümünü çalıştırır: "Miyav".', 'luna.ses() вызывает версию Kedi: "Miyav".')},
      ], class_name="Kedi"),
    S("c18", 2, ("virtual: doğru metodu seç", "virtual: выбор нужного метода"), "memory",
      ["std::vector<std::unique_ptr<Hayvan>> liste;", "liste.push_back(std::make_unique<Kedi>());", "liste.push_back(std::make_unique<Kopek>());", "for (const auto& h : liste)", '    std::cout << h->ses() << " ";'],
      [
          {"line": 1, "say": ("Liste, taban sınıf Hayvan'a işaretçiler tutacak.", "Список будет хранить указатели на базовый класс Hayvan.")},
          {"line": 2, "new": [("Kedi", "Kedi : Hayvan", "🐱", {"heap": True}), ("liste[0]", "Hayvan*", None, {"to": "Kedi"})], "say": ("Heap'te bir Kedi oluşur; işaretçinin türü Hayvan ama gösterdiği nesne Kedi.", "В куче создаётся Kedi; тип указателя — Hayvan, но объект — Kedi.")},
          {"line": 3, "new": [("Kopek", "Kopek : Hayvan", "🐶", {"heap": True}), ("liste[1]", "Hayvan*", None, {"to": "Kopek"})], "say": ("Aynı listeye bir Kopek de eklenir.", "В тот же список добавляется Kopek.")},
          {"line": 5, "mark": {"liste[0]": "deref-from", "Kedi": "deref"}, "out": "Miyav ", "say": ('ses() virtual olduğu için gerçek nesneye bakılır: Kedi::ses → "Miyav".', 'Так как ses() — virtual, смотрим на реальный объект: Kedi::ses → "Miyav".')},
          {"line": 5, "mark": {"liste[1]": "deref-from", "Kopek": "deref"}, "out": "Hav ", "say": ('Aynı satır, bu kez Kopek::ses → "Hav". Buna polimorfizm denir.', 'Та же строка, теперь Kopek::ses → "Hav". Это и есть полиморфизм.')},
      ]),

    # ——— 19. Şablonlar ve lambda ———
    S("c19", 0, ("Şablondan kod üretimi", "Генерация кода из шаблона"), "flow",
      ["template <typename T>", "T enKucuk(T a, T b) { return a < b ? a : b; }", "std::cout << enKucuk(3, 7);", "std::cout << enKucuk(2.5, 1.5);"],
      [
          {"line": 1, "stage": 0, "payload": "T = ?", "say": ("Şablon bir kalıptır; T henüz belli değil, tek başına kod üretmez.", "Шаблон — это заготовка; T пока неизвестен, сам по себе код не создаётся.")},
          {"line": 3, "stage": 1, "payload": "(3, 7)", "say": ("enKucuk(3, 7) çağrısında derleyici argümanlara bakar: T = int.", "При вызове enKucuk(3, 7) компилятор смотрит на аргументы: T = int.")},
          {"line": 3, "stage": 2, "payload": "3", "out": "3", "say": ("int için gerçek bir fonksiyon üretilir ve çalışır: 3.", "Для int создаётся настоящая функция и выполняется: 3.")},
          {"line": 4, "stage": 1, "payload": "(2.5, 1.5)", "say": ("İkinci çağrıda T = double.", "Во втором вызове T = double.")},
          {"line": 4, "stage": 3, "payload": "1.5", "out": "1.5", "say": ("Aynı kalıptan double sürümü üretilir: 1.5. Tek kod, birçok tür!", "Из того же шаблона создаётся версия для double: 1.5. Один код — много типов!")},
      ],
      stages=[{"icon": "📐", "label": "template<T>", "sub": ("kalıp", "шаблон")}, {"icon": "⚙️", "label": ("derleyici", "компилятор"), "sub": ("T'yi bulur", "выводит T")},
              {"icon": "🔢", "label": "enKucuk<int>", "sub": "int"}, {"icon": "🔣", "label": "enKucuk<double>", "sub": "double"}]),
    S("c19", 2, ("Lambda ile count_if", "count_if с лямбдой"), "array",
      ["std::vector<int> v{5, 2, 9, 4};", "int esik = 4;", "int buyukler = std::count_if(v.begin(), v.end(),", "    [esik](int x) { return x > esik; });", "std::cout << buyukler;"],
      [
          {"line": 1, "new": [(f"v[{i}]", "int", x, arr(i)) for i, x in enumerate([5, 2, 9, 4])], "say": ("v dört eleman tutar.", "v содержит четыре элемента.")},
          {"line": 2, "new": [("esik", "int", 4)], "say": ("esik = 4; lambda bu değeri [esik] ile kopyalayıp yakalayacak.", "esik = 4; лямбда захватит это значение копией через [esik].")},
          {"line": 4, "new": [("sayac", "int", 1)], "mark": {"v[0]": "active"}, "note": "5 > 4 → true ✓", "say": ("count_if her elemanı lambdaya verir: 5 > 4 doğru, sayılır.", "count_if передаёт каждый элемент в лямбду: 5 > 4 — истина, считаем.")},
          {"line": 4, "mark": {"v[1]": "active"}, "note": "2 > 4 → false", "say": ("2 > 4 yanlış, sayılmaz.", "2 > 4 — ложь, не считаем.")},
          {"line": 4, "set": {"sayac": 2}, "mark": {"v[2]": "active"}, "note": "9 > 4 → true ✓", "say": ("9 > 4 doğru: sayaç 2.", "9 > 4 — истина: счётчик 2.")},
          {"line": 4, "mark": {"v[3]": "active"}, "note": "4 > 4 → false", "say": ("4 > 4 yanlış: eşit olmak büyük olmak değildir.", "4 > 4 — ложь: равно не значит больше.")},
          {"line": 5, "del": ["sayac"], "new": [("buyukler", "int", 2)], "out": "2", "say": ("count_if 2 döndürür; sonuç buyukler'e yazılır.", "count_if возвращает 2; результат записывается в buyukler.")},
      ], array_name="std::vector<int> v"),

    # ——— 20. map ve set ———
    S("c20", 0, ("map: anahtar → değer", "map: ключ → значение"), "array",
      ["std::map<std::string, int> sayac;", 'for (std::string k : {"mama", "kedi", "mama"})', "    sayac[k]++;", 'for (auto& [k, v] : sayac) std::cout << k << " " << v << " ";'],
      [
          {"line": 1, "note": ("boş map", "пустой map"), "say": ("Boş bir map: her kayıt bir anahtar ve bir değer çiftidir.", "Пустой map: каждая запись — пара ключ и значение.")},
          {"line": 3, "new": [('"mama"', "int", 1, key("mama"))], "note": 'k = "mama"', "say": ('sayac["mama"] ilk kez görülünce 0 ile oluşur, ++ ile 1 olur.', 'sayac["mama"] при первом обращении создаётся с 0, а ++ делает 1.')},
          {"line": 3, "new": [('"kedi"', "int", 1, key("kedi"))], "note": 'k = "kedi"', "say": ('map anahtarları hep sıralı tutar: "kedi", "mama"nın önüne yerleşir.', 'map всегда держит ключи упорядоченными: "kedi" встаёт перед "mama".')},
          {"line": 3, "set": {'"mama"': 2}, "note": 'k = "mama"', "say": ('"mama" zaten var: yeni kayıt açılmaz, değeri 2 olur.', '"mama" уже есть: новая запись не создаётся, значение становится 2.')},
          {"line": 4, "out": "kedi 1 mama 2 ", "note": ("anahtar sırasıyla", "в порядке ключей"), "say": ("Dolaşırken çiftler anahtara göre alfabetik sırayla gelir.", "При обходе пары идут в алфавитном порядке ключей.")},
      ], array_name="std::map<std::string, int> sayac", sorted=True),
    S("c20", 2, ("map ile sayma ve arama", "Подсчёт и поиск в map"), "array",
      ["std::map<std::string, int> stok;", 'stok["top"] = 2;', 'stok["mama"] += 3;', 'stok["mama"] += 1;', "for (const auto& [urun, adet] : stok)", '    std::cout << urun << " " << adet << " ";', 'std::cout << stok.count("ip");'],
      [
          {"line": 1, "note": ("stok boş", "stok пуст"), "say": ("Boş bir map oluşturuldu.", "Создан пустой map.")},
          {"line": 2, "new": [('"top"', "int", 2, key("top"))], "say": ('stok["top"] = 2; yeni kayıt: top → 2.', 'stok["top"] = 2; новая запись: top → 2.')},
          {"line": 3, "new": [('"mama"', "int", 3, key("mama"))], "say": ('"mama" yoktu: 0 ile oluşur, += 3 ile 3 olur. Sıralama gereği top\'un önüne geçer.', '"mama" не было: создаётся с 0, += 3 даёт 3. Из-за сортировки встаёт перед top.')},
          {"line": 4, "set": {'"mama"': 4}, "say": ("Aynı anahtar: yalnızca değer güncellenir → 4.", "Тот же ключ: обновляется только значение → 4.")},
          {"line": 6, "mark": {'"mama"': "active"}, "out": "mama 4 ", "say": ("Dolaşma anahtar sırasıyla: önce mama…", "Обход в порядке ключей: сначала mama…")},
          {"line": 6, "mark": {'"top"': "active"}, "out": "top 2 ", "say": ("…sonra top.", "…затем top.")},
          {"line": 7, "out": "0", "note": 'stok.count("ip") = 0', "say": ('count("ip") 0 döner. [] kullansaydık yanlışlıkla boş bir "ip" kaydı oluşurdu.', 'count("ip") возвращает 0. Если бы мы использовали [], случайно создалась бы пустая запись "ip".')},
      ], array_name="std::map<std::string, int> stok", sorted=True),

    # ——— 21. Taşıma semantiği ———
    S("c21", 2, ("Kopya mı, taşıma mı?", "Копия или перемещение?"), "memory",
      ["std::vector<int> a{1, 2, 3};", "std::vector<int> b = a;", "std::vector<int> c = std::move(a);", "std::cout << b.size() << c.size() << a.size();"],
      [
          {"line": 1, "new": [("heap#1", "int[3]", "{1, 2, 3}", {"heap": True, "size": 12}), ("a", "vector<int>", None, {"to": "heap#1"})], "say": ("a'nın elemanları heap'te durur; a yalnızca onları gösteren küçük bir tutamaktır.", "Элементы a лежат в куче; сам a — лишь небольшой дескриптор, который на них указывает.")},
          {"line": 2, "new": [("heap#2", "int[3]", "{1, 2, 3}", {"heap": True, "size": 12}), ("b", "vector<int>", None, {"to": "heap#2"})], "say": ("Kopya: heap'te yeni bir alan ayrılır ve üç eleman tek tek çoğaltılır. Büyük veride pahalıdır.", "Копия: в куче выделяется новая память, и все три элемента дублируются. Для больших данных это дорого.")},
          {"line": 3, "new": [("c", "vector<int>", None, {"to": "heap#1"})], "to": {"a": None}, "mark": {"a": "moved"}, "say": ("std::move ile c, a'nın heap alanını olduğu gibi devralır; hiçbir eleman kopyalanmaz. a boş kalır.", "Через std::move c забирает память a целиком; ни один элемент не копируется. a остаётся пустым.")},
          {"line": 4, "out": "330", "say": ("b ve c üçer eleman tutar, taşınmış a'nın boyutu 0'dır.", "b и c содержат по три элемента, размер перемещённого a — 0.")},
      ]),

    # ——— 22. optional, variant, string_view ———
    S("c22", 2, ("string_view kopyalamaz", "string_view не копирует"), "memory",
      ['std::string metin = "pati kedi";', "std::string_view ilk = std::string_view(metin).substr(0, 4);", "std::string kopya = metin.substr(5);", 'std::cout << ilk << " " << kopya;'],
      [
          {"line": 1, "new": [("heap#1", "char[9]", '"pati kedi"', {"heap": True, "size": 9}), ("metin", "std::string", None, {"to": "heap#1"})], "say": ("metin karakterlerini kendi belleğinde tutar ve onların sahibidir.", "metin хранит символы в своей памяти и владеет ими.")},
          {"line": 2, "new": [("ilk", "string_view · 4", None, {"to": "heap#1", "size": 16})], "say": ("string_view yalnızca bir işaretçi ve bir uzunluktur (4): aynı karakterlere bakar, yeni bellek ayırmaz.", "string_view — это просто указатель и длина (4): он смотрит на те же символы и не выделяет память.")},
          {"line": 3, "new": [("heap#2", "char[4]", '"kedi"', {"heap": True, "size": 4}), ("kopya", "std::string", None, {"to": "heap#2"})], "say": ("std::string::substr ise yeni bir string üretir: karakterler kopyalanır.", "А std::string::substr создаёт новую строку: символы копируются.")},
          {"line": 4, "out": "pati kedi", "mark": {"ilk": "deref-from", "heap#1": "deref"}, "say": ("ilk, metin yaşadığı sürece geçerlidir; metin yok olursa ilk sarkık kalır.", "ilk корректен, пока жив metin; если metin исчезнет, ilk станет висячим.")},
      ]),

    # ——— 23. Concepts ve ranges ———
    S("c23", 2, ("Tembel görünüm hattı", "Ленивый конвейер представлений"), "array",
      ["std::vector<int> v{5, 2, 8, 1, 6};", "auto ciftKare = v | std::views::filter([](int x) { return x % 2 == 0; })", "                  | std::views::transform([](int x) { return x * x; });", 'for (int x : ciftKare) std::cout << x << " ";'],
      [
          {"line": 1, "new": [(f"v[{i}]", "int", x, arr(i)) for i, x in enumerate([5, 2, 8, 1, 6])], "say": ("v beş sayı tutar.", "v содержит пять чисел.")},
          {"line": 3, "note": ("henüz hesap yok", "пока ничего не вычислено"), "say": ("Görünüm hattı kuruldu ama tembeldir: henüz hiçbir eleman işlenmedi, yeni vector de yok.", "Конвейер построен, но он ленивый: ни один элемент ещё не обработан, нового vector нет.")},
          {"line": 4, "mark": {"v[0]": "active"}, "note": "5 → filter ✗", "say": ("Döngü ilk elemanı ister: 5 tek sayı, filter onu geçirmez.", "Цикл запрашивает первый элемент: 5 нечётное, filter его не пропускает.")},
          {"line": 4, "mark": {"v[1]": "active"}, "note": "2 → 2·2 = 4", "out": "4 ", "say": ("2 çift: filter geçirir, transform karesini alır → 4.", "2 чётное: filter пропускает, transform возводит в квадрат → 4.")},
          {"line": 4, "mark": {"v[2]": "active"}, "note": "8 → 64", "out": "64 ", "say": ("8 → 64. Her eleman ancak istendiği anda hesaplanır.", "8 → 64. Каждый элемент вычисляется только в момент запроса.")},
          {"line": 4, "mark": {"v[3]": "active"}, "note": "1 → filter ✗", "say": ("1 tek, atlanır.", "1 нечётное, пропускается.")},
          {"line": 4, "mark": {"v[4]": "active"}, "note": "6 → 36", "out": "36 ", "say": ("6 → 36. v hiç değişmedi; görünüm yalnızca ona baktı.", "6 → 36. v не изменился; представление только смотрело на него.")},
      ], array_name="std::vector<int> v"),

    # ——— 24. Eşzamanlılık ———
    S("c24", 2, ("atomic sayaç ve jthread", "Атомарный счётчик и jthread"), "memory",
      ["std::atomic<int> sayac{0};", "{", "    std::jthread a([&] { for (int i = 0; i < 1000; ++i) ++sayac; });", "    std::jthread b([&] { for (int i = 0; i < 1000; ++i) ++sayac; });", "}   // a ve b burada join eder", "std::cout << sayac.load();"],
      [
          {"line": 1, "new": [("sayac", "atomic<int>", 0)], "say": ("sayac atomiktir: ++ işlemi tek ve bölünmez bir adımdır.", "sayac атомарный: ++ — одна неделимая операция.")},
          {"line": 3, "new": [("a", "jthread", ("çalışıyor", "работает"), {"size": 8})], "set": {"sayac": 412}, "say": ("a başladı ve sayacı artırmaya koyuldu; main beklemeden devam eder.", "Поток a запущен и увеличивает счётчик; main продолжает работу, не дожидаясь.")},
          {"line": 4, "new": [("b", "jthread", ("çalışıyor", "работает"), {"size": 8})], "set": {"sayac": 1187}, "say": ("b de aynı anda artırıyor. Sıra karışık olsa da atomik ++ sayesinde hiçbir artış kaybolmaz.", "b одновременно тоже увеличивает. Порядок перемешан, но благодаря атомарному ++ ни одно увеличение не теряется.")},
          {"line": 5, "set": {"sayac": 2000, "a": ("bitti", "завершён"), "b": ("bitti", "завершён")}, "say": ("Kapsam bitince jthread'ler kendiliğinden join eder: main ikisinin de bitmesini bekler.", "В конце области видимости jthread сами вызывают join: main ждёт завершения обоих.")},
          {"line": 6, "del": ["a", "b"], "out": "2000", "say": ("Sonuç her çalıştırmada 2000. Düz int ile artışlar kaybolabilir ve sonuç değişirdi.", "Результат при каждом запуске — 2000. С обычным int увеличения могли бы теряться, и результат менялся бы.")},
      ]),
]


def scenes_for(chapter_id, lang="tr"):
    lang = "ru" if lang == "ru" else "tr"
    return [build(scene, lang) for scene in SCENES if scene["chapter"] == chapter_id]
