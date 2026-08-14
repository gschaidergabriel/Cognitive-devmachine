#!/usr/bin/env python3
"""Differential handoff test: frozen FRANK ActiveAssembly score -> ClayCode compiler."""
from __future__ import annotations
import importlib.util,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import claycode_base_pure_toolchain as cc
SRC=ROOT/'research_entity/claycode/base/examples/FRANK_ACTIVE_ASSEMBLY_SCORE_V1.clay';REF=ROOT/'research_entity/harness/reference/active_assembly.py';OUT=ROOT/'research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_SCORE_HANDOFF_RECEIPT.json';SEED=20260809

def load_ref():
 spec=importlib.util.spec_from_file_location('aa_ref',REF);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def main():
 m=load_ref();typed=cc.compile_source(SRC.read_text());rng=random.Random(SEED);mismatch=[]
 for i in range(2000):
  vals=[rng.random() for _ in range(4)];p=m.AssemblyPacket(str(i),'f','memory',*vals,valid_epoch=1);want=m.packet_score(p);got=cc.evaluate(typed,'score',vals)
  if round(float(got),12)!=want:mismatch.append({'i':i,'args':vals,'ref':want,'clay':got})
 native=[]
 for vals in ([.9,.8,.4,.1],[0.,0.,0.,1.],[1.,1.,1.,0.],[.123,.456,.789,.222]):
  row=cc.differential(typed,'score',list(vals));native.append(row)
  if not row['match']:mismatch.append({'kind':'native','row':row})
 report={'schema_version':'1.0','experiment':'Frozen FRANK ActiveAssembly packet_score real-subsystem ClayCode handoff','frank_reference':str(REF.relative_to(ROOT)),'frank_reference_sha256':cc.sha(REF.read_bytes()),'clay_source':str(SRC.relative_to(ROOT)),'clay_source_sha256':cc.sha(SRC.read_bytes()),'clay_typed_semantic_hash':typed['semantic_hash'],'random_seed':SEED,'reference_differential_cases':2000,'native_translation_cases':len(native),'mismatch_count':len(mismatch),'mismatches':mismatch[:20],'pass':not mismatch,'authority_note':'packet score is descriptive cognition only and carries no execution authority','scope_guard':'This closes a real frozen FRANK subsystem handoff evidence slice, not FULL_FRANK_HANDOFF or target-host acceptance.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':report['pass'],'mismatch_count':len(mismatch)}));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
