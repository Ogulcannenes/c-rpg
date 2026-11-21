// Monaco editor bootstrap (moved out of index.html so the CSP can forbid inline scripts).
// window.MonacoReady always settles. It resolves with monaco, or — if the vendored editor cannot
// load — with a small <textarea>-based stand-in that implements the subset of the Monaco API this
// app uses, so every code task, the workshop, arena and interviews stay usable offline.
window.MonacoLoadError = null;

function createMonacoFallback() {
  const KeyMod = { CtrlCmd: 2048, Shift: 1024, Alt: 512 };
  const KeyCode = { KeyS: 49, Enter: 3 };
  const keyName = { 49: 's', 3: 'Enter' };
  class Range {
    constructor(startLineNumber, startColumn, endLineNumber, endColumn) {
      Object.assign(this, { startLineNumber, startColumn, endLineNumber, endColumn });
    }
  }
  const disposable = () => ({ dispose() {} });
  function create(host, options = {}) {
    const area = document.createElement('textarea');
    area.className = 'code-fallback';
    area.spellcheck = false;
    area.setAttribute('autocapitalize', 'off');
    area.setAttribute('autocomplete', 'off');
    area.setAttribute('aria-label', document.documentElement.lang === 'ru' ? 'Редактор кода C++' : 'C++ kod düzenleyicisi');
    area.value = options.value || '';
    area.readOnly = !!options.readOnly;
    host.replaceChildren(area);
    const listeners = new Set();
    const commands = [];
    const changed = () => listeners.forEach(fn => fn({}));
    area.addEventListener('input', changed);
    area.addEventListener('keydown', event => {
      if (event.key === 'Tab' && !event.shiftKey && !event.ctrlKey && !area.readOnly) {
        event.preventDefault();
        area.setRangeText('    ', area.selectionStart, area.selectionEnd, 'end');
        changed();
        return;
      }
      for (const { keybinding, handler } of commands) {
        const ctrl = (keybinding & KeyMod.CtrlCmd) !== 0;
        const key = keyName[keybinding & 255];
        if (key && ctrl === (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === key.toLowerCase()) {
          event.preventDefault();
          handler();
        }
      }
    });
    const model = { getValue: () => area.value, setValue: value => { area.value = value; changed(); } };
    return {
      getValue: model.getValue,
      setValue: model.setValue,
      getModel: () => model,
      onDidChangeModelContent(fn) { listeners.add(fn); return { dispose: () => listeners.delete(fn) }; },
      addCommand(keybinding, handler) { commands.push({ keybinding, handler }); return commands.length; },
      deltaDecorations: () => [],
      revealLineInCenterIfOutsideViewport() {},
      updateOptions(next = {}) { if ('readOnly' in next) area.readOnly = !!next.readOnly; },
      layout() {},
      focus() { area.focus(); },
      dispose() { listeners.clear(); area.remove(); },
    };
  }
  return Object.freeze({
    isFallback: true,
    KeyMod, KeyCode, Range,
    editor: Object.freeze({ create }),
    languages: Object.freeze({
      registerCompletionItemProvider: disposable,
      CompletionItemKind: {},
      CompletionItemInsertTextRule: {},
    }),
  });
}

window.MonacoReady = new Promise(resolve => {
  let settled = false;
  const fallback = error => {
    if (settled) return;
    settled = true;
    window.MonacoLoadError = error;
    console.error('Monaco editor failed to load; using the plain-text editor', error);
    window.monaco = createMonacoFallback();
    resolve(window.monaco);
  };
  if (typeof require !== 'function' || typeof require.config !== 'function') {
    fallback(new Error('Monaco loader is missing'));
    return;
  }
  require.config({ paths: { vs: '/vendor/vs' } });
  require.onError = fallback;
  require(['vs/editor/editor.main'], () => { if (!settled) { settled = true; resolve(window.monaco); } });
});
