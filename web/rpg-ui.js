(()=>{
  const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const text=(tr,ru)=>typeof lang!=='undefined'&&lang==='ru'?ru:tr;
  const profile=()=>typeof profileId==='string'?profileId:'';
  const WORLD_ZONES={get tr(){return window.CppAdventureI18n.module('worldZones','tr')},get ru(){return window.CppAdventureI18n.module('worldZones','ru')}};
  const WORLD_POSITIONS=[[8,10],[28,7],[49,10],[72,12],[86,25],[9,38],[33,33],[54,35],[76,37],[8,66],[30,64],[53,65],[76,67],[20,83],[65,83]];
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
    const world=chapters.map((chapter,index)=>{
      const zone=[WORLD_ZONES.tr[index],WORLD_ZONES.ru[index]]||[chapter.title?.tr||`Region ${index+1}`,chapter.title?.ru||`Регион ${index+1}`];
      const unlocked=typeof chapterUnlocked==='function'&&chapterUnlocked(index);
      const done=(chapter.tasks||[]).filter(task=>completed.has(task.id)).length;
      const boss=(chapter.tasks||[]).find(task=>task.kind==='boss');
      const bossDone=!!boss&&completed.has(boss.id);
      const percent=chapter.tasks?.length?Math.round(done*100/chapter.tasks.length):0;
      const status=bossDone?L('pairs.rpg.003'):unlocked?L('pairs.rpg.004'):L('pairs.rpg.005');
      const activeIndex=unlocked&&typeof currentOpenTask==='function'?currentOpenTask(index):-1;
      const active=activeIndex>=0?chapter.tasks[activeIndex]:null;
      const [x,y]=WORLD_POSITIONS[index]||[8+(index%5)*19,8+Math.floor(index/5)*28];
      return `<article class="world-zone ${unlocked?'open':'locked'} ${bossDone?'cleared':''}" style="--zone-x:${x}%;--zone-y:${y}%" data-world-zone="${index}"><button class="world-zone-select" data-world-chapter="${index}" ${unlocked?'':'disabled'} aria-label="${esc(L('pairs.rpg.006')+text(zone[0],zone[1]))}"><span class="world-zone-top"><span class="world-zone-number">${String(index+1).padStart(2,'0')}</span><span class="world-zone-state">${status}</span></span><strong>${esc(text(zone[0],zone[1]))}</strong><span class="world-zone-topic">${esc(tx(chapter.title))}</span><span class="world-zone-progress"><span>${done}/${chapter.tasks.length} ${L('pairs.rpg.007')}</span><i><b style="width:${percent}%"></b></i></span>${active?`<span class="world-active-quest">${L('pairs.rpg.008')}${esc(tx(active.title))}</span>`:''}</button>${boss?`<button class="world-boss ${bossDone?'defeated':''}" data-world-boss="${esc(boss.id)}" ${unlocked&&!bossDone?'':'disabled'}>${bossDone?L('pairs.rpg.009'):L('pairs.rpg.010')}</button>`:''}</article>`
    }).join('');
    host.innerHTML=`<span class="eyebrow">♟ ${L('pairs.rpg.011')}</span><h1 class="view-title">${L('pairs.rpg.012')}</h1><p class="view-lead">${L('pairs.rpg.013')}</p>
      <div class="rpg-hero panel"><div class="rpg-cat"><img src="/assets/cat-companion.png" alt="${L('pairs.rpg.014')}"><span class="rpg-wear">${gear.find(x=>x.id===rpg.active_item)?.icon||''}</span><small>${L('pairs.rpg.015')} ${stage}</small></div><div class="rpg-rank"><span class="eyebrow">${L('pairs.rpg.016')}</span><h2>${esc(rpg.rank.title)}</h2><p>${rpg.xp} XP · ${L('pairs.rpg.017')} ${rpg.rank.index}/${rpg.rank.count}</p>${next?`<div class="rpg-meter"><i style="width:${next.progress}%"></i></div><small>${Math.max(0,next.xp-rpg.xp)} XP · ${L('pairs.rpg.018')} ${esc(next.title)}</small>`:`<small>${L('pairs.rpg.019')}</small>`}<div class="rpg-metrics"><span>${rpg.metrics.bosses} / 3 ${L('pairs.rpg.020')}</span><span>${rpg.metrics.projects} ${L('pairs.rpg.021')}</span><span>${rpg.metrics.items} ${L('pairs.rpg.022')}</span><span>${rpg.metrics.minutes} ${L('pairs.rpg.023')}</span></div></div></div>
      <section class="rpg-section rpg-world"><div class="section-head"><div><span class="eyebrow">${L('pairs.rpg.024')}</span><h2>${L('pairs.rpg.025')}</h2><p>${L('pairs.rpg.026')}</p></div><span class="world-map-legend"><i></i>${L('pairs.rpg.027')} <i class="locked-dot"></i>${L('pairs.rpg.028')} <i class="boss-dot"></i>${L('pairs.rpg.029')}</span></div><div class="world-map-toolbar"><span>${L('pairs.rpg.030')}</span><div><button class="secondary" id="world-zoom-out" aria-label="${L('pairs.rpg.031')}">−</button><output id="world-zoom-label">100%</output><button class="secondary" id="world-zoom-in" aria-label="${L('pairs.rpg.032')}">+</button><button class="secondary" id="world-zoom-reset">${L('pairs.rpg.033')}</button></div></div><div class="world-map-viewport" id="world-map-viewport" aria-label="${L('pairs.rpg.034')}"><div class="world-map-canvas" id="world-map-canvas"><img class="world-map-art" src="/assets/cpp-world-map.svg" alt="${L('pairs.rpg.035')}" draggable="false"><div class="world-map-path">${world||`<div class="panel">${L('pairs.rpg.036')}</div>`}</div></div></div></section>
      <section class="rpg-section"><div class="section-head"><div><h2>${L('pairs.rpg.037')}</h2><p>${L('pairs.rpg.038')}</p></div><button class="secondary" id="rpg-shop">${L('pairs.rpg.039')}</button></div><div class="rpg-quest-grid">${rpg.secret_quests.map(q=>`<article class="panel rpg-quest ${q.claimed?'claimed':''}"><div class="rpg-quest-icon">${q.claimed?'✓':'✦'}</div><h3>${esc(q.title)}</h3><p>${esc(q.description)}</p><div class="rpg-meter"><i style="width:${Math.round(q.progress/q.target*100)}%"></i></div><small>${q.progress}/${q.target} · +${q.reward} XP</small><button class="${q.unlocked&&!q.claimed?'primary':'secondary'}" data-rpg-claim="${esc(q.id)}" ${q.unlocked&&!q.claimed?'':'disabled'}>${q.claimed?L('pairs.rpg.040'):q.unlocked?L('pairs.rpg.041'):L('pairs.rpg.042')}</button></article>`).join('')}</div></section>
      <section class="rpg-section"><h2>${L('pairs.rpg.043')}</h2><p>${L('pairs.rpg.044')}</p><div class="rpg-gear-row">${gear.length?gear.map(item=>`<button class="rpg-gear ${item.id===rpg.active_item?'equipped':''}" data-rpg-equip="${esc(item.id)}"><span>${item.icon}</span><b>${esc(item.name[ru?'ru':'tr'])}</b><small>${item.id===rpg.active_item?L('pairs.rpg.045'):L('pairs.rpg.046')}</small></button>`).join(''):`<div class="panel">${L('pairs.rpg.047')}</div>`}<button class="rpg-gear unequip" data-rpg-equip="">${L('pairs.rpg.048')}</button></div></section>`;
    host.querySelector('.rpg-hero')?.insertAdjacentHTML('afterend',window.CppAdventureCatGuide('boss','catBoss'));
    host.querySelector('#rpg-shop').onclick=()=>document.querySelector('[data-view="shop"]')?.click();
    host.querySelectorAll('[data-world-chapter]').forEach(button=>button.onclick=()=>openChapter(Number(button.dataset.worldChapter)));
    host.querySelectorAll('[data-world-boss]').forEach(button=>button.onclick=()=>openTaskById(button.dataset.worldBoss));
    setupWorldMap();
    host.querySelectorAll('[data-rpg-claim]').forEach(btn=>btn.onclick=async()=>{btn.disabled=true;const {data}=await request('/api/rpg/secret/claim',{quest_id:btn.dataset.rpgClaim});if(data.error){window.toast?.(data.error);btn.disabled=false;return}window.toast?.(`+${data.reward} XP`,true);await render()});
    host.querySelectorAll('[data-rpg-equip]').forEach(btn=>btn.onclick=async()=>{btn.disabled=true;const {data}=await request('/api/rpg/equip',{item_id:btn.dataset.rpgEquip});if(data.error){window.toast?.(data.error);btn.disabled=false;return}await render()});
  }
  function setupWorldMap(){
    const viewport=$('#world-map-viewport'),canvas=$('#world-map-canvas'),label=$('#world-zoom-label');if(!viewport||!canvas)return;
    let fit=Math.min(viewport.clientWidth/1500,viewport.clientHeight/900),scale=fit,tx=(viewport.clientWidth-1500*fit)/2,ty=(viewport.clientHeight-900*fit)/2,drag=null,moved=false;
    const paint=()=>{canvas.style.transform=`translate(${tx}px,${ty}px) scale(${scale})`;if(label)label.value=`${Math.round(scale/fit*100)}%`};
    const zoom=(next,cx=viewport.clientWidth/2,cy=viewport.clientHeight/2)=>{const mapX=(cx-tx)/scale,mapY=(cy-ty)/scale;scale=Math.max(fit*.82,Math.min(fit*2.6,next));tx=cx-mapX*scale;ty=cy-mapY*scale;paint()};
    $('#world-zoom-in').onclick=()=>zoom(scale*1.2);$('#world-zoom-out').onclick=()=>zoom(scale/1.2);$('#world-zoom-reset').onclick=()=>{scale=fit;tx=(viewport.clientWidth-1500*fit)/2;ty=(viewport.clientHeight-900*fit)/2;paint()};
    viewport.addEventListener('wheel',event=>{event.preventDefault();const rect=viewport.getBoundingClientRect();zoom(scale*(event.deltaY<0?1.12:1/1.12),event.clientX-rect.left,event.clientY-rect.top)},{passive:false});
    viewport.addEventListener('pointerdown',event=>{if(event.target.closest('button'))return;drag={x:event.clientX,y:event.clientY,tx,ty};moved=false;viewport.setPointerCapture(event.pointerId);viewport.classList.add('dragging')});
    viewport.addEventListener('pointermove',event=>{if(!drag)return;const dx=event.clientX-drag.x,dy=event.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>4)moved=true;tx=drag.tx+dx;ty=drag.ty+dy;paint()});
    const release=()=>{drag=null;viewport.classList.remove('dragging')};viewport.addEventListener('pointerup',release);viewport.addEventListener('pointercancel',release);
    window.addEventListener('resize',()=>{if(!viewport.isConnected)return;fit=Math.min(viewport.clientWidth/1500,viewport.clientHeight/900);scale=Math.max(fit*.82,Math.min(fit*2.6,scale));paint()},{once:true});paint();
  }
  document.addEventListener('DOMContentLoaded',()=>{
    const item=document.querySelector('[data-view="rpg"]');const label=item?.querySelector('[data-rpg-label]');
    if(item)item.addEventListener('click',()=>{if(typeof setView==='function')setView('rpg');const crumb=$('#crumb-current');if(crumb)crumb.textContent=L('pairs.rpg.049');render()});
    if(label)label.textContent=L('pairs.rpg.050');
    document.addEventListener('cpp-adventure-language-changed',()=>{if(label)label.textContent=L('pairs.rpg.051');if(!$('#view-rpg')?.classList.contains('hidden'))render()});
  });
})();
