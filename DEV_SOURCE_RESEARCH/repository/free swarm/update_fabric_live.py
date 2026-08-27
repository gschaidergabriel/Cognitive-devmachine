#!/usr/bin/env python3
"""Keep the current 6000-worker fabric visible at the top of free swarm/README.md.

Only metadata/counters are read; secret values are never read or rendered.
"""
from __future__ import annotations
import argparse, datetime as dt, json, time
from pathlib import Path

BEGIN='<!-- FABRIC_6000_AUTO:BEGIN -->'
END='<!-- FABRIC_6000_AUTO:END -->'


def load(path:Path)->dict:
    try:
        x=json.loads(path.read_text(encoding='utf-8')); return x if isinstance(x,dict) else {}
    except Exception:return {}


def catalog_counts(repo:Path)->dict[str,int]:
    x=load(repo/'agentZero/tresor/kataloge.json'); out={p:0 for p in ('groq','mistral','nvidia','openrouter')}
    for row in ((x.get('api') or {}).get('eintraege') or []):
        if not isinstance(row,dict):continue
        a=str(row.get('anbieter') or '').lower()
        for p in out:
            if a==p or a.startswith(p): out[p]+=1
    return out


def latest_status(art:Path)->dict:
    xs=sorted(art.glob('active-fabric6000-v2-*/status.json'),key=lambda p:p.stat().st_mtime if p.exists() else 0,reverse=True)
    return load(xs[0]) if xs else {}


def receipt_count(art:Path)->int:
    p=art/'free_lane_execution_receipts.jsonl'
    try:
        with p.open('rb') as f:return sum(1 for line in f if line.strip())
    except OSError:return 0


def block(repo:Path,art:Path)->str:
    sup=load(art/'SUPERVISOR_6000.json'); fabric=sup.get('fabric') if isinstance(sup.get('fabric'),dict) else {}
    if not fabric or str(fabric.get('schema','')).endswith('FINAL/v2'):
        live=latest_status(art)
        if live:fabric=live
    pool=load(art/'CREDENTIAL_POOL.json'); material=((pool.get('providers') or {}) if isinstance(pool,dict) else {})
    cat=catalog_counts(repo); providers=fabric.get('providers') or {}; now=dt.datetime.now(dt.timezone.utc).isoformat()
    logical=int(fabric.get('logical_workers_configured') or sup.get('logical_workers_requested') or 0)
    active=int(fabric.get('actual_model_calls_inflight') or 0); target=int(fabric.get('adaptive_provider_target_inflight') or 0)
    hard=int(fabric.get('provider_hard_ceiling_sum') or 0); waiting=int(fabric.get('logical_workers_waiting') or max(0,logical-active))
    successful=int(fabric.get('successful_calls') or 0); receipts=receipt_count(art)
    util=(100.0*active/target) if target else 0.0
    lines=[BEGIN,'## AUTO — 6000er Free-Swarm Fabric — LIVE',f'Aktualisiert: `{now}`','',
      '**Wichtig:** `6000` sind gleichzeitig vorgehaltene logische Forschungsorgane. `actual model calls inflight` ist die reale externe Inference-Parallelität. Beide Zahlen werden getrennt gemessen.','',
      '| Live-Kennzahl | Wert |','|---|---:|',
      f'| logische Forschungsorgane | **{logical:,}** |',f'| aktuell wartend | {waiting:,} |',f'| **echte Model-Calls gleichzeitig aktiv** | **{active:,}** |',
      f'| adaptives Inference-Ziel | {target:,} |',f'| Zielauslastung | {util:.1f}% |',f'| Summe lokaler Hard-Ceilings | {hard:,} |',
      f'| erfolgreiche Calls dieses Fabric-Runs | {successful:,} |',f'| wirtschaftlich gebundene FREE_LANE receipts kumuliert | {receipts:,} |',
      f'| Global Work-Stealing | {"JA" if fabric.get("work_stealing") else "NEIN"} |','',
      '### Provider-Verteilung — real materialisiert vs. Katalog','| Provider | Keys jetzt materialisiert | Katalog-Einträge (nur Inventar) | aktiv | Ziel | Hard max | Success | 429 | Fehler | Cooldown s |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for p in ('nvidia','groq','openrouter','mistral'):
        r=providers.get(p) or {}; m=material.get(p) or {}
        lines.append(f'| `{p}` | {int(m.get("keys") or 0)} | {cat.get(p,0)} | {int(r.get("active") or 0)} | {int(r.get("target_concurrency") or 0)} | {int(r.get("max_concurrency") or 0)} | {int(r.get("successes") or 0)} | {int(r.get("rate_limits") or 0)} | {int(r.get("errors") or 0)} | {float(r.get("cooldown_seconds") or 0):.1f} |')
    roles=fabric.get('role_assignments') or {}
    lines += ['','### Arbeitsteilung dieses Runs','| Rolle | gestartete Aufgaben |','|---|---:|']
    if roles:
        for k,v in sorted(roles.items(),key=lambda kv:(-int(kv[1]),kv[0])): lines.append(f'| `{k}` | {int(v)} |')
    else: lines.append('| — | 0 |')
    assigns=fabric.get('provider_assignments') or {}
    if assigns:
        lines += ['','Provider-Zuteilungen seit Run-Start: '+', '.join(f'`{k}`={int(v)}' for k,v in sorted(assigns.items()))+'.']
    lines += ['','Katalogzahlen sind **keine** Behauptung, dass diese Schlüssel aktuell vorhanden oder nutzbar sind. Nur `CREDENTIAL_POOL.json` zählt als materialisierte Runtime-Kapazität.',END]
    return '\n'.join(lines)


def replace(readme:Path,b:str)->None:
    text=readme.read_text(encoding='utf-8') if readme.exists() else '# Free Swarm\n'
    if BEGIN in text and END in text:
        a=text.index(BEGIN); z=text.index(END,a)+len(END); text=text[:a]+b+text[z:]
    else:
        lines=text.splitlines(); text=(lines[0]+'\n\n'+b+'\n\n'+'\n'.join(lines[1:]).lstrip()) if lines and lines[0].startswith('# ') else b+'\n\n'+text
    readme.write_text(text.rstrip()+'\n',encoding='utf-8')


def once(repo:Path,art:Path)->None:
    b=block(repo,art); replace(repo/'free swarm/README.md',b); (repo/'free swarm/FABRIC_6000_LIVE.json').write_text(json.dumps({'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'supervisor':load(art/'SUPERVISOR_6000.json'),'credential_pool':load(art/'CREDENTIAL_POOL.json'),'economic_receipts':receipt_count(art)},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',default='/workspace/clay-global-research-entity'); ap.add_argument('--artifacts',default='/artifacts/clay-entityos-swarm'); ap.add_argument('--watch',action='store_true'); ap.add_argument('--interval-seconds',type=float,default=30); a=ap.parse_args(); repo=Path(a.repo); art=Path(a.artifacts)
    if not a.watch: once(repo,art); return 0
    while True:
        try: once(repo,art)
        except Exception: pass
        time.sleep(max(5.0,a.interval_seconds))

if __name__=='__main__':raise SystemExit(main())
