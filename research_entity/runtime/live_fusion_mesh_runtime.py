#!/usr/bin/env python3
"""Executable research companion for Clay live-fusion causal mesh candidate.

Research candidate only. It does not replace CLAY_WORK_EVENT_PROTOCOL or grant truth/effect authority.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / 'research_entity/state/RAE_UNIFIED.sqlite'

SCHEMA = r'''
CREATE TABLE IF NOT EXISTS clay_live_fusion_pulses(
  pulse_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  parent_state_hash TEXT,
  semantic_epoch TEXT NOT NULL,
  origin_actor TEXT NOT NULL,
  origin_branch TEXT NOT NULL,
  ancestry_family TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  impact TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clay_live_fusion_targets(
  pulse_id TEXT NOT NULL,
  receiver TEXT NOT NULL,
  route_sources_json TEXT NOT NULL,
  state TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  acked_at TEXT,
  receiver_epoch TEXT,
  reason_json TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY(pulse_id,receiver),
  FOREIGN KEY(pulse_id) REFERENCES clay_live_fusion_pulses(pulse_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS clay_live_fusion_replans(
  receipt_id TEXT PRIMARY KEY,
  pulse_id TEXT NOT NULL,
  receiver TEXT NOT NULL,
  decision TEXT NOT NULL,
  old_revision_refs_json TEXT NOT NULL,
  new_revision_refs_json TEXT NOT NULL,
  invalidator_result_json TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(pulse_id) REFERENCES clay_live_fusion_pulses(pulse_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS clay_live_fusion_repairs(
  repair_id TEXT PRIMARY KEY,
  pulse_id TEXT NOT NULL,
  required_targets_json TEXT NOT NULL,
  missing_before_json TEXT NOT NULL,
  replayed_json TEXT NOT NULL,
  still_missing_json TEXT NOT NULL,
  converged INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(pulse_id) REFERENCES clay_live_fusion_pulses(pulse_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_lf_target_state ON clay_live_fusion_targets(state);
CREATE INDEX IF NOT EXISTS idx_lf_pulse_event ON clay_live_fusion_pulses(event_id);
'''

VALID_STATES={'ADDRESSED','DELIVERED','INGESTED','DEDUPED','REPLANNED','NO_CHANGE','REJECTED','EXPIRED'}
VALID_DECISIONS={'REVISE','CANCEL','DEFER','CONTINUE','NO_CHANGE'}


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def J(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',',':'))

def open_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(path, timeout=10)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=10000')
    c.executescript(SCHEMA)
    c.commit()
    return c

def pulse_id(event_id, semantic_epoch, payload):
    body=f'{event_id}\0{semantic_epoch}\0{J(payload)}'.encode()
    return 'pulse:'+hashlib.sha256(body).hexdigest()[:32]

def publish(c, *, event_id, semantic_epoch, origin_actor, origin_branch, ancestry_family,
            evidence_class, impact, payload, claygraph_targets, unifieddb_targets,
            parent_state_hash='UNKNOWN'):
    pid=pulse_id(event_id, semantic_epoch, payload)
    idem=hashlib.sha256((event_id+'\0'+semantic_epoch+'\0'+J(payload)).encode()).hexdigest()
    c.execute('''INSERT OR IGNORE INTO clay_live_fusion_pulses
      (pulse_id,event_id,idempotency_key,parent_state_hash,semantic_epoch,origin_actor,origin_branch,ancestry_family,evidence_class,impact,payload_json,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
      (pid,event_id,idem,parent_state_hash,semantic_epoch,origin_actor,origin_branch,ancestry_family,evidence_class,impact,J(payload),now()))
    route={}
    for r in set(claygraph_targets)|{origin_branch}: route.setdefault(r,set()).add('CLAYGRAPH')
    for r in set(unifieddb_targets)|{origin_branch}: route.setdefault(r,set()).add('UNIFIEDDB')
    for receiver,sources in route.items():
        c.execute('''INSERT OR IGNORE INTO clay_live_fusion_targets
          (pulse_id,receiver,route_sources_json,state,attempts,reason_json)
          VALUES(?,?,?,?,0,'{}')''',(pid,receiver,J(sorted(sources)),'ADDRESSED'))
    c.commit()
    return {'pulse_id':pid,'targets':sorted(route),'topology_disagreement':set(claygraph_targets)!=set(unifieddb_targets)}

def mark_attempt(c,pid,receiver):
    cur=c.execute('UPDATE clay_live_fusion_targets SET attempts=attempts+1 WHERE pulse_id=? AND receiver=?',(pid,receiver))
    if not cur.rowcount: raise KeyError((pid,receiver))
    c.commit()

def ack(c,pid,receiver,state,receiver_epoch='UNKNOWN',reason=None):
    if state not in VALID_STATES: raise ValueError(state)
    cur=c.execute('''UPDATE clay_live_fusion_targets SET state=?,acked_at=?,receiver_epoch=?,reason_json=?
                     WHERE pulse_id=? AND receiver=?''',(state,now(),receiver_epoch,J(reason or {}),pid,receiver))
    if not cur.rowcount: raise KeyError((pid,receiver))
    c.commit()

def replan(c,pid,receiver,decision,old_refs=None,new_refs=None,invalidator_result=None,evidence=None):
    if decision not in VALID_DECISIONS: raise ValueError(decision)
    rid='replan:'+hashlib.sha256((pid+'\0'+receiver+'\0'+decision+'\0'+J(new_refs or [])).encode()).hexdigest()[:32]
    c.execute('''INSERT OR IGNORE INTO clay_live_fusion_replans
      (receipt_id,pulse_id,receiver,decision,old_revision_refs_json,new_revision_refs_json,invalidator_result_json,evidence_json,created_at)
      VALUES(?,?,?,?,?,?,?,?,?)''',(rid,pid,receiver,decision,J(old_refs or []),J(new_refs or []),J(invalidator_result or {}),J(evidence or []),now()))
    new_state='NO_CHANGE' if decision=='NO_CHANGE' else 'REPLANNED'
    ack(c,pid,receiver,new_state,reason={'replan_receipt_id':rid})
    return rid

def status(c,pid):
    p=c.execute('SELECT * FROM clay_live_fusion_pulses WHERE pulse_id=?',(pid,)).fetchone()
    if not p: raise KeyError(pid)
    t=[dict(x) for x in c.execute('SELECT * FROM clay_live_fusion_targets WHERE pulse_id=? ORDER BY receiver',(pid,))]
    r=[dict(x) for x in c.execute('SELECT * FROM clay_live_fusion_replans WHERE pulse_id=? ORDER BY receiver',(pid,))]
    return {'pulse':dict(p),'targets':t,'replans':r}

def reconcile(c,pid,required_targets):
    rows={x['receiver']:x for x in c.execute('SELECT receiver,state FROM clay_live_fusion_targets WHERE pulse_id=?',(pid,))}
    accepted={'INGESTED','DEDUPED','REPLANNED','NO_CHANGE'}
    missing=sorted(r for r in set(required_targets) if r not in rows or rows[r]['state'] not in accepted)
    for r in missing:
        c.execute('''INSERT OR IGNORE INTO clay_live_fusion_targets
          (pulse_id,receiver,route_sources_json,state,attempts,reason_json)
          VALUES(?,?,?,?,0,?)''',(pid,r,J(['RECONCILIATION']),'ADDRESSED',J({'repair':'missing_target'})))
    rid='repair:'+hashlib.sha256((pid+'\0'+J(missing)+'\0'+now()).encode()).hexdigest()[:32]
    c.execute('''INSERT INTO clay_live_fusion_repairs
      (repair_id,pulse_id,required_targets_json,missing_before_json,replayed_json,still_missing_json,converged,created_at)
      VALUES(?,?,?,?,?,?,?,?)''',(rid,pid,J(sorted(set(required_targets))),J(missing),J(missing),J(missing),0 if missing else 1,now()))
    c.commit()
    return {'repair_id':rid,'missing_before':missing,'replayed':missing,'converged':not missing}

def finalize_repair(c,repair_id):
    rr=c.execute('SELECT * FROM clay_live_fusion_repairs WHERE repair_id=?',(repair_id,)).fetchone()
    if not rr: raise KeyError(repair_id)
    pid=rr['pulse_id']; required=json.loads(rr['required_targets_json'])
    rows={x['receiver']:x['state'] for x in c.execute('SELECT receiver,state FROM clay_live_fusion_targets WHERE pulse_id=?',(pid,))}
    accepted={'INGESTED','DEDUPED','REPLANNED','NO_CHANGE'}
    still=sorted(r for r in required if rows.get(r) not in accepted)
    c.execute('UPDATE clay_live_fusion_repairs SET still_missing_json=?,converged=? WHERE repair_id=?',(J(still),0 if still else 1,repair_id))
    c.commit(); return {'repair_id':repair_id,'still_missing':still,'converged':not still}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db',type=Path,default=DEFAULT_DB)
    sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('init')
    p=sp.add_parser('publish'); p.add_argument('--event-id',required=True);p.add_argument('--semantic-epoch',required=True);p.add_argument('--origin-actor',required=True);p.add_argument('--origin-branch',required=True);p.add_argument('--ancestry-family',default='UNKNOWN');p.add_argument('--evidence-class',default='UNVERIFIED');p.add_argument('--impact',default='NORMAL');p.add_argument('--payload-json',default='{}');p.add_argument('--claygraph-target',action='append',default=[]);p.add_argument('--unifieddb-target',action='append',default=[])
    a=sp.add_parser('ack');a.add_argument('--pulse-id',required=True);a.add_argument('--receiver',required=True);a.add_argument('--state',required=True);a.add_argument('--receiver-epoch',default='UNKNOWN')
    s=sp.add_parser('status');s.add_argument('--pulse-id',required=True)
    r=sp.add_parser('reconcile');r.add_argument('--pulse-id',required=True);r.add_argument('--required-target',action='append',default=[])
    args=ap.parse_args();c=open_db(args.db)
    try:
        if args.cmd=='init': out={'initialized':str(args.db)}
        elif args.cmd=='publish': out=publish(c,event_id=args.event_id,semantic_epoch=args.semantic_epoch,origin_actor=args.origin_actor,origin_branch=args.origin_branch,ancestry_family=args.ancestry_family,evidence_class=args.evidence_class,impact=args.impact,payload=json.loads(args.payload_json),claygraph_targets=args.claygraph_target,unifieddb_targets=args.unifieddb_target)
        elif args.cmd=='ack': ack(c,args.pulse_id,args.receiver,args.state,args.receiver_epoch);out={'acked':True}
        elif args.cmd=='status': out=status(c,args.pulse_id)
        else: out=reconcile(c,args.pulse_id,args.required_target)
        print(J(out))
    finally:c.close()

if __name__=='__main__': main()
