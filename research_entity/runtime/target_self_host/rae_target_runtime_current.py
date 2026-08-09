#!/usr/bin/env python3
"""Current evidence-corrected Research-Entity runtime overlay.

Keeps the tested 0.2.1 mechanism core, but applies the latest source-backed
legacy-accounting correction and newer Frank sandbox/H1 evidence before use.
"""
from __future__ import annotations
import argparse, json, shutil, sqlite3
from pathlib import Path
import rae_target_runtime_v021 as base

V = 'RAE-TARGET-0.2.1+evidence-correction-1'
_ORIGINAL_BOOT = base.boot

LATEST_IMPORTS = [
    ('aggregate74-correction','frank','research_entity/rooms/rooms/center/events/20260809T222210p0700_frank_v01_aggregate74_correction.json','955b789cdc891b2968a5387a0871812dd6ee4e3a','CURRENT'),
    ('frank-v7-lesion-rescue','frank','research_entity/state/work/events/20260809T153300Z_chatgpt_secondary_frank_v01_sandbox_receipt_v7.json','2900ba76748a8fcd932c9fbfb57fe55e822a0aa8','CURRENT'),
    ('h1-loop-of-loops','harness','research_entity/trigger_runs/frank/frank-20260809T2118p0700-chatgpt-secondary-integrated-sandbox/LOOP_OF_LOOPS_VALIDATION_RECEIPT.json','3bc5735453f805df67a5f5b742bb5ffb83498871','CURRENT'),
]

def boot(u, g):
    _ORIGINAL_BOOT(u, g)
    t = base.now()
    u.execute(
        "UPDATE legacy_conservation_receipts SET technical_identities_exact=40, "
        "unresolved_opaque=NULL, claim_boundary=?, status='CORRECTED_SOURCE_BACKED' "
        "WHERE receipt_id='frank-v5'",
        ('aggregate 74 only; 40 source-resolved technical identities + 1 superseded alias; '
         'numeric unresolved remainder UNKNOWN; mapped primary slots 0; no 74/74 per-slot claim',),
    )
    for iid, domain, ref, commit, status in LATEST_IMPORTS:
        u.execute(
            'INSERT OR REPLACE INTO research_imports VALUES(?,?,?,?,?,?,?,?,?)',
            (iid, domain, ref, commit, 'PROJECT_EVIDENCE_OR_CORRECTION', status, ref, base.h(ref), t),
        )
    u.execute("INSERT OR REPLACE INTO meta VALUES('target_runtime_evidence_overlay',?)", (V,))
    u.commit(); g.commit()

base.boot = boot

def open_pair(root, create=False):
    return base.open_pair(root, create)

