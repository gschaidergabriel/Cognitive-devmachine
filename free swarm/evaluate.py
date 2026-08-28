#!/usr/bin/env python3
"""Autonomous evaluator for the Clay FREE_ONLY research swarm.

Reads provider worker receipts and append-only architecture-delta adjudications,
computes concurrency/token/model/code-quality metrics, measures a clearly marked
repo-corpus token proxy, refreshes the AUTO section of free swarm/README.md, and
optionally publishes README/LIVE_METRICS.json back to main through the GitHub
Contents API when an authorized GH_TOKEN/GITHUB_TOKEN is already present.

No credential value is ever logged or persisted by this program.
"""
from __future__ import annotations

import argparse
import base64
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from forge_evidence_credit_871 import evidence_reason, nominal_accept  # noqa: E402

AUTO_BEGIN = "<!-- FREE_SWARM_AUTO:BEGIN -->"
AUTO_END = "<!-- FREE_SWARM_AUTO:END -->"
TEXT_EXTS = {".md", ".txt", ".json", ".jsonl", ".py", ".clay", ".toml", ".yaml", ".yml", ".sh", ".rs", ".c", ".h", ".cpp", ".hpp"}
SKIP_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv", "private", "secrets", "secret"}


def parse_ts(value: str) -> dt.datetime | None:
    try:
        x = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def iter_jsonl(paths: list[Path]):
    for path in paths:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for line_no, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    if isinstance(row, dict):
                        row.setdefault("_source", str(path))
                        row.setdefault("_line", line_no)
                        yield row
        except OSError:
            continue


def usage_triplet(usage: dict[str, Any]) -> tuple[int, int, int, bool]:
    if not isinstance(usage, dict):
        return 0, 0, 0, False
    inp = usage.get("input_tokens", usage.get("prompt_tokens"))
    out = usage.get("output_tokens", usage.get("completion_tokens"))
    total = usage.get("total_tokens")
    exact = isinstance(inp, (int, float)) or isinstance(out, (int, float)) or isinstance(total, (int, float))
    i = int(inp or 0) if isinstance(inp, (int, float)) else 0
    o = int(out or 0) if isinstance(out, (int, float)) else 0
    t = int(total) if isinstance(total, (int, float)) else i + o
    return i, o, t, exact


