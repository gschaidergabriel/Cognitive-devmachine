#!/usr/bin/env python3
"""Bridge strict Evidence-Forge PASS records into the Distillery dataset.

This is a deterministic evidence path, not a model-review bypass. A packet is
eligible only when the Forge's own SQLite candidate state is ACCEPTED and the
append-only evaluation independently carries the strict executable discriminators
used by ``run_free_evidence_forge.py``: two reproducible runs, zero positive,
negative, and static failures, benchmark non-regression, and measured improvement.

No provider credential is read. No model is called. Imported packets explicitly
carry zero canonical-truth/training credit and zero model-review scores; their
acceptance basis is executable reproduction rather than reviewer consensus.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from typing import Any


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def approx_tokens(text: str) -> int:
    return max(1,math.ceil(len(text)/4)) if text else 0


def _strict_pass(ev: dict[str,Any]) -> bool:
    try:
        return (
            ev.get("schema")=="CLAY_FORGE_DELTA_EVALUATION/v1"
            and ev.get("status")=="accepted"
            and int(ev.get("reproducible_runs") or 0)>=2
            and int(ev.get("tests_failed") or 0)==0
            and int(ev.get("negative_tests_failed") or 0)==0
            and int(ev.get("static_checks_failed") or 0)==0
            and ev.get("benchmark_non_regression") is True
            and float(ev.get("relative_improvement_pct") or 0.0)>0.0
            and bool(str(ev.get("worker_sha") or "").strip())
            and bool(str(ev.get("delta_id") or "").strip())
        )
    except (TypeError,ValueError):
        return False


def _ensure_distillery_schema(con: sqlite3.Connection) -> None:
    # The ordinary Distillery owns these tables. The IF-NOT-EXISTS definitions
    # only make this bridge safe during first-start ordering and preserve the
    # canonical column contract.
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS questions(
          id TEXT PRIMARY KEY,
          parent_id TEXT,
          root_problem TEXT NOT NULL,
          question TEXT NOT NULL UNIQUE,
          depth INTEGER NOT NULL DEFAULT 0,
          priority REAL NOT NULL DEFAULT 1.0,
          status TEXT NOT NULL DEFAULT 'OPEN',
          attempts INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          last_touched TEXT,
          source_worker_sha TEXT
        );
        CREATE TABLE IF NOT EXISTS knowledge_packets(
          id TEXT PRIMARY KEY,
          question_id TEXT NOT NULL,
          root_problem TEXT NOT NULL,
          packet_text TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          intrinsic_score REAL NOT NULL,
          grf_score REAL NOT NULL,
          project_fit REAL NOT NULL,
          novelty_score REAL NOT NULL,
          approx_tokens INTEGER NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS counters(
          key TEXT PRIMARY KEY,
          value INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS forge_ingest(
          evaluation_sha256 TEXT PRIMARY KEY,
          delta_id TEXT NOT NULL,
          knowledge_packet_id TEXT NOT NULL,
          ingested_at TEXT NOT NULL
        );
        """
    )


def _bump(con: sqlite3.Connection,key: str,delta: int) -> None:
    con.execute(
        "INSERT INTO counters(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
        (key,int(delta)),
    )


