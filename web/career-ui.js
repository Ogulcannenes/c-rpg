(() => {
  const x=k=>window.CppAdventureI18n.t('career.'+k);
  function updateCareerNav(){const career=document.querySelector('[data-career-label]'),interview=document.querySelector('[data-interview-label]');if(career)career.textContent=x('navCareer');if(interview)interview.textContent=x('navInterview')}
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let interviewEditor=null,timer=null,deadline=0;
  async function json(url){return fetch(url).then(r=>r.json())}
  async function post(url,body){return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,profile_id:profileId})}).then(async r=>({status:r.status,data:await r.json()}))}
  function dispose(){if(interviewEditor){interviewEditor.dispose();interviewEditor=null}if(timer){clearInterval(timer);timer=null}}
  function setCareer(view){dispose();setView(view)}
  function downloadPortfolio(data){
    const c=data.career;
    const lines=[`# ${appState?.profile?.name||'C++ Adventure'} — ${x('portfolio')}`,`\n${x('career')}: ${c.level}`,`\n## ${x('portfolio')}`];
    for(const p of data.portfolio){lines.push(`\n### ${p.title} — ${p.completed?x('completed'):x('working')}`,`\n${p.description}`,`\n**${x('technologies')}:** ${p.technologies}`,`\n**Score:** ${p.score}%`,`\n\`\`\`cpp\n${p.code||''}\n\`\`\``)}
    const blob=new Blob([lines.join('\n')],{type:'text/markdown;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='cpp-adventure-portfolio.md';a.click();URL.revokeObjectURL(url);toast(x('exported'),true)
  }
  async function renderCareer(){
    updateCareerNav();
    const host=document.querySelector('#view-career');if(!host)return;
    dispose();host.innerHTML=`<div class="panel career-loading">${esc(x('career'))}…</div>`;
    const data=await json('/api/career?profile_id='+encodeURIComponent(profileId));if(data.error){host.textContent=data.error;return}
    const c=data.career;
    host.innerHTML=`<span class="eyebrow">✦ ${esc(x('career').toUpperCase())}</span><h1 class="view-title">${esc(x('career'))}</h1><p class="view-lead">${esc(x('careerLead'))}</p><section class="panel career-hero"><div><span class="eyebrow">${L('ui.app.careerCurrent')}</span><h2>${esc(c.level)}</h2><p>${c.tasks_completed} / ${c.total_tasks} ${esc(x('tasks'))} · ${c.projects_completed} / ${c.projects_total} ${esc(x('projects'))}</p>${c.next_level?`<small>${L('ui.app.next')}: ${esc(c.next_level)}</small>`:''}</div><div class="career-milestones">${c.career_levels.map(level=>`<article class="career-step ${level.unlocked?'unlocked':''}"><b>${esc(level.title)}</b><small>${level.tasks} ${esc(x('tasks'))} · ${level.projects} ${esc(x('projects'))}</small></article>`).join('')}</div></section><div class="career-columns"><section class="panel"><div class="section-head"><div><h2>${esc(x('interview'))}</h2><p>${esc(x('interviewLead'))}</p></div><button class="primary" id="interview-start">${esc(x('start'))}</button></div>${data.interviews.length?`<div class="interview-history">${data.interviews.map(s=>`<div class="interview-row"><span>${s.completed?`${esc(x('score'))}: ${s.score}/${s.question_count}`:`${s.answered}/${s.question_count} · ${esc(x('working'))}`}</span>${s.completed?'':`<button class="secondary" data-resume="${esc(s.session_id)}">${esc(x('resume'))}</button>`}</div>`).join('')}</div>`:`<p class="muted">${esc(x('noHistory'))}</p>`}</section><section class="panel"><h2>${esc(x('strengths'))}</h2><p>${data.strengths.length?data.strengths.map(([topic,n])=>`${esc(topic)} · ${n}`).join('  /  '):'—'}</p><h2>${esc(x('review'))}</h2><p>${data.review_topics.length?data.review_topics.map(([topic,n])=>`${esc(topic)} · ${n}`).join('  /  '):'—'}</p></section></div><section class="career-portfolio"><div class="section-head"><div><h2>${esc(x('portfolio'))}</h2><p>${L('ui.app.portfolioLead')}</p></div><button id="portfolio-export" class="secondary" ${data.portfolio.length?'':'disabled'}>${esc(x('export'))}</button></div>${data.portfolio.length?`<div class="portfolio-grid">${data.portfolio.map(p=>`<article class="panel portfolio-card"><span class="portfolio-status ${p.completed?'done':''}">${esc(p.completed?x('completed'):x('working'))} · ${p.score}%</span><h3>${esc(p.title)}</h3><label>${esc(x('description'))}<textarea class="portfolio-description" data-project="${esc(p.project_id)}" maxlength="1000">${esc(p.description)}</textarea></label><label>${esc(x('technologies'))}<input class="portfolio-tech" data-project="${esc(p.project_id)}" maxlength="200" value="${esc(p.technologies)}"></label><details><summary>${esc(x('source'))}</summary><pre>${esc(p.code)}</pre></details><button class="secondary portfolio-save" data-project="${esc(p.project_id)}">${esc(x('save'))}</button></article>`).join('')}</div>`:`<div class="panel empty-career"><p>${esc(x('empty'))}</p><button class="secondary" id="open-workshop">${esc(L('ui.app.openWorkshop'))}</button></div>`}</section>`;
    $('#interview-start',host).onclick=startInterview;
    host.querySelectorAll('[data-resume]').forEach(b=>b.onclick=()=>resumeInterview(b.dataset.resume));
    $('#portfolio-export',host)?.addEventListener('click',()=>downloadPortfolio(data));
    host.querySelectorAll('.portfolio-save').forEach(b=>b.onclick=async()=>{const id=b.dataset.project,description=host.querySelector(`.portfolio-description[data-project="${CSS.escape(id)}"]`).value,technologies=host.querySelector(`.portfolio-tech[data-project="${CSS.escape(id)}"]`).value;const r=await post('/api/portfolio/note',{project_id:id,description,technologies});toast(r.data.error||x('save'),!r.data.error)});
    $('#open-workshop',host)?.addEventListener('click',()=>{document.querySelector('[data-view="workshop"]').click()});
  }
  async function renderInterviewHome(){
    updateCareerNav();
    const host=document.querySelector('#view-interview');if(!host)return;
    dispose();const data=await json('/api/career?profile_id='+encodeURIComponent(profileId));if(data.error){host.textContent=data.error;return}
    host.innerHTML=`<section class="panel interview-home"><span class="eyebrow">▣ ${esc(x('interview').toUpperCase())}</span><h1 class="view-title">${esc(x('interview'))}</h1><p class="view-lead">${esc(x('interviewLead'))}</p><button class="primary" id="interview-start">${esc(x('start'))}</button><div class="interview-history">${data.interviews.length?data.interviews.map(s=>`<div class="interview-row"><span>${s.completed?`${esc(x('score'))}: ${s.score}/${s.question_count}`:`${s.answered}/${s.question_count} · ${esc(x('working'))}`}</span>${s.completed?'':`<button class="secondary" data-resume="${esc(s.session_id)}">${esc(x('resume'))}</button>`}</div>`).join(''):`<p class="muted">${esc(x('noHistory'))}</p>`}</div></section>`;
    $('#interview-start',host).onclick=startInterview;host.querySelectorAll('[data-resume]').forEach(b=>b.onclick=()=>resumeInterview(b.dataset.resume));
  }
  async function startInterview(){const r=await post('/api/interview/start',{});if(r.data.error){toast(r.data.error);return}await showQuestion({...r.data,remaining_seconds:900})}
  async function resumeInterview(id){const r=await json(`/api/interview?profile_id=${encodeURIComponent(profileId)}&session_id=${encodeURIComponent(id)}`);if(r.error){toast(r.error);return}await showQuestion(r)}
  async function showQuestion(session){
    setCareer('interview');
    const host=document.querySelector('#view-interview');
    window.currentInterview=session;
    if(session.completed||!session.question){host.innerHTML=`<section class="panel interview-result"><span class="eyebrow">✦ ${esc(x('result').toUpperCase())}</span><h1>${esc(x('result'))}</h1><p>${esc(x('back'))}</p><button class="primary" id="career-back">${esc(x('back'))}</button></section>`;$('#career-back',host).onclick=()=>{renderCareer();setView('career')};return}
    deadline=Date.now()+Math.max(0,session.remaining_seconds??900)*1000;
    host.innerHTML=`<section class="panel interview-panel"><header><span class="eyebrow">${esc(x('interview').toUpperCase())} · ${session.index+1}/${session.total}</span><b id="interview-clock"></b></header><div class="progress-track"><span style="width:${Math.round((session.index/session.total)*100)}%"></span></div><span class="badge-pill">${esc(session.question.topic)}</span><h1>${esc(session.question.prompt)}</h1>${session.question.kind==='choice'?`<div class="interview-options">${session.question.options.map((o,i)=>`<button class="interview-option" data-choice="${i}">${esc(o)}</button>`).join('')}</div><button id="interview-answer" class="primary" disabled>${esc(x('submit'))}</button>`:`<p class="muted">${esc(x('tests'))}: ${session.index===session.total-1?2:3} · ${esc(session.question.prompt)}</p><div id="interview-editor" class="monaco-host interview-editor"></div><button id="interview-answer" class="primary">${esc(x('submit'))}</button>`}<div id="interview-feedback"></div></section>`;
    let selected=null;
    host.querySelectorAll('[data-choice]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.choice);host.querySelectorAll('[data-choice]').forEach(q=>q.classList.toggle('selected',q===b));$('#interview-answer',host).disabled=false});
    if(session.question.kind==='code')window.MonacoReady.then(monaco=>{if(!$('#interview-editor',host))return;interviewEditor=monaco.editor.create($('#interview-editor',host),{value:session.question.starter,language:'cpp',theme:'vs-dark',automaticLayout:true,fontSize:13,fontFamily:'Consolas, monospace',minimap:{enabled:false},wordWrap:'on',tabSize:4})});
    $('#interview-answer',host).onclick=async()=>{
      const answer=session.question.kind==='choice'?selected:interviewEditor?.getValue()||session.question.starter;
      $('#interview-answer',host).disabled=true;$('#interview-answer',host).textContent=x('waiting');
      const r=await post('/api/interview/answer',{session_id:session.session_id,index:session.index,answer});
      if(r.data.error){$('#interview-feedback',host).innerHTML=`<div class="tip error">${esc(r.data.error)}</div>`;return}
      const result=r.data;const feedback=$('#interview-feedback',host);feedback.innerHTML=`<div class="tip ${result.correct?'success':'error'}">${esc(result.correct?x('correct'):x('wrong'))}<p>${esc(result.explanation||result.hint||'')}</p>${result.checks?.map(check=>`<div>${check.passed?'✓':'✕'} ${esc(check.name)} ${check.error?esc(check.error):''}</div>`).join('')||''}<b>${esc(x('score'))}: ${result.score}/${result.total}</b></div>`;
      if(result.complete){$('#interview-answer',host).remove();const button=document.createElement('button');button.className='primary';button.textContent=x('back');button.onclick=()=>{renderCareer();setView('career')};feedback.append(button);return}
      setTimeout(()=>showQuestion({session_id:session.session_id,index:result.answered,total:result.total,question:result.next_question,remaining_seconds:Math.max(0,Math.floor((deadline-Date.now())/1000))}),850);
    };
    timer=setInterval(()=>{const seconds=Math.max(0,Math.floor((deadline-Date.now())/1000)),clock=$('#interview-clock',host);if(clock)clock.textContent=`${x('time')}: ${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;if(seconds===0&&timer){clearInterval(timer);timer=null}},500);
  }
  document.addEventListener('DOMContentLoaded',()=>{
    updateCareerNav();document.addEventListener('cpp-adventure-language-changed',()=>{updateCareerNav();if(!document.querySelector('#view-career').classList.contains('hidden'))renderCareer();if(!document.querySelector('#view-interview').classList.contains('hidden'))renderInterviewHome()});
    document.querySelector('[data-view="career"]')?.addEventListener('click',()=>{if(!profileId)return;renderCareer();setView('career')});
    document.querySelector('[data-view="interview"]')?.addEventListener('click',()=>{if(!profileId)return;renderInterviewHome();setView('interview')});
  });
  window.renderCareerView=renderCareer;
})();
