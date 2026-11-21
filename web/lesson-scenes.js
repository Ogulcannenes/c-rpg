// lesson-scenes.js — Konu anlatımlarına "canlı anlatım" sahneleri ekler.
// Sahneler /api/lesson-scenes uç noktasından gelir ve lab-theater.js motoruyla çizilir:
// kod satır satır yürür, değerler bellekteki yerlerine uçar, oklar ve akışlar canlanır.
// Sahne ekrana girince kendiliğinden oynar; kullanıcı durdurabilir, adım adım ilerleyebilir.
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = v => String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const currentLang = () => { try { return lang === 'ru' ? 'ru' : 'tr'; } catch (_) { return 'tr'; } };
  const T = (tr, ru) => currentLang() === 'ru' ? ru : tr;
  const reduce = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cache = new Map();
  const players = new Set();

  function load(chapterId, lg) {
    const key = `${chapterId}:${lg}`;
    if (!cache.has(key)) cache.set(key, fetch(`/api/lesson-scenes?chapter=${encodeURIComponent(chapterId)}&lang=${lg}`).then(r => r.json()).then(d => d.scenes || []).catch(() => { cache.delete(key); return []; }));
    return cache.get(key);
  }

  const observer = 'IntersectionObserver' in window ? new IntersectionObserver(entries => entries.forEach(entry => entry.target._scenePlayer?.visible(entry.isIntersecting && entry.intersectionRatio >= 0.4)), {threshold: [0, 0.4, 0.75]}) : null;

  function createPlayer(scene, host) {
    const fig = document.createElement('figure');
    fig.className = 'lesson-scene';
    fig.innerHTML = `<figcaption class="ls-head"><span class="ls-live"><i aria-hidden="true"></i>${T('Canlı anlatım', 'Живой разбор')}</span><b class="ls-title">${esc(scene.title)}</b>
      <div class="ls-ctrl"><button type="button" class="ls-prev" aria-label="${T('Geri adım', 'Шаг назад')}">‹</button><button type="button" class="ls-play"></button><button type="button" class="ls-next" aria-label="${T('İleri adım', 'Шаг вперёд')}">›</button></div></figcaption>
      <div class="ls-caption" aria-live="polite"><span class="ls-count"></span><p></p></div>
      <div class="ls-body"></div>`;
    host.append(fig);
    const last = scene.steps.length - 1;
    let index = 0, timer = 0, playing = false, started = false, resume = false;
    const inst = CppTheater.create($('.ls-body', fig), {className: 'is-lesson', duration: () => 640, onSeek: i => { stop(); go(i); }});
    const playBtn = $('.ls-play', fig);

    function sync() {
      const ended = index >= last && !playing;
      playBtn.innerHTML = playing ? `⏸ <span>${T('Duraklat', 'Пауза')}</span>` : ended && started ? `↻ <span>${T('Tekrar izle', 'Смотреть снова')}</span>` : `▶ <span>${T('Oynat', 'Играть')}</span>`;
      playBtn.setAttribute('aria-pressed', String(playing));
      $('.ls-prev', fig).disabled = index === 0;
      $('.ls-next', fig).disabled = index === last;
      fig.classList.toggle('is-playing', playing);
    }
    function go(i) {
      index = Math.max(0, Math.min(last, i));
      inst.render(scene, index);
      const step = scene.steps[index], caption = $('.ls-caption p', fig);
      caption.textContent = step.text;
      if (!reduce()) { caption.classList.remove('ls-in'); void caption.offsetWidth; caption.classList.add('ls-in'); }
      $('.ls-count', fig).textContent = `${index + 1}/${last + 1}`;
      sync();
    }
    const wait = () => Math.max(2600, Math.min(6200, 1500 + scene.steps[index].text.length * 42));
    function tick() {
      if (index >= last) { stop(); return; }
      go(index + 1);
      timer = setTimeout(tick, wait());
    }
    function play() {
      started = true;
      if (index >= last) go(0);
      playing = true; sync();
      clearTimeout(timer);
      timer = setTimeout(tick, wait());
    }
    function stop() { playing = false; clearTimeout(timer); sync(); }

    playBtn.onclick = () => { resume = false; playing ? stop() : play(); };
    $('.ls-prev', fig).onclick = () => { stop(); go(index - 1); };
    $('.ls-next', fig).onclick = () => { stop(); started = true; go(index + 1); };
    fig.addEventListener('keydown', event => {
      if (event.key === 'ArrowRight') { event.preventDefault(); $('.ls-next', fig).click(); }
      if (event.key === 'ArrowLeft') { event.preventDefault(); $('.ls-prev', fig).click(); }
    });

    const player = {
      fig,
      visible(on) {
        if (on && !started && !reduce()) play();
        else if (on && resume) { resume = false; play(); }
        else if (!on && playing) { resume = true; stop(); }
      },
      destroy() { stop(); observer?.unobserve(fig); players.delete(player); },
      relayout() { inst.relayout(); }
    };
    fig._scenePlayer = player;
    players.add(player);
    go(0);
    observer?.observe(fig);
    return player;
  }

  async function decorate() {
    const view = $('#view-lesson');
    let chapter = null, lg = currentLang();
    try { chapter = appState.curriculum[currentChapter]; } catch (_) { return; }
    if (!view || !chapter || !window.CppTheater) return;
    const sections = $$('.lesson-concept', view);
    if (!sections.length) return;
    const token = `${chapter.id}:${lg}:${Date.now()}`;
    view.dataset.sceneToken = token;
    players.forEach(p => { if (!document.contains(p.fig)) p.destroy(); });
    const scenes = await load(chapter.id, lg);
    if (view.dataset.sceneToken !== token) return;
    scenes.forEach(scene => {
      const section = sections[scene.section];
      const host = section && section.querySelector(':scope > div:last-child');
      if (!host || $('.lesson-scene', host)) return;
      section.classList.add('has-scene');
      createPlayer(scene, host);
    });
  }

  App.after('renderLessonIntro', () => decorate());

  document.addEventListener('DOMContentLoaded', () => {
    let resizeTimer = 0;
    window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => players.forEach(p => document.contains(p.fig) ? p.relayout() : p.destroy()), 140); });
  });
})();
