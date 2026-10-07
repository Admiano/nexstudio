import sys,json,numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,minimum_filter,median_filter
d=sys.argv[1];ref=sys.argv[2]
seg=np.fromfile(f'{d}/lines.raw.f64',np.float64).reshape(-1,12)
meta=json.load(open(f'{d}/meta.json'));cam=meta['camera']
im=np.asarray(Image.open(ref).convert('RGBA'),dtype=np.float32)/255;h,w=im.shape[:2]
lum=(im[...,:3]@np.array([.2126,.7152,.0722]))*im[...,3]+(1-im[...,3])
rim=(im[...,3]>.5)&(minimum_filter(im[...,3],5)<=.5)
ink=binary_dilation(minimum_filter(lum,3)<.8*median_filter(lum,9),iterations=3)
mid=(seg[:,3:6]+seg[:,6:9])/2
u=(mid[:,0]-cam['x'])/(cam['scale']*cam['aspect'])+.5;v=(mid[:,2]-cam['z'])/cam['scale']+.5
x=np.clip((u*w).astype(int),0,w-1);y=np.clip(((1-v)*h).astype(int),0,h-1)
hit=ink[y,x]
ends=np.round(np.concatenate([seg[:,3:6],seg[:,6:9]]),5);_,ids=np.unique(ends,axis=0,return_inverse=True);ids=ids.ravel();n=len(seg);a,b=ids[:n],ids[n:];keep=hit.copy()
for _ in range(3):
    at=np.bincount(np.concatenate([a[keep],b[keep]]),minlength=ids.max()+1)>0;keep|=at[a]&at[b]
keep&=~rim[y,x]
out=seg[keep][:,[0,1,2,9,10,11]].astype(np.float32);out.tofile(f'{d}/lines.bin')
print('LINES',n,int(hit.sum()),int(keep.sum()))
