(() => {
  const stages = [
    {id:'kitten',min:1,max:1,asset:'/assets/cat-growth-kitten.png',labelKey:'catStageKitten',size:58},
    {id:'growing',min:2,max:5,asset:'/assets/cat-growth-growing.png',labelKey:'catStageGrowing',size:66},
    {id:'young',min:6,max:10,asset:'/assets/cat-growth-young.png',labelKey:'catStageYoung',size:75},
    {id:'adult',min:11,max:15,asset:'/assets/cat-growth-adult.png',labelKey:'catStageAdult',size:84},
    {id:'veteran',min:16,max:20,asset:'/assets/cat-growth-veteran.png',labelKey:'catStageVeteran',size:92},
    {id:'legend',min:21,max:Infinity,asset:'/assets/cat-growth-legend.png',labelKey:'catStageLegend',size:100}
  ];
  const forLevel = level => stages.find(s => Number(level||1) >= s.min && Number(level||1) <= s.max) || stages[0];
  window.CatGrowth = {stages, forLevel};
  window.catGrowthAssetForLevel = level => forLevel(level).asset;
  let last = null;

  function showLevelUp(detail) {
    const profileId=String(detail.profileId||'');
    const level=Number(detail.level||1);
    const stage=forLevel(level);
    if (!profileId || !window.appState?.profile) return;
    document.querySelector('.cat-levelup-overlay')?.remove();
    const ui=(key)=>window.L(`ui.app.${key}`);
    const overlay=document.createElement('section');
    overlay.className=`cat-levelup-overlay growth-${stage.id}`;
    overlay.setAttribute('role','status');
    overlay.setAttribute('aria-live','polite');
    overlay.innerHTML=`<div class="cat-levelup-card"><button type="button" class="cat-levelup-close" aria-label="${ui('catGrowthClose')}">×</button><span class="eyebrow">${ui('catGrowthTitle')}</span><h2 data-level="${level}">${ui('catGrowthLevel').replace('{level}',level)}</h2><p>${ui(stage.labelKey)}</p>${window.renderCatCompanion(window.appState.profile.equipped_items||{},false,ui(stage.labelKey),level)}</div>`;
    document.body.append(overlay);
    let timer;
    const close=()=>{clearTimeout(timer);overlay.classList.add('leaving');setTimeout(()=>overlay.remove(),180)};
    overlay.querySelector('.cat-levelup-close').onclick=close;
    overlay.addEventListener('click',e=>{if(e.target===overlay)close()});
    timer=setTimeout(()=>{if(overlay.isConnected)close()},4400);
  }

  document.addEventListener('cpp-adventure-level-up',e=>showLevelUp(e.detail||{}));
  document.addEventListener('cpp-adventure-language-changed',()=>{
    const overlay=document.querySelector('.cat-levelup-overlay');
    if(!overlay)return;
    const level=Number(overlay.querySelector('h2')?.dataset.level||window.appState?.profile?.level||1);
    const stage=forLevel(level);
    overlay.remove();
    showLevelUp({profileId:window.appState?.profile?.profile_id,level});
  });
})();
