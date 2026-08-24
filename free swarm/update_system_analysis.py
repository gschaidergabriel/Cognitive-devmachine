#!/usr/bin/env python3
"""Maintain the detailed autonomous Free-Swarm/GO system analysis in README.

The compact live tables are useful but insufficient for system diagnosis. This
script adds a durable AUTO block covering every research script, GO trigger flow,
research frontier, pipeline conversion/yield, matched code-quality evidence and a
Claude Sonnet 5 cost-equivalent comparison.

Important: monetary values are counterfactual API cost equivalents. Historical
provider traffic is NOT relabelled FREE when current typed authority says its
cost class was UNKNOWN. Credential values are never read or written here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

BEGIN = "<!-- SYSTEM_ANALYSIS_AUTO:BEGIN -->"
END = "<!-- SYSTEM_ANALYSIS_AUTO:END -->"
ROLES_PER_MACROCYCLE = 12


def jload(path: Path) -> dict[str, Any]:
    try:
        x = json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except Exception:
        return {}


def iter_jsonl(paths: list[Path]):
    for p in paths:
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    x = json.loads(line)
                except Exception:
                    continue
                if isinstance(x, dict):
                    yield x
        except OSError:
            continue


def balanced_json(text: str, marker: str) -> dict[str, Any] | None:
    pos = text.find(marker)
    if pos < 0:
        return None
    start = text.find("{", pos + len(marker))
    if start < 0:
        return None
    depth = 0; in_string = False; esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_string:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': in_string = False
            continue
        if c == '"': in_string = True
        elif c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    x = json.loads(text[start:i+1])
                    return x if isinstance(x, dict) else None
                except Exception:
                    return None
    return None


def worker_conversion(artifacts: Path) -> dict[str, Any]:
    paths = sorted(artifacts.glob("active-*/workers.jsonl"))
    success = delta = ready = questions = 0
    cycles: dict[int, dict[str, int]] = {}
    for r in iter_jsonl(paths):
        st = r.get("http_status")
        if not (isinstance(st, int) and 200 <= st < 300):
            continue
        success += 1
        try: serial = int(r.get("worker_serial") or 0)
        except Exception: serial = 0
        cycle = ((serial - 1) // ROLES_PER_MACROCYCLE + 1) if serial > 0 else 0
        c = cycles.setdefault(cycle, {"success":0,"delta":0,"ready":0,"questions":0})
        c["success"] += 1
        text = str(r.get("text") or "")
        obj = balanced_json(text, "ARCHITECTURE_DELTA_JSON=")
        if obj is not None:
            delta += 1; c["delta"] += 1
            if obj.get("ready_for_forge") is True:
                ready += 1; c["ready"] += 1
        if "OPEN_RESEARCH_QUESTIONS_JSON=" in text:
            questions += 1; c["questions"] += 1
    usable_cycles = [v for k,v in cycles.items() if k > 0 and v["success"]]
    def avg_ratio(key: str) -> float | None:
        vals = [v[key]/v["success"] for v in usable_cycles]
        return (sum(vals)/len(vals)) if vals else None
    return {
        "successful_worker_outputs": success,
        "architecture_delta_outputs": delta,
        "ready_for_forge_outputs": ready,
        "research_question_outputs": questions,
        "macrocycles_observed": len(usable_cycles),
        "delta_emission_rate": delta/success if success else None,
        "ready_for_forge_rate": ready/success if success else None,
        "avg_delta_emission_per_macrocycle": avg_ratio("delta"),
        "avg_ready_for_forge_per_macrocycle": avg_ratio("ready"),
    }


def distillery_details(artifacts: Path, repo: Path) -> dict[str, Any]:
    status = jload(artifacts / "distillery/STATUS.json") or jload(repo / "free swarm/DISTILLERY_LIVE.json")
    db = artifacts / "distillery/distillery.sqlite3"
    top_questions: list[str] = []
    candidate_states: dict[str,int] = {}
    packet_count = int(status.get("accepted_packets") or 0)
    if db.exists():
        try:
            con = sqlite3.connect(db, timeout=2)
            try:
                top_questions = [str(r[0]) for r in con.execute(
                    "SELECT question FROM questions WHERE status IN ('OPEN','CYCLIC') ORDER BY priority DESC,COALESCE(last_touched,'') ASC LIMIT 10"
                ).fetchall()]
            except Exception: pass
            try:
                candidate_states = {str(a):int(b) for a,b in con.execute("SELECT status,COUNT(*) FROM candidates GROUP BY status").fetchall()}
            except Exception: pass
            try:
                packet_count = int(con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0])
            except Exception: pass
            con.close()
        except Exception:
            pass
    collected = int(status.get("collected_source_tokens") or 0)
    accepted = int(status.get("accepted_dataset_tokens") or 0)
    return {
        **status,
        "collected_source_tokens": collected,
        "accepted_dataset_tokens": accepted,
        "dataset_yield": accepted/collected if collected else 0.0,
        "accepted_packets": packet_count,
        "top_questions": top_questions,
        "candidate_states": candidate_states,
    }


def go_feedback(artifacts: Path, dist: dict[str, Any]) -> dict[str, Any]:
    """Measure accepted-research coverage injected into GO when receipts exist.

    go_feedback_context.jsonl is written by the optimized GO driver. Until it has
    observations, source->GO pass-through is still exactly zero when Distillery
    acceptance is zero; otherwise coverage remains UNKNOWN rather than invented.
    """
    rows = list(iter_jsonl([artifacts / "go_feedback_context.jsonl"]))
    by_cycle: dict[int, dict[str, Any]] = {}
    for r in rows:
        try: cycle = int(r.get("macrocycle_id") or 0)
        except Exception: continue
        if cycle <= 0: continue
        x = by_cycle.setdefault(cycle, {"available":0,"seen":set()})
        x["available"] = max(x["available"], int(r.get("available_packet_count") or 0))
        for pid in r.get("packet_ids") or []:
            x["seen"].add(str(pid))
    coverages=[]
    for x in by_cycle.values():
        if x["available"] > 0:
            coverages.append(min(1.0, len(x["seen"])/x["available"]))
    coverage = (sum(coverages)/len(coverages)) if coverages else None
    dyield = float(dist.get("dataset_yield") or 0.0)
    if dyield == 0.0:
        end_to_end = 0.0
    elif coverage is None:
        end_to_end = None
    else:
        end_to_end = dyield * coverage
    return {
        "feedback_receipts": len(rows),
        "macrocycles_with_coverage": len(coverages),
        "average_accepted_packet_reinjection_coverage": coverage,
        "source_to_go_pass_through": end_to_end,
        "definition": "Distillery dataset yield × average distinct accepted-packet coverage delivered to GO macrocycles",
    }


def sonnet_rates() -> tuple[float,float,str]:
    # Official Anthropic pricing observed 2026-08-24. Keep date switch explicit.
    if dt.datetime.now(dt.timezone.utc).date() <= dt.date(2026,8,31):
        return 2.0,10.0,"Claude Sonnet 5 introductory pricing through 2026-08-31: $2/M input + $10/M output"
    return 3.0,15.0,"Claude Sonnet 5 standard pricing: $3/M input + $15/M output"


def cost_equiv(inp: int, out: int, rin: float, rout: float) -> float:
    return inp*rin/1_000_000.0 + out*rout/1_000_000.0


def p(v: Any, digits: int = 3) -> str:
    if v is None: return "UNKNOWN"
    return f"{float(v)*100:.{digits}f}%"


def status_word(v: Any) -> str:
    if v is True:return "RUNNING"
    if v is False:return "STOPPED/QUARANTINED"
    return "UNKNOWN"


def build(repo: Path, artifacts: Path) -> tuple[dict[str, Any], str]:
    live = jload(repo / "free swarm/LIVE_METRICS.json")
    workers = live.get("workers") or {}
    deltas = live.get("deltas") or {}
    corpus = live.get("corpus") or {}
    dist = distillery_details(artifacts, repo)
    forge = jload(artifacts / "forge/STATUS.json")
    supervisor = jload(artifacts / "SUPERVISOR.json")
    conv = worker_conversion(artifacts)
    feedback = go_feedback(artifacts, dist)

    wi=int(workers.get("input_tokens") or 0); wo=int(workers.get("output_tokens") or 0); wt=int(workers.get("total_tokens") or wi+wo)
    di=int(dist.get("model_input_tokens") or 0); do=int(dist.get("model_output_tokens") or 0)
    rin,rout,price_basis=sonnet_rates()
    swarm_eq=cost_equiv(wi,wo,rin,rout); dist_eq=cost_equiv(di,do,rin,rout)
    measured_eq=swarm_eq+dist_eq
    observed=float(workers.get("observed_seconds") or 0.0)

    admission=supervisor.get("provider_admission") or {}
    admitted=list(admission.get("admitted_free_providers") or [])
    authority_ok=bool(admission.get("ok"))
    historical_saving_verified = False  # current authority explicitly forbids post-hoc FREE relabelling

    source_classes=deltas.get("source_classes") or {}
    freeq=source_classes.get("free_swarm") or {}; gptq=source_classes.get("gpt_worker") or {}; sonnetq=source_classes.get("sonnet_worker") or {}

    research_tracks = [
        "EntityOS/HCU executable architecture and causal receipts",
        "typed entry → verified loader consumption → actual model execution → inference/J-Space/training provenance",
        "ClayCode compiler/VM/runtime and minimal native deltas",
        "Global J-Space/GWT, memory, replay, online learning and model switching",
        "synthetic cognition interventions, pressure/deception/ablation with matched controls",
        "runtime bottlenecks, benchmarks, negative paths and recovery semantics",
        "external GitHub/arXiv/web mechanism harvesting and reproduction",
        "truth/effect/capability boundaries and falsification",
    ]

    system={
        "schema":"CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v2",
        "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "price_basis":price_basis,
        "go_trigger_pipeline":[
            "VPS sandbox/bridge health + storage preflight; repair/improve first if degraded",
            "refresh current main/supervisor/authority and preserve UNKNOWN/noncanonical boundaries",
            "coordinate GO research roles and emit executable ARCHITECTURE_DELTA_JSON + OPEN_RESEARCH_QUESTIONS_JSON",
            "Distillery expands unresolved questions using external/public evidence and compresses only accepted knowledge",
            "Evidence Forge searches implementations, patches disposable clones, runs tests/benchmarks and writes delta evidence",
            "local/public zero-provider-billing research lanes continue even when external LLM providers are quarantined",
            "accepted knowledge is reinjected into subsequent GO prompts; measured deltas enter the common evaluation ledger",
            "dashboard recomputes concurrency, tokens, yield, quality, progress, Sonnet cost-equivalent and GO pass-through",
        ],
        "research_tracks":research_tracks,
        "runtime":{
            "supervisor_schema":supervisor.get("schema"),
            "go_swarm":status_word(supervisor.get("go_swarm_running")),
            "distillery":status_word(supervisor.get("distillery_running")),
            "evidence_forge":status_word(supervisor.get("forge_running")),
            "dashboard":status_word(supervisor.get("dashboard_running")),
            "typed_provider_admission_ok":authority_ok,
            "admitted_free_providers":admitted,
            "policy":supervisor.get("policy"),
        },
        "free_swarm":{
            "worker_records":int(workers.get("worker_records") or 0),
            "average_concurrency":float(workers.get("average_concurrency") or 0.0),
            "peak_concurrency":int(workers.get("peak_concurrency") or 0),
            "input_tokens":wi,"output_tokens":wo,"total_tokens":wt,
            "aggregate_output_tokens_per_second":wo/observed if observed else None,
            "conversion":conv,
            "sonnet5_same_token_mix_equivalent_usd":swarm_eq,
        },
        "distillery":dist,
        "go_feedback":feedback,
        "evidence_forge":forge,
        "quality":{
            "free_swarm":freeq,"gpt_chatgpt":gptq,"sonnet":sonnetq,
            "matched_evaluation_rule":"Only common architecture_delta_evaluations records count; prose impressions do not.",
        },
        "costs":{
            "free_swarm_sonnet5_equivalent_usd":swarm_eq,
            "distillery_model_sonnet5_equivalent_usd":dist_eq,
            "measured_llm_token_mix_sonnet5_equivalent_usd":measured_eq,
            "repo_corpus_output_only_sonnet5_equivalent_usd":corpus.get("output_only_equivalent_usd"),
            "verified_historical_savings_usd":None,
            "nominal_avoided_cost_if_measured_calls_were_zero_cost_usd":measured_eq,
            "saving_caveat":"Current typed authority classifies historical external provider traffic as unadmitted/UNKNOWN cost class; nominal avoided cost must not be called verified savings until billing/free evidence exists.",
        },
    }

    forge_state=forge.get("state") or system["runtime"]["evidence_forge"]
    forge_disc=int(forge.get("discoveries") or forge.get("discoveries_written") or 0)
    forge_eval=int(forge.get("evaluations") or forge.get("evaluations_written") or forge.get("evaluated_candidates") or 0)
    forge_acc=int(forge.get("accepted_deltas") or forge.get("verified_deltas") or 0)
    q=dist.get("questions") or {}

    lines=[BEGIN,"## AUTO — Gesamtsystem, GO-Fluss, Script-Auswertung und Sonnet-Vergleich",f"Aktualisiert: `{system['generated_at']}`","",
        "### Wichtigster Effizienzindikator: Was kommt wieder bei GO an?",
        f"**Source → GO Pass-through:** **{p(feedback['source_to_go_pass_through'])}**. Definition: `{feedback['definition']}`.",
        f"Distillery-Yield: **{p(dist.get('dataset_yield'))}** ({int(dist.get('accepted_dataset_tokens') or 0):,} akzeptierte Dataset-Tokens aus {int(dist.get('collected_source_tokens') or 0):,} Quelltokens).",
        f"Ø Reinjection-Coverage akzeptierter Pakete pro gemessenem GO-Makrozyklus: **{p(feedback['average_accepted_packet_reinjection_coverage'])}** ({feedback['macrocycles_with_coverage']} Zyklen mit Coverage-Receipt).",
        f"GO-Worker → Architektur-Delta: **{p(conv.get('delta_emission_rate'))}**; ready-for-forge: **{p(conv.get('ready_for_forge_rate'))}**. Über beobachtete Makrozyklen: Ø Deltaquote **{p(conv.get('avg_delta_emission_per_macrocycle'))}**, Ø forge-ready **{p(conv.get('avg_ready_for_forge_per_macrocycle'))}**.",
        "Wenn noch keine akzeptierten Knowledge-Pakete existieren, ist Source→GO exakt 0%; eine fehlende Reinjection-Coverage wird separat als UNKNOWN gezeigt und nicht erfunden.","",
        "### Was `go` auslöst","1. **Preflight:** VPS-Sandbox/Bridge, Speicher und Runtime prüfen; bei Defekt zuerst reparieren/verbessern.","2. **Authority/State:** aktuellen `main`-/Supervisor-Stand lesen; Modelloutput bleibt Kandidat, nicht automatisch kanonisch.","3. **GO Swarm:** spezialisierte Rollen erzeugen Falsifier, Patches, Tests, Benchmarks, Architektur-Deltas und offene Forschungsfragen.","4. **Research Distillery:** offene Fragen zerlegen, externe Mechanismen sammeln, bewerten, komprimieren und nur akzeptiertes Wissen behalten.","5. **Evidence Forge:** konkrete Deltas/Repos in Disposable-Clones/Sandboxes reproduzieren, testen, benchmarken und falsifizieren.","6. **Feedback:** akzeptierte Knowledge-Pakete in spätere GO-Prompts einspeisen; verifizierte Deltas in gemeinsames Ledger geben.","7. **Messung:** README/LIVE-Metriken mit Tokens, Parallelität, Yield, Qualitätsvergleich, Kosten und Fortschritt aktualisieren.","",
        "### Script-by-Script — aktueller Zustand","| Subsystem | Aufgabe | Runtime | aktuell messbarer Fortschritt |","|---|---|---|---|",
        f"| **GO Free Swarm** `run_24h_entityos_swarm.py` + `run_free_go_swarm.py` | parallele Architektur-/Code-/Falsifikationsarbeiter | {system['runtime']['go_swarm']} | {workers.get('worker_records',0)} Records; Ø {float(workers.get('average_concurrency') or 0):.2f}, Peak {workers.get('peak_concurrency',0)}; {wt:,} Tokens; {conv['architecture_delta_outputs']} maschinenlesbare Deltas, {conv['ready_for_forge_outputs']} forge-ready |",
        f"| **Research Distillery** `run_research_distillery_entry.py` | Quellen/Chunks → konsistente GRF-kompatible Knowledge-Pakete | {system['runtime']['distillery']} | {int(dist.get('collected_source_tokens') or 0):,} Quelltokens → {int(dist.get('accepted_dataset_tokens') or 0):,} Dataset-Tokens; Yield {p(dist.get('dataset_yield'))}; Pakete {dist.get('accepted_packets',0)}; Fragen OPEN {q.get('OPEN',0)}, CYCLIC {q.get('CYCLIC',0)} |",
        f"| **Evidence Forge** `run_free_evidence_forge.py` | Proposal → Repro/Patch/Test/Benchmark → Delta-Evidenz | {forge_state} | Discoveries {forge_disc}; Evaluations {forge_eval}; akzeptierte/verifizierte Deltas {forge_acc} |",
        "| **Local research model lane** `local_research_model_server.sh` | dauerhafte lokale kleine Modelle für Suche/Vorfilter/Synthese ohne Provider-API | artifact-dependent | wird nur als aktiv gewertet, wenn eigener Runtime-Receipt/Status vorliegt; keine Aktivität wird aus Dateiexistenz erfunden |",
        f"| **Shared quota gate** `free_swarm_quota.py` | providerübergreifende Concurrency/Cooldown-/429-Koordination | embedded | verhindert parallele Scripts gegeneinander Rate-Limits zu verbrennen; Providerstatus zusätzlich in Distillery/Supervisor |",
        f"| **Dashboard/Evaluator** `free swarm/evaluate.py` | Tokens, Modelle, Deltas, Qualität, Kosten und diese Analyse | {system['runtime']['dashboard']} | autonomer README-Refresh; gemeinsames Delta-Scoring |","",
        "### Woran aktuell geforscht wird"]
    for x in research_tracks: lines.append(f"- {x}")
    if dist.get("top_questions"):
        lines += ["","**Aktuelle hoch priorisierte offene Fragen aus der Distillery:**"]
        for x in dist["top_questions"][:10]: lines.append(f"- {x}")

    lines += ["","### Fortschritt als Funnel","| Stufe | Wert | Interpretation |","|---|---:|---|",
        f"| erfolgreiche GO-Workeroutputs | {conv['successful_worker_outputs']} | Rohkandidaten aus Modellarbeit |",
        f"| maschinenlesbare Architektur-Deltas | {conv['architecture_delta_outputs']} ({p(conv.get('delta_emission_rate'))}) | in automatisierbare Form konvertiert |",
        f"| forge-ready Deltas | {conv['ready_for_forge_outputs']} ({p(conv.get('ready_for_forge_rate'))}) | ausreichend konkret für Reproduktion/Test |",
        f"| Distillery Quelltokens | {int(dist.get('collected_source_tokens') or 0):,} | kumulierte externe Forschungsrohmasse |",
        f"| akzeptierte Dataset-Tokens | {int(dist.get('accepted_dataset_tokens') or 0):,} ({p(dist.get('dataset_yield'))}) | komprimiertes Wissen, das überhaupt zurückfließen darf |",
        f"| Evidence-Forge akzeptiert/verifiziert | {forge_acc} | empirisch überlebende Deltas |",
        f"| gemeinsames Delta-Ledger akzeptiert | {int(deltas.get('accepted') or 0)} | Grundlage für Modell-/Codequalitätsranking |","",
        "### Free Swarm vs. GPT/ChatGPT vs. Claude Sonnet — Qualität","| Organ | akzeptierte Deltas | CodeQuality/100 | Ø gemessene Architekturverbesserung | Aussage |","|---|---:|---:|---:|---|",
        f"| Free Swarm | {freeq.get('accepted_deltas',0)} | {freeq.get('code_quality','UNKNOWN')} | {freeq.get('mean_improvement_pct','UNKNOWN')} | nur gemeinsames Ledger |",
        f"| GPT/ChatGPT | {gptq.get('accepted_deltas',0)} | {gptq.get('code_quality','UNKNOWN')} | {gptq.get('mean_improvement_pct','UNKNOWN')} | nur gemeinsames Ledger |",
        f"| Claude Sonnet | {sonnetq.get('accepted_deltas',0)} | {sonnetq.get('code_quality','UNKNOWN')} | {sonnetq.get('mean_improvement_pct','UNKNOWN')} | **kein Qualitätsurteil ohne matched Sonnet-Receipts** |","",
        "Der frühere qualitative Eindruck (`Free-Modelle brauchen mehr Filter/Fusion`) bleibt eine Hypothese. Das Dashboard erklärt erst dann einen Sieger, wenn Free/GPT/Sonnet unter demselben Patch/Test/Benchmark-Schema gemessen wurden.","",
        "### Claude-Sonnet-5 Kostenäquivalent / nominal vermiedene Kosten",f"Preisannahme: **{price_basis}**.","| Vergleich | Tokenbasis | Sonnet-5 API-Äquivalent |","|---|---:|---:|",
        f"| Free-Swarm gemessener Tokenmix | {wi:,} input + {wo:,} output | **${swarm_eq:.2f}** |",
        f"| Distillery Modellarbeit | {di:,} input + {do:,} output | **${dist_eq:.4f}** |",
        f"| zusammen, API-exakt soweit Usage vorhanden | — | **${measured_eq:.2f}** |",
        f"| persistenter Repo-Korpus, Output-only Proxy | {int(corpus.get('approx_tokens_4chars') or 0):,} Proxy-Tokens | **${float(corpus.get('output_only_equivalent_usd') or 0):.2f}** |","",
        f"**Nominal vermiedene Sonnet-Kosten, falls die gemessenen externen Calls tatsächlich $0 kosteten:** **${measured_eq:.2f}**. **Verifiziert gesparte Kosten: UNKNOWN**, weil die aktuelle typed Authority historische Provider-Ausführung ausdrücklich nicht nachträglich als FREE klassifizieren darf. Der Repo-Korpus-Wert ist zusätzlich nur ein Neu-Erzeugungsproxy, keine Rechnung.","",
        "### Kapazität relativ zu 15 parallelen Sonnet-Workern",f"Gemessene mittlere Free-Worker-Parallelität: **{float(workers.get('average_concurrency') or 0):.2f}/15 = {float(workers.get('average_concurrency') or 0)/15*100:.1f}%** der reinen Slotzahl; Peak **{int(workers.get('peak_concurrency') or 0)}/15 = {int(workers.get('peak_concurrency') or 0)/15*100:.1f}%**. Das ist **kein Qualitätsvergleich**. Gemessener aggregierter Free-Swarm Outputdurchsatz im Beobachtungsfenster: **{(wo/observed if observed else 0):.2f} Output-Tokens/s**; für Sonnet fehlt ein matched Durchsatzlauf.","",
        "### Autonome Update-Regel","Dieser Block wird aus Runtime-Artefakten neu erzeugt. Neue Scripts dürfen nicht einfach die ausführliche Analyse überschreiben: kompakte Live-Tabellen, Distillery, Evidence Forge, GO-Funnel, matched Qualitätsvergleich, Sonnet-Kosten und Source→GO-Pass-through bleiben Pflichtfelder.",END]
    return system, "\n".join(lines)+"\n"


def replace(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# Free Swarm\n"
    if BEGIN in text and END in text:
        a=text.index(BEGIN); b=text.index(END,a)+len(END)
        text=text[:a]+block.rstrip()+text[b:]
    else:
        # Keep this detailed block near the top, after any Distillery block if present.
        marker="<!-- RESEARCH_DISTILLERY_AUTO:END -->"
        if marker in text:
            i=text.index(marker)+len(marker)
            text=text[:i]+"\n\n"+block.rstrip()+text[i:]
        else:
            nl=text.find("\n")
            i=len(text) if nl<0 else nl+1
            text=text[:i]+"\n"+block+"\n"+text[i:]
    path.write_text(text.rstrip()+"\n",encoding="utf-8")


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",default="/workspace/clay-global-research-entity"); ap.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm"); args=ap.parse_args()
    repo=Path(args.repo).resolve(); artifacts=Path(args.artifacts).resolve()
    system,block=build(repo,artifacts)
    replace(repo/"free swarm/README.md",block)
    (repo/"free swarm/SYSTEM_ANALYSIS_LIVE.json").write_text(json.dumps(system,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"generated_at":system["generated_at"],"source_to_go":system["go_feedback"]["source_to_go_pass_through"],"sonnet_equivalent_usd":system["costs"]["measured_llm_token_mix_sonnet5_equivalent_usd"]}))
    return 0

if __name__=="__main__": raise SystemExit(main())
