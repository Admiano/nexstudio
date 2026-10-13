import assert from 'node:assert/strict';
import {DEFAULT_SPEC,normalizeCastSpec,CAST_SOURCE_VERSION} from '../src/studio-v2/cast/spec';
import {castRenderConfig,CAST_RENDER_VERSION} from '../src/studio-v2/cast/render-config';
const f=normalizeCastSpec({...DEFAULT_SPEC.female,outfit:{kind:'maxi'}});
assert.equal(f.outfit?.color,'burgundy');assert.equal(castRenderConfig(f).env.CAST_DRESS,'mindfront_f_dress_09');
assert.equal(normalizeCastSpec({...f,neck:'none'}).neck,null);
assert.equal(normalizeCastSpec({...DEFAULT_SPEC.male,watch:'none'}).watch,null);
const shortSleeve=normalizeCastSpec({...DEFAULT_SPEC.male,watch:'chrono',outfit:{kind:'o2'}});
assert.equal(shortSleeve.watch,'chrono');assert.equal(castRenderConfig(shortSleeve).env.CAST_WATCH,'chrono');
const m=normalizeCastSpec({...DEFAULT_SPEC.male,skin:'ab8765',outfit:{kind:'o3',color:'28665c',pieces:{bottom:'classic-jeans',shoes:'classic-sneakers',bottomColor:'#3a304a',shoesColor:'473624'}}});
assert.equal(m.skin,'#AB8765');assert.equal(m.sourceVersion,CAST_SOURCE_VERSION);
assert.equal(m.watch,null);assert.equal(castRenderConfig(m).env.CAST_WATCH,'none');
assert.equal(castRenderConfig(m).env.CAST_GARMENTS,'elvs_male_shirt_untucked_bd1=28665C,punkduck_male_classic_jeans=3A304A,culturalibre_sneakers=473624');
assert.deepEqual(castRenderConfig(m),castRenderConfig({...m,voiceId:'andrew'}));
assert.equal(castRenderConfig(DEFAULT_SPEC.female).env.CAST_SKIN_HEX,'F1D7C8');
assert.equal(castRenderConfig({...DEFAULT_SPEC.male,skin:'light'}).env.CAST_SKIN_HEX,'F1D7C8');
assert.equal(castRenderConfig({...f,lip:'coral'}).env.CAST_LIP_HEX,'E0664F');
console.log('PASS source mapping, custom colours, independent pieces, None, voice and legacy defaults');

const environmentSpec=normalizeCastSpec({...DEFAULT_SPEC.male,environment:'cafe',environmentFormat:'portrait'});
assert.equal(environmentSpec.environment,'cafe');assert.equal(environmentSpec.environmentFormat,'portrait');
assert.deepEqual(castRenderConfig(environmentSpec),castRenderConfig(DEFAULT_SPEC.male));
assert.equal(normalizeCastSpec({...DEFAULT_SPEC.female,environment:'missing' as never}).environment,null);
const {castSpecSchema}=await import('../src/lib/cast-spec-schema');
assert.equal(castSpecSchema.parse(environmentSpec).environment,'cafe');
assert.equal(castSpecSchema.safeParse({...environmentSpec,environment:'../../private'}).success,false);
console.log('PASS environment persistence, validation and character-cache reuse');


// Every selected complexion is explicit, including the default light skin.
const {SKINS}=await import('../src/studio-v2/cast/spec');
for(const character of ['female','male'] as const) for(const skin of SKINS){
 const c=castRenderConfig({...DEFAULT_SPEC[character],skin:skin.key});
 assert.equal(c.env.CAST_SKIN_HEX,skin.hex.slice(1).toUpperCase());
}

// Soft rose uses the per-complexion makeup palette; explicit choices remain literal.
for(const skin of SKINS){
 assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:skin.key,lip:'rose'}).env.CAST_LIP_HEX,'');
 assert.equal(castRenderConfig({...DEFAULT_SPEC.female,skin:skin.key,lip:'red'}).env.CAST_LIP_HEX,'B3202A');
}
assert.equal(CAST_RENDER_VERSION,'approved-v3-v6-corrected-original-performance-v20-formal-v1');

const femaleFormal=normalizeCastSpec({...DEFAULT_SPEC.female,outfit:{kind:'formal-statement',color:'#BA4088',tieColor:'#EEEFFF'}});
assert.equal(femaleFormal.outfit?.kind,'formal-statement');
assert.equal(femaleFormal.outfit?.color,'#BA4088');
assert.equal(femaleFormal.outfit?.tieColor,'#EEEFFF');
const femaleConfig=castRenderConfig(femaleFormal);
assert.equal(femaleConfig.env.CAST_FORMAL_LOOK,'female-statement');
assert.equal(femaleConfig.env.CAST_SUIT_HEX,'BA4088');
assert.equal(femaleConfig.env.CAST_TIE_HEX,'EEEFFF');
assert.equal(femaleConfig.env.CAST_DRESS,'mindfront_f_dress_11');
const maleFormal=normalizeCastSpec({...DEFAULT_SPEC.male,outfit:{kind:'formal-dinner-jacket',color:'cream',tieColor:'black'}});
const maleConfig=castRenderConfig(maleFormal);
assert.equal(maleConfig.env.CAST_FORMAL_LOOK,'male-dinner-jacket');
assert.equal(maleConfig.env.CAST_MALE_LOOK,'O3');
assert.equal(maleConfig.env.CAST_SUIT_HEX,'DED5C4');
assert.equal(maleConfig.env.CAST_TIE_HEX,'17191F');
assert.equal(maleFormal.watch,null);
assert.ok(castSpecSchema.safeParse(maleFormal).success);
assert.ok(!castSpecSchema.safeParse({...maleFormal,outfit:{kind:'o1',tieColor:'red'}}).success);
assert.ok(!castSpecSchema.safeParse({...maleFormal,outfit:{kind:'formal-malicious',tieColor:'black'}}).success);
assert.equal(normalizeCastSpec({...maleFormal,outfit:{kind:'o3'}}).outfit?.tieColor,undefined);
assert.notEqual(castRenderConfig(maleFormal).env.CAST_SUIT_HEX,castRenderConfig({...maleFormal,outfit:{kind:'formal-dinner-jacket',color:'navy',tieColor:'black'}}).env.CAST_SUIT_HEX);
console.log('PASS SceneBam formal looks, independent suit/tie palettes, validation and backwards compatibility');
