#!/usr/bin/env python3
"""Fail-closed preflight for RAE workers.

This does not create scientific state. It verifies that a worker is booting against a
coherent canonical head and emits a compact join receipt that agent runners can attach
to a prompt/run record before substantive work.
"""
from __future__ import annotations
import argparse, hashlib, json, os, socket, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'research_entity'/'continuity'/'RESEARCH_ENTITY_CANONICAL.json'
BOOT=ROOT/'research_entity'/'continuity'/'BOOTSTRAP_MINIMAL.json'
MEMBERSHIP=ROOT/'research_entity'/'global'/'SESSION_MEMBERSHIP_PROTOCOL.md'
DOMAINS=ROOT/'research_entity'/'global'/'DOMAIN_REGISTRY.json'


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--task',default='')
    ap.add_argument('--worker-id',default='')
    ap.add_argument('--json-out',default='')
    args=ap.parse_args()
    missing=[str(p.relative_to(ROOT)) for p in [CANON,BOOT,MEMBERSHIP,DOMAINS] if not p.exists()]
    receipt={
      'receipt_version':'1.0',
      'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      'host':socket.gethostname(),
      'pid':os.getpid(),
      'worker_id':args.worker_id or f'worker-{socket.gethostname()}-{os.getpid()}',
      'task_digest':hashlib.sha256(args.task.encode()).hexdigest() if args.task else None,
      'status':'DEGRADED_UNJOINED' if missing else 'PENDING_VERIFY',
      'missing':missing
    }
    if not missing:
        c=json.loads(CANON.read_text(encoding='utf-8'))
        b=json.loads(BOOT.read_text(encoding='utf-8'))
        problems=[]
        if c.get('entity_version') != b.get('expected_entity_version'): problems.append('entity_version_mismatch')
        if c.get('revision') != b.get('expected_revision'): problems.append('revision_mismatch')
        if c.get('state_hash') != b.get('expected_state_hash'): problems.append('state_hash_mismatch')
        receipt.update({
          'canonical_revision':c.get('revision'),
          'canonical_state_hash':c.get('state_hash'),
          'canonical_file_sha256':sha256(CANON),
          'bootstrap_file_sha256':sha256(BOOT),
          'membership_file_sha256':sha256(MEMBERSHIP),
          'problems':problems,
          'status':'DEGRADED_UNJOINED' if problems else 'JOINED_READY_FOR_ROUTING'
        })
    text=json.dumps(receipt,ensure_ascii=False,indent=2)
    print(text)
    if args.json_out:
        out=Path(args.json_out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(text+'\n',encoding='utf-8')
    return 0 if receipt['status']=='JOINED_READY_FOR_ROUTING' else 2

if __name__=='__main__':
    raise SystemExit(main())
