(() => {
  const $=s=>document.querySelector(s),grid=$('#iconGrid'),count=$('#iconCount'),manifest=$('#iconManifest');
  const controls={style:$('#iconStyle'),palette:$('#iconPalette'),treatment:$('#iconTreatment'),motion:$('#iconMotion'),state:$('#iconState'),size:$('#iconSize'),energy:$('#iconEnergy'),search:$('#iconSearch')};
  let filter='all';
  const navigation=new Set(['home','menu','expand','collapse','forward','back','location','link']);
  function matches(def){const term=controls.search.value.trim().toLowerCase();const hay=[def.name,def.slug,...def.keywords,...def.intents].join(' ').toLowerCase();if(term&&!hay.includes(term))return false;if(filter==='bespoke'&&!def.bespokeInternalMotion)return false;if(filter==='stateful'&&!def.states.includes('completed'))return false;if(filter==='navigation'&&!navigation.has(def.slug))return false;return true}
  function currentState(def){const state=controls.state.value;return def.states.includes(state)?state:(state==='completed'?'active':def.states[0])}
  function createCard(def){
    const card=document.createElement('article');card.className='icon-card';card.dataset.iconId=def.id;card.dataset.bespoke=String(def.bespokeInternalMotion);card.innerHTML=`<header class="icon-card-head"><div><h3>${def.name}</h3><div class="icon-card-id">${def.id}</div></div><div class="icon-card-badges"><span class="icon-card-badge">${def.bespokeInternalMotion?'bespoke':'shared'}</span><span class="icon-card-badge">${def.states.length} states</span></div></header><div class="icon-stage"></div><footer class="icon-card-actions"><button data-action="replay">Replay</button><button data-action="manifest">Manifest</button></footer>`;
    const stage=card.querySelector('.icon-stage'),icon=NexIcons.create(def,{size:Number(controls.size.value),treatment:controls.treatment.value,state:currentState(def)});stage.appendChild(icon);icon.__tl=NexIcons.animate(icon,{motion:controls.motion.value,energy:controls.energy.value});icon.__tl.seek(icon.__tl.duration());
    card.querySelector('[data-action="replay"]').onclick=()=>icon.__tl.restart();card.querySelector('[data-action="manifest"]').onclick=()=>openManifest(def);card.ondblclick=()=>{const next=icon.dataset.state==='active'?'inactive':'active';NexIcons.setState(icon,next)};return card;
  }
  function render(){NexTheme.setStyle(controls.style.value);NexTheme.applyPalette(controls.palette.value);NexTheme.setEnergy(controls.energy.value);const defs=NexIcons.registry.filter(matches);grid.replaceChildren(...defs.map(createCard));count.textContent=defs.length;if(!defs.length){const empty=document.createElement('div');empty.className='icon-empty';empty.textContent='No icons match this search.';grid.appendChild(empty)}}
  function openManifest(def){manifest.querySelector('pre').textContent=JSON.stringify(def,null,2);manifest.classList.add('open')}
  Object.values(controls).forEach(el=>el.addEventListener(el===controls.search?'input':'change',render));
  document.querySelectorAll('.icon-filter').forEach(btn=>btn.onclick=()=>{filter=btn.dataset.filter;document.querySelectorAll('.icon-filter').forEach(x=>x.classList.toggle('active',x===btn));render()});
  $('#replayAll').onclick=()=>[...grid.querySelectorAll('.nex-icon')].forEach((el,i)=>setTimeout(()=>el.__tl?.restart(),i*24));
  $('#closeIconManifest').onclick=()=>manifest.classList.remove('open');
  window.NexIconExplorer={render,get filter(){return filter}};render();
})();
