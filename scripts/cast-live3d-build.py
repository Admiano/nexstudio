"""Render, assemble and bake every Cast live-3D part source, then write the manifest.

Jobs come from scripts/cast-live3d-jobs.ts. Each job renders the exact approved
look (kept as the reference image), saves its assembled scene and exports the
parts that look contributes."""
import re,hashlib,json,os,subprocess,sys,time
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('CAST_LIVE3D_OUT',ROOT/'engine_sources/makehuman-lineart/out/cast-live3d'))
PARTS=OUT/'parts'
SOURCE=Path(os.environ.get('CAST_SOURCE_DIR',ROOT/'engine_sources/makehuman-lineart/presenters_v1'))
BLENDER=os.environ.get('BLENDER_BIN','/opt/blender-5.2.1-linux-x64/blender')
PROFILE=dict(CAST_QUALITY_PILOT='1',CAST_FINISH_UPGRADE='1',CAST_GARMENT_STRUCTURE_PILOT='1',CAST_SKIN_APPEARANCE='1',CAST_HAIR_GROOM='1',CAST_FACIAL_REFINEMENT='1',CAST_CLOTH_APPEARANCE='1')

def part_keys(spec):
    c=spec['character'][0];o=spec['outfit']['kind']
    keys={'body':f"{c}-face{spec['face']}-{o}",'hair':f"{c}-{spec['hair']['style']}",'garment':f"{c}-{o}"}
    if c=='f':
        keys['earring']=f"f-{spec['hair']['style']}"
        if spec.get('neck') and spec['neck']!='none':keys['neck']=f"f-{spec['neck']}"
    elif spec.get('watch') and o in ('o1','o2'):keys['watch']=f"m-{spec['watch']}-{o}"
    return keys

