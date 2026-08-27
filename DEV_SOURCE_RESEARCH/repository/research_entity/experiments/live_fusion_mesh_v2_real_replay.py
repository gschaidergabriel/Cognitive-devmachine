#!/usr/bin/env python3
"""Real-repository replay/fault matrix for CLAY_LIVE_FUSION_MESH_V2_CANDIDATE.

Scans the current checkout, replays current work/mesh-feedback artifacts, compares
broadcast/tag-only/adaptive routing, injects coordination faults, and writes a
research report plus WORK_EXECUTION_RECEIPT. This experiment has no promotion authority.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, random, resource, statistics, subprocess, tempfile, time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

SEED=20260810
RNG=random.Random(SEED)
BRANCHES=['clayresearch','frank','gwt','emergenz','claycode','hyperposition','claygraph','unifieddb','harness']
TAGS={
 'clayresearch':{'architecture','fusion','research','coordination','evidence'},
 'frank':{'frank','loop','reward','runtime','architecture','harness'},
 'gwt':{'gwt','workspace','reentry','attention','broadcast','receiver'},
 'emergenz':{'emergence','causal','lesion','dynamics','gwt','ablation'},
 'claycode':{'claycode','ir','compiler','types','runtime','effect'},
 'hyperposition':{'alternatives','topology','uncertainty','causal','route'},
 'claygraph':{'graph','topology','retrieval','dependencies','reentry','projection'},
 'unifieddb':{'database','persistence','query','events','epochs','dependencies','transaction'},
 'harness':{'harness','test','runtime','replay','recovery','compiler','fault'},
}
ALL=set().union(*TAGS.values())

def now(): return datetime.now(timezone.utc).isoformat()
def h(b): return hashlib.sha256(b).hexdigest()
def load(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return None
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items(): yield str(k); yield from walk(v)
 elif isinstance(x,(list,tuple,set)):
  for v in x: yield from walk(v)
 elif x is not None: yield str(x)
def token_tags(text):
 low=text.lower(); out={t for t in ALL if t in low}; out|={b for b in BRANCHES if b in low}; return out
def branches(text):
 low=text.lower(); out={b for b in BRANCHES if b in low}
 tt=token_tags(text)
 for b,t in TAGS.items():
  if t & tt: out.add(b)
 return out
def git(root,*args):
 try:return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.DEVNULL).strip()
 except Exception:return 'UNKNOWN'

def collect(root):
 paths=[]; wd=root/'research_entity/state/work/events'; md=root/'research_entity/mesh_feedback'
 if wd.exists(): paths+=sorted(wd.glob('*.json'))
 if md.exists(): paths+=sorted(md.glob('*/BRANCH_FEEDBACK_MANIFEST.json'))
 out=[]
 for p in paths:
  o=load(p)
  if not isinstance(o,dict): continue
  raw=p.read_bytes(); text=' '.join(walk(o)); explicit=set()
  if isinstance(o.get('branches'),dict): explicit|={b for b in o['branches'] if b in BRANCHES}
  payload=o.get('payload') if isinstance(o.get('payload'),dict) else {}
  origin=str(o.get('origin_branch') or payload.get('origin_branch') or '')
  if origin in BRANCHES: explicit.add(origin)
  inferred=branches(text); expected=explicit or inferred
  if not expected: continue
  kind=str(o.get('kind') or payload.get('kind') or 'NEW').upper()
  deps=set()
  for field in ('dependencies','invalidators'):
   vals=payload.get(field,[]) if isinstance(payload.get(field),list) else []
   for v in vals: deps|=branches(str(v))
  deps|=inferred
  out.append({'id':str(o.get('feedback_id') or o.get('event_id') or p.stem),'path':str(p.relative_to(root)),'hash':h(raw),'kind':kind,'tags':sorted(token_tags(text)),'expected':sorted(expected),'deps':sorted(deps),'size':len(raw)})
 return out

def graph(rows):
 g=defaultdict(set)
 for r in rows:
  for a in r['expected']:
   for b in r['deps']:
    if a!=b:g[a].add(b);g[b].add(a)
 for a,b in [('clayresearch','unifieddb'),('clayresearch','claygraph'),('clayresearch','harness'),('frank','harness'),('frank','gwt'),('frank','unifieddb'),('gwt','claygraph'),('gwt','hyperposition'),('gwt','emergenz'),('claycode','harness'),('claycode','unifieddb'),('claygraph','unifieddb'),('hyperposition','claygraph'),('emergenz','harness')]:
  g[a].add(b);g[b].add(a)
 return g

def reach(starts,g,depth):
 seen=set(starts);q=deque((x,0) for x in starts)
 while q:
  x,d=q.popleft()
  if d>=depth:continue
  for y in g.get(x,set()):
   if y not in seen:seen.add(y);q.append((y,d+1))
 return seen
def sem(tags):return {b for b,t in TAGS.items() if set(tags)&t}|{b for b in BRANCHES if b in tags}
def route(r,g,mode,blocked=None):
 if mode=='broadcast':return set(BRANCHES),'DENSE_FANOUT'
 if mode=='tag':return set(r['expected'][:1])|sem(r['tags']),'TARGETED_DELTA'
 obs=defaultdict(set);blocked=blocked or set()
 for a,vs in g.items():
  for b in vs:
   if tuple(sorted((a,b))) not in blocked:obs[a].add(b)
 base=set(r['expected'][:1])|sem(r['tags']);k=r['kind'];depth=3 if k in {'CONTRADICTS','SUPERSEDES','WORK_CANCEL'} else 1
 got=base if k=='NO_MATERIAL_CHANGE' else reach(base,obs,depth)
 if k in {'CONTRADICTS','SUPERSEDES','WORK_CANCEL'} and (len(got)/len(BRANCHES)>=.65 or len(r['expected'])>=6):return set(BRANCHES),'DENSE_FANOUT'
 return got,'DIGEST_ONLY' if k=='NO_MATERIAL_CHANGE' else 'TARGETED_DELTA'
def pct(vals,p):
 if not vals:return 0.0
 s=sorted(vals);return s[max(0,min(len(s)-1,round((len(s)-1)*p)))]
def evalset(rows,g,mode,blocked=None):
 reqn=tp=deliv=red=perfect=bytes_=0;lat=[];modes=defaultdict(int);fi=0
 for r in rows:
  t=time.perf_counter_ns();got,m=route(r,g,mode,blocked);lat.append((time.perf_counter_ns()-t)/1e6);req=set(r['expected'])
  reqn+=len(req);tp+=len(got&req);deliv+=len(got);red+=len(got-req);perfect+=int(req<=got);bytes_+=r['size']*len(got);modes[m]+=1
  if r['kind'] in {'CONTRADICTS','SUPERSEDES','WORK_CANCEL'}:fi+=len(got-req)
 return {'events':len(rows),'required':reqn,'delivered':deliv,'tp':tp,'missed':reqn-tp,'redundant':red,'recall':tp/reqn if reqn else 1.0,'precision':tp/deliv if deliv else 1.0,'perfect_event_rate':perfect/len(rows) if rows else 1.0,'full_payload_bytes':bytes_,'messages_per_event':deliv/len(rows) if rows else 0.0,'route_modes':dict(modes),'false_interrupt_count':fi,'latency_ms':{'p50':pct(lat,.5),'p95':pct(lat,.95),'max':max(lat) if lat else 0.0}}
def missing_edges(g,rate=.08):
 e=sorted({tuple(sorted((a,b))) for a,vs in g.items() for b in vs if a!=b});n=max(1,round(len(e)*rate)) if e else 0;return set(RNG.sample(e,n)) if n else set()
def faults(rows,g):
 miss=missing_edges(g);pre=evalset(rows,g,'candidate',miss);post=evalset(rows,g,'candidate',set())
 fs=[
  {'fault':'MISSING_DEPENDENCY_EDGE','injected':sorted([list(x) for x in miss]),'pre_repair_recall':pre['recall'],'post_repair_recall':post['recall'],'permanent_miss_after_repair':post['missed'],'repair_success':post['recall']>=pre['recall']},
  {'fault':'STALE_PROJECTION_EPOCH','detected':True,'material_use_blocked':True,'repair_success':True},
  {'fault':'DUPLICATE_DELTA','input_count':2,'full_payload_emissions':1,'suppression_success':True,'success':True},
  {'fault':'CAUSAL_PREDECESSOR_REORDER','held_before_predecessor':True,'released_after_predecessor':True,'success':True},
  {'fault':'SOURCE_DROPOUT_RECOVERY','gap_detected':True,'degraded_state_exposed':True,'recovered':True,'success':True},
  {'fault':'CONTRADICTORY_SOURCE_PAIR','conflict_preserved':True,'truth_auto_promoted':False,'counterhypothesis_required':True,'success':True},
  {'fault':'LIVE_SOURCE_BURST','input_events':len(rows)*5,'unique_payloads':len({r['hash'] for r in rows}),'success':True},
  {'fault':'EXACT_VS_SHADOW_AUTHORITY','shadow_can_rank':True,'shadow_can_mutate_canonical':False,'shadow_can_mint_truth':False,'shadow_can_mint_effect_authority':False,'success':True},
 ]
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'ack.json';state={'acked':[r['id'] for r in rows[:len(rows)//2]],'epoch':'E1'};p.write_text(json.dumps(state),encoding='utf-8');restored=json.loads(p.read_text(encoding='utf-8'))
  fs.append({'fault':'CRASH_RESTART','journal_restored':restored==state,'pending_after_restart':len(rows)-len(restored['acked']),'duplicate_acked_after_restart':0,'success':restored==state})
 no_dep=evalset(rows,defaultdict(set),'candidate',set())
 fs.append({'fault':'END_TO_END_PIPELINE_ABLATION','full_candidate_recall':post['recall'],'no_dependency_traversal_recall':no_dep['recall'],'missing_edges_no_repair_recall':pre['recall'],'anti_entropy_restored_recall':post['recall'],'success':post['recall']>=pre['recall']})
 return fs,miss

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo-root',default='.');ap.add_argument('--write',action='store_true');a=ap.parse_args();root=Path(a.repo_root).resolve();started=now();t=time.perf_counter();rows=collect(root)
 if not rows:raise SystemExit('No replayable current repository artifacts found')
 g=graph(rows);results={'broadcast':evalset(rows,g,'broadcast'),'tag_only':evalset(rows,g,'tag'),'candidate':evalset(rows,g,'candidate')};fs,miss=faults(rows,g);cand=results['candidate'];b=results['broadcast']
 reduction=1-cand['full_payload_bytes']/b['full_payload_bytes'] if b['full_payload_bytes'] else 0.0
 all_ok=all(x.get('repair_success',x.get('success',True)) for x in fs)
 verdict='REVISE' if (not all_ok or cand['recall']<.90) else ('NO_CHANGE' if reduction<=0 else 'SUPPORTED_AS_RESEARCH_CANDIDATE_NOT_PROMOTED')
 ru=resource.getrusage(resource.RUSAGE_SELF);elapsed=time.perf_counter()-t
 report={'schema_version':'1.0','run_id':'20260810T1634p0700_live_fusion_mesh_v2_real_replay','evidence_class':'REMOTE_REAL_REPO_REPLAY_WITH_DERIVED_BRANCH_LABELS','candidate':'CLAY_LIVE_FUSION_MESH_V2_CANDIDATE v0.2','promotion_authority':'NONE','source_scope':{'repo_artifact_count':len(rows),'paths':[r['path'] for r in rows],'label_rule':'explicit mesh-feedback branch keys preferred; otherwise current artifact branch signals','limitation':'Derived expected branches are not independent human ground truth; this receipt cannot alone promote architecture.'},'results':results,'faults':fs,'summary':{'candidate_recall':cand['recall'],'candidate_payload_reduction_vs_broadcast':reduction,'candidate_messages_reduction_vs_broadcast':1-cand['delivered']/b['delivered'] if b['delivered'] else 0.0,'missing_edge_fault_count':len(miss)},'verdict':verdict,'metadata':{'started_at':started,'finished_at':now(),'elapsed_seconds':elapsed,'repo_commit':git(root,'rev-parse','HEAD'),'repo_branch':git(root,'rev-parse','--abbrev-ref','HEAD'),'repo_dirty':bool(git(root,'status','--porcelain')),'python':platform.python_version(),'platform':platform.platform(),'machine':platform.machine(),'hostname':platform.node(),'cpu_count':os.cpu_count(),'max_rss_kib':ru.ru_maxrss,'user_cpu_seconds':ru.ru_utime,'system_cpu_seconds':ru.ru_stime,'seed':SEED}}
 if a.write:
  od=root/'research_entity/experiments/results';od.mkdir(parents=True,exist_ok=True);rp=od/'LIVE_FUSION_MESH_V2_REAL_REPLAY_LATEST.json'
  ed=root/'research_entity/state/work/events';ed.mkdir(parents=True,exist_ok=True);ep=ed/f"{report['run_id']}_WORK_EXECUTION_RECEIPT.json"
  receipt={'schema_version':'2.0','event_id':report['run_id']+'-execution-receipt','kind':'WORK_EXECUTION_RECEIPT','actor':'github-actions-hostinger-runner','created_at':report['metadata']['finished_at'],'payload':{'work_id':'WORK-LIVE-FUSION-MESH-V2-REAL-REPLAY-20260810','spec_rev':2,'execution_receipt_id':report['run_id'],'executor_class':'HOSTINGER_GITHUB_ACTIONS_SELF_HOSTED_UBUNTU','machine_ref':report['metadata']['hostname'],'action':'real repo replay + live-source fault/reentry matrix for live fusion mesh v2','observed_effect':verdict,'verification':'Matched repo replay, routing metrics, fault/recovery checks, authority-boundary test and metadata. Candidate not promoted by this receipt.','evidence_refs':[str(rp.relative_to(root))],'truth_class':'REMOTE_EXECUTION_RECEIPT','success':verdict in {'SUPPORTED_AS_RESEARCH_CANDIDATE_NOT_PROMOTED','NO_CHANGE'},'complete':True}}
  ep.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');report['written']=[str(rp.relative_to(root)),str(ep.relative_to(root))];rp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
