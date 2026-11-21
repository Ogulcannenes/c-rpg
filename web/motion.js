// motion.js — C++ Adventure animasyon katmanı.
// Uygulama kodunu değiştirmeden çalışır: api(), setView(), renderSidebar() ve catReact() sarmalanır,
// yeni çizilen öğeler (terminal çıktısı, örnek kod, harita, ipucu kutusu) MutationObserver ile yakalanır.
(() => {
  const reduce = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches || document.body.classList.contains('reduce-motion');
  const M = key => (window.L ? window.L(`motion.${key}`) : key);
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  let lastPointer = {x: innerWidth / 2, y: innerHeight / 2};
  document.addEventListener('pointerdown', e => { lastPointer = {x: e.clientX, y: e.clientY}; }, true);

  /* ——— Kedi ruh hali ——— */
  const MOOD_MAP = {sad: 'oops', error: 'oops'};
  function setCatMood(mood = 'idle', ms = 2200) {
    mood = MOOD_MAP[mood] || mood;
    $$('.view:not(.hidden) .cat-stage, .cat-levelup-overlay .cat-stage').forEach(stage => {
      stage.dataset.mood = mood;
      clearTimeout(stage._moodTimer);
      if (mood !== 'idle' && ms) stage._moodTimer = setTimeout(() => { if (stage.dataset.mood === mood) stage.dataset.mood = 'idle'; }, ms);
    });
  }
  window.CatMood = {set: setCatMood};
  // app.js'teki eski catReact yalnızca tek bir kediye veri koyuyordu; artık ekrandaki tüm yoldaşlar tepki verir.
  window.catReact = mood => setCatMood(mood === 'idle' ? 'idle' : mood, 2200);

  // Uzun süre işlem yoksa kedi uyuklar, ilk dokunuşta gerinerek uyanır.
  let idleTimer = null;
  const SLEEP_AFTER = 75000;
  function wake() {
    if (document.body.dataset.catMood === 'sleep') {
      delete document.body.dataset.catMood;
      setCatMood('wake', 800);
    }
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => { document.body.dataset.catMood = 'sleep'; }, SLEEP_AFTER);
  }
  ['pointerdown', 'keydown', 'wheel', 'pointermove'].forEach(ev => document.addEventListener(ev, wake, {passive: true}));

  /* ——— Pati konfetisi ——— */
  const PAW = '<svg viewBox="0 0 24 24" aria-hidden="true"><ellipse cx="12" cy="16" rx="5.4" ry="4.6"/><circle cx="5.6" cy="10" r="2.3"/><circle cx="9.6" cy="6.4" r="2.4"/><circle cx="14.4" cy="6.4" r="2.4"/><circle cx="18.4" cy="10" r="2.3"/></svg>';
  const COLORS = ['#ffa45c', '#5fe0cf', '#a885ff', '#ffd58a', '#ff8fc7', '#f6efe4'];
  function confetti(x = lastPointer.x, y = lastPointer.y, count = 26) {
    if (reduce()) return;
    const layer = document.createElement('div');
    layer.className = 'paw-burst';
    layer.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < count; i++) {
      const a = Math.random() * Math.PI * 2, dist = 90 + Math.random() * 190;
      const bit = document.createElement('span');
      bit.className = 'paw-bit';
      bit.innerHTML = PAW;
      bit.style.cssText = `--x:${x}px;--y:${y}px;--dx:${Math.cos(a) * dist}px;--dy:${Math.sin(a) * dist * .8 + 120}px;--r:${(Math.random() * 540 - 270) | 0}deg;--s:${12 + Math.random() * 14}px;--c:${COLORS[i % COLORS.length]};--d:${.9 + Math.random() * .6}s`;
      layer.append(bit);
    }
    document.body.append(layer);
    setTimeout(() => layer.remove(), 1700);
  }
  window.PawConfetti = confetti;

  function floatXp(amount, x, y) {
    if (!amount || reduce()) return;
    const el = document.createElement('div');
    el.className = 'xp-float';
    el.textContent = `${amount > 0 ? '+' : ''}${amount} XP`;
    el.style.left = `${x}px`; el.style.top = `${y}px`;
    document.body.append(el);
    setTimeout(() => el.remove(), 1600);
  }

  /* ——— Başarım bildirimi ——— */
  function badgePop(id) {
    const badge = (typeof BADGES !== 'undefined' ? BADGES : []).find(b => b[0] === id);
    const title = badge && typeof tr === 'function' ? tr(badge[2]) : id;
    const pop = document.createElement('div');
    pop.className = 'badge-pop';
    pop.setAttribute('role', 'status');
    pop.innerHTML = `<span class="badge-medal" aria-hidden="true">${badge ? badge[1] : '★'}</span><span><small>${M('newBadge')}</small><b></b></span>`;
    pop.querySelector('b').textContent = title;
    const stack = $$('.badge-pop').length;
    pop.style.top = `${78 + stack * 84}px`;
    document.body.append(pop);
    setTimeout(() => { pop.classList.add('leaving'); setTimeout(() => pop.remove(), 380); }, 3600);
  }
  window.BadgePop = badgePop;

  /* ——— Kenar çubuğu: XP akışı, seri alevi, yeni başarımlar ——— */
  let prev = null;
  function rollNumber(el, from, to, suffix) {
    if (!el || reduce() || from === to) return;
    const start = performance.now(), dur = Math.min(1400, 400 + Math.abs(to - from) * 2);
    el.classList.add('xp-rolling');
    const step = now => {
      const t = Math.min(1, (now - start) / dur), eased = 1 - Math.pow(1 - t, 3);
      el.textContent = `${Math.round(from + (to - from) * eased)}${suffix}`;
      if (t < 1) requestAnimationFrame(step); else el.classList.remove('xp-rolling');
    };
    requestAnimationFrame(step);
  }
  function afterSidebar() {
    const p = window.appState?.profile;
    if (!p) return;
    const now = {id: p.id || (typeof profileId !== 'undefined' ? profileId : ''), xp: Number(p.xp || 0), streak: Number(p.streak || 0), badges: new Set(p.achievements || [])};
    const streakEl = $('.streak');
    streakEl?.classList.toggle('has-streak', now.streak > 0);
    if (prev && prev.id === now.id) {
      if (now.xp !== prev.xp) {
        rollNumber($('#side-xp'), prev.xp, now.xp, ' XP');
        const card = $('.profile-card');
        if (card && now.xp > prev.xp) {
          card.classList.remove('xp-glow'); void card.offsetWidth; card.classList.add('xp-glow');
          const r = card.getBoundingClientRect();
          floatXp(now.xp - prev.xp, r.left + r.width / 2, r.top + 8);
        }
      }
      if (now.streak > prev.streak && streakEl) { streakEl.classList.remove('bump'); void streakEl.offsetWidth; streakEl.classList.add('bump'); }
      [...now.badges].filter(b => !prev.badges.has(b)).slice(0, 4).forEach((b, i) => setTimeout(() => badgePop(b), 300 + i * 450));
    }
    prev = now;
  }

  /* ——— api() sarmalayıcı: ödül ve hata anlarını yakalar ——— */
  function compileErrorLine(text) {
    const m = String(text || '').match(/(?:main\.cpp|\.cpp|<stdin>|^[^\s:]+):(\d+):(\d+):\s*(?:fatal\s+)?error/m) || String(text || '').match(/:(\d+):(\d+):\s*(?:fatal\s+)?error/);
    return m ? Number(m[1]) : 0;
  }
  let errorDecorations = [];
  function flashErrorLine(line) {
    const editor = typeof monacoEditor !== 'undefined' ? monacoEditor : null;
    if (!editor || !line || !window.monaco) return;
    errorDecorations = editor.deltaDecorations(errorDecorations, [{range: new monaco.Range(line, 1, line, 1), options: {isWholeLine: true, className: 'cpp-error-line', glyphMarginClassName: 'cpp-error-glyph'}}]);
    editor.revealLineInCenterIfOutsideViewport?.(line);
    setTimeout(() => { errorDecorations = editor.deltaDecorations(errorDecorations, []); }, 4000);
  }
  function onApiResult(url, body, result) {
    if (!result || typeof result !== 'object') return;
    const path = String(url).split('?')[0];
    if (path === '/api/submit') {
      if (result.correct) {
        const btn = $('#submit-task');
        const r = btn?.getBoundingClientRect();
        confetti(r ? r.left + r.width / 2 : lastPointer.x, r ? r.top + r.height / 2 : lastPointer.y, 30);
        setTimeout(() => { setCatMood('happy', 2600); buddySay(M('buddyRight')); }, 30);
      } else if (result.correct === false) {
        const res = result.result || {};
        flashErrorLine(compileErrorLine(res.error || res.compile_output || ''));
        setTimeout(() => { setCatMood('oops', 2400); buddySay(M('buddyWrong')); }, 30);
      }
    } else if (path === '/api/run') {
      if (result.compile_ok === false) { flashErrorLine(compileErrorLine(result.compile_output || result.error)); setCatMood('oops', 1800); }
    } else if (path === '/api/shop/buy' && !result.error) {
      confetti(lastPointer.x, lastPointer.y, 22);
    } else if (!result.error && (result.correct === true || Number(result.awarded_xp) > 0 || Number(result.reward) > 0 && /claim/.test(path))) {
      confetti(lastPointer.x, lastPointer.y, 22);
    }
  }

  /* ——— Görev ekranındaki kedi yoldaş ——— */
  function buddySay(text) {
    const bubble = $('.cat-buddy-bubble');
    if (!bubble || !text) return;
    const hint = $('#hint-box');
    if (hint && !hint.classList.contains('hidden')) return; // ipucu gösteriliyorsa onu kapatma
    typeText(bubble, text);
  }
  function typeText(el, text) {
    clearInterval(el._typing);
    el.classList.remove('bubble-pop'); void el.offsetWidth; el.classList.add('bubble-pop');
    if (reduce()) { el.textContent = text; return; }
    let i = 0;
    el.textContent = '';
    el._typing = setInterval(() => {
      i = Math.min(text.length, i + 2);
      el.textContent = text.slice(0, i);
      if (i >= text.length) clearInterval(el._typing);
    }, 18);
  }
  function mountBuddy() {
    const hint = $('#view-lesson #hint-box');
    if (!hint || hint.closest('.cat-buddy') || typeof window.renderCatCompanion !== 'function') return;
    const p = window.appState?.profile || {};
    const buddy = document.createElement('div');
    buddy.className = 'cat-buddy';
    const equipment = p.equipped_items && !Array.isArray(p.equipped_items) ? p.equipped_items : {};
    buddy.innerHTML = window.renderCatCompanion(equipment, false, M('buddyLabel'));
    hint.replaceWith(buddy);
    buddy.append(hint);
    const bubble = document.createElement('div');
    bubble.className = 'cat-buddy-bubble';
    bubble.setAttribute('aria-live', 'polite');
    buddy.append(bubble);
    typeText(bubble, M('buddyIdle'));
    // İpucu metni değişince balon gibi daktilo efektiyle yazılır.
    // Yazma sırasında oluşan ara metinler hedefin önekidir; onları yeni ipucu sanmamak için hedef saklanır.
    new MutationObserver(() => {
      const text = hint.textContent;
      if (hint.classList.contains('hidden') || (hint._target && hint._target.startsWith(text))) return;
      hint._target = text;
      typeText(hint, text);
    }).observe(hint, {childList: true, characterData: true, subtree: true});
  }

  /* ——— Örnek kodun yazılması ——— */
  function typeCode(block) {
    if (block._typed || reduce()) return;
    block._typed = true;
    const full = block.textContent;
    if (!full || full.length > 2400) return;
    const perFrame = Math.max(2, Math.ceil(full.length / 45));
    let i = 0;
    const text = document.createTextNode(''), caret = document.createElement('span');
    caret.className = 'type-caret';
    caret.setAttribute('aria-hidden', 'true');
    block.textContent = '';
    block.append(text, caret);
    const step = () => {
      if (!block.isConnected) return;
      i = Math.min(full.length, i + perFrame);
      text.data = full.slice(0, i);
      if (i < full.length) requestAnimationFrame(step); else setTimeout(() => caret.remove(), 900);
    };
    requestAnimationFrame(step);
  }

  /* ——— Terminal çıktısı satır satır ——— */
  function animateReport(report) {
    if (report._animated || reduce()) return;
    report._animated = true;
    report.classList.add('motion-in');
    report.querySelectorAll('pre').forEach(pre => {
      const lines = pre.textContent.split('\n');
      if (lines.length > 200) return;
      pre.textContent = '';
      lines.forEach((line, i) => {
        const span = document.createElement('span');
        span.className = 'term-line';
        span.style.setProperty('--i', String(Math.min(i, 40)));
        span.textContent = line || '​';
        pre.append(span);
      });
    });
  }

  /* ——— Dünya haritası: kedi bir sonraki bölgeye yürür, açılan bölgenin sisi dağılır ——— */
  const MAP_KEY = 'cppAdventureMapState';
  function readMapState() { try { return JSON.parse(localStorage.getItem(MAP_KEY) || '{}'); } catch (_) { return {}; } }
  function saveMapState(v) { try { localStorage.setItem(MAP_KEY, JSON.stringify(v)); } catch (_) {} }
  function decorateMap(canvas) {
    if (canvas._decorated) return;
    canvas._decorated = true;
    const zones = $$('.world-zone', canvas);
    if (!zones.length) return;
    const pid = window.appState?.profile?.id || 'x';
    const all = readMapState(), st = all[pid] || {};
    const locked = zones.filter(z => z.classList.contains('locked')).map(z => z.dataset.worldZone);
    if (Array.isArray(st.locked)) zones.forEach(z => { if (st.locked.includes(z.dataset.worldZone) && !z.classList.contains('locked')) { z.classList.add('fog-clearing'); setTimeout(() => z.classList.remove('fog-clearing'), 1900); } });
    const target = zones.find(z => z.classList.contains('open') && !z.classList.contains('cleared')) || [...zones].reverse().find(z => z.classList.contains('cleared')) || zones[0];
    const pos = z => ({x: z.style.getPropertyValue('--zone-x'), y: z.style.getPropertyValue('--zone-y'), id: z.dataset.worldZone});
    const to = pos(target), from = st.cat && zones.some(z => z.dataset.worldZone === st.cat.id) ? st.cat : to;
    const cat = document.createElement('div');
    cat.className = 'map-cat';
    cat.setAttribute('aria-hidden', 'true');
    const level = window.appState?.profile?.level || 1;
    cat.innerHTML = `<img src="${window.catGrowthAssetForLevel?.(level) || '/assets/cat-companion.png'}" alt="">`;
    cat.style.left = from.x; cat.style.top = from.y;
    canvas.append(cat);
    if (from.id !== to.id && !reduce()) {
      cat.classList.add('walking');
      requestAnimationFrame(() => requestAnimationFrame(() => { cat.style.left = to.x; cat.style.top = to.y; }));
      setTimeout(() => cat.classList.remove('walking'), 1550);
    } else { cat.style.left = to.x; cat.style.top = to.y; }
    all[pid] = {locked, cat: to};
    saveMapState(all);
  }
  window.resetMapWalk = () => { const all = readMapState(); delete all[window.appState?.profile?.id || 'x']; saveMapState(all); };

  /* ——— Görev ekranı: kod içeren görev metni ve tıklanabilir quiz şıkları ——— */
  function currentTaskInfo() {
    try { return appState.curriculum[currentChapter].tasks[currentTask]; } catch (_) { return null; }
  }
  // `kod` biçimindeki parçaları satır içi kod olarak gösterir (ters tırnaklar görünmez).
  function inlineCode(node) {
    const text = node.textContent;
    if (!text.includes('`')) return;
    const safe = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    node.innerHTML = safe.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');
  }
  function formatPrompt(el) {
    if (el._formatted) return;
    el._formatted = true;
    const text = el.textContent, cut = text.indexOf('\n');
    const head = cut < 0 ? text : text.slice(0, cut), rest = cut < 0 ? '' : text.slice(cut + 1);
    if (cut < 0 || !/[;{}]|std::|#include/.test(rest)) { inlineCode(el); return; }
    el.textContent = '';
    const p = document.createElement('span'); p.className = 'prompt-head'; p.textContent = head;
    const pre = document.createElement('pre'); pre.className = 'code-block prompt-code'; pre.textContent = rest;
    el.append(p, pre);
    inlineCode(p);
  }
  function quizOptions(input) {
    if (input._options) return;
    const task = currentTaskInfo();
    if (!task || task.kind !== 'quiz') return;
    let lg = 'tr';
    try { lg = lang; } catch (_) {}
    const prompt = task.prompt?.[lg] || task.prompt?.tr || '';
    const match = prompt.match(/\(([^()]*\/[^()]*)\)\s*$/);
    if (!match) return;
    input._options = true;
    const options = match[1].split(' / ').map(x => x.trim()).filter(Boolean);
    const row = document.createElement('div');
    row.className = 'quiz-options';
    row.setAttribute('role', 'group');
    row.setAttribute('aria-label', M('quizPick'));
    options.forEach((option, i) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'quiz-option';
      b.innerHTML = `<kbd>${i + 1}</kbd><span></span>`;
      b.querySelector('span').textContent = option;
      b.onclick = () => { input.value = option; row.querySelectorAll('.quiz-option').forEach(x => x.classList.toggle('picked', x === b)); input.focus(); };
      row.append(b);
    });
    input.placeholder = M('quizPick');
    const promptEl = document.querySelector('.quest-prompt');
    if (promptEl && !promptEl.querySelector('pre')) promptEl.textContent = promptEl.textContent.replace(/\s*\([^()]*\/[^()]*\)\s*$/, '');
    input.before(row);
    input.addEventListener('keydown', e => {
      if (!input.value && /^[1-9]$/.test(e.key) && row.children[+e.key - 1]) { e.preventDefault(); row.children[+e.key - 1].click(); }
    });
  }

  /* ——— Gözlemci: yeni çizilen öğeleri süsler ——— */
  function scan(root) {
    if (!(root instanceof Element)) return;
    const pick = sel => (root.matches(sel) ? [root] : []).concat($$(sel, root));
    pick('.code-block.lesson-example').forEach(typeCode);
    pick('.run-report').forEach(animateReport);
    pick('.world-map-canvas').forEach(c => setTimeout(() => decorateMap(c), 30));
    if (pick('#hint-box').length) mountBuddy();
    pick('.quest-prompt').forEach(formatPrompt);
    pick('#answer-input').forEach(quizOptions);
  }
  const observer = new MutationObserver(list => { for (const m of list) m.addedNodes.forEach(scan); });

  /* ——— Seviye atlama: konfeti ——— */
  document.addEventListener('cpp-adventure-level-up', () => setTimeout(() => {
    const card = $('.cat-levelup-card');
    if (!card) return;
    const r = card.getBoundingClientRect();
    setTimeout(() => confetti(r.left + r.width / 2, r.top + r.height * .45, 40), 650);
  }, 0));

  // Extension points (core.js): registered at load, so they are active before boot() renders.
  App.after('api', ([url, body], result) => onApiResult(url, body, result));
  App.after('setView', ([view]) => {
    const el = document.getElementById(`view-${view}`);
    if (el && !reduce()) { el.classList.remove('view-enter'); void el.offsetWidth; el.classList.add('view-enter'); }
  });
  App.after('renderSidebar', () => afterSidebar());

  document.addEventListener('DOMContentLoaded', () => {
    observer.observe(document.body, {childList: true, subtree: true});
    wake();
  });
})();
