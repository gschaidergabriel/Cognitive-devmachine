#!/usr/bin/env python3
"""Publish third-swarm Evidence Forge metrics into free swarm/README.md."""
from __future__ import annotations
import argparse,datetime as dt,json
from pathlib import Path

BEGIN="<!-- EVIDENCE_FORGE_AUTO:BEGIN -->"; END="<!-- EVIDENCE_FORGE_AUTO:END -->"

def load(path:Path)->dict:
    if not path.exists():return {"state":"NOT_STARTED","generated_at":dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        x=json.loads(path.read_text(encoding="utf-8")); x["state"]="LIVE"; return x
    except Exception:return {"state":"BROKEN_STATUS","generated_at":dt.datetime.now(dt.timezone.utc).isoformat()}

def md(m:dict,free:dict,dist:dict)->str:
    total=((free.get("workers") or {}).get("total_tokens") or 0); accepted=int(m.get("accepted_deltas") or 0)
    per_m=(accepted*1_000_000/total) if total else 0.0
    lines=[BEGIN,"## AUTO — Evidence Forge / dritter autonomer Swarm",f"Aktualisiert: `{m.get('generated_at')}`","",
      "Zweck: **Aktivität → ausführbarer Patch/Test → reproduzierbare Architektur-Evidenz**. Der Forge nutzt primär andere Kapazitäten als die LLM-Swarms: OpenAlex, Crossref, Semantic Scholar, Hugging Face Hub, GitHub, lokale Disposable-Clones und — innerhalb eines harten Free-Credit-Budgets — parallele E2B-Sandboxes.","",
      "| Kennzahl | Wert |","|---|---:|",f"| Discovery-Queries | {m.get('discovery_queries',0)} |",f"| Discovery-Hits | {m.get('discovery_hits',0)} |",f"| Forge-Evaluierungen | {m.get('evaluations',0)} |",f"| evident akzeptierte Forge-Deltas | {accepted} |",f"| akzeptierte Deltas pro 1 Mio. Free-Swarm-Tokens | {per_m:.3f} |",f"| E2B-Reproduktionsjobs | {m.get('e2b_jobs',0)} |",f"| E2B-PASS | {m.get('e2b_pass',0)} |",f"| E2B kumulierte Sandbox-Sekunden | {m.get('e2b_sandbox_seconds',0)} |",f"| gemessener Forge-Peak parallel | {m.get('peak_parallel_tasks',0)} |",f"| Forge SQLite | {m.get('db_bytes',0):,} Byte |",""]
    lines += ["### Candidate-Zustände","| Zustand | Anzahl |","|---|---:|"]
    states=m.get("candidate_states") or {}
    if states:
        for k,v in sorted(states.items(),key=lambda x:(-x[1],x[0])):lines.append(f"| `{k}` | {v} |")
    else:lines.append("| — | 0 |")
    lines += ["","### Zusätzliche Tool-Quellen","| Tool/Quelle | Hits |","|---|---:|"]
    src=m.get("discovery_sources") or {}
    if src:
        for k,v in sorted(src.items(),key=lambda x:(-x[1],x[0])):lines.append(f"| `{k}` | {v} |")
    else:lines.append("| — | 0 |")
    budget=((m.get("shared_provider_budget") or {}).get("providers") or {})
    lines += ["","### Zentral beobachtete Provider-/Tool-Limits","| Provider/Tool | Max inflight | aktiv | Requests | 200 | 429 | Fehler |","|---|---:|---:|---:|---:|---:|---:|"]
    if budget:
        for k,v in sorted(budget.items()):lines.append(f"| `{k}` | {v.get('max_inflight',0)} | {v.get('active_leases',0)} | {v.get('total_requests',0)} | {v.get('total_success',0)} | {v.get('total_429',0)} | {v.get('total_errors',0)} |")
    else:lines.append("| — | 0 | 0 | 0 | 0 | 0 | 0 |")
    dy=dist.get("dataset_yield") if isinstance(dist,dict) else None
    lines += ["","### Produktivitätsdiagnose",f"- Free-Swarm-Tokenzähler sind **kumuliert über die vorhandenen Worker-Artefakte**, nicht 'aktuell aktive Credentials'. Dadurch ist die frühere Null-Baseline kein Widerspruch mehr, sondern eine historische Startmessung.",f"- Distillery Entity-Dataset-Yield: **{(dy*100):.3f}%**." if isinstance(dy,(int,float)) else "- Distillery Entity-Dataset-Yield: **UNKNOWN**.",f"- Forge Architecture-Conversion: **{per_m:.3f} akzeptierte Deltas / 1 Mio. Free-Swarm-Tokens**.","- Ein Forge-Delta zählt erst als `accepted`, wenn Patch/Test in einem Disposable-Clone mindestens zweimal reproduziert, negative/static checks bestanden und ein positiver Baseline-Unterschied oder Benchmarkvorteil gemessen wurde.",END]
    return "\n".join(lines)

def replace(path:Path,block:str):
    text=path.read_text(encoding="utf-8") if path.exists() else "# Free Swarm\n"
    if BEGIN in text and END in text:
        a=text.index(BEGIN); b=text.index(END,a)+len(END); text=text[:a]+block+text[b:]
    else:
        lines=text.splitlines(); text=(lines[0]+"\n\n"+block+"\n\n"+"\n".join(lines[1:]).lstrip()) if lines and lines[0].startswith("# ") else block+"\n\n"+text
    path.write_text(text.rstrip()+"\n",encoding="utf-8")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",default="/workspace/clay-global-research-entity");ap.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm");args=ap.parse_args();repo=Path(args.repo); art=Path(args.artifacts)
    m=load(art/"forge/STATUS.json")
    try:free=json.loads((repo/"free swarm/LIVE_METRICS.json").read_text(encoding="utf-8"))
    except Exception:free={}
    try:dist=json.loads((repo/"free swarm/DISTILLERY_LIVE.json").read_text(encoding="utf-8"))
    except Exception:dist={}
    replace(repo/"free swarm/README.md",md(m,free,dist)); (repo/"free swarm/FORGE_LIVE.json").write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); print(json.dumps({"state":m.get("state"),"evaluations":m.get("evaluations",0),"accepted":m.get("accepted_deltas",0)}))
if __name__=="__main__":main()
