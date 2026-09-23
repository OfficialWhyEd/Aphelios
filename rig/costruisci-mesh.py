# -*- coding: utf-8 -*-
"""Rig a mesh con ossa e pesi (skinning) per il corpo di Aphelios.
Ogni pezzo (busto, braccio alto, avambraccio, gambe) diventa una griglia di triangoli con la sua texture;
i vertici vicino ai giunti mescolano due ossa: le pieghe sono morbide, niente snodi a palla.
Legge rig/pezzi-base/*.png + geometria.json (da taglia-pezzi.py). Scrive rig/mesh/aphelios-mesh.json
e rig/mesh/_verifica-mesh.png (anteprima delle griglie e dei pesi)."""
from PIL import Image, ImageDraw
import numpy as np, json, os, cv2
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs("rig/mesh",exist_ok=True)
S=3
geo=json.load(open("rig/pezzi-base/geometria.json")); M=geo["meta"]
CELL=8
D3=np.load("rig/pezzi-base/_D3.npy")   # la sagoma intera del disegno a 3x (da taglia-pezzi.py)
OVER=4*S                                # quanto ogni pezzo entra nel vicino (4 px a 1x)
# ossa: nome, genitore, perno (coordinate scena 1x, posa di riposo)
hips=M["hips"]; pelvis=[512.0, M["notchTop"]-6]
BONES=[
 ("root",None,pelvis),
 ("spine","root",pelvis),
 ("upperL","spine",M["pivots"]["spalla-sx"]), ("foreL","upperL",geo["gomito-sx"]),
 ("upperR","spine",M["pivots"]["spalla-dx"]), ("foreR","upperR",geo["gomito-dx"]),
 ("legL","root",hips[0]), ("legR","root",hips[1]),
]
BI={b[0]:i for i,b in enumerate(BONES)}
aw=M["armW"]
# giunti: (osso genitore, osso figlio, centro, raggio di fusione)
JOINTS=[("spine","upperL",M["pivots"]["spalla-sx"],aw*1.0),("upperL","foreL",geo["gomito-sx"],aw*1.5),
        ("spine","upperR",M["pivots"]["spalla-dx"],aw*1.0),("upperR","foreR",geo["gomito-dx"],aw*1.5),
        ("root","legL",hips[0],34),("root","legR",hips[1],34)]
PIECES=[("gamba-sx","legL"),("gamba-dx","legR"),("busto","spine"),("braccio-sx","upperL"),("braccio-dx","upperR")]
ARM={"upperL":("foreL",M["pivots"]["spalla-sx"],geo["gomito-sx"],"braccio-sx"),"upperR":("foreR",M["pivots"]["spalla-dx"],geo["gomito-dx"],"braccio-dx")}
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def hand_of(name):
    g=geo[name]; im=np.array(Image.open(f"rig/pezzi-base/{name}.png"))[...,3]>128
    ys,xs=np.where(im); yb=ys.max(); row=xs[ys>yb-3*S*2]; return [g["x"]+row.mean()/S, g["y"]+yb/S]
def arm_weights(Vs, up, torso=False):
    """peso del braccio alto e dell'avambraccio in funzione della posizione (uguale per busto e braccio:
    cosi' la pelle della spalla si muove insieme al braccio senza cuciture)."""
    fore,piv,elb,nm=ARM[up]; piv=np.array(piv,np.float32); elb=np.array(elb,np.float32); hand=np.array(hand_of(nm),np.float32)
    u=elb-piv; u/=np.linalg.norm(u); n=np.array([-u[1],u[0]],np.float32)
    d=(Vs-piv)@u; l=np.abs((Vs-piv)@n)
    a=smooth(-aw*0.7,aw*0.7,d)                                      # quanto segue il braccio (vs busto)
    if torso: a=smooth(-aw*0.5,aw*0.5,d)*(1-smooth(aw*0.35,aw*0.6,l))*(1-smooth(0,aw*0.5,d))   # nel busto solo la pelle sotto la radice del braccio
    u2=hand-elb; u2/=np.linalg.norm(u2); d2=(Vs-elb)@u2
    f=smooth(-aw*1.3,aw*1.3,d2)                                     # quanto segue l'avambraccio (vs braccio alto)
    return a,f
