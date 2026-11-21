# C++ Adventure

**[Русский](#русский) · [English](#english) · [Türkçe](README.tr.md)**

![C++ Adventure](docs/screenshots/03-sonra-panel.png)

**Версия / Version:** 0.5.0 · **Платформа / Platform:** Windows 10/11 (64-bit) · **Языки интерфейса / UI languages:** Türkçe, Русский

---

## Русский

Приключенческая игра с котами для изучения C++. Уроки, задания и подсказки — на турецком и русском. Твой код компилируется настоящим компилятором G++ на этом компьютере и запускается в защищённой песочнице. Приложение работает без интернета; интернет нужен только для необязательного ИИ-преподавателя (бесплатного).

### Возможности

- **24 главы, 192 задания:** от первой программы до указателей, умных указателей, наследования, шаблонов и STL. Есть главы по современному C++:
  - семантика перемещения;
  - `optional` / `variant` / `string_view`;
  - концепты и ranges;
  - настоящие `std::thread` / `mutex` / `atomic`.
- **Одинаковая структура глав:** сначала урок (примеры кода, частые ошибки, пошаговые анимации), затем 8 заданий: вопрос, предсказание вывода, исправление ошибки, разминка, практика и босс главы.
- **Настоящая проверка:** код компилируется и запускается со скрытыми тестами. Также проверяется, что нужная конструкция C++ действительно использована. Вывод программ — на английском, тексты заданий — на турецком и русском.
- **Дерево навыков:** главы открываются по предварительным условиям; у закрытой главы видно, что нужно пройти.
- **Редактор кода:** редактор Monaco, подсказки C++, панель ввода и вывода программы. Если Monaco не загрузится, включается простой запасной редактор.
- **Игровые элементы:**
  - XP, уровни и ежедневная серия;
  - достижения;
  - кот-спутник и магазин аксессуаров;
  - гильдия и карта мира;
  - ежедневная арена.
- **Практика:**
  - лаборатория кода;
  - визуальные лаборатории (память, указатели, сортировка, стек вызовов);
  - инструменты разработчика (симуляция Git, CMake и терминала);
  - мастерская многофайловых проектов;
  - режим собеседования, карьера и портфолио.
- **Журнал обучения и статистика:** сильные темы, что стоит повторить, время занятий.
- **Доступность:**
  - всё приложение работает с клавиатуры;
  - при смене раздела фокус переходит на заголовок;
  - размер текста 100–150 % (также Ctrl + плюс / минус);
  - переключатель «Уменьшить анимацию».
- **Профили:** несколько игроков на одном компьютере, у каждого профиля может быть PIN.

### Системные требования

| Компонент | Нужен? | Примечание |
|---|---|---|
| Windows 10 или 11, 64-bit | Да | |
| Microsoft Edge WebView2 Runtime | Да | Есть в Windows 11; если нет, приложение покажет ссылку на бесплатную установку. |
| Компилятор G++ (рекомендуется MSYS2 UCRT64) | Для заданий с кодом | Уроки, вопросы и предсказания работают и без компилятора. |
| Интернет | Нет | Только для необязательного ИИ-преподавателя и первичной установки. |
| Python 3.10+ | Только для запуска из исходников | Установленному приложению Python не нужен. |

### Установка

### Скачать с GitHub и установить

1. **Скачай проект** — один из способов:
   - Открой https://github.com/Ogulcannenes/c-rpg → зелёная кнопка **Code** → **Download ZIP**. Распакуй архив, например в `C:\Games\c-rpg`.
   - Или с Git: `git clone https://github.com/Ogulcannenes/c-rpg.git`
2. **Проще всего:** дважды щёлкни **`kur.bat`** в папке проекта. Он проверит Python 3.10+, компилятор G++, WebView2 и зависимости приложения, спросит и установит недостающее через winget (Python, MSYS2 + G++, WebView2, `.venv`), а затем предложит открыть приложение. `kur.bat -CheckOnly` — только проверка, без установки.

   Шаги 3–5 ниже — то же самое вручную.
3. **Установи Python 3.10+** с https://www.python.org/downloads/ — в установщике отметь **Add python.exe to PATH**.
4. **Установи компилятор G++** — см. шаг 1 ниже (MSYS2).
5. В папке проекта дважды щёлкни **`setup-desktop.bat`** (один раз, нужен интернет), затем **`start-desktop.bat`** — приложение откроется в окне.
6. Хочешь настоящий установщик с ярлыками? Запусти **`build-windows.bat`** — файл установки появится в `dist\` (подробнее в [Сборка из исходников](#сборка-из-исходников)).

Если Windows предупреждает о файлах .bat из интернета: **Подробнее → Выполнить в любом случае**, или правый щелчок по ZIP → Свойства → **Разблокировать** перед распаковкой.

**1. Установи компилятор C++ (один раз)**

1. Скачай и установи MSYS2 с https://www.msys2.org. Путь по умолчанию `C:\msys64` подходит. Можно и так: `winget install MSYS2.MSYS2`.
2. Открой из меню «Пуск» окно **MSYS2 UCRT64** и выполни:

   ```bash
   pacman -S --needed mingw-w64-ucrt-x86_64-gcc
   ```

3. Готово. Приложение сначала ищет компилятор в `PATH`, а если не находит — в стандартных папках MSYS2 (например, `C:\msys64\ucrt64\bin`). Настраивать PATH не обязательно. Для другого пути укажи полный путь к `g++.exe` в переменной `CPP_ADVENTURE_COMPILER`.

**2а. Через установщик**

1. Готовый установщик не распространяется — его нужно собрать (см. [Сборка из исходников](#сборка-из-исходников)). После `build-windows.bat` файл появится в папке `dist\`:
   - если установлен Inno Setup 6 — `C++Adventure-Setup-0.5.0.exe` (с деинсталлятором, рекомендуется);
   - если нет — `C++Adventure-Setup.exe` (старый однофайловый установщик без деинсталлятора).
2. Запусти установщик. Права администратора не нужны, программа ставится только для твоей учётной записи Windows. Язык установки — турецкий или русский.
3. Если приложение открыто, установщик попросит его закрыть. Если нет WebView2, он сообщит об этом.

Установщик не подписан, поэтому Windows SmartScreen может показать «Неизвестный издатель». Нажми **Подробнее → Выполнить в любом случае**.

**2б. Запуск из исходников (для разработчиков)**

```bat
:: В папке проекта
setup-desktop.bat      :: создаёт .venv и ставит зафиксированные зависимости (нужен интернет)
start-desktop.bat      :: открывает приложение в окне
```

- `start-desktop.bat` запускает `dist\CppAdventure\CppAdventure.exe`, если он есть; иначе запускает исходный код через Python из `.venv`.
- В браузере: `start-browser.bat` (запускает `python server.py` и открывает http://127.0.0.1:8765).
- Точные версии зависимостей — в `requirements-desktop.lock.txt`.

### Первый запуск

1. **Персонаж:** выбери кота (их 7), введи имя и, если хочешь, PIN из 4–8 цифр.
2. **База:** карточка «Продолжи с того места, где остановился» ведёт к следующему заданию.
3. **Урок:** сначала прочитай урок; пошаговые анимации запускаются сами.
4. **Задания:** открываются по порядку — решённое задание открывает следующее. В заданиях с кодом:
   - напиши код;
   - проверь его кнопкой **Запустить**;
   - отправь на проверку кнопкой **Отправить решение**.
5. **Подсказки:** использованная подсказка уменьшает XP за задание на 10 %.
6. **Босс главы:** победа над ним открывает в дереве навыков следующие главы.

| Клавиши | Действие |
|---|---|
| Ctrl + S | Окно сохранения и резервных копий |
| Ctrl + плюс / минус / 0 | Увеличить / уменьшить / сбросить размер текста |
| Ctrl + M (в редакторе) | Tab переключается между отступом и переходом фокуса |
| Первое нажатие Tab | Ссылка «Перейти к содержимому» |

### Настройки (⚙)

- **ИИ-преподаватель:** бесплатный онлайн-ИИ (Groq), офлайн-подсказки или выключен.
- **Внешний вид:** размер текста (100 / 115 / 130 / 150 %) и «Уменьшить анимацию».
- **Язык:** кнопка Türkçe / Русский в верхней панели, переключается сразу.

### Бесплатный ИИ-преподаватель (необязательно)

Используется только **бесплатный план Groq**: карта не нужна, плата не взимается, модель не скачивается.

1. Создай бесплатный аккаунт и ключ на https://console.groq.com/keys (ключ начинается с `gsk_`).
2. В приложении: ⚙ Настройки → **API-ключ Groq** → вставь ключ → **Сохранить ключ**. Ключ проверяется без расхода токенов.
3. В задании с кодом нажми **Проверить мой код**. Код отправляется только после твоего согласия, каждый раз.

- **Три уровня подсказки:** направление, затем строка с ошибкой, затем пошаговое объяснение. Полное решение не даётся никогда.
- **Что не отправляется:** имя, ID профиля и скрытые тесты.
- **Офлайн-подсказки:** без интернета, без ключа или при исчерпанном лимите показываются офлайн-подсказки с объяснением причины.
- **Хранение ключа:** ключ хранится в `%LOCALAPPDATA%\CppAdventure\secrets`, зашифрован Windows DPAPI.

### Данные, резервные копии и восстановление

| Что | Установленное приложение | Запуск из исходников |
|---|---|---|
| База данных (профили, прогресс) | `%LOCALAPPDATA%\CppAdventure\data\adventure.db` | `data\adventure.db` |
| Автоматические резервные копии | `%LOCALAPPDATA%\CppAdventure\backups\` | `backups\` |
| Журналы (запуск, непредвиденные ошибки) | `%LOCALAPPDATA%\CppAdventure\logs\` | `logs\` |
| Код, открытый в VS Code | `%LOCALAPPDATA%\CppAdventure\student-work\` | `student-work\` |

- **Автоматические копии:** перед обновлением схемы базы и перед восстановлением из файла приложение делает проверенную копию. Копии приложение **никогда не удаляет**.
- **Окно Ctrl + S:**
  - **Экспорт** — профиль в файл JSON, без PIN;
  - **Импорт** — восстановить профиль из JSON (для профиля с PIN спрашивается PIN);
  - **Резервная копия** — копия всей базы.
- **Восстановление вручную:**
  1. Закрой приложение.
  2. Перемести `adventure.db` в другое место.
  3. Скопируй нужный файл из `backups\` в `data\` под именем `adventure.db`.
  4. Запусти приложение.

### Удаление

**Параметры → Приложения → C++ Adventure → Удалить** (или Панель управления → Программы).

- Удаляются файлы программы и профиль песочницы (в нём только временные файлы запусков).
- **Профили, прогресс и резервные копии остаются** в `%LOCALAPPDATA%\CppAdventure`; эту папку можно удалить вручную.

### Сборка из исходников

```bat
build-windows.bat
```

1. Готовит `.venv` и с помощью PyInstaller собирает `dist\CppAdventure\CppAdventure.exe` (с информацией о версии, без сжатия UPX).
2. Если установлен **Inno Setup 6** (бесплатно: https://jrsoftware.org/isdl.php), создаётся `dist\C++Adventure-Setup-<версия>.exe`: с деинсталлятором, турецким/русским мастером, закрытием запущенного приложения. Скрипт: `installer\CppAdventure.iss`.
3. Без Inno Setup создаётся старый однофайловый `dist\C++Adventure-Setup.exe` без деинсталлятора.

Номер версии хранится в одном месте: `server.py` → `APP_VERSION`.

### Тесты и оценки

```bat
.venv\Scripts\python.exe -B -m unittest discover -s tests
:: для окружения, созданного Python из MSYS2: .venv\bin\python.exe
```

302 теста; полный прогон занимает около 5 минут, потому что решения заданий компилируются настоящим G++. Результаты тестов и оценки качества — в **[SCORES.md](SCORES.md)** (на турецком).

### Безопасность и конфиденциальность

- **Песочница:** код учащегося в Windows запускается в AppContainer без прав и в Job Object:
  - нет сети и доступа к файлам пользователя, нельзя запускать дочерние процессы;
  - есть лимиты памяти и времени, вывод ограничен 64 КБ.
- **Защита при компиляции:** запрещены приёмы чтения файлов — `#include` с внешними путями, `#embed`, `.incbin`.
- **Локальный API:**
  - доступен только с `127.0.0.1`;
  - требует cookie сессии, новой при каждом запуске;
  - использует строгий CSP;
  - профили с PIN не открываются без PIN.
- **Ответы:** ответы и скрытые тесты не отправляются в браузер. Ввод и ожидаемый вывод проваленного скрытого теста не показываются.
- **По умолчанию офлайн:** ИИ-преподаватель отправляет данные, только если добавлен ключ и ты подтвердил запрос.

### Решение проблем

| Проблема | Решение |
|---|---|
| «G++/Clang++ не найден» | [Установи компилятор](#установка); для нестандартного пути задай `CPP_ADVENTURE_COMPILER`. |
| Приложение не открывается, сообщение о WebView2 | Установи WebView2 Runtime (бесплатно): https://go.microsoft.com/fwlink/p/?LinkId=2124703 |
| При повторном запуске не появляется новое окно | Так и задумано: работает одна копия, она выводится на передний план. |
| «Непредвиденная ошибка (код …)» | Подробности в `logs\server-errors.log`, ищи по коду. |
| Ошибка при запуске | Смотри `%LOCALAPPDATA%\CppAdventure\logs\startup.log`. |
| ИИ-преподаватель не отвечает | Настройки → **Проверить ключ**; если лимит исчерпан, подожди — офлайн-подсказки работают. |
| Мелкий текст | Настройки → Внешний вид → Размер текста или Ctrl + плюс. |

### Переменные среды

| Переменная | Назначение |
|---|---|
| `CPP_ADVENTURE_COMPILER` | Полный путь к `g++.exe` или `clang++.exe` |
| `GROQ_API_KEY` | Ключ Groq (вместо ввода в настройках) |
| `CPP_ADVENTURE_GROQ_MODEL`, `CPP_ADVENTURE_GROQ_FALLBACK_MODEL` | Модели Groq |
| `CPP_ADVENTURE_ADMIN=1` | Тестовая панель для разработки (Ctrl + Shift + A); в выпуске выключена |
| `CPP_ADVENTURE_SANDBOX=job` | Только Job Object вместо AppContainer (для отладки) |

---

## English

A cat-themed adventure game for learning C++. Lessons, tasks and feedback are in Turkish and Russian. (The interface itself is Turkish/Russian; button names below are English translations.) Your code is compiled by the real G++ compiler on this computer and runs in a protected sandbox. The app works offline; the internet is only needed for the optional (free) AI tutor.

### Features

- **24 chapters, 192 tasks:** from your first program to pointers, smart pointers, inheritance, templates and the STL. Modern C++ chapters cover:
  - move semantics;
  - `optional` / `variant` / `string_view`;
  - concepts and ranges;
  - real `std::thread` / `mutex` / `atomic`.
- **Same structure in every chapter:** first a lesson (code examples, common mistakes, step-by-step animations), then 8 tasks: concept question, output prediction, bug fix, warm-up, practice and the chapter boss.
- **Real grading:** code is compiled and run against hidden tests, and the required C++ construct must really be used. Program output is in English; task descriptions are in Turkish and Russian.
- **Skill tree:** chapters unlock by prerequisites; a locked chapter tells you what to finish first.
- **Code editor:** the Monaco editor with C++ suggestions and a program input/output panel. A simple fallback editor takes over if Monaco cannot load.
- **Game elements:**
  - XP, levels and a daily streak;
  - achievements;
  - cat companion and accessory shop;
  - guild and world map;
  - daily arena.
- **Practice:**
  - code lab;
  - visual labs (memory, pointers, sorting, call stack);
  - developer tools (Git, CMake and terminal simulation);
  - multi-file project workshop;
  - interview mode, career and portfolio.
- **Learning journal and statistics:** strong topics, what to review, study time.
- **Accessibility:**
  - the whole app works with the keyboard;
  - focus moves to the page heading on every view change;
  - text size 100–150 % (also Ctrl + Plus / Minus);
  - a "Reduce animations" switch.
- **Profiles:** several players on one computer, each profile can have a PIN.

### Requirements

| Component | Required? | Note |
|---|---|---|
| Windows 10 or 11, 64-bit | Yes | |
| Microsoft Edge WebView2 Runtime | Yes | Included in Windows 11; if missing, the app shows a link to the free installer. |
| G++ compiler (MSYS2 UCRT64 recommended) | For code tasks | Lessons, questions and predictions work without it. |
| Internet | No | Only for the optional AI tutor and the first-time setup downloads. |
| Python 3.10+ | Only to run from source | The installed app does not need Python. |

### Installation

### Download from GitHub and install

1. **Download the project** — either:
   - Open https://github.com/Ogulcannenes/c-rpg → green **Code** button → **Download ZIP**, and extract it, e.g. to `C:\Games\c-rpg`.
   - Or with Git: `git clone https://github.com/Ogulcannenes/c-rpg.git`
2. **Easiest:** double-click **`kur.bat`** in the project folder. It checks Python 3.10+, the G++ compiler, WebView2 and the app dependencies, asks and installs what is missing with winget (Python, MSYS2 + G++, WebView2, `.venv`), then offers to open the app. `kur.bat -CheckOnly` only checks and installs nothing.

   Steps 3–5 below do the same by hand.
3. **Install Python 3.10+** from https://www.python.org/downloads/ — tick **Add python.exe to PATH** in the installer.
4. **Install the G++ compiler** — see step 1 below (MSYS2).
5. In the project folder double-click **`setup-desktop.bat`** (once, needs internet), then **`start-desktop.bat`** — the app opens in its window.
6. Want a real installer with shortcuts? Run **`build-windows.bat`**; the setup file appears in `dist\` (see [Building from source](#building-from-source)).

If Windows warns about .bat files from the internet: **More info → Run anyway**, or right-click the ZIP → Properties → **Unblock** before extracting.

**1. Install the C++ compiler (once)**

1. Download and install MSYS2 from https://www.msys2.org. The default `C:\msys64` is fine. Alternative: `winget install MSYS2.MSYS2`.
2. Open **MSYS2 UCRT64** from the Start menu and run:

   ```bash
   pacman -S --needed mingw-w64-ucrt-x86_64-gcc
   ```

3. Done. The app looks for the compiler on `PATH` and, if it is not there, in the standard MSYS2 folders (for example `C:\msys64\ucrt64\bin`), so editing PATH is not required. For another location, set `CPP_ADVENTURE_COMPILER` to the full path of `g++.exe`.

**2a. With the setup program**

1. No prebuilt installer is distributed; you build it (see [Building from source](#building-from-source)). After `build-windows.bat` the file is in `dist\`:
   - with Inno Setup 6 installed: `C++Adventure-Setup-0.5.0.exe` (with an uninstaller, recommended);
   - without it: `C++Adventure-Setup.exe` (older single-file installer, no uninstaller).
2. Run it. No administrator rights are needed; the app is installed for your Windows account only. The setup language is Turkish or Russian.
3. Setup asks you to close the app if it is running and warns if WebView2 is missing.

The installer is not code-signed, so Windows SmartScreen may show "Unknown publisher". Choose **More info → Run anyway**.

**2b. Run from source (developers)**

```bat
:: In the project folder
setup-desktop.bat      :: creates .venv and installs the pinned dependencies (needs internet)
start-desktop.bat      :: opens the app in a desktop window
```

- `start-desktop.bat` runs `dist\CppAdventure\CppAdventure.exe` if it exists; otherwise it runs the source with the Python in `.venv`.
- In a browser: `start-browser.bat` (runs `python server.py` and opens http://127.0.0.1:8765).
- Exact dependency versions are in `requirements-desktop.lock.txt`.

### First steps

1. **Character:** pick one of 7 cats, enter a name and, optionally, a 4–8 digit PIN.
2. **Home:** the "Continue where you left off" card takes you to the next task.
3. **Lesson:** read the lesson first; the step-by-step animations play by themselves.
4. **Tasks:** they open in order — solving one unlocks the next. In code tasks:
   - write your code;
   - try it with **Run**;
   - submit it with **Submit task**.
5. **Hints:** a hint you use lowers the XP for that task by 10 %.
6. **Chapter boss:** beating it unlocks the next chapters in the skill tree.

| Keys | Action |
|---|---|
| Ctrl + S | Save and backup window |
| Ctrl + Plus / Minus / 0 | Larger / smaller / reset text size |
| Ctrl + M (in the editor) | Tab switches between indenting and moving focus |
| First Tab press | "Skip to content" link |

### Settings (⚙)

- **AI tutor:** free online AI (Groq), offline hints, or off.
- **Appearance:** text size (100 / 115 / 130 / 150 %) and "Reduce animations".
- **Language:** the Türkçe / Русский button in the top bar switches instantly.

### Free AI tutor (optional)

Only **Groq's free plan** is used: no card, no charges, no model download.

1. Create a free account and key at https://console.groq.com/keys (the key starts with `gsk_`).
2. In the app: ⚙ Settings → **Groq API key** → paste → **Save key**. The key is checked without using tokens.
3. In a code task press **Review my code**. Your code is sent only after you agree, every time.

- **Three hint levels:** a direction, then the faulty line, then a step-by-step walkthrough. The full solution is never given.
- **What is never sent:** your name, profile ID and the hidden tests.
- **Offline hints:** without internet, without a key, or when the limit is reached, offline hints are shown and the reason is explained.
- **Key storage:** the key is stored in `%LOCALAPPDATA%\CppAdventure\secrets`, encrypted with Windows DPAPI.

### Data, backups and restore

| What | Installed app | Running from source |
|---|---|---|
| Database (profiles, progress) | `%LOCALAPPDATA%\CppAdventure\data\adventure.db` | `data\adventure.db` |
| Automatic backups | `%LOCALAPPDATA%\CppAdventure\backups\` | `backups\` |
| Logs (startup, unexpected errors) | `%LOCALAPPDATA%\CppAdventure\logs\` | `logs\` |
| Code opened in VS Code | `%LOCALAPPDATA%\CppAdventure\student-work\` | `student-work\` |

- **Automatic copies:** before a database schema upgrade and before restoring from a file, the app makes a verified copy. It **never deletes** these copies.
- **Ctrl + S window:**
  - **Export** — the profile to a JSON file, without the PIN;
  - **Import** — restore a profile from JSON (asks for the PIN on PIN-protected profiles);
  - **Backup** — a copy of the whole database.
- **Manual restore:**
  1. Close the app.
  2. Move `adventure.db` somewhere else.
  3. Copy the backup you want from `backups\` into `data\` as `adventure.db`.
  4. Start the app.

### Uninstall

**Settings → Apps → C++ Adventure → Uninstall** (or Control Panel → Programs).

- The program files and the sandbox profile (temporary run files only) are removed.
- **Your profiles, progress and backups are kept** in `%LOCALAPPDATA%\CppAdventure`; delete that folder yourself to remove everything.

### Building from source

```bat
build-windows.bat
```

1. Prepares `.venv` and builds `dist\CppAdventure\CppAdventure.exe` with PyInstaller (with a version resource, no UPX).
2. With **Inno Setup 6** installed (free: https://jrsoftware.org/isdl.php) it creates `dist\C++Adventure-Setup-<version>.exe`: with an uninstaller, a Turkish/Russian wizard and closing of the running app. Script: `installer\CppAdventure.iss`.
3. Without Inno Setup it creates the older single-file `dist\C++Adventure-Setup.exe`, with no uninstaller.

The version number lives in one place: `server.py` → `APP_VERSION`.

### Tests and scores

```bat
.venv\Scripts\python.exe -B -m unittest discover -s tests
:: for an environment created with MSYS2 Python: .venv\bin\python.exe
```

302 tests; a full run takes about 5 minutes because task solutions are compiled with real G++. Test results and quality scores are in **[SCORES.md](SCORES.md)** (in Turkish).

### Security and privacy

- **Sandbox:** learner code runs on Windows in a capability-less AppContainer plus a Job Object:
  - no network, no access to user files, no child processes;
  - memory and time limits, output capped at 64 KB.
- **Compile-time protection:** file-reading tricks are blocked — `#include` of outside paths, `#embed`, `.incbin`.
- **Local API:**
  - reachable only from `127.0.0.1`;
  - needs a session cookie created anew at every start;
  - uses a strict CSP;
  - PIN-protected profiles stay locked without the PIN.
- **Answers:** answers and hidden tests are never sent to the browser. The input and expected output of a failed hidden test are not shown either.
- **Offline by default:** the AI tutor sends data only when a key is added and you approve the request.

### Troubleshooting

| Symptom | Fix |
|---|---|
| "G++/Clang++ not found" | [Install the compiler](#installation); for a non-standard location set `CPP_ADVENTURE_COMPILER`. |
| The app does not open, WebView2 message | Install the WebView2 Runtime (free): https://go.microsoft.com/fwlink/p/?LinkId=2124703 |
| A second launch shows no new window | Expected: the app runs as a single copy and brings that window to the front. |
| "Unexpected error (code …)" | Details in `logs\server-errors.log`; search for the code. |
| Error at startup | See `%LOCALAPPDATA%\CppAdventure\logs\startup.log`. |
| The AI tutor does not answer | Settings → **Check key**; if the free limit is reached, wait — offline hints keep working. |
| Text is too small | Settings → Appearance → Text size, or Ctrl + Plus. |

### Environment variables

| Variable | Purpose |
|---|---|
| `CPP_ADVENTURE_COMPILER` | Full path to `g++.exe` or `clang++.exe` |
| `GROQ_API_KEY` | Groq key (instead of entering it in Settings) |
| `CPP_ADVENTURE_GROQ_MODEL`, `CPP_ADVENTURE_GROQ_FALLBACK_MODEL` | Groq models |
| `CPP_ADVENTURE_ADMIN=1` | Test panel for development (Ctrl + Shift + A); off in release builds |
| `CPP_ADVENTURE_SANDBOX=job` | Job Object only instead of AppContainer (debugging only) |

### Project structure

```
server.py            Local HTTP server, API endpoints, grading
desktop.py           Desktop window (WebView2), single instance, WebView2 check
curriculum.py        Curriculum (chapters 1–20) + modern_cpp.py (chapters 21–24)
mission_contracts.py Tests for code, bug-fix and boss tasks
concept_checker.py   "Was the required C++ construct used?" check
sandbox*.py          Safe compilation and execution of learner code
db_migrations.py     Versioned database upgrades and backups
ai_tutor.py          Free Groq AI tutor
error_catalog.py     Error codes and Russian error messages
web/                 UI (HTML/CSS/JS), locales.json (TR/RU strings), Monaco editor
tests/               302 automated tests
installer/           Inno Setup script and older installer helpers
docs/                Reports and screenshots
```

### Documents

| Document | Contents |
|---|---|
| [SCORES.md](SCORES.md) | Test results and quality scores (Turkish) |
| [docs/UX_AUDIT.md](docs/UX_AUDIT.md) | Visual UI/UX, accessibility and technical audit with before/after screenshots (Turkish) |
| [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md) | Modernization report, phases 0–12 (Turkish) |
| [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) | Development log (English) |
| [README.tr.md](README.tr.md) | This README in Turkish |

### Artwork and license

The cat characters, mascot and backgrounds were made for this project and live in `web/assets/`; nothing is loaded from the internet. The Monaco editor ships under its own license in `web/vendor/`. The project itself has no license file yet.
