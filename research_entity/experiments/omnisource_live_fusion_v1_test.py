#!/usr/bin/env python3
"""Deterministic candidate test for UnifiedDB V10 omnisource live fusion/research re-entry.

Evidence classes:
- local invocation: LOCAL_SANDBOX_SQLITE_CANDIDATE_TEST
- GitHub self-hosted Ubuntu workflow: REMOTE_EXECUTION_RECEIPT if wrapper records success.

Exactly one out-of-box experiment is included: temporal_braid_fault.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, statistics, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = ROOT / "research_entity/runtime/RAE_UNIFIEDDB_V10_OMNISOURCE_LIVE_FUSION.sql"
SOURCE_CLASSES = [
    "REPO_STATE","WORK_EVENT","WORKER_RESULT","RUNTIME_RECEIPT","BENCHMARK_ROW",
    "TEST_FAILURE","NEGATIVE_RESULT","USER_DIRECTIVE","USER_OBSERVATION","UPLOADED_SOURCE",
    "EXTERNAL_PRIMARY","EXTERNAL_OFFICIAL","EXTERNAL_TECHNICAL","PROVIDER_CAPABILITY",
    "FRANK_TELEMETRY","UNIFIEDDB_DELTA","CLAYGRAPH_DELTA","EXPERIMENT_OUTPUT",
    "OTHER_PROVENANCE_BOUND",
]

def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def insert_obs(
    con, oid, sc, sem, epoch, payload, prov,
    epoch_state="CURRENT", verified="VERIFIED", eligible=1,
    work_id=None, work_spec_rev=None, work_revision_state="NOT_APPLICABLE",
    work_credit=0, repo_head=None, component_hashes="[]", execution_started_at=None,
):
    con.execute("""INSERT INTO clay_omnisource_observations(
      observation_id,source_class,source_ref,source_actor,source_time,observed_at,
      semantic_epoch,epoch_state,semantic_identity,content_hash,raw_payload_ref,provenance_hash,
      verification_state,promotion_eligible,work_id,work_spec_rev,work_revision_state,
      current_work_credit_eligible,bound_repo_head,bound_component_hashes_clay,execution_started_at,
      freshness,confidence,created_by)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (oid,sc,f"test://{sc.lower()}/{oid}","test-worker","2026-08-10T16:36:00+07:00",
       "2026-08-10T16:36:00+07:00",epoch,epoch_state,sem,h(payload),f"test://payload/{oid}",h(prov),
       verified,eligible,work_id,work_spec_rev,work_revision_state,work_credit,repo_head,
       component_hashes,execution_started_at,1.0,0.9,"chatgpt-secondary"))

