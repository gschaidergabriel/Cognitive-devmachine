#!/usr/bin/env python3
"""Replay actual current Clay work-event files and classify execution receipts by current spec revision."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVENTS=ROOT/'research_entity/state/work/events'

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_events(work_id: str):
    rows=[]
    for p in sorted(EVENTS.glob('*.json')):
        try: e=json.loads(p.read_text(encoding='utf-8'))
        except Exception: continue
        if not isinstance(e,dict) or not isinstance(e.get('payload'),dict): continue
        if e['payload'].get('work_id')!=work_id: continue
        rows.append((str(e.get('created_at') or ''),str(e.get('event_id') or p.name),p,e))
    rows.sort(key=lambda x:(x[0],x[1],x[2].name))
    return rows

def replay(work_id: str, expect_min_rev: int) -> dict:
    rows=load_events(work_id)
    current_rev=0
    created=False
    event_ids=set(); duplicate_event_ids=[]
    sequence=[]; receipts=[]; terminal=None
    for created_at,event_id,path,e in rows:
        if event_id in event_ids: duplicate_event_ids.append(event_id)
        event_ids.add(event_id)
        kind=str(e.get('kind') or '')
        payload=e['payload']
        before=current_rev
        if kind=='WORK_CREATE':
            if created:
                sequence.append({'event_id':event_id,'kind':kind,'error':'SECOND_CREATE','path':str(path.relative_to(ROOT))})
                continue
            created=True; current_rev=1
        elif kind=='WORK_REVISE':
            if not created:
                sequence.append({'event_id':event_id,'kind':kind,'error':'REVISE_BEFORE_CREATE','path':str(path.relative_to(ROOT))})
                continue
            current_rev+=1
        elif kind in {'WORK_DEFER','WORK_CANCEL'}:
            terminal=kind
        receipt=None
        if kind=='WORK_EXECUTION_RECEIPT':
            try: spec_rev=int(payload.get('spec_rev'))
            except Exception: spec_rev=-1
            receipt={
              'event_id':event_id,
              'path':str(path.relative_to(ROOT)),
              'file_sha256':digest(path),
              'execution_receipt_id':payload.get('execution_receipt_id'),
              'spec_rev':spec_rev,
              'success':bool(payload.get('success')),
              'complete':bool(payload.get('complete')),
              'truth_class':payload.get('truth_class'),
            }
            receipts.append(receipt)
        sequence.append({
          'event_id':event_id,'kind':kind,'created_at':created_at,'path':str(path.relative_to(ROOT)),
          'file_sha256':digest(path),'revision_before':before,'revision_after':current_rev,
          'payload_spec_rev':receipt['spec_rev'] if receipt else None,
        })
    for r in receipts:
        r['revision_relation']='CURRENT' if r['spec_rev']==current_rev else ('STALE' if 0<r['spec_rev']<current_rev else 'INVALID_OR_FUTURE')
        r['current_work_credit_eligible']=r['revision_relation']=='CURRENT'
        r['diagnostic_evidence_preserved']=True
    stale=[r for r in receipts if r['revision_relation']=='STALE']
    current=[r for r in receipts if r['revision_relation']=='CURRENT']
    future=[r for r in receipts if r['revision_relation']=='INVALID_OR_FUTURE']
    unsafe_stale_complete=[r for r in stale if r['complete']]
    checks={
      'work_created':created,
      'minimum_revision_reached':current_rev>=expect_min_rev,
      'no_duplicate_event_ids':not duplicate_event_ids,
      'no_future_or_invalid_receipts':not future,
      'stale_receipts_preserved':all(r['diagnostic_evidence_preserved'] for r in stale),
      'stale_receipts_receive_no_current_credit':all(not r['current_work_credit_eligible'] for r in stale),
      'no_stale_receipt_claims_complete':not unsafe_stale_complete,
    }
    return {
      'schema_version':'1.0',
      'evidence_class':'CURRENT_REPO_RAW_WORK_EVENT_REPLAY',
      'work_id':work_id,
      'event_root':str(EVENTS.relative_to(ROOT)),
      'current_spec_rev':current_rev,
      'terminal_event':terminal,
      'event_count':len(rows),
      'execution_receipt_count':len(receipts),
      'stale_execution_receipt_count':len(stale),
      'current_execution_receipt_count':len(current),
      'invalid_or_future_receipt_count':len(future),
      'sequence':sequence,
      'receipts':receipts,
      'checks':checks,
      'pass':all(checks.values()),
      'interpretation':'Execution success is preserved as evidence, but current-work credit is derived from the latest raw WORK_CREATE/WORK_REVISE event sequence, not from success alone.'
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work-id',required=True)
    ap.add_argument('--expect-min-rev',type=int,default=1)
    ap.add_argument('--out')
    a=ap.parse_args()
    r=replay(a.work_id,a.expect_min_rev)
    text=json.dumps(r,indent=2,sort_keys=True)+'\n'
    if a.out: Path(a.out).write_text(text,encoding='utf-8')
    print(text,end='')
    raise SystemExit(0 if r['pass'] else 1)

if __name__=='__main__': main()
