#!/usr/bin/env python3
"""Local proxy experiment for SPAWN ClayCode HTTP+SQLite vertical slice.

This is NOT the production ClayCode compiler. It is a deterministic narrow
semantic-spec -> Python host lowering witness used to discriminate whether
HTTP/SQLite functionality obviously requires new core language semantics.
"""
from __future__ import annotations
import hashlib, json, os, sqlite3, subprocess, sys, tempfile, urllib.error, urllib.request

SPEC = {
    "module": "spawn.http_sqlite_vertical_slice.v1",
    "semantic_classes": [
        "http_request_response","typed_state","effect_intent","desired_outcome",
        "constraints","rollback","resource_identity","provenance"
    ],
    "db": {
        "adapter": "sqlite",
        "table": "items",
        "transaction_mode": "explicit",
        "columns": [
            {"name":"id","type":"INTEGER","primary_key":True},
            {"name":"name","type":"TEXT","not_null":True,"unique":True},
        ],
    },
    "routes": [
        {"method":"POST","path":"/items","op":"create","transaction":"atomic","success":201},
        {"method":"GET","path":"/items/{id}","op":"read","transaction":"read","success":200,"not_found":404},
        {"method":"PUT","path":"/items/{id}","op":"update","transaction":"atomic","success":200,"not_found":404},
        {"method":"DELETE","path":"/items/{id}","op":"delete","transaction":"atomic","success":204,"not_found":404},
    ],
    "errors": {"invalid":400,"conflict":409,"method":405,"internal":500},
    "test_injection": {"query":"fail=1","point":"after_write_before_commit"},
}

