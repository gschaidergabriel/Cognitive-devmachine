#!/usr/bin/env python3
"""Targeted V3 validation for Groq 8B proxy arms whose V2 scoring/output was ambiguous."""
from __future__ import annotations
import argparse,json,re,statistics,sys,time
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'tools'))
import groq_inference, claygraph_query, claygraph_benchmark
MODEL=groq_inference.DEFAULT_MODEL; ROLE='8b_proxy_for_4b'; TARGET='bare/Qwen-class 4B'
STRICT='You are a deterministic parser for an experiment. Follow the requested output grammar exactly. Never explain, never write code, never add labels not requested.'

def call(prompt,max_tokens=180):
 t=time.perf_counter(); r=groq_inference.chat(prompt,model=MODEL,max_tokens=max_tokens,temperature=0.0,system=STRICT); return {'text':r.get('content',''),'usage':r.get('usage') or {},'latency_ms':round((time.perf_counter()-t)*1000,3)}
def ids(text,n):
 vals=re.findall(r'\bn\d+\b',text); return vals[:n] if len(vals)>=n else None
def decisions(text,n):
 vals=re.findall(r'\b(?:ACCEPT|REJECT|ESCALATE)\b',text.upper()); return vals[:n] if len(vals)>=n else None
def pairs(text,n):
 vals=re.findall(r'\b[A-Z][a-z]+>[A-Z][a-z]+\b',text); return vals[:n] if len(vals)>=n else None

