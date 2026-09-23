# -*- coding: utf-8 -*-
"""Taglia i pezzi del rig dal disegno APPROVATO: la cella centrale della griglia vettoriale
(out/griglia/02-vettori-a.jpg, cella 429..600 x 384..665). Il disegno viene ingrandito 9x con
bordi netti (solo preparazione tecnica, nessun ritocco) e messo in una scena 1024x1024 (pezzi a 3x).
Separazioni misurate riga per riga sui solchi bianchi del disegno stesso.
Uscita: rig/pezzi-base/*.png + geometria.json (unita' 1x) + _verifica-braccia.png."""
from PIL import Image
import numpy as np, cv2, json, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S=3                      # pezzi a 3x della scena
K=9.5                    # ingrandimento del disegno sorgente (cella ~191x301 -> ~1720x2710)
a=np.array(Image.open("out/griglia/02-vettori-a.jpg").convert("L")).astype(np.float32)
x0,x1,y0,y1=429,600,384,665; M=12
src=255-a[y0-M:y1+M+1,x0-M:x1+M+1]                       # scuro = alto
big=cv2.resize(src,None,fx=K,fy=K,interpolation=cv2.INTER_CUBIC); big=cv2.GaussianBlur(big,(0,0),4.5)
P=np.clip((big-128)*8+128,0,255)
Ph=(P>128)
ys,xs=np.where(Ph); bx0,bx1,by0,by1=xs.min(),xs.max(),ys.min(),ys.max()
# scena: centro orizzontale a 512, piedi a 985 (unita' 1x)
CX=512; FEET=985
OX=int(round(CX*S-(bx0+bx1)/2)); OY=int(round(FEET*S-by1))
D=np.zeros((1024*S,1024*S),np.float32); D[OY:OY+P.shape[0],OX:OX+P.shape[1]]=P
Dhard=np.where(D>200,255.0,0.0); B=Dhard>0
H3,W3=D.shape
def segs(row):
    xs=np.where(row)[0]
    if len(xs)==0: return []
    cuts=np.where(np.diff(xs)>1)[0]; starts=np.r_[xs[0],xs[cuts+1]]; ends=np.r_[xs[cuts],xs[-1]]
    return list(zip(starts,ends))
# --- misure automatiche (in pixel 3x) ---
top=by0+OY; bot=by1+OY
# occhi: componenti bianche chiuse dentro la sagoma
n,lab,st,_=cv2.connectedComponentsWithStats((~B).astype(np.uint8),4)
holes=[i for i in range(1,n) if st[i][0]>0 and st[i][1]>0 and st[i][0]+st[i][2]<W3 and st[i][1]+st[i][3]<H3 and st[i][4]>2000]
holes=sorted(holes,key=lambda i:st[i][0]); assert len(holes)==2, holes
eyeBot=max(st[i][1]+st[i][3] for i in holes)
# collo: riga piu' stretta fra il fondo degli occhi e le braccia
widths=[(segs(B[y])[-1][1]-segs(B[y])[0][0] if segs(B[y]) else 10**9) for y in range(H3)]
def is_arm_row(s): return len(s)==3 and (s[1][1]-s[1][0])>2.5*max(s[0][1]-s[0][0],s[2][1]-s[2][0])
three=[y for y in range(eyeBot,bot) if is_arm_row(segs(B[y]))]
gapTop,gapBot=three[0],three[-1]
neck=min(range(eyeBot,gapTop),key=lambda y:widths[y])
two=[y for y in range(gapBot+1,bot+1) if len(segs(B[y]))==2]
notchTop=two[0]; split=CX*S   # le gambe si dividono al centro del personaggio
print("collo y",neck/S,"solco braccia",gapTop/S,gapBot/S,"gambe da",notchTop/S,"split x",split/S)
# bordi per riga (3x): braccio esterno->solco, busto
gapL=np.full(H3,np.nan); gapR=np.full(H3,np.nan); tL=np.full(H3,np.nan); tR=np.full(H3,np.nan)
for y in range(gapTop,gapBot+1):
    s=segs(B[y])
    if is_arm_row(s): gapL[y]=s[0][1]; tL[y]=s[1][0]; tR[y]=s[1][1]; gapR[y]=s[2][0]
def fillnan(v):
    idx=np.arange(len(v)); ok=~np.isnan(v); return np.interp(idx,idx[ok],v[ok])
gapL,gapR,tL,tR=map(fillnan,(gapL,gapR,tL,tR))
# sopra il solco: la linea di separazione prosegue dritta verso il collo (pendenza del primo tratto)
def extend_up(v,y_from):
    v=v.copy(); ya=y_from; yb=y_from+18*S; sl=(v[yb]-v[ya])/(yb-ya)
    for y in range(y_from-1,-1,-1): v[y]=v[y_from]+(y-y_from)*sl
    return v