out=dict(bones=[dict(name=n,parent=(BI[p] if p else -1),pivot=[float(pv[0]),float(pv[1])]) for n,p,pv in BONES],pieces=[])
prev=Image.new("RGB",(1024,1024),(237,235,230)); dr=ImageDraw.Draw(prev)
COL={"spine":(60,60,60),"upperL":(30,120,255),"foreL":(0,190,230),"upperR":(255,60,60),"foreR":(255,150,0),"legL":(0,170,90),"legR":(140,60,200),"root":(0,0,0)}
def blend(c1,c2,t): return tuple(int(a*(1-t)+b*t) for a,b in zip(c1,c2))
for name,bone in PIECES:
    g=geo[name]; im=np.array(Image.open(f"rig/pezzi-base/{name}.png"))[...,3]
    # ogni pezzo entra di qualche pixel nei vicini, ma solo DENTRO la sagoma del disegno: sul taglio fra due pezzi
    # il nero e' pieno da tutte e due le parti (niente riga chiara), mentre il contorno vero resta quello disegnato
    bx0,by0=int(round(g["x"]*S)),int(round(g["y"]*S)); sil=D3[by0:by0+im.shape[0],bx0:bx0+im.shape[1]]>200
    grow=cv2.dilate((im>128).astype(np.uint8),np.ones((2*OVER+1,2*OVER+1),np.uint8))>0
    im=np.maximum(im,np.where(grow&sil,255,0).astype(np.uint8))
    # texture con bordo trasparente (PAD px a 3x): il clamp ai bordi non sbava l'alpha fuori dal pezzo
    PAD=6; rgba=np.zeros((im.shape[0]+2*PAD,im.shape[1]+2*PAD,4),np.uint8); rgba[...,:3]=20; rgba[PAD:-PAD,PAD:-PAD,3]=im
    Image.fromarray(rgba).save(f"rig/mesh/tex-{name}.png"); TW,TH=rgba.shape[1],rgba.shape[0]
    a1=cv2.resize(im,(int(round(g["w"])),int(round(g["h"]))),interpolation=cv2.INTER_AREA)>16   # maschera 1x del pezzo
    a1=cv2.dilate(a1.astype(np.uint8),np.ones((CELL+3,CELL+3),np.uint8))>0
    h1,w1=a1.shape
    xs=np.arange(0,w1+CELL,CELL); ys=np.arange(0,h1+CELL,CELL)
    idx={}; V=[]
    for j,y in enumerate(ys):
        for i,x in enumerate(xs):
            if a1[min(h1-1,y),min(w1-1,x)]: idx[(i,j)]=len(V); V.append((x,y))
    T=[]
    for j in range(len(ys)-1):
        for i in range(len(xs)-1):
            q=[idx.get(k) for k in ((i,j),(i+1,j),(i,j+1),(i+1,j+1))]
            a,b,c,d=q
            if None not in q: T+= [(a,b,c),(b,d,c)]
            else:
                for tri in ((a,b,c),(b,d,c),(a,b,d),(a,d,c)):
                    if None not in tri: T.append(tri); break
    V=np.array(V,np.float32); Vs=V+np.array([g["x"],g["y"]],np.float32)   # coordinate scena
    uv=np.stack([(V[:,0]*S+PAD)/TW,(V[:,1]*S+PAD)/TH],axis=1)
    # pesi (fino a 4 ossa per vertice)
    NB=4; bi=np.zeros((len(V),NB),np.int32); bw=np.zeros((len(V),NB),np.float32)
    if bone in ("legL","legR"):
        c=np.array(BONES[BI[bone]][2],np.float32); d=np.linalg.norm(Vs-c,axis=1); t=np.clip(d/34,0,1); wo=0.5*(1-t)**2
        bi[:,0]=BI[bone]; bw[:,0]=1-wo; bi[:,1]=BI["root"]; bw[:,1]=wo
    elif bone=="spine":
        w=np.zeros((len(V),len(BONES)),np.float32); w[:,BI["spine"]]=1
        for up in ("upperL","upperR"):
            a,f=arm_weights(Vs,up,torso=True); fore=ARM[up][0]
            w[:,BI[up]]+=a*(1-f); w[:,BI[fore]]+=a*f; w[:,BI["spine"]]-=a
        for lg in ("legL","legR"):
            c=np.array(BONES[BI[lg]][2],np.float32); d=np.linalg.norm(Vs-c,axis=1); t=np.clip(d/34,0,1); wo=0.5*(1-t)**2
            w[:,BI[lg]]+=wo; w[:,BI["spine"]]-=wo
        order=np.argsort(-w,axis=1)[:,:NB]; bi=order.astype(np.int32); bw=np.take_along_axis(w,order,axis=1)
    else:
        a,f=arm_weights(Vs,bone); fore=ARM[bone][0]
        bi[:,0]=BI[bone]; bw[:,0]=a*(1-f); bi[:,1]=BI[fore]; bw[:,1]=a*f; bi[:,2]=BI["spine"]; bw[:,2]=1-a
    bw=np.clip(bw,0,1); bw/=bw.sum(axis=1,keepdims=True)
    out["pieces"].append(dict(name=name,tex="tex-"+name,geo=g,verts=Vs.round(2).flatten().tolist(),uv=uv.round(4).flatten().tolist(),
        tris=[int(v) for tri in T for v in tri],bi=bi.flatten().tolist(),bw=bw.round(4).flatten().tolist()))
    for tri in T: dr.polygon([tuple(Vs[k]) for k in tri],outline=(200,200,200))
    for k,(x,y) in enumerate(Vs):
        c=blend(COL[BONES[bi[k,0]][0]],COL[BONES[bi[k,1]][0]],float(bw[k,1]/max(1e-6,bw[k,0]+bw[k,1]))); dr.ellipse((x-2,y-2,x+2,y+2),fill=c)
    print(name,"vertici",len(V),"triangoli",len(T))
for n,p,pv in BONES:
    dr.ellipse((pv[0]-5,pv[1]-5,pv[0]+5,pv[1]+5),fill=(255,0,255))
    if p: q=BONES[BI[p]][2]; dr.line([tuple(q),tuple(pv)],fill=(255,0,255),width=2)
prev.save("rig/mesh/_verifica-mesh.png")
json.dump(out,open("rig/mesh/aphelios-mesh.json","w"))
print("ok", os.path.getsize("rig/mesh/aphelios-mesh.json"))
