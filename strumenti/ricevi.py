# -*- coding: utf-8 -*-
"""Riceve un'immagine (data URL) via POST da una pagina nel browser e la salva in E:/Dev/Mascotte/out/ricevuti/."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import base64, os, time
OUT="E:/Dev/Mascotte/out/ricevuti"; os.makedirs(OUT,exist_ok=True)
class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self): self.send_response(204); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","*"); self.end_headers()
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); body=self.rfile.read(n).decode()
        name=self.path.strip("/") or f"img-{int(time.time())}"
        head,data=body.split(",",1); ext="png" if "png" in head else "jpg"
        p=f"{OUT}/{name}.{ext}"; open(p,"wb").write(base64.b64decode(data))
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b"ok"); print("salvato",p,flush=True)
    def log_message(self,*a): pass
HTTPServer(("127.0.0.1",8766),H).serve_forever()
