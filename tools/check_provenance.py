#!/usr/bin/env python3
"""Validate multi-researcher artifact provenance.

This checks actor IDs, duplicate provenance IDs, referenced paths and basic provider/role
consistency. It intentionally does not invent provenance for legacy/imported artifacts.
Raw source attribution is handled by source manifests; authored Research-Entity artifacts
are indexed in ARTIFACT_PROVENANCE.jsonl.
"""
from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'research_entity'/'global'/'RESEARCH_ACTOR_REGISTRY.json'
LEDGER=ROOT/'research_entity'/'provenance'/'ARTIFACT_PROVENANCE.jsonl'
SCHEMA=ROOT/'schemas'/'provenance.schema.json'

# These high-value governance/runtime artifacts must always have explicit authorship.
MUST_COVER={
 'PROJECT_AUTO_BOOT_KERNEL_FINAL.txt',
 'CLAUDE.md',
 'CLAUDE_CODE_INTRODUCTION.md',
 'research_entity/global/RESEARCH_SCOPE_CHARTER.md',
 'research_entity/global/DOMAIN_REGISTRY.json',
 'research_entity/global/SESSION_MEMBERSHIP_PROTOCOL.md',
 'research_entity/global/RESEARCH_ACTOR_REGISTRY.json',
 'research_entity/global/MULTI_RESEARCHER_GOVERNANCE.md',
 'research_entity/global/PROVENANCE_POLICY.md',
 'research_entity/continuity/BOOTSTRAP_MINIMAL.json',
 'research_entity/continuity/OPERATIONAL_STATUS.json',
 'tools/build_source_db.py',
 'tools/validate_research_entity.py',
 '.github/workflows/research-entity-verify.yml'
}

def load_jsonl(path:Path):
    out=[]
    for n,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: out.append((n,json.loads(line)))
        except Exception as e: raise RuntimeError(f'{path}:{n}: {e}') from e
    return out

def main()->int:
    errors=[]
    reg=json.loads(REGISTRY.read_text(encoding='utf-8'))
    actors={x['actor_id']:x for x in reg['actors']}
    schema=json.loads(SCHEMA.read_text(encoding='utf-8'))
    validator=Draft202012Validator(schema)
    seen_ids=set(); covered=set()

    for lineno,item in load_jsonl(LEDGER):
        label=f'{LEDGER.relative_to(ROOT)}:{lineno}'
        for e in validator.iter_errors(item): errors.append(f'{label}: {e.message}')
        pid=item.get('provenance_id')
        if pid in seen_ids: errors.append(f'{label}: duplicate provenance_id {pid}')
        seen_ids.add(pid)
        path=item.get('path','')
        if path: covered.add(path)
        actor=item.get('origin_actor','')
        known = actor in actors or actor.startswith('external-author:') or actor.startswith('legacy-')
        if not known: errors.append(f'{label}: unknown origin_actor {actor!r}')
        if actor in actors:
            expected=actors[actor]
            role=item.get('actor_role')
            if role and role != expected.get('role'):
                errors.append(f'{label}: actor_role {role!r} disagrees with registry role {expected.get("role")!r}')
            provider=item.get('provider')
            org=expected.get('organization')
            if provider and org and provider != org:
                errors.append(f'{label}: provider {provider!r} disagrees with registry organization {org!r}')
        if path and path != str(LEDGER.relative_to(ROOT)) and not (ROOT/path).exists():
            errors.append(f'{label}: referenced path does not exist: {path}')

    missing=sorted(MUST_COVER-covered)
    for p in missing: errors.append(f'missing mandatory provenance record for {p}')

    if errors:
        print('PROVENANCE CHECK FAILED')
        for e in errors: print(' -',e)
        return 1
    print(f'PROVENANCE CHECK PASS: {len(seen_ids)} records, {len(covered)} paths, actors={sorted(actors)}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
