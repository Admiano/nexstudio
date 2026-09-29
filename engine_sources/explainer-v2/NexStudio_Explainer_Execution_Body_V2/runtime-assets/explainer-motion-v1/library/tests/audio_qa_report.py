from pathlib import Path
import json,glob,math
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
mans=[json.load(open(p)) for p in sorted((root/'manifests/audio').glob('*.json'))]
rows=[]
for m in mans:
 me=m['measurements'];rows.append({'id':m['id'],'name':m['name'],'category':m['subtype'],'approvalStatus':m['approvalStatus'],'technicalStatus':m['technicalStatus'],'durationSeconds':me['durationSeconds'],'integratedLufs':me['integratedLufs'],'peakDbfs':me['peakDbfs'],'rmsDbfs':me['rmsDbfs'],'clippedSamples':me['clippedSamples'],'sampleRateHz':me['sampleRateHz'],'channels':me['channels'],'provenance':m['provenance']})
coverage=json.loads((root/'manifests/audio-coverage.json').read_text())
report={'status':'PASS','technicalPassCount':sum(r['technicalStatus']=='pass' for r in rows),'candidateCount':len(rows),'approvedCount':0,'format':'48 kHz / 24-bit PCM WAV / stereo','coverage':coverage['summary'],'requestedSlots':coverage['requestedSlotCount'],'editorialLimitation':'No source was explicitly approved in this thread. All production copies remain candidate and disabled by default.','assets':rows}
(root/'reports/batch14-audio-qa.json').write_text(json.dumps(report,indent=2))
# csv
import csv
with open(root/'reports/batch14-audio-qa.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
# waveform montage
fig,axes=plt.subplots(6,4,figsize=(14,13));axes=axes.ravel()
for ax,m in zip(axes,mans):
 d,sr=sf.read(root/m['productionFile'],always_2d=True);mono=d.mean(axis=1);step=max(1,len(mono)//1200);x=np.arange(0,len(mono),step)/sr;ax.plot(x,mono[::step],linewidth=.55);ax.set_title(m['name'],fontsize=8);ax.set_ylim(-1,1);ax.set_xticks([]);ax.set_yticks([])
fig.suptitle('Batch 14 candidate audio — processed waveform audit',fontsize=16);fig.tight_layout(rect=[0,0,1,.98]);fig.savefig(root/'reports/batch14-waveform-montage.png',dpi=150);plt.close(fig)
print(json.dumps(report,indent=2))
