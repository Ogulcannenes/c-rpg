(() => {
  const copy = () => window.CppAdventureI18n.module('workshop',lang);
  const escapeHtml = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let templates=[], originalRender, editor, workspaces=[], active=null, activeFile='main.cpp', files={}, cmakeAvailable=false;
  const apiPost = async (path, body={}) => fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,profile_id:profileId})}).then(r=>r.json());
  const apiGet = async () => fetch('/api/projects?profile_id='+encodeURIComponent(profileId)).then(r=>r.json());
  const allTemplates=()=>[{id:'',name:{tr:'Mesaj modülü',ru:'Модуль сообщения'},files:['main.cpp','include/message.hpp','src/message.cpp']},...templates];
  function captureEditor(){if(editor&&activeFile)files[activeFile]=editor.getValue()}
  function dispose(){if(editor){editor.dispose();editor=null}}
  async function persistCurrent(root){
    if(!active)return;
    captureEditor();
    const result=await apiPost('/api/workspace/save',{workspace_id:active.workspace_id,name:root?.querySelector('#ws-name')?.value||active.name,files});
    if(!result.error)active.files={...files};
    return result;
  }
  function paintResult(result){
    const panel=document.querySelector('#workspace-output'); if(!panel)return;
    const c=copy();
    panel.innerHTML=`<div class="console-result ${result.ok?'run-success':'run-error'}"><b>${escapeHtml(({complete:lang==='ru'?'Готово':'Tamamlandı',compile:lang==='ru'?'Ошибка компиляции':'Derleme hatası',runtime:lang==='ru'?'Ошибка выполнения':'Çalışma hatası',timeout:lang==='ru'?'Превышено время':'Zaman aşımı',configure:lang==='ru'?'Ошибка настройки CMake':'CMake yapılandırma hatası',build:lang==='ru'?'Ошибка сборки':'Derleme hatası'})[result.phase]||result.phase||'')}</b><span>${escapeHtml(result.error||'')}</span>${result.compile_output?`<pre>${escapeHtml(result.compile_output)}</pre>`:''}<div><small>stdout</small><pre>${escapeHtml(result.stdout||'')}</pre></div>${result.stderr?`<div><small>stderr</small><pre>${escapeHtml(result.stderr)}</pre></div>`:''}${result.exit_code!==undefined&&result.exit_code!==null?`<small>Exit ${result.exit_code} · ${result.elapsed_ms||0} ms</small>`:''}</div>`;
  }
  async function renderBuilder(){
    const host=document.querySelector('#view-workshop'); if(!host||host.classList.contains('hidden'))return;
    const c=copy(), data=await apiGet(); if(data.error)return;
    workspaces=data.workspaces||[]; cmakeAvailable=!!data.cmake_available; templates=data.templates||[];
    if(active&&!workspaces.some(w=>w.workspace_id===active.workspace_id))active=null;
    if(!active&&workspaces.length)active=workspaces[0];
    const root=document.createElement('section'); root.className='panel multi-workspace'; root.innerHTML=`<div class="section-head"><div><span class="eyebrow">⚒ ${escapeHtml(c.title)}</span><h2>${escapeHtml(c.title)}</h2><p class="view-lead">${escapeHtml(c.lead)}</p></div><button class="primary" id="ws-create">＋ ${escapeHtml(c.create)}</button></div><div id="ws-create-box" class="workspace-create hidden"><label>${escapeHtml(c.name)}<input id="ws-new-name" maxlength="80" value="${escapeHtml(c.newProjectName)}"></label><label>${escapeHtml(lang==='ru'?'Шаблон':'Şablon')}<select id="ws-template">${allTemplates().map(t=>`<option value="${escapeHtml(t.id)}">${escapeHtml(t.name[lang]||t.name.tr)}</option>`).join('')}</select></label><button class="primary" id="ws-create-confirm">${escapeHtml(c.create)}</button><button class="secondary" id="ws-create-cancel">${escapeHtml(c.cancel)}</button></div><div id="ws-delete-box" class="workspace-create hidden"><span>${escapeHtml(c.confirmDelete)}</span><button class="secondary" id="ws-delete-confirm">${escapeHtml(c.delete)}</button><button class="secondary" id="ws-delete-cancel">${escapeHtml(c.cancel)}</button></div><p class="tip">${escapeHtml(c.safe)}</p><div class="workspace-grid"><aside class="workspace-files"><label ${workspaces.length?'':'hidden'}>${escapeHtml(c.select)}<select id="ws-select">${workspaces.map(w=>`<option value="${escapeHtml(w.workspace_id)}" ${active?.workspace_id===w.workspace_id?'selected':''}>${escapeHtml(w.name)}</option>`).join('')}</select></label>${active?`<div class="file-list"><b>${escapeHtml(c.files)}</b>${Object.keys(active.files).map(path=>`<button class="workspace-file ${path===activeFile?'selected':''}" data-path="${escapeHtml(path)}">${/\.(h|hpp|hh)$/.test(path)?'📘':/\.txt$/.test(path)?'📝':'📄'} ${escapeHtml(path)}</button>`).join('')}</div><label>${escapeHtml(c.fileName)}<input id="ws-file-path" placeholder="src/helper.cpp"></label><button class="secondary" id="ws-add-file">＋ ${escapeHtml(c.add)}</button><button class="secondary" id="ws-remove-file">${escapeHtml(c.remove)}</button><label>${escapeHtml(c.name)}<input id="ws-name" maxlength="80" value="${escapeHtml(active.name)}"></label><button class="secondary" id="ws-save">💾 ${escapeHtml(c.save)}</button><button class="secondary" id="ws-delete">${escapeHtml(c.delete)}</button>`:`<p>${escapeHtml(c.noProject)}</p>`}</aside><div class="workspace-main">${!active?`<div class="ws-templates"><p>${escapeHtml(lang==='ru'?'Начни с готового шаблона: файлы откроются в редакторе, и проект можно сразу собрать.':'Hazır bir şablonla başla: dosyalar düzenleyicide açılır ve proje hemen derlenebilir.')}</p><div class="ws-template-grid">${allTemplates().map(t=>`<button type="button" class="ws-template-card" data-template="${escapeHtml(t.id)}"><b>${escapeHtml(t.name[lang]||t.name.tr)}</b><small>${t.files.map(escapeHtml).join(' · ')}</small></button>`).join('')}</div></div>`:''}${active?`<div class="editor-top"><span>📄 ${escapeHtml(activeFile)}</span><small>Monaco · C++</small></div><div id="workspace-monaco" class="monaco-host workspace-editor"></div><label class="project-input-label"><span>⌨ ${escapeHtml(c.input)}</span><textarea id="ws-input" rows="2" maxlength="2000"></textarea></label><div class="editor-actions"><button class="secondary" id="ws-build">${escapeHtml(c.build)}</button><button class="primary" id="ws-cmake" ${cmakeAvailable?'':'disabled'}>${escapeHtml(c.cmake)}</button></div>${cmakeAvailable?'':`<small>${escapeHtml(c.cmakeMissing)}</small>`}<div id="workspace-output" class="console">${escapeHtml(c.ready)}</div>`:''}</div></div>`;
    host.append(root);
    root.querySelectorAll('.ws-template-card').forEach(card=>card.onclick=async()=>{const t=allTemplates().find(x=>x.id===card.dataset.template);const result=await apiPost('/api/workspace/create',{name:t.name[lang]||t.name.tr,template:t.id});if(result.error)return toast(result.error);active=result.workspace;activeFile=Object.keys(active.files)[0];files={...active.files};toast(copy().created,true);await refreshBuilder()});
    if(!active)return;
    $('#ws-select',root).onchange=async()=>{const result=await persistCurrent(root);if(result?.error)return toast(result.error);const selected=workspaces.find(w=>w.workspace_id===$('#ws-select',root).value);if(selected){active=selected;activeFile=Object.keys(active.files)[0]||'main.cpp';files={...active.files};dispose();root.remove();renderBuilder()}};
    root.querySelectorAll('.workspace-file').forEach(button=>button.onclick=()=>{captureEditor();active.files={...active.files,...files};activeFile=button.dataset.path;files={...active.files};dispose();root.remove();renderBuilder()});
    $('#ws-create',root).onclick=()=>$('#ws-create-box',root).classList.remove('hidden');
    $('#ws-create-cancel',root).onclick=()=>$('#ws-create-box',root).classList.add('hidden');
    $('#ws-create-confirm',root).onclick=async()=>{const name=$('#ws-new-name',root).value.trim();if(!name)return;const saved=await persistCurrent(root);if(saved?.error)return toast(saved.error);const result=await apiPost('/api/workspace/create',{name,template:$('#ws-template',root)?.value||''});if(result.error)return toast(result.error);active=result.workspace;activeFile=Object.keys(active.files)[0];files={...active.files};toast(c.created,true);await refreshBuilder()};
    $('#ws-add-file',root).onclick=()=>{const path=$('#ws-file-path',root).value.trim();if(!path)return;captureEditor();if(files[path])return toast(c.fileExists);files[path]='';active.files={...files};activeFile=path;dispose();root.remove();renderBuilder()};
    $('#ws-remove-file',root).onclick=()=>{if(Object.keys(files).length<2)return toast(c.keepOneFile);captureEditor();delete files[activeFile];active.files={...files};activeFile=Object.keys(files)[0];dispose();root.remove();renderBuilder()};
    $('#ws-save',root).onclick=async()=>{const result=await persistCurrent(root);if(result?.error)return toast(result.error);active.name=$('#ws-name',root).value;toast(c.saved,true)};
    $('#ws-delete',root).onclick=()=>$('#ws-delete-box',root).classList.remove('hidden');
    $('#ws-delete-cancel',root).onclick=()=>$('#ws-delete-box',root).classList.add('hidden');
    $('#ws-delete-confirm',root).onclick=async()=>{await apiPost('/api/workspace/delete',{workspace_id:active.workspace_id});active=null;files={};dispose();toast(c.deleted,true);await refreshBuilder()};
    const build=async mode=>{captureEditor();const output=$('#workspace-output',root);output.textContent=c.running;const result=await apiPost('/api/workspace/build',{workspace_id:active.workspace_id,files,mode,input:$('#ws-input',root).value});paintResult(result)};
    $('#ws-build',root).onclick=()=>build('g++'); $('#ws-cmake',root).onclick=()=>build('cmake');
    files={...active.files};if(!Object.prototype.hasOwnProperty.call(files,activeFile))activeFile=Object.keys(files)[0];
    window.MonacoReady.then(monaco=>{if(!root.isConnected)return;editor=monaco.editor.create($('#workspace-monaco',root),{value:files[activeFile]||'',language:activeFile.endsWith('.cpp')||/\.(cc|cxx|h|hpp|hh)$/.test(activeFile)?'cpp':'plaintext',theme:'vs-dark',automaticLayout:true,fontSize:13,fontFamily:'Consolas, monospace',minimap:{enabled:false},scrollBeyondLastLine:false,wordWrap:'on',tabSize:4,wordBasedSuggestions:'off',suggest:{showWords:false}});editor.onDidChangeModelContent(()=>{files[activeFile]=editor.getValue()})});
  }
  async function refreshBuilder(){const root=document.querySelector('.multi-workspace');root?.remove();await renderBuilder()}
  document.addEventListener('DOMContentLoaded',()=>{
    originalRender=window.renderWorkshop;
    if(typeof originalRender==='function')window.renderWorkshop=async(...args)=>{dispose();await originalRender(...args);await renderBuilder()};
  });
  document.addEventListener('cpp-adventure-language-changed',()=>{if(!document.querySelector('#view-workshop').classList.contains('hidden')){dispose();document.querySelector('.multi-workspace')?.remove();renderBuilder()}});
  window.addEventListener('beforeunload',captureEditor);
})();
