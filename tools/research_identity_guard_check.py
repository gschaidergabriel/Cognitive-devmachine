#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fail=[]

def require(path,*needles):
    p=ROOT/path
    if not p.exists():
        fail.append(f'MISSING:{path}');return ''
    text=p.read_text(encoding='utf-8')
    for n in needles:
        if n not in text:fail.append(f'MISSING_INVARIANT:{path}:{n}')
    return text

inj=require('research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md',
    'I_AM=RESEARCH_ENTITY_TEMPORARY_WORKER','I_AM_NOT=FRANK','ANDREAS_INTERFACE=FRANK_ONLY',
    'FRANK_ROOM_MEANS=RESEARCH_ABOUT_FRANK_NOT_ROLEPLAY_AS_FRANK','every','RESEARCH_IDENTITY_DRIFT')
boot=json.loads((ROOT/'research_entity/continuity/BOOTSTRAP_MINIMAL.json').read_text(encoding='utf-8'))
if boot.get('schema_version')!='2.1':fail.append('BOOT_SCHEMA_NOT_2_1')
if boot.get('identity',{}).get('every_turn_guard')!='research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md':fail.append('BOOT_IDENTITY_GUARD_POINTER_MISSING')
per=boot.get('per_turn',{})
if 'every substantive prompt_run_id' not in per.get('identity_injection',''):fail.append('BOOT_PER_TURN_INJECTION_NOT_MANDATORY')
inv='\n'.join(boot.get('mandatory_invariants',[]))
for n in ('Research Entity != Frank','Andreas uses Frank only','every substantive prompt_run_id refreshes the Research Entity identity injection'):
    if n not in inv:fail.append('BOOT_MANDATORY_INVARIANT_MISSING:'+n)
stack=require('research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay',
    'epoch 16','researcher_identity_injection=@research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md',
    'before_every_substantive_prompt_run inject CURRENT.researcher_identity_injection',
    'home_room("frank") = research_about(FRANK); never role_transition_to(FRANK)',
    'invariant Andreas_uses_FRANK_only','invariant ResearchEntity_and_FRANK_are_separate_entities')
turn=require('research_entity/global/RAE_TURN_KERNEL.clay',
    'module clay.turn.v7','load(LATEST.persona,LATEST.work_fabric,LATEST.researcher_identity_injection) each substantive_turn',
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
print(json.dumps({'status':'PASS','identity_guard':'EVERY_TURN_HOOKED','actor':'RESEARCH_ENTITY','frank':'SEPARATE_SUBJECT','andreas_interface':'FRANK_ONLY'},indent=2))
