import assert from 'node:assert/strict';
import {DEFAULT_SPEC, SKINS} from '../src/studio-v2/cast/spec';
import {castRenderConfig, CAST_RENDER_VERSION} from '../src/studio-v2/cast/render-config';

const configs = new Set<string>();
for (const character of ['female','male'] as const) {
 for (const skin of SKINS) {
  const config = castRenderConfig({...DEFAULT_SPEC[character],skin:skin.key});
  assert.equal(config.env.CAST_SKIN_HEX, skin.hex.slice(1));
  assert.equal(config.renderVersion, 'approved-v3-v6-skin-v9-upper-thigh');
  configs.add(JSON.stringify(config));
  if (character === 'female') {
   assert.equal(config.env.CAST_LIP_HEX, '');
   assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:skin.key,lip:'red'}).env.CAST_LIP_HEX,'B3202A');
   assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:skin.key,lip:'#AF756B'}).env.CAST_LIP_HEX,'AF756B');
  } else assert.equal(config.env.CAST_LIP_HEX,'');
 }
}
assert.equal(configs.size, 12);
assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:'#987765'}).env.CAST_SKIN_HEX,'987765');
assert.equal(CAST_RENDER_VERSION,'approved-v3-v6-skin-v9-upper-thigh');
console.log('PASS 12 complexion configurations, distinct cache keys, default and explicit lips');
