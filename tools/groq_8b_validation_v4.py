#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'tools'))
import groq_inference
MODEL=groq_inference.DEFAULT_MODEL; ROLE='8b_proxy_for_4b'; TARGET='bare/Qwen-class 4B'
SYSTEM='You are a deterministic experimental data reader. Compute each requested answer from the supplied data. Never explain and never output code. Preserve the exact requested labels.'
def call(p,n=180):
 t=time.perf_counter();r=groq_inference.chat(p,model=MODEL,max_tokens=n,temperature=0.0,system=SYSTEM);return {'text':r.get('content',''),'usage':r.get('usage') or {},'latency_ms':round((time.perf_counter()-t)*1000,3)}
def qmap(text): return {int(k):v for k,v in re.findall(r'\bq(\d+)\s*=\s*(n\d+)\b',text,re.I)}
def emap(text): return {int(k):v for k,v in re.findall(r'\be(\d+)\s*=\s*([A-Za-z]+>[A-Za-z]+|UNKNOWN)\b',text,re.I)}
def representation():
 gold={1:'n13',2:'n4',3:'n6',4:'n8',5:'n14',6:'n16',7:'n7',8:'n13',9:'n11',10:'n15'}; qs='q1=open task highest activation; q2=open sensor highest activation; q3=open tool lowest activation; q4=unknown item highest activation; q5=revoked sensor; q6=closed memory; q7=open item version 5; q8=task version>=8 highest activation; q9=open tool version 8; q10=open tool activation 0.25..0.35.'
 R=[('n0','tool',16,'open',1),('n1','task',14,'unknown',4),('n2','task',8,'open',6),('n3','tool',62,'closed',2),('n4','sensor',71,'open',9),('n5','tool',87,'closed',2),('n6','tool',11,'open',9),('n7','task',30,'open',5),('n8','tool',84,'unknown',4),('n9','sensor',47,'open',9),('n10','task',6,'closed',8),('n11','tool',21,'open',8),('n12','sensor',12,'closed',3),('n13','task',92,'open',9),('n14','sensor',67,'revoked',1),('n15','tool',31,'open',3),('n16','memory',19,'closed',8),('n17','task',57,'unknown',8)]
 tc={'task':'T','sensor':'S','memory':'M','tool':'L'};sc={'open':'O','closed':'C','unknown':'U','revoked':'R'};tn={'task':0,'sensor':1,'memory':2,'tool':3};sn={'open':0,'closed':1,'unknown':2,'revoked':3}
 arms={'natural':' '.join(f'{i} type={t} activation={a/100:.2f} status={s} version={v}.' for i,t,a,s,v in R),'json_named':json.dumps([{'id':i,'type':t,'activation':a/100,'status':s,'version':v} for i,t,a,s,v in R],separators=(',',':')),'json_positional':'schema=[id,type,activationPercent,status,version] '+json.dumps([list(x) for x in R],separators=(',',':')),'claycode_readable':'T=task S=sensor M=memory L=tool O=open C=closed U=unknown R=revoked; '+';'.join(f'{i}:{tc[t]},{a},{sc[s]},{v}' for i,t,a,s,v in R),'claycode_aggressive':'row=i,t,a,s,v id=n+i t:0task1sensor2memory3tool s:0open1closed2unknown3revoked; '+';'.join(f'{int(i[1:])},{tn[t]},{a},{sn[s]},{v}' for i,t,a,s,v in R)}
 rows=[]
 for name,data in arms.items():
  r=call('Answer all ten queries. Output exactly q1=nX;q2=nX;...;q10=nX with no other text. DATA='+data+' QUERIES='+qs,120); m=qmap(r['text']); correct=sum(m.get(i)==gold[i] for i in gold)
  rows.append({'arm':name,'answers':m,'accuracy':correct/10,'complete':len(m)==10,'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
 return {'experiment_id':'EXP-GROQ8B-XENO-REPRESENTATION-FACTORIAL-V4','gold':gold,'arms':rows}
def hyper():
 ev=[('e0','Ada','key','Ben'),('e1','Ben','key','Ada'),('e2','Cy','book','Dee'),('e3','Dee','book','Cy'),('e4','Eli','coin','Fox'),('e5','Fox','coin','Eli'),('e6','Gia','map','Hal'),('e7','Hal','map','Gia')];gold={i:f'{a}>{b}' for i,(_,a,_,b) in enumerate(ev)}
 arms={'nary':';'.join(f'{e}=transfer(sender={a},object={o},recipient={b})' for e,a,o,b in ev),'reified_role_edges':';'.join(f'{e}-sender->{a},{e}-object->{o},{e}-recipient->{b}' for e,a,o,b in ev),'naive_pairwise':';'.join(f'{a}-{o},{b}-{o}' for _,a,o,b in ev)}
 rows=[]
 for name,data in arms.items():
  r=call('For each event identify sender>recipient. If the representation does not identify roles for an event use UNKNOWN. Output exactly e0=X;e1=X;...;e7=X. DATA='+data,120);m=emap(r['text']);correct=sum(m.get(i)==gold[i] for i in gold)
  rows.append({'arm':name,'answers':m,'accuracy':correct/8,'unknowns':sum(v.upper()=='UNKNOWN' for v in m.values()),'complete':len(m)==8,'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
 return {'experiment_id':'EXP-GROQ8B-HYP-ROLE-BINDING-V4','gold':gold,'arms':rows}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();ex=[];fail=[]
 for name,fn in [('representation',representation),('hyper',hyper)]:
  try:ex.append(fn())
  except Exception as e:fail.append({'experiment':name,'error_type':type(e).__name__,'error':str(e)[:1200]})
 d={'schema_version':'1.0','run_id':'groq8b-v4-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'created_at':datetime.now(timezone.utc).isoformat(),'provider':'Groq','model':MODEL,'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'experiments':ex,'failures':fail,'boundary':'Label-stable final replication for representation/role-binding only; still hosted 8B proxy evidence.'};p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'run_id':d['run_id'],'experiments':len(ex),'failures':fail}));raise SystemExit(2 if fail else 0)
if __name__=='__main__':main()
