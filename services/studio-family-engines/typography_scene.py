"""Validate and bind explicit typography geometry; never interpret Art prose as layout."""
from copy import deepcopy
import math
import re
from canonical import stable
from contracts import AdapterBlocked, require_review_board

SCHEMA = 'StudioTypographySceneGraphV1'
PROPERTIES = {'x':(0,1),'y':(0,1),'opacity':(0,1),'blur':(0,30),
              'fontSize':(.005,.5),'brightness':(.2,1.2),'scale':(.1,3)}
EASES = {'linear','easeInOut','easeOut','hold'}

def fail(detail):
    raise AdapterBlocked('EDITORIAL_TYPOGRAPHY_CONTRACT_INVALID',detail)

def number(value,low,high,label):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        fail(label)

def keys(value,required,optional,label):
    if not isinstance(value,dict) or not required<=value.keys() or value.keys()-required-optional:
        fail(label)

def bind_typography_scene(board,contract):
    if contract is None: return None
    beats=require_review_board(board)
    keys(contract,{'schema','sourceBoardHash','nodes','tracks','supportBindings','actionBindings','soundSync'},
         {'sourceArtHash','contractHash','authoring'},'contract fields')
    if contract['schema']!=SCHEMA or contract['sourceBoardHash']!=stable(board): fail('source board binding')
    if contract.get('contractHash') and contract['contractHash']!=stable({k:v for k,v in contract.items() if k!='contractHash'}): fail('contract hash')
    art=board.get('authored_art') or {}
    if contract.get('sourceArtHash') and contract['sourceArtHash']!=stable(art): fail('source Art binding')
    form=art.get('form_request') or {}
    parts=form.get('semantic_parts') or []
    if not parts or not all(isinstance(part,str) and part for part in parts): fail('explicit authored semantic parts required')
    copy_source=' '.join(parts)
    scenes=[];cursor=0.
    for beat in beats:
        edit=beat['editorial'];start=edit['start'];duration=edit['duration']
        st=float(start['value'])/float(start['rate']);dur=float(duration['value'])/float(duration['rate'])
        if not math.isfinite(st+dur) or dur<=0 or abs(st-cursor)>.001: fail('contiguous canonical timing')
        if (beat.get('camera') or {}).get('camera_atom',{}).get('atom')!='HOLD': fail('moving camera needs explicit native binding')
        for action in beat['motion_actions']:
            if action.get('performer_class')!='SCENE_GRAPH': fail('non-native performer')
            verb=(action.get('execution') or {}).get('resolved_verb') or action.get('requested_verb')
            if verb not in {'TYPE_REVEAL','REVEAL','HIGHLIGHT','DE_EMPHASIZE','SETTLE','STATE_CHANGE','REFRAME_CONTENT'}: fail('unsupported motion verb')
        scenes.append({'beatId':beat['beat_id'],'start':st,'end':st+dur,
                       'actionIds':[a['action_id'] for a in beat['motion_actions']],
                       'adapterTrace':{'sourceBeatId':beat['beat_id'],'creativeChoiceIntroduced':False}})
        cursor+=dur
    if not isinstance(contract['nodes'],list) or not 1<=len(contract['nodes'])<=40: fail('node count')
    nodes={};used_parts=set()
    for node in contract['nodes']:
        keys(node,{'id','kind','sourcePart','x','y','width','height','color','opacity'},
             {'text','font','fontSize','weight','align','blur','brightness','scale','grain','seed','deboss'},'node fields')
        ident=node['id']
        if not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}',ident) or ident in nodes: fail('unique node ID')
        if node['sourcePart'] not in parts: fail('node sourcePart is not authored Art')
        used_parts.add(node['sourcePart'])
        if not isinstance(node['kind'],str) or node['kind'] not in {'text','paper','rule','dot'}: fail('unsupported primitive')
        for prop in ('x','y','width','height','opacity'): number(node[prop],0,1,ident+':'+prop)
        if node['width']<=0 or node['height']<=0 or node['x']+node['width']>1.001 or node['y']+node['height']>1.001: fail('node rectangle outside canvas')
        if not isinstance(node['color'],str) or not re.fullmatch(r'#[a-fA-F0-9]{6}',node['color']): fail('hex color required')
        for prop in ('blur','brightness','scale','fontSize'):
            if prop in node: number(node[prop],*PROPERTIES[prop],ident+':'+prop)
        if node['kind']=='text':
            if not isinstance(node.get('text'),str) or not node['text'] or node['text'] not in copy_source: fail('display copy must be verbatim authored Art')
            if not isinstance(node.get('font'),str) or node.get('font') not in {'didone','sans','mono'}: fail('known font required')
            number(node.get('fontSize'),.005,.5,'fontSize')
            number(node.get('weight',400),100,900,'weight')
            if node.get('align','left') not in {'left','center','right'}: fail('text alignment')
        if 'grain' in node: number(node['grain'],0,.15,'grain')
        if 'seed' in node: number(node['seed'],0,65535,'seed')
        if 'deboss' in node and not isinstance(node['deboss'],bool): fail('deboss')
        nodes[ident]=node
    if used_parts!=set(parts): fail('authored semantic part omitted')
    if not isinstance(contract['tracks'],list) or len(contract['tracks'])>200: fail('track count')
    seen=set()
    for track in contract['tracks']:
        keys(track,{'nodeId','property','keys'},set(),'track fields')
        if not isinstance(track['nodeId'],str) or not isinstance(track['property'],str): fail('track identity')
        pair=(track['nodeId'],track['property'])
        if pair in seen or pair[0] not in nodes or pair[1] not in PROPERTIES: fail('duplicate or unsupported track')
        seen.add(pair)
        frames=track['keys']
        if not isinstance(frames,list) or not 1<=len(frames)<=80: fail('keyframe count')
        previous=-1.
        for key in frames:
            keys(key,{'time','value','ease'},set(),'keyframe fields')
            number(key['time'],0,cursor,'key time')
            number(key['value'],*PROPERTIES[pair[1]],'key value')
            if key['time']<=previous or key['ease'] not in EASES: fail('ordered distinct keyframes and known easing')
            previous=key['time']
    expected={(b['beat_id'],label) for b in beats for label in b.get('supporting_assets') or []}
    if not isinstance(contract['supportBindings'],list) or not isinstance(contract['actionBindings'],list): fail('binding lists required')
    bound=set()
    for binding in contract['supportBindings']:
        keys(binding,{'beatId','sourceLabel','nodeIds'},set(),'support binding')
        if not isinstance(binding['beatId'],str) or not isinstance(binding['sourceLabel'],str) or not isinstance(binding['nodeIds'],list) or not all(isinstance(i,str) for i in binding['nodeIds']): fail('support binding types')
        pair=(binding['beatId'],binding['sourceLabel'])
        if pair not in expected or pair in bound or not binding['nodeIds'] or any(i not in nodes for i in binding['nodeIds']): fail('support binding identity')
        bound.add(pair)
    if bound!=expected: fail('support omitted')
    expected_actions={a['action_id'] for b in beats for a in b['motion_actions']}
    bound_actions=set()
    for binding in contract['actionBindings']:
        keys(binding,{'actionId','nodeIds'},set(),'action binding')
        if not isinstance(binding['actionId'],str) or not isinstance(binding['nodeIds'],list) or not all(isinstance(i,str) for i in binding['nodeIds']): fail('action binding types')
        if binding['actionId'] not in expected_actions or binding['actionId'] in bound_actions or not binding['nodeIds'] or any(i not in nodes for i in binding['nodeIds']): fail('action binding identity')
        bound_actions.add(binding['actionId'])
    if bound_actions!=expected_actions: fail('motion action omitted')
    expected_sound={e['event_id']:(b,e,s) for b,s in zip(beats,scenes) for e in b.get('sound_events') or [] if e['kind']!='SILENCE'}
    if not isinstance(contract['soundSync'],dict) or set(contract['soundSync'])!=set(expected_sound): fail('sound event omitted')
    bound_sound=deepcopy(contract['soundSync'])
    for ident,binding in contract['soundSync'].items():
        keys(binding,{'syncTarget','sourceBeatId','at'}, {'end','fadeIn','fadeOut'},'sound binding')
        beat,event,scene=expected_sound[ident]
        if binding['syncTarget']!=event['sync_target'] or binding['sourceBeatId']!=beat['beat_id']: fail('sound source changed')
        number(binding['at'],scene['start'],scene['end']-1e-6,'sound time')
        target=str(event['sync_target'])
        match=re.search(r'\baction_frame\s+(\d+)',target)
        if match:
            rate=beat['editorial']['duration']['rate'];local=int(match.group(1))/rate
            if abs(binding['at']-(scene['start']+local))>1e-4: fail('sound action frame changed')
            bound_sound[ident]['at']=scene['start']+local
        elif re.search(r'\bonset at frame 0\b',target) and abs(binding['at']-scene['start'])>1e-4: fail('sound onset changed')
        if 'end' in binding: number(binding['end'],binding['at']+1e-6,scene['end'],'sound end')
        for prop in ('fadeIn','fadeOut'):
            if prop in binding: number(binding[prop],0,binding.get('end',scene['end'])-binding['at'],'sound fade')
        if binding.get('fadeOut') and 'end' not in binding: fail('fade out requires end')
    spec=deepcopy(contract)
    spec['soundSync']=bound_sound
    spec.update({'duration':cursor,'scenes':scenes,'sourceArtHash':stable(art)})
    spec['renderBindingHash']=stable(spec)
    return spec
