// onboarding.js — Giriş ekranı: "Kim oynuyor?" profil seçimi ve interaktif karakter seçici.
// Emoji yerine C++ Adventure'ın kedi karakterlerinden biri seçilir; seçilen karakter canlı bir sahnede
// zıplar, konuşur ve fareyi takip eder. Kayıt üç adımlıdır: karakter → isim → (isteğe bağlı) PIN.
// Kayıttan sonra profil doğrudan açılır. Ayrıca tüm uygulamada avatarların karakter resmiyle gösterilmesini sağlar.
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const lg = () => { try { return lang === 'ru' ? 'ru' : 'tr'; } catch (_) { return 'tr'; } };
  const T = (tr, ru) => lg() === 'ru' ? ru : tr;
  const reduce = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const CHARS = [
    {id: 'c:buddy', img: 'cat-companion.png', color: '#ffa45c', name: ['Pati', 'Пати'], role: ['Neşeli yol arkadaşı', 'Весёлый спутник'], line: ['Miyav! İlk programını birlikte yazalım mı?', 'Мяу! Напишем первую программу вместе?'], stats: [4, 4, 3]},
    {id: 'c:prof', img: 'cat-professor.png', color: '#c9a8ff', name: ['Profesör', 'Профессор'], role: ['Kitap kurdu bilge', 'Мудрый книжный червь'], line: ['Her satırın bir nedeni vardır. Hadi keşfedelim!', 'У каждой строки есть причина. Давай разберёмся!'], stats: [5, 4, 2]},
    {id: 'c:teach', img: 'cat-teacher.png', color: '#5fe0cf', name: ['Rehber', 'Наставник'], role: ['Sabırlı öğretmen', 'Терпеливый учитель'], line: ['Takıldığın her yerde ipucuyla yanındayım.', 'Где бы ты ни застрял — я рядом с подсказкой.'], stats: [4, 5, 2]},
    {id: 'c:hack', img: 'cat-hacker.png', color: '#a885ff', name: ['Hacker', 'Хакер'], role: ['Gece kodlayan dâhi', 'Гений ночного кода'], line: ['Klavye ısındı. Derleyelim mi?', 'Клавиатура разогрета. Компилируем?'], stats: [3, 2, 5]},
    {id: 'c:debug', img: 'cat-debugger.png', color: '#70e0ae', name: ['Hata Avcısı', 'Охотник за багами'], role: ['Hiçbir hata kaçamaz', 'Ни один баг не уйдёт'], line: ['Bir hata mı gördüm? Büyüteç hazır!', 'Кажется, баг? Лупа наготове!'], stats: [4, 4, 3]},
    {id: 'c:wiz', img: 'cat-wizard.png', color: '#7aa6ff', name: ['Büyücü', 'Волшебник'], role: ['İleri C++ büyücüsü', 'Маг продвинутого C++'], line: ['Şablonlar, lambdalar… hepsi birer büyü!', 'Шаблоны, лямбды… сплошное волшебство!'], stats: [5, 3, 3]},
    {id: 'c:boss', img: 'cat-boss.png', color: '#ffd58a', name: ['Zırhlı Lider', 'Бронированный лидер'], role: ['Boss savaşlarının efendisi', 'Повелитель битв с боссами'], line: ['Hiçbir boss bana karşı koyamaz!', 'Ни один босс не устоит передо мной!'], stats: [2, 4, 5]},
  ];
  const STAT_NAMES = () => [T('Merak', 'Любопытство'), T('Sabır', 'Терпение'), T('Hız', 'Скорость')];
  const pick = pair => pair[lg() === 'ru' ? 1 : 0];
  const charOf = avatar => CHARS.find(c => c.id === avatar);

  window.CppCharacters = CHARS;
  window.avatarHtml = (avatar, cls = '') => {
    const c = charOf(avatar);
    return c ? `<img class="avatar-img ${cls}" src="/assets/${c.img}" alt="${esc(pick(c.name))}" draggable="false">` : `<span class="avatar-emoji ${cls}">${esc(avatar || '🐱')}</span>`;
  };

  /* ——— Karakter seçici (sihirbaz) ——— */
  let wiz = null; // {existing, step, index, name, pin, removePin, currentPin, error}

  function openWizard(existing = null) {
    const index = Math.max(0, CHARS.findIndex(c => c.id === existing?.avatar));
    wiz = {existing, step: 0, index, name: existing?.name || '', pin: '', currentPin: '', removePin: false, error: ''};
    paintWizard(true);
    document.removeEventListener('keydown', keys, true);
    document.addEventListener('keydown', keys, true);
    setTimeout(() => $(`#onboard-overlay .ob-card[data-idx="${wiz.index}"]`)?.focus(), 80);
  }

  function overlay() {
    let host = $('#onboard-overlay');
    if (!host) { host = document.createElement('div'); host.id = 'onboard-overlay'; document.body.append(host); }
    return host;
  }
  function closeWizard() { $('#onboard-overlay')?.remove(); wiz = null; document.body.classList.remove('onboard-open'); document.removeEventListener('keydown', keys, true); }

  function paintWizard(fresh = false) {
    const host = overlay(), c = CHARS[wiz.index], first = !profiles.length && !wiz.existing;
    document.body.classList.add('onboard-open');
    host.style.setProperty('--accent', c.color);
    const steps = [T('Karakter', 'Персонаж'), T('İsim', 'Имя'), T('Güvenlik', 'Защита')];
    if (fresh || !$('.ob-shell', host)) {
      host.innerHTML = `<div class="ob-shell" role="dialog" aria-modal="true" aria-labelledby="ob-title">
        <section class="ob-stage" aria-live="polite">
          <div class="ob-sky" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>
          <div class="ob-bubble"></div>
          <button type="button" class="ob-hero" aria-label="${esc(T('Karaktere dokun', 'Нажми на персонажа'))}"><img alt=""></button>
          <div class="ob-floor" aria-hidden="true"></div>
          <div class="ob-plate"><b></b><span></span></div>
        </section>
        <section class="ob-panel">
          <header class="ob-head"><span class="ob-brand">🐾 C++ Adventure</span><button type="button" class="ob-lang"></button>${profiles.length ? `<button type="button" class="ob-close" aria-label="${esc(T('Kapat', 'Закрыть'))}">✕</button>` : ''}</header>
          <h1 id="ob-title"></h1><p class="ob-lead"></p>
          <ol class="ob-steps"></ol>
          <div class="ob-body"></div>
          <p class="ob-error" role="alert"></p>
          <footer class="ob-actions"></footer>
        </section></div>`;
      $('.ob-hero', host).onclick = poke;
      $('.ob-stage', host).addEventListener('pointermove', tilt);
      $('.ob-stage', host).addEventListener('pointerleave', () => { $('.ob-hero', host).style.transform = ''; });
      $('.ob-lang', host).onclick = () => { try { changeLang(); } catch (_) {} };
      $('.ob-close', host)?.addEventListener('click', closeWizard);
    }
    $('.ob-lang', host).textContent = lg() === 'ru' ? '🇹🇷 Türkçe' : '🇷🇺 Русский';
    $('#ob-title', host).textContent = wiz.existing ? T('Profilini düzenle', 'Редактировать профиль') : first ? T('Maceraya hoş geldin!', 'Добро пожаловать в приключение!') : T('Yeni oyuncu', 'Новый игрок');
    $('.ob-lead', host).textContent = first ? T('C++ öğrenirken sana eşlik edecek karakteri seç. İstediğin zaman değiştirebilirsin.', 'Выбери персонажа, который будет с тобой, пока ты учишь C++. Его можно сменить в любой момент.') : T('Üç kısa adım: karakter, isim ve isteğe bağlı PIN.', 'Три коротких шага: персонаж, имя и PIN по желанию.');
    $('.ob-steps', host).innerHTML = steps.map((s, i) => `<li class="${i < wiz.step ? 'done' : i === wiz.step ? 'current' : ''}"><span>${i < wiz.step ? '✓' : i + 1}</span>${esc(s)}</li>`).join('');
    showHero(c);
    $('.ob-error', host).textContent = wiz.error || '';
    const body = $('.ob-body', host), actions = $('.ob-actions', host);
    if (wiz.step === 0) {
      body.innerHTML = `<div class="ob-grid" role="radiogroup" aria-label="${esc(T('Karakterler', 'Персонажи'))}">${CHARS.map((ch, i) => `<button type="button" role="radio" aria-checked="${i === wiz.index}" class="ob-card ${i === wiz.index ? 'selected' : ''}" data-idx="${i}" style="--c:${ch.color}"><img src="/assets/${ch.img}" alt="" draggable="false"><b>${esc(pick(ch.name))}</b></button>`).join('')}</div>
        <article class="ob-info"><h2>${esc(pick(c.name))}</h2><p>${esc(pick(c.role))}</p><ul class="ob-stats">${STAT_NAMES().map((n, i) => `<li><span>${esc(n)}</span><i><b style="--v:${c.stats[i] * 20}%"></b></i></li>`).join('')}</ul><small>${esc(T('← → ile karakterler arasında gezin, karaktere tıklayıp selam ver.', 'Листай персонажей стрелками ← →, нажми на персонажа, чтобы поздороваться.'))}</small></article>`;
      $$('.ob-card', body).forEach(btn => btn.onclick = () => choose(+btn.dataset.idx));
      actions.innerHTML = `<span></span><button type="button" class="primary ob-next">${esc(T('Bu karakterle devam et', 'Продолжить с этим персонажем'))} →</button>`;
    } else if (wiz.step === 1) {
      body.innerHTML = `<label class="ob-field"><span>${esc(T('Oyuncu adın', 'Имя игрока'))}</span><input id="ob-name" maxlength="24" autocomplete="off" spellcheck="false" placeholder="${esc(T('Örneğin Mira', 'Например, Мира'))}" value="${esc(wiz.name)}"></label><p class="ob-hint">${esc(T('2–24 karakter. Bu isim liderlik tablosunda ve kedi yoldaşının yanında görünür.', 'От 2 до 24 символов. Имя видно в таблице лидеров и рядом с котом-спутником.'))}</p>`;
      const input = $('#ob-name', body);
      input.oninput = () => { wiz.name = input.value; wiz.error = ''; $('.ob-error', host).textContent = ''; say(greeting()); plate(); };
      setTimeout(() => input.focus(), 60);
      actions.innerHTML = `<button type="button" class="secondary ob-back">← ${esc(T('Geri', 'Назад'))}</button><button type="button" class="primary ob-next">${esc(T('İleri', 'Далее'))} →</button>`;
    } else {
      const ex = wiz.existing;
      body.innerHTML = `${ex?.has_pin ? `<label class="ob-field"><span>${esc(T('Mevcut PIN', 'Текущий PIN'))}</span><input id="ob-current" type="password" inputmode="numeric" maxlength="8" autocomplete="off" value="${esc(wiz.currentPin)}"></label>` : ''}
        <label class="ob-field"><span>${esc(ex?.has_pin ? T('Yeni PIN (değiştirmek istemiyorsan boş bırak)', 'Новый PIN (оставь пустым, чтобы не менять)') : T('PIN (isteğe bağlı)', 'PIN (необязательно)'))}</span><input id="ob-pin" type="password" inputmode="numeric" maxlength="8" autocomplete="new-password" placeholder="••••" value="${esc(wiz.pin)}"></label>
        <div class="ob-pin-dots" aria-hidden="true">${Array.from({length: 8}, (_, i) => `<i class="${i < wiz.pin.length ? 'on' : ''}"></i>`).join('')}</div>
        <p class="ob-hint">${esc(T('4–8 rakam. Aynı bilgisayarı başkalarıyla paylaşıyorsan PIN, ilerlemeni korur. Boş bırakırsan profil PIN olmadan açılır.', 'От 4 до 8 цифр. Если компьютером пользуются другие, PIN защитит твой прогресс. Без PIN профиль открывается сразу.'))}</p>
        ${ex?.has_pin ? `<label class="ob-check"><input type="checkbox" id="ob-remove" ${wiz.removePin ? 'checked' : ''}> ${esc(T('PIN korumasını kaldır', 'Снять защиту PIN'))}</label>` : ''}
        <div class="ob-summary">${window.avatarHtml(c.id, 'ob-summary-img')}<div><b>${esc(wiz.name.trim())}</b><span>${esc(pick(c.name))} · ${esc(pick(c.role))}</span></div></div>`;
      const pin = $('#ob-pin', body);
      pin.oninput = () => { pin.value = pin.value.replace(/\D/g, ''); wiz.pin = pin.value; $$('.ob-pin-dots i', body).forEach((d, i) => d.classList.toggle('on', i < wiz.pin.length)); };
      $('#ob-current', body)?.addEventListener('input', e => { e.target.value = e.target.value.replace(/\D/g, ''); wiz.currentPin = e.target.value; });
      $('#ob-remove', body)?.addEventListener('change', e => { wiz.removePin = e.target.checked; });
      setTimeout(() => ($('#ob-current', body) || pin).focus(), 60);
      actions.innerHTML = `<button type="button" class="secondary ob-back">← ${esc(T('Geri', 'Назад'))}</button><button type="button" class="primary ob-next ob-finish">${esc(ex ? T('Kaydet', 'Сохранить') : T('Maceraya başla', 'Начать приключение'))} ✦</button>`;
    }
    $('.ob-next', actions).onclick = next;
    $('.ob-back', actions)?.addEventListener('click', () => { wiz.step -= 1; wiz.error = ''; paintWizard(); });
    plate();
    say(wiz.step === 1 && wiz.name.trim() ? greeting() : wiz.step === 2 ? T('Neredeyse hazırız!', 'Почти готово!') : pick(c.line));
  }

  const greeting = () => wiz.name.trim() ? T(`Merhaba ${wiz.name.trim()}! Birlikte harika kodlar yazacağız.`, `Привет, ${wiz.name.trim()}! Мы напишем отличный код вместе.`) : T('Adını söyler misin?', 'Как тебя зовут?');
  function plate() {
    const c = CHARS[wiz.index], host = $('#onboard-overlay');
    if (!host) return;
    $('.ob-plate b', host).textContent = wiz.name.trim() || T('Yeni oyuncu', 'Новый игрок');
    $('.ob-plate span', host).textContent = pick(c.name);
  }
  function say(text) {
    const bubble = $('#onboard-overlay .ob-bubble');
    if (!bubble || bubble.dataset.text === text) return;
    bubble.dataset.text = text;
    bubble.textContent = text;
    if (!reduce()) { bubble.classList.remove('ob-pop'); void bubble.offsetWidth; bubble.classList.add('ob-pop'); }
  }
  function showHero(c) {
    const hero = $('#onboard-overlay .ob-hero img');
    if (!hero || hero.dataset.id === c.id) return;
    const swap = () => { hero.src = `/assets/${c.img}`; hero.dataset.id = c.id; hero.parentElement.classList.remove('ob-out'); if (!reduce()) { hero.parentElement.classList.remove('ob-in'); void hero.offsetWidth; hero.parentElement.classList.add('ob-in'); sparkle(10); } };
    if (hero.dataset.id && !reduce()) { hero.parentElement.classList.add('ob-out'); setTimeout(swap, 160); } else swap();
  }
  function sparkle(count) {
    const stage = $('#onboard-overlay .ob-stage');
    if (!stage || reduce()) return;
    for (let i = 0; i < count; i++) {
      const s = document.createElement('i');
      s.className = 'ob-spark';
      const angle = Math.random() * Math.PI * 2, dist = 70 + Math.random() * 90;
      s.style.setProperty('--dx', `${Math.cos(angle) * dist}px`);
      s.style.setProperty('--dy', `${Math.sin(angle) * dist - 40}px`);
      s.textContent = ['✦', '✧', '⋆', '🐾'][i % 4];
      stage.append(s);
      setTimeout(() => s.remove(), 900);
    }
  }
  function poke() {
    const hero = $('#onboard-overlay .ob-hero');
    if (!hero) return;
    if (!reduce()) { hero.classList.remove('ob-jump'); void hero.offsetWidth; hero.classList.add('ob-jump'); sparkle(8); }
    const c = CHARS[wiz.index], lines = [pick(c.line), T('Mırr… başını okşadın!', 'Мрр… ты меня погладил!'), T('Hazırsan başlayalım!', 'Если готов — начинаем!')];
    wiz.poke = ((wiz.poke || 0) + 1) % lines.length;
    say(lines[wiz.poke]);
  }
  function tilt(event) {
    if (reduce()) return;
    const stage = event.currentTarget, hero = $('.ob-hero', stage), r = stage.getBoundingClientRect();
    const x = (event.clientX - r.left) / r.width - 0.5, y = (event.clientY - r.top) / r.height - 0.5;
    hero.style.transform = `perspective(700px) rotateY(${x * 14}deg) rotateX(${-y * 8}deg) translateX(${x * 14}px)`;
  }
  function choose(i) {
    wiz.index = (i + CHARS.length) % CHARS.length;
    paintWizard();
    $(`#onboard-overlay .ob-card[data-idx="${wiz.index}"]`)?.focus();
  }
  function keys(event) {
    if (!wiz) return;
    if (event.key === 'Escape') { event.stopPropagation(); if (profiles.length) closeWizard(); return; }
    if (event.key === 'Tab') {
      const host = $('#onboard-overlay');
      const list = host ? [...host.querySelectorAll('button:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex="-1"])')] : [];
      if (list.length) {
        const first = list[0], last = list[list.length - 1];
        if (!host.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
        else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
      return;
    }
    if (wiz.step === 0 && (event.key === 'ArrowRight' || event.key === 'ArrowLeft')) { event.preventDefault(); choose(wiz.index + (event.key === 'ArrowRight' ? 1 : -1)); }
    if (event.key === 'Enter' && !event.target.closest?.('button')) { event.preventDefault(); next(); }
  }

  async function next() {
    wiz.error = '';
    if (wiz.step === 0) { wiz.step = 1; paintWizard(); return; }
    if (wiz.step === 1) {
      const name = wiz.name.trim();
      if (name.length < 2) { wiz.error = T('İsim en az 2 karakter olmalı.', 'Имя должно содержать не менее 2 символов.'); paintWizard(); return; }
      if (!wiz.existing && profiles.some(p => p.name.toLocaleLowerCase() === name.toLocaleLowerCase())) { wiz.error = T('Bu isimde bir profil zaten var.', 'Профиль с таким именем уже есть.'); paintWizard(); return; }
      wiz.step = 2; paintWizard(); return;
    }
    if (wiz.pin && !/^\d{4,8}$/.test(wiz.pin)) { wiz.error = T('PIN 4–8 rakam olmalı.', 'PIN должен содержать 4–8 цифр.'); paintWizard(); return; }
    const button = $('#onboard-overlay .ob-finish');
    if (button) button.disabled = true;
    const c = CHARS[wiz.index];
    try {
      if (wiz.existing) {
        const body = {profile_id: wiz.existing.id, name: wiz.name.trim(), avatar: c.id, pin: wiz.removePin ? 'REMOVE' : wiz.pin, current_pin: wiz.currentPin};
        const res = await post('/api/profile/update', body);
        if (res.error) { wiz.error = res.error; paintWizard(); return; }
        const editedId = wiz.existing.id;
        closeWizard();
        toast(T('Profil kaydedildi.', 'Профиль сохранён.'), true);
        if (editedId === profileId && appState) { appState = await api('/api/state?profile_id=' + encodeURIComponent(profileId)); renderSidebar(); }
        renderProfiles();
        return;
      }
      const res = await post('/api/profiles', {name: wiz.name.trim(), avatar: c.id, pin: wiz.pin, lang: lg()});
      if (res.error) { wiz.error = res.error; paintWizard(); return; }
      const sel = await post('/api/select', {profile_id: res.profile_id, pin: wiz.pin});
      if (sel.error) { wiz.error = sel.error; paintWizard(); return; }
      sparkle(18);
      say(T(`Hoş geldin ${wiz.name.trim()}! Macera başlıyor…`, `Добро пожаловать, ${wiz.name.trim()}! Приключение начинается…`));
      await new Promise(r => setTimeout(r, reduce() ? 0 : 650));
      await enter(res.profile_id);
      closeWizard();
    } finally { if (button?.isConnected) button.disabled = false; }
  }

  const post = (url, body) => fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}).then(r => r.json()).catch(() => ({error: T('Bağlantı hatası.', 'Ошибка соединения.')}));

  async function enter(id) {
    profileId = id;
    localStorage.setItem('cpp-adventure-profile', id);
    await loadProfiles();
    appState = await api('/api/state?profile_id=' + encodeURIComponent(id));
    lang = appState.profile.lang || lang;
    setLangButton();
    document.body.classList.remove('no-profile');
    renderSidebar(); renderHome(); setView('home');
    document.dispatchEvent(new Event('cpp-adventure-language-changed'));
  }

  /* ——— "Kim oynuyor?" ekranı ——— */
  async function renderProfilesScreen() {
    showingProfiles = true;
    const view = $('#view-home');
    $$('.view').forEach(v => v.classList.add('hidden'));
    view.classList.remove('hidden');
    $('#crumb-current').textContent = T('Profiller', 'Профили');
    await loadProfiles();
    document.body.classList.toggle('no-profile', !profileId || !profiles.some(p => p.id === profileId));
    if (!profiles.length) { view.innerHTML = ''; if (!wiz) openWizard(); return; }
    const board = await fetch('/api/leaderboard').then(r => r.json()).catch(() => ({leaderboard: []}));
    const list = board.leaderboard || [];
    view.innerHTML = `<section class="who-head"><span class="eyebrow">🐾 C++ Adventure</span><h1>${esc(T('Kim oynuyor?', 'Кто играет?'))}</h1><p>${esc(T('Profilini seç ya da yeni bir oyuncu oluştur.', 'Выбери свой профиль или создай нового игрока.'))}</p></section>
      <div class="who-grid">${profiles.map(p => {
        const c = charOf(p.avatar);
        return `<article class="who-card ${p.id === profileId ? 'is-current' : ''}" style="--c:${c?.color || '#a885ff'}">
          <button type="button" class="who-open" data-pid="${esc(p.id)}" aria-label="${esc(T('Bu profille devam et', 'Продолжить с этим профилем'))}: ${esc(p.name)}">
            <span class="who-art">${window.avatarHtml(p.avatar, 'who-img')}</span>
            <b>${esc(p.name)}</b><small>${p.xp} XP${p.has_pin ? ' · 🔒 PIN' : ''}</small>
            <span class="who-go">${esc(p.id === profileId ? T('Devam et', 'Продолжить') : T('Oyna', 'Играть'))} →</span></button>
          <div class="who-tools"><button type="button" class="who-edit" data-pid="${esc(p.id)}" title="${esc(T('Düzenle', 'Изменить'))}" aria-label="${esc(T('Düzenle', 'Изменить'))}">✎</button><button type="button" class="who-delete" data-pid="${esc(p.id)}" title="${esc(T('Sil', 'Удалить'))}" aria-label="${esc(T('Sil', 'Удалить'))}">🗑</button></div>
        </article>`;
      }).join('')}
      <button type="button" class="who-card who-new" id="create-profile"><span class="who-plus">＋</span><b>${esc(T('Yeni oyuncu', 'Новый игрок'))}</b><small>${esc(T('Karakterini seç', 'Выбери персонажа'))}</small></button></div>
      <section class="panel who-board"><h3>🏆 ${esc(T('Yerel liderlik tablosu', 'Локальная таблица лидеров'))}</h3>${list.length > 1 ? `<ol>${list.map((u, i) => `<li class="${u.id === profileId ? 'me' : ''}"><span class="who-rank">${['🥇', '🥈', '🥉'][i] || i + 1}</span>${window.avatarHtml(u.avatar, 'avatar-inline')}<b>${esc(u.name)}</b><span class="quest-xp">${u.xp} XP</span></li>`).join('')}</ol>` : `<p class="view-lead">${esc(T('Bu bilgisayarda başka oyuncu yok. Birlikte öğrendiğin biri varsa onun için de profil açın ve XP yarışı başlasın!', 'На этом компьютере других игроков нет. Создайте профиль для друга — и начнётся гонка за XP!'))}</p>`}</section>`;
    $$('.who-open', view).forEach(b => b.onclick = () => selectProfile(b.dataset.pid));
    $$('.who-edit', view).forEach(b => b.onclick = () => openWizard(profiles.find(p => p.id === b.dataset.pid)));
    $$('.who-delete', view).forEach(b => b.onclick = () => confirmDelete(profiles.find(p => p.id === b.dataset.pid)));
    $('#create-profile', view).onclick = () => openWizard();
  }

  function confirmDelete(p) {
    if (!p) return;
    const host = overlay();
    document.body.classList.add('onboard-open');
    host.innerHTML = `<div class="ob-confirm" role="alertdialog" aria-modal="true" aria-labelledby="ob-del-title">${window.avatarHtml(p.avatar, 'ob-del-img')}<h2 id="ob-del-title">${esc(T(`${p.name} silinsin mi?`, `Удалить профиль ${p.name}?`))}</h2><p>${esc(T('Tüm ilerleme, XP, kedi eşyaları ve kodlar kalıcı olarak silinir. Bu işlem geri alınamaz.', 'Весь прогресс, XP, вещи кота и код будут удалены навсегда. Это действие нельзя отменить.'))}</p>${p.has_pin ? `<label class="ob-field"><span>PIN</span><input id="ob-del-pin" type="password" inputmode="numeric" maxlength="8"></label>` : ''}<p class="ob-error" role="alert"></p><footer class="ob-actions"><button type="button" class="secondary" id="ob-del-cancel">${esc(T('Vazgeç', 'Отмена'))}</button><button type="button" class="primary danger" id="ob-del-ok">${esc(T('Kalıcı olarak sil', 'Удалить навсегда'))}</button></footer></div>`;
    $('#ob-del-cancel', host).onclick = closeWizard;
    host.onkeydown = e => { if (e.key === 'Escape') closeWizard(); };
    setTimeout(() => ($('#ob-del-pin', host) || $('#ob-del-cancel', host)).focus(), 40);
    $('#ob-del-ok', host).onclick = async () => {
      const res = await post('/api/profile/delete', {profile_id: p.id, pin: $('#ob-del-pin', host)?.value || ''});
      if (res.error) { $('.ob-error', host).textContent = res.error; return; }
      closeWizard();
      if (p.id === profileId) { profileId = ''; appState = null; localStorage.removeItem('cpp-adventure-profile'); }
      toast(T('Profil silindi.', 'Профиль удалён.'), true);
      renderProfilesScreen();
    };
  }

  /* ——— Kenar çubuğu ve üst çubuk: isim + karakter ——— */
  function decorateChrome() {
    const p = appState?.profile;
    const card = $('.sidebar .profile-card');
    if (card && p) {
      const avatar = $('.avatar', card);
      if (avatar && avatar.dataset.av !== p.avatar) { avatar.innerHTML = window.avatarHtml(p.avatar, 'avatar-fill'); avatar.dataset.av = p.avatar; }
      const rank = $('#rank');
      let name = $('.side-name', card);
      if (!name) { name = document.createElement('b'); name.className = 'side-name'; $('.profile-copy', card).prepend(name); }
      name.textContent = p.name;
      rank?.classList.add('side-rank');
      card.title = T('Profilleri aç', 'Открыть профили');
      card.onclick = () => renderProfiles();
    }
    const top = $('#top-profile');
    if (top && p && top.dataset.av !== p.avatar) { top.innerHTML = window.avatarHtml(p.avatar, 'avatar-fill'); top.dataset.av = p.avatar; }
  }

  // The onboarding module *provides* the profile screen and wizard (full replacements of the
  // simple app.js versions) and extends the sidebar. Done at load time so boot() already sees them.
  window.renderProfiles = renderProfilesScreen;
  window.profileForm = existing => openWizard(existing);
  App.after('renderSidebar', () => decorateChrome());

  document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('cpp-adventure-language-changed', () => { if (wiz && $('#onboard-overlay .ob-shell')) paintWizard(true); });
  });
})();