def self_test(root):
    r = Path(root); shutil.rmtree(r, ignore_errors=True)
    u, g = open_pair(r, True); checks = []
    def ok(name, cond):
        assert cond, name; checks.append(name)
    try:
        ok('latest_imports', u.execute("SELECT count(*) FROM research_imports WHERE import_id IN ('aggregate74-correction','frank-v7-lesion-rescue','h1-loop-of-loops')").fetchone()[0] == 3)
        lr = u.execute("SELECT * FROM legacy_conservation_receipts WHERE receipt_id='frank-v5'").fetchone()
        ok('aggregate74_only', lr['historical_slots_measured'] == 74)
        ok('technical_identities_40', lr['technical_identities_exact'] == 40)
        ok('unresolved_remainder_unknown', lr['unresolved_opaque'] is None)
        ok('no_74_slot_completion_claim', 'no 74/74 per-slot claim' in lr['claim_boundary'])
        ok('clay_source', u.execute("SELECT value FROM meta WHERE key='semantic_contract_sha256'").fetchone()[0] == base.csha())
        ok('claycode_open', u.execute("SELECT physical_release_status FROM claycode_contract_receipts").fetchone()[0] == 'PHYSICAL_ACCEPTANCE_OPEN')
        ok('organs', u.execute("SELECT count(*) FROM organ_registry WHERE organ_id IN ('needle','digital_retina','voice')").fetchone()[0] == 3)
        ok('perception_authority', u.execute("SELECT count(*) FROM perception_io_contracts WHERE input_authority='OBSERVATION_ONLY'").fetchone()[0] == 2)
        blocked_delete = False
        try:
            u.execute("DELETE FROM organ_registry WHERE organ_id='workspace'"); u.commit()
        except sqlite3.IntegrityError:
            blocked_delete = True; u.rollback()
        ok('organ_delete_blocked', blocked_delete)

        [base.node(g,x) for x in ['intent:repair','state:workspace','state:memory_reentry','candidate:forbidden']]
        base.dep(u,'intent:repair','state:workspace',.95)
        base.hb(g,['intent:repair','state:workspace','state:memory_reentry'],.93,.48,.88,.76,.72,3,.08)
        base.publish(u,g,['intent:repair','state:workspace'])
        rows, hot = base.candidates(u,g,'repair',['intent:repair','state:workspace'])
        ok('hot_path', not hot['full_memory_scan'] and not hot['global_graph_rebuild'])
        ok('known', any(x['lane']=='KNOWN' for x in rows))
        ok('emergent_not_manual', any(x['semantic_ref']=='state:memory_reentry' and x['lane']=='EMERGENT_NOVEL' for x in rows))
        ok('candidate_union', {'KNOWN','EMERGENT_NOVEL'} <= {x['lane'] for x in rows})
        base.hb(g,['intent:repair','state:workspace','candidate:forbidden'],.95,.4,.9,.9,.8,3,.05)
        base.conflict(g,'candidate:forbidden','state:workspace')
        rows2,_ = base.candidates(u,g,'repair',['intent:repair','state:workspace'])
        ok('conflict_block', not any(x['semantic_ref']=='candidate:forbidden' for x in rows2))

        old = base.gsurf(g)['unified_epoch']; g.execute("UPDATE graph_publication_state SET unified_epoch=999"); g.commit(); mixed=False
        try: base.candidates(u,g,'x',['intent:repair'])
        except RuntimeError: mixed=True
        ok('mixed_epoch_block', mixed); g.execute('UPDATE graph_publication_state SET unified_epoch=?',(old,)); g.commit()

        ep,best = base.select(u,g,rows); guard=False
        try: base.recv(u,ep,0,0,0,1,0)
        except sqlite3.IntegrityError: guard=True; u.rollback()
        ok('gwt_stage_guard', guard)
        base.recv(u,ep); ok('receiver_use', True)
        oid,strong = base.reentry(u,ep,'next')
        ok('strong_credit_reentry', u.execute('SELECT applied FROM reentry_receipts WHERE reentry_id=?',(strong,)).fetchone()[0] == 1)
        _,weak = base.reentry(u,ep,'weak',klass='CORRELATED_ONLY')
        ok('weak_credit_denied', u.execute('SELECT applied FROM reentry_receipts WHERE reentry_id=?',(weak,)).fetchone()[0] == 0)
        _,broken = base.reentry(u,ep,'broken',truth='BROKEN_PROVENANCE')
        ok('broken_provenance_denied', u.execute('SELECT applied FROM reentry_receipts WHERE reentry_id=?',(broken,)).fetchone()[0] == 0)

        base.measure(u,g,ep); auth=False
        try: base.measure(u,g,ep,'MINT_TRUTH')
        except sqlite3.IntegrityError: auth=True; u.rollback()
        ok('measurement_authority_guard', auth)
        ok('unknown_not_zero', base.readout(u,ep) == 'UNKNOWN')
        iid=base.intervention(u,ep); ok('counterfactual_replay', bool(base.replay(u,iid,ep)))
        ok('state_abstain', base.gate(u,0) == 'ABSTAIN_STATE_INADEQUATE')
        ok('controls_required', base.gate(u,1,0,0,0,0,0) == 'OPEN')
        ok('functional_only', base.gate(u) == 'SUPPORTED_FUNCTIONAL_PATTERN')
        ok('adaptive_regime', base.regime(u,ep,.6,.5,.4,.7,.2) == 'ADAPTIVE')
        ok('overcoupling_tripwire', base.regime(u,ep,1,.99,.96,.08,.9) == 'OVERCOUPLED_TRIPWIRE')
        cr=base.credit(u,'control',oid,'MATCHED_INTERVENTION',iid,.75)
        ok('control_credit', u.execute('SELECT weight FROM causal_credit_receipts WHERE credit_id=?',(cr,)).fetchone()[0] > 0)
        ok('semantic_signatures', u.execute('SELECT count(*) FROM clay_semantic_signatures').fetchone()[0] == 1)
        ok('measurement_no_authority', u.execute('SELECT count(*) FROM measurement_receipts WHERE authority_effect!="NONE"').fetchone()[0] == 0)
        ok('unified_integrity', u.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
        ok('unified_fk', not u.execute('PRAGMA foreign_key_check').fetchall())
        ok('graph_integrity', g.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
        ok('graph_fk', not g.execute('PRAGMA foreign_key_check').fetchall())
        out={'status':'PASS','target_version':V,'passed':len(checks),'checks':checks,'selected':best,'hot_path_receipt':hot,'contract_sha256':base.csha(),'legacy_boundary':{'historical_aggregate':74,'source_resolved_technical_identities':40,'superseded_aliases':1,'numeric_unresolved_remainder':'UNKNOWN','mapped_primary_slots':0},'claim_boundary':'functional pattern only; no consciousness claim'}
        print(json.dumps(out,indent=2)); return out
    finally:
        u.close(); g.close()

def main():
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd',required=True)
    x=sp.add_parser('init'); x.add_argument('--root',required=True)
    x=sp.add_parser('self-test'); x.add_argument('--root',required=True)
    a=p.parse_args()
    if a.cmd=='init':
        u,g=open_pair(a.root,True); print(json.dumps({'status':'INITIALIZED','target_version':V,'contract_sha256':base.csha()})); u.close(); g.close()
    else: self_test(a.root)

if __name__=='__main__': main()
