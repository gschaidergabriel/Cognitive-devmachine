#!/usr/bin/env python3
"""EntityOS/HCU driver for the FREE_ONLY adaptive GO swarm.

Optimization goals:
- spend tokens on executable deltas instead of restating stale governance text;
- feed workers live sandbox truth ahead of repository snapshots;
- prefer models that have actually succeeded and stop re-probing dead catalog entries;
- emit machine-readable research questions *and* architecture-delta candidates;
- keep the shared provider quota gate as the single cross-process concurrency view.
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import json
import os
from pathlib import Path
import re
import sqlite3
import urllib.error
import urllib.request

import run_free_go_swarm as base
from free_swarm_quota import slot as quota_slot, observe as quota_observe

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
DISTILLERY_DB = Path(os.getenv("CLAY_RESEARCH_DISTILLERY_DB", str(ARTIFACT_ROOT / "distillery/distillery.sqlite3")))
base.OWNER_DIRECTIVE_PATH = ROOT / "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md"
base.DEFAULT_ROLES = [
    ("ARCHITECT", "Produce ONE high-information EntityOS/HCU architecture delta, its strongest counterarchitecture and a cheap measurable discriminator. Do not spend output re-summarizing state."),
    ("FALSIFIER", "Choose ONE current assumption and design the cheapest executable falsifier. State what observation would kill the hypothesis."),
    ("CLAYCODE_FORGE", "Produce ONE minimal ClayCode-native implementation delta with target files, invariants, tests, negative tests and migration path."),
    ("HCU_CAUSAL", "Advance ONE missing edge in typed-entry -> loader -> model execution -> inference -> J-Space/training causal evidence. Prefer a runnable witness."),
    ("COGNITION", "Design ONE aggressive synthetic cognition intervention with matched control, measurable state variables and falsifiable prediction inside the authorized sandbox."),
    ("MEMORY_JSPACE", "Produce ONE measurable memory/J-Space provenance, replay, learning, model-switching or recovery delta and its failure test."),
    ("RUNTIME", "Find ONE compiler/VM/runtime/loader bottleneck and propose a benchmarkable repair with before/after metric."),
    ("EXTERNAL_HARVEST", "Name exact GitHub/arXiv/upstream candidates worth reproducing, the causal principle to isolate and a reproduction command/metric."),
    ("EXPERIMENT_DESIGN", "Turn ONE unresolved architecture claim into A/B + ablation + negative-control experiment with stopping rule and regression gate."),
    ("SECURITY", "Find ONE concrete truth/effect/capability boundary defect or mutation test. Avoid generic policy restatement."),
    ("REVIEWER", "Find ONE stale/duplicated/unmeasured claim that materially blocks progress and give the smallest executable correction."),
    ("SYNTHESIZER", "Fuse the strongest nonredundant evidence into ONE next executable delta while preserving the strongest disagreement."),
]

CATALOGS = {
    "groq": "https://api.groq.com/openai/v1/models",
    "mistral": "https://api.mistral.ai/v1/models",
    "nvidia": "https://integrate.api.nvidia.com/v1/models",
}
EXCLUDE = (
    "embedding", "embed-", "rerank", "whisper", "speech", "audio", "tts",
    "guard", "safety", "moderation", "classifier", "reward", "diffusion", "parse",
)
UNKNOWN_HIGH_VALUE = (
    "mistral-large", "mistral-medium", "mistral-small", "magistral", "codestral",
    "devstral", "nemotron", "deepseek", "reasoning", "instruct", "coder", "gpt-oss",
)
PROVIDER_MODEL_CAP = {"groq": 3, "mistral": 8, "nvidia": 16}

_ORIGINAL_REQUEST_CHAT = base.request_chat


def provider_bounded_request_chat(spec, key, model, prompt, max_tokens, timeout):
    if not base.provider_is_admitted_free(spec.name):
        return 412, {}, {"error": {"message": "typed FREE provider admission required", "type": "provider_admission"}}
    if spec.name == "groq":
        max_tokens = min(int(max_tokens), int(os.getenv("CLAY_GROQ_MAX_TOKENS", "900")))
    elif spec.name == "mistral":
        max_tokens = min(int(max_tokens), int(os.getenv("CLAY_MISTRAL_MAX_TOKENS", "1400")))
    elif spec.name == "nvidia":
        max_tokens = min(int(max_tokens), int(os.getenv("CLAY_NVIDIA_MAX_TOKENS", "1600")))
    owner = f"go-swarm:{model}"
    try:
        with quota_slot(spec.name, owner, timeout_s=min(float(timeout), 90.0), lease_s=max(240.0, float(timeout) + 45.0)):
            status, headers, payload = _ORIGINAL_REQUEST_CHAT(spec, key, model, prompt, max_tokens, timeout)
        quota_observe(spec.name, owner, status, headers)
        return status, headers, payload
    except TimeoutError:
        quota_observe(spec.name, owner, "GATE_TIMEOUT", {})
        return 503, {}, {"error": {"message": "shared provider gate timeout", "type": "local_quota_gate"}}


base.request_chat = provider_bounded_request_chat
_ORIGINAL_BUILD_STATE_CONTEXT = base.build_state_context
_ORIGINAL_WORKER_PROMPT = base.worker_prompt


def _read_json(path: Path, max_chars: int = 12000):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace")[:max_chars])
    except Exception:
        return None


def live_runtime_truth(max_chars: int) -> str:
    """Current artifact truth outranks stale repo narrative inside worker prompts."""
    current_status = None
    runs = sorted(ARTIFACT_ROOT.glob("active-*/status.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    if runs:
        current_status = _read_json(runs[0], 18000)
    payload = {
        "epistemic_rule": "CURRENT_RUNTIME_ARTIFACTS_OUTRANK_STALE_REPO_SNAPSHOTS_FOR_RUNTIME_FACTS",
        "supervisor": _read_json(ARTIFACT_ROOT / "SUPERVISOR.json", 10000),
        "current_swarm_status": current_status,
        "distillery_status": _read_json(ARTIFACT_ROOT / "distillery/STATUS.json", 12000),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:max_chars]


def distilled_context(max_chars: int) -> str:
    if not DISTILLERY_DB.exists() or max_chars <= 0:
        return '{"authority":"candidate_research_only","packets":[]}'
    try:
        con = sqlite3.connect(DISTILLERY_DB, timeout=2)
        rows = con.execute(
            "SELECT id,question_id,packet_text,intrinsic_score,grf_score,project_fit,novelty_score,created_at "
            "FROM knowledge_packets ORDER BY (intrinsic_score+grf_score+project_fit+novelty_score) DESC, created_at DESC LIMIT 16"
        ).fetchall()
        con.close()
    except Exception as exc:
        return json.dumps({"authority":"candidate_research_only","state":f"UNAVAILABLE:{type(exc).__name__}"})
    payload = [{"packet_id":r[0],"question_id":r[1],"packet":r[2],"intrinsic":r[3],"grf":r[4],"fit":r[5],"novelty":r[6],"created_at":r[7]} for r in rows]
    return json.dumps({"authority":"candidate_research_only","packets":payload},ensure_ascii=False,separators=(",",":"))[:max_chars]


def enriched_state_context(max_chars: int) -> str:
    # Previously workers spent large prompt budgets re-litigating stale supervisor text.
    # Give live truth first, then a smaller repo snapshot, then accepted candidate research.
    live_chars = max(3500, int(max_chars * 0.36))
    repo_chars = max(3500, int(max_chars * 0.42))
    dist_chars = max(1200, max_chars - live_chars - repo_chars)
    return (
        "CURRENT_RUNTIME_TRUTH\n" + live_runtime_truth(live_chars) +
        "\nREPOSITORY_CONTEXT_SECONDARY\n" + _ORIGINAL_BUILD_STATE_CONTEXT(repo_chars) +
        "\nDISTILLED_RESEARCH_DATASET\n" + distilled_context(dist_chars)
    )[:max_chars]


base.build_state_context = enriched_state_context


def optimized_worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    original = _ORIGINAL_WORKER_PROMPT(protocol, role, task, state_context, serial)
    return original + """

