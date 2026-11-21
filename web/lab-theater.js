// lab-theater.js — Kodun çalışmasını canlı gösteren animasyon motoru.
// Hem görsel laboratuvar hem de ders anlatımındaki "canlı anlatım" sahneleri bu motoru kullanır.
// Her adım; çalışan kod satırını, bellekteki hücreleri (adresleriyle), ekran çıktısını ve
// sahneye özel bilgileri (koşul, döngü, ifade, akış) taşır. Motor bunları bir sahneye çevirir:
// kod satırından belleğe uçan değerler, bellek şeridinde yerini alan değişkenler, pointer okları,
// dereference ışığı, yer değiştiren çubuklar, çağrı yığını, koşul çatalı ve daha fazlası.
(() => {
  const reduce = () => (window.matchMedia('(prefers-reduced-motion: reduce)').matches||document.body.classList.contains('reduce-motion'));
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const escHtml = v => String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const T = (tr, ru) => { try { return lang === 'ru' ? ru : tr; } catch (_) { return tr; } };
  const KEYWORDS = /\b(int|double|char|bool|void|auto|return|if|else|for|while|class|struct|public|private|new|delete|nullptr|const|std|cout|cin|swap|sort|stack|queue|true|false|template|typename|virtual|override|try|catch|throw|include|string|vector|map|set)\b/g;

  let active = null; // şu an çizilen sahne örneği (süre hesabı için)
  const duration = () => (active ? active.dur() : 600);

  function highlight(line) {
    const out = [];
    let rest = line, tail = '';
    const comment = rest.indexOf('//');
    if (comment >= 0) { tail = rest.slice(comment); rest = rest.slice(0, comment); }
    for (const part of rest.split(/("[^"]*"|'[^']*')/g)) {
      if (/^("[^"]*"|'[^']*')$/.test(part)) out.push(`<span class="tk-str">${escHtml(part)}</span>`);
      else out.push(escHtml(part).replace(KEYWORDS, '<span class="tk-kw">$1</span>').replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="tk-num">$1</span>'));
    }
    if (tail) out.push(`<span class="tk-com">${escHtml(tail)}</span>`);
    return out.join('');
  }

  /* ——— Ortak: anahtarlı çizim (giriş, değer değişimi, çıkış ve yeniden sıralama animasyonları) ——— */
  function keyed(container, items, keyOf, build, update, flip = false) {
    const existing = new Map($$(':scope > [data-key]', container).map(el => [el.dataset.key, el]));
    const before = flip && !reduce() ? new Map([...existing].map(([k, el]) => [k, el.getBoundingClientRect()])) : null;
    const seen = new Set();
    items.forEach((item, i) => {
      const key = String(keyOf(item, i));
      seen.add(key);
      let el = existing.get(key);
      if (!el || el.classList.contains('lt-leaving')) {
        el = build(item, i);
        el.dataset.key = key;
        el.classList.add('lt-enter');
        setTimeout(() => el.classList.remove('lt-enter'), duration() + 60);
      }
      container.append(el);
      update(el, item, i);
    });
    existing.forEach((el, key) => {
      if (seen.has(key) || el.classList.contains('lt-leaving')) return;
      el.classList.add('lt-leaving');
      if (before) { el.style.position = 'absolute'; el.style.visibility = 'hidden'; }
      setTimeout(() => el.remove(), duration());
    });
    if (before) existing.forEach((el, key) => {
      const old = before.get(key);
      if (!old || !seen.has(key)) return;
      const now = el.getBoundingClientRect(), dx = old.left - now.left, dy = old.top - now.top;
      if (Math.abs(dx) < 1 && Math.abs(dy) < 1) return;
      el.animate([{transform: `translate(${dx}px, ${dy}px)`}, {transform: 'none'}], {duration: duration(), easing: 'cubic-bezier(.2,.8,.2,1)'});
    });
  }

  function setValue(el, value) {
    const box = $('.lt-val', el);
    const text = String(value ?? '');
    if (box.dataset.v === text) return false;
    const had = box.dataset.v !== undefined, old = box.dataset.v;
    box.dataset.v = text;
    if (had && !reduce()) {
      const ghost = document.createElement('span');
      ghost.className = 'lt-val-old'; ghost.textContent = old;
      box.after(ghost);
      setTimeout(() => ghost.remove(), duration() + 100);
      box.classList.remove('lt-pop'); void box.offsetWidth; box.classList.add('lt-pop');
    }
    box.textContent = text;
    return true;
  }

  function cellNode() {
    const el = document.createElement('article');
    el.className = 'lt-cell';
    el.innerHTML = `<header><b class="lt-name"></b><i class="lt-type"></i></header><span class="lt-val"></span><small class="lt-addr"></small><em class="lt-badge"></em>`;
    return el;
  }
  const BADGES = {
    freed: () => T('serbest', 'освобождён'), leak: () => T('sızıntı!', 'утечка!'), dangling: () => T('sarkan pointer!', 'висячий указатель!'),
    allocated: () => 'new', deref: () => '*ptr', new: () => T('yeni', 'новое'), error: () => T('✗ hata', '✗ ошибка'),
    const: () => 'const', private: () => 'private', found: () => T('bulundu', 'найдено'), moved: () => T('taşındı', 'перемещён'), auto: () => T('otomatik silindi', 'удалён автоматически')
  };
  function updateCell(el, cell) {
    $('.lt-name', el).textContent = cell.name;
    $('.lt-type', el).textContent = cell.type || '';
    $('.lt-addr', el).textContent = cell.address || '';
    let alias = $('.lt-alias', el);
    if (cell.alias) {
      if (!alias) { alias = document.createElement('span'); alias.className = 'lt-alias'; $('header', el).append(alias); }
      alias.textContent = `& ${cell.alias}`;
    } else alias?.remove();
    setValue(el, cell.value);
    const keep = ['lt-enter', 'lt-slot'].filter(c => el.classList.contains(c)).join(' ');
    el.className = `lt-cell ${keep} ${cell.status ? 'st-' + cell.status : ''} ${cell.region === 'heap' ? 'is-heap' : ''}`;
    const strong = ['error', 'leak', 'dangling', 'freed', 'auto', 'moved', 'found'].includes(cell.status);
    $('.lt-badge', el).textContent = strong ? BADGES[cell.status]() : cell.badge || (BADGES[cell.status] ? BADGES[cell.status]() : '');
    el.dataset.name = cell.name;
    if (cell.points_to) el.dataset.pointsTo = cell.points_to; else delete el.dataset.pointsTo;
  }
  const cellsRow = (host, cells) => keyed(host, cells, c => c.name, cellNode, updateCell);

  /* ——— Bellek şeridi: değişkenlerin bellekteki yerini temsili olarak gösterir ——— */
  function byteSize(cell) {
    if (cell.size) return cell.size;
    const t = String(cell.type || '');
    if (/\*|ptr/.test(t)) return 8;
    if (/double|long/.test(t)) return 8;
    if (/^(char|bool)$/.test(t)) return 1;
    if (/string/.test(t)) return 32;
    if (/Node/.test(t)) return 16;
    return 4;
  }
  const hex = n => '0x' + n.toString(16).toUpperCase();
  function renderRam(host, cells) {
    const regions = [['stack', 'Stack'], ['heap', 'Heap']].map(([r, label]) => [r, label, cells.filter(c => (c.region === 'heap' ? 'heap' : 'stack') === r && /^0x/i.test(c.address || ''))]).filter(r => r[2].length);
    host.classList.toggle('is-empty', !regions.length);
    keyed(host, regions, r => r[0], ([r, label]) => {
      const row = document.createElement('div');
      row.className = `lt-ram-row is-${r}`;
      row.innerHTML = `<span class="lt-ram-label">${label}</span><div class="lt-ram-track"></div>`;
      return row;
    }, (row, [, , list]) => {
      const sorted = list.slice().sort((a, b) => parseInt(a.address, 16) - parseInt(b.address, 16));
      const items = [];
      let next = null;
      sorted.forEach(c => {
        const at = parseInt(c.address, 16), size = byteSize(c);
        if (next !== null && at > next) items.push({gap: true, key: `gap-${next}`, at: next, size: at - next});
        items.push({cell: c, key: c.name, at, size});
        next = at + size;
      });
      keyed($('.lt-ram-track', row), items, it => it.key, it => {
        const b = document.createElement('div');
        b.className = it.gap ? 'lt-ram-gap' : 'lt-ram-block';
        b.innerHTML = it.gap ? '' : '<b></b><span></span><small></small>';
        return b;
      }, (b, it) => {
        const units = it.gap ? 0.5 : Math.min(2.6, Math.max(0.8, it.size / 4));
        b.style.setProperty('--u', units);
        if (it.gap) return;
        const c = it.cell;
        $('b', b).textContent = c.name;
        const span = $('span', b), text = String(c.value ?? '');
        if (span.textContent !== text && span.textContent !== '' && !reduce()) { b.classList.remove('lt-ram-flash'); void b.offsetWidth; b.classList.add('lt-ram-flash'); }
        span.textContent = text;
        $('small', b).textContent = c.address;
        b.dataset.size = `${it.size}B`;
        b.className = `lt-ram-block ${c.status ? 'st-' + c.status : ''} ${b.classList.contains('lt-enter') ? 'lt-enter' : ''}`;
        b.dataset.name = c.name;
        b.title = `${c.type || ''} ${c.name} @ ${c.address} (${it.size} byte)`;
        if (c.points_to) b.dataset.pointsTo = c.points_to; else delete b.dataset.pointsTo;
      }, true);
    });
  }
  function drawRamArcs(ram) {
    if (!ram) return;
    let svg = $(':scope > svg', ram);
    if (!svg) { svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'lt-ram-arcs'); svg.setAttribute('aria-hidden', 'true'); ram.append(svg); }
    svg.innerHTML = '';
    const base = ram.getBoundingClientRect();
    svg.setAttribute('viewBox', `0 0 ${base.width} ${base.height}`);
    $$('.lt-ram-block[data-points-to]:not(.lt-leaving)', ram).forEach(src => {
      const dst = $(`.lt-ram-block[data-name="${CSS.escape(src.dataset.pointsTo)}"]:not(.lt-leaving)`, ram);
      if (!dst) return;
      const a = src.getBoundingClientRect(), b = dst.getBoundingClientRect();
      const x1 = a.left + a.width / 2 - base.left, x2 = b.left + b.width / 2 - base.left;
      let d;
      if (Math.abs(a.top - b.top) < 4) { const y = a.top - base.top, lift = Math.min(34, 14 + Math.abs(x2 - x1) * 0.18); d = `M${x1} ${y} C${x1} ${y - lift} ${x2} ${y - lift} ${x2} ${y - 2}`; }
      else { const y1 = a.bottom - base.top, y2 = b.top - base.top, my = (y1 + y2) / 2; d = `M${x1} ${y1} C${x1} ${my} ${x2} ${my} ${x2} ${y2 - 2}`; }
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', d);
      path.setAttribute('class', `lt-ram-arc ${src.classList.contains('st-dangling') ? 'dangling' : ''}`);
      path.setAttribute('marker-end', 'url(#lt-arrow-ram)');
      svg.append(path);
    });
    if (!$('#lt-arrow-ram')) {
      const defs = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      defs.setAttribute('width', '0'); defs.setAttribute('height', '0'); defs.style.position = 'absolute';
      defs.innerHTML = '<defs><marker id="lt-arrow-ram" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#5fe0cf"/></marker></defs>';
      document.body.append(defs);
    }
  }

  /* ——— Bellek sahnesi: stack çerçeveleri + heap, pointer okları ve bellek şeridi ——— */
  function renderMemory(scene, sim, step) {
    if (!scene.dataset.layout) {
      scene.dataset.layout = 'memory';
      const anyHeap = sim.steps.some(s => s.cells.some(c => c.region === 'heap'));
      scene.innerHTML = `<div class="lt-mem"><section class="lt-region lt-stack"><h4>Stack</h4><div class="lt-frames"></div></section>${anyHeap ? `<section class="lt-region lt-heap"><h4>Heap</h4><div class="lt-cells"></div></section>` : ''}</div>${sim.ram === false ? '' : `<div class="lt-ram" aria-label="${T('Bellek şeridi', 'Лента памяти')}"></div>`}`;
    }
    const stackCells = step.cells.filter(c => c.region !== 'heap');
    const frames = [...new Set(stackCells.map(c => c.frame || 'main'))];
    keyed($('.lt-frames', scene), frames, f => f, () => {
      const el = document.createElement('div');
      el.className = 'lt-frame';
      el.innerHTML = `<span class="lt-frame-name"></span><div class="lt-cells"></div>`;
      return el;
    }, (el, f) => {
      $('.lt-frame-name', el).textContent = f;
      cellsRow($('.lt-cells', el), stackCells.filter(c => (c.frame || 'main') === f));
    });
    const heap = $('.lt-heap .lt-cells', scene);
    if (heap) cellsRow(heap, step.cells.filter(c => c.region === 'heap'));
    const ram = $('.lt-ram', scene);
    if (ram) renderRam(ram, step.cells);
  }

  function drawWires(root, step) {
    const svg = $('.lt-wires', root), stage = $('.lt-stage', root);
    if (!svg || !stage) return;
    $$('path.lt-wire, circle.lt-spark', svg).forEach(n => n.remove());
    const base = stage.getBoundingClientRect();
    svg.setAttribute('viewBox', `0 0 ${base.width} ${base.height}`);
    $$('.lt-mem .lt-cell[data-points-to]:not(.lt-leaving)', stage).forEach(src => {
      const dst = $(`.lt-mem .lt-cell[data-name="${CSS.escape(src.dataset.pointsTo)}"]:not(.lt-leaving)`, stage);
      if (!dst) return;
      const a = src.getBoundingClientRect(), b = dst.getBoundingClientRect();
      const sameColumn = Math.abs(a.left - b.left) < 20 || (Math.abs(a.top - b.top) < 8 && Math.abs(a.left - b.left) < 260);
      let d;
      if (Math.abs(a.top - b.top) < 8) {
        const rightward = b.left > a.left;
        const x1 = (rightward ? a.left + a.width * 0.7 : a.left + a.width * 0.3) - base.left, y1 = a.top - base.top;
        const x2 = b.left + b.width / 2 - base.left, y2 = b.top - base.top;
        const lift = Math.min(60, 24 + Math.abs(x2 - x1) * 0.2);
        d = `M${x1} ${y1} C${x1} ${y1 - lift} ${x2} ${y2 - lift} ${x2} ${y2 - 4}`;
      } else if (sameColumn) {
        const x1 = a.right - base.left, y1 = a.top + a.height / 2 - base.top, x2 = b.right - base.left, y2 = b.top + b.height / 2 - base.top;
        const bend = Math.max(x1, x2) + 46;
        d = `M${x1} ${y1} C${bend} ${y1} ${bend} ${y2} ${x2 + 4} ${y2}`;
      } else {
        const rightward = b.left > a.left;
        const x1 = (rightward ? a.right : a.left) - base.left, y1 = a.top + a.height / 2 - base.top;
        const x2 = (rightward ? b.left : b.right) - base.left, y2 = b.top + b.height / 2 - base.top;
        const dx = (x2 - x1) * 0.5;
        d = `M${x1} ${y1} C${x1 + dx} ${y1} ${x2 - dx} ${y2} ${x2 + (rightward ? -4 : 4)} ${y2}`;
      }
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const status = src.classList.contains('st-dangling') ? 'dangling' : '';
      path.setAttribute('d', d);
      path.setAttribute('class', `lt-wire ${status}`);
      path.setAttribute('marker-end', 'url(#lt-arrow)');
      svg.append(path);
      const len = path.getTotalLength(), wireKey = `${src.dataset.pointsTo}`;
      if (!reduce() && src.dataset.wired !== wireKey) {
        path.style.strokeDasharray = `${len}`;
        path.style.strokeDashoffset = `${len}`;
        requestAnimationFrame(() => { path.style.transition = `stroke-dashoffset ${duration()}ms ease`; path.style.strokeDashoffset = '0'; });
        setTimeout(() => { path.style.strokeDasharray = status ? '6 6' : ''; path.style.transition = ''; }, duration() + 60);
      } else if (status) path.style.strokeDasharray = '6 6';
      src.dataset.wired = wireKey;
      if (src.classList.contains('st-deref-from') && !reduce()) {
        const spark = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        spark.setAttribute('r', '6');
        spark.setAttribute('class', 'lt-spark');
        const motion = document.createElementNS('http://www.w3.org/2000/svg', 'animateMotion');
        motion.setAttribute('dur', `${Math.max(.6, duration() / 600)}s`);
        motion.setAttribute('repeatCount', 'indefinite');
        motion.setAttribute('path', d);
        spark.append(motion);
        svg.append(spark);
      }
    });
    drawRamArcs($('.lt-ram', stage));
  }

  /* ——— Koşul çatalı ——— */
  function renderBranch(scene, sim, step) {
    const b = step.branch || {state: 'pending'};
    if (!scene.dataset.layout) {
      scene.dataset.layout = 'branch';
      scene.innerHTML = `<div class="lt-row lt-cells lt-branch-vars"></div>
        <div class="lt-branch">
          <div class="lt-diamond"><span class="lt-cond"></span><small class="lt-cond-result"></small></div>
          <svg class="lt-fork" viewBox="0 0 300 90" aria-hidden="true"><path class="lt-path-true" d="M150 4 C150 44 60 40 60 86"/><path class="lt-path-false" d="M150 4 C150 44 240 40 240 86"/><circle class="lt-token" r="8" cx="150" cy="4"/></svg>
          <div class="lt-exits"><div class="lt-exit lt-exit-true">true<small></small></div><div class="lt-exit lt-exit-false">false<small></small></div></div>
        </div>`;
    }
    cellsRow($('.lt-branch-vars', scene), step.cells.filter(c => c.region !== 'branch'));
    const exits = b.exits || sim.exits || ['std::cout << "true"', 'std::cout << "false"'];
    $('.lt-exit-true small', scene).textContent = exits[0];
    $('.lt-exit-false small', scene).textContent = exits[1];
    const cond = $('.lt-cond', scene), html = `${escHtml(b.left)} <b>${escHtml(b.op)}</b> ${escHtml(b.right)}`;
    if (cond.dataset.html !== html) { cond.dataset.html = html; cond.innerHTML = html; if (!reduce()) { cond.classList.remove('lt-pop'); void cond.offsetWidth; cond.classList.add('lt-pop'); } }
    $('.lt-cond-result', scene).textContent = b.state === 'true' || b.state === 'false' ? `→ ${b.state}` : b.state === 'checking' ? T('kontrol ediliyor…', 'проверяется…') : '';
    const branch = $('.lt-branch', scene);
    branch.dataset.state = b.state;
    const token = $('.lt-token', scene), gen = (token._gen = (token._gen || 0) + 1);
    if (b.state === 'true' || b.state === 'false') {
      const path = $(`.lt-path-${b.state}`, scene);
      if (reduce()) { const p = path.getPointAtLength(path.getTotalLength()); token.setAttribute('cx', p.x); token.setAttribute('cy', p.y); }
      else {
        const total = path.getTotalLength(), start = performance.now(), dur = duration() * 1.2;
        const tick = now => { if (token._gen !== gen) return; const t = Math.min(1, (now - start) / dur), p = path.getPointAtLength(total * (1 - Math.pow(1 - t, 2))); token.setAttribute('cx', p.x); token.setAttribute('cy', p.y); if (t < 1) requestAnimationFrame(tick); };
        requestAnimationFrame(tick);
      }
    } else { token.setAttribute('cx', 150); token.setAttribute('cy', 4); }
  }

  /* ——— Döngü izi ——— */
  function renderLoop(scene, sim, step) {
    const loop = step.loop || {values: [], done: 0};
    if (!scene.dataset.layout) {
      scene.dataset.layout = 'loop';
      scene.innerHTML = `<div class="lt-row lt-cells lt-loop-var"></div><div class="lt-track"><img class="lt-runner" src="/assets/cat-companion.png" alt=""><ol class="lt-laps"></ol></div><div class="lt-loop-exit"></div>`;
      $('.lt-laps', scene).innerHTML = loop.values.map((v, i) => `<li><b>${escHtml(v)}</b><small>${T('tur', 'итер.')} ${i + 1}</small></li>`).join('') || `<li class="lt-empty">${T('Koşul en baştan yanlış; döngü hiç çalışmadı.', 'Условие ложно с самого начала; цикл не выполнился.')}</li>`;
    }
    keyed($('.lt-loop-var', scene), step.cells, c => c.name, cellNode, (el, c) => updateCell(el, sim.lab_id ? Object.assign({}, c, {status: step.index > 0 && !loop.finished ? 'changed' : c.status}) : c));
    const laps = $$('.lt-laps li', scene);
    laps.forEach((li, i) => { li.classList.toggle('done', i < loop.done - 1 || (loop.finished && i < loop.done)); li.classList.toggle('current', !loop.finished && i === loop.done - 1); });
    const runner = $('.lt-runner', scene), target = laps[Math.max(0, Math.min(laps.length - 1, loop.done - 1))];
    if (target && loop.done > 0) {
      runner.style.opacity = '1';
      runner.style.transform = `translateX(${target.offsetLeft + target.offsetWidth / 2 - 18}px)`;
      const track = $('.lt-track', scene);
      const left = target.offsetLeft - track.clientWidth / 2 + target.offsetWidth / 2;
      if (track.scrollWidth > track.clientWidth) track.scrollTo({left, behavior: reduce() ? 'auto' : 'smooth'});
      if (!reduce()) { runner.classList.remove('lt-hop'); void runner.offsetWidth; runner.classList.add('lt-hop'); }
    } else runner.style.opacity = '0';
    $('.lt-loop-exit', scene).textContent = loop.finished ? (loop.exitText || T('Koşul yanlış oldu → döngüden çıkıldı', 'Условие стало ложным → выход из цикла')) : loop.check || '';
    $('.lt-loop-exit', scene).classList.toggle('is-check', !loop.finished && !!loop.check);
  }

  /* ——— Dizi, vector, string, map ——— */
  function renderArray(scene, sim, step) {
    if (!scene.dataset.layout) { scene.dataset.layout = 'array'; scene.innerHTML = `<div class="lt-row lt-cells lt-array-vars"></div><div class="lt-array-name"></div><div class="lt-array"></div><div class="lt-array-note"></div>`; }
    const slots = step.cells.filter(c => c.region === 'array' || c.index !== undefined), vars = step.cells.filter(c => !slots.includes(c));
    cellsRow($('.lt-array-vars', scene), vars);
    $('.lt-array-name', scene).textContent = sim.array_name || '';
    keyed($('.lt-array', scene), slots, c => c.name, c => {
      const el = cellNode(c); el.classList.add('lt-slot');
      const idx = document.createElement('span'); idx.className = 'lt-index'; el.append(idx);
      return el;
    }, (el, c, i) => {
      updateCell(el, c); el.classList.add('lt-slot');
      el.style.setProperty('--i', i);
      $('.lt-index', el).textContent = c.label ?? `[${c.index ?? i}]`;
    }, true);
    $('.lt-array', scene).classList.toggle('is-empty', !slots.length);
    $('.lt-array', scene).classList.toggle('is-many', slots.length > 5);
    const act = slots.find(c => c.status === 'active');
    $('.lt-array-note', scene).textContent = step.note ?? (act && /^0x/.test(act.address || '') && act.index !== undefined ? `${act.name} = ${act.value} · ${T('adres', 'адрес')} ${act.address} = 0x1000 + ${act.index} × 4` : slots[0]?.status === 'indexed' ? T('İndeksler 0\'dan başlar; her int 4 bayt yer kaplar.', 'Индексы начинаются с 0; каждый int занимает 4 байта.') : '');
  }

  /* ——— Sıralama / arama çubukları (yer değiştirme animasyonlu) ——— */
  function renderBars(scene, sim, step, prevStep, inst) {
    const values = step.cells.map(c => Number(c.value));
    if (!scene.dataset.layout) {
      scene.dataset.layout = 'bars';
      scene.innerHTML = `<div class="lt-bars"></div><div class="lt-legend"><span class="lg-cmp">${T('karşılaştırılan', 'сравнение')}</span><span class="lg-swap">${T('yer değiştiren', 'перестановка')}</span><span class="lg-found">${T('bulunan', 'найдено')}</span></div>`;
      inst.ids = values.map((_, i) => `b${i}`);
      inst.values = values.slice();
    }
    // Değer kimliğini adımlar arasında takip et: aynı değer yer değiştirince çubuğun kendisi kayar.
    const prevIds = inst.ids, prevValues = inst.values, ids = new Array(values.length), used = new Set();
    values.forEach((v, i) => { if (prevValues[i] === v && prevIds[i] && !used.has(prevIds[i])) { ids[i] = prevIds[i]; used.add(prevIds[i]); } });
    values.forEach((v, i) => {
      if (ids[i]) return;
      let best = -1, dist = Infinity;
      prevValues.forEach((pv, j) => { if (pv === v && !used.has(prevIds[j]) && Math.abs(j - i) < dist) { best = j; dist = Math.abs(j - i); } });
      ids[i] = best >= 0 ? prevIds[best] : `b${Date.now()}${i}`;
      used.add(ids[i]);
    });
    inst.ids = ids; inst.values = values.slice();
    const min = Math.min(0, ...values), max = Math.max(1, ...values), span = max - min || 1;
    const host = $('.lt-bars', scene), n = values.length;
    const changed = prevStep ? prevStep.cells.map(c => Number(c.value)).some((v, i) => v !== values[i]) : false;
    const items = values.map((v, i) => ({v, i, id: ids[i], status: step.cells[i].status}));
    keyed(host, items, it => it.id, () => {
      const el = document.createElement('div');
      el.className = 'lt-bar';
      el.innerHTML = '<span class="lt-bar-fill"></span><b></b><small></small>';
      return el;
    }, (el, it) => {
      el.style.setProperty('--x', `${(it.i / n) * 100}%`);
      el.style.setProperty('--w', `${100 / n}%`);
      el.style.setProperty('--h', String(Math.max(6, ((it.v - min) / span) * 100)));
      el.classList.toggle('cmp', it.status === 'active' && !changed);
      el.classList.toggle('swap', it.status === 'active' && changed);
      el.classList.toggle('found', it.status === 'found' || (step.output !== '' && !sim.no_found && String(it.i) === step.output));
      el.classList.toggle('dim', it.status === 'dim');
      $('b', el).textContent = it.v;
      $('small', el).textContent = it.i;
    });
  }

  /* ——— Çağrı yığını (fonksiyon / özyineleme) ——— */
  function renderCalls(scene, sim, step, prev, inst) {
    if (!scene.dataset.layout) { scene.dataset.layout = 'calls'; scene.innerHTML = `<section class="lt-region lt-callstack"><h4>${T('Çağrı yığını', 'Стек вызовов')}</h4><div class="lt-frames"></div></section>`; }
    const frames = [...new Set(step.cells.map(c => c.frame || 'main'))];
    const host = $('.lt-frames', scene);
    const before = new Map($$(':scope > [data-key]', host).map(el => [el.dataset.key, el.getBoundingClientRect()]));
    keyed(host, frames, f => f, () => {
      const el = document.createElement('div');
      el.className = 'lt-frame';
      el.innerHTML = '<span class="lt-frame-name"></span><div class="lt-cells"></div>';
      return el;
    }, (el, f, i) => {
      $('.lt-frame-name', el).textContent = f;
      el.classList.toggle('is-top', i === frames.length - 1);
      cellsRow($('.lt-cells', el), step.cells.filter(c => (c.frame || 'main') === f));
    });
    // Dönen değer: kaldırılan çerçeveden, değeri değişen hücreye doğru uçan bir baloncuk.
    const target = $('.lt-cell.st-changed', host);
    before.forEach((rect, key) => {
      if (frames.includes(key) || !target || reduce() || !inst.forward) return;
      inst.bubbled = true;
      const t = target.getBoundingClientRect();
      const bubble = document.createElement('div');
      bubble.className = 'lt-return-bubble';
      bubble.textContent = `return ${$('.lt-val', target).textContent}`;
      bubble.style.left = `${rect.left + rect.width / 2}px`; bubble.style.top = `${rect.top + rect.height / 2}px`;
      document.body.append(bubble);
      requestAnimationFrame(() => { bubble.style.transform = `translate(${t.left + t.width / 2 - rect.left - rect.width / 2}px, ${t.top + t.height / 2 - rect.top - rect.height / 2}px) scale(.8)`; bubble.style.opacity = '.0'; });
      setTimeout(() => bubble.remove(), duration() + 250);
    });
  }

  /* ——— Stack (LIFO) ve queue (FIFO) ——— */
  function renderLifo(scene, sim, step) {
    if (!scene.dataset.layout) { scene.dataset.layout = 'lifo'; scene.innerHTML = `<div class="lt-tube"><span class="lt-tube-label">top ↑</span><div class="lt-tube-items"></div></div><div class="lt-ds-note">LIFO · Last In, First Out</div>`; }
    keyed($('.lt-tube-items', scene), step.cells, c => c.item || c.name, cellNode, updateCell);
    $('.lt-tube', scene).classList.toggle('is-empty', !step.cells.length);
  }
  function renderFifo(scene, sim, step) {
    if (!scene.dataset.layout) { scene.dataset.layout = 'fifo'; scene.innerHTML = `<div class="lt-pipe"><span class="lt-pipe-end">front ←</span><div class="lt-pipe-items"></div><span class="lt-pipe-end">← back</span></div><div class="lt-ds-note">FIFO · First In, First Out</div>`; }
    keyed($('.lt-pipe-items', scene), step.cells, c => c.item || c.name, cellNode, updateCell);
  }

  /* ——— Sınıf ve nesne ——— */
  function renderObject(scene, sim, step) {
    if (!scene.dataset.layout) { scene.dataset.layout = 'object'; scene.innerHTML = `<div class="lt-oop"><div class="lt-blueprint-slot"></div><div class="lt-instances"></div></div>`; }
    const bp = step.cells.find(c => c.region === 'blueprint');
    const slot = $('.lt-blueprint-slot', scene);
    if (bp && !slot.firstChild) slot.innerHTML = `<article class="lt-blueprint"><header>${escHtml(bp.kind || 'class')} ${escHtml(bp.name)}</header><ul>${(bp.fields || []).map(f => `<li>${escHtml(f)}</li>`).join('')}${(bp.methods || []).map(m => `<li class="m">${escHtml(m)}</li>`).join('')}</ul><small>${T('şablon · bellekte yer kaplamaz', 'шаблон · не занимает память')}</small></article>`;
    const objects = [...new Set(step.cells.filter(c => c.region === 'object').map(c => c.frame))];
    keyed($('.lt-instances', scene), objects, o => o, () => {
      const el = document.createElement('article');
      el.className = 'lt-object';
      el.innerHTML = `<header></header><div class="lt-cells"></div>`;
      return el;
    }, (el, o) => {
      $('header', el).textContent = `${sim.class_name || bp?.name || 'Cat'} ${o}`;
      keyed($('.lt-cells', el), step.cells.filter(c => c.frame === o && c.region === 'object'), c => c.name, cellNode, (cellEl, c) => updateCell(cellEl, Object.assign({}, c, {name: c.name.split('.').pop()})));
    });
    $('.lt-instances', scene).classList.toggle('is-empty', !objects.length);
  }

  /* ——— Akış: derleme, cout akışı, dosya, istisna, şablon üretimi ——— */
  function renderFlow(scene, sim, step) {
    const stages = sim.stages || [];
    if (!scene.dataset.layout) {
      scene.dataset.layout = 'flow';
      scene.innerHTML = `<div class="lt-flow" style="--n:${stages.length}">${stages.map((s, i) => `<div class="lt-stagebox" data-idx="${i}"><span class="lt-stage-icon">${escHtml(s.icon)}</span><b>${escHtml(s.label)}</b><small>${escHtml(s.sub || '')}</small></div>`).join('<i class="lt-flow-link" aria-hidden="true"></i>')}<div class="lt-packet"></div></div><div class="lt-row lt-cells lt-flow-vars"></div>`;
    }
    const flow = $('.lt-flow', scene), at = Math.max(-1, Math.min(stages.length - 1, step.stage ?? -1));
    $$('.lt-stagebox', flow).forEach((box, i) => { box.classList.toggle('done', i < at); box.classList.toggle('current', i === at); box.classList.toggle('is-error', i === at && step.stage_state === 'error'); });
    $$('.lt-flow-link', flow).forEach((link, i) => link.classList.toggle('done', i < at));
    const packet = $('.lt-packet', flow), box = $(`.lt-stagebox[data-idx="${at}"]`, flow);
    if (box && step.payload) {
      packet.textContent = step.payload;
      packet.classList.toggle('is-error', step.stage_state === 'error');
      packet.style.opacity = '1';
      packet.style.transform = `translate(${box.offsetLeft + box.offsetWidth / 2}px, ${box.offsetTop - 4}px) translate(-50%, -100%)`;
    } else packet.style.opacity = '0';
    cellsRow($('.lt-flow-vars', scene), step.cells);
  }

  /* ——— İfade: işlem sırasını adım adım indirger ——— */
  function renderExpr(scene, sim, step) {
    if (!scene.dataset.layout) { scene.dataset.layout = 'expr'; scene.innerHTML = `<div class="lt-row lt-cells lt-expr-vars"></div><div class="lt-expr" aria-live="polite"></div><div class="lt-expr-rule"></div>`; }
    cellsRow($('.lt-expr-vars', scene), step.cells);
    const expr = $('.lt-expr', scene), html = (step.expr || []).map(p => p.k === 'hi' ? `<mark>${escHtml(p.t)}</mark>` : p.k === 'new' ? `<b class="lt-new-val">${escHtml(p.t)}</b>` : `<span>${escHtml(p.t)}</span>`).join('');
    if (expr.dataset.html !== html) { expr.dataset.html = html; expr.innerHTML = html; }
    $('.lt-expr-rule', scene).textContent = step.rule || '';
  }

  const RENDERERS = {memory: renderMemory, branch: renderBranch, loop: renderLoop, array: renderArray, bars: renderBars, calls: renderCalls, lifo: renderLifo, fifo: renderFifo, object: renderObject, flow: renderFlow, expr: renderExpr};

  /* ——— Değer uçuşu: çalışan satırdaki değer, bellekteki yerine uçar ——— */
  function flyValues(inst, step) {
    if (reduce() || !inst.forward || inst.bubbled) return;
    const scene = inst.scene, line = $('.lt-lines li.active', inst.root);
    let count = 0;
    step.cells.forEach(cell => {
      if (count >= 3 || !['new', 'changed', 'allocated'].includes(cell.status) || cell.value === '' || cell.value === undefined) return;
      const el = $(`.lt-cell[data-name="${CSS.escape(cell.name)}"]:not(.lt-leaving)`, scene);
      if (!el) return;
      let src = null;
      if (cell.points_to) src = $(`.lt-cell[data-name="${CSS.escape(cell.points_to)}"] .lt-addr`, scene);
      if (!src) src = line;
      if (!src) return;
      const a = src.getBoundingClientRect(), box = $('.lt-val', el), b = box.getBoundingClientRect();
      if (!a.width || !b.width || a.bottom < 0 || a.top > innerHeight) return;
      count += 1;
      const chip = document.createElement('div');
      chip.className = `lt-fly ${cell.points_to ? 'is-addr' : ''}`;
      chip.textContent = String(cell.value);
      const sx = cell.points_to ? a.left + a.width / 2 : Math.min(a.right - 30, a.left + 60 + Math.min(260, a.width * 0.35)), sy = a.top + a.height / 2;
      chip.style.left = `${sx}px`; chip.style.top = `${sy}px`;
      document.body.append(chip);
      box.classList.add('lt-await');
      const dx = b.left + b.width / 2 - sx, dy = b.top + b.height / 2 - sy, dur = Math.max(420, duration() * 1.05);
      const anim = chip.animate([
        {transform: 'translate(-50%,-50%) scale(.6)', opacity: 0},
        {transform: 'translate(-50%,-50%) scale(1.05)', opacity: 1, offset: 0.15},
        {transform: `translate(calc(-50% + ${dx * 0.5}px), calc(-50% + ${dy * 0.5 - 40}px)) scale(1.1)`, opacity: 1, offset: 0.55},
        {transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(.9)`, opacity: 1}
      ], {duration: dur, easing: 'cubic-bezier(.45,.05,.3,1)'});
      const land = () => { chip.remove(); box.classList.remove('lt-await', 'lt-pop'); void box.offsetWidth; box.classList.add('lt-pop'); el.classList.add('lt-landed'); setTimeout(() => el.classList.remove('lt-landed'), 500); };
      anim.onfinish = land; anim.oncancel = land;
      setTimeout(() => { if (chip.isConnected) land(); }, dur + 400);
    });
  }

  /* ——— Sahne örneği ——— */
  function create(host, options = {}) {
    const root = document.createElement('div');
    root.className = `lab-theater ${options.className || ''}`;
    root.innerHTML = `<div class="lt-code" aria-label="C++"><div class="lt-code-head"><i></i><i></i><i></i><span>${escHtml(options.file || 'main.cpp')}</span></div><div class="lt-code-body"><span class="lt-cursor" aria-hidden="true"></span><ol class="lt-lines"></ol></div></div>
      <div class="lt-stage"><svg class="lt-wires" aria-hidden="true"><defs><marker id="lt-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker></defs></svg><div class="lt-scene"></div></div>
      <div class="lt-console"><span class="lt-prompt">›_</span><code class="lt-out"></code></div>
      <div class="lt-timeline" role="group" aria-label="${T('Adımlar', 'Шаги')}"></div>`;
    host.append(root);
    const inst = {
      root, scene: $('.lt-scene', root), sim: null, index: -1, ids: [], values: [], wiresTimer: 0, forward: false, bubbled: false,
      dur: options.duration || (() => 600),
      render(sim, index) {
        if (!sim || !sim.steps?.length) return;
        active = inst;
        const fresh = inst.sim !== sim;
        if (fresh) {
          inst.scene.innerHTML = ''; delete inst.scene.dataset.layout; $('.lt-out', root).textContent = ''; $$('.lt-wire, .lt-spark', root).forEach(n => n.remove());
          Object.assign(inst, {sim, index: -1, ids: [], values: []});
          $('.lt-timeline', root).innerHTML = sim.steps.map((_, i) => `<button type="button" data-idx="${i}" aria-label="${T('Adım', 'Шаг')} ${i + 1}"></button>`).join('');
          $$('.lt-timeline button', root).forEach(btn => btn.onclick = () => options.onSeek?.(Number(btn.dataset.idx)));
          $('.lt-timeline', root).classList.toggle('is-dense', sim.steps.length > 18);
        }
        const steps = sim.steps, i = Math.max(0, Math.min(index, steps.length - 1)), step = steps[i];
        const prev = inst.index >= 0 ? steps[inst.index] : null;
        inst.forward = inst.index === i - 1;
        inst.bubbled = false;
        root.style.setProperty('--lt-dur', `${duration()}ms`);
        root.dataset.visual = sim.visual || 'memory';
        renderCode(root, sim, step, fresh);
        (RENDERERS[sim.visual] || renderMemory)(inst.scene, sim, step, prev, inst);
        renderConsole(root, step, inst.forward ? prev : null);
        $$('.lt-timeline button', root).forEach((btn, k) => { btn.classList.toggle('done', k < i); btn.classList.toggle('current', k === i); });
        clearTimeout(inst.wiresTimer);
        if ((sim.visual || 'memory') === 'memory') {
          if (fresh) $$('.lt-cell', inst.scene).forEach(c => delete c.dataset.wired);
          requestAnimationFrame(() => drawWires(root, step));
          inst.wiresTimer = setTimeout(() => drawWires(root, step), duration() + 80);
        }
        requestAnimationFrame(() => { active = inst; flyValues(inst, step); active = null; });
        inst.index = i;
        active = null;
      },
      relayout() { if (inst.sim && (inst.sim.visual || 'memory') === 'memory') { active = inst; drawWires(root, inst.sim.steps[inst.index] || inst.sim.steps[0]); active = null; } }
    };
    return inst;
  }

  function renderCode(root, sim, step, fresh) {
    const list = $('.lt-lines', root);
    if (fresh || list.dataset.count !== String((sim.code || []).length)) {
      list.dataset.count = String((sim.code || []).length);
      list.innerHTML = (sim.code || []).map(line => `<li>${highlight(line) || '&nbsp;'}</li>`).join('');
    }
    const items = $$('li', list);
    items.forEach((li, i) => { li.classList.toggle('active', i + 1 === step.line); li.classList.toggle('ran', i + 1 < step.line); });
    const cursor = $('.lt-cursor', root), current = items[step.line - 1];
    if (current) {
      cursor.style.opacity = '1'; cursor.style.transform = `translateY(${current.offsetTop}px)`; cursor.style.height = `${current.offsetHeight}px`;
      const body = $('.lt-code-body', root);
      if (current.offsetTop < body.scrollTop || current.offsetTop + current.offsetHeight > body.scrollTop + body.clientHeight) body.scrollTo({top: current.offsetTop - body.clientHeight / 2, behavior: reduce() ? 'auto' : 'smooth'});
    } else cursor.style.opacity = '0';
    $('.lt-code', root).classList.toggle('hidden', !(sim.code || []).length);
  }

  function renderConsole(root, step, prev) {
    const out = $('.lt-out', root), text = step.output || '', before = prev?.output || '';
    if (text && text.startsWith(before) && text !== before) out.innerHTML = `${escHtml(before)}<b class="lt-new">${escHtml(text.slice(before.length))}</b>`;
    else out.textContent = text;
    $('.lt-console', root).classList.toggle('empty', !text);
  }

  window.CppTheater = {create, highlight};

  /* ——— Görsel laboratuvar bağlantısı ——— */
  let labInst = null;
  const labDuration = () => { let speed = 1100; try { speed = labSpeed; } catch (_) {} return Math.max(220, Math.min(900, speed * 0.55)); };
  function renderLabTheater() {
    let sim = null, index = 0;
    try { sim = labSimulation; index = labStepIndex; } catch (_) { return; }
    if (!sim || !sim.steps?.length) return;
    const visual = $('.lab-visual');
    if (!visual) return;
    if (!labInst || !visual.contains(labInst.root)) {
      const slot = document.createElement('div');
      slot.className = 'lab-theater-slot';
      const anchor = $('.lab-memory-title', visual) || $('#lab-memory-grid', visual);
      if (anchor) anchor.before(slot); else visual.append(slot);
      labInst = create(slot, {duration: labDuration, onSeek: i => { try { labStepIndex = i; renderLabBoard(); } catch (_) {} }});
      slot.insertAdjacentHTML('beforeend', `<p class="lt-hint"><kbd>←</kbd><kbd>→</kbd> ${T('adım', 'шаг')} · <kbd>${T('Boşluk', 'Пробел')}</kbd> ${T('oynat / duraklat', 'играть / пауза')} · ${T('çizgiye tıklayıp istediğin adıma atla', 'нажми на полоску, чтобы перейти к шагу')}</p>`);
    }
    labInst.render(sim, index);
  }

  App.after('renderLabBoard', () => renderLabTheater());

  document.addEventListener('DOMContentLoaded', () => {
    let resizeTimer = 0;
    window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { try { labInst?.relayout(); } catch (_) {} }, 120); });
    // Klavye: ← → adım, boşluk oynat/duraklat (yalnızca laboratuvar açıkken ve yazı alanında değilken).
    document.addEventListener('keydown', event => {
      const labs = $('#view-labs');
      if (!labs || labs.classList.contains('hidden') || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.target.closest('input, textarea, select, [contenteditable], .monaco-editor')) return;
      const id = {ArrowRight: '#lab-next', ArrowLeft: '#lab-back', ' ': '#lab-play'}[event.key];
      const btn = id && $(id, labs);
      if (!btn || btn.disabled || !btn.offsetParent) return;
      event.preventDefault();
      btn.click();
    });
  });
})();
