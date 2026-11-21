(() => {
  // Labels can contain the profile name (user input): always escape before putting them in an attribute.
  const escAttr = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const ASSET = '/assets/cat-wearables.svg#';
  const SVG_ITEMS = {wizard:'wizard',crown:'crown',bow:'bow',headset:'headset',scarf:'scarf',moon:'moon-cape',backpack:'backpack',raincoat:'raincoat',yarn:'yarn',fish:'fish',shades:'shades',bowtie:'bowtie',mug:'mug',cape:'cape',wings:'wings',aura:'aura'};
  const BACK_ITEMS = ['aura','wings','cape','moon','backpack'];
  const SLOT_ORDER = ['head','ears','face','neck','body','back','aura','toy'];
  // Crop boxes (x,y,w,h) in the 1199x1312 portrait space, so each shop card shows the item on the cat.
  const ART_BOX = {head:[250,0,700,430],ears:[250,40,700,580],face:[400,230,560,260],neck:[430,520,440,260],body:[380,600,420,620],back:[40,260,1120,1000],aura:[0,0,1199,1312],toy:[740,960,400,300]};
  // Each growth stage is a different pose; this maps the adult portrait's art space onto the stage's eyes (matrix a b c d e f).
  const STAGE_ALIGN = {"kitten":[1.1402,-0.0428,0.0428,1.1402,-108.191,154.6638],"growing":[0.9646,-0.0599,0.0599,0.9646,34.4876,135.758],"young":[0.8411,-0.0293,0.0293,0.8411,128.0917,72.4992],"adult":[0.8437,-0.0141,0.0141,0.8437,157.684,80.6396],"veteran":[0.8196,-0.0178,0.0178,0.8196,198.1773,73.4579],"legend":[0.8374,-0.0051,0.0051,0.8374,203.91,35.006]};
  const alignFor = id => STAGE_ALIGN[id] ? `<g transform="matrix(${STAGE_ALIGN[id].join(' ')})">` : '<g>';
  // Face layer in the adult portrait's space: eyelids for blinking/sleeping, happy eyes, sweat drop, sleep Zs, sparkles.
  const lid = (cx,cy,rx,ry,rot,shape) => `<g transform="rotate(${rot} ${cx} ${cy})"><ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="url(#cf-fur)"/><path d="${shape==='joy'?`M${cx-rx*.72} ${cy+ry*.28}Q${cx} ${cy-ry*.62} ${cx+rx*.72} ${cy+ry*.28}`:`M${cx-rx*.8} ${cy+ry*.05}Q${cx} ${cy+ry*.72} ${cx+rx*.8} ${cy+ry*.05}`}" fill="none" stroke="#3a2418" stroke-width="10" stroke-linecap="round"/></g>`;
  const FACE_PARTS = `<defs><linearGradient id="cf-fur" x2="0" y2="1"><stop stop-color="#e98234"/><stop offset=".62" stop-color="#f2a05a"/><stop offset="1" stop-color="#f6d2b6"/></linearGradient></defs>
    <g class="cf-lid cf-lid-l">${lid(570,366,80,64,-6,'lid')}</g><g class="cf-lid cf-lid-r">${lid(788,341,64,60,-8,'lid')}</g>
    <g class="cf-joy cf-joy-l">${lid(570,366,80,64,-6,'joy')}</g><g class="cf-joy cf-joy-r">${lid(788,341,64,60,-8,'joy')}</g>
    <path class="cf-sweat" d="M935 205q-26 44-26 62a26 26 0 0 0 52 0q0-18-26-62Z" fill="#9fe6ff" stroke="#3d7fa6" stroke-width="7"/>
    <g class="cf-zzz" fill="#e8e2ff" stroke="#3b2f66" stroke-width="5" font-family="DM Sans,Arial,sans-serif" font-weight="800"><text class="cf-z1" x="900" y="210" font-size="90">z</text><text class="cf-z2" x="975" y="140" font-size="120">Z</text></g>
    <g class="cf-spark" fill="#fff3b0"><path d="M300 210l14 38 38 14-38 14-14 38-14-38-38-14 38-14z"/><path d="M1000 300l10 26 26 10-26 10-10 26-10-26-26-10 26-10z"/><path d="M960 90l8 20 20 8-20 8-8 20-8-20-20-8 20-8z"/></g>`;
  const faceLayer = stage => `<svg viewBox="0 0 1199 1312" preserveAspectRatio="none" class="cat-face" aria-hidden="true" style="--blink-delay:-${(Math.random()*5).toFixed(2)}s">${alignFor(stage)}${FACE_PARTS}</g></svg>`;
  // Only items that were not worn in the previous render get the "drop on" animation.
  let lastWorn = null;
  let shopFilter = 'all', shopSort = 'low';
  const rarityOf = cost => cost < 1000 ? 'common' : cost < 2000 ? 'rare' : cost < 3000 ? 'epic' : 'legend';
  window.shopItemArt = function(id) {
    const it = SHOP_ITEMS_UI[id]; if (!it) return '';
    const b = ART_BOX[it.slot] || [0,0,1199,1312], use = `<use href="${ASSET}${SVG_ITEMS[id]}" width="1199" height="1312"></use>`, cat = '<image href="/assets/cat-companion.png" x="0" y="0" width="1199" height="1312"></image>';
    return `<svg viewBox="${b.join(' ')}" preserveAspectRatio="xMidYMid meet" class="shop-art-svg" aria-hidden="true">${BACK_ITEMS.includes(id) ? use + cat : cat + use}</svg>`;
  };
  // Preview overrides are temporary per slot; owned/equipped state is untouched.
  let previewItems = {};

  function activeEquipment(profile) {
    const saved = profile?.equipped_items;
    if (saved && !Array.isArray(saved)) return {...saved};
    const legacy = profile?.active_item;
    const item = SHOP_ITEMS_UI?.[legacy];
    return item ? {[item.slot]:legacy} : {};
  }

  function wearLayers(equipment, stage) {
    const values = Object.values(equipment || {});
    return BACK_ITEMS.filter(id=>values.includes(id)).map(id=>`<svg viewBox="0 0 1199 1312" preserveAspectRatio="none" class="cat-wearable cat-wearable-back${lastWorn&&!lastWorn.has(id)?' just-worn':''}" data-wearable="${id}" aria-hidden="true">${alignFor(stage)}<use href="${ASSET}${SVG_ITEMS[id]}" width="1199" height="1312"></use></g></svg>`).join('');
  }

  window.renderCatCompanion = function(equipment={}, large=false, label='', level=null) {
    const catLevel=Number(level??window.appState?.profile?.level??1)||1;
    const growth=window.CatGrowth?.forLevel(catLevel);
    const ordered = ['headset','wizard','crown','bow','scarf','raincoat','bowtie','shades','yarn','fish','mug'];
    const worn = new Set(Object.values(equipment||{})), fresh = id => lastWorn && !lastWorn.has(id) ? ' just-worn' : '';
    const overlays = ordered.filter(id=>worn.has(id)).map(id=>`<svg viewBox="0 0 1199 1312" preserveAspectRatio="none" class="cat-wearable cat-wearable-front slot-${SHOP_ITEMS_UI[id].slot}${fresh(id)}" data-wearable="${id}" aria-hidden="true">${alignFor(growth?.id)}<use href="${ASSET}${SVG_ITEMS[id]}" width="1199" height="1312"></use></g></svg>`).join('');
    const stageClass=growth?`growth-${growth.id}`:'';
    const html = `<div class="cat-stage cat-layered ${large?'cat-stage-large':''} ${stageClass}" role="img" aria-label="${escAttr(label)}" data-cat-level="${catLevel}"><div class="cat-growth-model">${wearLayers(equipment,growth?.id)}<img class="cat-companion-base" src="${growth?.asset||'/assets/cat-companion.png'}" alt="">${faceLayer(growth?.id)}<span class="cat-wearable-anchor">${overlays}</span></div></div>`;
    lastWorn = worn;
    return html;
  };

  function previewEquipment(profile) {
    const equipment = activeEquipment(profile);
    for (const [slot,id] of Object.entries(previewItems)) {
      if (!SHOP_ITEMS_UI[id]) continue;
      if (id) equipment[slot]=id;
      else delete equipment[slot];
    }
    return equipment;
  }

  function renderShop() {
    if (!appState?.profile) return;
    const p=appState.profile, owned=new Set(p.owned_items||[]), equipped=activeEquipment(p), shown=previewEquipment(p);
    const currentItems=Object.values(equipped);
    const preview=Object.entries(previewItems).some(([slot,id])=>id!==equipped[slot]);
    const loadouts=p.companion_loadouts||[];
    const ui=(key)=>window.L(`ui.app.${key}`);
    const title=(it)=>window.L(`shop.${it.titleKey}`), desc=(it)=>window.L(`shop.${it.descriptionKey}`);
    const slotName=(slot)=>ui(`catSlot_${slot}`);
    const allEntries=Object.entries(SHOP_ITEMS_UI);
    const filters=['all','owned',...SLOT_ORDER.filter(sl=>allEntries.some(([,it])=>it.slot===sl))];
    if(!filters.includes(shopFilter))shopFilter='all';
    const visible=allEntries.filter(([id,it])=>shopFilter==='all'||(shopFilter==='owned'?owned.has(id):it.slot===shopFilter)).sort((a,b)=>shopSort==='high'?b[1].cost-a[1].cost:a[1].cost-b[1].cost);
    const filterLabel=f=>f==='all'?ui('shopFilterAll'):f==='owned'?ui('shopFilterOwned'):slotName(f);
    document.querySelector('#view-shop').innerHTML=`
      <span class="eyebrow">🐈 ${tr('shop')}</span><h1 class="view-title">${tr('shop')}</h1>
      <p class="view-lead">${tr('shopLead')} · <b>${p.xp} XP</b></p>
      <section class="shop-feature cat-shop-feature"><div class="shop-feature-copy"><span class="eyebrow">${ex('shopCat')} · ${ui('level')} ${p.level} · ${ui(window.CatGrowth?.forLevel(p.level).labelKey||'catStageKitten')}</span><h2>${esc(p.name)}</h2>
        <p>${preview?ui('catPreviewing'):ui('catWearingNow')}: <b>${Object.values(shown).map(id=>title(SHOP_ITEMS_UI[id])).join(' · ')||ui('defaultAppearance')}</b></p>
        <div class="shop-collection" role="img" aria-label="${ui('shopCollection')} ${owned.size}/${allEntries.length}"><span>${ui('shopCollection')}</span><b>${owned.size}/${allEntries.length}</b><i><u style="width:${Math.round(owned.size/allEntries.length*100)}%"></u></i></div><p class="cat-shop-note">${ui('catLayerNote')}</p><button class="secondary" id="cat-clear-preview">${ui('catClearPreview')}</button></div>
        ${window.renderCatCompanion(shown,true,`${ex('shopCat')} ${p.name}`)}</section>
      <section class="cat-outfit-bar panel"><div><h2>${ui('catOutfits')}</h2><p>${ui('catOutfitsHelp')}</p></div><div class="cat-outfit-save"><input id="cat-outfit-name" maxlength="32" placeholder="${ui('catOutfitName')}"><button class="primary" id="cat-save-outfit">${ui('catSaveOutfit')}</button></div></section>
      ${loadouts.length?`<div class="cat-loadout-list">${loadouts.map(o=>`<article class="cat-loadout panel"><div><b>${esc(o.name)}</b><small>${Object.values(o.equipment||{}).map(id=>SHOP_ITEMS_UI[id]?title(SHOP_ITEMS_UI[id]):'').filter(Boolean).join(' · ')||ui('defaultAppearance')}</small></div><button class="secondary" data-loadout-apply="${o.loadout_id}">${ui('catApplyOutfit')}</button><button class="quiet-button" data-loadout-delete="${o.loadout_id}" aria-label="${ui('delete')}">×</button></article>`).join('')}</div>`:''}
      <div class="shop-section-title"><div><h2>${ex('buyMore')}</h2><p>${ui('catTryBeforeBuy')}</p></div></div>
      <div class="shop-toolbar"><div class="shop-chips" role="tablist">${filters.map(f=>`<button class="shop-chip ${f===shopFilter?'active':''}" role="tab" aria-selected="${f===shopFilter}" data-shop-filter="${f}">${filterLabel(f)}</button>`).join('')}</div><label class="shop-sort"><span>${ui('shopSortLabel')}</span><select id="shop-sort"><option value="low" ${shopSort==='low'?'selected':''}>${ui('shopSortLow')}</option><option value="high" ${shopSort==='high'?'selected':''}>${ui('shopSortHigh')}</option></select></label></div>
      <div class="achievement-grid shop-grid cat-shop-grid">${visible.length?visible.map(([id,it])=>{
        const isOwned=owned.has(id), isEquipped=currentItems.includes(id), isPreview=previewItems[it.slot]===id, rar=rarityOf(it.cost), lack=it.cost-p.xp;
        return `<article class="achievement-card shop-item cat-shop-item rarity-${rar} ${isOwned?'owned':''} ${isEquipped?'equipped':''} ${isPreview?'previewing':''}" data-card-item="${id}">
          <div class="shop-art">${window.shopItemArt(id)}${isEquipped?`<span class="shop-worn-badge">${ui('shopEquippedNow')}</span>`:''}</div>
          <div class="shop-item-meta"><span class="cat-slot-chip">${slotName(it.slot)}</span><span class="rarity-chip rarity-${rar}">${ui('shopRarity_'+rar)}</span></div><h3>${title(it)}</h3><p>${desc(it)}</p>
          ${isOwned?`<p class="cat-owned-label">${ui('catOwned')}</p>`:`<p class="shop-price">${it.cost.toLocaleString()} XP${lack>0?` <small class="shop-need">${lack.toLocaleString()} ${ui('shopNeedMore')}</small>`:''}</p>`}
          <div class="cat-item-actions"><button class="secondary cat-preview-item" data-item="${id}">${isPreview?ui('catPreviewing'):ui('catTryOn')}</button>
          ${isOwned?`<button class="${isEquipped?'secondary':'primary'} cat-equip-item" data-item="${id}">${isEquipped?ui('catRemove'):tr('wear')}</button>`:`<button class="primary cat-buy-item" data-item="${id}" ${p.xp<it.cost?'disabled':''}>${tr('buy')}</button>`}</div></article>`
      }).join(''):`<p class="shop-empty panel">${ui('shopEmpty')}</p>`}</div>`;

    document.querySelectorAll('[data-shop-filter]').forEach(b=>b.onclick=()=>{shopFilter=b.dataset.shopFilter;renderShop()});
    document.querySelector('#shop-sort').onchange=e=>{shopSort=e.target.value;renderShop()};
    document.querySelector('#cat-clear-preview').onclick=()=>{previewItems={};renderShop()};
    document.querySelectorAll('.cat-preview-item').forEach(b=>b.onclick=()=>{const id=b.dataset.item,slot=SHOP_ITEMS_UI[id].slot,next={...previewItems};if(next[slot]===id)delete next[slot];else next[slot]=id;previewItems=next;renderShop()});
    document.querySelectorAll('.cat-buy-item').forEach(b=>b.onclick=async()=>{const r=await api('/api/shop/buy',{item_id:b.dataset.item});if(r.error)return toast(r.error);previewItems={};await refresh();renderShop();toast(ui('itemUnlocked'),true)});
    document.querySelectorAll('.cat-equip-item').forEach(b=>b.onclick=async()=>{const id=b.dataset.item,it=SHOP_ITEMS_UI[id];const body=currentItems.includes(id)?{item_id:'',slot:it.slot}:{item_id:id};const r=await api('/api/companion/equip',body);if(r.error)return toast(r.error);previewItems={};await refresh();renderShop()});
    document.querySelector('#cat-save-outfit').onclick=async()=>{const name=document.querySelector('#cat-outfit-name').value.trim();if(!name)return toast(ui('catNameRequired'));const r=await api('/api/companion/loadout/save',{name});if(r.error)return toast(r.error);await refresh();renderShop();toast(ui('catOutfitSaved'),true)};
    document.querySelectorAll('[data-loadout-apply]').forEach(b=>b.onclick=async()=>{const r=await api('/api/companion/loadout/apply',{loadout_id:b.dataset.loadoutApply});if(r.error)return toast(r.error);previewItems={};await refresh();renderShop();toast(ui('catOutfitApplied'),true)});
    document.querySelectorAll('[data-loadout-delete]').forEach(b=>b.onclick=async()=>{const r=await api('/api/companion/loadout/delete',{loadout_id:b.dataset.loadoutDelete});if(r.error)return toast(r.error);await refresh();renderShop()});
  }

  catStage=(item,large=false)=>window.renderCatCompanion(activeEquipment(appState?.profile),large,ex('shopCat'));
  window.renderShop=renderShop;
  document.addEventListener('cpp-adventure-language-changed',()=>{if(appState?.profile&&!document.querySelector('#view-shop')?.classList.contains('hidden'))renderShop()});
})();