PRODUCTIVITY CONTRACT — MANDATORY
- Spend at most ~15% of the answer restating supplied state. Runtime facts in CURRENT_RUNTIME_TRUTH outrank stale repository prose.
- The useful unit is an executable discriminator, patch, test, benchmark or architecture delta — not another architecture essay.
- Do not claim a credential/provider is absent when CURRENT_RUNTIME_TRUTH shows it active.
- If you cannot produce a credible delta, say NO_DELTA and give the missing evidence instead of padding.
- Prefer minimal diffs and commands that can run in disposable worktrees/sandboxes.

After DEUTSCHE_ZUSAMMENFASSUNG emit BOTH machine-readable lines, with valid compact JSON and no Markdown fence:
ARCHITECTURE_DELTA_JSON={"delta_id":"worker-<serial>-short-name","hypothesis":"...","mechanism":"...","target_files":["..."],"patch_unified_diff":"optional unified diff or empty string","test_commands":["..."],"benchmark_command":"... or empty","metric":"...","expected_direction":"higher|lower|boolean","baseline_needed":true,"falsifier":"...","risk":"...","ready_for_forge":true}
OPEN_RESEARCH_QUESTIONS_JSON=["question 1","question 2","question 3"]
Set ready_for_forge=false when the proposal is not executable yet. Questions must be unresolved and causally distinct from accepted distilled packets.
"""


base.worker_prompt = optimized_worker_prompt


def fetch_catalog(provider: str, url: str, key: str, timeout: float) -> list[dict]:
    if not base.provider_is_admitted_free(provider):
        return []
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent":"clay-entityos-swarm/5.0"})
    owner=f"go-swarm:catalog:{provider}"
    try:
        with quota_slot(provider,owner,timeout_s=min(timeout,60.0),lease_s=120.0):
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="replace"))
                headers={k.lower():v for k,v in resp.headers.items()}
        quota_observe(provider,owner,200,headers)
    except urllib.error.HTTPError as exc:
        headers={k.lower():v for k,v in exc.headers.items()} if exc.headers else {}
        quota_observe(provider,owner,int(exc.code),headers)
        return []
    except Exception:
        quota_observe(provider,owner,"CATALOG_ERROR",{})
        return []
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    return [x if isinstance(x, dict) else {"id": str(x)} for x in rows]


def explicit_billions(model_id: str) -> float | None:
    vals=[]
    for raw in re.findall(r"(?i)(\d+(?:\.\d+)?)\s*b(?:\b|[-_])", model_id):
        try: vals.append(float(raw))
        except ValueError: pass
    return max(vals) if vals else None


def empirical_model_stats(provider: str) -> dict[str, tuple[int,int,int]]:
    stats: dict[str, list[int]] = collections.defaultdict(lambda:[0,0,0])
    for path in ARTIFACT_ROOT.glob("active-*/workers.jsonl"):
        try:
            lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:r=json.loads(line)
            except Exception:continue
            if r.get("provider") != provider: continue
            m=str(r.get("model") or "")
            if not m: continue
            stats[m][0]+=1
            s=r.get("http_status")
            if isinstance(s,int) and 200<=s<300: stats[m][1]+=1
            elif s!=429: stats[m][2]+=1
    return {m:tuple(v) for m,v in stats.items()}


def choose_models(provider: str, rows: list[dict]) -> list[str]:
    history=empirical_model_stats(provider)
    ranked=[]
    for card in rows:
        model_id=str(card.get("id") or card.get("model") or "").strip(); low=model_id.lower()
        if not model_id or any(x in low for x in EXCLUDE): continue
        capabilities=card.get("capabilities")
        if isinstance(capabilities,dict) and capabilities.get("completion_chat") is False: continue
        b=explicit_billions(model_id)
        if b is not None and b < 12.0: continue
        if b is None and not any(x in low for x in UNKNOWN_HIGH_VALUE): continue
        attempts,successes,errors=history.get(model_id,(0,0,0))
        # Stop burning requests on empirically dead routes until the catalog identity changes.
        if attempts >= 2 and successes == 0 and errors >= 2: continue
        ratio=successes/max(1,attempts)
        score=(b or 0.0)
        score += successes*35.0 + ratio*160.0 - errors*18.0
        if any(x in low for x in ("ultra","large","reasoning","deepseek","120b","405b","550b")): score+=80
        if any(x in low for x in ("nemotron","magistral","devstral","codestral","coder","instruct")): score+=45
        if model_id == "nvidia/llama-3.3-nemotron-super-49b-v1": score+=300
        ranked.append((score,successes,model_id))
    ranked.sort(key=lambda x:(-x[0],-x[1],x[2]))
    cap=PROVIDER_MODEL_CAP.get(provider,8)
    return base.unique([mid for _,_,mid in ranked])[:cap]


def discover_and_export(timeout: float) -> dict[str, dict]:
    report={}
    try: admission=base.load_provider_admission()
    except base.ProviderAdmissionError as exc:
        return {spec.name:{"source":"typed_admission_invalid","keys":0,"models":[],"status":str(exc)} for spec in base.PROVIDERS}
    if not base.truthy(os.getenv("CLAY_FREE_ONLY_ATTESTED")):
        return {spec.name:{"source":"global_compat_attestation_missing","keys":0,"models":[]} for spec in base.PROVIDERS}
    for spec in base.PROVIDERS:
        if not base.provider_is_admitted_free(spec.name,admission):
            report[spec.name]={"source":"typed_admission_blocked","keys":0,"models":[]}; continue
        if not base.truthy(os.getenv(spec.attestation_env)):
            report[spec.name]={"source":"provider_compat_attestation_missing","keys":0,"models":[]}; continue
        keys=base.collect_keys(spec,admission); override=base.split_values(os.getenv(spec.models_env))
        if override:
            report[spec.name]={"source":"environment_override","keys":len(keys),"models":override}; continue
        if not keys:
            report[spec.name]={"source":"no_keys_after_free_admission","keys":0,"models":[]}; continue
        rows=fetch_catalog(spec.name,CATALOGS[spec.name],keys[0],timeout); selected=choose_models(spec.name,rows)
        if selected:
            os.environ[spec.models_env]=",".join(selected)
            report[spec.name]={"source":"live_catalog_empirical_filter","keys":len(keys),"catalog":len(rows),"models":selected}
        else:
            report[spec.name]={"source":"controller_fallback","keys":len(keys),"catalog":len(rows),"models":list(spec.default_models)}
    return report


async def main(args: argparse.Namespace) -> int:
    report=discover_and_export(args.timeout)
    print(json.dumps({"schema":"CLAY_ENTITYOS_SWARM_DISCOVERY/v5","providers":report,"distillery_context":DISTILLERY_DB.exists(),"live_runtime_context":True,"shared_quota_gate":True,"typed_provider_admission":True},ensure_ascii=False),flush=True)
    if args.inventory_only:return 0
    out=args.output_dir or f"/artifacts/clay-entityos-swarm/{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    base_args=argparse.Namespace(hours=args.hours,max_tokens=args.max_tokens,context_chars=args.context_chars,timeout=args.timeout,drain_seconds=args.drain_seconds,output_dir=out)
    return await base.run(base_args)


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(description="Run the adaptive EntityOS/HCU research swarm")
    p.add_argument("--hours",type=float,default=24.0)
    p.add_argument("--max-tokens",type=int,default=1600)
    p.add_argument("--context-chars",type=int,default=15000)
    p.add_argument("--timeout",type=float,default=180.0)
    p.add_argument("--drain-seconds",type=float,default=240.0)
    p.add_argument("--output-dir",default="")
    p.add_argument("--inventory-only",action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(parse_args())))
