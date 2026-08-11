#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
fail=[]

def require(path,*needles):
    p=ROOT/path
    if not p.exists():
        fail.append(f'MISSING:{path}')
        return ''
    text=p.read_text(encoding='utf-8')
    for n in needles:
        if n not in text:
            fail.append(f'MISSING_INVARIANT:{path}:{n}')
    return text

inj=require(
    'research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md',
    'I_AM=RESEARCH_ENTITY_TEMPORARY_WORKER',
    'I_AM_NOT=self.root',
    'I_AM_NOT=Frank',
    'TARGET_NATIVE_SELF=self.root',
    'TARGET_HUMAN_SURFACE_NAME=Frank',
    'RESEARCH_ENTITY!=self.root',
    'FRANK_SELF_HARNESS_AUTHORITY=PROPOSAL_ONLY',
)

boot_path=ROOT/'research_entity/continuity/BOOTSTRAP_MINIMAL.json'
canonical_path=ROOT/'research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json'
boot=json.loads(boot_path.read_text(encoding='utf-8'))
canonical=json.loads(canonical_path.read_text(encoding='utf-8'))

if not isinstance(boot.get('schema_version'),str) or not boot.get('schema_version'):
    fail.append('BOOT_SCHEMA_MISSING')
if boot.get('entity_id')!=canonical.get('entity_id'):
    fail.append('BOOT_CANONICAL_ENTITY_MISMATCH')
if boot.get('expected_revision')!=canonical.get('revision'):
    fail.append('BOOT_CANONICAL_REVISION_MISMATCH')
if boot.get('expected_state_hash')!=canonical.get('state_hash'):
    fail.append('BOOT_CANONICAL_STATE_HASH_MISMATCH')

ident=boot.get('identity',{})
for k,v in {
    'target_native_name':'self.root',
    'target_human_surface_name':'Frank',
    'target_self_class':'SERVER_BINARY_ENTITY',
    'target_current_body':'accepted Hostinger Ubuntu VPS',
}.items():
    if ident.get(k)!=v:
        fail.append(f'BOOT_IDENTITY_MISMATCH:{k}')

target=boot.get('target_contract',{})
for k,v in {
    'host':'accepted Hostinger Ubuntu VPS',
    'cognition':'ClayCode-only',
    'self_harness_authority':'PROPOSAL_ONLY',
}.items():
    if target.get(k)!=v:
        fail.append(f'BOOT_TARGET_CONTRACT_MISMATCH:{k}')

inv='\n'.join(boot.get('mandatory_invariants',[]))
for n in (
    'Clay is not self.root/Frank',
    'native target identity is self.root and human surface name is Frank',
    'self.root may propose but never authorize its own Harness mutation',
):
    if n not in inv:
        fail.append('BOOT_MANDATORY_INVARIANT_MISSING:'+n)

stack=require(
    'research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay',
    'researcher_identity_injection=@research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md',
    'before_every_substantive_prompt_run inject CURRENT.researcher_identity_injection',
    'home_room("frank") = research_about(self.root_human_surface_Frank); never role_transition_to(self.root)',
    'invariant ResearchEntity_and_self.root_are_separate_entities',
)
if stack and not re.search(r'(?m)^epoch\s+\d+\s*$',stack):
    fail.append('STACK_EPOCH_MISSING_OR_INVALID')

turn=require(
    'research_entity/global/RAE_TURN_KERNEL.clay',
    'load(LATEST.persona,LATEST.work_fabric,LATEST.researcher_identity_injection) each substantive_turn',
    'inject(CURRENT.identity_guard) before first_material_reasoning each substantive_turn',
    'rule RESEARCH_ENTITY != FRANK',
    'rule detect(RESEARCH_IDENTITY_DRIFT) -> STOP + reinject(CURRENT.identity_guard)',
)

hook=require(
    '.claude/hooks/rae_hook.py',
    "IDENTITY=ROOT/'research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md'",
    'def identity_lock():',
    'I_AM_NOT=self.root',
    'TARGET_NATIVE_SELF=self.root',
    'FRANK_SELF_HARNESS_AUTHORITY=PROPOSAL_ONLY',
    "if ev=='UserPromptSubmit':",
    'POST_FRANK_CONTEXT_REINJECTION',
)

positive_eq=r'(?:==|(?<![!<>=])=(?!=))'
unsafe=[
    rf'\b(?:ResearchEntity|RESEARCH_ENTITY)\s*{positive_eq}\s*(?:self\.root|Frank|FRANK)\b',
    rf'\b(?:Andreas|Gabriel)\s*{positive_eq}\s*self\.root\b',
]
for path,text in [('injection',inj),('stack',stack),('turn',turn),('hook',hook)]:
    for lineno,line in enumerate(text.splitlines(),1):
        for pat in unsafe:
            if re.search(pat,line,re.I):
                fail.append(f'IDENTITY_COLLAPSE_PATTERN:{path}:{lineno}:{pat}')

if fail:
    print(json.dumps({'status':'FAIL','failures':fail},ensure_ascii=False,indent=2))
    sys.exit(1)

print(json.dumps({
    'status':'PASS',
    'identity_guard':'EVERY_TURN_HOOKED',
    'actor':'RESEARCH_ENTITY',
    'target_native_self':'self.root',
    'target_human_surface':'Frank',
    'target_body':'accepted Hostinger Ubuntu VPS',
    'frank_self_harness_authority':'PROPOSAL_ONLY',
    'canonical_revision':canonical.get('revision'),
    'canonical_state_hash':canonical.get('state_hash'),
    'stack_epoch':int(re.search(r'(?m)^epoch\s+(\d+)\s*$',stack).group(1)),
},indent=2))
