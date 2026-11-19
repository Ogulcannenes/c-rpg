(() => {
  let selected = 'git';
  let state = null;
  let lastRun = null;
  const modules = ['git', 'conflict', 'cmake', 'testing', 'terminal'];

  async function render() {
    if (!profileId) return;
    const host = document.querySelector('#view-devtools');
    host.innerHTML = `<div class="journal-loading">${L('ui.app.devtoolsLoading')}</div>`;
    const reply = await fetch(`/api/devtools?profile_id=${encodeURIComponent(profileId)}&module=${selected}`).then(r => r.json());
    if (reply.error) { host.innerHTML = `<div class="tip error">${esc(reply.error)}</div>`; return; }
    state = reply.state;
    const tabs = modules.map(id => `<button class="secondary dt-tab ${selected === id ? 'active' : ''}" data-dt-module="${id}">${dt(id)}</button>`).join('');
    const panel = selected === 'git' ? gitPanel() : selected === 'conflict' ? conflictPanel() : selected === 'cmake' ? cmakePanel() : selected === 'testing' ? testingPanel() : terminalPanel();
    host.innerHTML = `<span class="eyebrow">⌘ ${dt('nav').toUpperCase()}</span><h1 class="view-title">${dt('title')}</h1><p class="view-lead">${dt('lead')}</p><div class="editor-actions dt-tabs">${tabs}</div><div class="tip">${dt('safety')}</div>${panel}${state.last ? `<div class="panel dt-last"><b>${dt('output')}:</b> ${esc(state.last)}</div>` : ''}${lastRun ? `<div class="panel dt-last"><b>${lastRun.tests_passed ? '✓' : '✕'} ${dt('output')}</b><pre>${esc(lastRun.stdout || lastRun.output || lastRun.error || '')}</pre><small>${esc(lastRun.phase || '')} · exit ${lastRun.exit_code ?? '—'}</small></div>` : ''}`;
  }

  function gitPanel() {
    return `<div class="panel"><h2>${dt('git')}</h2><p>${L('ui.app.gitSafety')}</p><div class="editor-actions"><button class="primary" data-action="init">${dt('init')}</button><button class="secondary" data-action="status">${dt('status')}</button></div><div class="two-col" style="margin-top:12px"><label>${dt('file')}<input class="answer-input" id="dt-name" value="notes.txt"></label><label>${dt('branch')}<input class="answer-input" id="dt-branch" value="feature-notes"></label></div><label>${dt('content')}<textarea class="answer-input" id="dt-content" rows="4">Hello Git!</textarea></label><div class="editor-actions"><button class="secondary" data-action="write">${dt('write')}</button><button class="secondary" data-action="add">${dt('add')}</button><button class="primary" data-action="commit">${dt('commitBtn')}</button><button class="secondary" data-action="branch">${dt('branchBtn')}</button><button class="secondary" data-action="checkout">${L('ui.app.gitCheckout')}</button><button class="secondary" data-action="merge">${L('ui.app.gitMerge')}</button><button class="secondary" data-action="pull">${L('ui.app.gitPull')}</button><button class="secondary" data-action="push">${L('ui.app.gitPush')}</button></div><label style="display:block;margin-top:12px">${dt('commit')}<input class="answer-input" id="dt-message" value="Add learning notes"></label><div class="panel" style="margin-top:12px"><b>${L('ui.app.branch')}:</b> ${esc(state.branch)} · <b>Commits:</b> ${state.commits.length}<pre>${esc(JSON.stringify(state.files, null, 2))}</pre></div></div>`;
  }
  function conflictPanel() {
    return `<div class="panel"><h2>${dt('conflict')}</h2><p>${L('ui.app.conflictHelp')}</p><button class="primary" data-action="start">${dt('conflictStart')}</button>${state.conflict ? `<div class="two-col" style="margin:14px 0"><button class="secondary dt-version" data-choice="left">feature-a: ${esc(state.left)}</button><button class="secondary dt-version" data-choice="right">feature-b: ${esc(state.right)}</button></div><p id="dt-selected">${L('ui.app.chooseVersion')}</p><button class="primary" data-action="resolve">${dt('resolve')}</button>` : ''}</div>`;
  }
  function cmakePanel() {
    return `<div class="panel"><h2>${dt('cmake')}</h2><div class="offline-banner">${dt('cmakeStatus')}: <b>${state.cmake_available ? 'CMake' : (L('ui.app.cmakeSimulator'))}</b>. ${L('ui.app.noArbitraryCmake')}</div><ol>${DEVTOOLS_TEXT[lang].cmakeSteps.map((step, i) => `<li style="margin:12px 0"><button class="secondary" data-action="step" data-step="${i + 1}" ${i >= state.step ? '' : 'disabled'}>${step} ${i < state.step ? '✓' : ''}</button></li>`).join('')}</ol><p class="tip">${esc(state.last || `${state.step}/4`)}</p><button class="secondary" data-action="reset">${dt('reset')}</button> ${state.complete ? `<b class="status-ok">✓ ${dt('done')}</b>` : ''}</div>`;
  }
  function testingPanel() {
    return `<div class="panel"><h2>${dt('testing')}</h2><p>${L('ui.app.testingLabHelp')}</p><label>${dt('code')}<textarea class="answer-input code-input" id="dt-code" rows="10">${esc(state.code)}</textarea></label><div class="two-col"><label>${dt('input')}<textarea class="answer-input" id="dt-input" rows="3">${esc(state.input)}</textarea></label><label>${dt('expected')}<textarea class="answer-input" id="dt-expected" rows="3">${esc(state.expected)}</textarea></label></div><button class="primary" data-action="run">${dt('runTests')}</button> <span>${L('ui.app.runCount')}: ${state.runs} · ${L('ui.app.passedCount')}: ${state.passed}</span></div>`;
  }
  function terminalPanel() {
    return `<div class="panel"><h2>${dt('terminal')}</h2><div class="console dt-console">${(state.history || []).map(x => `<div><b>&gt; ${esc(x.command)}</b><pre>${esc(x.output)}</pre></div>`).join('') || esc(L('ui.app.terminalHint'))}</div><div class="editor-actions"><input class="answer-input" id="dt-command" placeholder="${dt('command')}"><button class="primary" data-action="terminal">${dt('execute')}</button></div></div>`;
  }

  async function act(button) {
    const action = button.dataset.action;
    const body = { module: selected, action };
    if (action === 'write') { body.name = document.querySelector('#dt-name').value; body.content = document.querySelector('#dt-content').value; }
    if (action === 'add') body.name = document.querySelector('#dt-name').value;
    if (action === 'commit') body.message = document.querySelector('#dt-message').value;
    if (action === 'branch') body.name = document.querySelector('#dt-branch').value;
    if (['checkout', 'merge'].includes(action)) body.name = document.querySelector('#dt-branch').value;
    if (action === 'resolve') body.resolved = state[document.querySelector('#dt-selected')?.dataset.choice] || '';
    if (action === 'step') body.step = Number(button.dataset.step);
    if (action === 'terminal') body.command = document.querySelector('#dt-command').value;
    if (action === 'run') { body.code = document.querySelector('#dt-code').value; body.input = document.querySelector('#dt-input').value; body.expected = document.querySelector('#dt-expected').value; }
    button.disabled = true;
    try {
      const result = await api('/api/devtools/action', body);
      if (result.error) { toast(result.error); return; }
      state = result.state; lastRun = result.result || null;
      await render();
    } finally { if (button.isConnected) button.disabled = false; }
  }

  document.addEventListener('click', event => {
    const nav = event.target.closest('.nav-item[data-view="devtools"]');
    if (nav) { selected = 'git'; lastRun = null; setView('devtools'); render(); return; }
    const tab = event.target.closest('.dt-tab');
    if (tab) { selected = tab.dataset.dtModule; lastRun = null; render(); return; }
    const choice = event.target.closest('.dt-version');
    if (choice) { const label = document.querySelector('#dt-selected'); label.dataset.choice = choice.dataset.choice; label.textContent = `${choice.dataset.choice}: ${state[choice.dataset.choice]}`; return; }
    const button = event.target.closest('[data-action]');
    if (button) act(button);
  });
  document.addEventListener('cpp-adventure-language-changed', () => { if (!document.querySelector('#view-devtools').classList.contains('hidden')) render(); });
})();
