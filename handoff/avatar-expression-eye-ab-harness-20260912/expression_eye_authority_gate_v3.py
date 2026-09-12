#!/usr/bin/env python3
"""Fail-closed authority pre-gate for the v2 special-expression eye A/B harness.

No live source writes. Proves that the exact local subject, stable HTTP routes,
actual browser expression resource, and #kopf-dreh eye topology all refer to the
productive relief2 subject before visual A/B evidence is interpreted.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile, time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import requests, websocket

HTML = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
DAEMON = "5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2"
OPEN = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
GAZE = "8e07af6c8fd44eb00816c4c94f6716cbd078159ab6808152650a5861385d28ef"
BASE = "http://127.0.0.1:8788/"


def sha_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def sha_file(p: Path) -> str: return sha_bytes(p.read_bytes())
def http_hash(path: str) -> dict[str, Any]:
    u = BASE.rstrip("/") + "/" + path.lstrip("/")
    r = requests.get(u, timeout=10); r.raise_for_status()
    return {"url": u, "sha256": sha_bytes(r.content), "bytes": len(r.content)}

class CDP:
    def __init__(self, url: str):
        self.ws = websocket.create_connection(url, timeout=20, origin="http://localhost"); self.i = 0
    def close(self): self.ws.close()
    def call(self, method: str, params=None, timeout=20):
        self.i += 1; ident = self.i; self.ws.settimeout(timeout)
        self.ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0: raise TimeoutError(method)
            self.ws.settimeout(remain); msg = json.loads(self.ws.recv())
            if msg.get("id") != ident: continue
            if "error" in msg: raise RuntimeError(msg["error"])
            return msg.get("result", {})
    def eval(self, expr: str):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, 15)
        if r.get("exceptionDetails"): raise RuntimeError(r)
        return r.get("result", {}).get("value")

def snapshot(cdp: CDP) -> list[dict[str, Any]]:
    raw = cdp.eval("JSON.stringify([...document.querySelectorAll('img')].map((e,i)=>({i,id:e.id||'',url:e.currentSrc||e.src})))")
    return json.loads(raw)
def changed(before, after) -> list[str]:
    b={(x['i'],x['id']):x['url'] for x in before}; a={(x['i'],x['id']):x['url'] for x in after}
    return sorted({a[k] for k in a if a.get(k) and a.get(k) != b.get(k)})

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--visual-root',type=Path,default=Path('.'))
    ap.add_argument('--port',type=int,default=9241); ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--expression-register',default='anime_90s'); ap.add_argument('--expression',default='anime_fassungslos')
    args=ap.parse_args(); root=args.visual_root.resolve(); out=args.out.resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    files={'html':(root/'buehne.html',HTML),'daemon':(root/'buehne_daemon.py',DAEMON),'open':(root/'augen_blink_relief2/blink_000.png',OPEN),'gaze':(root/'augen_gaze_relief2/rotglow_tracking_master.png',GAZE)}
    local={k:sha_file(p) for k,(p,_) in files.items()}; expected={k:h for k,(_,h) in files.items()}
    if local != expected: raise SystemExit(f'FAIL local subject drift {local}')
    http={'html':http_hash('/'),'open':http_hash('/augen_blink/blink_000.png'),'gaze':http_hash('/augen_gaze/rotglow_tracking_master.png')}
    if http['html']['sha256'] != HTML or http['open']['sha256'] != OPEN or http['gaze']['sha256'] != GAZE: raise SystemExit(f'FAIL stable-route drift {http}')
    tmp=Path(tempfile.mkdtemp(prefix='f2-eye-authority-v3-')); so=(tmp/'chrome.out').open('wb'); se=(tmp/'chrome.err').open('wb')
    proc=subprocess.Popen(['google-chrome','--headless=new','--no-sandbox','--disable-dev-shm-usage',f'--remote-debugging-port={args.port}','--remote-allow-origins=*',f'--user-data-dir={tmp / "profile"}','--window-size=1536,1024',BASE],stdout=so,stderr=se)
    cdp=None
    try:
        target=None
        for _ in range(120):
            try:
                tabs=requests.get(f'http://127.0.0.1:{args.port}/json/list',timeout=.5).json(); target=next((t for t in tabs if t.get('type')=='page' and '127.0.0.1:8788' in t.get('url','')),None)
                if target: break
            except Exception: pass
            time.sleep(.1)
        if not target: raise SystemExit('FAIL target page not found')
        cdp=CDP(target['webSocketDebuggerUrl']); cdp.call('Runtime.enable')
        for _ in range(100):
            if cdp.eval("document.readyState==='complete' && !!document.getElementById('kopf-dreh')"): break
            time.sleep(.1)
        topology=json.loads(cdp.eval("JSON.stringify((()=>{const h=document.getElementById('kopf-dreh'),b=document.getElementById('augen-blink'),g=document.getElementById('pupillen-glow');return {head_count:document.querySelectorAll('#kopf-dreh').length,blink_count:document.querySelectorAll('#augen-blink').length,gaze_count:document.querySelectorAll('#pupillen-glow').length,blink_in_head:!!(h&&b&&h.contains(b)),gaze_in_head:!!(h&&g&&h.contains(g))}})())"))
        if topology != {'head_count':1,'blink_count':1,'gaze_count':1,'blink_in_head':True,'gaze_in_head':True}: raise SystemExit(f'FAIL topology {topology}')
        before=snapshot(cdp); cdp.eval(f"(()=>{{sonderausdruckZeigen({json.dumps(args.expression_register)},{json.dumps(args.expression)},15000);return true}})()") ; time.sleep(1)
        if not cdp.eval("typeof _sonderLaeuft!=='undefined' && _sonderLaeuft===true"): raise SystemExit('FAIL expression inactive')
        urls=changed(before,snapshot(cdp)); bindings=[]
        for u in urls:
            p=urlparse(u)
            if p.hostname not in ('127.0.0.1','localhost') or '/ausdruck_erweitert/' not in p.path or 'stufe_' not in p.path: continue
            data=requests.get(u,timeout=10); data.raise_for_status(); hs=sha_bytes(data.content)
            rel=p.path.split('/ausdruck_erweitert/',1)[1]; lp=root/'ausdruck_erweitert_relief2'/rel
            row={'url':u,'http_sha256':hs,'local_path':str(lp),'local_exists':lp.exists()}
            if lp.exists(): row['local_sha256']=sha_file(lp); row['byte_identical_relief2']=row['local_sha256']==hs
            bindings.append(row)
        if not bindings or not any(x.get('byte_identical_relief2') for x in bindings): raise SystemExit(f'FAIL no byte-identical active relief2 expression binding urls={urls}')
        after={k:sha_file(p) for k,(p,_) in files.items()}
        if after != local: raise SystemExit(f'FAIL source mutation before={local} after={after}')
        report={'schema':'FRANK_AVATAR_EXPRESSION_EYE_AUTHORITY_GATE/v3','status':'PASS','scope':'READ_ONLY_EXACT_SUBJECT_PRE_GATE','local':local,'http':http,'topology':topology,'expression':{'register':args.expression_register,'name':args.expression},'changed_img_urls':urls,'relief2_bindings':bindings,'source_mutation':False}
        out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps(report,sort_keys=True)); print('EXPRESSION_EYE_AUTHORITY_GATE_V3=PASS'); return 0
    finally:
        if cdp:
            try: cdp.close()
            except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
        so.close(); se.close()

if __name__=='__main__': raise SystemExit(main())
