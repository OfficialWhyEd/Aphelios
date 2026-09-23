# -*- coding: utf-8 -*-
"""Pose prese DIRETTAMENTE dalla griglia approvata (out/griglia/02-vettori-a.jpg), senza ritocchi.
Per ogni cella: ingrandimento 9,5x con bordi netti (come la base), poi:
- gli occhi (buchi bianchi nella meta' alta) diventano pezzi separati, cosi' possono crescere e sbattere;
- il disegno con i buchi riempiti e' il corpo della posa (testa compresa: e' quella disegnata);
- tutto viene allineato: centro x a 512, piedi a 985 (stessa scala della base, e' lo stesso foglio).
Uscita: rig/pose/<nome>.png, rig/pose/<nome>-occhio-N.png, rig/pose/geometria.json, rig/pose/_verifica.png."""
from PIL import Image
import numpy as np, cv2, json, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs("rig/pose",exist_ok=True)
S=3; K=9.5; CX=512; FEET=985
geo=json.load(open("rig/pezzi-base/geometria.json")); EL=geo["occhio-sx"]; ER=geo["occhio-dx"]; EYE_Y=(EL["y"]+EL["h"]/2+ER["y"]+ER["h"]/2)/2
GRIDS={"out/griglia/02-vettori-a.jpg":["saluta","piange","indica","stordito","base","mazza","innamorato","biscotto","sbircia"],
       "out/griglia/04-vettori-quotidiano-a.jpg":["seduto","laptop","cuffie","caffe","pensa","gioca","dorme","esulta","corre"],
       "out/griglia/05-camminata-a.png":["cammina1","cammina2","cammina3","cammina4","cammina5","cammina6","corre1","corre2","corre3"],
       "out/griglia/06-intere-a.png":["saluta2","piange2","innamorato2","boh","salta","scocciato","indica2","pollice","fiero"]}
