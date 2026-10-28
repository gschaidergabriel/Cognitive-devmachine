#!/usr/bin/env python3
"""Compact GRID state projection. SQLite stays on the host; Git transports deltas.

No independent GRID authority: this module is a materialized exchange cache only.
Use GRID10's existing lease/CAS commit path to adopt proposed updates.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

SCHEMA = "OMEGA_GRID_DELTA/v1"
HOSTS = {"gabriel": "ai-core-node", "andreas": "andreas-maco"}
DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY, owner TEXT NOT NULL, machine_id TEXT NOT NULL,
  scope TEXT NOT NULL, entity TEXT NOT NULL, revision INTEGER NOT NULL,
  operation TEXT NOT NULL, payload TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
  parent_event_id TEXT, committed_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(owner,machine_id,scope,entity,revision);
CREATE TABLE IF NOT EXISTS state (
  owner TEXT NOT NULL,machine_id TEXT NOT NULL,scope TEXT NOT NULL,
  entity TEXT NOT NULL,revision INTEGER NOT NULL,event_id TEXT NOT NULL,
  payload TEXT NOT NULL,PRIMARY KEY(owner,machine_id,scope,entity));
"""
def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=False)

def digest(obj):
    return hashlib.sha256(canon(obj).encode()).hexdigest()

def connect(path):
    p = Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    db = sqlite3.connect(str(p))
    db.executescript(DDL)
    return db

def validate(packet):
    if packet.get("schema") != SCHEMA: raise ValueError("schema mismatch")
    owner = packet.get("owner")
    if owner not in HOSTS or packet.get("machine_id") != HOSTS[owner]:
        raise ValueError("owner/host mismatch")
    if packet.get("operation") not in ("replace","merge","delete_proposal"):
        raise ValueError("invalid operation")
    if not isinstance(packet.get("revision"),int) or packet["revision"] < 1:
        raise ValueError("invalid revision")
    for k in ("scope","entity","committed_at","event_id"):
        if not isinstance(packet.get(k),str) or not packet[k] or len(packet[k])>256:
            raise ValueError("invalid "+k)
    if not isinstance(packet.get("payload"),dict):
        raise ValueError("payload must be object")
    if packet.get("payload_sha256") != digest(packet["payload"]):
        raise ValueError("payload hash mismatch")
    identity = {k:packet[k] for k in ("schema","owner","machine_id","scope","entity","revision","operation","payload_sha256","parent_event_id","committed_at")}
    if packet["event_id"] != digest(identity):
        raise ValueError("event id mismatch")

def make(owner,scope,entity,revision,operation,payload,parent_event_id,committed_at):
    if owner not in HOSTS: raise ValueError("unknown owner")
    d = dict(schema=SCHEMA,owner=owner,machine_id=HOSTS[owner],
             scope=scope,entity=entity,revision=revision,operation=operation,
             payload=payload,payload_sha256=digest(payload),
             parent_event_id=parent_event_id,committed_at=committed_at)
    d["event_id"]=digest({k:v for k,v in d.items() if k not in ("payload","event_id")})
    validate(d)
    return d

def apply(db,packet):
    validate(packet)
    key=(packet["owner"],packet["machine_id"],packet["scope"],packet["entity"])
    with db:
        current=db.execute("SELECT revision,event_id,payload FROM state WHERE owner=? AND machine_id=? AND scope=? AND entity=?",key).fetchone()
        exists=db.execute("SELECT 1 FROM events WHERE event_id=?",(packet["event_id"],)).fetchone()
        if exists: return "duplicate"
        expected_rev=(current[0]+1) if current else 1
        expected_parent=current[1] if current else None
        if packet["revision"] != expected_rev or packet["parent_event_id"] != expected_parent:
            raise ValueError("revision/parent CAS failure")
        if packet["operation"]=="merge":
            base=json.loads(current[2]) if current else {}
            merged={**base,**packet["payload"]}
        elif packet["operation"]=="replace":
            merged=packet["payload"]
        else:
            # A deletion proposal is NOT an authorized delete; do not remove state.
            merged=json.loads(current[2]) if current else {}
        db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
          (packet["event_id"],*key,packet["revision"],packet["operation"],
           canon(packet["payload"]),packet["payload_sha256"],
           packet["parent_event_id"],packet["committed_at"]))
        db.execute("INSERT INTO state VALUES (?,?,?,?,?,?,?) ON CONFLICT(owner,machine_id,scope,entity) DO UPDATE SET revision=excluded.revision,event_id=excluded.event_id,payload=excluded.payload",
          (*key,packet["revision"],packet["event_id"],canon(merged)))
    return "applied"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",required=True)
    sub=ap.add_subparsers(dest="cmd",required=True)
    incoming=sub.add_parser("apply");incoming.add_argument("json_file")
    show=sub.add_parser("get");show.add_argument("owner",choices=HOSTS);show.add_argument("scope");show.add_argument("entity")
    proposal=sub.add_parser("propose")
    proposal.add_argument("owner",choices=HOSTS);proposal.add_argument("scope");proposal.add_argument("entity")
    proposal.add_argument("operation",choices=["replace","merge","delete_proposal"])
    proposal.add_argument("payload_file");proposal.add_argument("--at",required=True)
    a=ap.parse_args();db=connect(a.db)
    if a.cmd=="apply":
        print(apply(db,json.loads(Path(a.json_file).read_text())))
    elif a.cmd=="get":
        r=db.execute("SELECT revision,event_id,payload FROM state WHERE owner=? AND machine_id=? AND scope=? AND entity=?",(a.owner,HOSTS[a.owner],a.scope,a.entity)).fetchone()
        print(canon({"revision":r[0],"event_id":r[1],"state":json.loads(r[2])} if r else None))
    else:
        r=db.execute("SELECT revision,event_id FROM state WHERE owner=? AND machine_id=? AND scope=? AND entity=?",(a.owner,HOSTS[a.owner],a.scope,a.entity)).fetchone()
        packet=make(a.owner,a.scope,a.entity,r[0]+1 if r else 1,a.operation,json.loads(Path(a.payload_file).read_text()),r[1] if r else None,a.at)
        print(canon(packet))
if __name__=="__main__":main()
