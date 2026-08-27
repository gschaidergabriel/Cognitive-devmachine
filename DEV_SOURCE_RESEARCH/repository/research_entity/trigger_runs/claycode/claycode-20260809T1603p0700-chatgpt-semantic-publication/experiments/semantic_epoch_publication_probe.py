from __future__ import annotations
import sqlite3, json, hashlib, random, time, sys
from dataclasses import dataclass

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE semantic_state(
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);
CREATE TABLE tx(
  id TEXT PRIMARY KEY,
  idem TEXT UNIQUE NOT NULL,
  base_epoch INTEGER NOT NULL,
  committed_epoch INTEGER,
  status TEXT NOT NULL
);
CREATE TABLE state_epoch(
  epoch INTEGER PRIMARY KEY,
  root_hash TEXT NOT NULL,
  tx_id TEXT NOT NULL
);
CREATE TABLE graph_epoch(
  graph_epoch INTEGER PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  projection_closed INTEGER NOT NULL,
  retraction_closed INTEGER NOT NULL,
  projection_hash TEXT NOT NULL
);
CREATE TABLE publication(
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  state_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  receipt_hash TEXT NOT NULL
);
INSERT INTO publication VALUES(1,0,0,'genesis');
"""

@dataclass(frozen=True)
class Capability:
    issuer: str
    permits: tuple[str,...]
    valid: bool = True
    revoked: bool = False

class Probe:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA)
        self.db.commit()

    def published(self):
        return self.db.execute("select state_epoch,graph_epoch,receipt_hash from publication where singleton=1").fetchone()

    def latest_state(self):
        row=self.db.execute("select coalesce(max(epoch),0) from state_epoch").fetchone()
        return int(row[0])

    def commit_state(self, tx_id, idem, base_epoch, payload, writer_authorized=True):
        prior=self.db.execute("select committed_epoch from tx where idem=?",(idem,)).fetchone()
        if prior:
            return {"ok":True,"replayed":True,"state_epoch":prior[0]}
        if not writer_authorized:
            return {"ok":False,"reason":"WRITER_AUTHORITY"}
        if base_epoch != self.latest_state():
            return {"ok":False,"reason":"BASE_EPOCH_MISMATCH"}
        next_epoch=base_epoch+1
        root=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        with self.db:
            self.db.execute("insert into tx(id,idem,base_epoch,committed_epoch,status) values(?,?,?,?,?)",
                            (tx_id,idem,base_epoch,next_epoch,"COMMITTED"))
            self.db.execute("insert into state_epoch(epoch,root_hash,tx_id) values(?,?,?)",(next_epoch,root,tx_id))
        return {"ok":True,"replayed":False,"state_epoch":next_epoch,"root_hash":root}

    def project_graph(self, source_epoch, projection_closed=True, retraction_closed=True):
        ge=(self.db.execute("select coalesce(max(graph_epoch),0)+1 from graph_epoch").fetchone()[0])
        ph=hashlib.sha256(f"{source_epoch}|{ge}|{projection_closed}|{retraction_closed}".encode()).hexdigest()
        with self.db:
            self.db.execute("insert into graph_epoch values(?,?,?,?,?)",
                            (ge,source_epoch,int(projection_closed),int(retraction_closed),ph))
        return {"graph_epoch":ge,"source_epoch":source_epoch,"projection_hash":ph,
                "projection_closed":projection_closed,"retraction_closed":retraction_closed}

    def publish(self, state_epoch, graph_epoch):
        s=self.db.execute("select root_hash from state_epoch where epoch=?",(state_epoch,)).fetchone()
        g=self.db.execute("select source_epoch,projection_closed,retraction_closed,projection_hash from graph_epoch where graph_epoch=?",(graph_epoch,)).fetchone()
        if not s: return {"ok":False,"reason":"UNKNOWN_STATE_EPOCH"}
        if not g: return {"ok":False,"reason":"UNKNOWN_GRAPH_EPOCH"}
        if g[0] != state_epoch: return {"ok":False,"reason":"SOURCE_EPOCH_MISMATCH"}
        if not g[1]: return {"ok":False,"reason":"PROJECTION_OPEN"}
        if not g[2]: return {"ok":False,"reason":"RETRACTION_OPEN"}
        receipt=hashlib.sha256(f"{state_epoch}|{graph_epoch}|{s[0]}|{g[3]}".encode()).hexdigest()
        with self.db:
            self.db.execute("update publication set state_epoch=?,graph_epoch=?,receipt_hash=? where singleton=1",
                            (state_epoch,graph_epoch,receipt))
        return {"ok":True,"receipt_hash":receipt}

def effect_allowed(graph_relation_present: bool, cap: Capability|None):
    return bool(cap and cap.valid and not cap.revoked and cap.issuer=="HOST_AUTHORITY" and "COMMIT" in cap.permits)

def fixed_cases():
    p=Probe()
    out=[]
    def add(name, observed, expected):
        out.append({"case":name,"observed":observed,"expected":expected,"match":observed==expected})

    c1=p.commit_state("t1","i1",0,{"x":1})
    g1=p.project_graph(c1["state_epoch"])
    add("coherent_publish", p.publish(c1["state_epoch"],g1["graph_epoch"])["ok"], True)
    pub1=p.published()

    add("base_epoch_mismatch", p.commit_state("tbad","ibad",0,{"x":2})["reason"], "BASE_EPOCH_MISMATCH")

    c2=p.commit_state("t2","i2",1,{"x":2})
    gstale=p.project_graph(1)
    add("stale_graph_source_rejected", p.publish(c2["state_epoch"],gstale["graph_epoch"])["reason"], "SOURCE_EPOCH_MISMATCH")

    gopen=p.project_graph(c2["state_epoch"],projection_closed=False)
    add("projection_open_rejected", p.publish(c2["state_epoch"],gopen["graph_epoch"])["reason"], "PROJECTION_OPEN")

    gretract=p.project_graph(c2["state_epoch"],retraction_closed=False)
    add("retraction_open_rejected", p.publish(c2["state_epoch"],gretract["graph_epoch"])["reason"], "RETRACTION_OPEN")

    add("crash_after_state_commit_keeps_prior_reader_epoch", p.published()[:2], pub1[:2])

    grec=p.project_graph(c2["state_epoch"])
    add("recovery_publish", p.publish(c2["state_epoch"],grec["graph_epoch"])["ok"], True)
    pub2=p.published()
    add("recovery_reader_epoch_coherent", pub2[0]==c2["state_epoch"] and pub2[1]==grec["graph_epoch"], True)

    before=p.latest_state()
    replay=p.commit_state("t2-again","i2",1,{"x":999})
    add("idempotent_replay_same_epoch", (replay["replayed"],replay["state_epoch"],p.latest_state()), (True,c2["state_epoch"],before))

    add("graph_relation_alone_no_effect_authority", effect_allowed(True,None), False)
    add("valid_host_capability_authorizes_independently", effect_allowed(True,Capability("HOST_AUTHORITY",("COMMIT",))), True)
    add("revoked_capability_rejected", effect_allowed(True,Capability("HOST_AUTHORITY",("COMMIT",),True,True)), False)
    return out

def mutation(seed=20260809, rounds=20000):
    rng=random.Random(seed)
    violations=[]
    accepted=0
    rejected=0
    for i in range(rounds):
        p=Probe()
        c=p.commit_state("t","idem",0,{"i":i})
        source = c["state_epoch"] if rng.random()<0.75 else 0
        proj_closed = rng.random()<0.85
        retract_closed = rng.random()<0.85
        g=p.project_graph(source,proj_closed,retract_closed)
        before=p.published()
        r=p.publish(c["state_epoch"],g["graph_epoch"])
        after=p.published()
        should = (source==c["state_epoch"] and proj_closed and retract_closed)
        if r["ok"]: accepted += 1
        else: rejected += 1
        if r["ok"] != should:
            violations.append({"i":i,"kind":"ADMISSION_MISMATCH","params":[source,proj_closed,retract_closed],"r":r})
            break
        if not r["ok"] and after != before:
            violations.append({"i":i,"kind":"MIXED_EPOCH_VISIBLE","before":before,"after":after})
            break
        if effect_allowed(True,None):
            violations.append({"i":i,"kind":"GRAPH_AUTHORITY_ESCALATION"})
            break
    return {"seed":seed,"rounds":rounds,"accepted":accepted,"rejected":rejected,"violations":violations}

def main():
    t0=time.perf_counter()
    fixed=fixed_cases()
    mut=mutation()
    result={
        "experiment":"ClayCode G9 semantic publication barrier representability proxy",
        "scope":"run-local executable semantic oracle; not production ClayCode parser/compiler evidence",
        "fixed":fixed,
        "fixed_pass":sum(x["match"] for x in fixed),
        "fixed_total":len(fixed),
        "mutation":mut,
        "all_ok":all(x["match"] for x in fixed) and not mut["violations"],
        "elapsed_ms":round((time.perf_counter()-t0)*1000,3)
    }
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0 if result["all_ok"] else 1

if __name__=="__main__":
    raise SystemExit(main())
