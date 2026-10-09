from pathlib import Path
import subprocess,json,os
root=Path(__file__).resolve().parents[1];reports=root/'reports'
commands=[
 ['npx','hyperframes','lint'],['npx','hyperframes','validate'],['npx','hyperframes','inspect','--samples','15'],['npx','hyperframes','compositions'],['npx','hyperframes','benchmark','.']
]
results=[]
env=os.environ.copy();env['NPM_CONFIG_OFFLINE']='true';env['npm_config_yes']='false'
for cmd in commands:
 try:
  p=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,timeout=25)
  results.append({'command':' '.join(cmd),'exitCode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:],'status':'PASS' if p.returncode==0 else 'UNAVAILABLE'})
 except subprocess.TimeoutExpired as e:
  results.append({'command':' '.join(cmd),'exitCode':None,'stdout':(e.stdout or '')[-4000:] if isinstance(e.stdout,str) else '', 'stderr':(e.stderr or '')[-4000:] if isinstance(e.stderr,str) else '', 'status':'TIMEOUT'})
report={'officialHyperFramesCliAvailable':all(r['exitCode']==0 for r in results),'results':results,'note':'Commands were attempted with npm offline mode to prevent an unreviewed package download. Local deterministic validation is reported separately.'}
(reports/'batch15-official-cli-attempts.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
