#!/usr/bin/env python3
"""Phoneme timings for lip sync from a voiceover and its script (local, CPU).

Usage: python3 cast-phoneme-align.py voice.wav script.txt|- out.json
With "-" (uploaded voiceover, no script) faster-whisper (MIT, local CPU)
transcribes first; WHISPER_MODEL picks the size (default small.en).
Runs the Montreal Forced Aligner (MIT; english_us_arpa models) and writes
{"phones": [[start_sec, end_sec, "ARPAbet"], ...], "words": [[start, end, word], ...]}.
MFA_BIN points at the mfa executable (its conda env bin must hold openfst/kaldi).
"""
import json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
voice,script,out=Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3])
def transcribe():
    from faster_whisper import WhisperModel
    model=WhisperModel(os.environ.get('WHISPER_MODEL','small.en'),device='cpu',compute_type='int8')
    segments,_=model.transcribe(str(voice),beam_size=5,vad_filter=True)
    return ' '.join(x.text.strip() for x in segments)
text=transcribe() if script=='-' else Path(script).read_text()
mfa=os.environ.get('MFA_BIN') or shutil.which('mfa')
if not mfa:sys.exit('MFA_RUNTIME_MISSING')
env=dict(os.environ,PATH=str(Path(mfa).parent)+os.pathsep+os.environ.get('PATH',''))
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'in';dst=Path(tmp)/'out';src.mkdir()
    subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(voice),'-ac','1','-ar','16000',str(src/'voice.wav')],check=True)
    (src/'voice.lab').write_text(' '.join(text.split()))
    subprocess.run([mfa,'align','--clean','-j','4','--single_speaker','--output_format','json',str(src),
                    os.environ.get('MFA_DICTIONARY','english_us_arpa'),os.environ.get('MFA_ACOUSTIC','english_us_arpa'),str(dst)]
                   # out-of-dictionary words (brand names) are spelled by the G2P model
                   +['--g2p_model_path',os.environ.get('MFA_G2P','english_us_arpa')],
                   check=True,env=env,stdout=subprocess.DEVNULL)
    tiers=json.loads((dst/'voice.json').read_text())['tiers']
out.write_text(json.dumps({'phones':[[round(s,3),round(e,3),p] for s,e,p in tiers['phones']['entries']],
                           'words':[[round(s,3),round(e,3),w] for s,e,w in tiers['words']['entries']]})+'\n')
print('PHONEME_ALIGN',json.dumps({'phones':len(tiers['phones']['entries']),'words':len(tiers['words']['entries'])}))
