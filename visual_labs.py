"""Safe, deterministic visual simulations for C++ learning labs.

These models visualize concepts only. They never manipulate the host process memory.
"""

LABS = [
    {"id":"variables","title":{"tr":"Değişkenler Ormanı","ru":"Лес переменных"},"xp":12},
    {"id":"conditions","title":{"tr":"Koşullar Köyü","ru":"Деревня условий"},"xp":12},
    {"id":"loops","title":{"tr":"Döngü Zindanı","ru":"Подземелье циклов"},"xp":15},
    {"id":"functions","title":{"tr":"Fonksiyon Dağları","ru":"Горы функций"},"xp":15},
    {"id":"arrays","title":{"tr":"Dizi Bahçesi","ru":"Сад массивов"},"xp":15},
    {"id":"pointers","title":{"tr":"Pointer Geçidi","ru":"Перевал указателей"},"xp":18},
    {"id":"memory","title":{"tr":"Bellek Diyarı","ru":"Мир памяти"},"xp":18},
    {"id":"oop","title":{"tr":"Nesneler Krallığı","ru":"Королевство объектов"},"xp":18},
    {"id":"algorithms","title":{"tr":"Algoritma Arenası","ru":"Арена алгоритмов"},"xp":18},
]

TR = {
    "variables": {"challenge":"Son değeri tahmin et: puan kaç oldu?","input":"başlangıç ve artış miktarı","steps":["int puan için stack üzerinde bir bellek hücresi oluşturuldu.","puan değişkenine başlangıç değeri atandı.","puan güncellendi; aynı değişken hücresi yeni değeri tutuyor."],"final":"Son değer"},
    "conditions": {"challenge":"Program hangi dala girdi? (true / false)","input":"puan ve eşik değeri","steps":["puan ve eşik değerleri belleğe alındı.","puan >= eşik koşulu değerlendirildi.","Koşulun sonucuna göre dal seçildi."],"final":"Seçilen dal"},
    "loops": {"challenge":"Döngü toplam kaç kez çalıştı?","input":"başlangıç, bitiş ve adım","steps":["Döngü sayacı başlangıç değerini aldı."],"iteration":"Sayaç = {value}; yineleme {index}","finished":"Koşul artık doğru değil; döngü sona erdi.","final":"Yineleme sayısı"},
    "functions": {"challenge":"Fonksiyonun döndürdüğü değer nedir?","input":"parametre ve işlem","steps":["Çağıran kapsam parametreyi hazırladı.","Fonksiyon çağrıldı; parametre çağrı yığınına aktarıldı.","Fonksiyon return değeriyle çağırana döndü."],"final":"Dönüş değeri"},
    "arrays": {"challenge":"Seçilen indeksteki değer nedir?","input":"virgülle ayrılmış değerler ve indeks","steps":["Dizi hücreleri ardışık sembolik bellek yuvalarına yerleştirildi.","Her eleman sıfır tabanlı indeks aldı.","Seçilen indeksin hücresi okundu."],"final":"Seçilen değer"},
    "pointers": {"challenge":"Pointer hangi değeri gösteriyor?","input":"iki değer ve hedef değişken","steps":["İki değişken ayrı sembolik bellek hücrelerinde oluşturuldu.","Pointer değişkenine hedef hücrenin sembolik adresi verildi.","Dereference ile işaret edilen değer okundu."],"final":"İşaret edilen değer"},
    "memory": {"challenge":"Simülasyonda hangi bellek durumu oluştu? (freed / leak / dangling)","input":"bellek senaryosu","steps":["Stack değişkeni güvenli simülasyonda oluşturuldu.","Heap tahsisi sembolik bir blok olarak modellendi.","Senaryo sonunda sahiplik ve blok durumu incelendi."],"final":"Bellek durumu"},
    "oop": {"challenge":"Nesnenin seviyesini tahmin et.","input":"nesne adı ve başlangıç seviyesi","steps":["Cat sınıfı özellik ve davranış şablonunu tanımlar.","Luna nesnesi sınıftan örneklendi; kendi alanlarına sahip.","Nesne metodu seviye değerini artırdı."],"final":"Nesnenin seviyesi"},
    "algorithms": {"challenge":"Sıralanmış diziyi yaz.","search":"Hedefin indeksini yaz (yoksa -1).","input":"dizi, algoritma, aranacak değer","steps":["Dizi başlangıç sırasıyla belleğe yüklendi."],"final":"Sonuç"},
}
RU = {
    "variables": {"challenge":"Предскажи итоговое значение: чему равен score?","input":"начальное значение и прибавка","steps":["Для int score создана ячейка в смоделированном стеке.","В переменную score записано начальное значение.","score обновлён; та же ячейка хранит новое значение."],"final":"Итоговое значение"},
    "conditions": {"challenge":"В какую ветвь вошла программа? (true / false)","input":"балл и порог","steps":["Баллы и порог записаны в модель памяти.","Проверено условие score >= threshold.","По результату условия выбрана ветвь."],"final":"Выбранная ветвь"},
    "loops": {"challenge":"Сколько раз выполнился цикл?","input":"начало, конец и шаг","steps":["Счётчик цикла получил начальное значение."],"iteration":"Счётчик = {value}; итерация {index}","finished":"Условие больше не истинно; цикл завершён.","final":"Число итераций"},
    "functions": {"challenge":"Какое значение вернула функция?","input":"параметр и операция","steps":["Вызывающая область подготовила параметр.","Функция вызвана; параметр передан в стек вызовов.","Функция вернулась к вызывающему коду со значением return."],"final":"Возвращённое значение"},
    "arrays": {"challenge":"Какое значение находится по выбранному индексу?","input":"значения через запятую и индекс","steps":["Элементы массива размещены в последовательных условных ячейках.","Каждый элемент получил индекс, начиная с нуля.","Прочитана ячейка выбранного индекса."],"final":"Выбранное значение"},
    "pointers": {"challenge":"На какое значение указывает pointer?","input":"два значения и целевая переменная","steps":["Две переменные созданы в отдельных условных ячейках памяти.","Pointer получил условный адрес целевой ячейки.","Через dereference прочитано значение по адресу."],"final":"Значение по адресу"},
    "memory": {"challenge":"Какое состояние памяти получилось? (freed / leak / dangling)","input":"сценарий памяти","steps":["Переменная стека создана в безопасной модели.","Выделение heap представлено условным блоком.","Проверено владение блоком в конце сценария."],"final":"Состояние памяти"},
    "oop": {"challenge":"Какой уровень у объекта?","input":"имя объекта и начальный уровень","steps":["Класс Cat задаёт шаблон полей и поведения.","Объект Luna создан из класса и имеет собственные поля.","Метод объекта увеличил уровень."],"final":"Уровень объекта"},
    "algorithms": {"challenge":"Напиши отсортированный массив.","search":"Напиши индекс цели (или -1, если её нет).","input":"массив, алгоритм и цель поиска","steps":["Массив загружен в память в исходном порядке."],"final":"Результат"},
}


