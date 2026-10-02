import bpy,os
_ST=os.environ.get('STONE','')
if _ST:
    _l=lambda c:(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4)
    B=[_l(int(_ST.lstrip('#')[i:i+2],16)/255) for i in (0,2,4)]
    nt=bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.nodes
    mi=[i for i in nt['Mix'].inputs if i.enabled and i.type=='RGBA']
    a0=list(mi[0].default_value)[:3]; b0=list(mi[1].default_value)[:3]
    r=[a/b for a,b in zip(a0,b0)]
    mi[1].default_value=(*B,1); mi[0].default_value=(*[x*k for x,k in zip(B,r)],1)
    bl=[i for i in nt['Mix.001'].inputs if i.enabled and i.type=='RGBA' and not i.is_linked][0]
    bl.default_value=(*[x*k for x,k in zip(B,(0.89,0.54,0.63))],1)
    for mn,k in (('LINEART_SKIN_WHITE',(1,1,1)),('V60_EAR_SKIN',(0.80,0.71,0.70))):
        m=bpy.data.materials.get(mn)
        if m: m.node_tree.nodes['Emission'].inputs['Color'].default_value=(*[x*q for x,q in zip(B,k)],1)
    print('STONE',_ST,[round(x,3) for x in B],'shade',[round(x,3) for x in r])