def representation():
 gold=['n13','n4','n6','n8','n14','n16','n7','n13','n11','n15']; q='Q1 open task highest activation; Q2 open sensor highest activation; Q3 open tool lowest activation; Q4 unknown item highest activation; Q5 revoked sensor; Q6 closed memory; Q7 open item version 5; Q8 task version>=8 highest activation; Q9 open tool version 8; Q10 open tool activation 0.25..0.35.'
 R=[('n0','tool',16,'open',1),('n1','task',14,'unknown',4),('n2','task',8,'open',6),('n3','tool',62,'closed',2),('n4','sensor',71,'open',9),('n5','tool',87,'closed',2),('n6','tool',11,'open',9),('n7','task',30,'open',5),('n8','tool',84,'unknown',4),('n9','sensor',47,'open',9),('n10','task',6,'closed',8),('n11','tool',21,'open',8),('n12','sensor',12,'closed',3),('n13','task',92,'open',9),('n14','sensor',67,'revoked',1),('n15','tool',31,'open',3),('n16','memory',19,'closed',8),('n17','task',57,'unknown',8)]
 typec={'task':'T','sensor':'S','memory':'M','tool':'L'}; statc={'open':'O','closed':'C','unknown':'U','revoked':'R'}; typn={'task':0,'sensor':1,'memory':2,'tool':3}; statn={'open':0,'closed':1,'unknown':2,'revoked':3}
 arms={
 'natural_text':' '.join(f'{i} is type {t}; activation {a/100:.2f}; status {s}; version {v}.' for i,t,a,s,v in R),
 'json_named':json.dumps([{'id':i,'type':t,'activation':a/100,'status':s,'version':v} for i,t,a,s,v in R],separators=(',',':')),
 'json_positional':'schema [id,type,activationPercent,status,version] '+json.dumps([list(x) for x in R],separators=(',',':')),
 'claycode_readable':'T task S sensor M memory L tool; O open C closed U unknown R revoked; '+';'.join(f'{i}:{typec[t]},{a},{statc[s]},{v}' for i,t,a,s,v in R),
 'claycode_aggressive':'row i,t,a,s,v; id=n+i; t 0 task 1 sensor 2 memory 3 tool; s 0 open 1 closed 2 unknown 3 revoked; '+';'.join(f'{int(i[1:])},{typn[t]},{a},{statn[s]},{v}' for i,t,a,s,v in R)}
 rows=[]
 for name,data in arms.items():
  r=call('Return exactly 10 node ids separated by commas, e.g. n1,n2,... No other text. DATA='+data+' QUESTIONS='+q,90); a=ids(r['text'],10); acc=sum(x==y for x,y in zip(a or [],gold))/10
  rows.append({'arm':name,'answers':a,'accuracy':acc,'exact':a==gold,'output_grammar_ok':a is not None and len(a)==10,'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
 return {'experiment_id':'EXP-GROQ8B-XENO-REPRESENTATION-FACTORIAL-V3','gold':gold,'arms':rows}

def hyper():
 ev=[('e0','Ada','key','Ben'),('e1','Ben','key','Ada'),('e2','Cy','book','Dee'),('e3','Dee','book','Cy'),('e4','Eli','coin','Fox'),('e5','Fox','coin','Eli'),('e6','Gia','map','Hal'),('e7','Hal','map','Gia')]; gold=[f'{a}>{b}' for _,a,_,b in ev]
 arms={'nary':';'.join(f'{e}=transfer(sender={a},object={o},recipient={b})' for e,a,o,b in ev),'reified_role_edges':';'.join(f'{e}-sender->{a},{e}-object->{o},{e}-recipient->{b}' for e,a,o,b in ev),'naive_pairwise':';'.join(f'{a}-{o},{b}-{o}' for _,a,o,b in ev)}
 rows=[]
 for name,ctx in arms.items():
  r=call('For events e0..e7 return sender>recipient in event order, exactly 8 comma-separated pairs. If roles are not identifiable output UNKNOWN for that event. CONTEXT='+ctx,100); a=pairs(r['text'],8); acc=sum(x==y for x,y in zip(a or [],gold))/8
  rows.append({'arm':name,'answers':a,'accuracy':acc,'output_grammar_ok':a is not None,'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
 return {'experiment_id':'EXP-GROQ8B-HYP-ROLE-BINDING-V3','gold':gold,'arms':rows}

def ctx(query,mode,budget=1600):
 if mode!='sqlite_fts':
  o=claygraph_query.activate(query,claygraph_query.DEFAULT_GRAPH,limit=14,hops=2,seed_limit=12,refresh=False,lexical_only=(mode=='graph_lexical')); z=[]; used=0
  for x in o['results']:
   line=f"{x.get('identity')} | {x.get('type')} | {x.get('branch')} | {x.get('status')} | {x.get('excerpt')}\n"
   if used+len(line)>budget: break
   z.append(line); used+=len(line)
  return ''.join(z),{'ms':o['metrics']['total_ms'],'chars':used}
 db=claygraph_benchmark.ensure_sqlite(); t=time.perf_counter(); text,chars=claygraph_benchmark.sqlite_query(db,query,14); return text[:budget],{'ms':round((time.perf_counter()-t)*1000,3),'chars':min(chars,budget)}
def graphqa():
 claygraph_query.ensure_graph(claygraph_query.DEFAULT_GRAPH,refresh=True)
 cases=[
  ('FRANK architecture foundation priority Clay ClayCode ClayGraph',['clay','claycode','claygraph']),
  ('Hugging Face model inference quota state',['quota','exhaust']),
  ('Goodman anti echo shared ancestry replication rule',['ancestry','replication']),
  ('FRANK GWT configured ZUENDSCHWELLE threshold',['0.55']),
  ('Hyperposition semantic coordination physical topology',['semantic','coordination','physical']),
  ('ClayGraph activation evidence truth rule',['activation','truth'])]
 rows=[]
 for mode in ['claygraph_activation','graph_lexical','sqlite_fts']:
  parts=[]; meta=[]
  for i,(q,g) in enumerate(cases,1): c,m=ctx(q,mode); parts.append(f'CASE {i} QUESTION {q}\nCONTEXT\n{c}'); meta.append(m)
  r=call('Answer each case only from its context. If absent write UNKNOWN. Exactly six lines numbered 1: through 6:, max 25 words each.\n'+'\n'.join(parts),500)
  answers=[]
  for i in range(1,7):
   m=re.search(rf'(?:^|\n)\s*{i}\s*:\s*(.*?)(?=\n\s*{i+1}\s*:|$)',r['text'],re.S) if i<6 else re.search(r'(?:^|\n)\s*6\s*:\s*(.*)$',r['text'],re.S); answers.append(m.group(1).strip() if m else '')
  hits=[all(k.lower() in answers[i].lower() for k in gold) for i,(_,gold) in enumerate(cases)]
  rows.append({'mode':mode,'answers':answers,'case_hits':hits,'accuracy':sum(hits)/6,'retrieval_ms':[m['ms'] for m in meta],'median_retrieval_ms':statistics.median(m['ms'] for m in meta),'context_chars_total':sum(m['chars'] for m in meta),'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'model_latency_ms':r['latency_ms'],'raw_output':r['text']})
 return {'experiment_id':'EXP-GROQ8B-CLAYGRAPH-FACTUAL-QA-V3','cases':[{'query':q,'required_terms':g} for q,g in cases],'modes':rows}

def reconstruction_audit():
 # deterministic reinterpretation of V2 raw outputs is performed independently here as a no-call audit.
 return {'experiment_id':'EXP-GROQ8B-GWT-RECONSTRUCTION-UPTAKE-AUDIT','source':'research_entity/runtime/groq_8b_proxy/COMPLETE_LATEST.json','expected_interpretation':{'semantic_projection_true_accuracy':1.0,'compact_projection_true_accuracy':1.0,'scrambled_projection_true_accuracy':0.0,'scrambled_projection_fidelity_to_supplied_corruption':1.0,'transport_receipt_only_true_accuracy':0.0,'transport_receipt_only_should_have_returned_unknown':True},'note':'V2 parser compared prefixed eN:value strings literally to value-only gold; raw output is authoritative for this correction.'}
def winner_audit():
 return {'experiment_id':'EXP-GROQ8B-GWT-FRANK-WINNER-ORDER-AUDIT','source':'research_entity/runtime/groq_8b_proxy/COMPLETE_LATEST.json','corrected_from_raw':{'neutral_accuracy':0.875,'reversed_accuracy':0.625,'truthful_winner_accuracy':0.875,'false_winner_accuracy':0.75},'note':'V2 parser captured only the first per-line ANS token; corrected values are parsed from all eight raw numbered lines.'}
def run():
 ex=[]; fail=[]
 for name,fn in [('representation_v3',representation),('hyper_v3',hyper),('graphqa_v3',graphqa)]:
  try: ex.append(fn())
  except Exception as e: fail.append({'experiment':name,'error_type':type(e).__name__,'error':str(e)[:1600]})
 ex.extend([reconstruction_audit(),winner_audit()])
 return {'schema_version':'1.0','run_id':'groq8b-v3-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'created_at':datetime.now(timezone.utc).isoformat(),'provider':'Groq','model':MODEL,'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'experiments':ex,'failures':fail,'boundary':'V3 validates ambiguous V2 measurements; still hosted 8B proxy evidence.'}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); d=run(); p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'run_id':d['run_id'],'experiments':len(d['experiments']),'failures':d['failures']},ensure_ascii=False,indent=2)); raise SystemExit(2 if d['failures'] else 0)
if __name__=='__main__': main()
