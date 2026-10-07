import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import numpy as np, cv2, math, json, cairosvg
from lxml import etree

ROOT=Path(os.environ.get('OPEN_PEEPS_SOURCE_ROOT','.'))
SRC=ROOT/'extracted/Flat Assets/Templates/Standing/peep-standing-20.svg'
OUT=Path(os.environ.get('OPEN_PEEPS_RIG_OUT','OPEN_PEEPS_ARTICULATED_RIG_V6'))
(OUT/'REVIEW_V6/raw').mkdir(parents=True,exist_ok=True)
(OUT/'runtime').mkdir(parents=True,exist_ok=True)
(OUT/'QA').mkdir(parents=True,exist_ok=True)
S=4
SW,SH=213,706
CW,CH=440,790
OX,OY=110,40
W,H=CW*S,CH*S
srcpng=ROOT/'peep20_v6_rgba.png'
if not srcpng.exists(): cairosvg.svg2png(url=str(SRC),write_to=str(srcpng),output_width=SW*S,output_height=SH*S)
base=Image.open(srcpng).convert('RGBA')

# Core: authored head/torso/lower body without frozen source arms.
coremask=Image.new('L',base.size,0); md=ImageDraw.Draw(coremask)
md.polygon([(48*S,0),(166*S,0),(166*S,133*S),(48*S,133*S)],fill=255)
md.polygon([(48*S,119*S),(166*S,119*S),(171*S,151*S),(168*S,235*S),(173*S,350*S),(141*S,370*S),(114*S,356*S),(88*S,370*S),(50*S,351*S),(53*S,235*S),(48*S,151*S)],fill=255)
md.rectangle((0,342*S,213*S,706*S),fill=255)
core=base.copy();core.putalpha(Image.fromarray(np.minimum(np.array(base.getchannel('A')),np.array(coremask)).astype(np.uint8)))

J={'ls':(58,153),'le':(47,255),'lw':(54,354),'rs':(164,153),'re':(183,255),'rw':(184,354)}
def rotvec(v,a):
 r=math.radians(a);c=math.cos(r);s=math.sin(r);return (c*v[0]-s*v[1],s*v[0]+c*v[1])
def fk(side,a,b):
 sh,el,wr=(J['ls'],J['le'],J['lw']) if side=='l' else (J['rs'],J['re'],J['rw'])
 v1=(el[0]-sh[0],el[1]-sh[1]);v2=(wr[0]-el[0],wr[1]-el[1])
 v1=rotvec(v1,a);ep=(sh[0]+v1[0],sh[1]+v1[1]);v2=rotvec(v2,a+b);wp=(ep[0]+v2[0],ep[1]+v2[1])
 return sh,ep,wp,a+b

def render_donor(i):
 p=ROOT/f'extracted/Flat Assets/Templates/Standing/peep-standing-{i}.svg';r=etree.parse(str(p)).getroot();w=int(r.get('width').replace('px',''));h=int(r.get('height').replace('px',''));o=ROOT/f'peep{i}_v6_rgba.png'
 if not o.exists():cairosvg.svg2png(url=str(p),write_to=str(o),output_width=w*S,output_height=h*S)
 return Image.open(o).convert('RGBA')
def crop_poly(im,box,points):
 cr=im.crop(tuple(int(v*S) for v in box));m=Image.new('L',cr.size,0);d=ImageDraw.Draw(m);d.polygon([(x*S,y*S) for x,y in points],fill=255);cr.putalpha(Image.fromarray(np.minimum(np.array(cr.getchannel('A')),np.array(m)).astype(np.uint8)));return cr
# authored hands
relax_r=crop_poly(base,(163,334,213,410),[(0,2),(50,0),(50,76),(0,76)]);relax_anchor=((184-163)*S,(354-334)*S)
p22=render_donor(22);open_r=crop_poly(p22,(220,220,321,305),[(12,25),(101,0),(101,85),(18,85),(0,60)]);open_anchor=(18*S,47*S)
p16=render_donor(16);point_r=crop_poly(p16,(235,145,309,240),[(17,0),(74,0),(74,89),(24,92),(7,68)]);point_anchor=(24*S,73*S)
SPR={'relaxed':(relax_r,relax_anchor),'open':(open_r,open_anchor),'point':(point_r,point_anchor)}

