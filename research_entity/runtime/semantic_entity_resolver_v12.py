from __future__ import annotations
from dataclasses import dataclass
import re,sqlite3,time
_TOKEN_RE=re.compile(r'[a-z0-9_]+',re.I)
def tokens(x): return list(dict.fromkeys(t.lower() for t in _TOKEN_RE.findall(x)))
@dataclass(frozen=True)
class EntityResolution:
 logical_id:str|None; resolution_class:str; confidence:float; candidates:tuple[str,...]; latency_ns:int
class SemanticEntityResolverV12:
 def __init__(self,con:sqlite3.Connection,min_score:float=2.5,min_margin:float=.20): self.con=con; self.min_score=min_score; self.min_margin=min_margin
 def resolve(self,text:str,*,source_epoch:int)->EntityResolution:
  st=time.perf_counter_ns(); qt=set(tokens(text))
  if not qt:return EntityResolution(None,'MISS',0,(),time.perf_counter_ns()-st)
  marks=','.join('?' for _ in qt)
  row=self.con.execute(f"SELECT logical_id FROM semantic_entity_aliases WHERE logical_id IN ({marks}) AND source_epoch=? AND status='CURRENT' ORDER BY logical_id LIMIT 1",(*qt,source_epoch)).fetchone()
  if row:return EntityResolution(row[0],'EXACT_LOGICAL_ID',1.0,(row[0],),time.perf_counter_ns()-st)
  expr=' OR '.join('"'+t.replace('"','')+'"' for t in qt if len(t)>1)
  if not expr:return EntityResolution(None,'MISS',0,(),time.perf_counter_ns()-st)
  rows=self.con.execute('''SELECT a.alias_norm,a.logical_id,a.alias_class,a.confidence,semantic_entity_alias_fts.rank
    FROM semantic_entity_alias_fts JOIN semantic_entity_aliases a USING(alias_version_id)
    WHERE semantic_entity_alias_fts MATCH ? AND a.source_epoch=? AND a.status='CURRENT'
      AND a.alias_class IN ('CANONICAL','EXPLICIT','DOCUMENT_DERIVED')
    ORDER BY semantic_entity_alias_fts.rank,a.confidence DESC,a.logical_id LIMIT 24''',(expr,source_epoch)).fetchall()
  by={}
  for alias,lid,cls,conf,_rank in rows:
   at=set(tokens(alias)); coverage=len(at&qt)/max(1,len(at)); class_weight={'CANONICAL':1.0,'EXPLICIT':.98,'DOCUMENT_DERIVED':.82}[cls]
   score=2.0*coverage+float(conf)*class_weight
   by[lid]=max(by.get(lid,0),score)
  ranked=sorted(by.items(),key=lambda kv:(-kv[1],kv[0])); cands=tuple(x[0] for x in ranked[:8])
  if not ranked or ranked[0][1]<self.min_score:return EntityResolution(None,'LOW_CONFIDENCE' if ranked else 'MISS',ranked[0][1] if ranked else 0,cands,time.perf_counter_ns()-st)
  if len(ranked)>1 and ranked[0][1]-ranked[1][1]<self.min_margin:return EntityResolution(None,'AMBIGUOUS',ranked[0][1],cands,time.perf_counter_ns()-st)
  return EntityResolution(ranked[0][0],'EVIDENCE_ALIAS',min(1.0,ranked[0][1]/3.0),cands,time.perf_counter_ns()-st)
