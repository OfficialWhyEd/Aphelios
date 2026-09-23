# -*- coding: utf-8 -*-
"""Genera la mascotte di WhyEd da geometria pura. Ogni numero e' regolabile."""
import math, sys
from PIL import Image, ImageDraw

P = dict(
    W=1000, H=1000,
    testa_larg   = 700,   # larghezza massima della testa
    testa_alt    = 620,   # altezza della testa (senza orecchie)
    calotta      = 0.62,  # quanto e' bombata la fronte (piu' basso = testa piu' bassa)
    mento        = 0.86,  # quanto e' pieno il mento
    orecchio_alt = 300,   # quanto salgono le orecchie sopra la testa
    orecchio_larg= 165,   # base dell'orecchio
    orecchio_ang = 12,    # inclinazione verso l'esterno, in gradi
    incavo       = 0.30,  # quanto scende la V fra le orecchie (0 = piatta)
    occhio_larg  = 250,
    occhio_alt   = 150,
    occhio_y     = 0.72,  # 0 = cima testa, 1 = mento
    occhio_gap   = 60,    # nero fra i due occhi
    occhio_tilt  = 16,    # inclinazione in gradi
)

def bezier(p0,p1,p2,p3,n=60):
    out=[]
    for i in range(n+1):
        t=i/n; u=1-t
        out.append((u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0],
                    u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]))
    return out

def costruisci(p):
    cx, cy = p["W"]/2, p["H"]/2
    hw = p["testa_larg"]/2
    top    = cy - p["testa_alt"]/2
    bottom = cy + p["testa_alt"]/2
    hh = p["testa_alt"]/2

    # punti fissi
    spallaL = (cx-hw, cy - hh*0.05)
    spallaR = (cx+hw, cy - hh*0.05)
    # dove le orecchie appoggiano sulla calotta
    bL_est = (cx - hw*0.86, top + hh*0.42)
    bL_int = (cx - hw*0.34, top + hh*0.16)
    bR_int = (cx + hw*0.34, top + hh*0.16)
    bR_est = (cx + hw*0.86, top + hh*0.42)
    # punte
    a = math.radians(p["orecchio_ang"])
    puntaL = (bL_est[0] - p["orecchio_alt"]*math.sin(a)*0.6, bL_est[1] - p["orecchio_alt"])
    puntaR = (bR_est[0] + p["orecchio_alt"]*math.sin(a)*0.6, bR_est[1] - p["orecchio_alt"])

    c = []
    # mento
    c += bezier(spallaL, (cx-hw, cy + hh*p["mento"]), (cx-hw*0.42, bottom), (cx, bottom))
    c += bezier((cx, bottom), (cx+hw*0.42, bottom), (cx+hw, cy + hh*p["mento"]), spallaR)
    # fianco destro dritto fino alla punta dell orecchio destro
    c += [puntaR]
    # lato interno orecchio destro fino alla base interna
    c += [bR_int]
    # calotta: arco continuo da destra a sinistra, con una V appena accennata
    c += bezier(bR_int,
                (cx + hw*0.20, top + hh*p["incavo"]*0.9),
                (cx - hw*0.20, top + hh*p["incavo"]*0.9),
                bL_int)
    # lato interno orecchio sinistro e punta
    c += [puntaL]
    c += [spallaL]

    # occhi
    ey = top + p["testa_alt"]*p["occhio_y"]
    ow, oh = p["occhio_larg"], p["occhio_alt"]
    def occhio(verso):
        s = 1 if verso=="dx" else -1
        ox = cx + s*(p["occhio_gap"]/2 + ow/2)
        pts  = bezier((ox - s*ow/2, ey + oh*0.05),
                      (ox - s*ow/2, ey - oh*0.62),
                      (ox + s*ow/2, ey - oh*0.50),
                      (ox + s*ow/2, ey + oh*0.10))
        pts += bezier((ox + s*ow/2, ey + oh*0.10),
                      (ox + s*ow/2, ey + oh*0.62),
                      (ox - s*ow/5, ey + oh*0.58),
                      (ox - s*ow/2, ey + oh*0.05))
        t = math.radians(p["occhio_tilt"]*s)
        return [((x-ox)*math.cos(t)-(y-ey)*math.sin(t)+ox,
                 (x-ox)*math.sin(t)+(y-ey)*math.cos(t)+ey) for x,y in pts]
    return c, occhio("dx"), occhio("sx")

def inquadra(shapes, W, H, margine=0.10):
    """centra e scala tutto dentro il quadro"""
    pts = [q for s in shapes for q in s]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    bw = max(xs)-min(xs); bh = max(ys)-min(ys)
    k = min(W*(1-2*margine)/bw, H*(1-2*margine)/bh)
    ox = (W - bw*k)/2 - min(xs)*k
    oy = (H - bh*k)/2 - min(ys)*k
    return [[(q[0]*k+ox, q[1]*k+oy) for q in s] for s in shapes]

def salva(p, nome):
    corpo, edx, esx = costruisci(p)
    corpo, edx, esx = inquadra([corpo, edx, esx], p["W"], p["H"])
    def path(pts):
        return " ".join([f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]+
                        [f"L {q[0]:.1f} {q[1]:.1f}" for q in pts[1:]])+" Z"
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {p["W"]} {p["H"]}" width="{p["W"]}" height="{p["H"]}">',
         f'<rect width="{p["W"]}" height="{p["H"]}" fill="#F7F5F0"/>',
         f'<path d="{path(corpo)}" fill="#111111"/>',
         f'<path d="{path(edx)}" fill="#F7F5F0"/>',
         f'<path d="{path(esx)}" fill="#F7F5F0"/>','</svg>']
    open(fr"E:\Dev\Mascotte\out\{nome}.svg","w",encoding="utf-8").write("\n".join(svg))
    img=Image.new("RGB",(p["W"],p["H"]),(247,245,240)); d=ImageDraw.Draw(img)
    d.polygon(corpo, fill=(17,17,17))
    d.polygon(edx, fill=(247,245,240)); d.polygon(esx, fill=(247,245,240))
    img.save(fr"E:\Dev\Mascotte\out\{nome}.png")

if __name__ == "__main__":
    for k, v in (a.split("=") for a in sys.argv[1:] if "=" in a):
        P[k] = float(v) if "." in v else int(v)
    salva(P, "mascotte-costruita")
    print("fatto:", {k:P[k] for k in ("testa_alt","calotta","orecchio_alt","occhio_larg","occhio_y")})
