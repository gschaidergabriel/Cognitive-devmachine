#!/usr/bin/env python3
"""Refresh the Research Distillery section in free swarm/README.md.

Reads only derived metrics/metadata from the artifact SQLite database. Raw source
chunks never enter Git. The first metric is the requested collected-token ->
accepted-dataset-token ratio.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sqlite3

BEGIN="<!-- RESEARCH_DISTILLERY_AUTO:BEGIN -->"
END="<!-- RESEARCH_DISTILLERY_AUTO:END -->"


def q(con,sql,args=()):
    return con.execute(sql,args).fetchall()


def load(db:Path)->dict:
    if not db.exists():
        return {"state":"NOT_STARTED","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"collected_source_tokens":0,"accepted_dataset_tokens":0,"dataset_yield":0.0,"compression_factor":None,"accepted_packets":0,"rejected_candidates":0,"questions":{},"sources":{},"reviewers":[],"small_models":[],"provider_budget":{}}
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    counters={r[0]:int(r[1]) for r in q(con,"SELECT key,value FROM counters")}
    collected=counters.get("collected_source_tokens",0); accepted=counters.get("accepted_dataset_tokens",0)
    questions={r[0]:r[1] for r in q(con,"SELECT status,COUNT(*) FROM questions GROUP BY status")}
    sources={r[0]:r[1] for r in q(con,"SELECT source_type,COUNT(*) FROM source_chunks GROUP BY source_type")}
    packets=q(con,"SELECT COUNT(*),COALESCE(SUM(approx_tokens),0) FROM knowledge_packets")[0]
    reviewers=[dict(r) for r in q(con,"SELECT lane,provider,model,COUNT(*) AS votes FROM review_votes GROUP BY lane,provider,model ORDER BY votes DESC")]
    con.close()
    status_path=db.parent/"STATUS.json"; status={}
    try: status=json.loads(status_path.read_text(encoding="utf-8"))
    except Exception: pass
    return {
      "state":"LIVE","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
      "collected_source_tokens":collected,"accepted_dataset_tokens":accepted,
      "dataset_yield":accepted/collected if collected else 0.0,
      "compression_factor":collected/accepted if accepted else None,
      "accepted_packets":int(packets[0]),"accepted_packet_tokens":int(packets[1]),
      "rejected_candidates":counters.get("rejected_candidates",0),"collected_chunks":counters.get("collected_chunks",0),
      "model_input_tokens":counters.get("model_input_tokens",0),"model_output_tokens":counters.get("model_output_tokens",0),
      "questions":questions,"sources":sources,"reviewers":reviewers,
      "small_models":status.get("small_models",[]),"provider_budget":status.get("shared_provider_budget",{}),
      "db_bytes":db.stat().st_size,
    }


def md(m:dict)->str:
    collected=m["collected_source_tokens"]; accepted=m["accepted_dataset_tokens"]
    ratio=f"{accepted:,} / {collected:,} = {m['dataset_yield']*100:.3f}%" if collected else "0 / 0 = 0.000%"
    factor=f"{m['compression_factor']:.2f}:1" if isinstance(m.get("compression_factor"),(int,float)) else "UNKNOWN"
    lines=[BEGIN,"## AUTO — Research Distillery / kumuliertes Wissens-Dataset",f"Aktualisiert: `{m['generated_at']}`","",
           f"**1. wichtigste Quote — Entity-Dataset-Yield:** `{ratio}`  ",
           f"Kompressionsfaktor Quelltokens : akzeptierte Dataset-Tokens: **{factor}**.","",
           "| Kennzahl | Wert |","|---|---:|",
           f"| kumulierte Quell-/Chunk-Tokens | {collected:,} |",f"| akzeptierte komprimierte Dataset-Tokens | {accepted:,} |",
           f"| akzeptierte Knowledge-Pakete | {m.get('accepted_packets',0)} |",f"| verworfene Kandidaten | {m.get('rejected_candidates',0)} |",
           f"| gesichtete Chunks | {m.get('collected_chunks',0)} |",f"| Distillery Modell-Input-Tokens | {m.get('model_input_tokens',0):,} |",
           f"| Distillery Modell-Output-Tokens | {m.get('model_output_tokens',0):,} |",f"| SQLite-Größe | {m.get('db_bytes',0):,} Byte |","",
           "### Quellenmix — Herkunft ist Metadatum, kein Rankingfaktor","| Quelltyp | Metadaten-/Chunk-Rekorde |","|---|---:|"]
    if m.get("sources"):
        for k,v in sorted(m["sources"].items(),key=lambda x:(-x[1],x[0])): lines.append(f"| `{k}` | {v} |")
    else: lines.append("| — | 0 |")
    lines += ["","### Forschungsfragen","| Status | Anzahl |","|---|---:|"]
    if m.get("questions"):
        for k,v in sorted(m["questions"].items()): lines.append(f"| `{k}` | {v} |")
    else: lines.append("| — | 0 |")
    lines += ["","### Kleine Such-/Synthesemodelle"]
    sms=m.get("small_models") or []
    lines.append(", ".join(f"`{x}`" for x in sms) if sms else "**NO SMALL FREE MODEL VERIFIED YET**")
    lines += ["","### Reviewer-Panel"]
    rev=m.get("reviewers") or []
    if rev:
        for r in rev: lines.append(f"- `{r.get('lane')}` → {r.get('provider')} / `{r.get('model')}` — {r.get('votes')} Votes")
    else: lines.append("- Noch keine Review-Votes.")
    lines += ["","### Epistemische Regel","Quellenrang, Zitationszahl, Stars, Popularität und Wiederholung gehen **nicht** in den Acceptance-Score ein. Kandidaten werden auf intrinsische Konsistenz, GRF-Kompatibilität, EntityOS/HCU-Projektfit, Neuheit des Mechanismus und Falsifizierbarkeit geprüft. Nach Sichtung werden abgelehnte Rohchunks gelöscht; akzeptierte Rohtexte werden ebenfalls entfernt und nur komprimierte Knowledge-Pakete plus Quellenmetadaten/Hashes bleiben erhalten.","",
              "### Vernetzung mit GO","GO-Worker emittieren `OPEN_RESEARCH_QUESTIONS_JSON`. Die Distillery zerlegt diese Fragen rekursiv, erzwingt bei Wiederbehandlung einen neuen Ansatz und schreibt nur akzeptierte komprimierte Pakete in SQLite. Der GO-Swarm liest diese Pakete beim nächsten Prompt als `DISTILLED_RESEARCH_DATASET` ein. Beide Swarms teilen `provider_budget.sqlite3` für providerweite Concurrency/Cooldown-Beobachtung.",END]
    return "\n".join(lines)


def replace(readme:Path,block:str)->None:
    text=readme.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        a=text.index(BEGIN); b=text.index(END,a)+len(END); text=text[:a]+block+text[b:]
    else:
        lines=text.splitlines()
        if lines and lines[0].startswith("# "): text=lines[0]+"\n\n"+block+"\n\n"+"\n".join(lines[1:]).lstrip()
        else: text=block+"\n\n"+text
    readme.write_text(text.rstrip()+"\n",encoding="utf-8")


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",default="/workspace/clay-global-research-entity"); ap.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm"); args=ap.parse_args()
    repo=Path(args.repo); metrics=load(Path(args.artifacts)/"distillery/distillery.sqlite3")
    replace(repo/"free swarm/README.md",md(metrics))
    (repo/"free swarm/DISTILLERY_LIVE.json").write_text(json.dumps(metrics,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"state":metrics["state"],"collected":metrics["collected_source_tokens"],"accepted":metrics["accepted_dataset_tokens"],"yield":metrics["dataset_yield"]}))
    return 0

if __name__=="__main__": raise SystemExit(main())
