(() => {
  const originalHome = renderHome;
  renderHome = function () {
    originalHome();
    if (!profileId) return;
    fetch(`/api/journal?profile_id=${encodeURIComponent(profileId)}`).then(r => r.json()).then(data => {
      const head = document.querySelector('#view-home .section-head');
      if (!head || data.error) return;
      document.querySelector('#adaptive-summary')?.remove();
      const suggestion = data.adaptive_path;
      const chapter = appState.curriculum.find(item => item.id === suggestion?.chapter_id);
      const section = document.createElement('section');
      section.id = 'adaptive-summary'; section.className = 'panel adaptive-panel';
      const title = chapter ? tx(chapter.title) : (L('ui.app.learningDataWaiting'));
      const predictions = data.predictions || [];
      section.innerHTML = `<div><span class="eyebrow">${L('ui.app.personalPath')}</span><h3>${L('ui.app.bestNextStep')}</h3><p>${esc(suggestion?.label || (L('ui.app.predictionNotEnough')))}</p>${chapter ? `<b>${esc(title)}</b>` : ''}</div><div class="adaptive-side"><span>${predictions.length ? L('ui.app.reviewTopicCount',{count:predictions.length}) : (L('ui.app.predictionInsufficient'))}</span><button class="secondary" id="adaptive-go">${L('ui.app.openPath')} →</button></div>`;
      head.before(section);
      section.querySelector('#adaptive-go').onclick = () => {
        if (!chapter) return;
        if (suggestion.task_id) openTaskById(suggestion.task_id); else openChapter(chapter.number - 1);
      };
    }).catch(() => {});
  };

  const originalJournal = renderJournal;
  renderJournal = async function () {
    await originalJournal();
    const host = document.querySelector('#view-journal');
    const data = await fetch(`/api/journal?profile_id=${encodeURIComponent(profileId)}`).then(r => r.json()).catch(() => null);
    if (!host || !data || data.error) return;
    host.querySelector('.adaptive-insights')?.remove();
    const predictions = data.predictions || [];
    const path = data.adaptive_path;
    const items = predictions.map(item => {
      const topic = appState.curriculum.find(ch => ch.id === item.chapter_id);
      return topic ? `<button class="journal-suggestion" data-insight-chapter="${topic.number - 1}"><span>${item.risk === 'high' ? '!' : '↻'}</span><span><b>${esc(tx(item.title))}</b><small>${esc(item.risk_label)} · ${L('ui.app.recentAttempts')} ${Math.round(item.recent_accuracy * 100)}% · ${item.attempts} ${L('ui.app.attemptCount')}</small></span></button>` : '';
    }).join('');
    const section = document.createElement('section');
    section.className = 'panel adaptive-insights';
    section.innerHTML = `<span class="eyebrow">${L('ui.app.dataSuggestion')}</span><h2>${L('ui.app.adaptivePath')}</h2><p>${esc(path?.label || '')}${path?.chapter_id ? ` · ${esc(tx(appState.curriculum.find(ch => ch.id === path.chapter_id)?.title || {}))}` : ''}</p>${predictions.length ? `<h3 class="journal-subhead">${L('ui.app.reviewPredictions')}</h3>${items}` : `<p class="journal-note">${esc(data.prediction_note || (L('ui.app.predictionAfterThree')))}</p>`}<small class="journal-note">${L('ui.app.predictionCaveat')}</small>`;
    host.querySelector('.journal-columns')?.before(section);
    section.querySelectorAll('[data-insight-chapter]').forEach(button => button.onclick = () => openChapter(Number(button.dataset.insightChapter)));
  };
})();
