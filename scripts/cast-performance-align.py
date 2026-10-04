"""Offline two-pass forced word/phoneme alignment; never estimates speech timing."""
import json,re,wave,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'vendor'))
PHONE_VISEME={**{p:'MBP' for p in ['M','B','P']},**{p:'FV' for p in ['F','V']},**{p:'OH' for p in ['OW','UW','UH','AO','OY','W']},**{p:'EE' for p in ['IY','IH','EY','Y']},**{p:'AH' for p in ['AA','AE','AH','AW','AY','EH','ER']},**{p:'RELAX' for p in ['D','DH','G','HH','JH','K','L','N','NG','R','S','SH','T','TH','Z','ZH','CH']}}
def align_master(path,text):
 from pocketsphinx import Decoder
 if not isinstance(text,str) or not text.strip():raise ValueError('TRANSCRIPT_REQUIRED')
 path=Path(path)
 with wave.open(str(path)) as f:
  assert f.getframerate()==16000 and f.getnchannels()==1 and f.getsampwidth()==2
  audio=f.readframes(f.getnframes());duration=f.getnframes()/f.getframerate()
 tokens=re.findall(r"[a-z]+(?:'[a-z]+)?",text.lower());d=Decoder(lm=None,loglevel='ERROR')
 for word in tokens:
  if not d.lookup_word(word):raise RuntimeError('ALIGNMENT_DICTIONARY_WORD_MISSING:'+word)
 d.set_align_text(' '.join(tokens));d.start_utt();d.process_raw(audio,full_utt=True);d.end_utt();d.set_alignment();d.start_utt();d.process_raw(audio,full_utt=True);d.end_utt()
 words=[];phones=[];silence=[]
 for word in d.get_alignment():
  start=word.start/100;end=(word.start+word.duration)/100
  if word.name in ('<sil>','<s>','</s>','[SPEECH]'):
   if end>start:silence.append([start,min(duration,end)])
   continue
  words.append({'word':re.sub(r'\(\d+\)$','',word.name),'pronunciationVariant':word.name,'start':start,'end':end,'acousticScore':word.score})
  for phone in word:
   p=phone.name;a=phone.start/100;b=(phone.start+phone.duration)/100
   if p=='SIL':
    if b>a:silence.append([a,min(b,duration)])
   elif b>a:
    if p not in PHONE_VISEME:raise RuntimeError('PHONE_NOT_MAPPED:'+p)
    phones.append({'phone':p,'viseme':PHONE_VISEME[p],'start':a,'end':min(duration,b),'intensity':.85})
 assert [w['word'] for w in words]==tokens,([w['word'] for w in words],tokens)
 assert all(0<=p['start']<p['end']<=duration for p in phones)
 assert all(w['end']>w['start'] for w in words)
 out={'text':text,'duration':duration,'word_segments':words,'viseme_segments':phones,'silence_windows':silence,'alignment':'PocketSphinx 5.0.4 two-pass forced word/phone alignment, acoustic 10 ms grid','completeWordCoverage':True,'audioSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'language':'en-US','alignmentIsNotAnEliteQualityScore':True}
 return out

if __name__=='__main__':
 audio,transcript,output=map(Path,sys.argv[1:4])
 result=align_master(audio,transcript.read_text())
 output.write_text(json.dumps(result,indent=2))
 print('ALIGNED',result['duration'],'WORDS',len(result['word_segments']),'PHONES',len(result['viseme_segments']))
