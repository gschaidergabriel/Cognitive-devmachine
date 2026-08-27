#!/usr/bin/env python3
"""Validate reserved Research Entity trigger registry and protocol paths."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'research_entity/global/RESEARCH_TRIGGER_REGISTRY.json'
PROJECT=ROOT/'research_entity/global/PROJECT_COMMAND_REGISTRY.json'
REQUIRED={'666','q12','dump','fusion','hypofusion','clayresearch','gwt','frank','emergenz','claycode','hyperposition','claygraph','unifieddb','harness'}


def main():
    errors=[]
    try:r=json.loads(REG.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'trigger registry unreadable: {e}');return 2
    try:p=json.loads(PROJECT.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'project command registry unreadable: {e}');return 2
    triggers=r.get('triggers',{})
    commands=p.get('commands',{})
    missing=REQUIRED-set(triggers)
    extra=set(commands)-set(triggers)
    if missing:errors.append('missing triggers: '+','.join(sorted(missing)))
    if extra:errors.append('project commands absent from authoritative trigger registry: '+','.join(sorted(extra)))
    if set(commands)!=set(triggers):errors.append('project/trigger registry key sets differ')
    if 'clay' in triggers:errors.append('clay must be entity address/name, not trigger')
    if r.get('trigger_renames',{}).get('clay')!='clayresearch':errors.append('trigger rename clay -> clayresearch missing')
    if p.get('trigger_renames',{}).get('clay')!='clayresearch':errors.append('project trigger rename clay -> clayresearch missing')
    for key,spec in triggers.items():
        if key!=key.lower() or not key.strip() or ' ' in key:errors.append(f'invalid trigger word: {key!r}')
        proto=ROOT/spec.get('protocol','')
        if not proto.is_file():errors.append(f'{key}: missing protocol {spec.get("protocol")}')
        if not spec.get('purpose') and key not in commands:errors.append(f'{key}: missing purpose')
    for path in [ROOT/r.get('master_protocol',''),ROOT/r.get('status_footer_protocol',''),ROOT/'research_entity/global/KNOWLEDGE_MICRO_PACKET_PROTOCOL.md']:
        if not path.is_file():errors.append(f'missing required support file: {path.relative_to(ROOT) if path.is_absolute() else path}')
    if errors:
        print('RAE trigger validation FAILED')
        for e in errors:print(' -',e)
        return 1
    print('RAE trigger validation PASS:', ' · '.join(sorted(triggers)))
    return 0

if __name__=='__main__':raise SystemExit(main())
