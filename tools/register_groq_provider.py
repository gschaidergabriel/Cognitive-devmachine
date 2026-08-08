#!/usr/bin/env python3
"""Idempotently register Groq as the RAE small-model proxy provider."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'research_entity'/'global'/'EXTERNAL_RESEARCH_TOOL_REGISTRY.json'

CANONICAL_FALLBACK_RULE=(
    "If a preferred provider is unavailable, rate-limited, quota-exhausted or lacks credentials, "
    "record the reason and use the next suitable capability without silently weakening provenance. "
    "Current practical fallbacks: Semantic Scholar -> OpenAlex/arXiv/Crossref; E2B -> Judge0/local sandbox; "
    "Piston -> Judge0/local sandbox; Tavily/Exa -> DDGS/native web; Groq 8B small-model proxy -> true "
    "target/local 4B when available, otherwise Hugging Face/other model provider under normal quota policy."
)

def main():
    d=json.loads(P.read_text(encoding='utf-8'))
    tools=d.setdefault('tools',[])
    entry={
      'tool_name':'groq_inference',
      'provider':'Groq',
      'script':'tools/groq_inference.py',
      'class':'small_model_inference',
      'requires_secret':['GROQ_API_KEY'],
      'credential_required':True,
      'auth_transport':'Authorization: Bearer to api.groq.com/openai/v1',
      'default_model':'llama-3.1-8b-instant',
      'parameter_class':'8B',
      'evidence_role':'8b_proxy_for_4b',
      'proxy_policy':'research_entity/global/SMALL_MODEL_PROXY_POLICY.md',
      'preferred_for':['small-model semantic reader tests','ClayCode/XENO representation experiments','ClayGraph answer-quality proxy','GWT/FRANK matched-content model sensitivity','Hyperposition representation tests'],
      'not_equivalent_to':['Qwen3-4B target model','bare 4B evidence','local target-hardware latency/memory/energy','LoRA internalization'],
      'evidence_class':'external_model_runtime_proxy',
      'status':'RUNTIME_VERIFIED' if (ROOT/'research_entity'/'runtime'/'groq_verification.json').exists() else 'ADAPTER_READY_PENDING_RUNTIME_VERIFICATION',
      'verification_receipt':'research_entity/runtime/groq_verification.json',
      'worker_bridge_verified':True
    }
    # Replace every stale duplicate Groq entry with exactly one canonical entry.
    d['tools']=[x for x in tools if x.get('tool_name')!='groq_inference']+[entry]
    d['schema_version']='2.2'
    d['small_model_proxy_policy']='research_entity/global/SMALL_MODEL_PROXY_POLICY.md'
    # Assign, never append: repeated health/proxy runs must be byte-idempotent.
    d['fallback_rule']=CANONICAL_FALLBACK_RULE
    P.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'registered':'groq_inference','status':entry['status'],'idempotent':True}))

if __name__=='__main__': main()
