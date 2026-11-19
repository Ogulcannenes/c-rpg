const st=(key)=>window.CppAdventureI18n.t('stats.'+key);

async function renderStats(){
  const host=document.querySelector('#view-stats');
  host.innerHTML=`<div class="journal-loading">${st('loading')}</div>`;
  const data=await fetch(`/api/stats?profile_id=${encodeURIComponent(profileId)}`).then(r=>r.json()).catch(()=>({error:tr('unavailable')}));
  if(data.error){host.innerHTML=`<div class="tip error">${esc(data.error)}</div>`;return}
  const minutes=Math.floor(data.study_seconds_30d/60),seconds=data.study_seconds_30d%60,accuracy=data.attempts?Math.round(data.correct/data.attempts*100):0;
  const maxDaily=Math.max(60,...data.daily.map(x=>x.seconds||0));
  const daily=data.daily.map(day=>`<div class="stats-day" title="${esc(day.day)} · ${Math.floor(day.seconds/60)} ${st('min')}"><i style="height:${Math.max(4,Math.round((day.seconds||0)/maxDaily*100))}%"></i><small>${esc(day.day.slice(5))}</small></div>`).join('');
  const topics=data.topics.filter(x=>x.attempts).map(item=>`<button class="stats-topic" data-topic="${esc(item.chapter_id)}"><span><b>${esc(tx(item.title))}</b><small>${item.correct}/${item.attempts} ${st('attempts')}</small></span><i><em style="width:${Math.round(item.accuracy*100)}%"></em></i><strong>${Math.round(item.accuracy*100)}%</strong></button>`).join('');
  const errors=data.errors.map(item=>`<div class="stats-error"><span>${esc(item.error_kind.replaceAll('_',' '))}</span><b>${item.count}</b></div>`).join('');
  host.innerHTML=`<span class="eyebrow">▥ ${st('nav').toUpperCase()}</span><h1 class="view-title">${st('title')}</h1><p class="view-lead">${st('lead')}</p><div class="stats-grid stats-grid-wide"><article class="stat-card"><div class="stat-head">${st('xp')}</div><div class="stat-number">${data.xp}</div></article><article class="stat-card"><div class="stat-head">${st('completed')}</div><div class="stat-number">${data.completed_tasks}<span class="stats-total"> / ${data.total_tasks}</span></div></article><article class="stat-card"><div class="stat-head">${st('time')}</div><div class="stat-number">${minutes}<span class="stats-unit">${st('min')}</span> ${seconds}<span class="stats-unit">${st('sec')}</span></div></article><article class="stat-card"><div class="stat-head">${st('accuracy')}</div><div class="stat-number">${accuracy}%</div></article><article class="stat-card"><div class="stat-head">${st('streak')}</div><div class="stat-number">${data.streak}</div></article><article class="stat-card"><div class="stat-head">${st('projects')} · ${st('badges')}</div><div class="stat-number">${data.projects} · ${data.achievements}</div></article></div><p class="stats-note">${st('timeNote')}</p><div class="stats-layout"><section class="panel"><h2>${st('daily')}</h2><div class="stats-days">${daily||`<p class="journal-note">${st('none')}</p>`}</div></section><section class="panel"><h2>${st('errors')}</h2><div class="stats-errors">${errors||`<p class="journal-note">${st('none')}</p>`}</div></section></div><section class="panel stats-topic-panel"><h2>${st('topics')}</h2><div class="stats-topic-list">${topics||`<p class="journal-note">${st('none')}</p>`}</div><button class="secondary" id="stats-map">${st('map')} →</button></section>`;
  host.querySelectorAll('.stats-topic').forEach(button=>button.onclick=()=>{const chapter=appState.curriculum.findIndex(x=>x.id===button.dataset.topic);if(chapter>=0)openChapter(chapter)});
  host.querySelector('#stats-map').onclick=()=>{renderMap();setView('map')};
}

const renderMapCore=renderMap;
renderMap=function(){
  renderMapCore();
  fetch(`/api/journal?profile_id=${encodeURIComponent(profileId)}`).then(r=>r.json()).then(data=>{
    if(data.error)return;
    const byId=new Map(data.topics.map(x=>[x.id,x]));
    document.querySelectorAll('#view-map .map-card').forEach(card=>{
      const chapter=appState.curriculum[Number(card.dataset.chapter)],topic=byId.get(chapter?.id);if(!topic)return;
      const level=topic.attempts>=3&&topic.accuracy>=.85?'mastered':topic.attempts>=2&&topic.accuracy<.6?'review':topic.attempts?'learning':'unseen';
      card.dataset.mastery=level;
      const status=card.querySelector('.knowledge-node-status');
      if(status&&!card.classList.contains('locked'))status.insertAdjacentHTML('afterend',`<span class="map-mastery">${st(level)}</span>`);
    });
    const lead=document.querySelector('#view-map .view-lead');
    if(lead&&!document.querySelector('#map-mastery-legend'))lead.insertAdjacentHTML('afterend',`<div id="map-mastery-legend" class="map-legend"><span class="mastered">● ${st('mastered')}</span><span class="review">● ${st('review')}</span><span class="learning">● ${st('learning')}</span><span class="unseen">● ${st('unseen')}</span></div>`);
  }).catch(()=>{});
};

document.addEventListener('click',event=>{
  const nav=event.target.closest('.nav-item[data-view="stats"]');
  if(nav){setView('stats');renderStats();}
});
document.addEventListener('cpp-adventure-language-changed',()=>{if(!document.querySelector('#view-stats').classList.contains('hidden'))renderStats();if(!document.querySelector('#view-map').classList.contains('hidden'))renderMap()});
