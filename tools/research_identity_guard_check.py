#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fail=[]

def require(path,*needles):
    """`needles` ist je Eintrag entweder ein Text oder ein Tupel gleichwertiger Texte.

    Ein Tupel heisst: EINE der Formen muss vorkommen. Gemeldet wird die erste (die
    kanonische), damit die Fehlermeldung eindeutig bleibt. Gebraucht wird das, weil die
    Verfassung von der FRANK- auf die self.root-Sprache umgestellt wurde und beide
    Formulierungen dieselbe Festlegung trafen.
    """
    p=ROOT/path
    if not p.exists():
        fail.append(f'MISSING:{path}');return ''
    text=p.read_text(encoding='utf-8')
    for n in needles:
        formen = n if isinstance(n,tuple) else (n,)
        if not any(f in text for f in formen):
            fail.append(f'MISSING_INVARIANT:{path}:{formen[0]}')
    return text

inj=require('research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md',
    'I_AM=RESEARCH_ENTITY_TEMPORARY_WORKER',
    ('I_AM_NOT=FRANK','I_AM_NOT=Frank'),
    ('ANDREAS_INTERFACE=FRANK_ONLY','ANDREAS_INTERFACE=Frank_only'),
    'FRANK_ROOM_MEANS=RESEARCH_ABOUT_FRANK_NOT_ROLEPLAY_AS_FRANK','every','RESEARCH_IDENTITY_DRIFT')

boot_path=ROOT/'research_entity/continuity/BOOTSTRAP_MINIMAL.json'
canonical_path=ROOT/'research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json'
boot=json.loads(boot_path.read_text(encoding='utf-8'))
canonical=json.loads(canonical_path.read_text(encoding='utf-8'))

# This checker guards identity continuity, not a particular bootstrap/stack release number.
# Version numbers are intentionally not hard-pinned: unrelated schema/epoch advancement must
# not create an identity-guard false negative. Instead, require the live boot pointer to be
# coherent with canonical identity/revision/hash and require the current stack to expose an epoch.
if not isinstance(boot.get('schema_version'),str) or not boot.get('schema_version'):
    fail.append('BOOT_SCHEMA_MISSING')
if boot.get('entity_id')!=canonical.get('entity_id'):
    fail.append('BOOT_CANONICAL_ENTITY_MISMATCH')
if boot.get('expected_revision')!=canonical.get('revision'):
    fail.append('BOOT_CANONICAL_REVISION_MISMATCH')
if boot.get('expected_state_hash')!=canonical.get('state_hash'):
    fail.append('BOOT_CANONICAL_STATE_HASH_MISMATCH')
if boot.get('identity',{}).get('every_turn_guard')!='research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md':
    fail.append('BOOT_IDENTITY_GUARD_POINTER_MISSING')
per=boot.get('per_turn',{})
if 'every substantive prompt_run_id' not in per.get('identity_injection',''):
    fail.append('BOOT_PER_TURN_INJECTION_NOT_MANDATORY')
inv='\n'.join(boot.get('mandatory_invariants',[]))
for formen in (('Research Entity != Frank','Clay is not self.root/Frank','Research Entity != self.root'),
               ('Andreas uses Frank only','Andreas uses the human surface Frank only'),
               ('every substantive prompt_run_id refreshes the Research Entity identity injection',)):
    if not any(f in inv for f in formen):fail.append('BOOT_MANDATORY_INVARIANT_MISSING:'+formen[0])

stack=require('research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay',
    'researcher_identity_injection=@research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md',
    'before_every_substantive_prompt_run inject CURRENT.researcher_identity_injection',
    ('home_room("frank") = research_about(FRANK); never role_transition_to(FRANK)',
     'home_room("frank") = research_about(self.root_human_surface_Frank); never role_transition_to(self.root)'),
    ('invariant Andreas_uses_FRANK_only','rule ANDREAS.interface=FRANK_ONLY','invariant Andreas_uses_self.root_human_surface_only'),
    ('invariant ResearchEntity_and_FRANK_are_separate_entities','invariant ResearchEntity_and_self.root_are_separate_entities'))
if stack and not re.search(r'(?m)^epoch\s+\d+\s*$',stack):
    fail.append('STACK_EPOCH_MISSING_OR_INVALID')

turn=require('research_entity/global/RAE_TURN_KERNEL.clay',
    'module clay.turn.','load(LATEST.persona,LATEST.work_fabric,LATEST.researcher_identity_injection) each substantive_turn',
    'inject(CURRENT.identity_guard) before first_material_reasoning each substantive_turn',
    'if home_room==frank then meaning=research_about(FRANK); never meaning=become(FRANK)',
    'detect(RESEARCH_IDENTITY_DRIFT) -> STOP + reinject(CURRENT.identity_guard)',
    'rule ANDREAS.interface=FRANK_ONLY','rule RESEARCH_ENTITY != FRANK')
hook=require('.claude/hooks/rae_hook.py',
    "IDENTITY=ROOT/'research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md'",
    'def identity_lock():','I_AM_NOT=FRANK','ANDREAS_INTERFACE=FRANK_ONLY',
    "if ev=='UserPromptSubmit':",'emit(ev,kernel()',
    'FRANK_RESEARCH_FRAME{actor=RESEARCH_ENTITY;subject=FRANK;room=frank;role_transition=FORBIDDEN;Andreas_interface=FRANK_ONLY}',
    "if ev=='PostToolUse':",'POST_FRANK_CONTEXT_REINJECTION{actor=RESEARCH_ENTITY;subject=FRANK;role_transition=FORBIDDEN;Andreas_interface=FRANK_ONLY}')

# Hard anti-collapse patterns. Explicit never/forbidden clauses are required above and are not violations.
for path,text in [('injection',inj),('stack',stack),('turn',turn),('hook',hook)]:
    for pat in (r'ResearchEntity\s*==\s*FRANK',r'RESEARCH_ENTITY\s*=\s*FRANK',r'ANDREAS\.interface\s*=\s*RESEARCH_ENTITY'):
        if re.search(pat,text,re.I):fail.append(f'IDENTITY_COLLAPSE_PATTERN:{path}:{pat}')
if fail:
    print(json.dumps({'status':'FAIL','failures':fail},ensure_ascii=False,indent=2));sys.exit(1)
print(json.dumps({
    'status':'PASS',
    'identity_guard':'EVERY_TURN_HOOKED',
    'actor':'RESEARCH_ENTITY',
    'frank':'SEPARATE_SUBJECT',
    'andreas_interface':'FRANK_ONLY',
    'canonical_revision':canonical.get('revision'),
    'canonical_state_hash':canonical.get('state_hash'),
    'stack_epoch':int(re.search(r'(?m)^epoch\s+(\d+)\s*$',stack).group(1)),
},indent=2))
