(function(root){'use strict';
function item(id,category,families,bind,silhouette,layer,style,roles,ages,neutral=true,clear={},expand={}){return {id,category,compatibleBodyFamilies:families,anchorBindRegions:bind,silhouetteRules:silhouette,layerPriority:layer,occlusionRules:{body:'cover-bound-region',sameCategory:'higher-layer-wins',hands:'never-cover-wrist-or-hand',feet:category==='footwear'?'shoe-covers-foot-shell':'preserve-footwear'},motionSafeExpansion:{torso:.018,arm:.012,leg:.014,foot:.008,head:.01,highMotion:.012,...expand},minimumClearances:{torso:.012,arm:.008,leg:.009,foot:.006,head:.01,...clear},styleTags:style,roleTags:roles,ageCompatibility:ages,genderNeutralCompatible:neutral};}
const A=['adult_man','adult_woman','diminutive_adult','elder_adult','plus_size_adult'], C=['boy','girl','diminutive_child'], ALL=['*'];
const items=[
 item('upper_tshirt','upper',ALL,['chest','pelvis','shoulder_l/r','upperarm_l/r'],{form:'tee',sleeve:'short',hem:'straight'},20,['casual','clean'],['general','student','creator'],['child','adult','elder']),
 item('upper_shirt','upper',A,['chest','pelvis','shoulder_l/r','arms'],{form:'shirt',sleeve:'long',collar:'point'},21,['smart','business'],['office','manager','sales'],['adult','elder'],false),
 item('upper_blouse','upper',['adult_woman','girl','diminutive_adult','diminutive_child','elder_adult','plus_size_adult'],['chest','pelvis','shoulder_l/r','arms'],{form:'blouse',sleeve:'long',collar:'soft'},21,['smart','soft-tailored'],['office','education','general'],['child','adult','elder'],false),
 item('upper_workshirt','upper',ALL,['chest','pelvis','shoulder_l/r','arms'],{form:'workshirt',sleeve:'long',collar:'utility'},21,['workwear','utility'],['technician','field','maker'],['child','adult','elder']),
 item('lower_trousers','lower',ALL,['pelvis','hips','knees','ankles'],{form:'trousers',cut:'straight'},15,['clean','smart'],['general','office'],['child','adult','elder']),
 item('lower_jeans','lower',ALL,['pelvis','hips','knees','ankles'],{form:'trousers',cut:'jeans'},15,['casual','denim'],['general','creator'],['child','adult','elder']),
 item('lower_worktrousers','lower',ALL,['pelvis','hips','knees','ankles'],{form:'trousers',cut:'utility'},15,['workwear','utility'],['technician','field','maker'],['child','adult','elder']),
 item('lower_shorts','lower',C,['pelvis','hips','knees'],{form:'trousers',cut:'shorts'},15,['casual','school'],['student','general'],['child']),
 item('lower_skirt','lower',['adult_woman','girl','diminutive_adult','diminutive_child','elder_adult','plus_size_adult'],['pelvis','hips','knees'],{form:'skirt',length:'midi',split:'adaptive'},16,['smart','clean'],['office','education','general'],['child','adult','elder'],false,{leg:.014},{leg:.035,highMotion:.03}),
 item('full_dress','full_body',['adult_woman','girl','diminutive_adult','diminutive_child','elder_adult','plus_size_adult'],['chest','pelvis','shoulders','arms','knees'],{form:'dress',sleeve:'short',length:'midi',split:'adaptive'},22,['clean','commercial'],['general','education','office'],['child','adult','elder'],false,{leg:.015},{leg:.04,highMotion:.035}),
 item('outer_hoodie','outerwear',ALL,['chest','pelvis','shoulders','arms'],{form:'hoodie',sleeve:'long',hood:true},30,['casual','soft'],['student','creator','general'],['child','adult','elder']),
 item('outer_blazer','outerwear',A,['chest','pelvis','shoulders','arms'],{form:'blazer',sleeve:'long',lapel:true},31,['business','tailored'],['executive','office','sales'],['adult','elder'],false),
 item('outer_workjacket','outerwear',ALL,['chest','pelvis','shoulders','arms'],{form:'workjacket',sleeve:'long'},31,['workwear','utility'],['technician','field','maker'],['child','adult','elder']),
 item('foot_sneakers','footwear',ALL,['ankle_l/r','toe_l/r'],{form:'shoe',sole:'sneaker'},40,['casual','sport'],['general','student'],['child','adult','elder']),
 item('foot_shoes','footwear',ALL,['ankle_l/r','toe_l/r'],{form:'shoe',sole:'flat'},40,['smart','business'],['office','general'],['child','adult','elder']),
 item('head_cap','optional_headwear',ALL,['head'],{style:'cap'},50,['casual','workwear'],['field','student','general'],['child','adult','elder']),
 item('accessory_badge','optional_accessory',ALL,['chest'],{style:'badge'},55,['utility','identity'],['staff','workwear'],['child','adult','elder'])
];
function p(id,label,families,slots,tags){return {id,label,compatibleBodyFamilies:families,items:{upper:null,lower:null,full_body:null,outerwear:null,footwear:null,optional_headwear:null,optional_accessory:null,...slots},styleTags:tags}}
const presets=[
 p('man_tshirt_trousers','T-shirt + trousers',['adult_man','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_tshirt',lower:'lower_trousers',footwear:'foot_sneakers'},['men','casual']),
 p('man_shirt_trousers','Shirt + trousers',['adult_man','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_shirt',lower:'lower_trousers',footwear:'foot_shoes'},['men','smart']),
 p('man_hoodie_jeans','Hoodie + jeans',['adult_man','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_tshirt',lower:'lower_jeans',outerwear:'outer_hoodie',footwear:'foot_sneakers'},['men','casual']),
 p('man_business_casual','Business casual',['adult_man','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_shirt',lower:'lower_trousers',footwear:'foot_shoes'},['men','business-casual']),
 p('man_light_suit','Lightweight blazer',['adult_man','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_shirt',lower:'lower_trousers',outerwear:'outer_blazer',footwear:'foot_shoes'},['men','business']),
 p('man_workwear','Workwear',['adult_man','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_workshirt',lower:'lower_worktrousers',outerwear:'outer_workjacket',footwear:'foot_shoes',optional_accessory:'accessory_badge'},['men','workwear']),
 p('woman_blouse_trousers','Blouse + trousers',['adult_woman','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_blouse',lower:'lower_trousers',footwear:'foot_shoes'},['women','smart']),
 p('woman_blouse_skirt','Blouse + skirt',['adult_woman','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_blouse',lower:'lower_skirt',footwear:'foot_shoes'},['women','smart']),
 p('woman_dress','Dress',['adult_woman','diminutive_adult','elder_adult','plus_size_adult'],{full_body:'full_dress',footwear:'foot_shoes'},['women','dress']),
 p('woman_hoodie_jeans','Hoodie + jeans',['adult_woman','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_tshirt',lower:'lower_jeans',outerwear:'outer_hoodie',footwear:'foot_sneakers'},['women','casual']),
 p('woman_blazer_business','Blazer business casual',['adult_woman','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_blouse',lower:'lower_trousers',outerwear:'outer_blazer',footwear:'foot_shoes'},['women','business']),
 p('woman_workwear','Workwear',['adult_woman','diminutive_adult','elder_adult','plus_size_adult'],{upper:'upper_workshirt',lower:'lower_worktrousers',outerwear:'outer_workjacket',footwear:'foot_shoes',optional_accessory:'accessory_badge'},['women','workwear']),
 p('child_tshirt_shorts','T-shirt + shorts',['boy','girl','diminutive_child'],{upper:'upper_tshirt',lower:'lower_shorts',footwear:'foot_sneakers'},['children','casual']),
 p('child_tshirt_trousers','T-shirt + trousers',['boy','girl','diminutive_child'],{upper:'upper_tshirt',lower:'lower_trousers',footwear:'foot_sneakers'},['children','casual']),
 p('child_hoodie','Hoodie outfit',['boy','girl','diminutive_child'],{upper:'upper_tshirt',lower:'lower_jeans',outerwear:'outer_hoodie',footwear:'foot_sneakers'},['children','casual']),
 p('child_school_casual','School/casual',['boy','girl','diminutive_child'],{upper:'upper_workshirt',lower:'lower_trousers',footwear:'foot_shoes'},['children','school']),
 p('child_simple_dress','Simple dress',['girl','diminutive_child'],{full_body:'full_dress',footwear:'foot_sneakers'},['children','dress']),
 p('workwear_universal','Universal workwear',['*'],{upper:'upper_workshirt',lower:'lower_worktrousers',outerwear:'outer_workjacket',footwear:'foot_shoes',optional_headwear:'head_cap',optional_accessory:'accessory_badge'},['workwear','gender-neutral'])
];
root.NexClothingLibraryV1={version:'1.0.0-phase-b',items,presets};
})(typeof window!=='undefined'?window:globalThis);
