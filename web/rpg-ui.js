(()=>{
  const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const text=(tr,ru)=>typeof lang!=='undefined'&&lang==='ru'?ru:tr;
  const profile=()=>typeof profileId==='string'?profileId:'';
  const WORLD_ZONES={get tr(){return window.CppAdventureI18n.module('worldZones','tr')},get ru(){return window.CppAdventureI18n.module('worldZones','ru')}};
  // Serpentine route: 4 rows of 5 zones, alternating direction, so cards never overlap and the order reads like a path.
  const WORLD_COLUMNS=[11,30.5,50,69.5,89],WORLD_ROWS=[13,38,63,87];
  const WORLD_POSITIONS=Array.from({length:20},(_,i)=>{const row=Math.floor(i/5),col=i%5;return [WORLD_COLUMNS[row%2?4-col:col],WORLD_ROWS[row]]});
  // Route drawn under the cards: done segments glow, open ones are dashed, locked ones fade.
  function worldRoute(states){
    const pt=i=>{const [x,y]=WORLD_POSITIONS[i];return [x*15,y*9]};
    let segs='';
    for(let i=0;i<Math.min(states.length,WORLD_POSITIONS.length)-1;i++){
      const [x1,y1]=pt(i),[x2,y2]=pt(i+1);
      const d=y1===y2?`M${x1} ${y1}Q${(x1+x2)/2} ${y1+(i%2?-34:34)} ${x2} ${y2}`:`M${x1} ${y1}C${x1+(x1>750?150:-150)} ${y1} ${x2+(x2>750?150:-150)} ${y2} ${x2} ${y2}`;
      const cls=states[i+1].cleared&&states[i].cleared?'done':states[i+1].unlocked?'open':'locked';
      segs+=`<path class="route-${cls}" d="${d}"/>`;
    }
    return `<svg class="world-route" viewBox="0 0 1500 900" aria-hidden="true">${segs}</svg>`;
  }
  window.CppAdventureWorldMap={get zones(){return WORLD_ZONES.tr.map((tr,index)=>({tr,ru:WORLD_ZONES.ru[index]}))}};
  async function request(url,body){const response=await fetch(url,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify({...body,profile_id:profile()}):undefined});return {status:response.status,data:await response.json()}}
  async function render(){
    const host=$('#view-rpg'); if(!profile()){host.innerHTML=`<div class="panel">${L('pairs.rpg.001')}</div>`;return}
    host.innerHTML=`<div class="journal-loading">${L('pairs.rpg.002')}</div>`;
    const [{data:rpg},{data:shop}]=await Promise.all([request(`/api/rpg?profile_id=${encodeURIComponent(profile())}`),request('/api/shop')]);
    if(rpg.error){host.innerHTML=`<div class="tip error">${esc(rpg.error)}</div>`;return}
    const ru=typeof lang!=='undefined'&&lang==='ru', gear=rpg.owned_items.map(id=>{const item=shop.items[id];return item?{id,...item}:null}).filter(Boolean);
    const stage=rpg.companion_stage, next=rpg.next_rank;
    const chapters=typeof appState!=='undefined'&&Array.isArray(appState?.curriculum)?appState.curriculum:[];
    const completed=typeof completedSet==='function'?completedSet():new Set();
    const routeStates=chapters.map((chapter,index)=>{const boss=(chapter.tasks||[]).find(task=>task.kind==='boss');return {unlocked:typeof chapterUnlocked==='function'&&chapterUnlocked(index),cleared:!!boss&&completed.has(boss.id)}});const currentZone=routeStates.findIndex(z=>z.unlocked&&!z.cleared);
    const world=chapters.map((chapter,index)=>{
      const zone=[WORLD_ZONES.tr[index]||chapter.title?.tr||`Region ${index+1}`,WORLD_ZONES.ru[index]||chapter.title?.ru||`Регион ${index+1}`];
      const unlocked=typeof chapterUnlocked==='function'&&chapterUnlocked(index);
      const done=(chapter.tasks||[]).filter(task=>completed.has(task.id)).length;
      const boss=(chapter.tasks||[]).find(task=>task.kind==='boss');
      const bossDone=!!boss&&completed.has(boss.id);
      const percent=chapter.tasks?.length?Math.round(done*100/chapter.tasks.length):0;
      const status=bossDone?L('pairs.rpg.003'):unlocked?L('pairs.rpg.004'):L('pairs.rpg.005');
      const activeIndex=unlocked&&typeof currentOpenTask==='function'?currentOpenTask(index):-1;
      const active=activeIndex>=0?chapter.tasks[activeIndex]:null;
      const [x,y]=WORLD_POSITIONS[index]||[8+(index%5)*19,8+Math.floor(index/5)*28];
      return `<article class="world-zone ${unlocked?'open':'locked'} ${bossDone?'cleared':''} ${index===currentZone?'current':''}" style="--zone-x:${x}%;--zone-y:${y}%" data-world-zone="${index}"><button class="world-zone-select" data-world-chapter="${index}" ${unlocked?'':'disabled'} aria-label="${esc(L('pairs.rpg.006')+text(zone[0],zone[1]))}"><span class="world-zone-top"><span class="world-zone-emblem">${typeof chapterIcon==='function'?chapterIcon(unlocked?index:-1):''}</span><span class="world-zone-number">${String(index+1).padStart(2,'0')}</span><span class="world-zone-state">${status}</span></span><strong>${esc(text(zone[0],zone[1]))}</strong><span class="world-zone-topic">${esc(tx(chapter.title))}</span><span class="world-zone-progress"><span>${done}/${chapter.tasks.length} ${L('pairs.rpg.007')}</span><i><b style="width:${percent}%"></b></i></span>${active?`<span class="world-active-quest">${L('pairs.rpg.008')}${esc(tx(active.title))}</span>`:''}</button>${boss?`<button class="world-boss ${bossDone?'defeated':''}" data-world-boss="${esc(boss.id)}" ${unlocked&&!bossDone?'':'disabled'}>${bossDone?L('pairs.rpg.009'):L('pairs.rpg.010')}</button>`:''}</article>`
    }).join('');
    host.innerHTML=`<span class="eyebrow">♟ ${L('pairs.rpg.011')}</span><h1 class="view-title">${L('pairs.rpg.012')}</h1><p class="view-lead">${L('pairs.rpg.013')}</p>
      <div class="rpg-hero panel"><div class="rpg-cat">${typeof catStage==='function'?catStage('',false):`<img src="/assets/cat-companion.png" alt="${L('pairs.rpg.014')}">`}<small>${L('pairs.rpg.015')} ${stage}</small></div><div class="rpg-rank"><span class="eyebrow">${L('pairs.rpg.016')}</span><h2>${esc(rpg.rank.title)}</h2><p>${rpg.xp} XP · ${L('pairs.rpg.017')} ${rpg.rank.index}/${rpg.rank.count}</p>${next?`<div class="rpg-meter"><i style="width:${next.progress}%"></i></div><small>${Math.max(0,next.xp-rpg.xp)} XP · ${L('pairs.rpg.018')} ${esc(next.title)}</small>`:`<small>${L('pairs.rpg.019')}</small>`}<div class="rpg-metrics"><span>${rpg.metrics.bosses} / 3 ${L('pairs.rpg.020')}</span><span>${rpg.metrics.projects} ${L('pairs.rpg.021')}</span><span>${rpg.metrics.items} ${L('pairs.rpg.022')}</span><span>${rpg.metrics.minutes} ${L('pairs.rpg.023')}</span></div></div></div>
      <section class="rpg-section rpg-world"><div class="section-head"><div><span class="eyebrow">${L('pairs.rpg.024')}</span><h2>${L('pairs.rpg.025')}</h2><p>${L('pairs.rpg.026')}</p></div><span class="world-map-legend"><i></i>${L('pairs.rpg.027')} <i class="locked-dot"></i>${L('pairs.rpg.028')} <i class="boss-dot"></i>${L('pairs.rpg.029')}</span></div><div class="world-map-toolbar"><span>${L('pairs.rpg.030')}</span><div><button class="secondary" id="world-zoom-out" aria-label="${L('pairs.rpg.031')}">−</button><output id="world-zoom-label">100%</output><button class="secondary" id="world-zoom-in" aria-label="${L('pairs.rpg.032')}">+</button><button class="secondary" id="world-focus">${L('motion.mapFocus')}</button><button class="secondary" id="world-zoom-reset">${L('pairs.rpg.033')}</button></div></div><div class="world-map-viewport" id="world-map-viewport" aria-label="${L('pairs.rpg.034')}"><div class="world-map-canvas" id="world-map-canvas"><img class="world-map-art" src="/assets/cpp-world-map.svg" alt="${L('pairs.rpg.035')}" draggable="false">${worldRoute(routeStates)}<div class="world-map-path">${world||`<div class="panel">${L('pairs.rpg.036')}</div>`}</div></div></div></section>
      <section class="rpg-section"><div class="section-head"><div><h2>${L('pairs.rpg.037')}</h2><p>${L('pairs.rpg.038')}</p></div><button class="secondary" id="rpg-shop">${L('pairs.rpg.039')}</button></div><div class="rpg-quest-grid">${rpg.secret_quests.map(q=>`<article class="panel rpg-quest ${q.claimed?'claimed':''}"><div class="rpg-quest-icon">${q.claimed?'✓':'✦'}</div><h3>${esc(q.title)}</h3><p>${esc(q.description)}</p><div class="rpg-meter"><i style="width:${Math.round(q.progress/q.target*100)}%"></i></div><small>${q.progress}/${q.target} · +${q.reward} XP</small><button class="${q.unlocked&&!q.claimed?'primary':'secondary'}" data-rpg-claim="${esc(q.id)}" ${q.unlocked&&!q.claimed?'':'disabled'}>${q.claimed?L('pairs.rpg.040'):q.unlocked?L('pairs.rpg.041'):L('pairs.rpg.042')}</button></article>`).join('')}</div></section>
      <section class="rpg-section"><h2>${L('pairs.rpg.043')}</h2><p>${L('pairs.rpg.044')}</p><div class="rpg-gear-row">${gear.length?gear.map(item=>`<button class="rpg-gear ${item.id===rpg.active_item?'equipped':''}" data-rpg-equip="${esc(item.id)}"><span class="rpg-gear-art">${window.shopItemArt?window.shopItemArt(item.id):item.icon}</span><b>${esc(item.name[ru?'ru':'tr'])}</b><small>${item.id===rpg.active_item?L('pairs.rpg.045'):L('pairs.rpg.046')}</small></button>`).join(''):`<div class="panel">${L('pairs.rpg.047')}</div>`}<button class="rpg-gear unequip" data-rpg-equip="">${L('pairs.rpg.048')}</button></div></section>`;
    host.querySelector('.rpg-hero')?.insertAdjacentHTML('afterend',window.CppAdventureCatGuide('boss','catBoss'));
    host.querySelector('#rpg-shop').onclick=()=>document.querySelector('[data-view="shop"]')?.click();
    host.querySelectorAll('[data-world-chapter]').forEach(button=>button.onclick=()=>openChapter(Number(button.dataset.worldChapter)));
    host.querySelectorAll('[data-world-boss]').forEach(button=>button.onclick=()=>openTaskById(button.dataset.worldBoss));
    setupWorldMap();
    host.querySelectorAll('[data-rpg-claim]').forEach(btn=>btn.onclick=async()=>{btn.disabled=true;const {data}=await request('/api/rpg/secret/claim',{quest_id:btn.dataset.rpgClaim});if(data.error){window.toast?.(data.error);btn.disabled=false;return}window.toast?.(`+${data.reward} XP`,true);await render()});
    host.querySelectorAll('[data-rpg-equip]').forEach(btn=>btn.onclick=async()=>{btn.disabled=true;const {data}=await request('/api/rpg/equip',{item_id:btn.dataset.rpgEquip});if(data.error){window.toast?.(data.error);btn.disabled=false;return}if(typeof refresh==='function')await refresh();await render()});
  }
  // Interactive world map: always fills the viewport (no empty bands), panning is clamped to the art,
  // drags glide with inertia, cards can be dragged too, and buttons/keys animate smoothly.
  function setupWorldMap(){
    const viewport=$('#world-map-viewport'),canvas=$('#world-map-canvas'),label=$('#world-zoom-label');if(!viewport||!canvas)return;
    const W=1500,H=900,reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let cover=1,scale=1,tx=0,ty=0,drag=null,moved=false,velocity={x:0,y:0},glide=0;
    const measure=()=>{cover=Math.max(viewport.clientWidth/W,viewport.clientHeight/H)};
    const clamp=()=>{scale=Math.max(cover,Math.min(cover*3,scale));tx=Math.min(0,Math.max(viewport.clientWidth-W*scale,tx));ty=Math.min(0,Math.max(viewport.clientHeight-H*scale,ty))};
    const paint=(animate=false)=>{clamp();canvas.classList.toggle('map-animating',animate&&!reduce);canvas.style.transform=`translate(${tx}px,${ty}px) scale(${scale})`;if(label)label.value=`${Math.round(scale/cover*100)}%`;if(animate)setTimeout(()=>canvas.classList.remove('map-animating'),480)};
    const zoomAt=(next,cx=viewport.clientWidth/2,cy=viewport.clientHeight/2,animate=false)=>{const mx=(cx-tx)/scale,my=(cy-ty)/scale;scale=Math.max(cover,Math.min(cover*3,next));tx=cx-mx*scale;ty=cy-my*scale;paint(animate)};
    const focusZone=(zone,animate=true)=>{if(!zone)return;scale=Math.max(scale,Math.min(1,cover*2));const fx=parseFloat(zone.style.getPropertyValue('--zone-x'))*W/100,fy=parseFloat(zone.style.getPropertyValue('--zone-y'))*H/100;tx=viewport.clientWidth/2-fx*scale;ty=viewport.clientHeight/2-fy*scale;paint(animate)};
    const current=()=>canvas.querySelector('.world-zone.current')||[...canvas.querySelectorAll('.world-zone.cleared')].pop()||canvas.querySelector('.world-zone');
    measure();scale=cover;
    if(cover<.92)focusZone(current(),false);else{tx=(viewport.clientWidth-W*scale)/2;ty=(viewport.clientHeight-H*scale)/2;paint()}
    $('#world-zoom-in').onclick=()=>zoomAt(scale*1.3,undefined,undefined,true);
    $('#world-zoom-out').onclick=()=>zoomAt(scale/1.3,undefined,undefined,true);
    $('#world-zoom-reset').onclick=()=>{scale=cover;tx=(viewport.clientWidth-W*scale)/2;ty=(viewport.clientHeight-H*scale)/2;paint(true)};
    const focusBtn=$('#world-focus');if(focusBtn)focusBtn.onclick=()=>focusZone(current());
    viewport.tabIndex=0;
    viewport.addEventListener('keydown',e=>{const step=80,keys={ArrowLeft:[step,0],ArrowRight:[-step,0],ArrowUp:[0,step],ArrowDown:[0,-step]};if(keys[e.key]){e.preventDefault();tx+=keys[e.key][0];ty+=keys[e.key][1];paint(true)}else if(e.key==='+'||e.key==='='){zoomAt(scale*1.3,undefined,undefined,true)}else if(e.key==='-'){zoomAt(scale/1.3,undefined,undefined,true)}});
    viewport.addEventListener('wheel',e=>{e.preventDefault();const r=viewport.getBoundingClientRect();zoomAt(scale*(e.deltaY<0?1.12:1/1.12),e.clientX-r.left,e.clientY-r.top)},{passive:false});
    viewport.addEventListener('dblclick',e=>{if(e.target.closest('button'))return;const r=viewport.getBoundingClientRect();zoomAt(scale*1.6,e.clientX-r.left,e.clientY-r.top,true)});
    viewport.addEventListener('pointerdown',e=>{if(e.button!==0)return;cancelAnimationFrame(glide);drag={x:e.clientX,y:e.clientY,tx,ty,t:performance.now(),id:e.pointerId};moved=false;velocity={x:0,y:0}});
    viewport.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(!moved&&Math.abs(dx)+Math.abs(dy)>5){moved=true;viewport.setPointerCapture(drag.id);viewport.classList.add('dragging')}if(!moved)return;const now=performance.now(),dt=Math.max(1,now-drag.t);velocity={x:(e.clientX-(drag.lx??drag.x))/dt,y:(e.clientY-(drag.ly??drag.y))/dt};drag.lx=e.clientX;drag.ly=e.clientY;drag.t=now;tx=drag.tx+dx;ty=drag.ty+dy;paint()});
    const release=()=>{if(!drag)return;drag=null;viewport.classList.remove('dragging');const was=moved;setTimeout(()=>{moved=false},0);if(!was||reduce)return;let vx=velocity.x*16,vy=velocity.y*16;const step=()=>{vx*=.92;vy*=.92;tx+=vx;ty+=vy;paint();if(Math.abs(vx)+Math.abs(vy)>.4)glide=requestAnimationFrame(step)};glide=requestAnimationFrame(step)};
    viewport.addEventListener('pointerup',release);viewport.addEventListener('pointercancel',release);
    // A drag that started on a zone card must not also open that chapter.
    viewport.addEventListener('click',e=>{if(moved){e.stopPropagation();e.preventDefault();moved=false}},true);
    const onResize=()=>{if(!viewport.isConnected)return window.removeEventListener('resize',onResize);const ratio=scale/cover;measure();scale=cover*ratio;paint()};window.addEventListener('resize',onResize);
  }
  document.addEventListener('DOMContentLoaded',()=>{
    const item=document.querySelector('[data-view="rpg"]');const label=item?.querySelector('[data-rpg-label]');
    if(item)item.addEventListener('click',()=>{if(typeof setView==='function')setView('rpg');const crumb=$('#crumb-current');if(crumb)crumb.textContent=L('pairs.rpg.049');render()});
    if(label)label.textContent=L('pairs.rpg.050');
    document.addEventListener('cpp-adventure-language-changed',()=>{if(label)label.textContent=L('pairs.rpg.051');if(!$('#view-rpg')?.classList.contains('hidden'))render()});
  });
})();