sL=extend_up(gapL,gapTop); sR=extend_up(gapR,gapTop)
# perni: sull'asse del braccio, il piu' in alto possibile tale che la palla della spalla (raggio = meta'
# larghezza del braccio) stia tutta dentro il disegno: cosi' a riposo il disegno e' esatto e in rotazione
# la spalla resta tonda. Il busto ha un disco uguale davanti, che copre sempre la palla.
def axis(y):
    s=segs(B[y]); return (s[0][0]+s[0][1])/2, (s[2][0]+s[2][1])/2
aw=(gapL[gapTop+6*S]-segs(B[gapTop+6*S])[0][0])          # larghezza braccio (3x)
axL0,axR0=axis(gapTop+6*S); axL1,axR1=axis(gapTop+40*S)
Y=np.arange(H3)[:,None]; X=np.arange(W3)[None,:]
def disc(c,r): return np.clip(r-np.sqrt((X-c[0])**2+(Y-c[1])**2)+0.5,0,1)
rBall=aw*0.47
def piv_at(py):
    k=(py-(gapTop+6*S))/(34*S)
    return (axL0+(axL0-axL1)*(-k), py),(axR0+(axR0-axR1)*(-k), py)
# perno della spalla: poco sopra l'inizio del solco, dove la spalla incontra il braccio (la mesh fonde la pelle)
py=gapTop-22*S
pivL,pivR=piv_at(py)
print("larghezza braccio 1x",aw/S,"perni",pivL[0]/S,pivR[0]/S,py/S)
inArm=(Y>=py-2*S)&(Y<=gapBot+2)
# sotto il perno il braccio si allarga dalla palla alla sua larghezza vera con uno smusso: nessun angolo sporge dalla palla
kx=(axL0-axL1)/(34*S)
axLy=pivL[0]-(Y-py)*kx; axRy=pivR[0]+(Y-py)*kx
half=rBall+np.maximum(0,Y-py-2*S)*1.0
mL=(X<=sL[:,None]+2)&inArm&(np.abs(X-axLy)<=half); mR=(X>=sR[:,None]-2)&inArm&(np.abs(X-axRy)<=half)
aL=D*mL; aR=D*mR   # niente palla: la spalla la fonde la mesh (skinning)
geo={}
def salva(name,a3,col=20):
    a3=np.where(a3<48,0,a3); ys,xs=np.where(a3>0); bx0,bx1,by0,by1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    c=a3[by0:by1,bx0:bx1].astype(np.uint8); rgba=np.zeros((c.shape[0],c.shape[1],4),np.uint8); rgba[...,:3]=col; rgba[...,3]=c
    Image.fromarray(rgba).save(f"rig/pezzi-base/{name}.png"); return dict(x=bx0/S,y=by0/S,w=(bx1-bx0)/S,h=(by1-by0)/S)
gL=salva("braccio-sx",aL); gL["px"]=pivL[0]/S-gL["x"]; gL["py"]=pivL[1]/S-gL["y"]; geo["braccio-sx"]=gL
gR=salva("braccio-dx",aR); gR["px"]=pivR[0]/S-gR["x"]; gR["py"]=pivR[1]/S-gR["y"]; geo["braccio-dx"]=gR
# gomito: il braccio si divide in braccio-alto (dietro) e avambraccio (davanti al busto, cosi' le mani
# possono tenere le cose). Al gomito due dischi coincidenti: sull'avambraccio r 0,92 della mezza larghezza
# (con smusso sotto), sul braccio alto r piu' grande ritagliato sul braccio: il giunto e' tondo a ogni angolo.
def split_arm(a, side, piv):
    ys_,xs_=np.where(a>128); ybot=ys_.max()
    ey=int(round(piv[1]+0.52*(ybot-piv[1])))
    row=a[ey]>128; xs_r=np.where(row)[0]; x0_,x1_=xs_r.min(),xs_r.max(); ex=(x0_+x1_)/2; hw=(x1_-x0_)/2
    rF=hw*0.92; rU=hw+2*S
    am=(a>0).astype(np.float32)
    # asse locale: centro riga per riga (per lo smusso)
    cen=np.full(H3,ex)
    for y in range(ey-10*S,ey+10*S):
        r_=np.where(a[y]>128)[0]
        if len(r_): cen[y]=(r_.min()+r_.max())/2
    halfF=rF+np.maximum(0,Y-ey-S)*1.0
    fore=np.maximum(a*(Y>=ey)*(np.abs(X-cen[:,None])<=halfF), 255*disc((ex,ey),rF)*am)
    upper=np.maximum(a*(Y<ey), 255*disc((ex,ey),rU)*am)
    gU=salva("braccio-alto-"+side,upper); gU["px"]=piv[0]/S-gU["x"]; gU["py"]=piv[1]/S-gU["y"]; gU["ex"]=ex/S-gU["x"]; gU["ey"]=ey/S-gU["y"]
    gF=salva("avambraccio-"+side,fore); gF["px"]=ex/S-gF["x"]; gF["py"]=ey/S-gF["y"]
    geo["braccio-alto-"+side]=gU; geo["avambraccio-"+side]=gF; geo["gomito-"+side]=[ex/S,ey/S]
