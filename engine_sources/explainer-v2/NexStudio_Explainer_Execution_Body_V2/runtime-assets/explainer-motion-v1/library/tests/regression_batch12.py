from pathlib import Path
import subprocess,json,sys,time
root=Path(__file__).resolve().parents[1]
scripts=['smoke_objects.py','smoke_motion.py','smoke_icons.py','smoke_creator_icons.py','smoke_agent_icons.py','smoke_business_icons.py','smoke_typography.py','smoke_media_containers.py','smoke_data_visualisations.py','smoke_creator_modules.py']
results={};errors=[]
for s in scripts:
 t=time.time();p=subprocess.run(['python3',str(root/'tests'/s)],cwd=root,text=True,capture_output=True,timeout=75);results[s]={'status':'PASS' if p.returncode==0 else 'FAIL','seconds':round(time.time()-t,2),'returnCode':p.returncode,'tail':(p.stdout+p.stderr)[-1000:]}
 if p.returncode!=0:errors.append(s)
report={'status':'PASS' if not errors else 'FAIL','suites':len(scripts),'passed':len(scripts)-len(errors),'results':results,'errors':errors};(root/'reports/batch12-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'suites':report['suites'],'passed':report['passed'],'errors':errors},indent=2));sys.exit(1 if errors else 0)
