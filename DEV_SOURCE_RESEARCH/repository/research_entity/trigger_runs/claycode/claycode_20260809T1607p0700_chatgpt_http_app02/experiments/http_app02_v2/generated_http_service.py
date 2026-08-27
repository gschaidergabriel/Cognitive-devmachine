# deterministic target generated from ClayCode HTTP probe v2
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json, socket, sys, threading
ROUTES = {('GET', '/'): 'ROUTE_HOME', ('GET', '/asset.txt'): 'ROUTE_ASSET', ('GET', '/count'): 'ROUTE_COUNT'}
STATE = {"visits": 0}
LOCK = threading.Lock()

def deny(reason):
    print(json.dumps({"status":"DENIED","reason":reason}), flush=True)
    raise SystemExit(77)

if len(sys.argv) != 3 or sys.argv[1] != "--listen-fd":
    deny("missing_host_listener_handle")
try:
    fd=int(sys.argv[2])
    inherited=socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
    inherited.getsockname()
except Exception:
    deny("invalid_host_listener_handle")

class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        action=ROUTES.get(("GET",self.path))
        if action == "ROUTE_HOME":
            body=b"<html><body><h1>ClayCode APP-02 probe v2</h1></body></html>"; ctype="text/html; charset=utf-8"; status=200
        elif action == "ROUTE_ASSET":
            body=b"claycode-asset-v2\n"; ctype="text/plain; charset=utf-8"; status=200
        elif action == "ROUTE_COUNT":
            with LOCK:
                STATE["visits"] += 1
                n=STATE["visits"]
            body=json.dumps({"visits":n},sort_keys=True).encode(); ctype="application/json"; status=200
        else:
            body=b"not found"; ctype="text/plain; charset=utf-8"; status=404
        self.send_response(status); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)

srv=ThreadingHTTPServer(("127.0.0.1",0),H,bind_and_activate=False)
srv.socket=inherited
srv.server_address=inherited.getsockname()
print(json.dumps({"status":"SERVING_HOST_HANDLE","host":srv.server_address[0],"port":srv.server_address[1]}),flush=True)
srv.serve_forever()
