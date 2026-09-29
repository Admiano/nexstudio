_E=lambda k,d: float(os.environ.get(k,d))
_nt=bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.nodes
_s=_E('SKS','1.0')
_a=_nt['Mix'].inputs[6].default_value; _b=_nt['Mix'].inputs[7].default_value
_nt['Mix'].inputs[6].default_value=tuple(_b[i]-(_b[i]-_a[i])*_E('SKL','2.6') for i in range(3))+(1,)
_nt['Mix.006'].inputs[7].default_value=(_E('TR','0.80'),_E('TG','0.62'),_E('TB','0.57'),1)
_nt['Math.001'].inputs[1].default_value=_E('TF','1.0')
_nt['Math'].inputs[1].default_value=_E('BL','0.42')
print('SKIN',tuple(round(x,3) for x in _nt['Mix'].inputs[6].default_value))
_mr=_nt['Map Range']; _mr.inputs['From Min'].default_value=_E('MR0','-0.05'); _mr.inputs['From Max'].default_value=_E('MR1','0.08')
print('SKIN2',_mr.inputs['From Min'].default_value,_mr.inputs['From Max'].default_value)
_vm=_nt['Vector Math']
_lv=np.array([_E('LVX','-0.35'),_E('LVY','-0.75'),_E('LVZ','0.56')]); _lv/=np.linalg.norm(_lv)
_vm.inputs[1].default_value=tuple(_lv)
bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.links.new(_vm.outputs['Value'],_nt['Map Range'].inputs['Value'])
print('SKIN3',_vm.operation,tuple(round(x,3) for x in _lv))
