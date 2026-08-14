#!/usr/bin/env python3
"""Fresh target-host attestation for the full frozen FRANK H2 ActiveAssembly path.

A PASS here is target evidence for APP FULL_FRANK_HANDOFF / CC-WP-13 only when the
registered Andreas Ubuntu host identity is verified. It runs the exact H1<->H2
randomized/adversarial differential at the current git commit and preserves the rule that
serialized data, policy text and symbolic capability names never become bearer authority.
"""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from claycode_target_host_identity import verify,DEFAULT_REGISTRATION,TARGET_HOST
DETAIL=ROOT/'research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H2_RECEIPT.json'
H1=ROOT/'research_entity/harness/reference/active_assembly.py'
H2=ROOT/'research_entity/claycode/base/examples/FRANK_ACTIVE_ASSEMBLY_H2_V1.clay'
SELECTOR=ROOT/'tools/claycode_base_record_selection.py'
OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_FULL_FRANK_H2_HANDOFF.json'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ok,host=verify(DEFAULT_REGISTRATION)
 if not ok:print(json.dumps({'error':'TARGET_HOST_IDENTITY_NOT_VERIFIED','details':host}));return 3
 head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=False).stdout.strip()
 cp=subprocess.run([sys.executable,'tools/claycode_wp13_active_assembly_h2.py'],cwd=ROOT,text=True,capture_output=True,check=False,timeout=600)
 if not DETAIL.exists():print(json.dumps({'error':'H2_DETAIL_RECEIPT_MISSING','returncode':cp.returncode,'stderr_tail':cp.stderr[-3000:]}));return 2
 d=json.loads(DETAIL.read_text(encoding='utf-8'));checks=d.get('checks') or {}
 authority_ok=bool(checks.get('authority_mint_attempt_fail_closed') and checks.get('selector_policy_hash_bound_to_capability') and checks.get('capability_descriptor_not_authority') and checks.get('effect_and_capability_closure_exact'))
 passed=(cp.returncode==0 and d.get('pass') is True and d.get('counterexample_disposition')=='IMPLEMENTABLE_VIA_GENERIC_TYPED_FFI_RUNTIME_COLLECTION' and d.get('language_change_required_by_this_counterexample') is False and d.get('counts_as_target_acceptance') is False and d.get('counts_as_wp13_pass') is False and all(bool(v) for v in checks.values()) and authority_ok)
 app={'pass':passed,'source_or_program_hash':d.get('source_sha256') or sha(H2),'semantic_or_ir_hash':d.get('semantic_hash'),'compiler_runtime_version':f"{d.get('compiler_candidate')} + {d.get('runtime_version')} + {d.get('record_selector_version')}",'target_artifact_hash':d.get('lowered_artifact_hash'),'execution_command_or_test_id':'python tools/claycode_wp13_active_assembly_h2.py','expected':{'reference':'frozen H1 ActiveAssembly field-for-field across randomized/adversarial cases','h1_reference_sha256':sha(H1)},'observed':{'pass':d.get('pass'),'random_cases':d.get('random_cases'),'checks':checks,'counterexample_disposition':d.get('counterexample_disposition'),'translation_contract_hash':d.get('translation_contract_hash'),'record_selector_sha256':sha(SELECTOR)},'negative_or_failure_path':{'authority_and_policy_attacks':[k for k in checks if 'authority' in k or 'capability' in k or 'policy' in k],'all_checks':checks},'authority_boundary_preserved':authority_ok}
 report={'schema_version':'1.1','target_host':TARGET_HOST,'target_host_verified':True,'host_fingerprint':host.get('host_fingerprint',{}),'repository_commit':head,'runner_returncode':cp.returncode,'detail_receipt_sha256':sha(DETAIL),'h1_reference_sha256':sha(H1),'h2_source_sha256':sha(H2),'generic_selector_sha256':sha(SELECTOR),'application':app,'frank_handoff':{'pass':passed,'frozen_frank_source_hashes':[sha(H1)],'claycode_source_hashes':[sha(H2)],'production_chain_receipts':[str(DETAIL.relative_to(ROOT))],'semantic_escape_hatches':[] if passed else ['H2_DIFFERENTIAL_NOT_PASS'],'h2_h3_handoff_ready':passed,'h2_exact_behavior_pass':passed,'h3_contract':'H3 may inline the same generic runtime primitive; no new FRANK-specific semantic primitive is required by this counterexample'},'unresolved_language_counterexamples':[] if passed else ['FULL_ACTIVE_ASSEMBLY_H2'],'pass':passed,'promotion_performed':False,'authority_invariant':'model output != execution authority','stdout_tail':cp.stdout[-3000:],'stderr_tail':cp.stderr[-3000:]}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'pass':passed,'repository_commit':head,'output':str(OUT.relative_to(ROOT))}));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