def _integer(raw, key, default, minimum=-1000, maximum=1000):
    try: value = int(raw.get(key, default))
    except (TypeError, ValueError): value = default
    return max(minimum, min(maximum, value))


def _base_cells(values, active=()):
    active = set(active)
    return [{"name": f"values[{i}]", "address": f"0x{0x1000+4*i:04X}", "value": value, "type": "int", "region": "array", "status": "active" if i in active else ""} for i, value in enumerate(values)]


def simulate(lab_id, raw, language="tr"):
    if lab_id not in {lab["id"] for lab in LABS}: raise ValueError("Unknown lab")
    if not isinstance(raw, dict): raw = {}
    copy = (TR if language == "tr" else RU)[lab_id]
    steps, final, answer, cells = [], "", "", []
    custom_frames = []
    if lab_id == "variables":
        start, add = _integer(raw,"start",3), _integer(raw,"add",4)
        steps = [copy["steps"][0], f"{copy['steps'][1]} ({start})", copy["steps"][2] + f" ({start} + {add} = {start+add})"]
        cells = [{"name":"puan / score","address":"0x1000","value":start+add,"type":"int","region":"stack"}]
        answer = str(start + add); final = f"{copy['final']}: {answer}"
    elif lab_id == "conditions":
        score, threshold = _integer(raw,"score",72,0,100), _integer(raw,"threshold",50,0,100)
        passed = score >= threshold; branch = "true" if passed else "false"
        steps = [copy["steps"][0], f"{copy['steps'][1]} ({score} >= {threshold} → {branch})", copy["steps"][2]]
        cells = [{"name":"score","address":"0x1000","value":score,"type":"int","region":"stack"},{"name":"threshold","address":"0x1004","value":threshold,"type":"int","region":"stack"}]
        answer = branch; final = f"{copy['final']}: {branch}"
    elif lab_id == "loops":
        start,end,step = _integer(raw,"start",1,-100,100),_integer(raw,"end",5,-100,100),_integer(raw,"step",1,1,20)
        values=list(range(start,end+1,step))[:30] if start<=end else []
        steps=[copy["steps"][0]]+[copy.get("iteration","").format(value=value,index=i+1) for i,value in enumerate(values)]+[copy.get("finished","")]
        cells=[{"name":"i","address":"0x1000","value":values[-1] if values else start,"type":"int","region":"stack"}]
        answer=str(len(values));final=f"{copy['final']}: {answer}"
    elif lab_id == "functions":
        param=_integer(raw,"param",6); op=raw.get("operation","double")
        result=param*param if op=="square" else param+3 if op=="add3" else param*2
        steps=[copy["steps"][0],f"{copy['steps'][1]} ({param})",f"{copy['steps'][2]} ({result})"]
        cells=[{"name":"param","address":"stack:call#1","value":param,"type":"int","region":"stack"},{"name":"return","address":"stack:caller","value":result,"type":"int","region":"stack"}]
        answer=str(result);final=f"{copy['final']}: {answer}"
    elif lab_id == "arrays":
        raw_values=raw.get("values","3,5,8")
        try: values=[int(x.strip()) for x in str(raw_values).split(",")[:10]] or [0]
        except ValueError: values=[3,5,8]
        index=_integer(raw,"index",1,0,9); index=min(index,len(values)-1)
        cells=[{"name":f"numbers[{i}]","address":f"0x{0x1000+4*i:04X}","value":value,"type": "int","region":"stack"} for i,value in enumerate(values)]
        steps=[copy["steps"][0],copy["steps"][1],f"{copy['steps'][2]} (index {index})"]
        answer=str(values[index]);final=f"{copy['final']}: {answer}"
    elif lab_id == "pointers":
        a,b=_integer(raw,"a",10),_integer(raw,"b",20);target="b" if raw.get("target")=="b" else "a";val=b if target=="b" else a;address="0x1004" if target=="b" else "0x1000"
        cells=[{"name":"a","address":"0x1000","value":a,"type":"int","region":"stack"},{"name":"b","address":"0x1004","value":b,"type":"int","region":"stack"},{"name":"ptr","address":"0x2000","value":"&"+target+" → "+address,"type":"int*","region":"stack","points_to":target}]
        steps=[copy["steps"][0],f"{copy['steps'][1]} (&{target} = {address})",f"{copy['steps'][2]} (*ptr = {val})"]
        answer=str(val);final=f"{copy['final']}: {answer}"
    elif lab_id == "memory":
        scenario=raw.get("scenario","freed")
        if scenario in ("stack","queue","linked_list","dynamic"):
            if scenario=="stack":
                challenge="pop sonrası stack'in en üstünde hangi değer kalır? (LIFO)" if language=="tr" else "Какое значение останется сверху после pop? (LIFO)"
                steps=["Stack boş." if language=="tr" else "Stack пуст.","push(4): öğe tepeye eklendi." if language=="tr" else "push(4): элемент добавлен наверх.","push(9): öğe tepeye eklendi." if language=="tr" else "push(9): элемент добавлен наверх.","pop(): 9 ilk çıkar (LIFO)." if language=="tr" else "pop(): 9 удаляется первым (LIFO)."]
                states=[[],[4],[4,9],[4]];answer="LIFO";final="Stack sonucu: 4 · LIFO" if language=="tr" else "Результат stack: 4 · LIFO"
                custom_frames=[[{"name":f"stack[{i}]","address":f"stack:{i}","value":value,"type":"int","region":"stack"} for i,value in enumerate(items)] or [{"name":"stack","address":"stack frame","value":"empty","type":"stack","region":"stack"}] for items in states]
            elif scenario=="queue":
                challenge="İlk dequeue hangi değeri çıkarır? (FIFO)" if language=="tr" else "Какое значение первым вернёт dequeue? (FIFO)"
                steps=["Queue boş." if language=="tr" else "Очередь пуста.","enqueue(4), enqueue(9): arka uca eklendi." if language=="tr" else "enqueue(4), enqueue(9): добавлены в конец.","dequeue(): ilk eklenen 4 çıkar (FIFO)." if language=="tr" else "dequeue(): первым удаляется 4 (FIFO)."]
                states=[[],[4,9],[9]];answer="FIFO";final="Queue sonucu: 9 · FIFO" if language=="tr" else "Результат queue: 9 · FIFO"
                custom_frames=[[{"name":f"queue[{i}]","address":f"heap:node{i}","value":value,"type":"int","region":"queue"} for i,value in enumerate(items)] or [{"name":"queue","address":"heap","value":"empty","type":"queue","region":"heap"}] for items in states]
            elif scenario=="linked_list":
                challenge="Bağlantılı liste zincirini yaz." if language=="tr" else "Запиши цепочку связного списка."
                steps=["İlk düğüm heap alanında oluşturuldu." if language=="tr" else "Первый узел создан в heap.","İkinci düğüm oluşturuldu; next bağlantısı kuruldu." if language=="tr" else "Создан второй узел; связь next установлена.","Son düğüm nullptr ile bitti." if language=="tr" else "Последний узел заканчивается nullptr."]
                answer="4 → 9 → nullptr";final=f"Linked list: {answer}"
                custom_frames=[[{"name":"head","address":"stack:head","value":"heap:node1","type":"Node*","region":"stack"}],[{"name":"node1","address":"heap:node1","value":"4 · next → node2","type":"Node","region":"heap"},{"name":"node2","address":"heap:node2","value":"9 · next → nullptr","type":"Node","region":"heap"}],[{"name":"head","address":"stack:head","value":"node1 → node2 → nullptr","type":"Node*","region":"stack"}]]
            else:
                challenge="new ile ayrılan blok ne zaman serbest olur? (freed)" if language=="tr" else "Когда освобождается блок, выделенный new? (freed)"
                steps=["Stack pointer henüz heap'i göstermiyor." if language=="tr" else "Указатель stack ещё не ссылается на heap.","new ile sembolik heap bloğu ayrıldı." if language=="tr" else "Символический блок heap выделен через new.","delete ile blok serbest bırakıldı; tehlikeli erişim yok." if language=="tr" else "Блок освобождён через delete; опасного доступа нет."]
                answer="freed";final="Heap bloğu serbest" if language=="tr" else "Блок heap освобождён"
                custom_frames=[[{"name":"ptr","address":"stack:ptr","value":"nullptr","type":"int*","region":"stack"}],[{"name":"ptr","address":"stack:ptr","value":"heap:0","type":"int*","region":"stack"},{"name":"*ptr","address":"heap:0","value":42,"type":"int","region":"heap","status":"allocated"}],[{"name":"ptr","address":"stack:ptr","value":"nullptr","type":"int*","region":"stack"},{"name":"heap block","address":"heap:0","value":"freed","type":"int","region":"heap","status":"freed"}]]
            steps=[copy["steps"][0]]+steps
            custom_frames=[[{"name":"scenario","address":"safe simulation","value":scenario,"type":"memory model","region":"simulated"}]]+custom_frames
            cells=custom_frames[-1]
        else:
            if scenario not in ("freed","leak","dangling"):scenario="freed"
            status=scenario
            details={"freed":("delete ile blok serbest bırakıldı.","Блок освобождён через delete."),"leak":("İşaretçi kayboldu; heap bloğu serbest bırakılmadı (leak).","Указатель потерян, блок heap не освобождён (leak)."),"dangling":("Blok serbest bırakıldı fakat eski işaretçi kaldı (dangling).","Блок освобождён, но старый указатель остался (dangling).")}[scenario]
            steps=[copy["steps"][0],copy["steps"][1],copy["steps"][2]+" "+details[0 if language=="tr" else 1]]
            cells=[{"name":"heap block","address":"heap:0","value":"allocated" if scenario!="freed" else "freed","type":"simulated int","region":"heap","status":status}]
            answer=status;final=f"{copy['final']}: {status}"
            challenge=copy["challenge"]
    elif lab_id == "algorithms":
        try: values=[int(x.strip()) for x in str(raw.get("values","5,2,4,1")).split(",")[:10]] or [0]
        except ValueError: values=[5,2,4,1]
        operation=raw.get("algorithm","bubble_sort");target=_integer(raw,"target",4);current=list(values);frames_values=[list(values)];steps=[copy["steps"][0]];frame_marks=[()];custom_frames=[]
        line_now=[0];frame_lines=[0]
        def record(text, active=()):
            steps.append(text);frames_values.append(list(current));frame_marks.append(tuple(active));frame_lines.append(line_now[0])
        if operation in ("linear_search", "binary_search"):
            if operation=="binary_search":
                current.sort();frames_values[0]=list(current)
                line_now[0]=1;record(("Binary search için değerler küçükten büyüğe sıralandı." if language=="tr" else "Для binary search значения отсортированы по возрастанию."))
                low,high,found=0,len(current)-1,-1
                while low<=high:
                    middle=(low+high)//2
                    line_now[0]=4;record((f"{low}..{high} aralığının ortası {middle}: {current[middle]} hedefle karşılaştırılıyor." if language=="tr" else f"Середина диапазона {low}..{high} — индекс {middle}: сравнение с целью."), (middle,))
                    if current[middle]==target: found=middle;break
                    if current[middle]<target: low=middle+1
                    else: high=middle-1
                complexity="O(log n)"
            else:
                found=-1
                for index,value in enumerate(current):
                    line_now[0]=2;record((f"İndeks {index}: {value} hedefle karşılaştırıldı." if language=="tr" else f"Индекс {index}: значение {value} сравнено с целью."), (index,))
                    if value==target: found=index;break
                complexity="O(n)"
            answer=str(found);challenge=copy["search"];final=f"{copy['final']}: {answer} · {('Zaman' if language=='tr' else 'Время')}: {complexity}"
        elif operation=="recursion":
            n=_integer(raw,"target",4,0,7);result=1
            challenge=f"factorial({n}) sonucu nedir?" if language=="tr" else f"Чему равно factorial({n})?"
            custom_frames=[];steps=[copy["steps"][0]]
            for value in range(n,0,-1):
                steps.append((f"factorial({value}) çağrıldı; çağrı yığınına eklendi." if language=="tr" else f"Вызвана factorial({value}); кадр добавлен в стек."))
                custom_frames.append([{"name":f"factorial({x})","address":f"stack:call#{n-x+1}","value":"waiting","type":"call frame","region":"stack"} for x in range(n,value-1,-1)])
            steps.append(("Temel durum: factorial(0) = 1." if language=="tr" else "Базовый случай: factorial(0) = 1."));custom_frames.append([{"name":"factorial(0)","address":f"stack:call#{n+1}","value":1,"type":"return","region":"stack"}])
            for value in range(1,n+1):
                result*=value;steps.append((f"factorial({value}) döndü: {result}." if language=="tr" else f"factorial({value}) вернула: {result}."))
                remaining=list(range(n,max(0,value-1),-1));custom_frames.append([{"name":f"factorial({x})","address":f"stack:call#{n-x+1}","value":result if x==value else "returning","type":"call frame","region":"stack"} for x in remaining])
            answer=str(result);challenge=copy["challenge"];complexity="O(n) time · O(n) stack";final=f"{copy['final']}: {answer} · {complexity}"
        else:
            operation=operation if operation in ("bubble_sort","selection_sort","insertion_sort") else "bubble_sort"
            if operation=="bubble_sort":
                for end in range(len(current)-1,0,-1):
                    swapped=False
                    for index in range(end):
                        left,right=current[index],current[index+1];line_now[0]=3;record((f"{left} ve {right} karşılaştırıldı." if language=="tr" else f"Сравнены {left} и {right}."), (index,index+1))
                        if left>right: current[index],current[index+1]=right,left;swapped=True;line_now[0]=4;record(("Komşu değerler yer değiştirdi." if language=="tr" else "Соседние значения переставлены."), (index,index+1))
                    if not swapped:break
            elif operation=="selection_sort":
                for start in range(len(current)-1):
                    minimum=start
                    for index in range(start+1,len(current)):
                        line_now[0]=3;record((f"En küçük değer aranıyor: {current[index]} ile {current[minimum]} karşılaştırıldı." if language=="tr" else f"Поиск минимума: {current[index]} сравнено с {current[minimum]}."), (minimum,index))
                        if current[index]<current[minimum]:minimum=index
                    if minimum!=start:
                        current[start],current[minimum]=current[minimum],current[start];line_now[0]=4;record((f"{current[start]} doğru sıraya taşındı." if language=="tr" else f"{current[start]} перемещено на своё место."), (start,minimum))
            else:
                for index in range(1,len(current)):
                    key=current[index];cursor=index-1
                    line_now[0]=2;record((f"{key} için doğru yer aranıyor." if language=="tr" else f"Поиск места для {key}."), (index,))
                    while cursor>=0 and current[cursor]>key:
                        current[cursor+1]=current[cursor];line_now[0]=3;record((f"{current[cursor]} bir hücre sağa kaydı." if language=="tr" else f"{current[cursor]} сдвинуто на одну ячейку вправо."), (cursor,cursor+1));cursor-=1
                    current[cursor+1]=key;line_now[0]=4;record((f"{key}, indeks {cursor+1} konumuna yerleştirildi." if language=="tr" else f"{key} вставлено по индексу {cursor+1}."), (cursor+1,))
            answer=", ".join(str(value) for value in current);challenge=copy["challenge"];complexity="O(n²) worst case";final=f"{copy['final']}: {answer} · {('Zaman' if language=='tr' else 'Время')}: {complexity}"
        cells=_base_cells(current)
    else:
        name=str(raw.get("name","Luna"))[:20] or "Luna";level=_integer(raw,"level",1,1,99)+1
        steps=[copy["steps"][0],f"{copy['steps'][1]} ({name})",f"{copy['steps'][2]} ({level})"]
        cells=[{"name":name+".level","address":"object:Luna","value":level,"type":"int","region":"object"}]
        answer=str(level);final=f"{copy['final']}: {answer}"
    frames = []
    for i, text in enumerate(steps):
        frame_cells = [dict(cell) for cell in cells]
        if lab_id == "variables" and i < 2:
            frame_cells[0]["value"] = start
        elif lab_id == "conditions":
            if i < 2: frame_cells.append({"name":"condition","address":"control flow","value":"checking" if i else "pending","type":"bool","region":"branch"})
            else: frame_cells.append({"name":"condition","address":"control flow","value":"true" if score >= threshold else "false","type":"bool","region":"branch"})
        elif lab_id == "loops":
            if i == 0: frame_cells[0]["value"] = start
            elif i <= len(values): frame_cells[0]["value"] = values[i-1]
            else: frame_cells[0]["value"] = (values[-1]+step) if values else start
        elif lab_id == "functions":
            if i == 0: frame_cells = [{"name":"param","address":"stack:caller","value":param,"type":"int","region":"stack"}]
            elif i == 1: frame_cells = [dict(cells[0])]
        elif lab_id == "arrays" and i < 2:
            frame_cells = frame_cells[:max(1, min(len(frame_cells), 1 if i == 0 else len(frame_cells)))]
        elif lab_id == "pointers" and i < 2:
            frame_cells = frame_cells[:2] if i == 0 else frame_cells
        elif lab_id == "memory":
            if custom_frames:
                frame_cells=custom_frames[min(i,len(custom_frames)-1)]
            elif i == 0: frame_cells[0]["value"] = "not allocated"
            elif i == 1: frame_cells[0]["value"] = "allocated"
        elif lab_id == "oop":
            if i == 0: frame_cells = [{"name":"Cat","address":"class blueprint","value":"class definition","type":"class","region":"blueprint"}]
            elif i == 1: frame_cells[0]["value"] = "level 1"
        elif lab_id == "algorithms":
            if custom_frames:
                frame_cells=custom_frames[min(max(0,i-1),len(custom_frames)-1)] if i else []
            else:
                values_at_step=frames_values[min(i,len(frames_values)-1)]
                frame_cells=_base_cells(values_at_step, frame_marks[min(i,len(frame_marks)-1)])
        frames.append({"index":i,"text":text,"cells":frame_cells})
    prompt=challenge if lab_id in ("algorithms","memory") else copy["challenge"]
    result={"lab_id":lab_id,"steps":frames,"cells":cells,"final":final,"challenge":{"prompt":prompt,"expected_type":"short answer"},"answer_key":answer}
    return _annotate(lab_id, raw, language, result, locals().get("frame_lines"), locals().get("operation"))


