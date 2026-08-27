#!/usr/bin/env python3
"""Register authorship/provenance for a durable artifact.

Example:
  python tools/register_provenance.py reports/live_frank_audit.md \
    --actor claude-code-lead --model 'Claude Code <actual model>'

The script computes SHA-256 and appends an immutable attribution record. It does not
change scientific claim status and does not make an artifact true merely by registering it.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'research_entity'/'global'/'RESEARCH_ACTOR_REGISTRY.json'
LEDGER=ROOT/'research_entity'/'provenance'/'ARTIFACT_PROVENANCE.jsonl'

def git_head():
    try:
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--actor',required=True)
    ap.add_argument('--model',default='')
    ap.add_argument('--runtime',default='')
    ap.add_argument('--session-id',default='')
    ap.add_argument('--prompt-run-id',default='')
    ap.add_argument('--note',default='')
    args=ap.parse_args()

    reg=json.loads(REGISTRY.read_text(encoding='utf-8'))
    actors={a['actor_id']:a for a in reg['actors']}
    if args.actor not in actors:
        raise SystemExit(f'Unknown actor {args.actor!r}; register actor first.')
    actor=actors[args.actor]

    p=(ROOT/args.path).resolve()
    try: rel=str(p.relative_to(ROOT))
    except ValueError: raise SystemExit('Artifact must be inside repository root')
    if not p.is_file(): raise SystemExit(f'Not a file: {rel}')
    data=p.read_bytes(); sha=hashlib.sha256(data).hexdigest()
    now=datetime.now(timezone.utc).isoformat()
    provider=actor.get('organization') or ('human' if actor.get('role','').startswith('PROJECT_OWNER') else '')
    pid='PV-'+args.actor.upper().replace('_','-')+'-'+sha[:16]+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    record={
      'provenance_id':pid,
      'path':rel,
      'content_sha256':sha,
      'origin_actor':args.actor,
      'actor_role':actor.get('role',''),
      'provider':provider,
      'model':args.model,
      'runtime':args.runtime,
      'session_id':args.session_id,
      'prompt_run_id':args.prompt_run_id,
      'created_at':now,
      'git_parent_at_registration':git_head(),
      'attribution_confidence':'VERIFIED',
      'note':args.note
    }
    LEDGER.parent.mkdir(parents=True,exist_ok=True)
    with LEDGER.open('a',encoding='utf-8') as f:
        f.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
