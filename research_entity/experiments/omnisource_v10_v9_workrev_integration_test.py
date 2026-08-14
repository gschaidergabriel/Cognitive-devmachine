#!/usr/bin/env python3
"""Integration falsifier: V10 current-work credit must follow V9 authoritative spec revisions."""
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, tempfile
from pathlib import Path

MIN_V9_WORK = r"""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS clay_work_items(
  work_id TEXT PRIMARY KEY,
  goal_ref TEXT NOT NULL,
  origin_class TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  terminal_status TEXT,
  terminal_at TEXT
);
CREATE TABLE IF NOT EXISTS clay_work_spec_revisions(
  work_id TEXT NOT NULL REFERENCES clay_work_items(work_id) ON DELETE CASCADE,
  spec_rev INTEGER NOT NULL,
  parent_rev INTEGER,
  title TEXT NOT NULL,
  work_clay TEXT NOT NULL,
  reason_clay TEXT NOT NULL DEFAULT '{}',
  completion_clay TEXT NOT NULL,
  evidence_need_clay TEXT NOT NULL DEFAULT '[]',
  executor_policy_clay TEXT NOT NULL DEFAULT '{}',
  required_capabilities_clay TEXT NOT NULL DEFAULT '[]',
  write_scope_clay TEXT NOT NULL DEFAULT '[]',
  dependency_clay TEXT NOT NULL DEFAULT '[]',
  invalidation_clay TEXT NOT NULL DEFAULT '[]',
  base_priority REAL NOT NULL DEFAULT 0.5,
  expected_impact REAL NOT NULL DEFAULT 0.5,
  urgency REAL NOT NULL DEFAULT 0.0,
  information_gain REAL NOT NULL DEFAULT 0.0,
  status TEXT NOT NULL CHECK(status IN ('PROPOSED','READY','DEFERRED','BLOCKED','SUPERSEDED','CANCELLED')),
  source_ref TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(work_id,spec_rev)
);
CREATE VIEW IF NOT EXISTS v_clay_current_work_specs AS
WITH ranked AS (
 SELECT s.*,ROW_NUMBER() OVER(PARTITION BY work_id ORDER BY spec_rev DESC) rn
 FROM clay_work_spec_revisions s
)
SELECT r.* FROM ranked r JOIN clay_work_items w USING(work_id)
WHERE r.rn=1 AND w.terminal_status IS NULL;
"""

