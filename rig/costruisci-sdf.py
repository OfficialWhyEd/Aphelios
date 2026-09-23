# -*- coding: utf-8 -*-
"""Campi di distanza (SDF) delle pose per le transizioni fluide: da una posa all'altra il corpo si trasforma
invece di scattare. Per ogni posa in rig/pose/: la silhouette (senza occhi, cioe' il PNG riempito) messa nella
scena 1024x1024, distanza con segno in pixel, salvata a RES x RES in 8 bit (128 = bordo, 1 livello = 1/4 px).
Uscita: rig/sdf/<nome>.png + rig/sdf/geometria.json."""
from PIL import Image
import numpy as np, json, os
from scipy import ndimage
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs("rig/sdf",exist_ok=True)
RES=512; SCALE=2.0     # 1 livello = 0,5 px (scena 1024); intervallo +-64 px: evita i plateau grigi nel morph
g=json.load(open("rig/pose/geometria.json")); out={}
for name,p in g.items():
    im=Image.open(f"rig/pose/{name}.png").split()[-1]
    im=im.resize((int(round(p["w"])),int(round(p["h"]))),Image.LANCZOS)
    canvas=np.zeros((1024,1024),np.float32)
    x0,y0=int(round(p["x"])),int(round(p["y"])); a=np.array(im).astype(np.float32)/255
    h,w=a.shape; canvas[y0:y0+h,x0:x0+w]=np.maximum(canvas[y0:y0+h,x0:x0+w],a[:1024-y0,:1024-x0])
    inside=canvas>0.5
    d_out=ndimage.distance_transform_edt(~inside); d_in=ndimage.distance_transform_edt(inside)
    sdf=np.where(inside,-d_in,d_out)                           # negativo dentro
    # correzione sub-pixel col valore di alpha sul bordo (evita gradini)
    edge=(canvas>0.02)&(canvas<0.98); sdf[edge]=(0.5-canvas[edge])
    small=ndimage.zoom(sdf,RES/1024,order=1)
    enc=np.clip(small*SCALE+128,0,255).astype(np.uint8)
    Image.fromarray(enc).save(f"rig/sdf/{name}.png")
    out[name]=dict(occhi=p["occhi"])
json.dump(dict(res=RES,scale=SCALE,pose=out),open("rig/sdf/geometria.json","w"))
print("ok",len(out))
