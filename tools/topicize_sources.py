#!/usr/bin/env python3
"""Deterministically project all available source text into cross-domain topic files.

Consumes both direct text sources and text derivatives extracted from PDFs/ZIPs by
`ingest_source.py`. This is a retrieval classifier, not an epistemic judge.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEXT=ROOT/'research_sources'/'text'
DERIVED=ROOT/'research_sources'/'derived'
OUT=ROOT/'research_sources'/'topics'
TOPICS={
 'systems_architecture':['architecture','architektur','runtime','kernel','systemd','process','prozess','service','scheduler','ipc','linux','windows','macos','portable','portabil','android'],
 'frank_gwt':['frank','global workspace','gwt','thalamus','amygdala','nucleus accumbens','reentry','re-entry','workspace','regelkreis','e-pq','epq'],
 'synthetic_clay':['synthetic clay','claycode','clay graph','clay runtime','assembly','assemblies','hyperposition','activation'],
 'xeno_language':['xeno','machine language','maschinensprache','iesf','codec','wire','record','motif','hyperedge','aliencode','language forge'],
 'grf':['generative reality framework','grf','possibility space','realized state','counterfactual','generative predecessor','invariant'],
 'memory_state':['memory','gedächtnis','retrieval','rag','database','datenbank','sqlite','ledger','provenance','history','state','zustand'],
 'research_entity':['research entity','forscherentität','hypothesis','hypothese','experiment','pipeline','evidence','forschung','research'],
 'security_authority':['security','sicherheit','capability','authority','permission','sandbox','rollback','commit','witness','rights'],
 'emergence_consciousness':['emergence','emergenz','bewusstsein','consciousness','coupling','kopplung','omega','integration'],
 'performance_economics':['token','latency','latenz','cost','kosten','throughput','performance','effizienz','cache','battery','thermal'],
 'observability_recovery':['log','trace','telemetry','replay','recovery','crash','fault','receipt','audit','validator'],
 'model_runtime':['4b','qwen','llm','claude','opus','sonnet','lora','inference','needle','router','model','quantization','vulkan','npu'],
 'programming_runtime':['compiler','parser','validator','dsl','programmiersprache','directcode','binary','ast','code'],
 'persona_continuity':['persona','identity','identität','continuity','kontinuität','self model','world model','behavior memory','drift']
}
TEXT_EXTS={'.txt','.md','.json','.jsonl','.csv','.tsv','.py','.sh','.yaml','.yml','.toml','.ini','.cfg','.conf','.sql','.xml','.html','.js','.ts','.cc','.c','.h','.hpp','.rs','.go','.java','.ebnf','.log'}


def source_files():
    if TEXT.exists():
        for p in sorted(TEXT.rglob('*')):
            if p.is_file(): yield 'text',p
    if DERIVED.exists():
        for p in sorted(DERIVED.rglob('*')):
            if not p.is_file(): continue
            if p.name=='document.txt' or '/text/' in p.as_posix() or p.suffix.lower() in TEXT_EXTS:
                yield 'derived',p


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rec={k:[] for k in TOPICS}; seen_source_hashes=set()
    for root_kind,p in source_files():
        data=p.read_bytes(); sh=hashlib.sha256(data).hexdigest()
        if sh in seen_source_hashes: continue
        seen_source_hashes.add(sh)
        txt=data.decode('utf-8',errors='ignore')
        paras=[re.sub(r'\s+',' ',x).strip() for x in re.split(r'\n\s*\n+',txt) if len(re.sub(r'\s+',' ',x).strip())>=40]
        rel=p.relative_to(TEXT if root_kind=='text' else DERIVED).as_posix()
        for i,para in enumerate(paras,1):
            low=para.lower(); scores={k:sum(low.count(t) for t in terms) for k,terms in TOPICS.items()}; m=max(scores.values(),default=0)
            if not m: continue
            chosen=[k for k,v in scores.items() if v and v>=max(1,m*.45)]
            h=hashlib.sha256(para.encode()).hexdigest()[:16]; ref=f'{root_kind}:{rel}#p{i}'
            for k in chosen: rec[k].append((h,ref,para))
    idx={}
    for k,arr in rec.items():
        seen=set(); rows=[]
        for h,ref,para in arr:
            if h in seen: continue
            seen.add(h); rows.append(f'## {ref} [{h}]\n\n{para}\n')
        (OUT/f'{k}.md').write_text(f'# Topic Corpus: {k}\n\nRecords: {len(rows)}\n\n'+"\n".join(rows),encoding='utf-8')
        idx[k]={'records':len(rows),'path':f'research_sources/topics/{k}.md'}
    (OUT/'INDEX.json').write_text(json.dumps(idx,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(idx,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