split_arm(aL,"sx",pivL); split_arm(aR,"dx",pivR)
# busto: dal collo (6px sopra, solo dentro la larghezza del collo) al fondo, fino ai SUOI bordi; spalla tonda
ns=segs(B[neck]); nL,nR=ns[0][0],ns[-1][1]
tLf=np.where(Y[:,0]<gapTop,sL+2,tL); tRf=np.where(Y[:,0]<gapTop,sR-2,tR)
tLf=np.where(Y[:,0]<py,-1,tLf); tRf=np.where(Y[:,0]<py,W3+1,tRf)
# il busto sale 20px sopra il collo seguendo il contorno delle guance: e' il collo che si vede quando la testa si alza o ruota
NECK_UP=36*S   # il busto sale sotto le guance: cosi' quando la testa ruota (fino a 7 gradi) non si apre una fessura chiara
inT=(X>=tLf[:,None]-2)&(X<=tRf[:,None]+2)&(Y<notchTop+2)&(Y>=neck-NECK_UP)
rDisc=rBall*1.25   # il disco del busto e' un po' piu' grande della palla: copre lo smusso e la nasconde sempre
t=np.maximum(D*inT, D*np.maximum(disc(pivL,rDisc),disc(pivR,rDisc)))
geo["busto"]=salva("busto",t)
# testa: buchi degli occhi riempiti, taglio morbido al collo
m=np.zeros(B.shape,np.uint8)
for i in holes: m|=(lab==i).astype(np.uint8)
filled=np.where(cv2.dilate(m,np.ones((15,15),np.uint8))>0,255.0,D)
geo["testa"]=salva("testa",filled*np.clip((neck+2-Y)/S+0.5,0,1))
# gambe: da poco sopra l'incavo, divise al centro dell'incavo, larghe quanto la loro gamba
lg=segs(B[notchTop+10*S])
geo["gamba-sx"]=salva("gamba-sx",D*np.clip((Y-(notchTop-12*S))/S,0,1)*(X<split)*(X>=lg[0][0]-3*S))
geo["gamba-dx"]=salva("gamba-dx",D*np.clip((Y-(notchTop-12*S))/S,0,1)*(X>=split)*(X<=lg[-1][1]+3*S))
# occhi neutri: i buchi bianchi del disegno, esatti
for i,side in zip(holes,["sx","dx"]):
    reg=np.where(lab==i,255.0,0.0); reg=cv2.GaussianBlur(reg,(0,0),0.8)
    geo["occhio-"+side]=salva("occhio-neutro-"+side,reg,col=255)
geo["meta"]=dict(CX=CX,chin=neck/S,neck=[nL/S,nR/S],armW=aw/S,scale=K/S)

# --- per il rig a mesh (costruisci-mesh.py): etichette delle parti a 1x, giunti, texture del corpo ---
np.save("rig/pezzi-base/_D3.npy", D.astype(np.uint8))
lab1=np.zeros((1024,1024),np.uint8)   # 0 niente, 1 busto, 2 braccio alto sx, 3 avambraccio sx, 4 alto dx, 5 avamb dx, 6 gamba sx, 7 gamba dx
def down(a): return a.reshape(1024,S,1024,S).mean(axis=(1,3))
body=(down(D)>128)&(np.arange(1024)[:,None]>=(neck-NECK_UP)/S)
tor=down(t)>128; laL=down(aL)>128; laR=down(aR)>128
legLm=down(D*np.clip((Y-(notchTop-12*S))/S,0,1)*(X<split))>128; legRm=down(D*np.clip((Y-(notchTop-12*S))/S,0,1)*(X>=split))>128
lab1[body]=1
lab1[body&legLm&~tor]=6; lab1[body&legRm&~tor]=7
eyL=geo["gomito-sx"][1]; eyR=geo["gomito-dx"][1]
yy1=np.arange(1024)[:,None]
m=body&laL&~tor; lab1[m]=np.where((yy1*np.ones((1,1024)))[m]>=eyL,3,2)
m=body&laR&~tor; lab1[m]=np.where((yy1*np.ones((1,1024)))[m]>=eyR,5,4)
np.save("rig/pezzi-base/_etichette.npy",lab1)
geo["meta"]["neckTop"]=(neck-NECK_UP)/S; geo["meta"]["notchTop"]=notchTop/S; geo["meta"]["hips"]=[[ (lg[0][0]+split)/2/S, notchTop/S ],[ (split+lg[-1][1])/2/S, notchTop/S ]]
geo["meta"]["pivots"]={"spalla-sx":[pivL[0]/S,pivL[1]/S],"spalla-dx":[pivR[0]/S,pivR[1]/S]}
json.dump(geo,open("rig/pezzi-base/geometria.json","w"),indent=1)
# verifica: composizione a riposo, 45 e 100 gradi; differenza dal disegno
def rot_paste(canvas,name,rot,center):
    p=Image.open(f"rig/pezzi-base/{name}.png"); g=geo[name]; Xp,Yp=round(g["x"]*S),round(g["y"]*S)
    bigc=Image.new("RGBA",(p.width*3,p.height*3)); bigc.alpha_composite(p,(p.width,p.height))
    bigc=bigc.rotate(rot,center=(p.width+center[0]*S,p.height+center[1]*S),resample=Image.BICUBIC)
    canvas.alpha_composite(bigc,(Xp-p.width,Yp-p.height))