def public_result(result):
    """Remove the answer key before sending a simulation to the UI."""
    return {key:value for key,value in result.items() if key!="answer_key"}


def _cell(name, value, region="stack", address="", type_="int", **extra):
    cell = {"name": name, "address": address, "value": value, "type": type_, "region": region}
    cell.update(extra)
    return cell


def _annotate(lab_id, raw, language, result, frame_lines=None, operation=None):
    """Add what the animated lab needs: the C++ code being run, the line each step is on,
    the console output so far, and richer memory cells (frames, heap blocks, pointer links)."""
    tr = language == "tr"
    steps = result["steps"]
    count = len(steps)
    code, lines, outputs, visual = [], [0] * count, [""] * count, lab_id

    def frames(cell_lists):
        for i, cells in enumerate(cell_lists[:count]):
            steps[i]["cells"] = cells

    if lab_id == "variables":
        start, add = _integer(raw, "start", 3), _integer(raw, "add", 4)
        code = [f"int puan = {start};", f"puan = puan + {add};", "std::cout << puan;"]
        lines = [1, 1, 2]
        frames([[_cell("puan", "?", address="0x1000", status="new", frame="main")],
                [_cell("puan", start, address="0x1000", frame="main")],
                [_cell("puan", start + add, address="0x1000", status="changed", frame="main")]])
        outputs = ["", "", ""]
        visual = "memory"
    elif lab_id == "conditions":
        score, threshold = _integer(raw, "score", 72, 0, 100), _integer(raw, "threshold", 50, 0, 100)
        passed = score >= threshold
        code = [f"int score = {score}, threshold = {threshold};", "if (score >= threshold) {", '    std::cout << "true";', "} else {", '    std::cout << "false";', "}"]
        lines = [1, 2, 3 if passed else 5]
        outputs = ["", "", "true" if passed else "false"]
        visual = "branch"
        for i, step in enumerate(steps):
            step["branch"] = {"left": score, "right": threshold, "op": ">=", "state": "pending" if i == 0 else "checking" if i == 1 else ("true" if passed else "false")}
    elif lab_id == "loops":
        start, end, step_ = _integer(raw, "start", 1, -100, 100), _integer(raw, "end", 5, -100, 100), _integer(raw, "step", 1, 1, 20)
        values = list(range(start, end + 1, step_))[:30] if start <= end else []
        code = [f"for (int i = {start}; i <= {end}; i += {step_}) {{", '    std::cout << i << " ";', "}"]
        lines = [1] + [2] * len(values) + [1]
        printed = []
        for i in range(count):
            if 1 <= i <= len(values):
                printed.append(str(values[i - 1]))
            outputs[i] = " ".join(printed)
            steps[i]["loop"] = {"values": values, "done": min(max(i, 0), len(values)), "finished": i == count - 1}
        visual = "loop"
    elif lab_id == "functions":
        param = _integer(raw, "param", 6)
        op = raw.get("operation", "double")
        expr = "x * x" if op == "square" else "x + 3" if op == "add3" else "x * 2"
        res = param * param if op == "square" else param + 3 if op == "add3" else param * 2
        code = ["int f(int x) {", f"    return {expr};", "}", "int main() {", f"    int sonuc = f({param});", "    std::cout << sonuc;", "}"]
        lines = [5, 2, 6]
        frames([[_cell("sonuc", "?", frame="main()", address="0x2000")],
                [_cell("sonuc", "?", frame="main()", address="0x2000"), _cell("x", param, frame=f"f({param})", address="0x1FF0", status="new")],
                [_cell("sonuc", res, frame="main()", address="0x2000", status="changed")]])
        outputs = ["", "", str(res)]
        visual = "calls"
    elif lab_id == "arrays":
        try:
            values = [int(x.strip()) for x in str(raw.get("values", "3,5,8")).split(",")[:10]] or [0]
        except ValueError:
            values = [3, 5, 8]
        index = min(_integer(raw, "index", 1, 0, 9), len(values) - 1)
        code = ["int numbers[] = {" + ", ".join(map(str, values)) + "};", f"// numbers[0] … numbers[{len(values) - 1}]", f"std::cout << numbers[{index}];"]
        lines = [1, 2, 3]
        base = [_cell(f"numbers[{i}]", v, "array", f"0x{0x1000 + 4 * i:04X}", index=i) for i, v in enumerate(values)]
        frames([[dict(c, status="new") for c in base], [dict(c, status="indexed") for c in base], [dict(c, status="active" if c["index"] == index else "") for c in base]])
        outputs = ["", "", str(values[index])]
        visual = "array"
    elif lab_id == "pointers":
        a, b = _integer(raw, "a", 10), _integer(raw, "b", 20)
        target = "b" if raw.get("target") == "b" else "a"
        address = "0x1004" if target == "b" else "0x1000"
        code = [f"int a = {a}, b = {b};", f"int* ptr = &{target};", "std::cout << *ptr;"]
        lines = [1, 2, 3]
        A = _cell("a", a, address="0x1000", frame="main")
        B = _cell("b", b, address="0x1004", frame="main")
        frames([[dict(A, status="new"), dict(B, status="new")],
                [A, B, _cell("ptr", address, address="0x1008", type_="int*", frame="main", points_to=target, status="new")],
                [dict(A, status="deref" if target == "a" else ""), dict(B, status="deref" if target == "b" else ""), _cell("ptr", address, address="0x1008", type_="int*", frame="main", points_to=target, status="deref-from")]])
        outputs = ["", "", str(b if target == "b" else a)]
        visual = "memory"
    elif lab_id == "memory":
        scenario = raw.get("scenario", "freed")
        comment = (lambda t, r: t if tr else r)
        ptr0 = _cell("ptr", "nullptr", address="0x7FF0", type_="int*", frame="main")
        ptr1 = _cell("ptr", "0xA000", address="0x7FF0", type_="int*", frame="main", points_to="heap#1")
        block = _cell("heap#1", 42, "heap", "0xA000", status="allocated")
        if scenario in ("freed", "leak", "dangling"):
            visual = "memory"
            if scenario == "freed":
                code = ["int* ptr = new int(42);", "std::cout << *ptr;", "delete ptr; ptr = nullptr;"]
                lines = [1, 1, 3]
                frames([[ptr0], [ptr1, block], [ptr0, dict(block, value="freed", status="freed")]])
            elif scenario == "leak":
                code = ["int* ptr = new int(42);", "ptr = nullptr;  // " + comment("adres kayboldu", "адрес потерян"), "// " + comment("delete yok → sızıntı", "нет delete → утечка")]
                lines = [1, 1, 2]
                frames([[ptr0], [ptr1, block], [ptr0, dict(block, status="leak")]])
            else:
                code = ["int* ptr = new int(42);", "delete ptr;", "std::cout << *ptr;  // " + comment("tanımsız davranış!", "неопределённое поведение!")]
                lines = [1, 1, 3]
                frames([[ptr0], [ptr1, block], [dict(ptr1, status="dangling"), dict(block, value="freed", status="freed")]])
        elif scenario == "stack":
            code = ["std::stack<int> s;", "s.push(4);", "s.push(9);", "s.pop();"]
            lines = [0, 1, 2, 3, 4]
            states = [[], [], [4], [4, 9], [4]]
            frames([[_cell(f"s[{i}]", v, "lifo", f"top-{len(items) - 1 - i}", item=f"v{i}") for i, v in enumerate(items)] for items in states])
            visual = "lifo"
        elif scenario == "queue":
            code = ["std::queue<int> q;", "q.push(4); q.push(9);", "q.pop();"]
            lines = [0, 1, 2, 3]
            frames([[], [], [_cell("q[0]", 4, "fifo", "front", item="v4"), _cell("q[1]", 9, "fifo", "back", item="v9")], [_cell("q[0]", 9, "fifo", "front", item="v9")]])
            visual = "fifo"
        elif scenario == "linked_list":
            code = ["Node* head = new Node{4};", "head->next = new Node{9};", "// head → 4 → 9 → nullptr"]
            lines = [0, 1, 2, 3]
            head0 = _cell("head", "nullptr", address="0x7FF0", type_="Node*", frame="main")
            head1 = _cell("head", "0xA000", address="0x7FF0", type_="Node*", frame="main", points_to="node1")
            n1 = _cell("node1", 4, "heap", "0xA000", type_="Node", next="nullptr")
            n1b = dict(n1, next="0xA010", points_to="node2")
            n2 = _cell("node2", 9, "heap", "0xA010", type_="Node", next="nullptr", status="new")
            frames([[head0], [head1, dict(n1, status="new")], [head1, n1b, n2], [dict(head1, status="active"), dict(n1b, status="active"), dict(n2, status="active")]])
            visual = "memory"
        else:
            code = ["int* ptr = nullptr;", "ptr = new int(42);", "delete ptr; ptr = nullptr;"]
            lines = [0, 1, 2, 3]
            frames([[], [ptr0], [ptr1, block], [ptr0, dict(block, value="freed", status="freed")]])
            visual = "memory"
    elif lab_id == "oop":
        name = str(raw.get("name", "Luna"))[:20] or "Luna"
        start = _integer(raw, "level", 1, 1, 99)
        code = ["class Cat {", "public:", "    std::string name; int level;", "    void levelUp() { ++level; }", "};", f'Cat {name.lower() or "luna"}{{"{name}", {start}}};', f"{name.lower() or 'luna'}.levelUp();"]
        lines = [1, 6, 7]
        blueprint = _cell("Cat", "class", "blueprint", "", "class", fields=["name", "level"], methods=["levelUp()"])
        frames([[blueprint],
                [blueprint, _cell(f"{name}.name", name, "object", "0x3000", "std::string", frame=name, status="new"), _cell(f"{name}.level", start, "object", "0x3020", frame=name, status="new")],
                [blueprint, _cell(f"{name}.name", name, "object", "0x3000", "std::string", frame=name), _cell(f"{name}.level", start + 1, "object", "0x3020", frame=name, status="changed")]])
        visual = "object"
    elif lab_id == "algorithms":
        op = operation or "bubble_sort"
        if op == "recursion":
            n = _integer(raw, "target", 4, 0, 7)
            code = ["int factorial(int n) {", "    if (n == 0) return 1;", "    return n * factorial(n - 1);", "}", f"std::cout << factorial({n});"]
            cell_lists, call_lines = [[]], [5]
            for v in range(n, 0, -1):
                cell_lists.append([_cell("n", x, frame=f"factorial({x})", status="new" if x == v else "") for x in range(n, v - 1, -1)])
                call_lines.append(1 if v == n else 3)
            cell_lists.append([_cell("n", x, frame=f"factorial({x})") for x in range(n, 0, -1)] + [_cell("return", 1, frame="factorial(0)", status="changed")])
            call_lines.append(2)
            acc = 1
            for v in range(1, n + 1):
                acc *= v
                cell_lists.append([_cell("n", x, frame=f"factorial({x})") for x in range(n, v, -1)] + [_cell("return", acc, frame=f"factorial({v})", status="changed")])
                call_lines.append(3)
            frames(cell_lists)
            lines = (call_lines + [3] * count)[:count]
            outputs = [""] * (count - 1) + [str(acc)]
            visual = "calls"
        else:
            codes = {
                "bubble_sort": ["for (int end = n - 1; end > 0; --end)", "  for (int i = 0; i < end; ++i)", "    if (a[i] > a[i + 1])", "      std::swap(a[i], a[i + 1]);"],
                "selection_sort": ["for (int s = 0; s < n - 1; ++s) {", "  int m = s;", "  for (int i = s + 1; i < n; ++i) if (a[i] < a[m]) m = i;", "  std::swap(a[s], a[m]);", "}"],
                "insertion_sort": ["for (int i = 1; i < n; ++i) {", "  int key = a[i], j = i - 1;", "  while (j >= 0 && a[j] > key) { a[j + 1] = a[j]; --j; }", "  a[j + 1] = key;", "}"],
                "linear_search": ["for (int i = 0; i < n; ++i)", "  if (a[i] == target) return i;", "return -1;"],
                "binary_search": ["std::sort(a, a + n);", "int lo = 0, hi = n - 1;", "while (lo <= hi) { int mid = (lo + hi) / 2;", "  if (a[mid] == target) return mid;", "  if (a[mid] < target) lo = mid + 1; else hi = mid - 1; }"],
            }
            code = codes.get(op, codes["bubble_sort"])
            lines = (list(frame_lines or []) + [0] * count)[:count]
            if op in ("linear_search", "binary_search"):
                outputs = [""] * (count - 1) + [result["answer_key"]]
            visual = "bars"
    for i, step in enumerate(steps):
        step["line"] = lines[i] if i < len(lines) else 0
        step["output"] = outputs[i] if i < len(outputs) else ""
    result["code"] = code
    result["visual"] = visual
    return result
