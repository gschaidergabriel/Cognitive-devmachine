from __future__ import annotations
from dataclasses import dataclass
import re,sqlite3,time
_TOKEN_RE=re.compile(r'[a-z0-9]+',re.I)
def norm(x):return ' '.join(m.group(0).lower() for m in _TOKEN_RE.finditer(x))
@dataclass(frozen=True)
class CyclePin:
 cycle_id:str; generation_id:str; source_epoch:int; graph_epoch:int; derivation_hash:str
class CyclePinnedSemanticAccessV13:
 def __init__(self,con:sqlite3.Connection):self.con=con
 def pin(self,cycle_id:str,*,source_epoch:int,graph_epoch:int,pinned_at:str)->CyclePin:
  r=self.con.execute('''select g.generation_id,g.derivation_hash from semantic_access_head h join semantic_access_generations g on g.generation_id=h.generation_id
    where h.head_key='CURRENT' and g.status='CURRENT' and h.source_epoch=? and h.graph_epoch=? and g.source_epoch=h.source_epoch and g.graph_epoch=h.graph_epoch and g.derivation_hash=h.derivation_hash''',(source_epoch,graph_epoch)).fetchone()
  if not r:raise RuntimeError('no coherent CURRENT generation for requested epochs')
  p=CyclePin(cycle_id,r[0],source_epoch,graph_epoch,r[1])
  with self.con:self.con.execute("insert into semantic_access_cycle_pins values(?,?,?,?,?,'PINNED',?,NULL)",(cycle_id,p.generation_id,source_epoch,graph_epoch,p.derivation_hash,pinned_at))
  return p
 def query(self,pin:CyclePin,text:str,limit:int=8):
  st=time.perf_counter_ns(); rows=self.con.execute('''select target_record_id from semantic_access_flat_v13
     where generation_id=? and normalized_key=? order by path_rank,path_weight desc,authority_rank desc,target_record_id limit ?''',(pin.generation_id,norm(text),limit)).fetchall()
  return tuple(r[0] for r in rows),time.perf_counter_ns()-st
