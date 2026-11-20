// admin-panel.js — deneme yapmak için test paneli.
// Üst çubuktaki anahtar düğmesi veya Ctrl+Shift+A ile açılır. Yalnızca etkin profili değiştirir.
// Sunucuda CPP_ADVENTURE_ADMIN=0 ortam değişkeniyle tamamen kapatılabilir.
(() => {
  const A = (key, vars) => (window.L ? window.L(`admin.${key}`, vars) : key);
  const $ = (s, r = document) => r.querySelector(s);
  let panel = null, enabled = false;

  const STAGES = [[1, 'stageKitten'], [2, 'stageGrowing'], [6, 'stageYoung'], [11, 'stageAdult'], [16, 'stageVeteran'], [21, 'stageLegend']];

  async function call(action, value) {
    const pid = typeof profileId !== 'undefined' ? profileId : '';
    if (!pid) { window.toast?.(A('needProfile')); return null; }
    const res = await fetch('/api/admin', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({profile_id: pid, action, value})});
    const data = await res.json().catch(() => ({error: A('failed')}));
    if (data.error) { window.toast?.(data.error); return null; }
    await window.refresh?.();
    rerenderVisible();
    render();
    window.toast?.(A('done'), true);
    return data;
  }

  // Görünen sayfa yeni verilerle yeniden çizilir (ders ekranı refresh ile güncellenir).
  function rerenderVisible() {
    const view = document.querySelector('.view:not(.hidden)')?.id?.replace('view-', '');
    if (!view || view === 'lesson') { if (view === 'lesson') window.renderLesson?.(); return; }
    if (view === 'shop') return window.renderShop?.();
    document.querySelector(`.nav-item[data-view="${view}"]`)?.click();
  }

  function num(id) { return Number($(`#${id}`, panel)?.value); }

  function render() {
    if (!panel) return;
    const p = window.appState?.profile;
    const chapters = window.appState?.curriculum || [];
    const lg = typeof lang !== 'undefined' ? lang : 'tr', tx = obj => obj?.[lg] || obj?.tr || '';
    panel.querySelector('.adm-body').innerHTML = !p ? `<p class="adm-note">${A('needProfile')}</p>` : `
      <section class="adm-stats" aria-label="${A('current')}">
        <div><span>${A('xp')}</span><b>${p.xp}</b></div>
        <div><span>${A('level')}</span><b>${p.level}</b></div>
        <div><span>${A('streak')}</span><b>${p.streak || 0}</b></div>
        <div><span>${A('items')}</span><b>${(p.owned_items || []).length}</b></div>
      </section>

      <section class="adm-group"><h3>${A('xpTitle')}</h3>
        <div class="adm-chips">${[100, 500, 1000, 5000].map(n => `<button data-adm="add_xp" data-val="${n}">+${n}</button>`).join('')}<button data-adm="add_xp" data-val="-500">−500</button></div>
        <div class="adm-row"><label for="adm-xp">${A('setXp')}</label><input id="adm-xp" type="number" min="0" max="10000000" value="${p.xp}"><button data-adm="set_xp" data-from="adm-xp">${A('apply')}</button></div>
      </section>

      <section class="adm-group"><h3>${A('levelTitle')}</h3>
        <p class="adm-note">${A('levelNote')}</p>
        <div class="adm-chips">${STAGES.map(([lv, key]) => `<button data-adm="set_level" data-val="${lv}" class="${p.level === lv ? 'on' : ''}">${lv} · ${A(key)}</button>`).join('')}</div>
        <div class="adm-row"><label for="adm-level">${A('setLevel')}</label><input id="adm-level" type="number" min="1" max="60" value="${p.level}"><button data-adm="set_level" data-from="adm-level">${A('apply')}</button></div>
        <div class="adm-row"><label for="adm-streak">${A('setStreak')}</label><input id="adm-streak" type="number" min="0" max="3650" value="${p.streak || 0}"><button data-adm="set_streak" data-from="adm-streak">${A('apply')}</button></div>
      </section>

      <section class="adm-group"><h3>${A('itemsTitle')}</h3>
        <div class="adm-chips"><button data-adm="grant_items">${A('grantItems')}</button><button data-adm="clear_items" class="warn">${A('clearItems')}</button></div>
      </section>

      <section class="adm-group"><h3>${A('progressTitle')}</h3>
        <div class="adm-row"><label for="adm-chapter">${A('chapter')}</label><select id="adm-chapter">${chapters.map((c, i) => `<option value="${i}">${String(i + 1).padStart(2, '0')} · ${tx(c.title).replace(/[<>&"]/g, '')}</option>`).join('')}</select><button data-adm="complete_chapter" data-from="adm-chapter">${A('completeChapter')}</button></div>
        <div class="adm-chips"><button data-adm="complete_all">${A('completeAll')}</button><button data-adm="grant_badges">${A('grantBadges')}</button></div>
        <div class="adm-chips"><button data-adm="reset_progress" class="danger" data-confirm="1">${A('resetProgress')}</button></div>
      </section>

      <section class="adm-group"><h3>${A('fxTitle')}</h3>
        <div class="adm-chips">
          <button data-fx="confetti">${A('fxConfetti')}</button>
          <button data-fx="happy">${A('fxHappy')}</button>
          <button data-fx="oops">${A('fxOops')}</button>
          <button data-fx="sleep">${A('fxSleep')}</button>
          <button data-fx="levelup">${A('fxLevelUp')}</button>
          <button data-fx="badge">${A('fxBadge')}</button>
          <button data-fx="walk">${A('fxWalk')}</button>
        </div>
      </section>
      <p class="adm-note">${A('footer')}</p>`;
  }

  function fx(kind) {
    const r = panel.getBoundingClientRect();
    if (kind === 'confetti') return window.PawConfetti?.(innerWidth / 2, innerHeight / 2, 40);
    if (kind === 'levelup') return document.dispatchEvent(new CustomEvent('cpp-adventure-level-up', {detail: {profileId: typeof profileId !== 'undefined' ? profileId : '', level: window.appState?.profile?.level || 1}}));
    if (kind === 'badge') return window.BadgePop?.((window.appState?.profile?.achievements || [])[0] || 'first_steps');
    if (kind === 'walk') { window.resetMapWalk?.(); window.toast?.(A('walkNote')); return; }
    if (kind === 'sleep') { document.body.dataset.catMood = 'sleep'; return; }
    window.CatMood?.set(kind, 2600);
    void r;
  }

  function onClick(e) {
    const btn = e.target.closest('button');
    if (!btn || !panel.contains(btn)) return;
    if (btn.classList.contains('adm-close')) return toggle(false);
    if (btn.dataset.fx) return fx(btn.dataset.fx);
    const action = btn.dataset.adm;
    if (!action) return;
    // Geri alınamayan işlem iki tıklama ister (tarayıcı onay penceresi açılmaz).
    if (btn.dataset.confirm && !btn.classList.contains('armed')) {
      btn.classList.add('armed');
      btn.dataset.label = btn.textContent;
      btn.textContent = A('confirmAgain');
      setTimeout(() => { if (btn.isConnected) { btn.classList.remove('armed'); btn.textContent = btn.dataset.label; } }, 3500);
      return;
    }
    const value = btn.dataset.from ? num(btn.dataset.from) : btn.dataset.val !== undefined ? Number(btn.dataset.val) : null;
    btn.disabled = true;
    call(action, value).finally(() => { if (btn.isConnected) btn.disabled = false; });
  }

  function build() {
    panel = document.createElement('aside');
    panel.className = 'admin-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', A('title'));
    panel.innerHTML = `<header><div><b>${A('title')}</b><small>${A('subtitle')}</small></div><button class="adm-close" aria-label="${A('close')}">×</button></header><div class="adm-body"></div>`;
    panel.addEventListener('click', onClick);
    panel.addEventListener('keydown', e => { if (e.key === 'Escape') toggle(false); });
    document.body.append(panel);
  }

  function toggle(force) {
    if (!enabled) return;
    if (!panel) build();
    const open = force ?? !panel.classList.contains('open');
    panel.classList.toggle('open', open);
    document.querySelector('#admin-open')?.setAttribute('aria-expanded', String(open));
    if (open) { render(); setTimeout(() => panel.querySelector('.adm-close')?.focus(), 50); }
  }
  window.AdminPanel = {toggle};

  document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) { e.preventDefault(); toggle(); }
  });
  document.addEventListener('cpp-adventure-language-changed', () => {
    if (!panel) return;
    const wasOpen = panel.classList.contains('open');
    panel.remove(); panel = null;
    const btn = document.querySelector('#admin-open');
    if (btn) btn.title = A('title');
    if (wasOpen) toggle(true);
  });

  document.addEventListener('DOMContentLoaded', async () => {
    try { enabled = !!(await (await fetch('/api/meta')).json()).admin; } catch (_) { enabled = false; }
    if (!enabled) return;
    const btn = document.createElement('button');
    btn.className = 'icon-button';
    btn.id = 'admin-open';
    btn.title = A('title');
    btn.setAttribute('aria-label', A('title'));
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.5 6.5a4 4 0 0 0-5 5L4 17l3 3 5.5-5.5a4 4 0 0 0 5-5l-2.5 2.5-2.5-.5-.5-2.5z"/></svg>';
    btn.onclick = () => toggle();
    document.querySelector('#settings-open')?.before(btn);
  });
})();
