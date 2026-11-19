(() => {
  const ASSET = '/assets/cat-wearables.svg#';
  const SVG_ITEMS = {wizard:'wizard',crown:'crown',bow:'bow',headset:'headset',scarf:'scarf',moon:'moon-cape',backpack:'backpack',raincoat:'raincoat',yarn:'yarn',fish:'fish'};
  // Preview overrides are temporary per slot; owned/equipped state is untouched.
  let previewItems = {};

  function activeEquipment(profile) {
    const saved = profile?.equipped_items;
    if (saved && !Array.isArray(saved)) return {...saved};
    const legacy = profile?.active_item;
    const item = SHOP_ITEMS_UI?.[legacy];
    return item ? {[item.slot]:legacy} : {};
  }

  function wearLayers(equipment) {
    const values = Object.values(equipment || {});
    return ['moon','backpack'].filter(id=>values.includes(id)).map(id=>`<svg viewBox="0 0 1199 1312" preserveAspectRatio="none" class="cat-wearable cat-wearable-back" data-wearable="${id}" aria-hidden="true"><use href="${ASSET}${SVG_ITEMS[id]}"></use></svg>`).join('');
  }

  window.renderCatCompanion = function(equipment={}, large=false, label='', level=null) {
    const ordered = ['headset','wizard','crown','bow','scarf','raincoat','yarn','fish'];
    const overlays = ordered.filter(id=>Object.values(equipment).includes(id)).map(id=>`<svg viewBox="0 0 1199 1312" preserveAspectRatio="none" class="cat-wearable cat-wearable-front slot-${SHOP_ITEMS_UI[id].slot}" data-wearable="${id}" aria-hidden="true"><use href="${ASSET}${SVG_ITEMS[id]}"></use></svg>`).join('');
    const catLevel=Number(level??window.appState?.profile?.level??1)||1;
    const growth=window.CatGrowth?.forLevel(catLevel);
    const stageClass=growth?`growth-${growth.id}`:'';
    return `<div class="cat-stage cat-layered ${large?'cat-stage-large':''} ${stageClass}" role="img" aria-label="${label}" data-cat-level="${catLevel}"><div class="cat-growth-model">${wearLayers(equipment)}<img class="cat-companion-base" src="${growth?.asset||'/assets/cat-companion.png'}" alt=""><span class="cat-wearable-anchor">${overlays}</span></div></div>`;
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
    document.querySelector('#view-shop').innerHTML=`
      <span class="eyebrow">🐈 ${tr('shop').toUpperCase()}</span><h1 class="view-title">${tr('shop')}</h1>
      <p class="view-lead">${tr('shopLead')} · <b>${p.xp} XP</b></p>
      <section class="shop-feature cat-shop-feature"><div class="shop-feature-copy"><span class="eyebrow">${ex('shopCat')} · ${ui('level')} ${p.level} · ${ui(window.CatGrowth?.forLevel(p.level).labelKey||'catStageKitten')}</span><h2>${esc(p.name)}</h2>
        <p>${preview?ui('catPreviewing'):ui('catWearingNow')}: <b>${Object.values(shown).map(id=>title(SHOP_ITEMS_UI[id])).join(' · ')||ui('defaultAppearance')}</b></p>
        <p class="cat-shop-note">${ui('catLayerNote')}</p><button class="secondary" id="cat-clear-preview">${ui('catClearPreview')}</button></div>
        ${window.renderCatCompanion(shown,true,`${ex('shopCat')} ${p.name}`)}</section>
      <section class="cat-outfit-bar panel"><div><h2>${ui('catOutfits')}</h2><p>${ui('catOutfitsHelp')}</p></div><div class="cat-outfit-save"><input id="cat-outfit-name" maxlength="32" placeholder="${ui('catOutfitName')}"><button class="primary" id="cat-save-outfit">${ui('catSaveOutfit')}</button></div></section>
      ${loadouts.length?`<div class="cat-loadout-list">${loadouts.map(o=>`<article class="cat-loadout panel"><div><b>${esc(o.name)}</b><small>${Object.values(o.equipment||{}).map(id=>SHOP_ITEMS_UI[id]?title(SHOP_ITEMS_UI[id]):'').filter(Boolean).join(' · ')||ui('defaultAppearance')}</small></div><button class="secondary" data-loadout-apply="${o.loadout_id}">${ui('catApplyOutfit')}</button><button class="quiet-button" data-loadout-delete="${o.loadout_id}" aria-label="${ui('delete')}">×</button></article>`).join('')}</div>`:''}
      <div class="shop-section-title"><div><h2>${ex('buyMore')}</h2><p>${ui('catTryBeforeBuy')}</p></div></div>
      <div class="achievement-grid shop-grid cat-shop-grid">${Object.entries(SHOP_ITEMS_UI).map(([id,it])=>{
        const isOwned=owned.has(id), isEquipped=currentItems.includes(id), isPreview=previewItems[it.slot]===id;
        return `<article class="achievement-card shop-item cat-shop-item ${isOwned?'owned':''} ${isEquipped?'equipped':''} ${isPreview?'previewing':''}" data-card-item="${id}">
          <span class="shop-item-icon" aria-hidden="true">${it.icon}</span><span class="cat-slot-chip">${slotName(it.slot)}</span><h3>${title(it)}</h3><p>${desc(it)}</p>
          ${isOwned?`<p class="cat-owned-label">${ui('catOwned')}</p>`:`<p class="shop-price">${it.cost.toLocaleString()} XP</p>`}
          <div class="cat-item-actions"><button class="secondary cat-preview-item" data-item="${id}">${isPreview?ui('catPreviewing'):ui('catTryOn')}</button>
          ${isOwned?`<button class="${isEquipped?'secondary':'primary'} cat-equip-item" data-item="${id}">${isEquipped?ui('catRemove'):tr('wear')}</button>`:`<button class="primary cat-buy-item" data-item="${id}" ${p.xp<it.cost?'disabled':''}>${tr('buy')}</button>`}</div></article>`
      }).join('')}</div>`;

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

