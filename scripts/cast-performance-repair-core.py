"""Patch only audited blockers in the unchanged core runtime. Native character assets are untouched."""
import ast,textwrap,json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
input_path,output_path=map(Path,sys.argv[1:3])
source_bytes=input_path.read_bytes()
if hashlib.sha256(source_bytes).hexdigest()!='ca77fcaf084e6807cbd8e62df0fae18b962f69a41dc8f6fab505f5fe52e3e43c':raise ValueError('CORE_RUNTIME_SOURCE_VERSION_MISMATCH')
src=source_bytes.decode('utf-8')
tree=ast.parse(src);edits=[]
def edit(n,new):edits.append((n.lineno-1,n.end_lineno,new.splitlines(keepends=True)))
for n in tree.body:
 if isinstance(n,ast.FunctionDef):
  old=ast.get_source_segment(src,n)
  if n.name=='plan_actor':
   old=old.replace("    actor=deep(actor_context);", "    errors=pg_actor_errors(actor_context)\n    if errors:return pg_failure(actor_context,errors)\n    actor=deep(actor_context);")
   edit(n,old+'\n')
  elif n.name=='segment_script':
   old=old.replace('    if word_segments:\n','    if word_segments:\n        if [w.lower() for s in word_segments for w in pg_words(s.get(\'word\',s.get(\'text\',\'\')))] != [w.lower() for w in pg_words(script)]:raise ValueError(\'INCOMPLETE_OR_MISMATCHED_WORD_ALIGNMENT\')\n')
   old=old.replace("                a=float(word_segments[-1]['end']) if word_segments else 0.0;b=a+estimate_duration(text,wpm)","                raise ValueError('INCOMPLETE_WORD_ALIGNMENT')")
   edit(n,old+'\n')
  elif n.name=='validate_segments':
   old=old.replace("        if a<last-1e-6:","        if not math.isfinite(a) or not math.isfinite(b):errs.append({'code':'NONFINITE_TIMING','index':i});continue\n        if a<last-1e-6:")
   old=old.replace('b>duration+.04','b>duration+1e-7');edit(n,old+'\n')
  elif n.name=='compile_speech_timing':
   old=old.replace("    duration=float(duration or speech.get('duration') or estimate_duration(text))", "    if speech.get('timing_authority')=='MASTER_AUDIO':\n        preflight=pg_actor_errors({'script':text,'script_beats':speech.get('_validated_script_beats'),'speech':speech})\n        try:\n            master_duration=pg_number(speech.get('duration'),'master.duration',positive=True)\n            requested=master_duration if duration is None else pg_number(duration,'requested.duration',positive=True)\n            if abs(requested-master_duration)>1e-7:preflight.append({'code':'MASTER_DURATION_MISMATCH'})\n        except ValueError as ex:preflight.append({'code':'MASTER_DURATION_INVALID','detail':str(ex)})\n        if preflight:return {'status':'FAIL_CLOSED','errors':preflight,'duration':0,'segments':[],'word_segments':[],'phone_segments':[],'timing_authority':'MASTER_AUDIO'}\n        duration=master_duration\n    else:duration=float(duration or speech.get('duration') or estimate_duration(text))")
   old=old.replace("    authority=speech.get('timing_authority')", "    authority=speech.get('timing_authority')\n    timing_errors=pg_actor_errors({'script':text,'script_beats':speech.get('_validated_script_beats'),'speech':speech}) if authority=='MASTER_AUDIO' else []\n    if authority=='MASTER_AUDIO' and abs(duration-float(speech['duration']))>1e-7:timing_errors.append({'code':'MASTER_DURATION_MISMATCH'})")
   old=old.replace('errors=validate_segments(word_seg,duration)+validate_segments(seg,duration)','errors=timing_errors+validate_segments(word_seg,duration)+validate_segments(seg,duration)')
   # Explicit beat timing is accepted for body/attention, never used to invent phonemes.
   old=old.replace('word_seg=words_in or estimated_words(text,duration)',"word_seg=words_in or ([] if authority=='MASTER_AUDIO' else estimated_words(text,duration))")
   edit(n,old+'\n')
  elif n.name=='build_tracks':
   old=old.replace("speech_req.setdefault('text',actor.get('script'))","speech_req.setdefault('text',actor.get('script'));speech_req['_validated_script_beats']=actor.get('script_beats')")
   edit(n,old+'\n')
  elif n.name=='validate_attention_event':edit(n,"def validate_attention_event(event):\n    return pg_attention(event,LIVING_ATTENTION_DATA['attention']['limits_deg'])\n")
  elif n.name=='solve_seated_support':
   old=old.replace("    native =", "    native =")
   # Insert after the original docstring.
   doc=n.body[0];offset=doc.end_lineno-n.lineno+1;ls=old.splitlines(keepends=True);ls[offset:offset]=["    finite_errors=pg_seat_errors(character,chair)\n","    if finite_errors:return {'status':'FAIL_CLOSED','failure':{'code':'SEATED_ADAPTER_INVALID','details':finite_errors}}\n"];edit(n,''.join(ls)+'\n')
  elif n.name=='validate_seated_support':
   old=old.replace("    failures=[]","    failures=[]\n    try:\n        for key in required:pg_number(sup[key],key)\n        pg_number(tolerance,'tolerance',positive=True)\n        pg_number(sup.get('back_contact_tolerance',.025),'back_contact_tolerance',positive=True)\n    except ValueError as ex:return {'status':'FAIL_CLOSED','failures':[str(ex)]}");edit(n,old+'\n')
 if isinstance(n,ast.ClassDef):
  for m in n.body:
   if not isinstance(m,ast.FunctionDef):continue
   old=textwrap.dedent(ast.get_source_segment(src,m)) if False else '\n'.join(src.splitlines()[m.lineno-1:m.end_lineno])
   # Keep class indentation explicitly.
   if n.name=='SpeechSystem' and m.name=='sample_timeline':
    new="    def sample_timeline(self,events,time_seconds,speaker_owned=True):\n        state=pg_sample_viseme(events,time_seconds,speaker_owned)\n        return self.apply(state['viseme'],state['intensity'],state['speaker_owned'])\n";edit(m,new)
   elif n.name=='PerformanceExecutor' and m.name=='execute_actor_plan':
    old=old.replace("            sf=_sec_to_frame(d['start'],fps,frame0)","            sf=_sec_to_frame(d['start'],fps,frame0)\n            ef=_sec_to_frame(d['end'],fps,frame0)\n            self._directive_end_frame=ef")
    old=old.replace("        return {'status':'FAIL_CLOSED' if failures else 'PASS'","        self._directive_end_frame=None\n        return {'status':'FAIL_CLOSED' if failures else 'PASS'");edit(m,old+'\n')
   elif n.name=='PerformanceExecutor' and m.name=='add_overlay':
    old=old.replace('start_frame=1, influence=1.0):','start_frame=1, influence=1.0, end_frame=None):')
    old=old.replace('lo,hi=map(float,a.frame_range); end_frame=float(start_frame)+(hi-lo)',"lo,hi=map(float,a.frame_range)\n        start_frame=pg_number(start_frame,'overlay.start')\n        bound=end_frame if end_frame is not None else getattr(self,'_directive_end_frame',None)\n        end_frame=pg_number(bound,'overlay.end') if bound is not None else start_frame+(hi-lo)\n        if end_frame<=start_frame or hi<=lo:raise ValueError('OVERLAY_WINDOW_INVALID')")
    old=old.replace('st.frame_start=float(start_frame); st.frame_end=end_frame','st.frame_start=float(start_frame); st.scale=(end_frame-start_frame)/(hi-lo); st.frame_end=end_frame')
    edit(m,old+'\n')
if len(edits)!=11:raise ValueError('CORE_PATCH_TARGET_COUNT_MISMATCH')
lines=src.splitlines(keepends=True)
for a,b,new in sorted(edits,reverse=True):lines[a:b]=new
out=''.join(lines)+'\n# Audited strict boundary helpers. Embedded so the saved core is self-contained.\n'+(R/'nex_performance_guards.py').read_text()
compile(out,'patched_runtime','exec');output_path.write_text(out)
print('PATCHED_BLOCKER_NODES',len(edits))