def comp(rotL=0,rotR=0,elbL=0,elbR=0):
    canvas=Image.new("RGBA",(1024*S,1024*S),(237,235,230,255))
    for name in ["gamba-sx","gamba-dx"]:
        p=Image.open(f"rig/pezzi-base/{name}.png"); g=geo[name]; canvas.alpha_composite(p,(round(g["x"]*S),round(g["y"]*S)))
    for side,rot,elb in (("sx",rotL,elbL),("dx",rotR,elbR)):
        gU=geo["braccio-alto-"+side]; rot_paste(canvas,"braccio-alto-"+side,rot,(gU["px"],gU["py"]))
    for name in ["busto","testa"]:
        p=Image.open(f"rig/pezzi-base/{name}.png"); g=geo[name]; canvas.alpha_composite(p,(round(g["x"]*S),round(g["y"]*S)))
    for side,rot,elb in (("sx",rotL,elbL),("dx",rotR,elbR)):
        gU=geo["braccio-alto-"+side]; gF=geo["avambraccio-"+side]
        # gomito ruotato attorno alla spalla
        import math
        sx,sy=gU["x"]+gU["px"],gU["y"]+gU["py"]; ex,ey=gU["x"]+gU["ex"],gU["y"]+gU["ey"]
        a=-math.radians(rot); dx,dy=ex-sx,ey-sy
        nex,ney=sx+dx*math.cos(a)-dy*math.sin(a), sy+dx*math.sin(a)+dy*math.cos(a)
        p=Image.open(f"rig/pezzi-base/avambraccio-{side}.png")
        bigc=Image.new("RGBA",(p.width*3,p.height*3)); bigc.alpha_composite(p,(p.width,p.height))
        bigc=bigc.rotate(rot+elb,center=(p.width+gF["px"]*S,p.height+gF["py"]*S),resample=Image.BICUBIC)
        X0=round((nex-gF["px"])*S)-p.width; Y0=round((ney-gF["py"])*S)-p.height
        canvas.alpha_composite(bigc,(X0,Y0))
    for s_ in ("sx","dx"):
        p=Image.open(f"rig/pezzi-base/occhio-neutro-{s_}.png"); g=geo["occhio-"+s_]; canvas.alpha_composite(p,(round(g["x"]*S),round(g["y"]*S)))
    return canvas
rest=comp(); ref=Image.fromarray((255-D).astype(np.uint8))
diff=np.abs(np.array(rest.convert("L")).astype(int)-np.array(ref).astype(int)); print("pixel diversi >60 a riposo (3x):",int((diff>60).sum()))
Image.fromarray(((diff>60)*255).astype(np.uint8)).resize((1024,1024)).save("rig/pezzi-base/_diff.png")
sheet=Image.new("RGB",(1536,512),(237,235,230))
for i,im in enumerate([rest,comp(rotL=-45,rotR=45,elbL=-70,elbR=70),comp(rotL=-60,rotR=20,elbL=-100,elbR=-110)]): sheet.paste(im.convert("RGB").resize((512,512),Image.LANCZOS),(i*512,0))
sheet.save("rig/pezzi-base/_verifica-braccia.png")
rest.resize((1024,1024),Image.LANCZOS).convert("RGB").save("rig/pezzi-base/_riposo.png")
comp(rotL=-60,rotR=20,elbL=-100,elbR=-110).crop((int(200*S),int(560*S),int(520*S),int(800*S))).convert("RGB").resize((640,480)).save("rig/pezzi-base/_zoom-spalla.png"); print("ok")
