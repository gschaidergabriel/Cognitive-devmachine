#!/usr/bin/env python3
"""Autonomous detailed Free-Swarm / GO / Sonnet analysis for free swarm/README.md.

This block is intentionally independent from the compact model table. It answers:
what every script does, what `go` triggers, what is being researched, how far the
pipeline has progressed, what fraction reaches later GO cycles, and what the same
measured token mix would cost on Claude Sonnet 5.

Historical provider traffic is never post-hoc relabelled FREE. Cost savings remain
counterfactual until billing/free evidence proves them. No secret values are read.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, sqlite3
from pathlib import Path
from typing import Any

BEGIN="<!-- SYSTEM_ANALYSIS_AUTO:BEGIN -->"; END="<!-- SYSTEM_ANALYSIS_AUTO:END -->"; ROLES=12


def jl(p:Path)->dict[str,Any]:
    try:
        x=json.loads(p.read_text(encoding="utf-8")); return x if isinstance(x,dict) else {}
    except Exception:return {}


def jsonl(paths):
    for p in paths:
        try:
            for line in p.read_text(encoding="utf-8",errors="replace").splitlines():
                try:x=json.loads(line)
                except Exception:continue
                if isinstance(x,dict):yield x
        except OSError:pass


def proc_has(*needles:str)->bool:
    """Best-effort live process truth; works in sandbox and usually from rootless host."""
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:s=p.read_bytes().replace(b'\0',b' ').decode(errors='replace')
        except Exception:continue
        if any(n in s for n in needles):return True
    return False


def balanced(text:str,marker:str)->dict|None:
    k=text.find(marker)
    if k<0:return None
    a=text.find('{',k+len(marker))
    if a<0:return None
    depth=0; ins=False; esc=False
    for i,c in enumerate(text[a:],a):
        if ins:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c=='"':ins=False
            continue
        if c=='"':ins=True
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                try:
                    x=json.loads(text[a:i+1]); return x if isinstance(x,dict) else None
                except Exception:return None
    return None


def conversion(art:Path)->dict[str,Any]:
    success=delta=ready=questions=0; cycles={}
    for r in jsonl(sorted(art.glob('active-*/workers.jsonl'))):
        st=r.get('http_status')
        if not(isinstance(st,int) and 200<=st<300):continue
        success+=1
        try:s=int(r.get('worker_serial') or 0)
        except Exception:s=0
        cid=(s-1)//ROLES+1 if s>0 else 0
        c=cycles.setdefault(cid,{'success':0,'delta':0,'ready':0,'questions':0}); c['success']+=1
        text=str(r.get('text') or '')
        d=balanced(text,'ARCHITECTURE_DELTA_JSON=')
        if d is not None:
            delta+=1;c['delta']+=1
            if d.get('ready_for_forge') is True:ready+=1;c['ready']+=1
        if 'OPEN_RESEARCH_QUESTIONS_JSON=' in text:questions+=1;c['questions']+=1
    usable=[v for k,v in cycles.items() if k>0 and v['success']]
    def ar(key):
        z=[v[key]/v['success'] for v in usable];return sum(z)/len(z) if z else None
    return {'successful':success,'delta':delta,'ready':ready,'questions':questions,'macrocycles':len(usable),
            'delta_rate':delta/success if success else None,'ready_rate':ready/success if success else None,
            'question_rate':questions/success if success else None,'avg_cycle_delta_rate':ar('delta'),'avg_cycle_ready_rate':ar('ready')}


def distillery(art:Path,repo:Path)->dict[str,Any]:
    s=jl(art/'distillery/STATUS.json') or jl(repo/'free swarm/DISTILLERY_LIVE.json'); db=art/'distillery/distillery.sqlite3'
    top=[]; states={}; packets=int(s.get('accepted_packets') or 0)
    if db.exists():
        try:
            con=sqlite3.connect(db,timeout=2)
            try:top=[str(x[0]) for x in con.execute("SELECT question FROM questions WHERE status IN ('OPEN','CYCLIC') ORDER BY priority DESC,COALESCE(last_touched,'') ASC LIMIT 10")]
            except Exception:pass
            try:states={str(a):int(b) for a,b in con.execute('SELECT status,COUNT(*) FROM candidates GROUP BY status')}
            except Exception:pass
            try:packets=int(con.execute('SELECT COUNT(*) FROM knowledge_packets').fetchone()[0])
            except Exception:pass
            con.close()
        except Exception:pass
    src=int(s.get('collected_source_tokens') or 0); acc=int(s.get('accepted_dataset_tokens') or 0)
    return {**s,'collected_source_tokens':src,'accepted_dataset_tokens':acc,'dataset_yield':acc/src if src else 0.0,
            'accepted_packets':packets,'top_questions':top,'candidate_states':states}


def feedback(art:Path,d:dict[str,Any])->dict[str,Any]:
    rows=list(jsonl([art/'go_feedback_context.jsonl'])); cycles={}
    for r in rows:
        try:c=int(r.get('macrocycle_id') or 0)
        except Exception:continue
        if c<=0:continue
        x=cycles.setdefault(c,{'available':0,'seen':set()});x['available']=max(x['available'],int(r.get('available_packet_count') or 0))
        x['seen'].update(str(v) for v in (r.get('packet_ids') or []))
    cov=[min(1.0,len(x['seen'])/x['available']) for x in cycles.values() if x['available']>0]
    coverage=sum(cov)/len(cov) if cov else None; y=float(d.get('dataset_yield') or 0.0)
    end=0.0 if y==0 else (None if coverage is None else y*coverage)
    return {'receipts':len(rows),'cycles':len(cov),'coverage':coverage,'source_to_go':end,
            'definition':'accepted dataset-token yield × average distinct accepted-packet coverage delivered to GO macrocycles'}


def rates():
    if dt.datetime.now(dt.timezone.utc).date()<=dt.date(2026,8,31):return 2.0,10.0,'Claude Sonnet 5 introductory through 2026-08-31: $2/M input + $10/M output'
    return 3.0,15.0,'Claude Sonnet 5 standard: $3/M input + $15/M output'


def pc(v):return 'UNKNOWN' if v is None else f'{100*float(v):.3f}%'
def cq(x):return 'UNKNOWN' if x is None else f'{float(x):.2f}'
def cost(i,o,ri,ro):return i*ri/1e6+o*ro/1e6


def build(repo:Path,art:Path):
    live=jl(repo/'free swarm/LIVE_METRICS.json'); w=live.get('workers') or {}; ds=live.get('deltas') or {}; corp=live.get('corpus') or {}
    d=distillery(art,repo); f=jl(art/'forge/STATUS.json'); sup=jl(art/'SUPERVISOR.json'); c=conversion(art); fb=feedback(art,d)
    go_run=proc_has('run_24h_entityos_swarm.py') or bool(sup.get('go_swarm_running'))
    dist_run=proc_has('run_research_distillery_local.py','run_research_distillery_entry.py') or bool(sup.get('distillery_running'))
    forge_run=proc_has('run_free_evidence_forge.py') or bool(sup.get('forge_running'))
    dash_run=proc_has('free swarm/evaluate.py') or bool(sup.get('dashboard_running'))
    sup_run=proc_has('run_24h_entityos_swarm_supervisor.sh')
    local_ready=bool(sup.get('local_research_model_ready'))
    local_build=proc_has('local_research_model_server.sh','cmake --build')
    local_state='READY' if local_ready else ('BUILDING/BOOTSTRAPPING' if local_build else 'NOT_READY')
    def rs(x):return 'RUNNING' if x else 'STOPPED/QUARANTINED'
    wi=int(w.get('input_tokens') or 0);wo=int(w.get('output_tokens') or 0);wt=int(w.get('total_tokens') or wi+wo)
    di=int(d.get('model_input_tokens') or 0);do=int(d.get('model_output_tokens') or 0);ri,ro,pbasis=rates(); swcost=cost(wi,wo,ri,ro);dcost=cost(di,do,ri,ro)
    classes=ds.get('source_classes') or {};fq=classes.get('free_swarm') or {};gq=classes.get('gpt_worker') or {};sq=classes.get('sonnet_worker') or {}
    forge_hits=int(f.get('discovery_hits') or f.get('discoveries') or f.get('discoveries_written') or 0);forge_q=int(f.get('discovery_queries') or 0);forge_eval=int(f.get('evaluations') or f.get('evaluations_written') or 0);forge_acc=int(f.get('accepted_deltas') or f.get('verified_deltas') or 0)
    observed=float(w.get('observed_seconds') or 0);q=d.get('questions') or {}
    budget=((f.get('shared_provider_budget') or {}).get('providers') or (d.get('shared_provider_budget') or {}).get('providers') or {})
    tracks=['EntityOS/HCU executable architecture and causal receipts','typed entry → loader consumption → actual model execution → inference/J-Space/training provenance','ClayCode compiler/VM/runtime and minimal native deltas','Global J-Space/GWT, memory, replay, online learning and model switching','synthetic cognition interventions with matched controls','runtime bottlenecks, benchmarks, negative paths and recovery semantics','external GitHub/arXiv/web mechanism harvesting and reproduction','truth/effect/capability boundaries and falsification']
    obj={'schema':'CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v3','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
         'runtime':{'supervisor':rs(sup_run),'go_swarm':rs(go_run),'distillery':rs(dist_run),'evidence_forge':rs(forge_run),'dashboard':rs(dash_run),'local_model':local_state,'provider_admission':sup.get('provider_admission'),'policy':sup.get('policy')},
         'conversion':c,'go_feedback':fb,'distillery':d,'evidence_forge':f,
         'costs':{'price_basis':pbasis,'free_swarm_sonnet5_equivalent_usd':swcost,'distillery_sonnet5_equivalent_usd':dcost,'measured_total_sonnet5_equivalent_usd':swcost+dcost,'verified_historical_savings_usd':None,'nominal_avoided_if_zero_cost_usd':swcost+dcost,'repo_output_only_proxy_usd':corp.get('output_only_equivalent_usd')}}
    lines=[BEGIN,'## AUTO — Gesamtsystem, GO-Fluss, Script-Auswertung und Sonnet-Vergleich',f"Aktualisiert: `{obj['generated_at']}`",'',
      '### 1. Wichtigster Effizienzindikator — was geht im Durchschnitt wieder an `go`?',
      f"**Source → GO Pass-through: {pc(fb['source_to_go'])}.** Definition: `{fb['definition']}`.",
      f"Distillery-Yield: **{pc(d.get('dataset_yield'))}** ({d.get('accepted_dataset_tokens',0):,}/{d.get('collected_source_tokens',0):,} Tokens). Reinjection-Coverage: **{pc(fb['coverage'])}** über {fb['cycles']} gemessene GO-Zyklen.",
      f"Aus {c['successful']} erfolgreichen historischen GO-Workeroutputs über **{c['macrocycles']} rekonstruierte 12-Rollen-Makrozyklen** enthalten {c['delta']} maschinenlesbare Deltas ({pc(c['delta_rate'])}) und {c['ready']} forge-ready Deltas ({pc(c['ready_rate'])}); Ø pro Makrozyklus: Deltaquote {pc(c['avg_cycle_delta_rate'])}, forge-ready {pc(c['avg_cycle_ready_rate'])}.",
      'Bei 0 akzeptierten Dataset-Tokens ist Source→GO exakt 0%; fehlende Reinjection-Receipts bleiben zusätzlich UNKNOWN statt erfunden.','',
      '### 2. Was `go` auslöst','1. Sandbox/Bridge/Storage-Preflight; Defekte zuerst reparieren.','2. Aktuellen `main`-/Supervisor-/Authority-State lesen.','3. GO-Rollen erzeugen Falsifier, Patches, Tests, Benchmarks, Deltas und offene Fragen.','4. Distillery zerlegt Fragen, sammelt Quellenmechanismen, filtert und komprimiert.','5. Evidence Forge reproduziert Repos/Deltas in Disposable-Clones/Sandboxes und misst.','6. Akzeptiertes Wissen wird in spätere GO-Kontexte reinjiziert; verifizierte Deltas gehen ins gemeinsame Ledger.','7. Dashboard berechnet Funnel, Qualität, Modelle, Kosten, Pass-through und Fortschritt neu.','',
      '### 3. Script-by-Script — live','| Subsystem | Funktion | Runtime | Messbarer Stand |','|---|---|---|---|',
      f"| **24h Supervisor** `run_24h_entityos_swarm_supervisor.sh` | hält lokale/public Lanes am Leben, quarantänisiert externe LLMs ohne typed FREE admission | {rs(sup_run)} | policy `{sup.get('policy','UNKNOWN')}` |",
      f"| **GO Free Swarm** `run_24h_entityos_swarm.py` + `run_free_go_swarm.py` | parallele Architektur-/Code-/Falsifikationsorgane | {rs(go_run)} | {w.get('worker_records',0)} Records; Ø {float(w.get('average_concurrency') or 0):.2f}, Peak {w.get('peak_concurrency',0)}; {wt:,} Tokens; {c['delta']} Delta-Records |",
      f"| **Research Distillery** `run_research_distillery_local.py` / `run_research_distillery_entry.py` | Quellen + offene Fragen → komprimierte Knowledge-Pakete | {rs(dist_run)} | {d.get('collected_source_tokens',0):,} Quelltokens → {d.get('accepted_dataset_tokens',0):,}; Yield {pc(d.get('dataset_yield'))}; OPEN {q.get('OPEN',0)}, CYCLIC {q.get('CYCLIC',0)} |",
      f"| **Evidence Forge** `run_free_evidence_forge.py` | Suche → Repo/Patch → Test/Benchmark → Evidenz | {rs(forge_run)} | **{forge_q} Queries / {forge_hits} Hits**; {forge_eval} Evaluations; {forge_acc} akzeptierte Deltas |",
      f"| **Local 4B lane** `local_research_model_server.sh` | providerunabhängige lokale Synthese/Vorfilterung | {local_state} | Ready wird nur per Loopback-Health bestätigt; Build ≠ Runtime-PASS |",
      f"| **Shared quota gate** `free_swarm_quota.py` | gemeinsame Concurrency/Cooldown-/429-Koordination | EMBEDDED | {len(budget)} beobachtete Provider/Tool-Lanes |",
      f"| **Dashboard** `evaluate.py` + `update_distillery_readme.py` + `update_system_analysis.py` | autonome Messung + README-Publikation | {rs(dash_run)} | dieses Dashboard wird aus Receipts/SQLite/Runtime neu erzeugt |",'',
      '### 4. Woran die Research Entity gerade arbeitet']
    lines += [f'- {x}' for x in tracks]
    if d.get('top_questions'):
        lines += ['','**Top offene Forschungsfragen aus der laufenden Queue:**']+[f"- {x}" for x in d['top_questions'][:10]]
    lines += ['', '### 5. Fortschritts-Funnel','| Stufe | Wert |','|---|---:|',f"| erfolgreiche GO-Workeroutputs | {c['successful']} |",f"| davon Research-Question-Emitter | {c['questions']} ({pc(c['question_rate'])}) |",f"| maschinenlesbare Architektur-Deltas | {c['delta']} ({pc(c['delta_rate'])}) |",f"| forge-ready Deltas | {c['ready']} ({pc(c['ready_rate'])}) |",f"| Distillery Quelltokens | {d.get('collected_source_tokens',0):,} |",f"| akzeptierte Dataset-Tokens | {d.get('accepted_dataset_tokens',0):,} ({pc(d.get('dataset_yield'))}) |",f"| Forge Discovery-Hits | {forge_hits:,} |",f"| Forge Evaluations | {forge_eval} |",f"| Forge akzeptierte Deltas | {forge_acc} |",f"| gemeinsames Ledger akzeptiert | {int(ds.get('accepted') or 0)} |",'',
      '### 6. Free Swarm vs. GPT/ChatGPT vs. Claude Sonnet — gleiche Messlatte','| Organ | akzeptierte Deltas | CodeQuality/100 | Ø Architekturverbesserung |','|---|---:|---:|---:|',f"| Free Swarm | {fq.get('accepted_deltas',0)} | {cq(fq.get('code_quality'))} | {cq(fq.get('mean_improvement_pct'))}% |",f"| GPT/ChatGPT | {gq.get('accepted_deltas',0)} | {cq(gq.get('code_quality'))} | {cq(gq.get('mean_improvement_pct'))}% |",f"| Claude Sonnet | {sq.get('accepted_deltas',0)} | {cq(sq.get('code_quality'))} | {cq(sq.get('mean_improvement_pct'))}% |",'',
      '**Kein Qualitätsgewinner ohne matched Receipts.** Eloquenz oder Modellname zählen nicht; nur Patch/Test/Benchmark/Non-Regression im gemeinsamen Delta-Schema.','',
      '### 7. Claude-Sonnet-5 Kostenäquivalent / nominal vermiedene Kosten',f"Preisannahme: **{pbasis}**.",'| Vergleich | Tokenbasis | Sonnet-5 Äquivalent |','|---|---:|---:|',f"| Free-Swarm Usage | {wi:,} input + {wo:,} output | **${swcost:.2f}** |",f"| Distillery Modellarbeit | {di:,} input + {do:,} output | **${dcost:.4f}** |",f"| zusammen, gemessener LLM-Tokenmix | — | **${swcost+dcost:.2f}** |",f"| persistenter Repo-Korpus, Output-only Proxy | {int(corp.get('approx_tokens_4chars') or 0):,} Proxy-Tokens | **${float(corp.get('output_only_equivalent_usd') or 0):.2f}** |",'',f"**Nominal vermiedene Sonnet-Kosten, falls diese Calls tatsächlich $0 kosteten: ${swcost+dcost:.2f}. Verifiziert gespart: UNKNOWN.** Die aktuelle typed Authority verbietet die nachträgliche FREE-Klassifikation historischer Provider-Traffic; der Korpuswert ist ebenfalls nur ein Neu-Erzeugungsproxy.",'',
      '### 8. Kapazität vs. 15 parallele Sonnet-Worker',f"Slotvergleich: Ø **{float(w.get('average_concurrency') or 0):.2f}/15 = {float(w.get('average_concurrency') or 0)/15*100:.1f}%**, Peak **{int(w.get('peak_concurrency') or 0)}/15 = {int(w.get('peak_concurrency') or 0)/15*100:.1f}%**. Gemessener Free-Swarm Outputdurchsatz: **{(wo/observed if observed else 0):.2f} Output-Tokens/s**. Das ist kein Qualitäts- oder Sonnet-Durchsatzbenchmark.",'',
      '### 9. Autonome Update-Regel','Dieser komplette Block ist Pflichtbestandteil des Publishers. Kompakte Tabellen dürfen ihn nicht mehr verdrängen. GO-Pass-through, alle Scripts, Forschungsfragen, Funnel, matched Qualitätsvergleich und Sonnet-Kosten werden fortlaufend neu berechnet.',END]
    return obj,'\n'.join(lines)+'\n'


def replace(p:Path,block:str):
    t=p.read_text(encoding='utf-8') if p.exists() else '# Free Swarm\n'
    if BEGIN in t and END in t:
        a=t.index(BEGIN);b=t.index(END,a)+len(END);t=t[:a]+block.rstrip()+t[b:]
    else:
        marker='<!-- RESEARCH_DISTILLERY_AUTO:END -->';i=t.index(marker)+len(marker) if marker in t else (t.find('\n')+1 if '\n' in t else len(t));t=t[:i]+'\n\n'+block.rstrip()+t[i:]
    # Keep old hand-written baseline explicitly historical so it cannot contradict AUTO runtime.
    t=t.replace('## 2. Aktueller verifizierter Startstand — 2026-08-24','## 2. Historischer initialer Startstand — 2026-08-24 (nicht aktueller Runtime-Stand)')
    p.write_text(t.rstrip()+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='/workspace/clay-global-research-entity');ap.add_argument('--artifacts',default='/artifacts/clay-entityos-swarm');a=ap.parse_args();repo=Path(a.repo);art=Path(a.artifacts)
    obj,block=build(repo,art);replace(repo/'free swarm/README.md',block);(repo/'free swarm/SYSTEM_ANALYSIS_LIVE.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps({'generated_at':obj['generated_at'],'source_to_go':obj['go_feedback']['source_to_go'],'cost_usd':obj['costs']['measured_total_sonnet5_equivalent_usd'],'runtime':obj['runtime']}));return 0
if __name__=='__main__':raise SystemExit(main())
