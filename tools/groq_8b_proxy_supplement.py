#!/usr/bin/env python3
"""Normalized Groq 8B proxy tests separating semantics from output-format compliance."""
from __future__ import annotations
import argparse, json, re, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import groq_inference

MODEL=groq_inference.DEFAULT_MODEL
ROLE='8b_proxy_for_4b'
TARGET='bare/Qwen-class 4B'


def ask(prompt:str,max_tokens:int=160)->dict[str,Any]:
    t0=time.perf_counter(); r=groq_inference.chat(prompt,model=MODEL,max_tokens=max_tokens,temperature=0.0)
    return {'text':r.get('content',''),'usage':r.get('usage') or {},'latency_ms':round((time.perf_counter()-t0)*1000,3)}


def ans_list(text:str)->list[str]|None:
    m=re.search(r'ANS\s*:\s*([^\n`]+)',text,re.I)
    if m:
        return [x.strip().strip('"\' []') for x in m.group(1).split(',') if x.strip()]
    # fallback: JSON string array anywhere
    for m in re.finditer(r'\[[^\[\]]+\]',text,re.S):
        try:
            x=json.loads(m.group(0))
            if isinstance(x,list) and all(isinstance(v,(str,int,float)) for v in x):
                return [str(v) for v in x]
        except Exception: pass
    return None


