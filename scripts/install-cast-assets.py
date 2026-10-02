from pathlib import Path
import hashlib,json,struct,zlib,time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen,Request
ROOT=Path(__file__).resolve().parents[1]
files=json.loads((ROOT/'engine_sources/makehuman-lineart/assets/FILES.json').read_text())
def verified(f):
 p=ROOT/f['path']
 if not p.is_file():return False
 data=p.read_bytes()
 return len(data)==f['size'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==f['sha']
groups={}
for f in files:
 if f['path'].endswith('/ASSETS.json'):
  if not verified(f):raise RuntimeError('The checked-in asset provenance has changed.')
  continue
 if verified(f):continue
 pack=f['path'].split('/')[3];groups.setdefault(pack,[]).append(f)
def restore(pair):
 pack,wanted=pair;name=pack.rsplit('_',1)[0];url=f'https://files2.makehumancommunity.org/asset_packs/{name}/{pack}.zip';full=None
 def fetch(lo=None,hi=None,tail=False):
  nonlocal full
  if full is not None:return full[-65557:] if tail else full[lo:hi+1]
  rg='bytes=-65557' if tail else f'bytes={lo}-{hi}'
  for attempt in range(3):
   try:
    with urlopen(Request(url+f'?cast_range={"tail" if tail else str(lo)+"-"+str(hi)}',headers={'Range':rg}),timeout=60) as r:
     data=r.read()
     if r.status==200:full=data;return full[-65557:] if tail else full[lo:hi+1]
     assert r.status==206
     return data
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 tail=fetch(tail=True);pos=tail.rfind(b'PK\x05\x06');assert pos>=0
 eocd=struct.unpack_from('<4s4H2LH',tail,pos);size,offset=eocd[5:7];central=fetch(offset,offset+size-1);entries={};i=0
 while i<len(central):
  values=struct.unpack_from('<4s6H3L5H2L',central,i);assert values[0]==b'PK\x01\x02'
  fn=central[i+46:i+46+values[10]].decode('utf-8');entries[fn]=(values[4],values[7],values[8],values[9],values[16]);i+=46+sum(values[10:13])
 for f in wanted:
  path=Path(f['path']);p=ROOT/path
  if p.is_file():
   existing=p.read_bytes()
   if hashlib.sha1(b'blob '+str(len(existing)).encode()+b'\0'+existing).hexdigest()==f['sha']:continue
  suffix='/'.join(path.parts[-2:]);hits=[n for n in entries if n.endswith(suffix)];assert len(hits)==1,(pack,suffix,hits)
  method,crc,compressed,size,offset=entries[hits[0]];b=fetch(offset,offset+30+2048+compressed-1);h=struct.unpack_from('<4s5H3L2H',b);assert h[0]==b'PK\x03\x04';start=30+h[-2]+h[-1];raw=b[start:start+compressed];data=zlib.decompress(raw,-15) if method==8 else raw
  assert len(data)==size and zlib.crc32(data)&0xffffffff==crc
  assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==f['sha'],path
  p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 print('RESTORED',pack,len(wanted),flush=True)
with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(restore,groups.items()))
if not all(verified(f) for f in files):raise RuntimeError('Asset verification failed.')
print('ALL 99 ORIGINAL ASSET FILES RESTORED AND HASH VERIFIED',flush=True)
