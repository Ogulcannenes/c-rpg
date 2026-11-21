// Monaco editor bootstrap (moved out of index.html so the CSP can forbid inline scripts).
// window.MonacoReady always settles: it resolves with monaco, or with null if the vendored
// editor cannot load, so callers never wait forever on an empty editor box.
window.MonacoLoadError = null;
window.MonacoReady = new Promise(resolve => {
  require.config({ paths: { vs: '/vendor/vs' } });
  require.onError = error => {
    window.MonacoLoadError = error;
    console.error('Monaco editor failed to load', error);
    resolve(null);
  };
  require(['vs/editor/editor.main'], () => resolve(window.monaco));
});