def ingest(artifacts: Path) -> dict[str,Any]:
    forge_root=artifacts/"forge";eval_path=forge_root/"architecture_delta_evaluations.jsonl"
    forge_db=forge_root/"forge.sqlite3";dist_db=artifacts/"distillery"/"distillery.sqlite3"
    result={"schema":"CLAY_FORGE_TO_DISTILLERY_BRIDGE/v1","observed_at":now_iso(),
            "eligible":0,"imported":0,"already_imported":0,"rejected_crossbind":0,
            "canonical_truth_credit":False,"training_credit":False}
    if not eval_path.is_file() or not forge_db.is_file():
        result["state"]="NO_FORGE_EVIDENCE";return result

    dist_db.parent.mkdir(parents=True,exist_ok=True)
    fcon=sqlite3.connect(forge_db,timeout=10);fcon.row_factory=sqlite3.Row
    dcon=sqlite3.connect(dist_db,timeout=20);dcon.row_factory=sqlite3.Row
    try:
        _ensure_distillery_schema(dcon)
        for raw in eval_path.read_text(encoding="utf-8",errors="replace").splitlines():
            line=raw.strip()
            if not line:continue
            ev_sha=hashlib.sha256(line.encode("utf-8")).hexdigest()
            try:ev=json.loads(line)
            except json.JSONDecodeError:continue
            if not isinstance(ev,dict) or not _strict_pass(ev):continue
            result["eligible"]+=1
            if dcon.execute("SELECT 1 FROM forge_ingest WHERE evaluation_sha256=?",(ev_sha,)).fetchone():
                result["already_imported"]+=1;continue

            # Cross-bind the append-only evaluation to the Forge DB state and the
            # exact worker proposal. A forged/copied JSONL PASS cannot self-admit.
            row=fcon.execute(
                "SELECT candidate_hash,proposal_json,state,worker_sha,delta_id,provider,model,role "
                "FROM candidates WHERE delta_id=? AND worker_sha=? ORDER BY evaluated_at DESC LIMIT 1",
                (str(ev["delta_id"]),str(ev["worker_sha"])),
            ).fetchone()
            if row is None or str(row["state"]).upper()!="ACCEPTED":
                result["rejected_crossbind"]+=1;continue
            try:proposal=json.loads(row["proposal_json"])
            except Exception:
                result["rejected_crossbind"]+=1;continue
            if not isinstance(proposal,dict):
                result["rejected_crossbind"]+=1;continue

            evidence={
                "evidence_class":"FORGE_EXECUTABLE_REPRODUCTION",
                "forge_schema":ev.get("schema"),
                "forge_candidate_hash":row["candidate_hash"],
                "delta_id":ev["delta_id"],
                "worker_sha":ev["worker_sha"],
                "provider":row["provider"],"model":row["model"],"role":row["role"],
                "metric":ev.get("metric"),
                "relative_improvement_pct":ev.get("relative_improvement_pct"),
                "reproducible_runs":ev.get("reproducible_runs"),
                "tests_passed":ev.get("tests_passed"),"tests_failed":ev.get("tests_failed"),
                "negative_tests_passed":ev.get("negative_tests_passed"),
                "negative_tests_failed":ev.get("negative_tests_failed"),
                "static_checks_passed":ev.get("static_checks_passed"),
                "static_checks_failed":ev.get("static_checks_failed"),
                "benchmark_non_regression":ev.get("benchmark_non_regression"),
                "evaluation_sha256":ev_sha,
                "acceptance_basis":"EXECUTABLE_FORGE_NOT_MODEL_CONSENSUS",
                "model_review_scores_applicable":False,
                "canonical_truth_credit":False,
                "training_credit":False,
            }
            packet={
                "problem":"Which executable EntityOS/HCU delta survived strict Forge reproduction?",
                "approach":"EVIDENCE_FORGE_REPRODUCTION",
                "claim":proposal.get("hypothesis") or ev.get("proposal_hypothesis"),
                "mechanism":proposal.get("mechanism"),
                "falsifier":proposal.get("falsifier") or ev.get("falsifier"),
                "predicted_architecture_delta":{
                    "target_files":proposal.get("target_files") or [],
                    "metric":ev.get("metric"),
                    "relative_improvement_pct":ev.get("relative_improvement_pct"),
                },
                "counterevidence":"The same strict Forge discriminator must fail or regress on a successor source identity before this evidence is generalized.",
                "evidence":evidence,
            }
            text=json.dumps(packet,ensure_ascii=False,separators=(",",":"),sort_keys=True)
            kid="k-forge-"+hashlib.sha256((ev_sha+text).encode("utf-8")).hexdigest()[:18]
            qid="q-forge-executable-evidence"
            question="Which strict Evidence-Forge reproductions provide executable evidence for EntityOS/HCU architecture deltas?"
            root_problem="Convert Free-Swarm work into reproducible executable EntityOS/HCU evidence without model-consensus promotion."
            dcon.execute(
                "INSERT OR IGNORE INTO questions(id,parent_id,root_problem,question,depth,priority,status,attempts,created_at,last_touched,source_worker_sha) "
                "VALUES(?,?,?, ?,0,3.0,'CYCLIC',0,?,?,?)",
                (qid,None,root_problem,question,now_iso(),now_iso(),str(ev["worker_sha"])),
            )
            tok=approx_tokens(text)
            # Score columns are legacy model-review fields and therefore remain
            # zero rather than fabricating a model score for executable evidence.
            dcon.execute(
                "INSERT INTO knowledge_packets(id,question_id,root_problem,packet_text,metadata_json,intrinsic_score,grf_score,project_fit,novelty_score,approx_tokens,created_at) "
                "VALUES(?,?,?,?,?,0.0,0.0,0.0,0.0,?,?)",
                (kid,qid,root_problem,text,json.dumps(evidence,ensure_ascii=False,sort_keys=True),tok,now_iso()),
            )
            dcon.execute(
                "INSERT INTO forge_ingest(evaluation_sha256,delta_id,knowledge_packet_id,ingested_at) VALUES(?,?,?,?)",
                (ev_sha,str(ev["delta_id"]),kid,now_iso()),
            )
            _bump(dcon,"accepted_dataset_tokens",tok);_bump(dcon,"accepted_packets",1);_bump(dcon,"forge_executable_packets",1)
            result["imported"]+=1
        dcon.commit();result["state"]="OK"
        return result
    finally:
        fcon.close();dcon.close()


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm")
    ap.add_argument("--status-out",default="")
    args=ap.parse_args();result=ingest(Path(args.artifacts))
    text=json.dumps(result,ensure_ascii=False,sort_keys=True)
    if args.status_out:
        p=Path(args.status_out);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(text+"\n",encoding="utf-8");tmp.replace(p)
    print(text)
    return 0


if __name__=="__main__":raise SystemExit(main())
