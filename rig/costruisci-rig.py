# -*- coding: utf-8 -*-
"""Monta la pagina del rig (demo/mascotte-rig.html) dai pezzi in rig/pezzi."""
import base64, json, os, io
from PIL import Image
def b64png(path):
    """PNG rifatto a 32 livelli (bastano per i bordi): pesa 5-8 volte meno."""
    im=Image.open(path).convert("RGBA"); q=im.quantize(colors=32,method=Image.Quantize.FASTOCTREE); b=io.BytesIO(); q.save(b,"PNG",optimize=True)
    return "data:image/png;base64,"+base64.b64encode(b.getvalue()).decode()
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P="rig/pezzi/"; PB="rig/pezzi-base/"
def d(n): return b64png(P+n)
def size(n): return Image.open(P+n).size
def db(n): return b64png(PB+n)
parts={k:dict(src=db(k+".png")) for k in ["testa","busto","braccio-alto-sx","braccio-alto-dx","avambraccio-sx","avambraccio-dx","gamba-sx","gamba-dx"]}
parts.update({k:dict(src=d(k+".png"),w=size(k+".png")[0],h=size(k+".png")[1]) for k in ["mazza","biscotto"]})
geo=json.load(open(PB+"geometria.json"))
eyes={k+"-"+s_:dict(src=d(f"occhio-{k}-{s_}.png"),w=size(f"occhio-{k}-{s_}.png")[0],h=size(f"occhio-{k}-{s_}.png")[1]) for k in ["tondi","arrabbiato","cuori","spirali","contento","dorme","diffidente","triste"] for s_ in ("sx","dx")}
for s_ in ("sx","dx"):
    im=Image.open(PB+f"occhio-neutro-{s_}.png"); eyes["neutro-"+s_]=dict(src=db(f"occhio-neutro-{s_}.png"),w=im.size[0],h=im.size[1])
PO="rig/oggetti/"
def do(n): return b64png(PO+n)
og=json.load(open(PO+"geometria.json"))
objs={k:dict(src=do(k+".png"),w=og[k]["w"],h=og[k]["h"]) for k in og}
mesh=json.load(open("rig/mesh/aphelios-mesh.json"))
for pc in mesh["pieces"]: parts[pc["tex"]]=dict(src=b64png("rig/mesh/"+pc["tex"]+".png"))
pg=json.load(open("rig/pose/geometria.json")); poses={}
def dp(n): return b64png("rig/pose/"+n)
for n,g in pg.items():
    poses[n]=dict(src=dp(n+".png"),x=g["x"],y=g["y"],w=g["w"],h=g["h"],occhi=[dict(src=dp(f"{n}-occhio-{j}.png"),**e) for j,e in enumerate(g["occhi"])])
sg=json.load(open("rig/sdf/geometria.json"))
sdf=dict(res=sg["res"],scale=sg["scale"],tex={n:"data:image/png;base64,"+base64.b64encode(open(f"rig/sdf/{n}.png","rb").read()).decode() for n in sg["pose"]})
DATA=json.dumps(dict(parts=parts,eyes=eyes,geo=geo,objs=objs,mesh=mesh,poses=poses,sdf=sdf))
core=open("rig/aphi-core.js",encoding="utf-8").read().replace("__DATA__",DATA)
for src,dst in (("rig/pagina-rig.html","demo/mascotte-rig.html"),("rig/pagina-stanza.html","demo/aphi-stanza.html")):
    if not os.path.exists(src): continue
    page=open(src,encoding="utf-8").read().replace("__CORE__",core)
    open(dst,"w",encoding="utf-8").write(page); print(dst,os.path.getsize(dst))
