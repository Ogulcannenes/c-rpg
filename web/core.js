// core.js — shared frontend infrastructure. Loaded before every other app script.
//
// Extension points: feature modules used to capture an app.js function and reassign the
// global (window.renderSidebar = function () { core(); extra(); }). That broke silently when
// script order changed, let one module's exception break the whole chain, and raced with boot().
// Now app.js installs each extension point exactly once (App.install) and modules only register:
//
//   App.before('renderWorkshop', () => dispose());
//   App.after('renderSidebar', () => decorate());
//   App.after('api', ([url, body], result) => observe(url, body, result));
//
// After-hooks receive (args, result). For async functions they run after the promise resolves
// and are awaited in registration order. A failing hook is logged and never breaks the call.
(() => {
  const beforeHooks = new Map();
  const afterHooks = new Map();
  const listFor = (map, name) => {
    if (!map.has(name)) map.set(name, []);
    return map.get(name);
  };

  function runSync(hooks, args, result) {
    for (const hook of hooks) {
      try {
        const value = hook(args, result);
        if (value && typeof value.then === 'function') value.catch(error => console.error(error));
      } catch (error) {
        console.error(error);
      }
    }
  }

  async function runAsync(hooks, args, result) {
    for (const hook of hooks) {
      try { await hook(args, result); } catch (error) { console.error(error); }
    }
  }

  function install(names) {
    for (const name of names) {
      const core = window[name];
      if (typeof core !== 'function' || core.__appHooked) continue;
      const hooked = function (...args) {
        runSync(beforeHooks.get(name) || [], args);
        const out = core.apply(this, args);
        if (out && typeof out.then === 'function') {
          return out.then(async value => { await runAsync(afterHooks.get(name) || [], args, value); return value; });
        }
        runSync(afterHooks.get(name) || [], args, out);
        return out;
      };
      hooked.__appHooked = true;
      hooked.__core = core;
      window[name] = hooked;
    }
  }

  const ESCAPES = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'};

  const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]):not([type="hidden"]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

  // Keep Tab inside a modal, close it on Escape and give focus back to the opener.
  // Returns a release function; call it when the dialog closes by other means.
  function trapFocus(container, { onEscape } = {}) {
    const opener = document.activeElement;
    const items = () => [...container.querySelectorAll(FOCUSABLE)].filter(el => el.offsetParent !== null || el === document.activeElement);
    function onKey(event) {
      if (!container.isConnected) return release();
      if (event.key === 'Escape' && onEscape) { event.preventDefault(); event.stopPropagation(); onEscape(); return; }
      if (event.key !== 'Tab') return;
      const list = items();
      if (!list.length) { event.preventDefault(); return; }
      const first = list[0], last = list[list.length - 1];
      if (!container.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
      else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    let released = false;
    function release() {
      if (released) return;
      released = true;
      document.removeEventListener('keydown', onKey, true);
      if (opener && opener.isConnected && typeof opener.focus === 'function') opener.focus();
    }
    document.addEventListener('keydown', onKey, true);
    setTimeout(() => { if (!released && !container.contains(document.activeElement)) items()[0]?.focus(); }, 30);
    return release;
  }

  window.App = Object.freeze({
    trapFocus,
    before: (name, hook) => { listFor(beforeHooks, name).push(hook); },
    after: (name, hook) => { listFor(afterHooks, name).push(hook); },
    install,
    // Escape untrusted text for HTML element content *and* attribute values.
    esc: value => String(value ?? '').replace(/[&<>"']/g, c => ESCAPES[c]),
  });
})();
