// devtools-ui.js — Geliştirici araçları laboratuvarları (Git, çakışma, CMake, test, terminal).
// Tüm işlemler sunucudaki sanal durum üzerinde çalışır; işletim sisteminde komut çalıştırılmaz.
// Bu arayüz, her işlemin gerçek komut karşılığını gösterir, depo durumunu görselleştirir ve
// sunucunun İngilizce durum mesajlarını Türkçe/Rusçaya çevirir.
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const lg = () => { try { return lang === 'ru' ? 'ru' : 'tr'; } catch (_) { return 'tr'; } };
  const T = (tr, ru) => lg() === 'ru' ? ru : tr;

  let selected = 'git', state = null, lastRun = null, busy = false, dvFocusTerm = false;
  const logs = {git: []};
  const termHistory = [];
  let termCursor = -1;
  const dvForm = {name: 'notes.txt', content: 'Hello Git!', message: 'Add learning notes', branch: 'feature-notes'};
  const dvConflict = {text: ''};

  const MODULES = [
    {id: 'git', icon: '🌿', name: ['Git temelleri', 'Основы Git'], desc: ['Commit, dal, birleştirme', 'Коммиты, ветки, слияние']},
    {id: 'conflict', icon: '⚔️', name: ['Çakışma çözümü', 'Разрешение конфликтов'], desc: ['İki dal aynı satırı değiştirirse', 'Когда две ветки меняют одну строку']},
    {id: 'cmake', icon: '🧱', name: ['CMake akışı', 'Сборка CMake'], desc: ['Projeyi derlemeye hazırla', 'Подготовь проект к сборке']},
    {id: 'testing', icon: '🧪', name: ['C++ test laboratuvarı', 'Лаборатория тестов C++'], desc: ['Girdi → beklenen çıktı', 'Ввод → ожидаемый вывод']},
    {id: 'terminal', icon: '⌨️', name: ['Güvenli terminal', 'Безопасный терминал'], desc: ['Temel kabuk komutları', 'Базовые команды оболочки']},
  ];
  const pick = pair => pair[lg() === 'ru' ? 1 : 0];

  /* ——— Sunucu mesajlarının çevirisi ——— */
  const MESSAGES = [
    [/^Initialized empty teaching repository on main\.$/, 'Boş bir öğretim deposu main dalında oluşturuldu.', 'Создан пустой учебный репозиторий в ветке main.'],
    [/^Run git init first\.$/, 'Önce git init çalıştır.', 'Сначала выполни git init.'],
    [/^Use a simple file name and 1–4000 characters of content\.$/, 'Basit bir dosya adı ve 1–4000 karakterlik içerik kullan.', 'Используй простое имя файла и содержимое от 1 до 4000 символов.'],
    [/^Working tree changed: (.+)$/, 'Çalışma alanında değişti: $1', 'Изменено в рабочей копии: $1'],
    [/^That file does not exist in the virtual workspace\.$/, 'Bu dosya sanal çalışma alanında yok. Önce "Dosyayı kaydet"e bas.', 'Такого файла нет в рабочей копии. Сначала нажми «Сохранить файл».'],
    [/^Staged (\d+) file\(s\)\.$/, 'Hazırlık alanında $1 dosya var.', 'Файлов в индексе: $1.'],
    [/^Stage a file and enter a commit message first\.$/, 'Önce bir dosyayı hazırlık alanına ekle (git add) ve commit mesajı yaz.', 'Сначала добавь файл в индекс (git add) и напиши сообщение коммита.'],
    [/^Commit (\d+) created on (.+)\.$/, '$2 dalında $1 numaralı commit oluşturuldu.', 'В ветке $2 создан коммит $1.'],
    [/^Choose a new branch name using letters, digits, dot, dash, or underscore\.$/, 'Yeni bir dal adı yaz (harf, rakam, nokta, tire, alt çizgi). Bu isimde dal zaten olabilir.', 'Введи новое имя ветки (буквы, цифры, точка, дефис, подчёркивание). Возможно, такая ветка уже есть.'],
    [/^Created and switched to (.+)\.$/, '$1 dalı oluşturuldu ve ona geçildi.', 'Создана ветка $1, выполнен переход на неё.'],
    [/^Branch not found\.$/, 'Dal bulunamadı.', 'Ветка не найдена.'],
    [/^Switched to (.+)\.$/, '$1 dalına geçildi.', 'Переход на ветку $1.'],
    [/^Choose another existing branch to merge\.$/, 'Birleştirmek için şu an bulunduğun daldan farklı, var olan bir dal seç.', 'Выбери для слияния другую существующую ветку.'],
    [/^Commit or discard working-tree changes before merging\.$/, 'Birleştirmeden önce çalışma alanındaki değişiklikleri commit et.', 'Перед слиянием закоммить изменения в рабочей копии.'],
    [/^Merge conflict in (.+)\. Resolve it in the Conflict lab, then retry\.$/, '$1 dosyasında çakışma var. Nasıl çözüleceğini Çakışma çözümü laboratuvarında öğren.', 'Конфликт в файле $1. Как его разрешить — в лаборатории «Разрешение конфликтов».'],
    [/^Merged (.+) into (.+) as commit (\d+)\.$/, '$1 dalı $2 dalına birleştirildi (commit $3).', 'Ветка $1 слита в $2 (коммит $3).'],
    [/^Pushed (.+) to the simulated remote\. No network connection was used\.$/, '$1 dalı sanal uzak depoya (origin) gönderildi. İnternet kullanılmadı.', 'Ветка $1 отправлена в виртуальный удалённый репозиторий (origin). Интернет не использовался.'],
    [/^No simulated remote update exists for this branch\.$/, 'Bu dal için uzak depoda bir şey yok. Önce git push yap.', 'В удалённом репозитории для этой ветки ничего нет. Сначала сделай git push.'],
    [/^Pulled simulated (.+) remote state\. No network connection was used\.$/, '$1 dalının uzak depodaki hâli çekildi. İnternet kullanılmadı.', 'Получено состояние ветки $1 из удалённого репозитория. Интернет не использовался.'],
    [/^On branch (.+) · staged: (\d+) · unstaged: (\d+)$/, 'Dal: $1 · hazırlıkta: $2 · commit edilmemiş değişiklik: $3', 'Ветка: $1 · в индексе: $2 · незакоммиченных изменений: $3'],
    [/^Unknown Git lab action\.$/, 'Bilinmeyen Git işlemi.', 'Неизвестное действие Git.'],
    [/^Both branches changed the same line\. Choose the final value to resolve the conflict\.$/, 'İki dal aynı satırı farklı biçimde değiştirdi. Son hâli seçerek ya da düzenleyerek çakışmayı çöz.', 'Обе ветки по-разному изменили одну строку. Выбери или отредактируй итоговый вариант.'],
    [/^Remove every conflict marker before finishing the merge\.$/, 'Bitirmeden önce bütün çakışma işaretlerini (<<<<<<<, =======, >>>>>>>) sil.', 'Перед завершением удали все маркеры конфликта (<<<<<<<, =======, >>>>>>>).'],
    [/^Use one of the branch versions shown above\.$/, 'Sonuç tek bir geçerli satır olmalı, örneğin: int canPuani = 110;', 'Результат должен быть одной корректной строкой, например: int canPuani = 110;'],
    [/^Conflict resolved and merge verified\.$/, 'Çakışma çözüldü, birleştirme tamamlandı.', 'Конфликт разрешён, слияние завершено.'],
    [/^Start the conflict scenario first\.$/, 'Önce çakışma senaryosunu başlat.', 'Сначала запусти сценарий конфликта.'],
    [/^Create CMakeLists\.txt\.$/, 'CMakeLists.txt oluşturuldu.', 'Создан CMakeLists.txt.'],
    [/^Declare the minimum CMake version and project\.$/, 'En düşük CMake sürümü ve proje adı yazıldı.', 'Указаны минимальная версия CMake и имя проекта.'],
    [/^Add the C\+\+ executable target\.$/, 'Çalıştırılabilir hedef eklendi.', 'Добавлена исполняемая цель.'],
    [/^Configure, build, then run the executable\.$/, 'Yapılandırıldı, derlendi ve çalıştırıldı.', 'Сконфигурировано, собрано и запущено.'],
    [/^Complete the CMake steps in order\.$/, 'CMake adımlarını sırayla tamamla.', 'Выполняй шаги CMake по порядку.'],
    [/^CMake executable: (detected|not detected) · lesson progress (\d)\/4\..*$/, m => m[1] === 'detected' ? T(`Bu bilgisayarda CMake bulundu · ilerleme ${m[2]}/4`, `CMake найден на этом компьютере · прогресс ${m[2]}/4`) : T(`Bu bilgisayarda CMake bulunamadı; laboratuvar simülasyonla çalışır · ilerleme ${m[2]}/4`, `CMake на этом компьютере не найден; лаборатория работает в симуляции · прогресс ${m[2]}/4`)],
    [/^Test case saved locally\.$/, 'Test durumu kaydedildi.', 'Тест сохранён.'],
    [/^C\+\+ test passed\.$/, 'Test geçti: çıktı beklenenle aynı.', 'Тест пройден: вывод совпал с ожидаемым.'],
    [/^C\+\+ test failed\..*$/, 'Test geçmedi: beklenen çıktıyla programın çıktısını karşılaştır.', 'Тест не пройден: сравни ожидаемый и фактический вывод.'],
    [/^Allowed: (.+)$/, 'İzin verilen komutlar: $1', 'Разрешённые команды: $1'],
    [/^Directory already exists\.$/, 'Bu klasör zaten var.', 'Такая папка уже есть.'],
    [/^Created (.+)$/, '$1 oluşturuldu.', 'Создано: $1'],
    [/^Removed (.+)$/, '$1 silindi.', 'Удалено: $1'],
    [/^File not found\.$/, 'Dosya bulunamadı.', 'Файл не найден.'],
    [/^Directory not found\.$/, 'Klasör bulunamadı.', 'Папка не найдена.'],
    [/^Use: echo TEXT > safe-file-name$/, 'Kullanım: echo METİN > dosya-adi', 'Использование: echo ТЕКСТ > имя-файла'],
    [/^Wrote (\d+) characters\.$/, '$1 karakter yazıldı.', 'Записано символов: $1.'],
    [/^On branch main\nNothing to commit \(simulated workspace\)\.$/, 'main dalındasın\nCommit edilecek değişiklik yok (sanal çalışma alanı).', 'Ты в ветке main\nНечего коммитить (виртуальная рабочая копия).'],
    [/^CMake lesson simulator · no host command was executed\.$/, 'CMake ders simülatörü · bilgisayarda komut çalıştırılmadı.', 'Учебный симулятор CMake · команды на компьютере не выполнялись.'],
    [/^Compiler is available\.$/, 'Derleyici hazır.', 'Компилятор доступен.'],
    [/^G\+\+ was not detected\.$/, 'G++ bulunamadı.', 'G++ не найден.'],
    [/^Terminal cleared\.$/, 'Terminal temizlendi.', 'Терминал очищен.'],
    [/^Blocked: .*$/, 'Engellendi: bu öğretim terminali yalnızca izinli sanal komutları kabul eder. Bilgisayarında hiçbir komut çalışmadı. Liste için help yaz.', 'Заблокировано: учебный терминал принимает только разрешённые виртуальные команды. На компьютере ничего не выполнялось. Список команд — help.'],
    [/^\(empty\)$/, '(boş)', '(пусто)'],
    [/^Command is too long \(240 character limit\)\.$/, 'Komut çok uzun (en fazla 240 karakter).', 'Команда слишком длинная (максимум 240 символов).'],
    [/^Enter a command, or type help\.$/, 'Bir komut ya da help yaz.', 'Введи команду или help.'],
  ];
  function msg(text) {
    const value = String(text ?? '');
    for (const [re, tr, ru] of MESSAGES) {
      const m = value.match(re);
      if (!m) continue;
      if (typeof tr === 'function') return tr(m);
      return value.replace(re, lg() === 'ru' ? ru : tr);
    }
    return value;
  }

  /* ——— Ortak iskelet ——— */
  function moduleDone(id, st) {
    if (!st) return false;
    if (id === 'git') return Object.keys(st.remote || {}).length > 0 && (st.commits || []).some(c => /^Merge /.test(c.message));
    if (id === 'conflict' || id === 'cmake') return !!st.complete;
    if (id === 'testing') return (st.passed || 0) > 0;
    if (id === 'terminal') return (st.history || []).length >= 5;
    return false;
  }

  async function render() {
    if (typeof profileId !== 'string' || !profileId) return;
    const host = $('#view-devtools');
    if (!host.querySelector('.dv-shell')) host.innerHTML = `<div class="journal-loading">${esc(T('Laboratuvar yükleniyor…', 'Загрузка лаборатории…'))}</div>`;
    const reply = await fetch(`/api/devtools?profile_id=${encodeURIComponent(profileId)}&module=${selected}`).then(r => r.json()).catch(() => ({error: T('Bağlantı hatası.', 'Ошибка соединения.')}));
    if (reply.error) { host.innerHTML = `<div class="tip error">${esc(reply.error)}</div>`; return; }
    state = reply.state;
    paint();
  }

  function paint() {
    const host = $('#view-devtools');
    const mod = MODULES.find(m => m.id === selected);
    const panel = {git: gitPanel, conflict: conflictPanel, cmake: cmakePanel, testing: testingPanel, terminal: terminalPanel}[selected]();
    host.innerHTML = `<div class="dv-shell"><span class="eyebrow">⌘ ${esc(T('Geliştirici araçları', 'Инструменты разработчика'))}</span><h1 class="view-title">${esc(T('Geliştirici laboratuvarları', 'Лаборатории разработчика'))}</h1>
      <p class="view-lead">${esc(T('Gerçek projelerde her gün kullanılan araçları güvenli bir sanal ortamda dene. Bilgisayarındaki dosyalar ve komutlar etkilenmez; yalnızca test laboratuvarı gerçek G++ ile derler.', 'Попробуй инструменты, которыми пользуются в реальных проектах, в безопасной виртуальной среде. Файлы и команды на компьютере не затрагиваются; только лаборатория тестов компилирует настоящим G++.'))}</p>
      <nav class="dv-modules" aria-label="${esc(T('Laboratuvarlar', 'Лаборатории'))}">${MODULES.map(m => `<button type="button" class="dv-module ${m.id === selected ? 'active' : ''}" data-dv-module="${m.id}" aria-pressed="${m.id === selected}"><span class="dv-icon">${m.icon}</span><span><b>${esc(pick(m.name))}</b><small>${esc(pick(m.desc))}</small></span>${m.id === selected && moduleDone(m.id, state) ? '<i class="dv-done">✓</i>' : ''}</button>`).join('')}</nav>
      <section class="dv-panel" aria-label="${esc(pick(mod.name))}">${panel}</section></div>`;
    wire(host);
  }

  /* ——— Git ——— */
  function gitView() {
    const st = state, committed = st.branch_files?.[st.branch] || {};
    const names = [...new Set([...Object.keys(st.files || {}), ...Object.keys(committed)])].sort();
    const files = names.map(name => {
      const now = st.files?.[name], before = committed[name];
      const staged = (st.staged || []).includes(name);
      const status = now === undefined ? 'deleted' : before === undefined ? 'new' : now !== before ? 'modified' : 'clean';
      return {name, status, staged};
    });
    const commits = st.commits || [];
    const branches = Object.keys(st.branches || {});
    const merged = commits.some(c => /^Merge /.test(c.message));
    const steps = [
      [st.initialized, 'git init', T('Depoyu başlat', 'Создай репозиторий'), T('Klasörü bir Git deposuna çevirir; değişiklikler artık izlenir.', 'Превращает папку в репозиторий Git; изменения начинают отслеживаться.')],
      [files.some(f => f.status !== 'clean') || commits.length > 0, T('dosyayı kaydet', 'сохрани файл'), T('Bir dosya oluştur ya da değiştir', 'Создай или измени файл'), T('Dosya adı ve içerik yaz, sonra "Dosyayı kaydet"e bas.', 'Введи имя и содержимое файла и нажми «Сохранить файл».')],
      [(st.staged || []).length > 0 || commits.length > 0, 'git add', T('Hazırlık alanına ekle', 'Добавь в индекс'), T('Bir sonraki commit\'e girecek dosyaları seçer.', 'Выбирает файлы, которые попадут в следующий коммит.')],
      [commits.length > 0, 'git commit', T('Commit oluştur', 'Создай коммит'), T('Hazırlık alanındaki değişikliklerin kalıcı bir fotoğrafını çeker.', 'Делает постоянный снимок изменений из индекса.')],
      [branches.length > 1, 'git switch -c', T('Yeni dal aç', 'Создай ветку'), T('Ana kodu bozmadan ayrı bir çizgide çalışmanı sağlar.', 'Позволяет работать отдельно, не ломая основной код.')],
      [commits.some(c => c.branch !== 'main'), 'git commit', T('Yeni dalda commit at', 'Закоммить в новой ветке'), T('Yeni daldayken bir dosyayı değiştir, git add yap ve commit et.', 'Находясь в новой ветке, измени файл, сделай git add и закоммить.')],
      [merged, 'git merge', T('main\'e dön ve birleştir', 'Вернись в main и слей'), T('"Diğer dal" listesinden main\'i seçip git switch yap, sonra diğer dalı seçip git merge yap.', 'Выбери main в списке «Другая ветка» и сделай git switch, затем выбери другую ветку и сделай git merge.')],
      [Object.keys(st.remote || {}).length > 0, 'git push', T('Uzak depoya gönder', 'Отправь в удалённый репозиторий'), T('Commit\'lerini paylaşılan depoya (origin) yollar.', 'Отправляет коммиты в общий репозиторий (origin).')],
    ];
    const current = steps.findIndex(s => !s[0]);
    return {files, commits, branches, steps, current};
  }

  function gitPanel() {
    const st = state, v = gitView();
    const lanes = v.branches;
    const graph = v.commits.length ? v.commits.map(c => {
      const lane = Math.max(0, lanes.indexOf(c.branch));
      const heads = lanes.filter(b => st.branches[b] === c.id);
      return `<li class="dv-commit" style="--lane:${lane}"><i class="dv-dot ${/^Merge /.test(c.message) ? 'merge' : ''}"></i><code>${esc(c.id)}</code><span>${esc(c.message)}</span>${heads.map(h => `<em class="dv-ref ${h === st.branch ? 'head' : ''}">${h === st.branch ? 'HEAD → ' : ''}${esc(h)}</em>`).join('')}</li>`;
    }).reverse().join('') : `<li class="dv-empty">${esc(T('Henüz commit yok.', 'Коммитов пока нет.'))}</li>`;
    const label = {new: T('yeni', 'новый'), modified: T('değişti', 'изменён'), deleted: T('silindi', 'удалён'), clean: '✓'};
    const fileRow = f => `<li class="dv-file st-${f.status}"><button type="button" class="dv-file-pick" data-file="${esc(f.name)}" title="${esc(T('Düzenlemek için seç', 'Выбрать для редактирования'))}">📄 ${esc(f.name)}</button><em>${label[f.status]}</em></li>`;
    const work = v.files.filter(f => !f.staged), staged = v.files.filter(f => f.staged);
    const otherBranches = v.branches.filter(b => b !== st.branch);
    const remote = Object.keys(st.remote || {});
    return `<div class="dv-git">
      <aside class="dv-guide"><h3>🧭 ${esc(T('Görev rehberi', 'Пошаговый план'))}</h3><ol>${v.steps.map((s, i) => `<li class="${s[0] ? 'done' : i === v.current ? 'current' : ''}"><span class="dv-step-n">${s[0] ? '✓' : i + 1}</span><div><b>${esc(s[2])}</b><code>${esc(s[1])}</code>${i === v.current ? `<p>${esc(s[3])}</p>` : ''}</div></li>`).join('')}</ol>${v.current < 0 ? `<p class="dv-win">🎉 ${esc(T('Tebrikler! Bir Git iş akışının tamamını uyguladın.', 'Поздравляем! Ты прошёл весь рабочий процесс Git.'))}</p>` : ''}</aside>
      <div class="dv-git-main">
        <div class="dv-repo" aria-label="${esc(T('Depo durumu', 'Состояние репозитория'))}">
          <section class="dv-zone"><h4>📂 ${esc(T('Çalışma alanı', 'Рабочая копия'))}</h4><ul>${work.map(fileRow).join('') || `<li class="dv-empty">${esc(T('Bekleyen değişiklik yok', 'Изменений нет'))}</li>`}</ul></section>
          <i class="dv-arrow" aria-hidden="true">add</i>
          <section class="dv-zone staging"><h4>📥 ${esc(T('Hazırlık alanı', 'Индекс'))}</h4><ul>${staged.map(fileRow).join('') || `<li class="dv-empty">${esc(T('Boş', 'Пусто'))}</li>`}</ul></section>
          <i class="dv-arrow" aria-hidden="true">commit</i>
          <section class="dv-zone repo"><h4>🗂 ${esc(T('Depo', 'Репозиторий'))} <small>${esc(T('dal', 'ветка'))}: <b>${esc(st.branch)}</b></small></h4><ul class="dv-graph">${graph}</ul></section>
          <i class="dv-arrow" aria-hidden="true">push</i>
          <section class="dv-zone remote"><h4>☁️ origin</h4><ul>${remote.map(b => `<li class="dv-file"><span>🌿 ${esc(b)}</span><em>${esc(st.remote[b].head || '—')}</em></li>`).join('') || `<li class="dv-empty">${esc(T('Henüz push yok', 'Push ещё не было'))}</li>`}</ul></section>
        </div>
        ${!st.initialized ? `<div class="dv-start"><p>${esc(T('Bu klasör henüz bir Git deposu değil. Başlamak için depoyu oluştur.', 'Эта папка ещё не репозиторий Git. Создай репозиторий, чтобы начать.'))}</p><button type="button" class="primary" data-action="init"><code>git init</code></button></div>` : `
        <div class="dv-controls">
          <fieldset class="dv-box"><legend>✏️ ${esc(T('Dosya', 'Файл'))}</legend>
            <label>${esc(T('Dosya adı', 'Имя файла'))}<input class="answer-input" id="dt-name" value="${esc(dvForm.name)}" spellcheck="false"></label>
            <label>${esc(T('İçerik', 'Содержимое'))}<textarea class="answer-input" id="dt-content" rows="3" spellcheck="false">${esc(dvForm.content)}</textarea></label>
            <div class="dv-buttons"><button type="button" class="secondary" data-action="write">💾 ${esc(T('Dosyayı kaydet', 'Сохранить файл'))}</button><button type="button" class="secondary" data-action="add"><code>git add <span data-mirror="name">${esc(dvForm.name)}</span></code></button><button type="button" class="secondary" data-action="add" data-all="1"><code>git add .</code></button></div>
          </fieldset>
          <fieldset class="dv-box"><legend>📸 Commit</legend>
            <label>${esc(T('Commit mesajı', 'Сообщение коммита'))}<input class="answer-input" id="dt-message" value="${esc(dvForm.message)}"></label>
            <div class="dv-buttons"><button type="button" class="primary" data-action="commit"><code>git commit -m "…"</code></button><button type="button" class="secondary" data-action="status"><code>git status</code></button></div>
          </fieldset>
          <fieldset class="dv-box"><legend>🌿 ${esc(T('Dallar', 'Ветки'))}</legend>
            <label>${esc(T('Yeni dal adı', 'Имя новой ветки'))}<input class="answer-input" id="dt-branch" value="${esc(dvForm.branch)}" spellcheck="false"></label>
            <div class="dv-buttons"><button type="button" class="secondary" data-action="branch"><code>git switch -c <span data-mirror="branch">${esc(dvForm.branch)}</span></code></button></div>
            ${otherBranches.length ? `<label>${esc(T('Diğer dal', 'Другая ветка'))}<select class="answer-input" id="dt-other">${otherBranches.map(b => `<option>${esc(b)}</option>`).join('')}</select></label>
            <div class="dv-buttons"><button type="button" class="secondary" data-action="checkout"><code>git switch</code></button><button type="button" class="secondary" data-action="merge"><code>git merge</code></button></div>` : ''}
          </fieldset>
          <fieldset class="dv-box"><legend>☁️ ${esc(T('Uzak depo', 'Удалённый репозиторий'))}</legend>
            <div class="dv-buttons"><button type="button" class="secondary" data-action="push"><code>git push</code></button><button type="button" class="secondary" data-action="pull"><code>git pull</code></button></div>
            <p class="dv-note">${esc(T('İnternete bağlanmaz; origin bu laboratuvarın içindeki sanal bir depodur.', 'Интернет не используется: origin — виртуальный репозиторий внутри лаборатории.'))}</p>
          </fieldset>
        </div>`}
        ${logPanel()}
      </div></div>`;
  }

  function logPanel() {
    const items = logs.git;
    if (!items.length) return state?.last ? `<div class="dv-log"><div class="dv-log-row"><span>${esc(msg(state.last))}</span></div></div>` : '';
    return `<div class="dv-log" aria-live="polite">${items.slice(-6).map(x => `<div class="dv-log-row ${x.bad ? 'bad' : ''}"><code>$ ${esc(x.cmd)}</code><span>${esc(x.out)}</span></div>`).join('')}</div>`;
  }

  /* ——— Çakışma ——— */
  function conflictPanel() {
    const st = state;
    const left = st.left || 'int canPuani = 100;', right = st.right || 'int canPuani = 120;';
    const marked = `<<<<<<< HEAD (feature-a)\n${left}\n=======\n${right}\n>>>>>>> feature-b`;
    const steps = [T('İki dal aynı satırı farklı biçimde değiştirdi.', 'Две ветки по-разному изменили одну строку.'), T('Git hangisinin doğru olduğunu bilemez; dosyaya çakışma işaretleri koyar.', 'Git не знает, какой вариант верный, и ставит в файл маркеры конфликта.'), T('Son hâline sen karar verirsin: birini seç ya da yeni bir satır yaz (örneğin 110).', 'Итог решаешь ты: выбери вариант или напиши новую строку (например, 110).'), T('İşaretleri sil ve birleştirmeyi bitir.', 'Удали маркеры и заверши слияние.')];
    const doneN = st.complete ? 4 : st.conflict ? 2 : 0;
    return `<div class="dv-conflict">
      <aside class="dv-guide"><h3>⚔️ ${esc(T('Çakışma nasıl çözülür?', 'Как разрешить конфликт?'))}</h3><ol>${steps.map((s, i) => `<li class="${i < doneN ? 'done' : i === doneN ? 'current' : ''}"><span class="dv-step-n">${i < doneN ? '✓' : i + 1}</span><div><p>${esc(s)}</p></div></li>`).join('')}</ol></aside>
      <div class="dv-conflict-main">
        <div class="dv-branches"><div class="dv-branch a"><b>🌿 feature-a</b><code>${esc(left)}</code></div><div class="dv-branch b"><b>🌿 feature-b</b><code>${esc(right)}</code></div></div>
        ${!st.conflict && !st.complete ? `<div class="dv-start"><p>${esc(T('Senaryo: iki arkadaş kahramanın can puanını farklı dallarda değiştirdi. Şimdi feature-b dalını feature-a dalına birleştiriyoruz.', 'Сценарий: двое друзей изменили здоровье героя в разных ветках. Теперь сливаем feature-b в feature-a.'))}</p><button type="button" class="primary" data-action="start"><code>git merge feature-b</code></button></div>` : ''}
        ${st.conflict ? `<div class="dv-file-editor"><div class="dv-editor-head">📄 kahraman.cpp <em>CONFLICT</em></div><pre class="dv-marked">${marked.split('\n').map(line => `<span class="${/^(<<<<<<<|>>>>>>>|=======)/.test(line) ? 'mk' : line === left ? 'ours' : 'theirs'}">${esc(line)}</span>`).join('\n')}</pre></div>
          <div class="dv-choices"><button type="button" class="secondary dv-choose" data-text="${esc(left)}">⬅ ${esc(T('feature-a\'yı al', 'Взять feature-a'))}</button><button type="button" class="secondary dv-choose" data-text="${esc(right)}">${esc(T('feature-b\'yi al', 'Взять feature-b'))} ➡</button><button type="button" class="secondary dv-choose" data-text="${esc(marked)}">✍️ ${esc(T('Elle düzenle', 'Изменить вручную'))}</button></div>
          <label class="dv-resolve">${esc(T('Dosyanın son hâli', 'Итоговое содержимое файла'))}<textarea class="answer-input" id="dt-resolved" rows="5" spellcheck="false">${esc(dvConflict.text || marked)}</textarea></label>
          <button type="button" class="primary" data-action="resolve">✓ ${esc(T('Çakışmayı çöz ve birleştirmeyi bitir', 'Разрешить конфликт и завершить слияние'))}</button>` : ''}
        ${st.complete ? `<div class="dv-win">🎉 ${esc(T('Birleştirme tamamlandı. Dosyanın son hâli:', 'Слияние завершено. Итоговая строка:'))} <code>${esc(st.resolved)}</code></div><button type="button" class="secondary" data-action="start">↻ ${esc(T('Senaryoyu yeniden başlat', 'Начать сценарий заново'))}</button>` : ''}
        ${st.last ? `<div class="dv-log"><div class="dv-log-row ${/Remove|Use one/.test(st.last) ? 'bad' : ''}"><span>${esc(msg(st.last))}</span></div></div>` : ''}
      </div></div>`;
  }

  /* ——— CMake ——— */
  const CMAKE = [
    {title: ['CMakeLists.txt dosyasını oluştur', 'Создай файл CMakeLists.txt'], why: ['CMake, projenin nasıl derleneceğini bu dosyadan okur. Dosya proje klasörünün köküne konur.', 'CMake читает из этого файла, как собирать проект. Файл лежит в корне папки проекта.'], lines: ['# CMakeLists.txt']},
    {title: ['Sürüm ve proje adını yaz', 'Укажи версию и имя проекта'], why: ['cmake_minimum_required gereken en düşük CMake sürümünü, project ise projenin adını ve dilini söyler.', 'cmake_minimum_required задаёт минимальную версию CMake, project — имя и язык проекта.'], lines: ['cmake_minimum_required(VERSION 3.16)', 'project(KediApp LANGUAGES CXX)', 'set(CMAKE_CXX_STANDARD 20)']},
    {title: ['Çalıştırılabilir hedefi ekle', 'Добавь исполняемую цель'], why: ['add_executable, hangi .cpp dosyalarından hangi programın üretileceğini tanımlar.', 'add_executable описывает, из каких .cpp файлов собирается программа.'], lines: ['add_executable(kedi main.cpp)']},
    {title: ['Yapılandır, derle ve çalıştır', 'Сконфигурируй, собери и запусти'], why: ['Önce build klasörü yapılandırılır, sonra derlenir ve program çalıştırılır.', 'Сначала конфигурируется папка build, затем идёт сборка и запуск программы.'], lines: []},
  ];
  function cmakePanel() {
    const st = state, step = st.step || 0;
    const file = CMAKE.slice(0, step).flatMap(s => s.lines), oldCount = CMAKE.slice(0, Math.max(0, step - 1)).flatMap(s => s.lines).length;
    const term = step >= 4 ? ['$ cmake -S . -B build', '-- Configuring done', '-- Generating done', '$ cmake --build build', '[100%] Built target kedi', '$ ./build/kedi', 'Miyav! CMake ile derlendim.'] : [];
    return `<div class="dv-cmake">
      <aside class="dv-guide"><h3>🧱 ${esc(T('Adımlar', 'Шаги'))}</h3><ol>${CMAKE.map((s, i) => `<li class="${i < step ? 'done' : i === step ? 'current' : ''}"><span class="dv-step-n">${i < step ? '✓' : i + 1}</span><div><b>${esc(pick(s.title))}</b>${i === step ? `<p>${esc(pick(s.why))}</p><button type="button" class="primary" data-action="step" data-step="${i + 1}">${esc(T('Bu adımı uygula', 'Выполнить шаг'))}</button>` : ''}</div></li>`).join('')}</ol>
        ${st.complete ? `<p class="dv-win">🎉 ${esc(T('Proje CMake ile derlendi!', 'Проект собран с помощью CMake!'))}</p>` : ''}<div class="dv-buttons"><button type="button" class="secondary" data-action="reset">↺ ${esc(T('Baştan başla', 'Начать сначала'))}</button><button type="button" class="secondary" data-action="status">${esc(T('CMake kurulu mu?', 'Установлен ли CMake?'))}</button></div></aside>
      <div class="dv-cmake-main">
        <div class="dv-tree"><b>📁 kedi-projesi/</b><ul><li>📄 main.cpp</li>${step >= 1 ? '<li class="dv-new">📄 CMakeLists.txt</li>' : ''}${step >= 4 ? '<li class="dv-new">📁 build/ <small>→ kedi</small></li>' : ''}</ul></div>
        <div class="dv-files"><div class="dv-file-editor"><div class="dv-editor-head">📄 main.cpp</div><pre>#include &lt;iostream&gt;
int main() {
    std::cout &lt;&lt; "Miyav! CMake ile derlendim.\\n";
}</pre></div>
        <div class="dv-file-editor"><div class="dv-editor-head">📄 CMakeLists.txt</div><pre>${step ? file.map((line, i) => `<span class="${i >= oldCount ? 'dv-line-new' : ''}">${esc(line)}</span>`).join('\n') : `<span class="dv-muted">${esc(T('(henüz yok)', '(пока нет)'))}</span>`}</pre></div></div>
        <div class="dv-terminal small"><div class="dv-term-body">${term.length ? term.map((line, i) => `<div class="${line.startsWith('$') ? 'cmd' : 'out'}" style="--i:${i}">${esc(line)}</div>`).join('') : `<div class="dv-muted">${esc(T('Son adımda komutlar burada çalışacak.', 'На последнем шаге здесь появятся команды.'))}</div>`}</div></div>
        ${st.last ? `<div class="dv-log"><div class="dv-log-row"><span>${esc(msg(st.last))}</span></div></div>` : ''}
      </div></div>`;
  }

  /* ——— Test laboratuvarı ——— */
  function testingPanel() {
    const st = state, run = lastRun;
    const actual = run ? String(run.stdout ?? run.output ?? '') : '';
    return `<div class="dv-testing">
      <div class="dv-test-intro"><p>${esc(T('Bir test, programa verilen girdi ile beklenen çıktıdan oluşur. Program gerçekten derlenir, çalıştırılır ve çıktısı beklenenle karşılaştırılır.', 'Тест — это ввод для программы и ожидаемый вывод. Программа действительно компилируется и запускается, а её вывод сравнивается с ожидаемым.'))}</p>
        <div class="dv-buttons"><button type="button" class="secondary dv-preset" data-preset="ok">✓ ${esc(T('Doğru örnek', 'Верный пример'))}</button><button type="button" class="secondary dv-preset" data-preset="bug">🐞 ${esc(T('Hatalı örnek', 'Пример с ошибкой'))}</button><button type="button" class="secondary dv-preset" data-preset="edge">🧩 ${esc(T('Sınır durumu', 'Граничный случай'))}</button></div></div>
      <div class="dv-test-grid">
        <label class="dv-code">${esc(T('C++ kodu', 'Код C++'))}<textarea class="answer-input code-input" id="dt-code" rows="12" spellcheck="false">${esc(st.code)}</textarea></label>
        <div class="dv-case">
          <label>${esc(T('Girdi (stdin)', 'Ввод (stdin)'))}<textarea class="answer-input" id="dt-input" rows="3" spellcheck="false">${esc(st.input)}</textarea></label>
          <label>${esc(T('Beklenen çıktı', 'Ожидаемый вывод'))}<textarea class="answer-input" id="dt-expected" rows="3" spellcheck="false">${esc(st.expected)}</textarea></label>
          <button type="button" class="primary" data-action="run">▶ ${esc(T('Testi çalıştır', 'Запустить тест'))}</button>
          <p class="dv-note">${esc(T('Çalıştırma', 'Запусков'))}: <b>${st.runs || 0}</b> · ${esc(T('Geçen', 'Пройдено'))}: <b>${st.passed || 0}</b></p>
        </div>
      </div>
      ${run ? `<div class="dv-result ${run.tests_passed ? 'pass' : 'fail'}"><h3>${run.tests_passed ? '✓ ' + esc(T('Test geçti', 'Тест пройден')) : '✕ ' + esc(T('Test geçmedi', 'Тест не пройден'))}</h3>
        ${run.ok === false && (run.error || run.compile_output) ? `<pre class="dv-err">${esc(run.compile_output || run.error)}</pre>` : `<div class="dv-diff"><div><small>${esc(T('Beklenen', 'Ожидалось'))}</small><pre>${esc(run.expected)}</pre></div><div><small>${esc(T('Programın çıktısı', 'Вывод программы'))}</small><pre>${esc(actual)}</pre></div></div>`}
        <small>${esc(({complete: T('tamamlandı', 'завершено'), compile: T('derleme', 'компиляция'), runtime: T('çalışma hatası', 'ошибка выполнения'), timeout: T('zaman aşımı', 'превышено время')})[run.phase] || run.phase || '')}${run.exit_code !== undefined && run.exit_code !== null ? ` · exit ${run.exit_code}` : ''}${run.elapsed_ms ? ` · ${run.elapsed_ms} ms` : ''}</small></div>` : ''}
    </div>`;
  }
  const PRESETS = {
    ok: {code: '#include <iostream>\nint main() {\n    int n;\n    std::cin >> n;\n    std::cout << n * 2;\n}', input: '21', expected: '42'},
    bug: {code: '#include <iostream>\nint main() {\n    int n;\n    std::cin >> n;\n    std::cout << n * 3;   // hata: 2 olmalı\n}', input: '21', expected: '42'},
    edge: {code: '#include <iostream>\nint main() {\n    int a, b;\n    std::cin >> a >> b;\n    std::cout << (a > b ? a : b);\n}', input: '-5 -5', expected: '-5'},
  };

  /* ——— Terminal ——— */
  function terminalPanel() {
    const st = state, cwd = st.cwd || '/adventure';
    const dirs = (st.dirs || []).slice().sort(), files = Object.keys(st.files || {}).sort();
    const tree = dirs.map(d => {
      const depth = d.split('/').length - 2;
      const inside = files.filter(f => f.slice(0, f.lastIndexOf('/')) === d);
      return `<li style="--d:${depth}" class="${d === cwd ? 'here' : ''}">📁 ${esc(d.split('/').pop())}${d === cwd ? ` <em>${esc(T('buradasın', 'ты здесь'))}</em>` : ''}</li>${inside.map(f => `<li style="--d:${depth + 1}">📄 ${esc(f.split('/').pop())}</li>`).join('')}`;
    }).join('');
    const chips = ['help', 'pwd', 'ls', 'mkdir kediler', 'cd kediler', 'touch notlar.txt', 'echo Miyav > not.txt', 'cat not.txt', 'cd ..', 'clear'];
    return `<div class="dv-term-wrap">
      <div class="dv-terminal" id="dv-terminal"><div class="dv-term-head"><i></i><i></i><i></i><span>kedi@adventure: ${esc(cwd)}</span></div>
        <div class="dv-term-body" id="dv-term-body">${(st.history || []).map(x => `<div class="cmd"><span class="ps">$</span> ${esc(x.command)}</div><div class="out">${esc(msg(x.output))}</div>`).join('') || `<div class="dv-muted">${esc(T('Bir komut yazıp Enter\'a bas. Ne yazacağını bilmiyorsan help yaz ya da sağdaki hazır komutlara tıkla.', 'Введи команду и нажми Enter. Если не знаешь, что писать, введи help или нажми на готовую команду справа.'))}</div>`}
          <form class="dv-term-input" id="dv-term-form"><span class="ps">${esc(cwd)} $</span><input id="dt-command" autocomplete="off" spellcheck="false" aria-label="${esc(T('Komut', 'Команда'))}"></form></div></div>
      <aside class="dv-side"><h3>🗂 ${esc(T('Dosya ağacı', 'Дерево файлов'))}</h3><ul class="dv-ftree">${tree}</ul>
        <h3>⚡ ${esc(T('Hazır komutlar', 'Готовые команды'))}</h3><div class="dv-chips">${chips.map(c => `<button type="button" class="dv-chip" data-cmd="${esc(c)}"><code>${esc(c)}</code></button>`).join('')}</div>
        <p class="dv-note">${esc(T('↑ / ↓ ile önceki komutlara dönebilirsin.', 'Стрелками ↑ / ↓ можно вернуть предыдущие команды.'))}</p></aside></div>`;
  }

  /* ——— Olaylar ——— */
  function wire(host) {
    $$('[data-dv-module]', host).forEach(b => b.onclick = () => { selected = b.dataset.dvModule; lastRun = null; render(); });
    $$('[data-action]', host).forEach(b => b.onclick = () => act(b));
    $$('.dv-file-pick', host).forEach(b => b.onclick = () => { dvForm.name = b.dataset.file; dvForm.content = state.files?.[b.dataset.file] ?? ''; paint(); });
    ['name', 'content', 'message', 'branch'].forEach(k => {
      const el = $(`#dt-${k}`, host);
      if (!el) return;
      el.oninput = () => { dvForm[k] = el.value; const mirror = $(`[data-mirror="${k}"]`, host); if (mirror) mirror.textContent = el.value; };
    });
    $$('.dv-choose', host).forEach(b => b.onclick = () => { dvConflict.text = b.dataset.text; const area = $('#dt-resolved', host); area.value = b.dataset.text; area.focus(); });
    $('#dt-resolved', host)?.addEventListener('input', e => { dvConflict.text = e.target.value; });
    $$('.dv-preset', host).forEach(b => b.onclick = () => { const p = PRESETS[b.dataset.preset]; $('#dt-code', host).value = p.code; $('#dt-input', host).value = p.input; $('#dt-expected', host).value = p.expected; });
    const form = $('#dv-term-form', host);
    if (form) {
      const input = $('#dt-command', host), body = $('#dv-term-body', host);
      body.scrollTop = body.scrollHeight;
      form.onsubmit = e => { e.preventDefault(); runCommand(input.value); };
      input.onkeydown = e => {
        if (e.key === 'ArrowUp' && termHistory.length) { e.preventDefault(); termCursor = termCursor < 0 ? termHistory.length - 1 : Math.max(0, termCursor - 1); input.value = termHistory[termCursor]; }
        if (e.key === 'ArrowDown' && termHistory.length) { e.preventDefault(); if (termCursor < 0) return; termCursor += 1; if (termCursor >= termHistory.length) { termCursor = -1; input.value = ''; } else input.value = termHistory[termCursor]; }
      };
      $('#dv-terminal', host).onclick = e => { if (!e.target.closest('input')) input.focus(); };
      $$('.dv-chip', host).forEach(c => c.onclick = () => runCommand(c.dataset.cmd));
      if (dvFocusTerm) input.focus();
    }
  }

  async function runCommand(command) {
    command = String(command || '').trim();
    if (!command) return;
    termHistory.push(command); termHistory.splice(0, Math.max(0, termHistory.length - 50)); termCursor = -1;
    dvFocusTerm = true;
    await act({dataset: {action: 'terminal'}, command});
  }

  const GIT_CMD = {init: () => 'git init', write: () => `edit ${dvForm.name}`, add: b => `git add ${b?.dataset?.all ? '.' : dvForm.name}`, commit: () => `git commit -m "${dvForm.message}"`, branch: () => `git switch -c ${dvForm.branch}`, checkout: name => `git switch ${name}`, merge: name => `git merge ${name}`, push: () => 'git push', pull: () => 'git pull', status: () => 'git status'};

  async function act(button) {
    if (busy) return;
    const action = button.dataset.action;
    const body = {profile_id: profileId, module: selected, action};
    const other = $('#dt-other')?.value || '';
    if (action === 'write') { body.name = dvForm.name.trim(); body.content = dvForm.content; }
    if (action === 'add') body.name = button.dataset.all ? '*' : dvForm.name.trim();
    if (action === 'commit') body.message = dvForm.message;
    if (action === 'branch') body.name = dvForm.branch.trim();
    if (action === 'checkout' || action === 'merge') body.name = other;
    if (action === 'resolve') body.resolved = ($('#dt-resolved')?.value || '').trim();
    if (action === 'step') body.step = Number(button.dataset.step);
    if (action === 'terminal') body.command = button.command;
    if (action === 'run') { body.code = $('#dt-code').value; body.input = $('#dt-input').value; body.expected = $('#dt-expected').value; }
    if (action === 'start') dvConflict.text = '';
    if (action !== 'terminal') dvFocusTerm = false;
    busy = true;
    if (button.disabled !== undefined) button.disabled = true;
    try {
      const result = await fetch('/api/devtools/action', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}).then(r => r.json()).catch(() => ({error: T('Bağlantı hatası.', 'Ошибка соединения.')}));
      if (result.error) { toast(result.error); return; }
      state = result.state; lastRun = result.result || null;
      if (selected === 'git' && GIT_CMD[action]) {
        const bad = /first|Stage a|Choose|not found|does not|Commit or|conflict|Use a|No simulated|Unknown/.test(state.last);
        logs.git.push({cmd: GIT_CMD[action](action === 'add' ? button : other), out: msg(state.last), bad});
      }
      paint();
    } finally { busy = false; }
  }

  document.addEventListener('click', event => {
    const nav = event.target.closest('.nav-item[data-view="devtools"]');
    if (nav) { lastRun = null; setView('devtools'); render(); }
  });
  document.addEventListener('cpp-adventure-language-changed', () => { if (!$('#view-devtools').classList.contains('hidden') && state) paint(); });
})();