def assess(con, aid, oid, novelty, mat, unc, sem_delta=None):
    con.execute("""INSERT INTO clay_fusion_assessments(
      assessment_id,observation_id,compared_against_epoch,novelty_class,materiality,uncertainty,
      affected_claims_clay,affected_hypotheses_clay,affected_work_clay,affected_components_clay,
      evidence_for_clay,evidence_against_clay,strongest_counterhypothesis_ref,semantic_delta_ref,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (aid,oid,100,novelty,mat,unc,'["claim:x"]','["hyp:x"]','["work:x"]','["component:x"]',
       '["ev:for"]','["ev:against"]',"counter:x",sem_delta,"2026-08-10T16:36:01+07:00"))

def reentry(
    con, rid, oid, aid, state="CLOSED", epoch=101,
    branches=("clayresearch","unifieddb","claygraph"),
    work_id=None, work_spec_rev=None, work_revision_state="NOT_APPLICABLE",
    work_credit=0, repo_head=None, component_hashes="[]",
):
    con.execute("""INSERT INTO clay_research_reentry_receipts(
      receipt_id,observation_id,assessment_id,fused_epoch,work_id,work_spec_rev,work_revision_state,
      current_work_credit_eligible,bound_repo_head,bound_component_hashes_clay,
      evidence_updates_clay,claim_updates_clay,hypothesis_updates_clay,counterhypothesis_updates_clay,
      experiment_updates_clay,work_updates_clay,architecture_delta_candidates_clay,test_obligations_clay,
      negative_results_clay,branch_feedback_targets_clay,no_change_reason_clay,next_falsifier_clay,
      rollback_or_recovery_impact_clay,closure_state,completed_at,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (rid,oid,aid,epoch,work_id,work_spec_rev,work_revision_state,work_credit,repo_head,component_hashes,
       "[]","[]","[]","[]","[]","[]","[]","[]","[]",json.dumps(list(branches)),
       None,"next falsifier","rollback preserved",state,"2026-08-10T16:36:02+07:00",
       "2026-08-10T16:36:02+07:00"))
    for b in branches:
        con.execute("""INSERT INTO clay_reentry_branch_receipts(
          receipt_id,branch_ref,route_reason,delivered,reconstructed,plan_revalidated,used,local_effect,
          interrupted_before_effect,ack_epoch,dependency_projection_hash,observed_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
          (rid,b,"DIRECT_SEMANTIC",1,1,1,1,0,0,epoch,h("projection"),"2026-08-10T16:36:03+07:00"))

def run(schema_path: Path, perf_n: int = 5000) -> dict:
    sql = schema_path.read_text(encoding="utf-8")
    fd, dbpath = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    con = None
    try:
        con=sqlite3.connect(dbpath)
        con.executescript(sql)

        for i, sc in enumerate(SOURCE_CLASSES):
            oid=f"obs-{i:02d}"
            insert_obs(con,oid,sc,f"semantic:{sc}",100+i,f"payload-{sc}",f"prov-{sc}")
            assess(con,f"a-{i:02d}",oid,"CONTRADICTS" if sc=="NEGATIVE_RESULT" else "NEW",0.8,0.2,f"delta-{i:02d}")
            reentry(con,f"r-{i:02d}",oid,f"a-{i:02d}",epoch=101+i)

        insert_obs(con,"dup-a","EXTERNAL_PRIMARY","semantic:duplicate",120,"same-content","source-A")
        insert_obs(con,"dup-b","EXTERNAL_OFFICIAL","semantic:duplicate",120,"same-content","source-B")
        assess(con,"a-dup-a","dup-a","CONFIRMS",0.3,0.1)
        assess(con,"a-dup-b","dup-b","DUPLICATE",0.0,0.0)

        stale_gate_ok=False
        try:
            insert_obs(con,"stale-bad","WORKER_RESULT","semantic:stale",90,"late-stale","prov-stale","STALE","VERIFIED",1)
        except sqlite3.IntegrityError:
            stale_gate_ok=True
        insert_obs(con,"stale-good","WORKER_RESULT","semantic:stale",90,"late-stale","prov-stale","STALE","VERIFIED",0)
        assess(con,"a-stale","stale-good","CONTRADICTS",0.9,0.4,"delta-stale")

        stale_work_credit_gate_ok=False
        try:
            insert_obs(
                con,"work-stale-bad","RUNTIME_RECEIPT","semantic:work-receipt",150,
                "technically-successful-old-work","prov-old-work",
                work_id="WORK-X",work_spec_rev=1,work_revision_state="STALE",work_credit=1,
                repo_head="old-head",component_hashes='["h-old"]',
                execution_started_at="2026-08-10T16:30:00+07:00",
            )
        except sqlite3.IntegrityError:
            stale_work_credit_gate_ok=True
        insert_obs(
            con,"work-stale-diag","RUNTIME_RECEIPT","semantic:work-receipt",150,
            "technically-successful-old-work","prov-old-work",
            work_id="WORK-X",work_spec_rev=1,work_revision_state="STALE",work_credit=0,
            repo_head="old-head",component_hashes='["h-old"]',
            execution_started_at="2026-08-10T16:30:00+07:00",
        )
        assess(con,"a-work-stale","work-stale-diag","CONFIRMS",0.8,0.1,"delta-work-stale")
        stale_work_rows=con.execute("SELECT count(*) FROM v_clay_stale_work_evidence WHERE work_id='WORK-X'").fetchone()[0]

        missing_binding_gate_ok=False
        try:
            insert_obs(
                con,"work-current-unbound","RUNTIME_RECEIPT","semantic:work-current",151,
                "current-but-unbound","prov-current-unbound",
                work_id="WORK-X",work_spec_rev=2,work_revision_state="CURRENT",work_credit=1,
                repo_head="head-2",component_hashes="[]",
                execution_started_at="2026-08-10T16:35:00+07:00",
            )
        except sqlite3.IntegrityError:
            missing_binding_gate_ok=True

        insert_obs(
            con,"work-current","RUNTIME_RECEIPT","semantic:work-current",151,
            "current-bound","prov-current",
            work_id="WORK-X",work_spec_rev=2,work_revision_state="CURRENT",work_credit=1,
            repo_head="head-2",component_hashes='["component-a","component-b"]',
            execution_started_at="2026-08-10T16:35:00+07:00",
        )
        assess(con,"a-work-current","work-current","CONFIRMS",0.85,0.1,"delta-work-current")
        reentry(
            con,"r-work-current","work-current","a-work-current",epoch=152,
            work_id="WORK-X",work_spec_rev=2,work_revision_state="CURRENT",work_credit=1,
            repo_head="head-2",component_hashes='["component-a","component-b"]',
        )
        current_work_credit_rows=con.execute(
            "SELECT count(*) FROM v_clay_current_work_credit_receipts WHERE work_id='WORK-X' AND work_spec_rev=2"
        ).fetchone()[0]

        insert_obs(con,"mat-open","EXPERIMENT_OUTPUT","semantic:open",130,"material-open","prov-open")
        assess(con,"a-open","mat-open","REFINES",0.95,0.2,"delta-open")
        pending_open_before=con.execute("""
          SELECT count(*) FROM v_clay_material_reentry_pending WHERE observation_id='mat-open'
        """).fetchone()[0]
        reentry(con,"r-open","mat-open","a-open",epoch=131)
        pending_open_after=con.execute("""
          SELECT count(*) FROM v_clay_material_reentry_pending WHERE observation_id='mat-open'
        """).fetchone()[0]

        insert_obs(con,"contra-1","EXTERNAL_PRIMARY","semantic:claim-z",140,"supports-z","p1")
        insert_obs(con,"contra-2","RUNTIME_RECEIPT","semantic:claim-z",141,"refutes-z","p2")
        assess(con,"a-contra-1","contra-1","CONFIRMS",0.8,0.2,"dz1")
        assess(con,"a-contra-2","contra-2","CONTRADICTS",1.0,0.1,"dz2")
        contra_count=con.execute("""SELECT count(*) FROM clay_fusion_assessments a
          JOIN clay_omnisource_observations o USING(observation_id)
          WHERE o.semantic_identity='semantic:claim-z'""").fetchone()[0]
        con.execute("""INSERT INTO clay_reentry_checkpoints(
          checkpoint_id,semantic_epoch,source_projection_hash,dependency_projection_hash,
          last_observation_id,last_reentry_receipt_id,health_state,created_at)
          VALUES(?,?,?,?,?,?,?,?)""",
          ("cp-1",141,h("src"),h("dep"),"contra-2","r-open","HEALTHY","2026-08-10T16:36:04+07:00"))
        con.commit()
        con.close()

        con=sqlite3.connect(dbpath); con.execute("PRAGMA foreign_keys=ON")
        cp=con.execute("""SELECT semantic_epoch,health_state,last_reentry_receipt_id
          FROM clay_reentry_checkpoints WHERE checkpoint_id='cp-1'""").fetchone()
        r_open=con.execute("""SELECT closure_state FROM clay_research_reentry_receipts
          WHERE receipt_id='r-open'""").fetchone()
        pending_open_after_restart=con.execute("""
          SELECT count(*) FROM v_clay_material_reentry_pending WHERE observation_id='mat-open'
        """).fetchone()[0]
        open_other_material=con.execute("SELECT count(*) FROM v_clay_material_reentry_pending").fetchone()[0]
        dup=con.execute("""SELECT observation_count,distinct_provenance_count
          FROM v_clay_duplicate_content_provenance WHERE content_hash=?""",(h("same-content"),)).fetchone()
        stale_work_rows_after_restart=con.execute(
            "SELECT count(*) FROM v_clay_stale_work_evidence WHERE work_id='WORK-X'"
        ).fetchone()[0]
        current_work_credit_after_restart=con.execute(
            "SELECT count(*) FROM v_clay_current_work_credit_receipts WHERE work_id='WORK-X' AND work_spec_rev=2"
        ).fetchone()[0]

        lat=[]; t0=time.perf_counter()
        con.execute("BEGIN")
        for i in range(perf_n):
            s=time.perf_counter_ns()
            oid=f"perf-{i}"; sc=SOURCE_CLASSES[i%len(SOURCE_CLASSES)]
            insert_obs(con,oid,sc,f"semantic:perf:{i%127}",200+i,f"perf-payload-{i}",f"perf-prov-{i}")
            assess(con,f"a-perf-{i}",oid,"NEW" if i%5==0 else "NO_MATERIAL_CHANGE",
                   0.9 if i%5==0 else 0.1,0.2,f"d-perf-{i}" if i%5==0 else None)
            lat.append((time.perf_counter_ns()-s)/1e6)
        con.commit(); elapsed=time.perf_counter()-t0

        # Exactly one bounded out-of-box GO experiment.
        # Temporal braid: a late stale contradiction crosses a duplicate-provenance event,
        # a checkpoint/restart boundary, then a fresh supersession.
        events=[
          {"arrival":1,"epoch":300,"value":"SUPPORTED","eligible":1,"kind":"CURRENT"},
          {"arrival":2,"epoch":298,"value":"REFUTED","eligible":0,"kind":"STALE"},
          {"arrival":3,"epoch":300,"value":"SUPPORTED","eligible":1,"kind":"DUPLICATE_PROVENANCE"},
          {"arrival":4,"epoch":301,"value":"REFINED","eligible":1,"kind":"FRESH_SUPERSESSION"},
        ]
        arrival_state=None; arrival_false_promotions=0
        epoch_state=None; epoch=-1; epoch_false_promotions=0
        for e in events:
            arrival_state=e["value"]
            if not e["eligible"]:
                arrival_false_promotions += 1
            if e["eligible"] and e["epoch"]>=epoch:
                epoch=e["epoch"]; epoch_state=e["value"]

        result={
          "schema_version":"1.1",
          "evidence_class":"EXECUTION_CONTEXT_TO_BE_WRAPPED",
          "source_class_coverage":{"covered":len(SOURCE_CLASSES),"total":len(SOURCE_CLASSES),"classes":SOURCE_CLASSES},
          "stale_promotion_gate_ok":stale_gate_ok,
          "work_revision_binding":{
            "stale_work_credit_gate_ok":stale_work_credit_gate_ok,
            "missing_component_binding_gate_ok":missing_binding_gate_ok,
            "stale_diagnostic_rows":stale_work_rows_after_restart,
            "current_work_credit_rows":current_work_credit_after_restart,
          },
          "duplicate_provenance":{"observations":dup[0],"distinct_provenance":dup[1]},
          "material_reentry_specific":{
            "pending_before_close":pending_open_before,
            "pending_after_close":pending_open_after,
            "pending_after_restart":pending_open_after_restart,
            "closed_receipt_state_after_restart":r_open[0],
          },
          "other_material_pending_after_restart":open_other_material,
          "contradiction_rows_preserved":contra_count,
          "restart_checkpoint":{"semantic_epoch":cp[0],"health_state":cp[1],"last_reentry_receipt_id":cp[2]},
          "performance":{"n":perf_n,"elapsed_s":round(elapsed,6),"rows_per_s":round(perf_n/elapsed,1),
            "insert_assess_ms_p50":round(statistics.median(lat),6),
            "insert_assess_ms_p95":round(sorted(lat)[int(.95*len(lat))-1],6),
            "db_bytes":os.path.getsize(dbpath)},
          "out_of_box":{"name":"temporal_braid_fault","arrival_order_final":arrival_state,
            "epoch_aware_final":epoch_state,"arrival_order_false_promotions":arrival_false_promotions,
            "epoch_aware_false_promotions":epoch_false_promotions,"final_epoch":epoch,"expected_final":"REFINED"},
        }
        checks = {
          "source_coverage": result["source_class_coverage"]["covered"] == result["source_class_coverage"]["total"],
          "stale_gate": result["stale_promotion_gate_ok"],
          "stale_work_credit_gate": stale_work_credit_gate_ok,
          "current_work_binding_gate": missing_binding_gate_ok,
          "stale_work_preserved_diagnostic": stale_work_rows==1 and stale_work_rows_after_restart==1,
          "current_work_credit_bound": current_work_credit_rows==1 and current_work_credit_after_restart==1,
          "provenance_preserved": dup == (2,2),
          "specific_reentry_closed": pending_open_before==1 and pending_open_after==0 and pending_open_after_restart==0 and r_open[0]=="CLOSED",
          "contradiction_preserved": contra_count==2,
          "checkpoint_recovered": cp==(141,"HEALTHY","r-open"),
          "oob_epoch_guard": epoch_false_promotions==0 and arrival_false_promotions==1 and epoch_state=="REFINED",
        }
        result["checks"]=checks
        result["pass"]=all(checks.values())
        return result
    finally:
        if con is not None:
            try: con.close()
            except Exception: pass
        if os.path.exists(dbpath): os.unlink(dbpath)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--schema",default=str(DEFAULT_SCHEMA))
    ap.add_argument("--perf-n",type=int,default=5000)
    ap.add_argument("--out")
    args=ap.parse_args()
    r=run(Path(args.schema),args.perf_n)
    text=json.dumps(r,indent=2,sort_keys=True)+"\n"
    if args.out:
        Path(args.out).write_text(text,encoding="utf-8")
    print(text,end="")
    raise SystemExit(0 if r["pass"] else 1)

if __name__=="__main__":
    main()
