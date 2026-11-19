(() => {
  const words = {get tr(){return window.CppAdventureI18n.module('splash','tr')},get ru(){return window.CppAdventureI18n.module('splash','ru')}};
  const $ = (selector) => document.querySelector(selector);
  const MIN_VISIBLE_MS = 3500;
  const shownAt = Date.now();
  let language = localStorage.getItem('cpp-adventure-language') === 'ru' ? 'ru' : 'tr';
  const status = $('#splash-status'), percent = $('#splash-percent'), bar = $('#splash-progress-bar');
  const track = $('.splash-progress'), retry = $('#splash-retry'), root = $('#startup-splash');
  function setLanguage(value) {
    language = value === 'ru' ? 'ru' : 'tr';
    document.documentElement.lang = language;
    root?.setAttribute?.('aria-label', words[language].screenLabel);
    track?.setAttribute?.('aria-label', words[language].progressLabel);
    if (retry) retry.textContent = words[language].retry;
  }
  function progress(value, key) {
    const amount = Math.max(0, Math.min(100, Math.round(value)));
    if (bar) bar.classList.remove('splash-progress-failed');
    if (retry) retry.hidden = true;
    if (percent) percent.textContent = `${amount}%`;
    if (bar) bar.style.width = `${amount}%`;
    if (track) track.setAttribute('aria-valuenow', String(amount));
    if (status && words[language][key]) status.textContent = words[language][key];
  }
  function hide() {
    progress(100, 'ready');
    const remaining = Math.max(0, MIN_VISIBLE_MS - (Date.now() - shownAt));
    window.setTimeout(() => {
      root?.classList.add('is-leaving');
      window.setTimeout(() => root?.remove(), 380);
    }, remaining);
  }
  function fail() {
    if (status) status.textContent = words[language].failed;
    if (bar) bar.classList.add('splash-progress-failed');
    if (retry) retry.hidden = false;
  }
  setLanguage(language);
  progress(0, 'startup');
  window.CppSplash = { progress, hide, fail, setLanguage, MIN_VISIBLE_MS, onRetry(callback) { if (retry) retry.onclick = callback; } };
})();

