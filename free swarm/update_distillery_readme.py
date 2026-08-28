#!/usr/bin/env python3
"""Refresh the Research Distillery section in free swarm/README.md.

After the Distillery block this updater also invokes update_system_analysis.py so
the autonomous publisher cannot refresh compact metrics while dropping the
script-by-script, GO-flow and Sonnet-cost analysis.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

BEGIN="<!-- RESEARCH_DISTILLERY_AUTO:BEGIN -->"
END="<!-- RESEARCH_DISTILLERY_AUTO:END -->"


def q(con,sql,args=()):return con.execute(sql,args).fetchall()


def load(db:Path)->dict:
    if not db.exists():
        return {"state":"NOT_STARTED","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"collected_source_tokens":0,"accepted_dataset_tokens":0,"dataset_yield":0.0,"compression_factor":None,"accepted_packets":0,"rejected_candidates":0,"questions":{},"sources":{},"reviewers":[],"small_models":[],"provider_budget":{},"counters":{}}
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    counters={r[0]:int(r[1]) for r in q(con,"SELECT key,value FROM counters")}
    collected=counters.get("collected_source_tokens",0); accepted=counters.get("accepted_dataset_tokens",0)
    questions={r[0]:r[1] for r in q(con,"SELECT status,COUNT(*) FROM questions GROUP BY status")}
    sources={r[0]:r[1] for r in q(con,"SELECT source_type,COUNT(*) FROM source_chunks GROUP BY source_type")}
    packets=q(con,"SELECT COUNT(*),COALESCE(SUM(approx_tokens),0) FROM knowledge_packets")[0]
    reviewers=[dict(r) for r in q(con,"SELECT lane,provider,model,COUNT(*) AS votes FROM review_votes GROUP BY lane,provider,model ORDER BY votes DESC")]
    candidate_states={r[0]:r[1] for r in q(con,"SELECT status,COUNT(*) FROM candidates GROUP BY status")}
    con.close(); status={}
    try:status=json.loads((db.parent/"STATUS.json").read_text(encoding="utf-8"))
    except Exception:pass
    return {"state":"LIVE","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"collected_source_tokens":collected,"accepted_dataset_tokens":accepted,"dataset_yield":accepted/collected if collected else 0.0,"compression_factor":collected/accepted if accepted else None,"accepted_packets":int(packets[0]),"accepted_packet_tokens":int(packets[1]),"rejected_candidates":counters.get("rejected_candidates",0),"collected_chunks":counters.get("collected_chunks",0),"model_input_tokens":counters.get("model_input_tokens",0),"model_output_tokens":counters.get("model_output_tokens",0),"questions":questions,"sources":sources,"reviewers":reviewers,"candidate_states":candidate_states,"counters":counters,"small_models":status.get("small_models",[]),"provider_budget":status.get("shared_provider_budget",{}),"db_bytes":db.stat().st_size}


def md(m:dict)->str:
    collected=m["collected_source_tokens"]; accepted=m["accepted_dataset_tokens"]
    ratio=f"{accepted:,} / {collected:,} = {m['dataset_yield']*100:.3f}%" if collected else "0 / 0 = 0.000%"
    factor=f"{m['compression_factor']:.2f}:1" if isinstance(m.get("compression_factor"),(int,float)) else "UNKNOWN"
    c=m.get("counters") or {}; near=c.get("near_miss_candidates",0); under=c.get("review_underfilled",0)+c.get("review_underfilled_no_nvidia",0); clear=c.get("clear_reject_candidates",0)
    lines=[BEGIN,"## AUTO — Research Distillery / kumuliertes Wissens-Dataset",f"Aktualisiert: `{m['generated_at']}`","",f"**1. wichtigste Quote — Entity-Dataset-Yield:** `{ratio}`  ",f"Kompressionsfaktor Quelltokens : akzeptierte Dataset-Tokens: **{factor}**.","","| Kennzahl | Wert |","|---|---:|",f"| kumulierte Quell-/Chunk-Tokens | {collected:,} |",f"| akzeptierte komprimierte Dataset-Tokens | {accepted:,} |",f"| akzeptierte Knowledge-Pakete | {m.get('accepted_packets',0)} |",f"| verworfene Kandidaten | {m.get('rejected_candidates',0)} |",f"| Near-Miss-Kandidaten | {near} |",f"| Reviewer-underfilled | {under} |",f"| klare Review-Rejects | {clear} |",f"| gesichtete Chunks | {m.get('collected_chunks',0)} |",f"| Distillery Modell-Input-Tokens | {m.get('model_input_tokens',0):,} |",f"| Distillery Modell-Output-Tokens | {m.get('model_output_tokens',0):,} |",f"| SQLite-Größe | {m.get('db_bytes',0):,} Byte |",""]
    lines += ["### Candidate-/Gate-Diagnose","| Zustand | Anzahl |","|---|---:|"]
    if m.get("candidate_states"):
        for k,v in sorted(m["candidate_states"].items(),key=lambda x:(-x[1],x[0])):lines.append(f"| `{k}` | {v} |")
    else:lines.append("| — | 0 |")
    if accepted==0 and collected>0:
        if under>0: lines += ["",f"**Aktueller Hauptengpass:** Reviewer-Panel war {under}× unterfüllt; das ist von Inhaltsqualität getrennt."]
        elif near>0: lines += ["",f"**Aktueller Hauptengpass:** {near} Kandidaten liegen als Near-Miss knapp unter dem Gate; Score-Gaps werden in den Distillery-Events protokolliert."]
        elif not m.get("candidate_states"): lines += ["","**Aktueller Hauptengpass:** Es wurden Quellen gesammelt, aber noch keine Candidate-Review-Stufe erreicht. Das ist ein Pipeline-/Runtime-Signal, kein Qualitätsurteil über die Quellen."]
    lines += ["","### Quellenmix — Herkunft ist Metadatum, kein Rankingfaktor","| Quelltyp | Metadaten-/Chunk-Rekorde |","|---|---:|"]
    if m.get("sources"):
        for k,v in sorted(m["sources"].items(),key=lambda x:(-x[1],x[0])):lines.append(f"| `{k}` | {v} |")
    else:lines.append("| — | 0 |")
    lines += ["","### Forschungsfragen","| Status | Anzahl |","|---|---:|"]
    if m.get("questions"):
        for k,v in sorted(m["questions"].items()):lines.append(f"| `{k}` | {v} |")
    else:lines.append("| — | 0 |")
    lines += ["","### Kleine Such-/Synthesemodelle"]
    sms=m.get("small_models") or []; lines.append(", ".join(f"`{x}`" for x in sms) if sms else "**NO SMALL FREE MODEL VERIFIED YET**")
    lines += ["","### Reviewer-Panel"]
    rev=m.get("reviewers") or []
    if rev:
        for r in rev:lines.append(f"- `{r.get('lane')}` → {r.get('provider')} / `{r.get('model')}` — {r.get('votes')} Votes")
    else:lines.append("- Noch keine Review-Votes.")
    lines += ["","### Epistemische Regel","Quellenrang, Zitationszahl, Stars, Popularität und Wiederholung gehen **nicht** in den Acceptance-Score ein. Kandidaten werden auf intrinsische Konsistenz, GRF-Kompatibilität, EntityOS/HCU-Projektfit, Neuheit des Mechanismus und Falsifizierbarkeit geprüft. `Near-Miss` senkt keine Schwelle; es macht nur sichtbar, *wo* das Gate greift.","","### Vernetzung mit GO","GO-Worker emittieren `OPEN_RESEARCH_QUESTIONS_JSON`; die Distillery zerlegt Fragen rekursiv und speist akzeptierte komprimierte Pakete als `DISTILLED_RESEARCH_DATASET` zurück. Shared `provider_budget.sqlite3` koordiniert Limits mit Free Swarm und Evidence Forge.",END]
    return "\n".join(lines)


def replace(readme:Path,block:str)->None:
    text=readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
    if BEGIN in text and END in text:
        a=text.index(BEGIN); b=text.index(END,a)+len(END); text=text[:a]+block+text[b:]
    else:
        lines=text.splitlines(); text=(lines[0]+"\n\n"+block+"\n\n"+"\n".join(lines[1:]).lstrip()) if lines and lines[0].startswith("# ") else block+"\n\n"+text
    readme.write_text(text.rstrip()+"\n",encoding="utf-8")


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",default="/workspace/clay-global-research-entity"); ap.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm"); args=ap.parse_args()
    repo=Path(args.repo); artifacts=Path(args.artifacts); metrics=load(artifacts/"distillery/distillery.sqlite3")
    replace(repo/"free swarm/README.md",md(metrics)); (repo/"free swarm/DISTILLERY_LIVE.json").write_text(json.dumps(metrics,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    analysis=repo/"free swarm/update_system_analysis.py"
    analysis_rc=None
    if analysis.exists():
        proc=subprocess.run([sys.executable,str(analysis),"--repo",str(repo),"--artifacts",str(artifacts)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120,check=False)
        analysis_rc=proc.returncode
    print(json.dumps({"state":metrics["state"],"collected":metrics["collected_source_tokens"],"accepted":metrics["accepted_dataset_tokens"],"yield":metrics["dataset_yield"],"near_miss":metrics.get("counters",{}).get("near_miss_candidates",0),"system_analysis_rc":analysis_rc})); return 0

if __name__=="__main__":raise SystemExit(main())
