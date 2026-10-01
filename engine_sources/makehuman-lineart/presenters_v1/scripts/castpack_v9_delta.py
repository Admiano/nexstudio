#!/usr/bin/env python3
# Pack only the Cast V9 delta plates: independent garment colours + true lip patches.
import glob, json, os, re, sys
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
import OpenEXR

NEW=os.environ.get("BAKE_OUT","/home/runner/work/cast-v9-out")
DST=os.environ.get("PLATE_DST","/home/runner/work/cast-v9-plates")
CW,CH=720,1080
os.makedirs(DST,exist_ok=True)
PLATES=json.load(open(os.path.join(NEW,"plates.json")))

def _id_float(hexs):
    return np.uint32(int(hexs,16)).view(np.float32)

_cache={}
def exr_meta_and_channels(path):
    if path in _cache: return _cache[path]
    f=OpenEXR.File(path); man={}; pairs=[]; top=None
    for p in f.parts:
        for k in p.header.keys():
            if k.startswith("cryptomatte") and k.endswith("/manifest"):
                v=p.header[k]
                s=v.decode() if isinstance(v,bytes) else str(v)
                for name,hexs in json.loads(s).items(): man[name]=_id_float(hexs)
    for p in f.parts:
        pname=p.name() if callable(p.name) else p.name
        if not pname.startswith("crypto"): continue
        cn=p.channels
        for a,b in (("r","g"),("b","a")):
            ia=f"{pname}.{a}"; cb=f"{pname}.{b}"
            if ia in cn and cb in cn:
                pairs.append((np.asarray(cn[ia].pixels),np.asarray(cn[cb].pixels)))
        if top is None and f"{pname}.r" in cn:
            top=np.asarray(cn[f"{pname}.r"].pixels)
    out=(man,pairs,top); _cache[path]=out; return out

def extract(src,keep):
    png=np.array(Image.open(os.path.join(NEW,src+".png")).convert("RGBA"))
    man,pairs,top=exr_meta_and_channels(os.path.join(NEW,"z_"+src+".exr"))
    keepids={man[n] for n in keep if n in man}
    missing=[n for n in keep if n not in man]
    # V64 objects are auxiliary line/proxy helpers. Some are intentionally
    # hidden from the beauty/Cryptomatte pass, so their absence is not an
    # extraction failure. Real garment/accessory objects remain strict.
    helper_missing=[n for n in missing if n.startswith("Host.V64_")]
    required_missing=[n for n in missing if not n.startswith("Host.V64_")]
    if helper_missing:
        print(f"WARN {src}: non-rendered helper ids omitted: {helper_missing[:8]}")
    if required_missing:
        raise RuntimeError(f"{src}: missing required cryptomatte ids: {required_missing[:8]}")
    if not keepids:
        raise RuntimeError(f"{src}: no requested objects are present in cryptomatte manifest")
    m=np.zeros(top.shape if top is not None else pairs[0][0].shape,bool)
    ids=list(keepids) or [np.float32(-1)]
    for idc,cov in pairs: m|=(cov>0)&np.isin(idc,ids)
    ink=(png[...,3]>0)&(png[...,:3].sum(2)<140)
    m|=ink&np.isin(top,ids)
    m|=ink&(top==0)&binary_dilation(m,iterations=4)
    out=png.copy(); out[...,3]=np.where(m,png[...,3],0)
    return out

def ship(stem,rgba):
    Image.fromarray(rgba).resize((CW,CH),Image.LANCZOS).save(os.path.join(DST,stem+".png"))

FEM_COLORS=("navy","burgundy","sage","emerald","rose")
MALE_COLORS=("navy","ivory","blue","burgundy","cream")
pat=re.compile(r"^(fem_outfit_(sheath|maxi|column|cocktail|qipao)_("+ "|".join(FEM_COLORS) +r")|male_outfit_(o1|o2|o3|o4|o5)_("+ "|".join(MALE_COLORS) +r"))$")
made=[]
for stem,spec in sorted(PLATES.items()):
    if not pat.match(stem): continue
    ship(stem,extract(spec["src"],spec["keep"])); made.append(stem)

for png in sorted(glob.glob(os.path.join(NEW,"fem_liprender_f*_*.png"))):
    stem=os.path.basename(png)[:-4]; _,_,face,shade=stem.split("_")
    variant=np.array(Image.open(png).convert("RGBA"))
    base=np.array(Image.open(os.path.join(NEW,f"fem_body_{face}_medium.png")).convert("RGBA"))
    diff=np.max(np.abs(variant[...,:3].astype(np.int16)-base[...,:3].astype(np.int16)),axis=2)
    mask=binary_dilation(diff>2,iterations=2)
    out=variant.copy(); out[...,3]=np.where(mask,variant[...,3],0)
    dst=f"fem_lip_{face}_{shade}"
    ship(dst,out); made.append(dst)

expected=int(os.environ.get("CAST_V9_EXPECTED","62"))
if len(set(made))!=expected:
    raise SystemExit(f"FAIL packed {len(set(made))}/{expected} delta plates")
print(f"PASS packed {expected}/{expected} Cast V9 delta plates")
