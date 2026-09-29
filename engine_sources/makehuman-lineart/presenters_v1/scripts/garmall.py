import os
for _it in [x.split('=') for x in os.environ.get('GARMS','').split(';') if x]:
    _d0=os.environ['DOBJ']; os.environ['DOBJ']=_it[0]; os.environ['DCOL']=_it[1]
    exec(open(__import__('os').environ['PV1']+'/garmart.py').read())
    os.environ['DOBJ']=_d0
