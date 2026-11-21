// dashboard.js — the home view: what to do next, progress, and the companion, at a glance.
// app.js's renderHome() delegates here (window.Dashboard). Uses app.js globals: appState, lang,
// tr/tx, toast, completedSet, chapterUnlocked, chapterDone, currentOpenTask, openChapter,
// openTaskById, BADGES.
(() => {
  const esc = App.esc;
  const copy = () => window.CppAdventureI18n.module('dashboard', lang === 'ru' ? 'ru' : 'tr');
  const locale = () => (lang === 'ru' ? 'ru-RU' : 'tr-TR');
  const number = value => new Intl.NumberFormat(locale()).format(value);
  // forms: {one, few, many, other} with {n}; Turkish only uses "other", Russian needs one/few/many.
  const plural = (count, forms) => (forms[new Intl.PluralRules(locale()).select(count)] || forms.other).replace('{n}', number(count));

  function focusChapterIndex() {
    const chapters = appState.curriculum;
    for (let i = 0; i < chapters.length; i++) if (chapterUnlocked(i) && !chapterDone(i)) return i;
    return chapters.length - 1;
  }

  function continueCard(c) {
    const index = focusChapterIndex();
    const chapter = appState.curriculum[index];
    const done = completedSet();
    const finished = chapter.tasks.filter(task => done.has(task.id)).length;
    const next = chapter.tasks[currentOpenTask(index)];
    const percent = Math.round(finished * 100 / chapter.tasks.length);
    const allDone = appState.curriculum.every((_, i) => chapterDone(i));
    return `<section class="dash-card dash-continue" aria-labelledby="dash-continue-title">
      <span class="dash-eyebrow">${esc(allDone ? c.allDoneEyebrow : c.continueEyebrow)}</span>
      <h2 id="dash-continue-title">${esc(`${String(chapter.number).padStart(2, '0')} · ${tx(chapter.title)}`)}</h2>
      <p class="dash-muted">${esc(next ? `${c.nextTask}: ${tx(next.title)}` : c.chapterComplete)}</p>
      <div class="dash-progress" role="progressbar" aria-label="${esc(c.chapterProgress)}" aria-valuemin="0" aria-valuemax="${chapter.tasks.length}" aria-valuenow="${finished}">
        <span style="--value:${percent}%"></span>
      </div>
      <div class="dash-row">
        <small class="dash-muted">${esc(`${finished} / ${chapter.tasks.length} ${c.tasksDone}`)}</small>
        <button type="button" class="primary dash-cta" data-dash-action="continue" data-chapter="${index}">${esc(next ? c.continueButton : c.reviewButton)} →</button>
      </div>
    </section>`;
  }

  function playerCard(c) {
    const p = appState.profile;
    const need = Math.max(1, p.next_level_xp || 1);
    const have = Math.min(need, p.level_xp || 0);
    const percent = Math.round(have * 100 / need);
    const streak = p.streak || 0;
    return `<section class="dash-card dash-player" aria-labelledby="dash-player-title">
      <div class="dash-player-head">
        <div class="dash-avatar" aria-hidden="true">${typeof window.avatarHtml === 'function' ? window.avatarHtml(p.avatar) : esc(p.avatar)}</div>
        <div><h2 id="dash-player-title">${esc(p.name)}</h2><span class="dash-level">${esc(c.level)} ${number(p.level)}</span></div>
      </div>
      <div class="dash-progress dash-progress-xp" role="progressbar" aria-label="${esc(c.levelProgress)}" aria-valuemin="0" aria-valuemax="${need}" aria-valuenow="${have}">
        <span style="--value:${percent}%"></span>
      </div>
      <small class="dash-muted">${esc(`${number(have)} / ${number(need)} XP · ${c.toNextLevel}`)}</small>
      <dl class="dash-stats">
        <div><dt>${esc(c.totalXp)}</dt><dd>${number(p.lifetime_xp ?? p.xp)}</dd></div>
        <div><dt>${esc(c.balance)}</dt><dd>${number(p.balance ?? p.xp)}</dd></div>
        <div><dt>${esc(c.streak)}</dt><dd><span aria-hidden="true">🔥</span> ${esc(plural(streak, c.days))}</dd></div>
      </dl>
    </section>`;
  }

  function dailyCard(c) {
    const quest = appState.profile.daily_quest;
    if (!quest) return '';
    return `<section class="dash-card dash-daily ${quest.completed ? 'is-done' : ''}" aria-labelledby="dash-daily-title">
      <span class="dash-eyebrow">${esc(c.dailyQuest)}</span>
      <h3 id="dash-daily-title">${esc(tx(quest.title))}</h3>
      <p class="dash-muted dash-clamp">${esc(tx(quest.prompt))}</p>
      <div class="dash-row">
        <span class="dash-chip">${quest.completed ? '✓ ' + esc(c.completed) : `+${number(quest.reward)} XP`}</span>
        ${quest.completed ? '' : `<button type="button" class="secondary" data-dash-action="task" data-task="${esc(quest.task_id)}">${esc(c.start)}</button>`}
      </div>
    </section>`;
  }

  function progressCard(c) {
    const done = completedSet().size;
    const total = appState.profile.total_tasks || appState.curriculum.reduce((sum, ch) => sum + ch.tasks.length, 0);
    const chapters = appState.curriculum.filter((_, i) => chapterDone(i)).length;
    const percent = Math.round(done * 100 / Math.max(1, total));
    return `<section class="dash-card dash-overall" aria-labelledby="dash-overall-title">
      <h3 id="dash-overall-title" class="dash-eyebrow">${esc(c.overall)}</h3>
      <div class="dash-ring" role="img" aria-label="${esc(`${percent}% ${c.complete}`)}" style="--value:${percent}"><b>${percent}%</b></div>
      <dl class="dash-stats">
        <div><dt>${esc(c.tasks)}</dt><dd>${number(done)} / ${number(total)}</dd></div>
        <div><dt>${esc(c.chapters)}</dt><dd>${number(chapters)} / ${number(appState.curriculum.length)}</dd></div>
      </dl>
    </section>`;
  }

  function companionCard(c) {
    const p = appState.profile;
    const mood = p.daily_quest?.completed ? c.catHappy : (p.streak > 1 ? c.catStreak : c.catHello);
    const cat = typeof window.renderCatCompanion === 'function'
      ? window.renderCatCompanion(p.equipped_items || {}, false, `${c.companion}: ${p.name}`, p.level) : '';
    return `<section class="dash-card dash-companion" aria-labelledby="dash-companion-title">
      <div class="dash-cat">${cat}</div>
      <div><span class="dash-eyebrow">${esc(c.companion)}</span><h3 id="dash-companion-title">${esc(c.catName)}</h3><p class="dash-muted">${esc(mood)}</p></div>
    </section>`;
  }

  function achievementsCard(c) {
    const owned = appState.profile.achievements || [];
    const known = typeof BADGES !== 'undefined' ? BADGES : [];
    const recent = owned.slice(0, 3).map(id => known.find(b => b[0] === id)).filter(Boolean);
    const body = recent.length
      ? `<ul class="dash-badges">${recent.map(([, emoji, title]) => `<li><span aria-hidden="true">${emoji}</span>${esc(tr(title))}</li>`).join('')}</ul>`
      : `<p class="dash-muted">${esc(c.noBadges)}</p>`;
    return `<section class="dash-card dash-achievements" aria-labelledby="dash-badges-title">
      <div class="dash-row"><h3 id="dash-badges-title">${esc(c.achievements)}</h3><span class="dash-chip">${number(owned.length)} / ${number(known.length)}</span></div>
      ${body}
      <button type="button" class="link-button" data-dash-action="view" data-view="achievements">${esc(c.allAchievements)} →</button>
    </section>`;
  }

  function reviewCard(c) {
    const due = appState.profile.review_due || [];
    const items = due.slice(0, 3).map(item => {
      const chapter = appState.curriculum.find(ch => ch.tasks.some(t => t.id === item.task_id));
      const task = chapter?.tasks.find(t => t.id === item.task_id);
      return task ? `<li><button type="button" class="link-button" data-dash-action="task" data-task="${esc(task.id)}">${esc(tx(task.title))}</button></li>` : '';
    }).join('');
    return `<section class="dash-card dash-review" aria-labelledby="dash-review-title">
      <div class="dash-row"><h3 id="dash-review-title">${esc(c.review)}</h3><span class="dash-chip">${esc(plural(due.length, c.topics))}</span></div>
      ${items ? `<ul class="dash-list">${items}</ul>` : `<p class="dash-muted">${esc(c.noReview)}</p>`}
    </section>`;
  }

  function chapterTiles(c) {
    const done = completedSet();
    return `<section class="dash-chapters" aria-labelledby="dash-chapters-title">
      <div class="section-head"><div><h2 id="dash-chapters-title">${esc(c.chaptersTitle)}</h2><p class="dash-muted">${esc(c.chaptersLead)}</p></div></div>
      <ol class="dash-chapter-grid">${appState.curriculum.map((chapter, i) => {
        const open = chapterUnlocked(i), complete = chapterDone(i);
        const finished = chapter.tasks.filter(t => done.has(t.id)).length;
        const state = complete ? 'done' : open ? 'open' : 'locked';
        const status = complete ? c.statusDone : open ? c.statusOpen : c.statusLocked;
        return `<li><button type="button" class="dash-chapter is-${state}" data-dash-action="chapter" data-chapter="${i}">
          <span class="dash-chapter-num" aria-hidden="true">${String(chapter.number).padStart(2, '0')}</span>
          <span class="dash-chapter-title">${esc(tx(chapter.title))}</span>
          <span class="dash-chapter-meta">${esc(status)} · ${finished}/${chapter.tasks.length}</span>
        </button></li>`;
      }).join('')}</ol>
    </section>`;
  }

  function onClick(event) {
    const button = event.target.closest('[data-dash-action]');
    if (!button) return;
    const action = button.dataset.dashAction;
    if (action === 'continue' || action === 'chapter') {
      const index = Number(button.dataset.chapter);
      if (!chapterUnlocked(index)) {
        const chapter = appState.curriculum[index];
        const missing = (chapter.prerequisites || []).map(id => appState.curriculum.find(ch => ch.id === id)).filter(Boolean).map(ch => tx(ch.title));
        toast(`${copy().lockedHint}: ${missing.join(', ')}`);
        return;
      }
      openChapter(index);
    } else if (action === 'task') {
      openTaskById(button.dataset.task);
    } else if (action === 'view') {
      document.querySelector(`.nav-item[data-view="${button.dataset.view}"]`)?.click();
    }
  }

  function render() {
    const host = document.querySelector('#view-home');
    if (!host || !appState) return;
    const c = copy();
    host.innerHTML = `<header class="dash-header"><span class="dash-eyebrow">${esc(c.eyebrow)}</span><h1 class="view-title">${esc(c.greeting.replace('{name}', appState.profile.name))}</h1></header>
      <div class="dash-grid">
        ${continueCard(c)}${playerCard(c)}
        ${dailyCard(c)}${progressCard(c)}${companionCard(c)}
        ${reviewCard(c)}${achievementsCard(c)}
      </div>
      ${chapterTiles(c)}`;
    if (!host.dataset.dashBound) {
      host.addEventListener('click', onClick);
      host.dataset.dashBound = '1';
    }
  }

  window.Dashboard = Object.freeze({ render });
})();
