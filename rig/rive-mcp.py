"""Ponte verso il MCP dell'editor Rive (Early Access) sulla porta 9791.

Uso:
  python rive-mcp.py list                      elenco dei tool
  python rive-mcp.py call <tool> '<json>'      chiama un tool con gli argomenti in JSON
  python rive-mcp.py schema <tool>             schema degli argomenti di un tool

Ogni chiamata apre una sessione (initialize + initialized) e poi esegue.
"""
import json, sys, urllib.request

URL = "http://127.0.0.1:9791/mcp"


class Rive:
    def __init__(self):
        self.sid = None
        self.n = 0
        r = self._post({"method": "initialize", "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "claude-code", "version": "1"}}})
        self._notify("notifications/initialized")

    def _headers(self):
        h = {"Content-Type": "application/json",
             "Accept": "application/json, text/event-stream"}
        if self.sid:
            h["mcp-session-id"] = self.sid
        return h

    def _post(self, body, want_result=True):
        self.n += 1
        body = {"jsonrpc": "2.0", "id": self.n, **body}
        req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                     headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            sid = resp.headers.get("mcp-session-id")
            if sid:
                self.sid = sid
            raw = resp.read().decode("utf-8", "replace")
        if raw.startswith("event:") or "\ndata:" in raw:
            # server-sent events: prendo l'ultimo blocco data
            datas = [l[5:].strip() for l in raw.splitlines() if l.startswith("data:")]
            raw = datas[-1] if datas else "{}"
        d = json.loads(raw) if raw.strip() else {}
        if "error" in d:
            raise RuntimeError(json.dumps(d["error"], ensure_ascii=False))
        return d.get("result", d)

    def _notify(self, method, params=None):
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                     headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()

    def tools(self):
        return self._post({"method": "tools/list", "params": {}})["tools"]

    def call(self, name, args=None):
        r = self._post({"method": "tools/call",
                        "params": {"name": name, "arguments": args or {}}})
        out = []
        for c in r.get("content", []):
            if c.get("type") == "text":
                out.append(c["text"])
            else:
                out.append(json.dumps(c)[:300])
        text = "\n".join(out)
        if r.get("isError"):
            raise RuntimeError(text)
        return text


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    rv = Rive()
    if cmd == "list":
        for t in rv.tools():
            print("-", t["name"], ":", (t.get("description") or "").split("\n")[0][:120])
    elif cmd == "schema":
        for t in rv.tools():
            if t["name"] == sys.argv[2]:
                print(t.get("description", ""))
                print(json.dumps(t.get("inputSchema", {}), indent=1, ensure_ascii=False))
    elif cmd == "call":
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(rv.call(sys.argv[2], args))