def run_job(job,lines_only=False,hair_only=False):
    spec=json.loads((job/'spec.json').read_text());config=json.loads((job/'request.json').read_text())['config']
    env=dict(os.environ,**config['env'],**PROFILE,CAST_SOURCE_DIR=str(SOURCE),BLENDER_BIN=BLENDER,CAST_RENDER_ENTRY=str(ROOT/'scripts/cast-render-assembled.py'),MH_ROOT=os.environ.get('MH_ROOT',str(SOURCE.parent/'assets')),PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1')
    started=time.monotonic()
    if not (job/'render.png').is_file() or not (job/'assembled.blend').is_file():
        with (job/'render.log').open('w') as log:
            subprocess.run(['bash',str(ROOT/'scripts/cast-preview-render.sh'),str(job/'request.json'),str(job/'render.png'),'--scene-output',str(job/'assembled.blend')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800,check=True)
    if job.name.startswith(('c_','v_')):return
    if lines_only or hair_only:env['LINES_ONLY']='1'
    if hair_only:env['HAIR_ONLY']='1'
    keys=part_keys(spec)
    if job.name.startswith('b_'):keys={'body':keys['body']};env['BAKE_GROUPS']='body'
    if job.name.startswith('w_'):keys={'watch':keys['watch']};env['BAKE_GROUPS']='watch'
    env.update(REF_PNG=str(job/'render.png'),PART_KEYS=json.dumps(keys),JOB_ID=job.name)
    with (job/'bake.log').open('w') as log:
        subprocess.run([BLENDER,'-b',str(job/'assembled.blend'),'--threads',os.environ.get('CAST_RENDER_THREADS','4'),'--python-exit-code','1','--python',str(ROOT/'scripts/cast-live3d-bake.py'),'--',str(PARTS),str(config['frame'])],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=3600,check=True)
    print('CAST_LIVE3D_JOB',job.name,round(time.monotonic()-started),flush=True)

def project(pos,cam,w,h):
    u=(pos[:,0]-cam['x'])/(cam['scale']*cam['aspect'])+.5;v=(pos[:,2]-cam['z'])/cam['scale']+.5
    return np.clip((u*w).astype(int),0,w-1),np.clip(((1-v)*h).astype(int),0,h-1)

def close_gaps(seg,hit,rounds=3):
    """Fill short unhit runs between inked segments of the same stroke, so render anti-aliasing does not leave dashes."""
    ends=np.round(np.concatenate([seg[:,0:3],seg[:,3:6]]),5);_,ids=np.unique(ends,axis=0,return_inverse=True);ids=ids.ravel();n=len(seg)
    a,b=ids[:n],ids[n:];keep=hit.copy()
    for _ in range(rounds):
        at=np.bincount(np.concatenate([a[keep],b[keep]]),minlength=ids.max()+1)>0
        keep=keep|(at[a]&at[b])
    return keep

def filter_lines():
    """Keep only the line segments the exact render actually inked, so edges Freestyle hid stay hidden in the browser. Segments on the figure's outer rim are left to the outline pass."""
    from PIL import Image
    from scipy.ndimage import binary_dilation,minimum_filter,median_filter
    cam=json.loads((PARTS/'camera.json').read_text());owners={};inks={}
    for meta_path in sorted(PARTS.glob('meta-*.json')):
        for group,info in json.loads(meta_path.read_text())['groups'].items():
            raw=PARTS/group/f"{info['key']}.lines.raw.bin"
            if raw.is_file():owners.setdefault(raw,[]).append(meta_path)
    for raw,metas in owners.items():
        owner=Path(str(raw).replace('.lines.raw.bin','.lines.job'));ref=OUT/'jobs'/owner.read_text().strip()/'render.png' if owner.is_file() else None
        if ref is None or not ref.is_file():continue
        if ref not in inks:
            im=np.asarray(Image.open(ref).convert('RGBA'),dtype=np.float32)/255
            lum=(im[...,:3]@np.array([.2126,.7152,.0722]))*im[...,3]+(1-im[...,3])
            rim=(im[...,3]>.5)&(minimum_filter(im[...,3],5)<=.5)
            inks[ref]=binary_dilation(minimum_filter(lum,3)<.8*median_filter(lum,9),iterations=3),rim
        ink,rim=inks[ref];h,w=ink.shape;seg=np.fromfile(raw,np.float32).reshape(-1,10);x,y=project((seg[:,0:3]+seg[:,3:6])/2,cam,w,h)
        keep=close_gaps(seg,ink[y,x])&~rim[y,x]
        seg[keep].tofile(str(raw).replace('.lines.raw.bin','.lines.bin'))
        print('CAST_LIVE3D_LINES',raw.name,len(seg),int(ink[y,x].sum()),int(keep.sum()),flush=True)

def hair_calibration(parts):
    """Rendered hair colour per catalog hair hex: the exact c_* renders of one look differ only in hair colour, so pixels that change between them are hair."""
    from PIL import Image
    renders={}
    for job in sorted((OUT/'jobs').glob('c_*')):
        if not (job/'render.png').is_file():continue
        spec=json.loads((job/'spec.json').read_text());env=json.loads((job/'request.json').read_text())['config']['env']
        c=spec['character'][0];hx=(env.get('CAST_HAIR_HEX') or ('9A4A2E' if c=='f' else '5A3A24')).upper()
        im=np.asarray(Image.open(job/'render.png').convert('RGBA'),dtype=np.float32)/255
        renders.setdefault(c,[]).append((hx,bool(env.get('CAST_HAIR_DYE')),im))
    shade={}
    for c,items in renders.items():
        if len(items)<2:continue
        stack=np.stack([im for _,_,im in items]);rgb=stack[...,:3]
        mask=((rgb.max(0)-rgb.min(0)).max(-1)>.08)&(stack[...,3].min(0)>.9)
        if mask.sum()<500:continue
        for hx,dye,im in items:
            if dye:continue
            px=im[...,:3][mask];lin=np.where(px<=.04045,px/12.92,((px+.055)/1.055)**2.4)
            shade.setdefault(c,{})[hx]=[round(float(x),5) for x in np.median(lin,0)]
    cal=ROOT/'engine_sources/makehuman-lineart/character_system/live3d-hair-calibration.json'
    for c,table in (json.loads(cal.read_text()) if cal.is_file() else {}).items():
        for hx,k in table.items():
            if hx in shade.get(c,{}):shade[c][hx]=[round(v*f,5) for v,f in zip(shade[c][hx],k)]
    return shade

def glb_meshes(path):
    data=bytearray(path.read_bytes());n=int.from_bytes(data[12:16],'little');gltf=json.loads(data[20:20+n]);base=20+n+8
    def view(i):
        a=gltf['accessors'][i];v=gltf['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];off=base+v.get('byteOffset',0)+a.get('byteOffset',0)
        return off,np.frombuffer(bytes(data[off:off+a['count']*k*dt.itemsize]),dt).reshape(-1,k)
    meshes=[]
    for node in gltf['nodes']:
        if 'mesh' not in node:continue
        assert 'matrix' not in node and 'children' not in node
        x,y,z,w=node.get('rotation',[0,0,0,1])
        rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        for prim in gltf['meshes'][node['mesh']]['primitives']:
            pos=(view(prim['attributes']['POSITION'])[1]*np.array(node.get('scale',[1,1,1])))@rot.T+np.array(node.get('translation',[0,0,0]))
            off,idx=view(prim['indices']);meshes.append((node['name'],pos,off,idx.reshape(-1,3)))
    return data,meshes

def cull_hidden_skin(cell=.0015):
    """Drop body faces the garment fully covers from the fixed orthographic camera, so skin under clothes cannot show through in the browser."""
    from scipy.ndimage import minimum_filter
    for body in sorted((PARTS/'body').glob('*-face*-*.glb')):
        c,o=body.stem.split('-face')[0],body.stem.rsplit('-',1)[1];garment=PARTS/'garment'/f'{c}-{o}.glb'
        if not garment.is_file():continue
        tris=np.concatenate([pos[idx] for _,pos,_,idx in glb_meshes(garment)[1]])
        lo=tris[...,:2].reshape(-1,2).min(0);shape=np.ceil((tris[...,:2].reshape(-1,2).max(0)-lo)/cell).astype(int)+1
        front=np.full(shape,-np.inf)
        for t in tris:
            xy=(t[:,:2]-lo)/cell;x0,y0=np.floor(xy.min(0)).astype(int);x1,y1=np.ceil(xy.max(0)).astype(int)
            gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1),indexing='ij');px=np.stack([gx.ravel(),gy.ravel()],1)+.5
            m=np.array([[xy[1,0]-xy[0,0],xy[2,0]-xy[0,0]],[xy[1,1]-xy[0,1],xy[2,1]-xy[0,1]]])
            if abs(np.linalg.det(m))<1e-12:continue
            uv=np.linalg.solve(m,(px-xy[0]).T).T;w=np.c_[1-uv.sum(1),uv];ok=(w>=-1e-6).all(1)
            if not ok.any():continue
            cx,cy=np.clip(px[ok,0].astype(int),0,shape[0]-1),np.clip(px[ok,1].astype(int),0,shape[1]-1)
            np.maximum.at(front,(cx,cy),w[ok]@t[:,2])
        front=minimum_filter(front,3,mode='constant',cval=-np.inf)
        data,meshes=glb_meshes(body);culled=0
        for name,pos,off,idx in meshes:
            if not re.fullmatch(r'L3D_Host\.(body|lineart_lower_legs)',name):continue
            g=np.floor((pos[:,:2]-lo)/cell).astype(int);inside=(g>=0).all(1)&(g<shape).all(1)
            hid=np.zeros(len(pos),bool);hid[inside]=front[g[inside,0],g[inside,1]]>pos[inside,2]
            drop=hid[idx].all(1)&(idx!=idx[:,:1]).any(1)
            if not drop.any():continue
            new=idx.copy();new[drop]=new[drop][:,:1];data[off:off+new.nbytes]=new.astype(idx.dtype).tobytes();culled+=int(drop.sum())
        if culled:body.write_bytes(data)
        print('CAST_LIVE3D_CULL',body.name,culled,flush=True)

def write_manifest():
    parts={};digest=hashlib.sha256()
    for meta_path in sorted(PARTS.glob('meta-*.json')):
        meta=json.loads(meta_path.read_text());env=meta['env'];digest.update(meta_path.read_bytes())
        request=OUT/'jobs'/meta_path.stem.removeprefix('meta-')/'request.json'
        if 'CAST_DRESS' not in env and request.is_file():env['CAST_DRESS']=json.loads(request.read_text())['config']['env'].get('CAST_DRESS','')
        garments=dict(x.split('=',1) for x in env['CAST_GARMENTS'].split(',') if '=' in x)
        for group,info in meta['groups'].items():
            key=info['key'];entry={'glb':f'{group}/{key}.glb'}
            for ext in ('lines','hair'):
                if (PARTS/group/f'{key}.{ext}.bin').is_file():entry[ext]=f'{group}/{key}.{ext}.bin'
            ink=PARTS/group/f'{key}.ink.json'
            if ink.is_file():entry['ink']={re.sub(r'^L3D_Host','',re.sub(r'[\[\].:/]','',n.replace(' ','_'))):i for n,i in json.loads(ink.read_text()).items()};digest.update(ink.read_bytes())
            if group=='body':entry.update(skin=env['CAST_SKIN_HEX'],lip=env['CAST_LIP_HEX'] or 'A86F66')
            if group=='hair':entry['hairHex']=env['CAST_HAIR_HEX'] or '9A4A2E'
            if group=='garment':entry['tint']=garments or {env['CAST_DRESS']:env['CAST_DRESS_HEX']}
            parts.setdefault(group,{})[key]=entry
    shade=hair_calibration(parts)
    for f in sorted(PARTS.rglob('*')):
        if f.is_file() and f.suffix in ('.glb','.bin'):digest.update(f'{f.relative_to(PARTS)}:{f.stat().st_size}:{f.stat().st_mtime_ns}'.encode())
    digest.update(json.dumps(shade,sort_keys=True).encode())
    from PIL import Image
    cam=json.loads((PARTS/'camera.json').read_text());ref=next((j/'render.png' for j in sorted((OUT/'jobs').iterdir()) if (j/'render.png').is_file()),None)
    outline={'width':cam['scale']/Image.open(ref).size[1],'colour':.008} if ref else None
    manifest={'version':digest.hexdigest()[:16],'parts':parts,'hairShade':shade,'outline':outline}
    (PARTS/'manifest.json').write_text(json.dumps(manifest,indent=1))
    print('CAST_LIVE3D_MANIFEST',manifest['version'],{g:len(v) for g,v in parts.items()})

if __name__=='__main__':
    PARTS.mkdir(parents=True,exist_ok=True)
    if '--hair-only' in sys.argv:
        for meta_path in sorted(PARTS.glob('meta-*.json')):
            if 'hair' in json.loads(meta_path.read_text())['groups']:run_job(OUT/'jobs'/meta_path.stem.removeprefix('meta-'),hair_only=True)
    elif '--lines-only' in sys.argv:
        for meta_path in sorted(PARTS.glob('meta-*.json')):run_job(OUT/'jobs'/meta_path.stem.removeprefix('meta-'),lines_only=True)
    elif '--manifest-only' not in sys.argv:
        for job in sorted((OUT/'jobs').iterdir()):run_job(job)
    filter_lines()
    cull_hidden_skin()
    write_manifest()