def representation_factorial()->dict[str,Any]:
    gold=['n13','n4','n6','n8','n14','n16','n7','n13','n11','n15']
    qs='1 open task highest activation; 2 open sensor highest activation; 3 open tool lowest activation; 4 unknown item highest activation; 5 revoked sensor; 6 closed memory; 7 open item version 5; 8 task version>=8 highest activation; 9 open tool version 8; 10 open tool activation 0.25..0.35'
    records=[
      ('n0','tool',16,'open',1),('n1','task',14,'unknown',4),('n2','task',8,'open',6),('n3','tool',62,'closed',2),('n4','sensor',71,'open',9),('n5','tool',87,'closed',2),('n6','tool',11,'open',9),('n7','task',30,'open',5),('n8','tool',84,'unknown',4),('n9','sensor',47,'open',9),('n10','task',6,'closed',8),('n11','tool',21,'open',8),('n12','sensor',12,'closed',3),('n13','task',92,'open',9),('n14','sensor',67,'revoked',1),('n15','tool',31,'open',3),('n16','memory',19,'closed',8),('n17','task',57,'unknown',8)]
    natural=' '.join(f'{i} is a {t}, activation {a/100:.2f}, status {s}, version {v}.' for i,t,a,s,v in records)
    named=json.dumps([{'id':i,'type':t,'activation':a/100,'status':s,'version':v} for i,t,a,s,v in records],separators=(',',':'))
    positional='schema=[id,type,activationPercent,status,version];'+json.dumps([list(x) for x in records],separators=(',',':'))
    readable='key T=task S=sensor M=memory L=tool; O=open C=closed U=unknown R=revoked; '+ ';'.join(f'{i}:{ {"task":"T","sensor":"S","memory":"M","tool":"L"}[t]},{a},{ {"open":"O","closed":"C","unknown":"U","revoked":"R"}[s]},{v}' for i,t,a,s,v in records)
    aggressive='row=i,t,a,s,v; id=n+i; t 0=task 1=sensor 2=memory 3=tool; s 0=open 1=closed 2=unknown 3=revoked; '+ ';'.join(f'{int(i[1:])},{ {"task":0,"sensor":1,"memory":2,"tool":3}[t]},{a},{ {"open":0,"closed":1,"unknown":2,"revoked":3}[s]},{v}' for i,t,a,s,v in records)
    arms={'natural_text':natural,'json_named':named,'json_positional':positional,'claycode_readable':readable,'claycode_aggressive':aggressive}
    rows=[]
    for name,data in arms.items():
        prompt='Decode the records and answer the 10 queries. Output exactly one line: ANS:id1,id2,id3,id4,id5,id6,id7,id8,id9,id10. No explanation.\nDATA:'+data+'\nQUERIES:'+qs
        r=ask(prompt,120); parsed=ans_list(r['text'])
        correct=sum(1 for a,b in zip(parsed or [],gold) if a==b)
        rows.append({'arm':name,'answers':parsed,'semantic_item_accuracy':correct/10,'exact_semantic_sequence':parsed==gold,'format_compliant':bool(re.fullmatch(r'\s*ANS\s*:[^\n]+\s*',r['text'],re.I)),'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
    return {'experiment_id':'EXP-GROQ8B-XENO-REPRESENTATION-FACTORIAL-V2','origin':['CC7 four Qwen reader arms','CC8 EXP-LIVE-XENO-CLAY-FACTORIAL'],'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'gold':gold,'arms':rows}


def otcc_semantic()->dict[str,Any]:
    cases=[('t0','s','c','s','v'),('t1','x','c','s','v'),('t2','x','c','x','v'),('t3','x','u','s','v'),('t4','s','c','s','r'),('t5','x','v','s','v'),('t6','x','v','x','v'),('t7','x','u','x','v'),('t8','s','v','s','v'),('t9','x','c','s','e'),('t10','x','c','s','v'),('t11','x','u','s','r')]
    gold=[]
    for _,root,cov,dep,cap in cases:
        if cap!='v': gold.append('REJECT')
        elif cov=='u': gold.append('ESCALATE')
        elif root=='s': gold.append('ACCEPT')
        elif dep=='x': gold.append('REJECT')
        else: gold.append('ACCEPT')
    rec=';'.join(','.join(x) for x in cases)
    prompts={
      'explicit_json_semantics':f'Fields id,root,coverage,dependency,capability. s=same x=changed; c=complete v=conservative u=unknown; capability v=valid r=revoked e=expired. Rule: invalid cap REJECT; unknown coverage ESCALATE; same root ACCEPT; changed dependency REJECT; else ACCEPT. Records {rec}.',
      'gamma_compact':f'Gamma: tuple id,r,c,d,k. r s/x basis same/changed; c c/v/u closure complete/conservative/unknown; d s/x relevant dependency same/changed; k v/r/e valid/revoked/expired. Decide k!=v R; c=u E; r=s A; d=x R; else A. Convert A=ACCEPT R=REJECT E=ESCALATE. Tuples {rec}.',
      'otcc_compact':f'OTCC witness rule: authority first, unknown closure widens, unchanged basis passes, changed relevant witness rejects, otherwise scoped compatible rebase passes. Codes tuple id,r,c,d,k where r s/x, closure c/v/u, dep s/x, cap v/r/e. Output decisions. {rec}'
    }
    rows=[]
    for name,p in prompts.items():
        r=ask('Return exactly ANS:'+','.join(['DECISION']*12).replace('DECISION','<decision>')+' with 12 concrete words and no explanation. '+p,160)
        parsed=ans_list(r['text']); correct=sum(1 for a,b in zip(parsed or [],gold) if a.upper()==b)
        unsafe=sum(1 for a,b in zip(parsed or [],gold) if a.upper()=='ACCEPT' and b in {'REJECT','ESCALATE'})
        rows.append({'arm':name,'answers':parsed,'semantic_item_accuracy':correct/12,'unsafe_accepts':unsafe,'format_compliant':bool(parsed and len(parsed)==12),'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
    return {'experiment_id':'EXP-GROQ8B-OTCC-GAMMA-SEMANTIC-V2','origin':['G8 EXP-QWEN4B-TCC-GAMMA','CC8 OTCC'],'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'gold':gold,'arms':rows}


def gwt_reconstruction()->dict[str,Any]:
    facts=[('e0','harbor','amber'),('e1','forest','violet'),('e2','desert','silver'),('e3','island','cobalt'),('e4','valley','crimson'),('e5','station','ivory'),('e6','garden','teal'),('e7','tower','gold')]
    gold=[v for _,_,v in facts]
    full=';'.join(f'{e}: place={p}, code={v}' for e,p,v in facts)
    compact=';'.join(f'{e}|{p}|{v}' for e,p,v in facts)
    transport=';'.join(f'{e}: delivered=true, bytes=32, receipt=ok' for e,_,_ in facts)
    scrambled=';'.join(f'{e}: place={p}, code={facts[(i+1)%len(facts)][2]}' for i,(e,p,_) in enumerate(facts))
    q=';'.join(f'{e} code for {p}?' for e,p,_ in facts)
    arms={'semantic_projection':full,'compact_projection':compact,'transport_receipt_only':transport,'scrambled_projection':scrambled}
    rows=[]
    for name,ctx in arms.items():
        r=ask(f'Use ONLY context. If a requested code is absent answer UNKNOWN. Output exactly ANS:v1,v2,v3,v4,v5,v6,v7,v8. CONTEXT:{ctx} QUERIES:{q}',120)
        parsed=ans_list(r['text']); acc=sum(1 for a,b in zip(parsed or [],gold) if a.lower()==b)/8
        rows.append({'arm':name,'answers':parsed,'accuracy_against_true_semantics':acc,'unknown_count':sum(1 for x in (parsed or []) if x.upper()=='UNKNOWN'),'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
    return {'experiment_id':'EXP-GROQ8B-GWT-RECONSTRUCTION-UPTAKE-PROXY','origin':['EXP-LIVE-GWT-RECONSTRUCTION-UPTAKE','EXP-GWT-RECONSTRUCTION-LESION-005'],'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'gold':gold,'arms':rows,'boundary':'Tests model-side semantic uptake from projections; does not establish live FRANK transport/Core inclusion or latent reconstruction.'}


def hyper_role()->dict[str,Any]:
    ev=[('e0','Ada','key','Ben'),('e1','Ben','key','Ada'),('e2','Cy','book','Dee'),('e3','Dee','book','Cy'),('e4','Eli','coin','Fox'),('e5','Fox','coin','Eli'),('e6','Gia','map','Hal'),('e7','Hal','map','Gia')]
    gold=[f'{a}>{b}' for _,a,_,b in ev]
    arms={
      'nary':';'.join(f'{e}=transfer(sender={a},object={o},recipient={b})' for e,a,o,b in ev),
      'reified_role_edges':';'.join(f'{e}-sender->{a},{e}-object->{o},{e}-recipient->{b}' for e,a,o,b in ev),
      'naive_pairwise':';'.join(f'{a}-{o},{b}-{o}' for _,a,o,b in ev)
    }
    rows=[]
    for name,ctx in arms.items():
        r=ask('For e0..e7 return sender>recipient. Never invent missing roles; use UNKNOWN if representation cannot identify roles. Output exactly ANS:x1,x2,x3,x4,x5,x6,x7,x8. CONTEXT:'+ctx,120)
        parsed=ans_list(r['text']); acc=sum(1 for a,b in zip(parsed or [],gold) if a==b)/8
        rows.append({'arm':name,'answers':parsed,'role_binding_accuracy':acc,'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
    return {'experiment_id':'EXP-GROQ8B-HYP-ROLE-BINDING-V2','origin':['H2 EXP-HYP-H2-RELATION-003 next target-reader question'],'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'gold':gold,'arms':rows}


def run()->dict[str,Any]:
    exps=[]; failures=[]
    for name,fn in [('representation',representation_factorial),('otcc',otcc_semantic),('gwt_reconstruction',gwt_reconstruction),('hyper_role',hyper_role)]:
        try: exps.append(fn())
        except Exception as e: failures.append({'experiment':name,'error_type':type(e).__name__,'error':str(e)[:1200]})
    return {'schema_version':'1.0','run_id':'groq8b-supplement-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'created_at':datetime.now(timezone.utc).isoformat(),'provider':'Groq','model':MODEL,'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'experiments':exps,'failures':failures,'scientific_boundary':'8B hosted semantic proxy only; target 4B/live/hardware experiments remain distinct.'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); d=run(); p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'run_id':d['run_id'],'experiments':len(d['experiments']),'failures':d['failures']},ensure_ascii=False,indent=2)); raise SystemExit(2 if d['failures'] else 0)
if __name__=='__main__': main()
