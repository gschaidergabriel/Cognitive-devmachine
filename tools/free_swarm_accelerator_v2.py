#!/usr/bin/env python3
"""Throughput accelerator for the Free Swarm.

Goals:
- remove slow 1->2->3 additive ramp on healthy providers;
- avoid provider-wide stalls on ordinary 5xx/model faults;
- exploit OpenRouter's explicitly free router without paid fallback;
- maximize Groq prompt-cache reuse by moving dynamic state behind a stable prefix;
- keep 429 economic/rate truth authoritative and never rotate keys to evade an org limit;
- coalesce one simultaneous 429 burst into one AIMD reduction instead of N repeated reductions.
"""
from __future__ import annotations
import asyncio, os, random, time
from typing import Any


def install(base:Any,opt:Any)->None:
    if not any(s.name=='openrouter' for s in base.PROVIDERS):
        base.PROVIDERS=tuple(base.PROVIDERS)+(
            base.ProviderSpec(
                name='openrouter',endpoint='https://openrouter.ai/api/v1/chat/completions',
                key_envs=('OPENROUTER_API_KEY',),keys_list_env='OPENROUTER_API_KEYS',
                models_env='OPENROUTER_SWARM_MODELS',default_models=('openrouter/free',),
                attestation_env='CLAY_OPENROUTER_FREE_ATTESTED',default_max_concurrency=8),
        )
    os.environ.setdefault('OPENROUTER_SWARM_MODELS','openrouter/free')
    opt.CATALOGS.setdefault('openrouter','https://openrouter.ai/api/v1/models')
    opt.PROVIDER_MODEL_CAP.setdefault('openrouter',1)

    OldRuntime=base.ProviderRuntime
    class FastRuntime(OldRuntime):
        def __init__(self,spec,keys,models,max_concurrency):
            super().__init__(spec,keys,models,max_concurrency)
            initial={'groq':2,'mistral':6,'nvidia':16,'openrouter':2}.get(spec.name,2)
            self.target_concurrency=min(self.max_concurrency,max(1,initial))
            self._healthy_windows=0
            self._429_epochs=0
            self._429_coalesced=0
        async def on_success(self)->None:
            async with self._condition:
                self.successes+=1;self.success_streak+=1
                self.rate_backoff=max(1.0,self.rate_backoff*0.75)
                threshold=max(4,self.target_concurrency//2)
                if self.success_streak>=threshold and self.target_concurrency<self.max_concurrency:
                    step=max(1,self.target_concurrency//3)
                    self.target_concurrency=min(self.max_concurrency,self.target_concurrency+step)
                    self.success_streak=0;self._healthy_windows+=1
                self._condition.notify_all()
        async def on_429(self,retry_after:float)->None:
            async with self._condition:
                self.rate_limits+=1;self.success_streak=0
                now=time.monotonic()
                # With tens/hundreds of requests in flight a provider can answer the
                # same overload/rate epoch with many concurrent 429s. Repeatedly
                # multiplying target by .6 for every member of that burst collapses
                # 96 -> 3 even though the evidence only says the 96 probe was too high.
                # The first 429 while not already cooling cuts once; the rest only
                # extend the same provider-wide cooldown. A later independent epoch
                # can cut again, so provider truth remains authoritative.
                new_epoch=now>=self.cooldown_until
                if new_epoch:
                    self.target_concurrency=max(1,int(self.target_concurrency*0.6))
                    self.rate_backoff=min(900.0,max(2.0,self.rate_backoff*1.7))
                    self._429_epochs+=1
                else:
                    self._429_coalesced+=1
                delay=max(float(retry_after),self.rate_backoff)+random.uniform(0.1,0.8)
                self.cooldown_until=max(self.cooldown_until,now+delay)
                self._condition.notify_all()
        async def on_transient_error(self)->None:
            async with self._condition:
                self.errors+=1;self.success_streak=0
                if self.errors%4==0:
                    self.target_concurrency=max(1,int(self.target_concurrency*0.85))
                self._condition.notify_all()
        def snapshot(self)->dict[str,Any]:
            out=super().snapshot();out['accelerator']='v2';out['healthy_ramp_windows']=self._healthy_windows
            out['rate_limit_epochs']=self._429_epochs;out['coalesced_429s']=self._429_coalesced
            return out
    base.ProviderRuntime=FastRuntime

    def cache_friendly_prompt(protocol:str,role:str,task:str,state_context:str,serial:int)->str:
        return f'''{protocol}

ENTITYOS/HCU FREE-SWARM STATIC PRODUCTIVITY CONTRACT
- Candidate/model output is never canonical authority.
- Produce ONE executable architecture delta, falsifier, patch/test/benchmark, or explicit NO_DELTA.
- Do not repeat supplied state except what is necessary to justify the delta.
- Preserve the strongest counterhypothesis and cheapest discriminator.
- `ready_for_forge=true` is a fail-closed contract: `target_files`, `patch_unified_diff`, and `test_commands` must all be non-empty and mutually consistent, and `falsifier` must be concrete.
- If an executable patch is not actually supplied, keep `ready_for_forge=false`; never label an empty patch as Forge-ready.
- For a Forge-ready candidate, `patch_unified_diff` must contain an actual applicable unified diff for the listed target files, not prose or a placeholder.
- For Forge-ready diffs, use exact `--- a/<path>` and `+++ b/<path>` headers (or `/dev/null` only for create/delete), real `@@ -old,count +new,count @@` hunks, and body lines beginning with space/+/-. Hunk counts must match the emitted lines.
- Encode patch newlines inside the one-line JSON value as `\\n` escapes. Never wrap the machine-readable JSON in Markdown fences and never use ellipses/pseudo-diff placeholders in a Forge-ready patch.
- End with DEUTSCHE_ZUSAMMENFASSUNG.
- Then emit exactly two compact machine-readable lines. The skeleton below is deliberately NOT Forge-ready; fill the executable fields first and only then switch `ready_for_forge` to true:
ARCHITECTURE_DELTA_JSON={{"delta_id":"worker-<serial>-short-name","hypothesis":"...","mechanism":"...","target_files":[],"patch_unified_diff":"","test_commands":[],"benchmark_command":"","metric":"...","expected_direction":"higher|lower|boolean","baseline_needed":true,"falsifier":"...","risk":"...","ready_for_forge":false}}
OPEN_RESEARCH_QUESTIONS_JSON=["causally distinct unresolved question"]

DYNAMIC WORK SHARD
worker_serial={serial}
worker_role={role}
role_task={task}

CURRENT RUNTIME / REPOSITORY / DISTILLED CONTEXT
{state_context}
'''
    base.worker_prompt=cache_friendly_prompt

    rebuilt=[]
    caps={'groq':12,'mistral':48,'nvidia':128,'openrouter':8}
    for s in base.PROVIDERS:
        cap=int(os.getenv(f'CLAY_{s.name.upper()}_MAX_CONCURRENCY',str(caps.get(s.name,s.default_max_concurrency))))
        rebuilt.append(base.ProviderSpec(s.name,s.endpoint,s.key_envs,s.keys_list_env,s.models_env,s.default_models,s.attestation_env,cap))
    base.PROVIDERS=tuple(rebuilt)
