#!/usr/bin/env python3
"""Read-only HTTP/SSE visual projection of CognitiveLoopFrame JSONL telemetry."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import time
from urllib.parse import urlparse


def read_frames(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if item.get("schema") == "COGNITIVE_LOOP_FRAME/v1":
            out.append(item)
    return out


HTML = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8"><title>GRID10 Cognitive Twin</title>
<style>
body{font-family:system-ui;margin:0;background:#111;color:#ddd}
main{display:grid;grid-template-columns:minmax(320px,1fr) minmax(360px,1fr);gap:18px;padding:18px}
.card{background:#1b1b1b;border:1px solid #333;border-radius:12px;padding:14px}
#loops{width:100%;height:520px}.axis{display:grid;grid-template-columns:180px 1fr 70px;gap:8px;margin:6px 0}
.track{height:10px;background:#333;border-radius:9px;overflow:hidden}.fill{height:100%;background:#aaa}
small{color:#999} code{word-break:break-all}
</style>
</head>
<body><main>
<section class="card"><h2>Live Cognitive Loops</h2><svg id="loops" viewBox="0 0 600 600"></svg><div id="meta"></div></section>
<section class="card"><h2>Envelope Axes</h2><div id="axes"></div><h3>Work</h3><pre id="work"></pre></section>
</main>
<script>
const svg=document.getElementById('loops'), axes=document.getElementById('axes'), meta=document.getElementById('meta');
function esc(x){return String(x??'')}
function render(f){
  const loops=f.loops||[]; svg.innerHTML='';
  loops.forEach((l,i)=>{
    const r=70+i*38, c=document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx',300);c.setAttribute('cy',300);c.setAttribute('r',r);c.setAttribute('fill','none');
    c.setAttribute('stroke', f.assurance_mode==='NORMAL'?'#8a8':f.assurance_mode==='CAUTION'?'#cc8':'#c88');
    c.setAttribute('stroke-width',Math.max(2,8*(l.activation||.1)));c.setAttribute('opacity',.85);svg.appendChild(c);
    const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',305+r);t.setAttribute('y',300);
    t.setAttribute('fill','#ddd');t.textContent=esc(l.loop_id)+' · '+esc(l.phase);svg.appendChild(t);
  });
  meta.innerHTML='<b>'+esc(f.assurance_mode)+'</b><br><small>tick '+esc(f.tick_id)+' · epoch '+esc(f.state_epoch)+'</small><br><code>'+esc(f.source_digest)+'</code>';
  axes.innerHTML='';
  Object.entries(f.axes||{}).forEach(([name,a])=>{
    const row=document.createElement('div');row.className='axis';
    const v=(a.projected_value==null)?0:Math.max(0,Math.min(1,Number(a.projected_value)));
    row.innerHTML='<span>'+esc(name)+'</span><div class="track"><div class="fill" style="width:'+(v*100)+'%"></div></div><span>'+esc(a.projected_value==null?'?':Number(a.projected_value).toFixed(3))+'</span>';
    axes.appendChild(row);
  });
  document.getElementById('work').textContent=JSON.stringify(f.work||{},null,2);
}
fetch('/latest').then(r=>r.ok?r.json():null).then(x=>x&&render(x));
const es=new EventSource('/events'); es.onmessage=e=>{try{render(JSON.parse(e.data))}catch(_){}};
</script></body></html>"""


def make_handler(frame_path: Path):
    class Handler(BaseHTTPRequestHandler):
        server_version = "GRID10CognitiveTwin/1"

        def _json(self, status: int, body: dict):
            raw = json.dumps(body, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            route = urlparse(self.path).path
            if route == "/health":
                self._json(200, {"status": "ok", "read_only": True, "frame_path": str(frame_path)})
                return
            if route == "/latest":
                frames = read_frames(frame_path)
                if not frames:
                    self._json(404, {"status": "no_frames"})
                else:
                    self._json(200, frames[-1])
                return
            if route == "/":
                raw = HTML.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(raw)
                return
            if route == "/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                index = 0
                deadline = time.time() + 25.0
                try:
                    while time.time() < deadline:
                        frames = read_frames(frame_path)
                        while index < len(frames):
                            payload = json.dumps(frames[index], sort_keys=True, separators=(",", ":"))
                            self.wfile.write(f"data: {payload}\n\n".encode())
                            self.wfile.flush()
                            index += 1
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                        time.sleep(0.5)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            self._json(404, {"error": "not_found"})

        def do_POST(self):
            self._json(405, {"error": "read_only_surface"})

        def do_PUT(self):
            self._json(405, {"error": "read_only_surface"})

        def do_DELETE(self):
            self._json(405, {"error": "read_only_surface"})

        def log_message(self, fmt, *args):
            return
    return Handler


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--frames-jsonl", required=True)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(Path(args.frames_jsonl)))
    print(json.dumps({"schema":"COGNITIVE_TWIN_SERVER/v1","host":args.host,"port":args.port,"read_only":True}, sort_keys=True))
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
