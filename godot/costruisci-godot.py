# -*- coding: utf-8 -*-
"""Genera il progetto Godot 4 di Aphelios dal disegno APPROVATO (rig/pose/base.png, la cella centrale
della griglia 02-vettori-a, a 2x) senza tagliare niente: UNA mesh sola per tutta la sagoma, uno
scheletro 2D (Skeleton2D + Bone2D) e pesi morbidi calcolati sulla mesh stessa (il collo, le spalle,
le anche sono fusioni, non tagli). Gli occhi sono i buchi bianchi veri del disegno, sprite separati
che seguono l'osso della testa e restano ritagliati dentro il corpo.

Uscita: godot/progetto/ (project.godot, aphi.tscn, aphi.gd, texture) e godot/_verifica-*.png."""
from PIL import Image, ImageDraw
import numpy as np, json, os, cv2, shutil
from scipy.spatial import Delaunay
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # E:\Dev\Mascotte
OUT = "godot/progetto"; os.makedirs(OUT, exist_ok=True); os.makedirs(OUT + "/tex", exist_ok=True)
G = 7            # passo della griglia dei vertici interni (px scena 1024)
SMOOTH = 7       # passate di fusione dei pesi sulla mesh (ampiezza della sfumatura ai giunti)

# ---------- il disegno: sagoma a 1x nella scena 1024, texture a 2x ----------
pg = json.load(open("rig/pose/geometria.json"))["base"]
tex0 = Image.open("rig/pose/base.png").convert("RGBA")          # 2x, sagoma piena (occhi riempiti)
PAD = 12                                                          # margine trasparente (px texture): il bordo lo fa l'alpha, non la mesh
tex = Image.new("RGBA", (tex0.width + 2 * PAD, tex0.height + 2 * PAD), (20, 20, 20, 0)); tex.paste(tex0, (PAD, PAD))
K2 = tex0.width / pg["w"]                                         # pixel texture per unita' scena (2x)
TX, TY, TW, TH = pg["x"] - PAD / K2, pg["y"] - PAD / K2, pg["w"] + 2 * PAD / K2, pg["h"] + 2 * PAD / K2
alpha1 = np.array(tex.split()[-1].resize((int(round(TW)), int(round(TH))), Image.LANCZOS))
sil = np.zeros((1024, 1024), np.uint8)
x0, y0 = int(round(TX)), int(round(TY)); sil[y0:y0 + alpha1.shape[0], x0:x0 + alpha1.shape[1]] = alpha1
inside = sil > 128
tex.save(OUT + "/tex/corpo.png")

# ---------- pezzi e misure gia' calcolate (solo per ETICHETTARE i vertici, non per tagliare) ----------
geo = json.load(open("rig/pezzi-base/geometria.json")); M = geo["meta"]
def mask1(name):
    g = geo[name]; a = Image.open(f"rig/pezzi-base/{name}.png").split()[-1].resize((int(round(g["w"])), int(round(g["h"]))), Image.LANCZOS)
    m = np.zeros((1024, 1024), bool); a = np.array(a) > 128
    x, y = int(round(g["x"])), int(round(g["y"])); m[y:y + a.shape[0], x:x + a.shape[1]] = a; return m
mk = {n: mask1(n) for n in ("testa", "busto", "braccio-alto-sx", "avambraccio-sx", "braccio-alto-dx", "avambraccio-dx", "gamba-sx", "gamba-dx")}
CX, CHIN = M["CX"], M["chin"]

# orecchie: base e punta misurate sul profilo superiore della testa (stesso metodo del rig 2D)
def ears():
    t = mk["testa"]; top = np.array([np.argmax(c) if c.any() else 10 ** 6 for c in t.T]); W = 1024; mid = 512
    out = {}
    for side, (a, b) in (("L", (0, mid)), ("R", (mid, W))):
        seg = top[a:b]; tip = a + int(np.argmin(seg))
        inner = range(tip, mid) if side == "L" else range(mid, tip)
        notch = max(inner, key=lambda x: top[x]); ny = int(top[notch]); outer = tip; step = -1 if side == "L" else 1
        while 0 <= outer + step < W and top[outer + step] <= ny: outer += step
        out[side] = dict(pivot=[(notch + outer) / 2, ny + 8], tip=[tip, int(top[tip])], halfW=abs(notch - outer) / 2)
    return out
E = ears()

# ---------- ossa: nome, genitore, posizione globale (a riposo) ----------
hips = M["hips"]; notch = M["notchTop"]
BONES = [
    ("root", None, [CX, notch + 20]),
    ("spine", "root", [CX, notch - 90]),
    ("neck", "spine", [CX, CHIN + 24]),
    ("head", "neck", [CX, CHIN]),
    ("earL", "head", E["L"]["pivot"]), ("earR", "head", E["R"]["pivot"]),
    ("upperL", "spine", M["pivots"]["spalla-sx"]), ("foreL", "upperL", geo["gomito-sx"]),
    ("upperR", "spine", M["pivots"]["spalla-dx"]), ("foreR", "upperR", geo["gomito-dx"]),
    ("legL", "root", hips[0]), ("legR", "root", hips[1]),
]
BI = {b[0]: i for i, b in enumerate(BONES)}