def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def add_work_rev(c, rev: int):
    c.execute("""INSERT INTO clay_work_spec_revisions(
      work_id,spec_rev,parent_rev,title,work_clay,reason_clay,completion_clay,evidence_need_clay,
      executor_policy_clay,required_capabilities_clay,write_scope_clay,dependency_clay,invalidation_clay,
      base_priority,expected_impact,urgency,information_gain,status,source_ref,created_by,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      ("WORK-X",rev,rev-1 if rev>1 else None,f"rev {rev}",f"work rev {rev}","{}","done","[]","{}","[]","[]","[]","[]",
       .5,.8,.5,.9,"READY",f"event-rev-{rev}","test","2026-08-10T17:00:00+07:00"))

def add_credit(c, suffix: str, rev: int):
    oid=f"obs-{suffix}"; aid=f"a-{suffix}"; rid=f"r-{suffix}"
    c.execute("""INSERT INTO clay_omnisource_observations(
      observation_id,source_class,source_ref,source_actor,source_time,observed_at,
      semantic_epoch,epoch_state,semantic_identity,content_hash,raw_payload_ref,provenance_hash,
      verification_state,promotion_eligible,work_id,work_spec_rev,work_revision_state,
      current_work_credit_eligible,bound_repo_head,bound_component_hashes_clay,execution_started_at,
      freshness,confidence,created_by)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (oid,"RUNTIME_RECEIPT",f"test://{oid}","test","2026-08-10T17:00:00+07:00","2026-08-10T17:00:00+07:00",
       200+rev,"CURRENT",f"semantic:{suffix}",h(suffix),f"payload:{suffix}",h("prov:"+suffix),
       "VERIFIED",1,"WORK-X",rev,"CURRENT",1,f"head-{rev}",json.dumps([f"component-{rev}"]),
       "2026-08-10T17:00:00+07:00",1.0,.9,"test"))
    c.execute("""INSERT INTO clay_fusion_assessments(
      assessment_id,observation_id,compared_against_epoch,novelty_class,materiality,uncertainty,
      affected_claims_clay,affected_hypotheses_clay,affected_work_clay,affected_components_clay,
      evidence_for_clay,evidence_against_clay,strongest_counterhypothesis_ref,semantic_delta_ref,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (aid,oid,200+rev,"CONFIRMS",.9,.1,"[]","[]",'["WORK-X"]',"[]","[]","[]",None,f"delta-{suffix}","2026-08-10T17:00:01+07:00"))
    c.execute("""INSERT INTO clay_research_reentry_receipts(
      receipt_id,observation_id,assessment_id,fused_epoch,work_id,work_spec_rev,work_revision_state,
      current_work_credit_eligible,bound_repo_head,bound_component_hashes_clay,
      evidence_updates_clay,claim_updates_clay,hypothesis_updates_clay,counterhypothesis_updates_clay,
      experiment_updates_clay,work_updates_clay,architecture_delta_candidates_clay,test_obligations_clay,
      negative_results_clay,branch_feedback_targets_clay,no_change_reason_clay,next_falsifier_clay,
      rollback_or_recovery_impact_clay,closure_state,completed_at,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (rid,oid,aid,201+rev,"WORK-X",rev,"CURRENT",1,f"head-{rev}",json.dumps([f"component-{rev}"]),
       "[]","[]","[]","[]","[]","[]","[]","[]","[]","[]",None,None,None,"CLOSED",
       "2026-08-10T17:00:02+07:00","2026-08-10T17:00:02+07:00"))

def run(schema_path: Path) -> dict:
    fd, dbpath=tempfile.mkstemp(suffix=".sqlite"); os.close(fd)
    c=None
    try:
        c=sqlite3.connect(dbpath)
        c.executescript(MIN_V9_WORK)
        c.executescript(schema_path.read_text(encoding="utf-8"))
        c.execute("INSERT INTO clay_work_items VALUES(?,?,?,?,?,?,?)",
                  ("WORK-X","FRANK_V0_1_ANDREAS_PC","TEST","test","2026-08-10T17:00:00+07:00",None,None))
        add_work_rev(c,1); add_credit(c,"rev1",1); c.commit()
        rev1_authoritative=c.execute("SELECT count(*) FROM v_clay_authoritative_current_work_credit_receipts WHERE work_id='WORK-X'").fetchone()[0]
        rev1_mismatch=c.execute("SELECT count(*) FROM v_clay_work_credit_revision_mismatches WHERE work_id='WORK-X'").fetchone()[0]

        add_work_rev(c,2); c.commit()
        old_after_revision=c.execute("SELECT count(*) FROM v_clay_authoritative_current_work_credit_receipts WHERE work_id='WORK-X'").fetchone()[0]
        mismatch_after_revision=c.execute("SELECT count(*) FROM v_clay_work_credit_revision_mismatches WHERE work_id='WORK-X'").fetchone()[0]
        current_spec=c.execute("SELECT spec_rev FROM v_clay_current_work_specs WHERE work_id='WORK-X'").fetchone()[0]

        add_credit(c,"rev2",2); c.commit()
        auth_rows=c.execute("SELECT receipt_id,work_spec_rev FROM v_clay_authoritative_current_work_credit_receipts WHERE work_id='WORK-X' ORDER BY receipt_id").fetchall()
        mismatch_rows=c.execute("SELECT receipt_id,receipt_spec_rev,current_spec_rev FROM v_clay_work_credit_revision_mismatches WHERE work_id='WORK-X' ORDER BY receipt_id").fetchall()
        result={
          "schema_version":"1.0",
          "pass": (
            rev1_authoritative==1 and rev1_mismatch==0 and
            old_after_revision==0 and mismatch_after_revision==1 and current_spec==2 and
            auth_rows==[("r-rev2",2)] and mismatch_rows==[("r-rev1",1,2)]
          ),
          "before_revision":{"authoritative_credit_rows":rev1_authoritative,"mismatch_rows":rev1_mismatch},
          "after_revision_before_new_receipt":{"authoritative_credit_rows":old_after_revision,"mismatch_rows":mismatch_after_revision,"current_spec_rev":current_spec},
          "after_current_receipt":{"authoritative_rows":auth_rows,"mismatch_rows":mismatch_rows},
          "interpretation":"V10 preserves old receipt evidence but V9 current-spec join removes its current-work credit immediately after spec revision advances."
        }
        return result
    finally:
        if c:
            try:c.close()
            except Exception:pass
        if os.path.exists(dbpath):os.unlink(dbpath)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--schema",required=True)
    ap.add_argument("--out")
    a=ap.parse_args()
    r=run(Path(a.schema))
    text=json.dumps(r,indent=2,sort_keys=True,default=list)+"\n"
    if a.out: Path(a.out).write_text(text,encoding="utf-8")
    print(text,end="")
    raise SystemExit(0 if r["pass"] else 1)

if __name__=="__main__":
    main()