def blank():return Image.new('RGBA',(W,H),(255,255,255,255))
def paste_actor(canvas,actor):canvas.alpha_composite(actor,(OX*S,OY*S))
def A_sprite(im,anchor,target,angle,scale,mirror=False):
 if mirror: im=ImageOps.mirror(im);anchor=(im.width-anchor[0],anchor[1])
 a=math.radians(angle);c=math.cos(a)*scale;s=math.sin(a)*scale
 tx=(OX+target[0])*S;ty=(OY+target[1])*S;ax,ay=anchor
 M=np.array([[c,-s,tx-c*ax+s*ay],[s,c,ty-s*ax-c*ay]],dtype=np.float64)
 arr=cv2.warpAffine(np.array(im),M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0));return Image.fromarray(arr,'RGBA')

def draw_sleeve(canvas,sh,el,wr):
 # absolute working-canvas coords
 P=[((OX+x)*S,(OY+y)*S) for x,y in (sh,el,wr)]
 d=ImageDraw.Draw(canvas)
 # upper sleeve, then lower; large overlap at elbow gives fabric continuity.
 d.line([P[0],P[1]],fill=(0,0,0,255),width=29*S)
 d.ellipse((P[0][0]-15*S,P[0][1]-15*S,P[0][0]+15*S,P[0][1]+15*S),fill=(0,0,0,255))
 d.ellipse((P[1][0]-14*S,P[1][1]-14*S,P[1][0]+14*S,P[1][1]+14*S),fill=(0,0,0,255))
 d.line([P[1],P[2]],fill=(0,0,0,255),width=23*S)
 d.ellipse((P[2][0]-11*S,P[2][1]-11*S,P[2][0]+11*S,P[2][1]+11*S),fill=(0,0,0,255))

def state_image(st):
 c=blank()
 if not any(st.get(k,0) for k in ('la','lb','ra','rb')):
  paste_actor(c,base)
 else:
  paste_actor(c,core)
  # draw arms after core. black sleeves merge into black torso shoulder stubs.
  for side in ('l','r'):
   a=st.get('la',0) if side=='l' else st.get('ra',0);b=st.get('lb',0) if side=='l' else st.get('rb',0)
   if not (a or b):
    # preserve source arm when inactive via a cropped strip from original to avoid amputating idle arm.
    # use transparent source arm crop, pasted in original location.
    x0,x1=(18,78) if side=='l' else (150,213)
    ar=base.crop((x0*S,130*S,x1*S,410*S));c.alpha_composite(ar,((OX+x0)*S,(OY+130)*S));continue
   sh,el,wr,ang=fk(side,a,b);draw_sleeve(c,sh,el,wr)
   ht=st.get(side+'_hand','open');sp,anc=SPR[ht]
   # semantic hand artwork has its own authored orientation, adjusted relative to forearm.
   orient={'open':0,'point':-35,'relaxed':90}[ht];scale={'open':0.42,'point':0.47,'relaxed':0.76}[ht]
   c=Image.alpha_composite(c,A_sprite(sp,anc,wr,ang+orient,scale,mirror=(side=='l')))
 # mild actor lean
 if st.get('lean'):
  deg=st['lean'];cx=(OX+108)*S;cy=(OY+350)*S;r=math.radians(deg);co=math.cos(r);si=math.sin(r);M=np.array([[co,-si,cx-co*cx+si*cy],[si,co,cy-si*cx-co*cy]])
  c=Image.fromarray(cv2.warpAffine(np.array(c),M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255,255)),'RGBA')
 return c.convert('RGB')

STATES={
'neutral':{},'listen':{'lean':-2},
'explain_right':{'ra':-55,'rb':48,'r_hand':'open'},
'explain_left':{'la':55,'lb':-48,'l_hand':'open'},
'two_hand_explain':{'la':48,'lb':-40,'ra':-48,'rb':40,'l_hand':'open','r_hand':'open'},
'point':{'ra':-70,'rb':30,'r_hand':'point'},
'emphasis':{'ra':-38,'rb':22,'r_hand':'open'},'lean':{'lean':6}}
for n,s in STATES.items():state_image(s).save(OUT/'REVIEW_V6/raw'/f'{n}.png')
(OUT/'runtime/open_peeps_conventional_rig_v6.py').write_text(Path(__file__).read_text())
(OUT/'runtime/OPEN_PEEPS_RIG_V6_CONTRACT.json').write_text(json.dumps({'schema':'OpenPeepsConventionalRigV6','source':'peep-standing-20.svg','working_canvas':[CW,CH],'offset':[OX,OY],'joints':J,'states':STATES,'architecture':'authored Open Peeps core + two-bone FK sleeve chains + authored semantic hand sprites','visual_policy':'no primitive torso/head/leg reconstruction; only sleeve geometry is reauthored to support articulation'},indent=2))
