"""Clay semantic retrieval runtime v11 candidate.

One indexed SQLite statement resolves semantic seed + coherent generation + access paths.
Natural-language/unknown intents fall back to independently ranked lexical/graph channels.
Clay/ClayCode remains semantic authority; access rank never mints truth or effect authority.
"""
from __future__ import annotations
from dataclasses import dataclass
import re, sqlite3, time
from typing import Sequence

_TOKEN_RE=re.compile(r"[a-z0-9]+",re.I)
def normalize_key(text:str)->str:
    return " ".join(m.group(0).lower() for m in _TOKEN_RE.finditer(text))

def reciprocal_rank_fusion(rankings:Sequence[Sequence[str]],k:int=60)->list[str]:
    score:dict[str,float]={}
    for ranking in rankings:
        for rank,item in enumerate(ranking,1): score[item]=score.get(item,0.0)+1.0/(k+rank)
    return [item for item,_ in sorted(score.items(),key=lambda kv:(-kv[1],kv[0]))]

@dataclass(frozen=True)
class RetrievalResult:
    refs:tuple[str,...]; mode:str; seed_id:str|None; generation_id:str|None
    source_epoch:int; graph_epoch:int; latency_ns:int

class SemanticRetrievalFabricV11:
    def __init__(self,con:sqlite3.Connection): self.con=con
    def query(self,natural_or_typed_key:str="",*,typed_seed_id:str|None=None,
              source_epoch:int,graph_epoch:int,limit:int=8,
              lexical_ranking:Sequence[str]|None=None,
              graph_fallback_ranking:Sequence[str]|None=None)->RetrievalResult:
        started=time.perf_counter_ns(); key=normalize_key(natural_or_typed_key)
        selector="s.seed_id=?" if typed_seed_id else "s.normalized_key=?"
        value=typed_seed_id if typed_seed_id else key
        rows=self.con.execute(f'''SELECT p.target_record_id,s.seed_id,g.generation_id
          FROM semantic_access_head h
          JOIN semantic_access_generations g ON g.generation_id=h.generation_id
          JOIN semantic_query_seeds s ON {selector}
          JOIN semantic_access_projection_v11 p
            ON p.generation_id=g.generation_id AND p.seed_id=s.seed_id
          WHERE h.head_key='CURRENT' AND g.status='CURRENT' AND s.status='CURRENT'
            AND h.source_epoch=? AND h.graph_epoch=?
            AND g.source_epoch=h.source_epoch AND g.graph_epoch=h.graph_epoch
            AND g.derivation_hash=h.derivation_hash
            AND s.source_epoch=h.source_epoch
            AND (s.graph_epoch IS NULL OR s.graph_epoch=h.graph_epoch)
          ORDER BY s.confidence DESC,p.path_rank ASC,p.path_weight DESC,
                   p.authority_rank DESC,p.target_record_id
          LIMIT ?''',(value,source_epoch,graph_epoch,limit)).fetchall()
        if rows:
            return RetrievalResult(tuple(r[0] for r in rows),"COHERENT_SEMANTIC_FASTPATH",
                                   rows[0][1],rows[0][2],source_epoch,graph_epoch,
                                   time.perf_counter_ns()-started)
        rankings=[r for r in (lexical_ranking,graph_fallback_ranking) if r]
        if len(rankings)>=2:
            refs=tuple(reciprocal_rank_fusion(rankings)[:limit]); mode="HYBRID_RRF_FALLBACK"
        elif rankings:
            refs=tuple(rankings[0][:limit]); mode="LEXICAL_FALLBACK"
        else:
            refs=(); mode="MISS"
        return RetrievalResult(refs,mode,None,None,source_epoch,graph_epoch,time.perf_counter_ns()-started)
