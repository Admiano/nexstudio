#!/usr/bin/env python3
"""Install verified SceneBam formalwear source scenes for the Cast Blender worker.

Usage:
  gh run download 38480065233 --repo Admiano/nexstudio \
      --name SCENEBAM_SIX_FORMALS_PRODUCTION_ASSEMBLY_PROOFS --dir /tmp/scenebam-forms
  python scripts/install-scenebam-formal-bank.py \
      /tmp/scenebam-forms /opt/scenebam/cast-formals
  export CAST_FORMAL_SCENE_DIR=/opt/scenebam/cast-formals

Does NOT deploy or change public production unless you intentionally set the
runtime environment and restart workers. Stages only the six genuine .blend
objects, with a SHA256 install manifest and atomic destination rename.
"""
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path

LOOKS=('female-double-breasted','female-statement','male-jacket-tie',
       'male-double-breasted','male-navy-classic','male-dinner-jacket')
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as file:
        for block in iter(lambda:file.read(1048576),b''):h.update(block)
    return h.hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('unpacked_proof_artifact',type=Path)
    parser.add_argument('destination',type=Path)
    a=parser.parse_args()
    src=a.unpacked_proof_artifact.resolve()
    dest=a.destination.resolve()
    if not src.is_dir():parser.error('Original GitHub Actions artifact must be unpacked first')
    if dest==src or src in dest.parents:parser.error('Destination must be outside source')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='scenebam-formals-stage-',dir=dest.parent) as directory:
        stage=Path(directory)
        manifest={'schema':'SceneBamActualBlenderFormalBankV1','originRun':38480065233,
                  'originArtifact':'SCENEBAM_SIX_FORMALS_PRODUCTION_ASSEMBLY_PROOFS',
                  'exactDeployedVMParityCertified':False,'looks':{}}
        for look in LOOKS:
            file=src/look/(look+'-production-assembled.blend')
            proof=src/look/'production-proof.json'
            if not file.is_file() or not proof.is_file():
                raise RuntimeError('SCENEBAM_FORMAL_SOURCE_MISSING:'+look)
            data=json.loads(proof.read_text())
            if data.get('variant')!=look or data.get('sourceRigRestMaxError',1)>1e-4:
                raise RuntimeError('SCENEBAM_FORMAL_PROVENANCE_INVALID:'+look)
            if data.get('productionRigBones')!=163 or data.get('garmentVertexCount',0)<1000:
                raise RuntimeError('SCENEBAM_FORMAL_RIG_INVALID:'+look)
            if file.stat().st_size<1_000_000 or file.open('rb').read(7)!=b'BLENDER':
                raise RuntimeError('SCENEBAM_FORMAL_NOT_REAL_BLEND:'+look)
            d=stage/look;d.mkdir()
            target=d/file.name
            shutil.copy2(file,target)
            sha=digest(target)
            manifest['looks'][look]={'file':look+'/'+file.name,'sha256':sha,
                         'bytes':target.stat().st_size,'rigBones':163}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        if dest.exists():raise FileExistsError('Destination exists; install into a new versioned directory: '+str(dest))
        # Atomic rename within destination filesystem; no partly installed bank.
        os.replace(stage,dest)
    print('SCENEBAM_ACTUAL_FORMAL_BANK_READY',json.dumps({'destination':str(dest),'count':len(LOOKS)}))
if __name__=='__main__':main()
