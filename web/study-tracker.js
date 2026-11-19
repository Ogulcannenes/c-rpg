(() => {
  let trackedProfile = '';
  let sessionId = '';
  let visibleSeconds = 0;
  let lastTick = 0;
  let timer = 0;
  let lastSent = 0;

  function flush() {
    if (!trackedProfile || visibleSeconds <= lastSent) return;
    lastSent = visibleSeconds;
    const date = new Date();
    const day = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    const payload = { profile_id: trackedProfile, session_id: sessionId, seconds: visibleSeconds, day };
    fetch('/api/study/pulse', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), keepalive: true }).catch(() => { lastSent = Math.min(lastSent, visibleSeconds - 1); });
  }
  function start(profile) {
    clearInterval(timer); trackedProfile = profile || ''; visibleSeconds = 0; lastSent = 0;
    if (!trackedProfile) return;
    sessionId = crypto.randomUUID(); lastTick = Date.now();
    timer = setInterval(() => {
      const now = Date.now();
      if (document.visibilityState === 'visible' && trackedProfile) visibleSeconds += Math.min(2, Math.max(0, Math.floor((now - lastTick) / 1000)));
      lastTick = now;
      if (visibleSeconds - lastSent >= 30) flush();
    }, 1000);
  }
  const previousBoot = boot;
  boot = async function () { await previousBoot(); start(profileId); };
  const previousSelect = selectProfile;
  selectProfile = async function (...args) { await previousSelect(...args); start(profileId); };
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flush(); lastTick = Date.now(); });
  window.addEventListener('pagehide', flush);
  window.addEventListener('beforeunload', flush);
})();