def canonical_hash(obj):
    raw=json.dumps(obj, sort_keys=True, separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def lower(spec):
    ops={r["op"] for r in spec["routes"]}
    if ops != {"create","read","update","delete"}:
        raise ValueError("unsupported route operation set")
    if spec["db"]["adapter"] != "sqlite" or spec["db"]["transaction_mode"] != "explicit":
        raise ValueError("unsupported db adapter/transaction mode")
    statuses={
        "create": next(r["success"] for r in spec["routes"] if r["op"]=="create"),
        "read": next(r["success"] for r in spec["routes"] if r["op"]=="read"),
        "update": next(r["success"] for r in spec["routes"] if r["op"]=="update"),
        "delete": next(r["success"] for r in spec["routes"] if r["op"]=="delete"),
        **spec["errors"],
    }
    table=spec["db"]["table"]
    return SERVER_TEMPLATE.replace("__TABLE__", table).replace("__STATUSES__", repr(statuses))

SERVER_TEMPLATE = r"""
import json, sqlite3, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB=sys.argv[1]
TABLE="__TABLE__"
S=__STATUSES__
c=sqlite3.connect(DB)
c.execute("PRAGMA journal_mode=WAL")
c.execute(f"CREATE TABLE IF NOT EXISTS {TABLE} (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)")
c.commit(); c.close()

def db(): return sqlite3.connect(DB, timeout=2.0)

class H(BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self, fmt, *args): pass
    def sendj(self, code, obj=None):
        b=b"" if obj is None else json.dumps(obj,sort_keys=True,separators=(",",":")).encode()
        self.send_response(code)
        if obj is not None: self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        if b: self.wfile.write(b)
    def body_name(self):
        try:
            n=int(self.headers.get("Content-Length","0"))
            x=json.loads(self.rfile.read(n) or b"{}")
            name=x.get("name")
            return name if isinstance(name,str) and name.strip() else None
        except Exception: return None
    def iid(self,u):
        try:
            if not u.path.startswith("/items/"): return None
            return int(u.path.split("/")[-1])
        except Exception: return None
    def do_POST(self):
        u=urlparse(self.path)
        if u.path!="/items": return self.sendj(404,{"error":"not_found"})
        name=self.body_name()
        if name is None: return self.sendj(S["invalid"],{"error":"invalid_name"})
        c=db()
        try:
            c.execute("BEGIN IMMEDIATE")
            cur=c.execute(f"INSERT INTO {TABLE}(name) VALUES (?)",(name,))
            iid=cur.lastrowid
            if parse_qs(u.query).get("fail")==["1"]: raise RuntimeError("injected")
            c.commit(); return self.sendj(S["create"],{"id":iid,"name":name})
        except sqlite3.IntegrityError:
            c.rollback(); return self.sendj(S["conflict"],{"error":"conflict"})
        except Exception:
            c.rollback(); return self.sendj(S["internal"],{"error":"internal"})
        finally: c.close()
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=="/count":
            c=db()
            try: n=c.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
            finally: c.close()
            return self.sendj(200,{"count":n})
        iid=self.iid(u)
        if iid is None:
            return self.sendj(S["invalid"] if u.path.startswith("/items/") else 404,
                              {"error":"invalid_id" if u.path.startswith("/items/") else "not_found"})
        c=db()
        try: row=c.execute(f"SELECT id,name FROM {TABLE} WHERE id=?",(iid,)).fetchone()
        finally: c.close()
        return self.sendj(404,{"error":"not_found"}) if row is None else self.sendj(S["read"],{"id":row[0],"name":row[1]})
    def do_PUT(self):
        u=urlparse(self.path); iid=self.iid(u); name=self.body_name()
        if iid is None: return self.sendj(S["invalid"],{"error":"invalid_id"})
        if name is None: return self.sendj(S["invalid"],{"error":"invalid_name"})
        c=db()
        try:
            c.execute("BEGIN IMMEDIATE")
            cur=c.execute(f"UPDATE {TABLE} SET name=? WHERE id=?",(name,iid))
            if cur.rowcount==0: c.rollback(); return self.sendj(404,{"error":"not_found"})
            if parse_qs(u.query).get("fail")==["1"]: raise RuntimeError("injected")
            c.commit(); return self.sendj(S["update"],{"id":iid,"name":name})
        except sqlite3.IntegrityError:
            c.rollback(); return self.sendj(S["conflict"],{"error":"conflict"})
        except Exception:
            c.rollback(); return self.sendj(S["internal"],{"error":"internal"})
        finally: c.close()
    def do_DELETE(self):
        u=urlparse(self.path); iid=self.iid(u)
        if iid is None: return self.sendj(S["invalid"],{"error":"invalid_id"})
        c=db()
        try:
            c.execute("BEGIN IMMEDIATE")
            cur=c.execute(f"DELETE FROM {TABLE} WHERE id=?",(iid,))
            if cur.rowcount==0: c.rollback(); return self.sendj(404,{"error":"not_found"})
            if parse_qs(u.query).get("fail")==["1"]: raise RuntimeError("injected")
            c.commit(); return self.sendj(S["delete"],None)
        except Exception:
            c.rollback(); return self.sendj(S["internal"],{"error":"internal"})
        finally: c.close()
    def do_PATCH(self): return self.sendj(S["method"],{"error":"method_not_allowed"})

srv=ThreadingHTTPServer(("127.0.0.1",0),H)
print(srv.server_address[1],flush=True)
srv.serve_forever()
"""

def request(port, method, path, obj=None):
    data=None; headers={}
    if obj is not None:
        data=json.dumps(obj).encode(); headers["Content-Type"]="application/json"
    rq=urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=3) as resp:
            raw=resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw=e.read()
        return e.code, (json.loads(raw) if raw else None)

