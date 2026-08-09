#!/usr/bin/env python3
"""Hosted synthetic discriminator for ClayCode effect-optimizer equivalence."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from collections import Counter,defaultdict
import argparse,hashlib,json,random
from pathlib import Path
VERSION='claycode-effect-optimizer-barrier-probe/0.1'; SEED=20260809
class CapabilityDenied(Exception): pass
@dataclass(frozen=True)
class Event: kind:str; resource:str; capability:str; phase:str; value:int
class Gateway:
 def __init__(self,caps=()): self.caps=set(caps); self.trace=[]; self.state={}
 def effect(self,kind,res,cap,value,phase='commit'):
  if cap not in self.caps: raise CapabilityDenied(cap)
  self.trace.append(Event(kind,res,cap,phase,value))
  if kind in ('FS_WRITE','DB_WRITE'): self.state[res]=value; return value
  if kind=='FS_READ': return self.state.get(res,value)
  if kind=='HTTP': return value+7
  return value
def lit(v): return ('lit',v)
def var(): return ('var',)
def add(a,b): return ('add',a,b)
def sub(a,b): return ('sub',a,b)
def mul(a,b): return ('mul',a,b)
def eff(k,r,c,a): return ('eff',k,r,c,a)
def ev(a,x,g):
 k=a[0]
 if k=='lit': return a[1]
 if k=='var': return x
 if k=='add': return ev(a[1],x,g)+ev(a[2],x,g)
 if k=='sub': return ev(a[1],x,g)-ev(a[2],x,g)
 if k=='mul': return ev(a[1],x,g)*ev(a[2],x,g)
 if k=='eff': return g.effect(a[1],a[2],a[3],ev(a[4],x,g))
 raise ValueError(k)
def execute(a,x,caps):
 g=Gateway(caps)
 try: out=ev(a,x,g); err=None
 except Exception as e: out=None; err=type(e).__name__+':'+str(e)
 return {'output':out,'error':err,'trace':list(g.trace),'state':dict(g.state)}
def ek(e): return (e.kind,e.resource,e.capability,e.phase,e.value)
def conflict(a,b): return a.resource==b.resource or a.kind=='HTTP' or b.kind=='HTTP'
def graph(t):
 nodes=Counter(ek(e) for e in t); occ=defaultdict(int); ids=[]
 for e in t: k=ek(e); ids.append((k,occ[k])); occ[k]+=1
 edges=[]
 for i,a in enumerate(t):
  for j in range(i+1,len(t)):
   if conflict(a,t[j]): edges.append((ids[i],ids[j]))
 return (tuple(sorted(nodes.items(),key=repr)),tuple(sorted(edges,key=repr)))
def eq(a,b,mode):
 if a['output']!=b['output'] or a['error']!=b['error']: return False
 if mode=='output_only': return True
 if a['state']!=b['state']: return False
 if mode=='output_state': return True
 if mode=='exact_trace': return [ek(x) for x in a['trace']]==[ek(x) for x in b['trace']]
 if mode=='effect_graph': return graph(a['trace'])==graph(b['trace'])
 raise ValueError(mode)
def cases():
 caps={'cap.fs.write','cap.db.write','cap.fs.read','cap.http'}; w=eff('FS_WRITE','file:A','cap.fs.write',var())
 dup=sub(add(eff('FS_WRITE','file:A','cap.fs.write',var()),eff('FS_WRITE','file:A','cap.fs.write',var())),eff('FS_WRITE','file:A','cap.fs.write',var()))
 cs=add(eff('FS_WRITE','file:A','cap.fs.write',var()),eff('FS_WRITE','file:A','cap.fs.write',add(var(),lit(1))))
 cm=add(eff('FS_WRITE','file:A','cap.fs.write',add(var(),lit(1))),eff('FS_WRITE','file:A','cap.fs.write',var()))
 ds=add(eff('FS_WRITE','file:A','cap.fs.write',var()),eff('DB_WRITE','db:B','cap.db.write',add(var(),lit(1))))
 dm=add(eff('DB_WRITE','db:B','cap.db.write',add(var(),lit(1))),eff('FS_WRITE','file:A','cap.fs.write',var()))
 return {'PURE_IDENTITY':(mul(add(var(),lit(0)),lit(1)),var(),caps),'EFFECT_ERASE':(add(mul(w,lit(0)),var()),var(),caps),'EFFECT_DUPLICATE_CANCEL':(w,dup,caps),'CONFLICT_REORDER':(cs,cm,caps),'DISJOINT_REORDER':(ds,dm,caps),'AUTH_BYPASS_AUTHORIZED':(w,var(),caps),'AUTH_BYPASS_DENIED':(w,var(),set())}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--trials',type=int,default=20000); p.add_argument('--out',type=Path,required=True); a=p.parse_args(); rng=random.Random(SEED); results={}; modes=['output_only','output_state','exact_trace','effect_graph']
 for name,(src,mut,caps) in cases().items():
  c=Counter()
  for _ in range(a.trials):
   x=rng.randint(-100000,100000); s,m=execute(src,x,caps),execute(mut,x,caps)
   for mode in modes: c[mode+'_accept']+=int(eq(s,m,mode))
  results[name]={'counts':dict(c)}
 receipt={'schema_version':'1.0','experiment':'ClayCode effect optimizer barrier / equivalence discriminator','evidence_class':'HOSTED_SYNTHETIC_PROXY_NOT_PRODUCTION_CLAYCODE','version':VERSION,'seed':SEED,'trials_per_case':a.trials,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,'interpretation_guards':['constructed counts discriminate equivalence relations; not prevalence estimates','PASS does not close any BASE work package or Ubuntu gate','ordering/dependency never grants capability authority','effect_graph conflict relation remains a candidate']}
 a.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n'); print(json.dumps({'pass':True,'cases':len(results),'trials_per_case':a.trials}))
if __name__=='__main__': main()