# ---------- la mesh: contorno + griglia interna, triangolazione dentro la sagoma ----------
grown = cv2.dilate(inside.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
cnts, _ = cv2.findContours(grown.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cnt = max(cnts, key=cv2.contourArea)
outline = cv2.approxPolyDP(cnt, 1.1, True).reshape(-1, 2).astype(np.float32)
# griglia interna, non troppo vicina al contorno (i triangoli di bordo li fa il contorno stesso)
er = cv2.erode(inside.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
grid = np.array([(x, y) for y in range(y0, y0 + alpha1.shape[0], G) for x in range(x0, x0 + alpha1.shape[1], G) if er[y, x]], np.float32)
V = np.vstack([outline, grid])
NO = len(outline)
tri = Delaunay(V).simplices
def ok(t):
    p = V[t]; c = p.mean(axis=0); mids = (p + np.roll(p, 1, axis=0)) / 2
    for q in (c, *mids):
        xi, yi = int(round(q[0])), int(round(q[1]))
        if not (0 <= xi < 1024 and 0 <= yi < 1024 and inside[yi, xi]): return False
    return True
# il test usa la sagoma allargata di 2 px: i triangoli di bordo (contorno + punto interno) restano tutti, e il bordo
# vero lo fa l'alpha della texture; i triangoli che scavalcano un solco o una concavita' vengono tolti lo stesso
inside_t = inside
inside = cv2.dilate(grown.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
keep = np.array([ok(t) for t in tri]); T = tri[keep]; inside = inside_t
# togli i vertici non usati (contorno compreso: alcuni punti del contorno possono restare fuori)
used = np.zeros(len(V), bool); used[T.flatten()] = True
remap = -np.ones(len(V), int); remap[used] = np.arange(used.sum())
V = V[used]; T = remap[T]; NO = int(used[:NO].sum())
print("vertici", len(V), "(contorno", NO, ") triangoli", len(T))

# ---------- etichette dai pezzi, poi FUSIONE morbida sulla mesh ----------
lab = np.full(len(V), BI["spine"])
def at(m, p): return m[min(1023, max(0, int(round(p[1])))), min(1023, max(0, int(round(p[0]))))]
for i, p in enumerate(V):
    if at(mk["testa"], p) and p[1] < CHIN + 6:
        lab[i] = BI["head"]
        for side in ("L", "R"):
            e = E[side]; piv = np.array(e["pivot"]); tip = np.array(e["tip"]); u = tip - piv; L = np.linalg.norm(u); u /= L
            d = (p - piv) @ u; l = abs((p - piv) @ np.array([-u[1], u[0]]))
            if d > L * 0.22 and l < e["halfW"] * 1.2: lab[i] = BI["ear" + side]
    elif at(mk["avambraccio-sx"], p): lab[i] = BI["foreL"]
    elif at(mk["braccio-alto-sx"], p): lab[i] = BI["upperL"]
    elif at(mk["avambraccio-dx"], p): lab[i] = BI["foreR"]
    elif at(mk["braccio-alto-dx"], p): lab[i] = BI["upperR"]
    elif at(mk["gamba-sx"], p) and p[1] > notch - 6: lab[i] = BI["legL"]
    elif at(mk["gamba-dx"], p) and p[1] > notch - 6: lab[i] = BI["legR"]
    elif p[1] > notch - 40: lab[i] = BI["root"]
Wt = np.zeros((len(V), len(BONES)), np.float32); Wt[np.arange(len(V)), lab] = 1
# adiacenza dalla mesh: la sfumatura passa solo dove il disegno e' collegato (spalla, collo, anche), mai attraverso i solchi
nb = [set() for _ in V]
for a, b, c in T: nb[a] |= {b, c}; nb[b] |= {a, c}; nb[c] |= {a, b}
for _ in range(SMOOTH):
    W2 = Wt.copy()
    for i in range(len(V)): W2[i] = 0.5 * Wt[i] + 0.5 * Wt[list(nb[i])].mean(axis=0)
    Wt = W2
Wt[Wt < 0.02] = 0; Wt /= Wt.sum(axis=1, keepdims=True)

# ---------- scena Godot (formato testo) ----------
def pv2(arr): return "PackedVector2Array(" + ", ".join(f"{x:.2f}, {y:.2f}" for x, y in arr) + ")"
def pf(arr): return "PackedFloat32Array(" + ", ".join(f"{v:.4f}" for v in arr) + ")"
# uv in pixel della texture 2x
sx, sy = tex.width / TW, tex.height / TH
UV = [((x - TX) * sx, (y - TY) * sy) for x, y in V]
bone_path = {}
def path(n):
    b = BONES[BI[n]]; return (path(b[1]) + "/" if b[1] else "") + n
lines = ['[gd_scene load_steps=6 format=3 uid="uid://aphi_scene"]', '',
         '[ext_resource type="Texture2D" path="res://tex/corpo.png" id="1"]',
         '[ext_resource type="Texture2D" path="res://tex/occhio-sx.png" id="2"]',
         '[ext_resource type="Texture2D" path="res://tex/occhio-dx.png" id="3"]',
         '[ext_resource type="Script" path="res://aphi.gd" id="4"]', '',
         '[node name="Aphi" type="Node2D"]', 'script = ExtResource("4")', '',
         '[node name="Skeleton2D" type="Skeleton2D" parent="."]', '']
for n, par, pos in BONES:
    ppos = BONES[BI[par]][2] if par else [0, 0]
    rel = (pos[0] - ppos[0], pos[1] - ppos[1])
    parent = "Skeleton2D" + ("/" + path(par) if par else "")
    lines += [f'[node name="{n}" type="Bone2D" parent="{parent}"]',
              f'position = Vector2({rel[0]:.3f}, {rel[1]:.3f})',
              f'rest = Transform2D(1, 0, 0, 1, {rel[0]:.3f}, {rel[1]:.3f})', '']
lines += ['[node name="Corpo" type="Polygon2D" parent="."]',
          'texture = ExtResource("1")', 'skeleton = NodePath("../Skeleton2D")',
          'clip_children = 2',
          'polygon = ' + pv2(V), 'uv = ' + pv2(UV),
          f'internal_vertex_count = {len(V) - NO}',
          'polygons = [' + ", ".join("PackedInt32Array(%d, %d, %d)" % tuple(t) for t in T) + ']',
          'bones = [' + ", ".join(f'NodePath("{path(b[0])}"), {pf(Wt[:, i])}' for i, b in enumerate(BONES)) + ']', '']
# occhi: i buchi veri del disegno, centrati; misura dal foglio approvato
for j, (n, rid) in enumerate((("OcchioSx", "2"), ("OcchioDx", "3"))):
    e = pg["occhi"][j]; im = Image.open(f"rig/pose/base-occhio-{j}.png").convert("RGBA"); im.save(OUT + f"/tex/occhio-{'sx' if j == 0 else 'dx'}.png")
    cx, cy = e["x"] + e["w"] / 2, e["y"] + e["h"] / 2
    lines += [f'[node name="{n}" type="Sprite2D" parent="Corpo"]', f'texture = ExtResource("{rid}")',
              f'position = Vector2({cx:.2f}, {cy:.2f})', f'scale = Vector2({e["w"] / im.width:.5f}, {e["h"] / im.height:.5f})', '']
open(OUT + "/aphi.tscn", "w", encoding="utf-8").write("\n".join(lines))

# metadati per lo script (perni e misure)
meta = dict(CX=CX, chin=CHIN, headW=geo["testa"]["w"], headY=geo["testa"]["y"],
            eyes=[dict(cx=pg["occhi"][j]["x"] + pg["occhi"][j]["w"] / 2, cy=pg["occhi"][j]["y"] + pg["occhi"][j]["h"] / 2) for j in range(2)],
            bones={b[0]: b[2] for b in BONES}, feet=985)
json.dump(meta, open(OUT + "/meta.json", "w"), indent=1)

# ---------- verifica: mesh e pesi disegnati ----------
prev = Image.new("RGB", (1024, 1024), (237, 235, 230)); dr = ImageDraw.Draw(prev)
COL = {"root": (0, 0, 0), "spine": (90, 90, 90), "neck": (200, 120, 0), "head": (60, 60, 200), "earL": (30, 160, 255), "earR": (255, 80, 80),
       "upperL": (0, 120, 255), "foreL": (0, 200, 230), "upperR": (255, 60, 60), "foreR": (255, 150, 0), "legL": (0, 170, 90), "legR": (140, 60, 200)}
for t in T: dr.polygon([tuple(V[k]) for k in t], outline=(205, 205, 205))
for i, (x, y) in enumerate(V):
    c = np.zeros(3)
    for b in range(len(BONES)): c += Wt[i, b] * np.array(COL[BONES[b][0]])
    dr.ellipse((x - 2, y - 2, x + 2, y + 2), fill=tuple(int(v) for v in c))
for n, par, pos in BONES:
    if par: q = BONES[BI[par]][2]; dr.line([tuple(q), tuple(pos)], fill=(255, 0, 255), width=2)
    dr.ellipse((pos[0] - 5, pos[1] - 5, pos[0] + 5, pos[1] + 5), fill=(255, 0, 255))
prev.save("godot/_verifica-mesh.png")
# import: le texture con mipmap (senza, rimpicciolite fanno i bordi seghettati)
for f in os.listdir(OUT + "/tex"):
    fi = OUT + "/tex/" + f + ".import"
    if f.endswith(".png") and os.path.exists(fi):
        t = open(fi).read().replace("mipmaps/generate=false", "mipmaps/generate=true"); open(fi, "w").write(t)
print("ok", OUT)
