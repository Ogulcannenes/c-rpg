// ux-a11y.js — fixes from the UI/UX/accessibility audit (docs/UX_AUDIT.md) that hook into
// app.js extension points instead of reassigning globals.
//
// - After every view change: focus the view's h1 (WCAG 2.4.3), update document.title, scroll to top.
// - Text size: an app-wide scale (Settings + Ctrl/⌘ + Plus/Minus/0). The packaged WebView2 window
//   disables the browser zoom shortcuts, so keyboard users had no way to enlarge text (WCAG 1.4.4).
// - Reduce motion: an in-app switch with the same effect as the OS preference.
(() => {
  const SCALE_KEY = 'cpp-adventure-ui-scale';
  const MOTION_KEY = 'cpp-adventure-reduce-motion';
  const SCALES = [1, 1.15, 1.3, 1.5];

  const read = (key, fallback) => { try { return localStorage.getItem(key) ?? fallback; } catch { return fallback; } };
  const write = (key, value) => { try { localStorage.setItem(key, String(value)); } catch { /* private mode */ } };

  function scale() {
    const value = parseFloat(read(SCALE_KEY, '1'));
    return SCALES.includes(value) ? value : 1;
  }
  function setScale(value) {
    const next = SCALES.includes(value) ? value : 1;
    write(SCALE_KEY, next);
    document.documentElement.style.zoom = next === 1 ? '' : String(next);
    return next;
  }
  function reducedMotion() { return read(MOTION_KEY, '0') === '1'; }
  function setReducedMotion(on) {
    write(MOTION_KEY, on ? '1' : '0');
    document.body?.classList.toggle('reduce-motion', !!on);
  }

  function step(direction) {
    const index = SCALES.indexOf(scale());
    return setScale(direction === 0 ? 1 : SCALES[Math.max(0, Math.min(SCALES.length - 1, index + direction))]);
  }

  document.addEventListener('keydown', event => {
    if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
    const key = event.key;
    const direction = key === '+' || key === '=' ? 1 : key === '-' || key === '_' ? -1 : key === '0' ? 0 : null;
    if (direction === null) return;
    event.preventDefault();
    step(direction);
  });

  App.after('setView', ([view]) => {
    const host = document.getElementById('view-' + view);
    if (!host) return;
    window.scrollTo(0, 0);
    // Several views render right after setView (journal, labs, ...): wait for the content.
    setTimeout(() => {
      const crumb = document.getElementById('crumb-current')?.textContent?.trim();
      document.title = crumb ? `${crumb} · C++ Adventure` : 'C++ Adventure';
      if (view === 'lesson') return; // renderLesson moves focus to #task-title itself
      const active = document.activeElement;
      if (active && host.contains(active)) return; // never steal focus from something inside the view
      const heading = host.querySelector('h1');
      if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
    }, 80);
  });

  setScale(scale());
  const applyMotion = () => setReducedMotion(reducedMotion());
  if (document.body) applyMotion(); else document.addEventListener('DOMContentLoaded', applyMotion);

  window.UxPrefs = Object.freeze({ scale, setScale, reducedMotion, setReducedMotion, step, SCALES });
})();
