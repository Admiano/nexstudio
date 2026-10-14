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
assert.equal(CAST_RENDER_VERSION,'approved-v3-v6-formalwardrobe-v21-upper-thigh');

const fFormal=normalizeCastSpec({...DEFAULT_SPEC.female,outfit:{kind:'formal-statement',color:'burgundy',pieces:{tieColor:'#bb4422'}}});
assert.equal(fFormal.outfit!.kind,'formal-statement');
assert.equal(fFormal.outfit!.pieces?.tieColor,'#BB4422');
assert.equal(fFormal.neck,'fine');
assert.equal(castRenderConfig(fFormal).env.CAST_NECK,'none');
assert.equal(castRenderConfig(fFormal).env.CAST_FORMAL_ID,'female-statement');
assert.equal(castRenderConfig(fFormal).env.CAST_FORMAL_SUIT_HEX,'602D3E');
assert.equal(castRenderConfig(fFormal).env.CAST_FORMAL_TIE_HEX,'BB4422');
const mFormal=normalizeCastSpec({...DEFAULT_SPEC.male,outfit:{kind:'formal-double-breasted',color:'#334455',pieces:{tieColor:'champagne'}}});
assert.equal(castRenderConfig(mFormal).env.CAST_FORMAL_ID,'male-double-breasted');
assert.equal(castRenderConfig(mFormal).env.CAST_MALE_LOOK,'O3');
assert.equal(castRenderConfig(mFormal).env.CAST_FORMAL_SUIT_HEX,'334455');
assert.equal(castRenderConfig(mFormal).env.CAST_FORMAL_TIE_HEX,'BEA479');
assert.equal(castRenderConfig({...mFormal,outfit:{...mFormal.outfit!,pieces:{tieColor:'black'}}}).env.CAST_FORMAL_SUIT_HEX,'334455');
assert.notEqual(castRenderConfig(mFormal).env.CAST_FORMAL_TIE_HEX,castRenderConfig({...mFormal,outfit:{...mFormal.outfit!,pieces:{tieColor:'black'}}}).env.CAST_FORMAL_TIE_HEX);
assert.equal(castSpecSchema.safeParse(mFormal).success,true);
assert.equal(castSpecSchema.safeParse({...mFormal,outfit:{...mFormal.outfit!,pieces:{tieColor:'not-hex'}}}).success,false);
assert.equal(castSpecSchema.safeParse({...mFormal,outfit:{...mFormal.outfit!,pieces:{tieColor:'black',bottom:'chinos'}}}).success,false);
assert.equal(normalizeCastSpec({...mFormal,outfit:{kind:'formal-bogus',color:'black'}}).outfit!.kind,'o3');
console.log('PASS formal cast wardrobe, independently persisted suit/tie colours and gender-safe catalog');

// Formal looks fail closed until deployment parity and per-look approval.
const {availableFormalWardrobe,formalSpecAvailable}=await import('../src/lib/cast-formal-availability');
const originalGate=process.env.SCENEBAM_FORMAL_WARDROBE_ENABLED;
process.env.SCENEBAM_FORMAL_WARDROBE_ENABLED='0';
assert.deepEqual(availableFormalWardrobe(),[]);
assert.equal(formalSpecAvailable(DEFAULT_SPEC.male),true);
assert.equal(formalSpecAvailable(mFormal),false);
const watchFormal=normalizeCastSpec({...DEFAULT_SPEC.male,watch:'chrono',outfit:{kind:'formal-jacket-tie',color:'navy',pieces:{tieColor:'black'}}});
assert.equal(watchFormal.watch,'chrono');
assert.equal(castRenderConfig(watchFormal).env.CAST_WATCH,'none');
if(originalGate===undefined)delete process.env.SCENEBAM_FORMAL_WARDROBE_ENABLED;else process.env.SCENEBAM_FORMAL_WARDROBE_ENABLED=originalGate;
console.log('PASS formal availability gate and accessor continuity');