def execute(code, full=True):
    td=tempfile.mkdtemp(prefix="clayspawn_httpdb_")
    sp=os.path.join(td,"generated_service.py"); dbp=os.path.join(td,"app.sqlite")
    with open(sp,"w") as f: f.write(code)
    p=subprocess.Popen([sys.executable,"-S",sp,dbp],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        line=p.stdout.readline().strip()
        if not line:
            return {"started":False,"stderr":p.stderr.read()}
        port=int(line)
        tests=[]
        def check(name, got, exp): tests.append({"name":name,"got":got,"expected":exp,"pass":got==exp})
        check("initial_count",request(port,"GET","/count"),(200,{"count":0}))
        check("create_alpha",request(port,"POST","/items",{"name":"alpha"}),(201,{"id":1,"name":"alpha"}))
        check("read_alpha",request(port,"GET","/items/1"),(200,{"id":1,"name":"alpha"}))
        check("create_beta_rollback",request(port,"POST","/items?fail=1",{"name":"beta"}),(500,{"error":"internal"}))
        check("rollback_count",request(port,"GET","/count"),(200,{"count":1}))
        check("create_gamma",request(port,"POST","/items",{"name":"gamma"}),(201,{"id":2,"name":"gamma"}))
        check("duplicate_conflict",request(port,"POST","/items",{"name":"alpha"}),(409,{"error":"conflict"}))
        if full:
            check("update_alpha",request(port,"PUT","/items/1",{"name":"alpha2"}),(200,{"id":1,"name":"alpha2"}))
            check("update_rollback",request(port,"PUT","/items/1?fail=1",{"name":"alpha3"}),(500,{"error":"internal"}))
            check("read_after_update_rollback",request(port,"GET","/items/1"),(200,{"id":1,"name":"alpha2"}))
            check("delete_rollback",request(port,"DELETE","/items/2?fail=1"),(500,{"error":"internal"}))
            check("read_after_delete_rollback",request(port,"GET","/items/2"),(200,{"id":2,"name":"gamma"}))
            check("delete_gamma",request(port,"DELETE","/items/2"),(204,None))
            check("read_deleted",request(port,"GET","/items/2"),(404,{"error":"not_found"}))
            check("invalid_name",request(port,"POST","/items",{"name":""}),(400,{"error":"invalid_name"}))
            check("method_reject",request(port,"PATCH","/items/1"),(405,{"error":"method_not_allowed"}))
            check("not_found",request(port,"GET","/items/999"),(404,{"error":"not_found"}))
        c=sqlite3.connect(dbp)
        try: rows=c.execute("select id,name from items order by id").fetchall()
        finally: c.close()
        return {
            "started":True,
            "tests_total":len(tests),
            "tests_passed":sum(t["pass"] for t in tests),
            "all_pass":all(t["pass"] for t in tests),
            "failures":[t for t in tests if not t["pass"]],
            "final_rows":rows,
        }
    finally:
        p.terminate()
        try: p.wait(timeout=1)
        except subprocess.TimeoutExpired: p.kill()

def mutate(code):
    return {
        "commit_before_failure": code.replace(
            'if parse_qs(u.query).get("fail")==["1"]: raise RuntimeError("injected")\n            c.commit(); return self.sendj(S["create"]',
            'c.commit()\n            if parse_qs(u.query).get("fail")==["1"]: raise RuntimeError("injected")\n            return self.sendj(S["create"]',1),
        "wrong_create_status": code.replace("'create': 201", "'create': 200",1),
        "drop_unique_constraint": code.replace("name TEXT NOT NULL UNIQUE","name TEXT NOT NULL"),
        "update_commit_before_failure": code.replace(
            'if parse_qs(u.query).get("fail")==["1"]: raise RuntimeError("injected")\n            c.commit(); return self.sendj(S["update"]',
            'c.commit()\n            if parse_qs(u.query).get("fail")==["1"]: raise RuntimeError("injected")\n            return self.sendj(S["update"]',1),
    }

def main():
    generated=lower(SPEC)
    base=execute(generated, full=True)
    mutants={name:execute(src,full=True) for name,src in mutate(generated).items()}
    out={
        "experiment_class":"LOCAL_HOST_PROXY_NOT_PRODUCTION_CLAYCODE",
        "semantic_spec_hash":canonical_hash(SPEC),
        "generated_target_hash":hashlib.sha256(generated.encode()).hexdigest(),
        "python":sys.version.split()[0],
        "sqlite":sqlite3.sqlite_version,
        "base":base,
        "mutations":{
            k:{
                "tests_total":v.get("tests_total"),
                "tests_passed":v.get("tests_passed"),
                "detected":not v.get("all_pass",False),
            } for k,v in mutants.items()
        },
    }
    print(json.dumps(out,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
