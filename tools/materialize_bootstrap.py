#!/usr/bin/env python3
"""Refresh BOOTSTRAP_MINIMAL.json from the current canonical head.

Only canonical-derived fields are rewritten; policy/budget/invariant content remains in the
checked-in bootstrap template. CI runs this and fails if the committed index is stale.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'research_entity'/'continuity'/'RESEARCH_ENTITY_CANONICAL.json'
BOOT=ROOT/'research_entity'/'continuity'/'BOOTSTRAP_MINIMAL.json'

c=json.loads(CANON.read_text(encoding='utf-8'))
b=json.loads(BOOT.read_text(encoding='utf-8'))
b['expected_entity_version']=c['entity_version']
b['expected_revision']=c['revision']
b['expected_state_hash']=c['state_hash']
b['active_experiment_ids']=c.get('active_experiment_ids',[])
b['critical_negative_result_ids']=c.get('critical_negative_result_ids',[])
b['architecture_frontier']=c.get('architecture_frontier',[])
BOOT.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"bootstrap refreshed: revision={c['revision']} state={c['state_hash']}")
