(() => {
  const copy = {get tr(){return window.CppAdventureI18n.module('pin','tr')},get ru(){return window.CppAdventureI18n.module('pin','ru')}};
  const cat = `<svg class="pin-cat is-hidden" viewBox="0 0 200 170" aria-hidden="true">
    <path class="cat-body" d="M45 149c2-30 23-49 55-49s53 19 55 49v21H45z"/>
    <path class="cat-ear" d="M49 58 43 13l43 28m28 0 43-28-6 45"/>
    <path class="cat-head" d="M47 63c0-34 21-54 53-54s53 20 53 54c0 35-22 55-53 55S47 98 47 63Z"/>
    <path class="cat-ear-inner" d="m56 43-3-18 20 13m54 0 20-13-3 18"/>
    <g class="cat-glasses"><circle cx="76" cy="66" r="14"/><circle cx="124" cy="66" r="14"/><path d="M90 66h20m-42-1-9-4m75 4 9-4"/></g>
    <g class="cat-eye-open"><ellipse cx="76" cy="66" rx="5" ry="8" fill="#482c45"/><ellipse cx="124" cy="66" rx="5" ry="8" fill="#482c45"/><circle cx="77" cy="63" r="2" fill="#fff"/><circle cx="125" cy="63" r="2" fill="#fff"/></g>
    <path class="cat-eye-closed" d="M66 67q10 9 20 0m28 0q10 9 20 0"/>
    <path class="cat-nose" d="m95 79 5 4 5-4q-5-6-10 0Z"/><path class="cat-mouth" d="M100 83v6m0 0q-8 8-16 0m16 0q8 8 16 0"/>
    <path class="cat-whiskers" d="m70 81-28-5m29 12-27 3m84-10 28-5m-29 12 27 3"/>
    <ellipse class="cat-paw cat-paw-left" cx="78" cy="76" rx="18" ry="14"/><ellipse class="cat-paw cat-paw-right" cx="122" cy="76" rx="18" ry="14"/>
    <path class="cat-sparkle" d="m38 35 3 8 8 3-8 3-3 8-3-8-8-3 8-3zm128 17 2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/>
  </svg>`;
  const post = async (url, body) => {
    try {
      const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const result = await response.json();
      return { ok: response.ok && !result.error, error: result.error };
    } catch { return { ok: false, offline: true }; }
  };

  function open({ language = 'tr', verify }) {
    const lang = language === 'ru' ? 'ru' : 'tr', t = copy[lang];
    const previous = document.activeElement;
    document.querySelector('#pin-backdrop')?.remove();
    const layer = document.createElement('div');
    layer.className = 'modal-backdrop pin-backdrop';
    layer.id = 'pin-backdrop';
    layer.innerHTML = `<section class="pin-dialog" role="dialog" aria-modal="true" aria-labelledby="pin-title" aria-describedby="pin-description">
      <button class="modal-close" type="button" data-pin-close aria-label="${t.close}">×</button>
      <div class="pin-cat-wrap">${cat}</div>
      <h2 id="pin-title">${t.title}</h2><p id="pin-description">${t.description}</p>
      <form class="pin-form" novalidate>
        <label class="pin-label" for="pin-entry">${t.label}</label>
        <div class="pin-input-row"><input id="pin-entry" class="pin-input" type="password" inputmode="numeric" autocomplete="current-password" maxlength="8" pattern="[0-9]{4,8}" required aria-describedby="pin-message"><button class="pin-eye" type="button" aria-label="${t.show}" aria-pressed="false" title="${t.show}">◉</button></div>
        <p class="pin-message" id="pin-message" role="status" aria-live="polite"></p>
        <div class="pin-actions"><button class="secondary" type="button" data-pin-cancel>${t.cancel}</button><button class="primary" type="submit">${t.submit}</button></div>
      </form>
    </section>`;
    document.body.append(layer);
    const dialog = layer.querySelector('.pin-dialog'), input = layer.querySelector('#pin-entry'), eye = layer.querySelector('.pin-eye'), message = layer.querySelector('.pin-message'), submit = layer.querySelector('[type="submit"]'), mascot = layer.querySelector('.pin-cat');
    let finished = false, busy = false;
    const visibilityState = () => input.type === 'text' ? 'is-visible' : 'is-hidden';
    const setState = state => { mascot.classList.remove('is-hidden', 'is-visible', 'is-wrong', 'is-success'); mascot.classList.add(state); };
    let resolvePromise;
    const close = value => {
      if (finished) return;
      finished = true;
      document.removeEventListener('keydown', onKeyDown, true);
      layer.remove();
      if (previous && typeof previous.focus === 'function') previous.focus();
      resolvePromise(value);
    };
    const wrong = (offline = false) => {
      dialog.classList.remove('is-shaking'); mascot.classList.remove('is-wrong');
      void dialog.offsetWidth;
      dialog.classList.add('is-shaking'); mascot.classList.add('is-wrong');
      message.textContent = offline ? t.service : t.wrong;
      message.classList.remove('is-good');
      input.value = '';
      window.setTimeout(() => { if (!finished) { dialog.classList.remove('is-shaking'); setState(visibilityState()); input.focus(); } }, 650);
    };
    const onKeyDown = event => {
      if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close(false); return; }
      if (event.key !== 'Tab') return;
      const focusable = [...dialog.querySelectorAll('button:not(:disabled),input:not(:disabled)')].filter(el => !el.hidden);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    eye.addEventListener('click', () => {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      eye.setAttribute('aria-pressed', String(show));
      eye.setAttribute('aria-label', show ? t.hide : t.show);
      eye.title = show ? t.hide : t.show;
      setState(visibilityState());
      input.focus();
    });
    layer.querySelectorAll('[data-pin-close],[data-pin-cancel]').forEach(button => button.addEventListener('click', () => close(false)));
    layer.addEventListener('click', event => { if (event.target === layer) close(false); });
    layer.querySelector('.pin-form').addEventListener('submit', async event => {
      event.preventDefault();
      if (busy) return;
      if (!/^\d{4,8}$/.test(input.value)) { wrong(); return; }
      busy = true; input.disabled = true; eye.disabled = true; submit.disabled = true;
      message.textContent = ''; message.classList.remove('is-good');
      const result = await verify(input.value);
      if (result?.ok) {
        mascot.classList.remove('is-hidden', 'is-visible', 'is-wrong'); mascot.classList.add('is-success');
        dialog.classList.add('is-successful'); message.textContent = t.success; message.classList.add('is-good');
        window.setTimeout(() => close(true), 430);
      } else {
        input.disabled = false; eye.disabled = false; submit.disabled = false; busy = false;
        wrong(!!result?.offline);
      }
    });
    document.addEventListener('keydown', onKeyDown, true);
    window.setTimeout(() => input.focus(), 30);
    return new Promise(resolve => { resolvePromise = resolve; });
  }
  window.CatPinDialog = { open, post };
})();
