"""Opt-in garment edge construction on the existing rigged meshes.

Sub-millimetre inner shells give open collars, cuffs and hems physical edges.
No source mesh, weights or character geometry is rewritten.
"""
import bpy,os
structure_report=[]
if os.environ.get('CAST_GARMENT_STRUCTURE_PILOT')=='1':
    names=[x.split('=')[0] for x in os.environ.get('GARMS','').split(';') if x]
    if os.environ['CAST_CHARACTER']=='female':names=[os.environ['DOBJ']]
    for name in names:
        ob=bpy.data.objects.get(name)
        if ob is None or ob.type!='MESH' or any(k in name.lower() for k in ('shoe','sneaker')):continue
        shell=ob.modifiers.get('Cast garment edge thickness') or ob.modifiers.new('Cast garment edge thickness','SOLIDIFY')
        shell.thickness=0.0008
        shell.offset=-1.0
        shell.use_even_offset=True
        shell.use_quality_normals=True
        shell.use_rim=True
        structure_report.append({'object':name,'thicknessMetres':shell.thickness,'afterRigAndSubdivision':True})