CELLS={}
for f,names in GRIDS.items():
    img=np.array(Image.open(f).convert("L")).astype(np.float32)
    # ogni macchia nera va alla cella in cui cade il suo baricentro: cosi' i piedi che sconfinano nella cella sotto
    # restano con la loro posa e non sporcano quella sotto
    cell=img.shape[0]/3
    nb,lb,stb,cen=cv2.connectedComponentsWithStats((img<128).astype(np.uint8),8)
    owner=np.full(nb,-1,int)
    for k in range(1,nb):
        cx_,cy_=cen[k]; owner[k]=int(cy_//cell)*3+int(cx_//cell)
        # roba che sconfina dalla cella sopra (l'ombra del salto nel foglio 06): il baricentro sta nel primo 10% della cella
        if "06-intere" in f and (cy_%cell)<cell*0.10 and stb[k][3]<cell*0.08: owner[k]=-1
    for i,n in enumerate(names):
        mask=np.isin(lb,np.where(owner==i)[0]); CELLS[n]=(np.where(mask,img,255.0),i,1024/img.shape[0])
ORDER=["base"]+[n for n in CELLS if n!="base"]
def crisp(src,k=K):
    big=cv2.resize(src,None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC); big=cv2.GaussianBlur(big,(0,0),0.5*k)   # sfocatura proporzionale all'ingrandimento, poi soglia dura: bordi lisci
    return np.clip((big-128)*8+128,0,255)
def salva(path,a3,col):
    a3=np.where(a3<48,0,a3); ys,xs=np.where(a3>0); x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    c=a3[y0:y1,x0:x1].astype(np.uint8); rgba=np.zeros((c.shape[0],c.shape[1],4),np.uint8); rgba[...,:3]=col; rgba[...,3]=c
    im=Image.fromarray(rgba); im=im.resize((max(1,round(im.width*2/3)),max(1,round(im.height*2/3))),Image.LANCZOS)   # salvo a 2x: basta e pesa la meta'
    im.save(path); return dict(x=x0/S,y=y0/S,w=(x1-x0)/S,h=(y1-y0)/S)
out={}
sheet=Image.new("RGB",(3*400,12*400),(237,235,230))
for name in ORDER:
    a,i,kk=CELLS[name]; gi=list(GRIDS).index([f for f,ns in GRIDS.items() if name in ns][0]); r,c=divmod(i,3)
    ys,xs=np.where(a<128); sub=a; bx0,by0,bx1,by1=max(0,xs.min()-8),max(0,ys.min()-8),xs.max()+9,ys.max()+9
    P=crisp(255-sub[by0:by1,bx0:bx1],K*kk); B=P>128
    # per la sbircia il muro e' una riga verticale a destra: la tolgo dal calcolo del centro (resta nel disegno)
    cols=B.sum(axis=0); body_cols=np.where(cols>B.shape[0]*0.15)[0] if name=="sbircia" else np.where(cols>0)[0]
    if name=="sbircia":
        # il muro e' la colonna piu' lunga: centro sul personaggio (colonne con almeno il 15% di nero, escluso il muro)
        wall=np.argmax(cols); body_cols=body_cols[np.abs(body_cols-wall)>4*S]
    # occhi nella cella: le due componenti bianche chiuse piu' grandi nella meta' alta
    def buchi(Bm,top,mid,minarea=600):
        n,lab,st,_=cv2.connectedComponentsWithStats((~Bm).astype(np.uint8),4); H_,W_=Bm.shape
        hs=[k for k in range(1,n) if st[k][0]>0 and st[k][1]>0 and st[k][0]+st[k][2]<W_ and st[k][1]+st[k][3]<H_ and st[k][4]>minarea and top<st[k][1]<mid]
        return sorted(hs,key=lambda k:st[k][0]),lab,st
    hs,lab0,st0=buchi(B,0,B.shape[0]*0.55)
    big2=sorted(hs,key=lambda k:-st0[k][4])[:2]
    ecx=np.mean([st0[k][0]+st0[k][2]/2 for k in big2]); ecy=np.mean([st0[k][1]+st0[k][3]/2 for k in big2])
    # larghezza della testa alla riga degli occhi (il tratto nero che contiene gli occhi): serve a riportare
    # ogni posa alla scala della testa base (i disegni della griglia hanno teste leggermente diverse)
    eh=max(st0[k][3] for k in big2); row=B[int(ecy-0.85*eh)]; xs_=np.where(row)[0]; cuts=np.where(np.diff(xs_)>1)[0]; starts=np.r_[xs_[0],xs_[cuts+1]]; ends=np.r_[xs_[cuts],xs_[-1]]
    seg=[(s0,e0) for s0,e0 in zip(starts,ends) if s0<=ecx<=e0] or [(xs_.min(),xs_.max())]
    hw=seg[0][1]-seg[0][0]
    if name=="base": HW0=hw
    OVER={"stordito":1.0,"mazza":0.95,"sbircia":0.96, **{f"cammina{i}":1.0 for i in range(1,7)}, **{f"corre{i}":1.0 for i in range(1,4)}}   # teste inclinate: la misura per riga non vale, valori a occhio
    sc=OVER.get(name, HW0/hw); sc=float(np.clip(sc,0.85,1.15))
    sc=min(sc, 1000*S/P.shape[1], 1000*S/P.shape[0])   # le pose larghe (corre, dorme, laptop) devono stare nel quadro
    if abs(sc-1)<0.01: sc=1.0
    if sc!=1.0: P=cv2.resize(P,None,fx=sc,fy=sc,interpolation=cv2.INTER_AREA); ecx*=sc; ecy*=sc
    print(name,"testa",hw/S,"scala",round(sc,3))
    # allineo il centro degli occhi a quello della base: cosi' la testa non salta cambiando posa
    canvas=np.zeros((1024*S,1024*S),np.float32)
    bw_=np.where((P>128).any(axis=0))[0]; ox=int(round(CX*S-(bw_.min()+bw_.max())/2)); oy=int(round(EYE_Y*S-ecy))   # x: centro del disegno; y: occhi come la base
    if name.startswith(("cammina","corre")) and name!="corre": oy=int(round(FEET*S-np.where((P>128).any(axis=1))[0].max()))   # fotogrammi di ciclo: piedi a terra
    oy=int(np.clip(oy, 12*S-0, 1012*S-P.shape[0]))   # se sfora in basso o in alto, lo sposto
    h3,w3=P.shape; Y0,X0=max(0,oy),max(0,ox); Y1,X1=min(1024*S,oy+h3),min(1024*S,ox+w3)
    canvas[Y0:Y1,X0:X1]=P[Y0-oy:Y1-oy,X0-ox:X1-ox]
    Bc=canvas>128
    # occhi: componenti bianche chiuse nella meta' alta del personaggio
    holes,lab,st=buchi(Bc,oy-1,oy+h3*0.55)
    m=np.zeros(Bc.shape,np.uint8)
    for k in holes: m|=(lab==k).astype(np.uint8)
    filled=np.where(cv2.dilate(m,np.ones((15,15),np.uint8))>0,255.0,canvas)
    g=salva(f"rig/pose/{name}.png",filled,20); g["occhi"]=[]
    for j,k in enumerate(holes):
        reg=np.where(lab==k,255.0,0.0); reg=cv2.GaussianBlur(reg,(0,0),0.8)
        g["occhi"].append(salva(f"rig/pose/{name}-occhio-{j}.png",reg,255))
    out[name]=g; print(name,"occhi",len(holes))
    # verifica
    v=Image.new("RGBA",(1024,1024),(237,235,230,255))
    bi=Image.open(f"rig/pose/{name}.png"); v.alpha_composite(bi.resize((int(round(g["w"])),int(round(g["h"]))),Image.LANCZOS),(int(round(g["x"])),int(round(g["y"]))))
    for j,e in enumerate(g["occhi"]):
        ei=Image.open(f"rig/pose/{name}-occhio-{j}.png"); v.alpha_composite(ei.resize((max(1,int(round(e["w"]))),max(1,int(round(e["h"])))),Image.LANCZOS),(int(round(e["x"])),int(round(e["y"]))))
    sheet.paste(v.convert("RGB").resize((400,400),Image.LANCZOS),(c*400,(r+3*gi)*400))
json.dump(out,open("rig/pose/geometria.json","w"),indent=1)
sheet.save("rig/pose/_verifica.png"); print("ok")
