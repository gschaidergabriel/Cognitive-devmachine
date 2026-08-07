#!/usr/bin/env python3
"""Materialize searchable text from RAE knowledge micro-packets.

Canonical/raw research evidence is not changed here. Knowledge micro-packets are
DERIVED research memory with explicit provenance. Two storage forms are supported:

1. normal one-packet-per-file Markdown under research_entity/knowledge_micro_packets/**
2. GitHub-efficient packed shards under
   research_entity/knowledge_micro_packets/source_compiled_shards/*.md

A packed shard may contain many `RAE_META` blocks. Every block is materialized as an
individually searchable packet, so packing for Git transport does not reduce retrieval
granularity.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'research_entity'/'knowledge_micro_packets'
OUT=ROOT/'research_sources'/'derived'/'knowledge_micro_packets'
META_RE=re.compile(r'<!--\s*RAE_META\s*(\{.*?\})\s*RAE_META\s*-->',re.S)


def render_packet(meta:dict, body:str, source_path:Path, ordinal:int)->str:
    pid=meta['packet_id']
    header=' | '.join([
        f'packet_id={pid}',
        f'title={meta.get("title","")}',
        'domains='+','.join(meta.get('domains',[])),
        'topics='+','.join(meta.get('topics',[])),
        f'epistemic_class={meta.get("epistemic_class","")}',
        f'claim_status_hint={meta.get("claim_status_hint","")}',
        f'origin_class={meta.get("origin_class","")}',
        f'origin_actor={meta.get("origin_actor","")}',
        f'compiled_by_actor={meta.get("compiled_by_actor","")}',
        f'compiled_by_model={meta.get("compiled_by_model","")}',
        f'source_sha256={meta.get("source_sha256","")}',
        'search_terms='+','.join(meta.get('search_terms',[])),
    ])
    return f'# {meta.get("title",pid)}\n\n{header}\n\n{body.strip()}\n\nSOURCE_PACKET={source_path.relative_to(ROOT)}#{ordinal}\n'


def extract_file(p:Path):
    text=p.read_text(encoding='utf-8',errors='strict')
    matches=list(META_RE.finditer(text))
    if not matches:
        return [],[f'{p.relative_to(ROOT)}: missing RAE_META']
    rows=[]; errors=[]
    for i,m in enumerate(matches):
        try: meta=json.loads(m.group(1))
        except Exception as e:
            errors.append(f'{p.relative_to(ROOT)}#{i}: invalid RAE_META: {e}')
            continue
        pid=meta.get('packet_id')
        if not pid:
            errors.append(f'{p.relative_to(ROOT)}#{i}: missing packet_id')
            continue
        start=m.end(); end=matches[i+1].start() if i+1<len(matches) else len(text)
        body=text[start:end]
        # packed shards separate packet blocks with markdown rules; strip only transport noise
        body=re.sub(r'^\s*---\s*','',body,flags=re.S).strip()
        rows.append((meta,body,i))
    return rows,errors


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rendered=[]; seen=set(); errors=[]; packed_files=0; individual_files=0
    if SRC.exists():
        for p in sorted(SRC.rglob('*.md')):
            packets,errs=extract_file(p); errors.extend(errs)
            if len(packets)>1: packed_files+=1
            else: individual_files+=1
            for meta,body,ordinal in packets:
                pid=meta['packet_id']
                if pid in seen:
                    errors.append(f'duplicate packet_id: {pid} ({p.relative_to(ROOT)}#{ordinal})')
                    continue
                seen.add(pid)
                rendered.append(render_packet(meta,body,p,ordinal))
    if errors:
        print('\n'.join(errors))
        return 2
    content='\n\n---\n\n'.join(rendered)
    (OUT/'micro_packets.md').write_text(content+'\n',encoding='utf-8')
    index={
      'schema_version':'1.1','packet_count':len(rendered),'individual_files':individual_files,
      'packed_shard_files':packed_files,
      'projection_path':'research_sources/derived/knowledge_micro_packets/micro_packets.md',
      'sha256':hashlib.sha256(content.encode()).hexdigest()
    }
    (OUT/'INDEX.json').write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(index,indent=2,ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
