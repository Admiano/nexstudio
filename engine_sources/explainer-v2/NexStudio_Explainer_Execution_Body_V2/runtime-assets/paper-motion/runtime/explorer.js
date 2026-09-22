(() => {
  const grid=document.querySelector('#componentGrid'); const registry=NexFoundation.registry; let filter='all';
  const style=document.querySelector('#styleSelect'),energy=document.querySelector('#energySelect'),palette=document.querySelector('#paletteSelect');
  function currentEnergy(){return energy.value}
  function render(){ grid.innerHTML=''; const items=registry.filter(x=>filter==='all'||x.subtype===filter); document.querySelector('#count').textContent=String(items.length).padStart(2,'0');
    items.forEach(def=>{const card=document.createElement('article');card.className='card';card.innerHTML=`<div class="card-head"><div><h3>${def.name}</h3><div class="id">${def.id}</div></div><div class="badge">${def.subtype}</div></div><div class="mount"></div><div class="actions"><button class="replay">Replay</button><button class="inspect">Manifest</button></div>`;const comp=NexFoundation.create(def);card.querySelector('.mount').appendChild(comp);const tl=NexFoundation.animate(comp,currentEnergy());tl.seek(tl.duration());card.querySelector('.replay').onclick=()=>{tl.restart()};card.querySelector('.inspect').onclick=()=>showManifest(def);grid.appendChild(card);});
  }
  function showManifest(def){const p=document.querySelector('#manifestPanel');p.querySelector('pre').textContent=JSON.stringify({...def,cssClass:undefined},null,2);p.classList.add('open')}
  document.querySelector('#manifestClose').onclick=()=>document.querySelector('#manifestPanel').classList.remove('open');
  document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');filter=b.dataset.filter;render()});
  style.onchange=()=>NexTheme.setStyle(style.value);energy.onchange=()=>{NexTheme.setEnergy(energy.value);render()};palette.onchange=()=>NexTheme.applyPalette(palette.value);
  ['primary','secondary','accent'].forEach(k=>document.querySelector(`#${k}Color`).oninput=e=>document.documentElement.style.setProperty(`--${k}`,e.target.value));
  document.querySelector('#replayAll').onclick=()=>document.querySelectorAll('.replay').forEach((b,i)=>setTimeout(()=>b.click(),i*35));
  NexTheme.setStyle(style.value);NexTheme.applyPalette(palette.value);render();
})();