def worker_metrics(artifact_root: Path) -> dict[str, Any]:
    files = sorted(artifact_root.rglob("workers.jsonl")) if artifact_root.exists() else []
    rows = list(iter_jsonl(files))
    models: dict[tuple[str, str], dict[str, Any]] = {}
    intervals: list[tuple[dt.datetime, dt.datetime]] = []
    exact_usage_rows = 0
    sums = {"input": 0, "output": 0, "total": 0}

    for row in rows:
        provider = str(row.get("provider") or "unknown")
        model = str(row.get("model") or "unknown")
        k = (provider, model)
        m = models.setdefault(k, {"provider": provider, "model": model, "requests": 0, "success": 0, "rate_limits": 0, "errors": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
        m["requests"] += 1
        status = row.get("http_status")
        if isinstance(status, int) and 200 <= status < 300:
            m["success"] += 1
        elif status == 429:
            m["rate_limits"] += 1
        else:
            m["errors"] += 1
        i, o, t, exact = usage_triplet(row.get("usage") or {})
        if exact:
            exact_usage_rows += 1
        m["input_tokens"] += i; m["output_tokens"] += o; m["total_tokens"] += t
        sums["input"] += i; sums["output"] += o; sums["total"] += t
        end = parse_ts(str(row.get("ts") or ""))
        elapsed = row.get("elapsed_s")
        if end and isinstance(elapsed, (int, float)) and elapsed >= 0:
            intervals.append((end - dt.timedelta(seconds=float(elapsed)), end))

    avg = 0.0; peak = 0; observed_seconds = 0.0
    if intervals:
        lo = min(a for a, _ in intervals); hi = max(b for _, b in intervals)
        observed_seconds = max((hi - lo).total_seconds(), 1e-9)
        busy_seconds = sum(max(0.0, (b - a).total_seconds()) for a, b in intervals)
        avg = busy_seconds / observed_seconds
        events: list[tuple[dt.datetime, int]] = []
        for a, b in intervals:
            events.append((a, +1)); events.append((b, -1))
        events.sort(key=lambda x: (x[0], x[1]))
        cur = 0
        for _, delta in events:
            cur += delta; peak = max(peak, cur)

    return {
        "worker_records": len(rows), "worker_files": len(files),
        "average_concurrency": avg, "peak_concurrency": peak,
        "observed_seconds": observed_seconds, "exact_usage_rows": exact_usage_rows,
        "input_tokens": sums["input"], "output_tokens": sums["output"], "total_tokens": sums["total"],
        "models": sorted(models.values(), key=lambda x: (-x["success"], -x["output_tokens"], x["provider"], x["model"])),
    }


def accepted_delta(row: dict[str, Any]) -> bool:
    """Current evidence-qualified Forge acceptance; historical nominal rows stay separate."""
    ok, _ = evidence_reason(row)
    return ok


def code_quality(row: dict[str, Any]) -> float | None:
    def ratio(p: str, f: str) -> float | None:
        try: a, b = int(row.get(p, 0)), int(row.get(f, 0))
        except Exception: return None
        return a / (a + b) if a + b else None
    test = ratio("tests_passed", "tests_failed")
    neg = ratio("negative_tests_passed", "negative_tests_failed")
    static = ratio("static_checks_passed", "static_checks_failed")
    if test is None:
        return None
    bench = 1.0 if row.get("benchmark_non_regression") is True else 0.0
    stable = min(max(float(row.get("survived_go_cycles", 0)) / 2.0, 0.0), 1.0) if not row.get("reverted", False) else 0.0
    return 100.0 * (0.40 * test + 0.25 * bench + 0.15 * (neg or 0.0) + 0.10 * (static or 0.0) + 0.10 * stable)


def delta_metrics(ledger: Path) -> dict[str, Any]:
    rows = list(iter_jsonl([ledger])) if ledger.exists() else []
    nominal = [r for r in rows if nominal_accept(r)]
    accepted = [r for r in nominal if accepted_delta(r)]
    qualification_reasons = collections.Counter(evidence_reason(r)[1] for r in nominal)
    by_model: dict[tuple[str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    by_class: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for r in accepted:
        by_model[(str(r.get("provider") or "unknown"), str(r.get("model") or r.get("organ") or "unknown"))].append(r)
        by_class[str(r.get("source_class") or "unknown")].append(r)

    model_scores=[]
    for (provider, model), rs in by_model.items():
        imps=[float(r["relative_improvement_pct"]) for r in rs]
        cqs=[x for x in (code_quality(r) for r in rs) if x is not None]
        innovation=sum(max(0.0, float(r["relative_improvement_pct"])) for r in {str(r.get("delta_id") or id(r)): r for r in rs}.values())
        model_scores.append({"provider":provider,"model":model,"accepted_deltas":len(rs),"mean_improvement_pct":statistics.fmean(imps),"innovation_index":innovation,"code_quality":statistics.fmean(cqs) if cqs else None})
    best=sorted(model_scores,key=lambda x:(-x["accepted_deltas"],-x["mean_improvement_pct"],-(x["code_quality"] or -1),x["model"]))
    innovative=sorted(model_scores,key=lambda x:(-x["innovation_index"],-x["accepted_deltas"],x["model"]))

    class_scores={}
    for cls, rs in by_class.items():
        cqs=[x for x in (code_quality(r) for r in rs) if x is not None]
        imps=[float(r["relative_improvement_pct"]) for r in rs]
        class_scores[cls]={"accepted_deltas":len(rs),"code_quality":statistics.fmean(cqs) if cqs else None,"mean_improvement_pct":statistics.fmean(imps) if imps else None}
    return {
        "records":len(rows),
        "accepted":len(accepted),
        "nominal_accepted":len(nominal),
        "legacy_or_unqualified_accepted":len(nominal)-len(accepted),
        "qualification_reasons":dict(sorted(qualification_reasons.items())),
        "model_scores":model_scores,
        "best_model":best[0] if best else None,
        "innovation_leader":innovative[0] if innovative else None,
        "source_classes":class_scores,
    }


def corpus_proxy(repo: Path) -> dict[str, Any]:
    roots=[repo/"research_entity",repo/"the artefact",repo/"governance",repo/"tools",repo/"free swarm"]
    chars=0; files=0
    for root in roots:
        if not root.exists(): continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in TEXT_EXTS: continue
            rel=p.relative_to(repo)
            low={x.lower() for x in rel.parts}
            if low & SKIP_PARTS or p.name.endswith(".env"): continue
            try:
                s=p.read_text(encoding="utf-8",errors="replace")
            except OSError: continue
            chars += len(s); files += 1
    approx=round(chars/4.0)
    today=dt.datetime.now(dt.timezone.utc).date()
    intro_end=dt.date(2026,8,31)
    input_rate, output_rate=(2.0,10.0) if today <= intro_end else (3.0,15.0)
    return {"text_files":files,"characters":chars,"approx_tokens_4chars":approx,"sonnet5_input_usd_per_mtok":input_rate,"sonnet5_output_usd_per_mtok":output_rate,"output_only_equivalent_usd":approx*output_rate/1_000_000.0,"pricing_basis":"Claude Sonnet 5 introductory through 2026-08-31: $2/M input + $10/M output; standard after: $3/M + $15/M"}


def fmt(v: Any, digits=2) -> str:
    if v is None: return "UNKNOWN"
    if isinstance(v,float): return f"{v:.{digits}f}"
    return str(v)


def auto_markdown(metrics: dict[str, Any]) -> str:
    w=metrics["workers"]; d=metrics["deltas"]; c=metrics["corpus"]
    best=d.get("best_model"); innov=d.get("innovation_leader")
    lines=[AUTO_BEGIN,"## AUTO — Live-Auswertung",f"Aktualisiert: `{metrics['generated_at']}`",""]
    lines += ["| Kennzahl | Wert |","|---|---:|",f"| Worker-Records | {w['worker_records']} |",f"| Ø gleichzeitig laufende Free-Worker | {w['average_concurrency']:.3f} |",f"| Peak Free-Worker | {w['peak_concurrency']} |",f"| Free-Swarm Input-Tokens | {w['input_tokens']} |",f"| Free-Swarm Output-Tokens | {w['output_tokens']} |",f"| Free-Swarm Total-Tokens | {w['total_tokens']} |",f"| Usage-exakte Worker-Records | {w['exact_usage_rows']} |",f"| Evident akzeptierte Architektur-Deltas | {d['accepted']} |",f"| Nominal/historisch akzeptierte Architektur-Deltas | {d['nominal_accepted']} |",f"| Legacy/unqualifizierte nominale Accepts | {d['legacy_or_unqualified_accepted']} |",f"| Repo-Korpus-Proxy Tokens (4 Zeichen/Token) | {c['approx_tokens_4chars']} |",f"| Sonnet-5 Output-only Äquivalent des Repo-Proxys | ${c['output_only_equivalent_usd']:.2f} |",""]
    lines += ["### Modelle","| Provider | Modell | Requests | Success | 429 | Input | Output | Total |","|---|---|---:|---:|---:|---:|---:|---:|"]
    if w["models"]:
        for m in w["models"]:
            lines.append(f"| {m['provider']} | `{m['model']}` | {m['requests']} | {m['success']} | {m['rate_limits']} | {m['input_tokens']} | {m['output_tokens']} | {m['total_tokens']} |")
    else: lines.append("| — | NO PROVIDER OUTPUT YET | 0 | 0 | 0 | 0 | 0 | 0 |")
    lines += ["", "### Evidenz-Ranking"]
    lines.append("Bestes Modell: **NO EVIDENCE YET**" if not best else f"Bestes Modell: **{best['provider']} / {best['model']}** — {best['accepted_deltas']} akzeptierte Deltas, Ø Verbesserung {best['mean_improvement_pct']:.3f}%, CodeQuality {fmt(best['code_quality'])}/100.")
    lines.append("Innovativstes Modell: **NO EVIDENCE YET**" if not innov else f"Innovativstes Modell: **{innov['provider']} / {innov['model']}** — Innovation-Index {innov['innovation_index']:.3f} aus reproduzierbar positiven Architektur-Deltas.")
    lines += ["", "### Codequalität Free Swarm vs. GPT/ChatGPT", "| Organ-Klasse | akzeptierte Deltas | CodeQuality/100 | Ø Architekturverbesserung |", "|---|---:|---:|---:|"]
    for cls,label in [("free_swarm","Free Swarm"),("gpt_worker","GPT/ChatGPT")]:
        x=d["source_classes"].get(cls,{})
        lines.append(f"| {label} | {x.get('accepted_deltas',0)} | {fmt(x.get('code_quality'))} | {fmt(x.get('mean_improvement_pct'),3)}% |")
    lines += ["", "### Research-Entity-Output / Sonnet-Kostenproxy", f"API-exakte historische Gesamttokens aller früheren Organe bleiben **UNKNOWN**, solange keine vollständige historische Usage-Buchhaltung existiert. Der messbare persistente Repo-Korpus umfasst aktuell {c['text_files']} Textdateien / {c['characters']} Zeichen ≈ **{c['approx_tokens_4chars']} Tokens** bei der ausdrücklich nur als Proxy verwendeten 4-Zeichen-Näherung.", f"Hypothetische reine Output-Neuerzeugung dieses Proxy-Korpus mit Claude Sonnet 5: **${c['output_only_equivalent_usd']:.2f}** zum derzeit geltenden Output-Tarif von ${c['sonnet5_output_usd_per_mtok']:.0f}/M Tokens. Input-/Caching-/Toolkosten sind darin nicht enthalten.", AUTO_END]
    return "\n".join(lines)+"\n"


def update_readme(path: Path, block: str) -> bool:
    text=path.read_text(encoding="utf-8") if path.exists() else "# Free Swarm\n\n"
    if AUTO_BEGIN in text and AUTO_END in text:
        a=text.index(AUTO_BEGIN); b=text.index(AUTO_END,a)+len(AUTO_END)
        new=text[:a]+block.rstrip()+text[b:]
    else:
        insert=text.find("\n",text.find("#"))
        insert=len(text) if insert<0 else insert+1
        new=text[:insert]+"\n"+block+"\n"+text[insert:]
    if new==text: return False
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(new,encoding="utf-8"); return True


def github_put(repo_slug: str, branch: str, rel: str, content: bytes, token: str, message: str) -> str:
    api=f"https://api.github.com/repos/{repo_slug}/contents/{urllib.parse.quote(rel, safe='/')}?ref={urllib.parse.quote(branch)}"
    headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"clay-free-swarm-dashboard/1"}
    sha=None
    try:
        with urllib.request.urlopen(urllib.request.Request(api,headers=headers),timeout=30) as r:
            obj=json.loads(r.read()); sha=obj.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404: raise
    payload={"message":message,"content":base64.b64encode(content).decode(),"branch":branch}
    if sha: payload["sha"]=sha
    req=urllib.request.Request(api.split("?ref=",1)[0],data=json.dumps(payload).encode(),headers={**headers,"Content-Type":"application/json"},method="PUT")
    with urllib.request.urlopen(req,timeout=60) as r:
        obj=json.loads(r.read()); return str((obj.get("commit") or {}).get("sha") or "UNKNOWN")


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    repo=Path(args.repo).resolve(); artifact=Path(args.artifacts).resolve()
    metrics={"schema":"CLAY_FREE_SWARM_METRICS/v1","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"workers":worker_metrics(artifact),"deltas":delta_metrics(repo/"free swarm/architecture_delta_evaluations.jsonl"),"corpus":corpus_proxy(repo)}
    out=repo/"free swarm/LIVE_METRICS.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(metrics,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    update_readme(repo/"free swarm/README.md",auto_markdown(metrics))
    if args.publish:
        token=os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
        if token:
            stamp_dir=artifact/"dashboard"; stamp_dir.mkdir(parents=True,exist_ok=True); stamp=stamp_dir/"last_publish.json"
            digest=hashlib.sha256((repo/"free swarm/README.md").read_bytes()+out.read_bytes()).hexdigest()
            prev={}
            try: prev=json.loads(stamp.read_text())
            except Exception: pass
            due=(time.time()-float(prev.get("time",0))) >= args.publish_min_seconds
            if digest != prev.get("digest") and due:
                sha1=github_put(args.github_repo,args.branch,"free swarm/README.md",(repo/"free swarm/README.md").read_bytes(),token,"metrics: refresh Free Swarm dashboard")
                sha2=github_put(args.github_repo,args.branch,"free swarm/LIVE_METRICS.json",out.read_bytes(),token,"metrics: refresh Free Swarm live metrics")
                stamp.write_text(json.dumps({"time":time.time(),"digest":digest,"readme_commit":sha1,"metrics_commit":sha2})+"\n")
        else:
            metrics["publish_state"]="NO_GITHUB_TOKEN_IN_RUNTIME"
    return metrics


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--repo",default="/workspace"); p.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm"); p.add_argument("--watch",action="store_true"); p.add_argument("--interval-seconds",type=int,default=60); p.add_argument("--hours",type=float,default=24); p.add_argument("--publish",action="store_true"); p.add_argument("--publish-min-seconds",type=int,default=900); p.add_argument("--github-repo",default="gschaidergabriel/clay-global-research-entity"); p.add_argument("--branch",default="main"); args=p.parse_args()
    deadline=time.monotonic()+args.hours*3600
    while True:
        m=evaluate(args); print(json.dumps({"generated_at":m["generated_at"],"workers":m["workers"]["worker_records"],"output_tokens":m["workers"]["output_tokens"],"accepted_deltas":m["deltas"]["accepted"],"nominal_accepted_deltas":m["deltas"]["nominal_accepted"]}),flush=True)
        if not args.watch or time.monotonic()>=deadline: return 0
        time.sleep(max(5,args.interval_seconds))


if __name__=="__main__": raise SystemExit(main())