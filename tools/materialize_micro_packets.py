#!/usr/bin/env python3
"""Materialize searchable text from RAE knowledge micro-packets.

The packet files are derived research memory with explicit provenance. This tool only
creates a rebuildable text projection consumed by the existing source DB builder.
It does not promote claims or alter canonical state.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'research_entity'/'knowledge_micro_packets'
OUT=ROOT/'research_sources'/'derived'/'knowledge_micro_packets'
META_RE=re.compile(r'<!--\s*RAE_META\s*(\{.*?\})\s*RAE_META\s*-->',re.S)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]; seen=set(); errors=[]
    if SRC.exists():
        for p in sorted(SRC.rglob('*.md')):
            text=p.read_text(encoding='utf-8',errors='strict')
            m=META_RE.search(text)
            if not m:
                errors.append(f'{p.relative_to(ROOT)}: missing RAE_META')
                continue
            try: meta=json.loads(m.group(1))
            except Exception as e:
                errors.append(f'{p.relative_to(ROOT)}: invalid RAE_META: {e}')
                continue
            pid=meta.get('packet_id')
            if not pid:
                errors.append(f'{p.relative_to(ROOT)}: missing packet_id')
                continue
            if pid in seen:
                errors.append(f'duplicate packet_id: {pid}')
                continue
            seen.add(pid)
            body=META_RE.sub('',text).strip()
            header=' | '.join([
                f'packet_id={pid}',
                f'title={meta.get("title","")}',
                'domains='+','.join(meta.get('domains',[])),
                'topics='+','.join(meta.get('topics',[])),
                f'epistemic_class={meta.get("epistemic_class","")}',
                f'claim_status_hint={meta.get("claim_status_hint","")}',
                f'origin_class={meta.get("origin_class","")}',
                f'origin_actor={meta.get("origin_actor","")}',
                'search_terms='+','.join(meta.get('search_terms',[])),
            ])
            rows.append(f'# {meta.get("title",pid)}\n\n{header}\n\n{body}\n\nSOURCE_PACKET={p.relative_to(ROOT)}\n')
    if errors:
        print('\n'.join(errors))
        return 2
    content='\n\n---\n\n'.join(rows)
    (OUT/'micro_packets.md').write_text(content+'\n',encoding='utf-8')
    index={
      'schema_version':'1.0','packet_count':len(rows),
      'projection_path':'research_sources/derived/knowledge_micro_packets/micro_packets.md',
      'sha256':hashlib.sha256(content.encode()).hexdigest()
    }
    (OUT/'INDEX.json').write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(index,indent=2,ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
