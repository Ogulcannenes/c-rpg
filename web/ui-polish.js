(()=>{
  const KEY='cppAdventureNavCollapsed';
  const read=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch(_){return[]}};
  const save=v=>{try{localStorage.setItem(KEY,JSON.stringify(v))}catch(_){}};
  document.addEventListener('DOMContentLoaded',()=>{
    const groups=[...document.querySelectorAll('.nav-group')];
    const closed=new Set(read());
    groups.forEach((g,i)=>{
      const label=g.querySelector('.nav-group-label');
      if(!label)return;
      label.setAttribute('role','button');label.tabIndex=0;
      const apply=()=>{g.classList.toggle('collapsed',closed.has(i));label.setAttribute('aria-expanded',String(!closed.has(i)))};
      const toggle=()=>{closed.has(i)?closed.delete(i):closed.add(i);apply();save([...closed])};
      label.addEventListener('click',toggle);
      label.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle()}});
      apply();
    });
    const sl=document.querySelector('.side-label');
    if(sl){
      const K2='cppAdventureChaptersCollapsed';
      const set=c=>{sl.classList.toggle('collapsed',c);sl.setAttribute('aria-expanded',String(!c))};
      let c=false;try{c=localStorage.getItem(K2)==='1'}catch(_){}
      sl.setAttribute('role','button');sl.tabIndex=0;set(c);
      const t=()=>{c=!c;set(c);try{localStorage.setItem(K2,c?'1':'0')}catch(_){}};
      sl.addEventListener('click',t);
      sl.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();t()}});
    }
  });
})();
