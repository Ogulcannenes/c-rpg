// advanced-cpp-ui.js — İleri C++: thread yarışı (race condition) / mutex simülasyonu ve Compiler Explorer.
// Thread laboratuvarı gerçek thread başlatmaz; sunucudaki adım adım modeli görselleştirir:
// paylaşılan sayaç, her thread'in kendi okuduğu (local) değer, kilit sahibi ve kaybolan güncellemeler.
// Compiler Explorer bu bilgisayardaki G++ ile O0 ve O2 assembly üretir; çıktıyı süzer ve karşılaştırır.
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const lg = () => { try { return lang === 'ru' ? 'ru' : 'tr'; } catch (_) { return 'tr'; } };
  const T = (tr, ru) => lg() === 'ru' ? ru : tr;
  const reduce = () => (window.matchMedia('(prefers-reduced-motion: reduce)').matches||document.body.classList.contains('reduce-motion'));

  let sim = null, step = 0, timer = null, speed = 900, mutex = false, workers = 2, increments = 3, tab = 'threads';
  let asmData = null, showAll = false, codeDraft = null;
  const pause = () => { if (timer) { clearInterval(timer); timer = null; } };

  const RACE_CODE = ['int counter = 0;', '', 'void calis() {', '    for (int i = 0; i < N; ++i) {', '        int local = counter;   // 1) oku', '        counter = local + 1;   // 2) yaz', '    }', '}'];
  const MUTEX_CODE = ['int counter = 0;', 'std::mutex m;', 'void calis() {', '    for (int i = 0; i < N; ++i) {', '        std::lock_guard<std::mutex> kilit(m);', '        ++counter;   // kilit varken tek thread', '    }', '}'];
  const PRESETS = [
    {id: 'square', name: ['Kare fonksiyonu', 'Функция квадрата'], code: '#include <iostream>\nint square(int n) {\n    return n * n;\n}\nint main() {\n    std::cout << square(7) << \'\\n\';\n}\n', note: ['O2\'de derleyici square(7) çağrısını derleme anında 49 olarak hesaplayabilir.', 'При O2 компилятор может вычислить square(7) = 49 ещё при компиляции.']},
    {id: 'loop', name: ['Döngü toplamı', 'Сумма в цикле'], code: '#include <iostream>\nint main() {\n    int toplam = 0;\n    for (int i = 1; i <= 100; ++i)\n        toplam += i;\n    std::cout << toplam << \'\\n\';\n}\n', note: ['O2\'de döngü çoğu zaman tamamen kaybolur; sonuç 5050 doğrudan yazılır.', 'При O2 цикл часто полностью исчезает: сразу выводится 5050.']},
    {id: 'branch', name: ['Koşul ve max', 'Условие и max'], code: 'int enBuyuk(int a, int b) {\n    if (a > b) return a;\n    return b;\n}\nint main() {\n    return enBuyuk(3, 9);\n}\n', note: ['O2\'de if dalı çoğu zaman tek bir cmov komutuna dönüşür.', 'При O2 ветвление часто превращается в одну инструкцию cmov.']},
  ];

  /* ——— Thread laboratuvarı ——— */
  async function simulate() {
    pause();
    const res = await fetch(`/api/advanced/concurrency?workers=${workers}&increments=${increments}&mutex=${mutex ? 1 : 0}&lang=${lg()}`).then(r => r.json()).catch(() => ({error: T('Bağlantı hatası.', 'Ошибка соединения.')}));
    if (res.error) { toast(res.error); return; }
    sim = res; step = 0;
    paintThreads();
  }

  function derive() {
    // Her adım için: her thread'in local değeri, sayaç, kaybolan güncelleme ve kilit sahibi.
    const locals = {}, out = [];
    let counter = 0, lost = 0;
    sim.steps.forEach((s, i) => {
      let event = 'read';
      if (sim.mode === 'mutex') { event = 'locked'; locals[s.thread] = s.value - 1; counter = s.value; }
      else if (s.line.startsWith('int local')) { locals[s.thread] = s.value; event = 'read'; }
      else { const before = counter; counter = s.value; event = counter <= before ? 'lost' : 'write'; if (event === 'lost') lost += 1; }
      out.push({i, thread: s.thread, event, counter, locals: {...locals}, lost});
    });
    return out;
  }

  function threadsPanel() {
    return `<section class="adv-lab">
      <aside class="panel adv-setup"><span class="eyebrow">${esc(T('Güvenli simülasyon', 'Безопасная симуляция'))}</span><h2>${esc(T('Race condition ve mutex', 'Гонка данных и mutex'))}</h2>
        <p>${esc(T('İki thread aynı sayacı aynı anda artırmaya çalışırsa ne olur? İkisi de eski değeri okur, ikisi de aynı sonucu yazar ve bir artış kaybolur. Mutex ile her artış sırayla yapılır.', 'Что будет, если два потока одновременно увеличивают один счётчик? Оба читают старое значение, оба пишут один и тот же результат — и одно увеличение теряется. С mutex увеличения идут по очереди.'))}</p>
        <div class="adv-fields"><label>${esc(T('Thread sayısı', 'Число потоков'))}<div class="adv-stepper" data-field="workers"><button type="button" data-d="-1" aria-label="-">−</button><b>${workers}</b><button type="button" data-d="1" aria-label="+">+</button></div></label>
          <label>${esc(T('Her thread kaç kez artırsın?', 'Сколько увеличений на поток?'))}<div class="adv-stepper" data-field="increments"><button type="button" data-d="-1" aria-label="-">−</button><b>${increments}</b><button type="button" data-d="1" aria-label="+">+</button></div></label></div>
        <div class="adv-mode" role="radiogroup"><button type="button" role="radio" aria-checked="${!mutex}" class="${!mutex ? 'active race' : ''}" data-mode="race">⚡ ${esc(T('Kilitsiz (yarış)', 'Без блокировки (гонка)'))}</button><button type="button" role="radio" aria-checked="${mutex}" class="${mutex ? 'active safe' : ''}" data-mode="mutex">🔒 ${esc(T('Mutex ile', 'С mutex'))}</button></div>
        <div class="adv-code"><div class="adv-code-head">thread.cpp</div><ol id="adv-code-lines">${(mutex ? MUTEX_CODE : RACE_CODE).map(l => `<li>${esc(l) || '&nbsp;'}</li>`).join('')}</ol></div>
        <p class="adv-note">${esc(T('Gerçek thread başlatılmaz; işlemcinin yapabileceği bir sıralama adım adım gösterilir.', 'Реальные потоки не запускаются: пошагово показан один из возможных порядков выполнения.'))}</p>
      </aside>
      <article class="panel adv-stage">
        <div class="adv-stage-top"><span>${esc(T('Paylaşılan bellek', 'Общая память'))}</span><b id="adv-step-label">—</b></div>
        <div class="adv-memory"><div class="adv-counter-box"><small>counter</small><b id="adv-counter">0</b><i id="adv-lock" class="adv-lock" aria-hidden="true">🔒</i></div>
          <div class="adv-expect"><small>${esc(T('Beklenen', 'Ожидается'))}</small><b id="adv-expected">0</b></div><div class="adv-expect lost"><small>${esc(T('Kaybolan', 'Потеряно'))}</small><b id="adv-lost">0</b></div></div>
        <div class="adv-lanes" id="adv-lanes"></div>
        <p class="adv-explain" id="adv-step-text" aria-live="polite"></p>
        <div class="adv-timeline" id="adv-timeline" role="group" aria-label="${esc(T('Adımlar', 'Шаги'))}"></div>
        <div class="adv-controls"><button type="button" class="secondary" id="adv-reset">↺ ${esc(T('Başa dön', 'В начало'))}</button><button type="button" class="secondary" id="adv-back">‹ ${esc(T('Geri', 'Назад'))}</button><button type="button" class="primary" id="adv-play">▶ ${esc(T('Oynat', 'Играть'))}</button><button type="button" class="secondary" id="adv-next">${esc(T('İleri', 'Вперёд'))} ›</button>
          <label class="adv-speed">${esc(T('Hız', 'Скорость'))}<input id="adv-speed" type="range" min="300" max="1800" step="100" value="${2100 - speed}"></label></div>
        <div class="adv-verdict" id="adv-verdict" hidden></div>
      </article></section>`;
  }

  function paintThreads() {
    const host = $('#view-advanced');
    if (!sim || !$('#adv-lanes', host)) return;
    const data = derive(), cur = data[step], s = sim.steps[step];
    const threads = Array.from({length: sim.workers}, (_, i) => `T${i + 1}`);
    $('#adv-step-label', host).textContent = `${step + 1} / ${sim.steps.length}`;
    const counter = $('#adv-counter', host);
    if (counter.textContent !== String(cur.counter)) { counter.textContent = cur.counter; if (!reduce()) { counter.classList.remove('bump', 'lost'); void counter.offsetWidth; counter.classList.add(cur.event === 'lost' ? 'lost' : 'bump'); } }
    else if (cur.event === 'lost' && !reduce()) { counter.classList.remove('bump', 'lost'); void counter.offsetWidth; counter.classList.add('lost'); }
    $('#adv-expected', host).textContent = sim.expected;
    $('#adv-lost', host).textContent = cur.lost;
    $('#adv-lock', host).classList.toggle('on', sim.mode === 'mutex');
    $('#adv-lanes', host).innerHTML = threads.map((t, k) => {
      const active = t === s.thread, local = cur.locals[t];
      return `<div class="adv-lane ${active ? 'active ' + cur.event : ''}" style="--k:${k}"><span class="adv-chip">${t}</span><div class="adv-reg"><small>local</small><b>${local ?? '—'}</b></div><code>${active ? esc(s.line) : '…'}</code>${active && cur.event === 'lost' ? `<em>${esc(T('ezildi!', 'затёрто!'))}</em>` : active && sim.mode === 'mutex' ? `<em class="ok">🔒 ${esc(T('kilit bende', 'блокировка у меня'))}</em>` : ''}</div>`;
    }).join('');
    // Kod satırı vurgusu
    const lineIndex = sim.mode === 'mutex' ? 4 : s.line.startsWith('int local') ? 4 : 5;
    $$('#adv-code-lines li', host).forEach((li, i) => li.classList.toggle('active', i === lineIndex || (sim.mode === 'mutex' && i === 5)));
    $('#adv-step-text', host).textContent = lg() === 'ru' ? s.text_ru : s.text;
    $('#adv-timeline', host).innerHTML = data.map((d, i) => `<button type="button" class="${d.event} ${i === step ? 'current' : ''} ${i < step ? 'past' : ''}" data-idx="${i}" title="${esc(sim.steps[i].thread)}" style="--k:${Number(sim.steps[i].thread.slice(1)) - 1}"></button>`).join('');
    $$('#adv-timeline button', host).forEach(b => b.onclick = () => { pause(); step = +b.dataset.idx; paintThreads(); });
    $('#adv-back', host).disabled = step === 0;
    $('#adv-next', host).disabled = step >= sim.steps.length - 1;
    $('#adv-play', host).textContent = timer ? `⏸ ${T('Duraklat', 'Пауза')}` : `▶ ${T('Oynat', 'Играть')}`;
    const verdict = $('#adv-verdict', host), end = step === sim.steps.length - 1;
    verdict.hidden = !end;
    if (end) {
      verdict.className = `adv-verdict ${sim.final === sim.expected ? 'ok' : 'bad'}`;
      verdict.innerHTML = sim.final === sim.expected
        ? `✓ ${esc(T(`Sonuç ${sim.final} / ${sim.expected}: mutex her artışı korudu, hiçbir güncelleme kaybolmadı.`, `Итог ${sim.final} / ${sim.expected}: mutex защитил каждое увеличение, ничего не потеряно.`))}`
        : `✕ ${esc(T(`Sonuç ${sim.final} / ${sim.expected}: ${sim.lost_updates} artış kayboldu. Şimdi "Mutex ile" seçeneğini dene.`, `Итог ${sim.final} / ${sim.expected}: потеряно увеличений — ${sim.lost_updates}. Теперь попробуй «С mutex».`))}`;
    }
  }

  /* ——— Compiler Explorer ——— */
  const MNEMONIC = /^\s*([a-z][a-z0-9.]*)/;
  function userFunctions(source) {
    const names = new Set(['main']);
    for (const m of String(source || '').matchAll(/\b([A-Za-z_]\w*)\s*\([^;{}()]*\)\s*(?:const\s*)?\{/g)) if (!['if', 'for', 'while', 'switch', 'catch'].includes(m[1])) names.add(m[1]);
    return [...names];
  }
  function filterAsm(text, names) {
    let keep = showAll;
    return String(text || '').split('\n').filter(line => {
      const t = line.trim();
      if (!t || /^#(APP|NO_APP)/.test(t)) return false;
      const label = t.match(/^([A-Za-z_.$][\w.$@]*):/);
      if (label && !label[1].startsWith('.L')) keep = showAll || names.some(n => label[1] === n || new RegExp(`\\d${n}[A-Z_v]`).test(label[1]) || label[1].includes(`${n.length}${n}`));
      if (!keep) return false;
      if (/^\.(cfi|file|ident|section|size|type|globl|p2align|align|text|intel_syntax|loc|weak|hidden|def|scl|endef|seh_)/.test(t)) return false;
      if (/^\.L(FB|FE|VL|LVL|BE)\d/.test(t)) return false;
      if (/^\.(long|byte|quad|string|ascii|zero|value)/.test(t) && !showAll) return false;
      return true;
    });
  }
  function instructionCount(lines) { return lines.filter(l => /^\s+[a-z]/.test(l) && !/^\s+\./.test(l)).length; }
  function highlightAsm(line) {
    if (/^[^\s].*:$/.test(line)) return `<span class="asm-label">${esc(line)}</span>`;
    const m = line.match(MNEMONIC);
    if (!m) return esc(line);
    const rest = line.slice(m[0].length);
    return `${esc(line.slice(0, line.indexOf(m[1])))}<span class="asm-op">${esc(m[1])}</span>${esc(rest).replace(/\b(e?r?[abcd]x|[re]?[sd]i|[re]?[sb]p|r\d+d?|xmm\d+|eax|edi|esi)\b/g, '<span class="asm-reg">$1</span>').replace(/\b(\d+)\b/g, '<span class="asm-num">$1</span>')}`;
  }

  function assemblyPanel() {
    const code = codeDraft ?? PRESETS[0].code;
    return `<section class="panel adv-asm"><div class="adv-asm-head"><div><h2>Compiler Explorer</h2><p>${esc(T('C++ kodunun derleyicide hangi makine komutlarına dönüştüğünü gör. Aynı kod iki kez derlenir: O0 (optimizasyon yok) ve O2 (hızlı kod).', 'Посмотри, в какие машинные инструкции компилятор превращает код C++. Один и тот же код собирается дважды: O0 (без оптимизаций) и O2 (быстрый код).'))}</p></div><span class="advanced-local">${esc(T('Bu bilgisayardaki G++', 'Локальный G++'))}</span></div>
      <div class="adv-presets">${PRESETS.map(p => `<button type="button" class="secondary adv-preset" data-preset="${p.id}">${esc(p.name[lg() === 'ru' ? 1 : 0])}</button>`).join('')}</div>
      <textarea id="adv-code" class="advanced-code" spellcheck="false" maxlength="20000">${esc(code)}</textarea>
      <div class="adv-asm-actions"><button type="button" class="primary" id="adv-compile">⚙ ${esc(T('Derle ve karşılaştır', 'Скомпилировать и сравнить'))}</button><label class="adv-toggle"><input type="checkbox" id="adv-showall" ${showAll ? 'checked' : ''}> ${esc(T('Kütüphane kodunu da göster', 'Показывать и код библиотек'))}</label></div>
      <div id="adv-asm-results" class="asm-results">${asmData ? asmResults() : ''}</div></section>`;
  }
  function asmResults() {
    const data = asmData;
    if (data.error) return `<div class="tip error">${esc(data.error)}</div>`;
    const names = userFunctions(codeDraft ?? $('#adv-code')?.value), cards = data.outputs.map(x => ({...x, lines: filterAsm(x.assembly, names)}));
    const counts = cards.map(c => instructionCount(c.lines)), max = Math.max(1, ...counts);
    const preset = PRESETS.find(p => p.code.trim() === ($('#adv-code')?.value || codeDraft || '').trim());
    return `<div class="adv-compare">${cards.map((c, i) => `<div class="adv-bar-row"><b>${esc(c.optimization)}</b><i><span style="--w:${counts[i] / max * 100}%"></span></i><em>${counts[i]} ${esc(T('komut', 'инструкций'))}</em></div>`).join('')}
      ${counts.length === 2 && counts[0] > 0 ? `<p>${esc(T(`O2 sürümü ${counts[1] < counts[0] ? `%${Math.round((1 - counts[1] / counts[0]) * 100)} daha az komut kullanıyor.` : 'benzer sayıda komut kullanıyor; ama komut sayısı tek ölçü değil, aşağıda hangi işlerin derleme anında yapıldığına bak.'}`, `Версия O2 ${counts[1] < counts[0] ? `использует на ${Math.round((1 - counts[1] / counts[0]) * 100)}% меньше инструкций.` : 'использует примерно столько же инструкций; но их число — не единственная мера, посмотри ниже, что вычислено ещё при компиляции.'}`))} ${preset ? esc(preset.note[lg() === 'ru' ? 1 : 0]) : ''}</p>` : ''}</div>
      <p class="adv-note">${esc(lg() === 'ru' ? data.notice_ru : data.notice_tr)} · ${esc(data.compiler)}</p>
      <div class="asm-grid">${cards.map(c => `<article class="asm-card"><h3>${esc(c.optimization)} ${c.ok ? '✓' : '✕'}</h3>${c.errors ? `<pre class="asm-error">${esc(c.errors)}</pre>` : ''}<pre class="asm-code">${c.lines.map(highlightAsm).join('\n') || esc(T('Çıktı yok.', 'Нет вывода.'))}</pre></article>`).join('')}</div>`;
  }

  /* ——— Ana görünüm ——— */
  function render() {
    const host = $('#view-advanced');
    if (typeof profileId !== 'string' || !profileId) { host.innerHTML = `<div class="panel">${esc(T('Önce bir profil seç.', 'Сначала выбери профиль.'))}</div>`; return; }
    pause();
    host.innerHTML = `<span class="eyebrow">⚡ ${esc(T('İleri C++', 'Продвинутый C++'))}</span><h1 class="view-title">${esc(T('Eşzamanlılık ve derleyici laboratuvarı', 'Лаборатория многопоточности и компилятора'))}</h1><p class="view-lead">${esc(T('Thread\'lerin neden kilide ihtiyaç duyduğunu ve derleyicinin kodunu nasıl hızlandırdığını keşfet.', 'Узнай, зачем потокам блокировки и как компилятор ускоряет твой код.'))}</p>
      <div class="advanced-tabs" role="tablist"><button type="button" role="tab" aria-selected="${tab === 'threads'}" class="${tab === 'threads' ? 'primary' : 'secondary'}" data-adv-tab="threads">🧵 ${esc(T('Thread laboratuvarı', 'Лаборатория потоков'))}</button><button type="button" role="tab" aria-selected="${tab === 'assembly'}" class="${tab === 'assembly' ? 'primary' : 'secondary'}" data-adv-tab="assembly">⚙ Compiler Explorer</button><button type="button" class="secondary" id="adv-quality">⛳ ${esc(T('Code Golf / kalite', 'Code Golf / качество'))}</button></div>
      ${tab === 'threads' ? threadsPanel() : assemblyPanel()}`;
    host.querySelector('.view-lead')?.insertAdjacentHTML('afterend', window.CppAdventureCatGuide ? window.CppAdventureCatGuide('wizard', 'catWizard') : '');
    $$('[data-adv-tab]', host).forEach(b => b.onclick = () => { if (tab === 'assembly') codeDraft = $('#adv-code', host)?.value ?? codeDraft; tab = b.dataset.advTab; render(); });
    $('#adv-quality', host).onclick = () => document.querySelector('[data-view="quality"]')?.click();
    if (tab === 'threads') {
      $$('.adv-stepper', host).forEach(st => st.querySelectorAll('button').forEach(b => b.onclick = () => {
        const field = st.dataset.field, limits = field === 'workers' ? [1, 4] : [1, 5];
        const value = Math.max(limits[0], Math.min(limits[1], (field === 'workers' ? workers : increments) + Number(b.dataset.d)));
        if (field === 'workers') workers = value; else increments = value;
        st.querySelector('b').textContent = value;
        simulate();
      }));
      $$('[data-mode]', host).forEach(b => b.onclick = () => { mutex = b.dataset.mode === 'mutex'; render(); });
      $('#adv-back', host).onclick = () => { pause(); step = Math.max(0, step - 1); paintThreads(); };
      $('#adv-next', host).onclick = () => { pause(); step = Math.min(sim.steps.length - 1, step + 1); paintThreads(); };
      $('#adv-reset', host).onclick = () => { pause(); step = 0; paintThreads(); };
      $('#adv-play', host).onclick = () => {
        if (timer) { pause(); paintThreads(); return; }
        if (!sim) return;
        if (step >= sim.steps.length - 1) step = 0;
        timer = setInterval(() => { if (step >= sim.steps.length - 1) { pause(); paintThreads(); return; } step++; paintThreads(); }, speed);
        paintThreads();
      };
      $('#adv-speed', host).oninput = e => { speed = 2100 - Number(e.target.value); if (timer) { pause(); $('#adv-play', host).click(); } };
      simulate();
    } else {
      $$('.adv-preset', host).forEach(b => b.onclick = () => { codeDraft = PRESETS.find(p => p.id === b.dataset.preset).code; $('#adv-code', host).value = codeDraft; });
      $('#adv-code', host).oninput = e => { codeDraft = e.target.value; };
      $('#adv-showall', host).onchange = e => { showAll = e.target.checked; if (asmData) $('#adv-asm-results', host).innerHTML = asmResults(); };
      $('#adv-compile', host).onclick = async () => {
        const out = $('#adv-asm-results', host), btn = $('#adv-compile', host);
        btn.disabled = true; out.innerHTML = `<p class="adv-note">${esc(T('Derleniyor…', 'Компиляция…'))}</p>`;
        asmData = await fetch('/api/compiler/assembly', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({profile_id: profileId, code: $('#adv-code', host).value})}).then(r => r.json()).catch(() => ({error: T('Bağlantı hatası.', 'Ошибка соединения.')}));
        if (!asmData.outputs && !asmData.error) asmData.error = T('Derleme başarısız.', 'Компиляция не удалась.');
        out.innerHTML = asmResults();
        btn.disabled = false;
      };
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const item = document.querySelector('[data-view="advanced"]');
    if (!item) return;
    item.addEventListener('click', () => { setView('advanced'); $('#crumb-current').textContent = T('İleri C++', 'Продвинутый C++'); render(); });
    document.addEventListener('cpp-adventure-language-changed', () => { const label = item.querySelector('[data-advanced-label]'); if (label) label.textContent = T('İleri C++', 'Продвинутый C++'); if (!$('#view-advanced')?.classList.contains('hidden')) render(); });
  });
})();
