window.NexTheme = (() => {
  const presets = {
    warm: { primary:'#6D45D8', secondary:'#FFB648', accent:'#F25F3A', ink:'#171419', paperBg:'#EFE8DC', paperSurface:'#FFFDF8', highlight:'#FFE681' },
    cobalt: { primary:'#1456D8', secondary:'#F3D12D', accent:'#F26832', ink:'#11182A', paperBg:'#F0F2F7', paperSurface:'#FFFFFF', highlight:'#FFE66D' },
    charcoal: { primary:'#C92323', secondary:'#CFC5B6', accent:'#F04D3B', ink:'#171717', paperBg:'#E8E0D4', paperSurface:'#F8F2E8', highlight:'#FFD5CF' }
  };
  const setVar=(name,value)=>document.documentElement.style.setProperty(name,value);
  function applyPalette(name){ const p=presets[name]||presets.warm; setVar('--primary',p.primary);setVar('--secondary',p.secondary);setVar('--accent',p.accent);setVar('--ink',p.ink);setVar('--paper-bg',p.paperBg);setVar('--paper-surface',p.paperSurface);setVar('--highlight',p.highlight); }
  function applyColors(values){ Object.entries(values).forEach(([k,v])=>setVar(`--${k}`,v)); }
  function setStyle(style){ document.documentElement.dataset.paperStyle=style; }
  function setEnergy(energy){ const map={low:[.8,1.25],medium:[1,1],high:[1.25,.8]};const [scale,duration]=map[energy]||map.medium;setVar('--motion-scale',scale);setVar('--motion-duration',duration); }
  return {presets,applyPalette,applyColors,setStyle,setEnergy};
})();
