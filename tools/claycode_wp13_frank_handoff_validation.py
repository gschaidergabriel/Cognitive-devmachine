#!/usr/bin/env python3
"""Differential handoff test for a real current FRANK H1 subsystem.

The source under test is ClayCode implementation of ActiveAssembly packet_score from
research_entity/harness/reference/active_assembly.py. Hosted execution proves semantic
compatibility of this bounded subsystem only; WP13 still requires the Andreas Ubuntu
production handoff and broader frozen FRANK subsystem coverage before promotion.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from claycode_base_pure_toolchain import compile_source, differential, evaluate

CLAY=ROOT/'research_entity/claycode/apps/frank_active_assembly_packet_score_v1.clay'
REF=ROOT/'research_entity/harness/reference/active_assembly.py'
OUT=ROOT/'research_entity/claycode/autonomous/WP13_FRANK_PACKET_SCORE_HANDOFF_RECEIPT.json'
SEED=130013


def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()


def load_reference():
    spec=importlib.util.spec_from_file_location('wp13_active_assembly_ref',REF)
    if spec is None or spec.loader is None: raise RuntimeError('REFERENCE_IMPORT_FAILED')
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod); return mod


def main()->int:
    mod=load_reference(); source=CLAY.read_text(encoding='utf-8'); typed=compile_source(source)
    rng=random.Random(SEED); rows=[]; mismatches=0; native_mismatches=0
    fixed=[(0.0,0.0,0.0,0.0),(1.0,1.0,1.0,1.0),(0.9,0.8,0.4,0.1),(0.5,0.5,0.5,0.5)]
    vectors=fixed+[tuple(rng.random() for _ in range(4)) for _ in range(60)]
    native_indices=set(range(0,len(vectors),4))
    generated_hashes=[]
    for idx,args in enumerate(vectors):
        expected=mod.packet_score(mod.AssemblyPacket('p','f','memory',args[0],args[1],args[2],args[3],1))
        observed=float(evaluate(typed,'packet_score',list(args)))
        same=round(observed,12)==expected
        native_same=True; native_value=None; c_hash=None
        if idx in native_indices:
            d=differential(typed,'packet_score',list(args)); native_value=float(d['native_stdout']); c_hash=d['generated_c_sha256']; generated_hashes.append(c_hash)
            native_same=d['match'] and round(native_value,12)==expected
        mismatches+=int(not same); native_mismatches+=int(not native_same)
        rows.append({'index':idx,'args':list(args),'reference_rounded12':expected,'interpreter':observed,'semantic_match':same,'native':native_value,'native_match':native_same,'generated_c_sha256':c_hash})
    report={
      'schema_version':'1.0','experiment':'real FRANK ActiveAssembly packet_score -> ClayCode typed IR/evaluator/C11 handoff',
      'reference_path':str(REF.relative_to(ROOT)),'reference_sha256':sha(REF),'clay_source_path':str(CLAY.relative_to(ROOT)),'clay_source_sha256':sha(CLAY),
      'clay_semantic_hash':typed['semantic_hash'],'seed':SEED,'vectors':len(vectors),'native_vectors':len(native_indices),
      'semantic_mismatches':mismatches,'native_mismatches':native_mismatches,'generated_c_unique_hashes':len(set(generated_hashes)),
      'rows':rows,'pass':mismatches==0 and native_mismatches==0,
      'counts_as_full_wp13_pass':False,'counts_as_target_acceptance':False,
      'scope':'REAL_CURRENT_FRANK_H1_SUBSYSTEM_BOUNDED_PACKET_SCORE',
      'next_required':'repeat through production target compiler/runtime on Andreas Ubuntu and expand handoff to stateful ActiveAssembly selection/conflict/re-expansion before WP13 promotion'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'pass':report['pass'],'vectors':len(vectors),'native_vectors':len(native_indices),'semantic_mismatches':mismatches,'native_mismatches':native_mismatches}))
    return 0 if report['pass'] else 1

if __name__=='__main__': raise SystemExit(main())
