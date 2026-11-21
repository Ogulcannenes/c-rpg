// skill-tree.js — the knowledge map's skill tree: a layered graph drawn from each chapter's real
// `prerequisites` (no hand-placed positions), so new chapters appear automatically.
// Nodes are <button>s (keyboard and screen-reader reachable); the SVG only draws the edges.
// Uses app.js globals: appState, lang, tx, toast, completedSet, chapterUnlocked, chapterDone, openChapter.
(() => {
  const esc = App.esc;
  const NODE_W = 184, NODE_H = 66, COL_W = 232, ROW_H = 84, PAD = 12;
  const copy = () => window.CppAdventureI18n.module('skillTree', lang === 'ru' ? 'ru' : 'tr');

  // Longest-path layering: a chapter sits one column right of its deepest prerequisite.
  function layout(chapters) {
    const byId = new Map(chapters.map((ch, i) => [ch.id, i]));
    const parentsOf = i => (chapters[i].prerequisites || []).map(id => byId.get(id)).filter(p => p !== undefined);
    const depth = new Array(chapters.length).fill(-1);
    const visiting = new Set();
    const depthOf = i => {
      if (depth[i] >= 0) return depth[i];
      if (visiting.has(i)) return 0; // a cycle would be a content bug; content_index.validate() rejects it
      visiting.add(i);
      const parents = parentsOf(i);
      depth[i] = parents.length ? 1 + Math.max(...parents.map(depthOf)) : 0;
      visiting.delete(i);
      return depth[i];
    };
    chapters.forEach((_, i) => depthOf(i));
    const columns = [];
    depth.forEach((d, i) => (columns[d] = columns[d] || []).push(i));
    // One barycentre pass: order each column by its parents' average row to reduce crossings.
    const row = new Array(chapters.length).fill(0);
    columns.forEach((column, d) => {
      if (d > 0) {
        const score = i => { const p = parentsOf(i); return p.length ? p.reduce((s, k) => s + row[k], 0) / p.length : 0; };
        column.sort((a, b) => score(a) - score(b) || a - b);
      }
      column.forEach((i, r) => (row[i] = r - (column.length - 1) / 2));
    });
    const maxRows = Math.max(...columns.map(col => col.length));
    const position = chapters.map((_, i) => ({
      x: PAD + depth[i] * COL_W,
      y: PAD + (row[i] + (maxRows - 1) / 2) * ROW_H,
    }));
    return {
      byId, depth, position,
      width: PAD * 2 + (columns.length - 1) * COL_W + NODE_W,
      height: PAD * 2 + (maxRows - 1) * ROW_H + NODE_H,
    };
  }

  const stateOf = i => (chapterDone(i) ? 'done' : chapterUnlocked(i) ? 'open' : 'locked');

  function render() {
    const host = document.querySelector('#view-map');
    const list = host?.querySelector('.knowledge-map');
    if (!list || !appState?.curriculum?.length) return;
    host.querySelector('.skill-tree-section')?.remove();
    const chapters = appState.curriculum;
    const c = copy();
    const { byId, position, width, height } = layout(chapters);
    const done = completedSet();
    const status = { done: c.done, open: c.open, locked: c.locked };

    const edges = [];
    chapters.forEach((chapter, child) => (chapter.prerequisites || []).forEach(id => {
      const parent = byId.get(id);
      if (parent === undefined) return;
      const a = position[parent], b = position[child];
      const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2, x2 = b.x, y2 = b.y + NODE_H / 2, mid = (x1 + x2) / 2;
      edges.push(`<path class="skill-edge ${chapterDone(parent) ? 'is-met' : ''}" data-from="${parent}" data-to="${child}" d="M${x1} ${y1} C${mid} ${y1} ${mid} ${y2} ${x2} ${y2}"/>`);
    }));

    const nodes = chapters.map((chapter, i) => {
      const state = stateOf(i);
      const finished = chapter.tasks.filter(t => done.has(t.id)).length;
      const needs = (chapter.prerequisites || []).map(id => chapters[byId.get(id)]).filter(Boolean);
      const number = String(chapter.number).padStart(2, '0');
      const label = `${number} · ${tx(chapter.title)} — ${status[state]}, ${finished}/${chapter.tasks.length}`
        + (needs.length ? `. ${c.requires}: ${needs.map(n => tx(n.title)).join(', ')}` : `. ${c.startHere}`);
      const { x, y } = position[i];
      return `<button type="button" class="skill-node is-${state}" data-skill="${i}" style="left:${x}px;top:${y}px;width:${NODE_W}px;height:${NODE_H}px" aria-label="${esc(label)}"${state === 'locked' ? ' aria-disabled="true"' : ''}>
        <span class="skill-node-num" aria-hidden="true">${state === 'done' ? '✓' : state === 'locked' ? '🔒' : number}</span>
        <span class="skill-node-title" aria-hidden="true">${esc(tx(chapter.title))}</span>
        <span class="skill-node-bar" aria-hidden="true"><span style="width:${Math.round(finished * 100 / chapter.tasks.length)}%"></span></span>
      </button>`;
    }).join('');

    list.insertAdjacentHTML('beforebegin', `<section class="skill-tree-section" aria-labelledby="skill-tree-title">
      <div class="skill-tree-head"><h2 id="skill-tree-title">${esc(c.title)}</h2><p class="dash-muted">${esc(c.lead)}</p></div>
      <div class="skill-tree-scroll">
        <div class="skill-tree" style="width:${width}px;height:${height}px">
          <svg class="skill-edges" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" aria-hidden="true" focusable="false">${edges.join('')}</svg>
          ${nodes}
        </div>
      </div>
      <h2 class="skill-tree-details">${esc(c.details)}</h2>
    </section>`);

    const tree = host.querySelector('.skill-tree');
    const highlight = (index, on) => tree.querySelectorAll(`.skill-edge[data-from="${index}"], .skill-edge[data-to="${index}"]`)
      .forEach(edge => edge.classList.toggle('is-lit', on));
    tree.addEventListener('click', event => {
      const node = event.target.closest('[data-skill]');
      if (!node) return;
      const index = Number(node.dataset.skill);
      if (!chapterUnlocked(index)) {
        const missing = (chapters[index].prerequisites || []).map(id => byId.get(id))
          .filter(k => k !== undefined && !chapterDone(k)).map(k => tx(chapters[k].title));
        toast(`${c.lockedHint}: ${missing.join(', ')}`);
        return;
      }
      openChapter(index);
    });
    const hover = on => event => { const node = event.target.closest('[data-skill]'); if (node) highlight(node.dataset.skill, on); };
    tree.addEventListener('mouseover', hover(true));
    tree.addEventListener('focusin', hover(true));
    tree.addEventListener('mouseout', hover(false));
    tree.addEventListener('focusout', hover(false));
    // Bring the learner's frontier into view on narrow windows.
    const frontier = tree.querySelector('.skill-node.is-open');
    if (frontier) host.querySelector('.skill-tree-scroll').scrollLeft = Math.max(0, frontier.offsetLeft - 40);
  }

  App.after('renderMap', render);
  window.SkillTree = Object.freeze({ render, layout });
})();
