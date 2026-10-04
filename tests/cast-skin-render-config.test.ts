import assert from 'node:assert/strict';
import {DEFAULT_SPEC, SKINS, LIPS} from '../src/studio-v2/cast/spec';
import {castRenderConfig, CAST_RENDER_VERSION} from '../src/studio-v2/cast/render-config';

const configs = new Set<string>();
for (const character of ['female','male'] as const) {
 for (const skin of SKINS) {
  const config = castRenderConfig({...DEFAULT_SPEC[character],skin:skin.key});
  assert.equal(config.env.CAST_SKIN_HEX, skin.hex.slice(1));
  assert.equal(config.renderVersion, 'approved-v3-v6-corrected-original-performance-v20-upper-thigh');
  configs.add(JSON.stringify(config));
  if (character === 'female') {
   assert.equal(config.env.CAST_LIP_HEX, '');
   for (const lip of LIPS) assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:skin.key,lip:lip.key}).env.CAST_LIP_HEX,lip.key==='rose'?'':lip.hex.slice(1));
   assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:skin.key,lip:'#AF756B'}).env.CAST_LIP_HEX,'AF756B');
  } else assert.equal(config.env.CAST_LIP_HEX,'');
 }
}
assert.equal(configs.size, 12);
assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:'#987765'}).env.CAST_SKIN_HEX,'987765');
assert.equal(CAST_RENDER_VERSION,'approved-v3-v6-corrected-original-performance-v20-upper-thigh');
console.log('PASS 12 complexion configurations, distinct cache keys, 30 preset skin/lip combinations and custom colours');
