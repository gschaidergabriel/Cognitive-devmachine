"""U13 Pulse-certified incremental semantic access over U11 immutable generations.

This is an optimization/read-projection candidate, not Frank's Pulse itself and not truth/effect
authority. U12 DatabasePulseV0 remains the endogenous cycle. U13 lets unchanged per-seed access
segments survive unrelated global source-epoch increments after U12 has atomically processed the
corresponding delta stream.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, re, sqlite3, time
from typing import Iterable, Sequence

_TOKEN_RE=re.compile(r"[a-z0-9]+",re.I)
def normalize_key(text:str)->str:
    return " ".join(m.group(0).lower() for m in _TOKEN_RE.finditer(text))
def _j(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def _h(x): return hashlib.sha256(_j(x).encode()).hexdigest()
def _rrf(rankings:Sequence[Sequence[str]],k:int=60)->tuple[str,...]:
    score={}
    for ranking in rankings:
        for rank,item in enumerate(ranking,1): score[item]=score.get(item,0.0)+1.0/(k+rank)
    return tuple(x for x,_ in sorted(score.items(),key=lambda kv:(-kv[1],kv[0])))

class IncrementalAccessInvariant(RuntimeError): pass

@dataclass(frozen=True)
class RetrievalResult:
    refs:tuple[str,...]; mode:str; seed_id:str|None; generation_id:str|None; pulse_id:str|None
    source_epoch:int; graph_epoch:int; latency_ns:int

class PulseIncrementalSemanticAccessV13:
    def __init__(self,con:sqlite3.Connection): self.con=con

    def _pulse(self):
        row=self.con.execute("SELECT pulse_count,source_epoch,graph_epoch,status FROM frank_database_pulse_state WHERE singleton_id=1").fetchone()
        if not row: raise IncrementalAccessInvariant('U12 Pulse state not bootstrapped')
        return row

    def _latest_pulse_id(self)->str|None:
        row=self.con.execute("SELECT pulse_id FROM frank_database_pulse_receipts ORDER BY pulse_index DESC LIMIT 1").fetchone()
        return row[0] if row else None

    def stage_seed_generation(self,*,generation_id:str,seed_id:str,derivation_id:str,derivation_hash:str,
                              paths:Iterable[dict],dependencies:Iterable[dict],dependency_capture:str='COMPLETE',
                              created_at:str='t')->dict:
        pulse=self._pulse(); source_epoch,graph_epoch=int(pulse[1]),int(pulse[2])
        if dependency_capture not in {'COMPLETE','PARTIAL'}: raise ValueError(dependency_capture)
        path_rows=[dict(p) for p in paths]; dep_rows=[dict(d) for d in dependencies]
        if not path_rows: raise IncrementalAccessInvariant('empty seed generation is not publishable')
        if dependency_capture=='COMPLETE' and not dep_rows:
            raise IncrementalAccessInvariant('COMPLETE dependency capture requires dependencies')
        seed=self.con.execute("SELECT 1 FROM semantic_query_seeds WHERE seed_id=? AND status='CURRENT'",(seed_id,)).fetchone()
        if not seed: raise IncrementalAccessInvariant('seed is not CURRENT')
        if self.con.in_transaction: self.con.commit()
        with self.con:
            self.con.execute("INSERT INTO semantic_access_generations VALUES(?,?,?,?,?,1,?,'{}','STAGING',?,NULL,NULL)",
                             (generation_id,source_epoch,graph_epoch,derivation_id,derivation_hash,len(path_rows),created_at))
            self.con.executemany("INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",[
                (generation_id,seed_id,str(p['target_record_id']),str(p.get('target_logical_id',p['target_record_id'])),
                 int(p['path_rank']),int(p.get('hop_count',0)),float(p.get('path_weight',0.0)),
                 float(p.get('authority_rank',0.0)),str(p.get('path_clay','{}'))) for p in path_rows])
            self.con.executemany("INSERT INTO semantic_access_seed_dependencies_v13 VALUES(?,?,?,?,?,?)",[
                (generation_id,seed_id,str(d['dependency_ref']),str(d.get('dependency_kind','SEMANTIC')),
                 d.get('dependency_version_hash'),1 if d.get('proof_eligible') else 0) for d in dep_rows])
            actual=self.con.execute("SELECT count(*) FROM semantic_access_projection_v11 WHERE generation_id=? AND seed_id=?",(generation_id,seed_id)).fetchone()[0]
            if actual!=len(path_rows): raise IncrementalAccessInvariant('path verification failed')
            self.con.execute("UPDATE semantic_access_generations SET verification_clay=?,status='VERIFIED',verified_at=? WHERE generation_id=?",
                             (_j({'u13_seed_segment':True,'dependency_capture':dependency_capture,'dependency_count':len(dep_rows)}),created_at,generation_id))
        return {'generation_id':generation_id,'seed_id':seed_id,'source_epoch':source_epoch,'graph_epoch':graph_epoch,'paths':len(path_rows),'dependencies':len(dep_rows),'dependency_capture':dependency_capture}

    def install_seed_head(self,*,seed_id:str,generation_id:str,dependency_capture:str='COMPLETE',now:str='t')->dict:
        pulse=self._pulse(); pulse_count,source_epoch,graph_epoch=int(pulse[0]),int(pulse[1]),int(pulse[2])
        g=self.con.execute("SELECT source_epoch,graph_epoch,derivation_hash,status FROM semantic_access_generations WHERE generation_id=?",(generation_id,)).fetchone()
        if not g or g[3] not in {'VERIFIED','CURRENT'}: raise IncrementalAccessInvariant('generation is not VERIFIED/CURRENT')
        if int(g[0])!=source_epoch or int(g[1])!=graph_epoch: raise IncrementalAccessInvariant('generation does not match current Pulse epochs')
        n=self.con.execute("SELECT count(*) FROM semantic_access_projection_v11 WHERE generation_id=? AND seed_id=?",(generation_id,seed_id)).fetchone()[0]
        if n<=0: raise IncrementalAccessInvariant('generation has no paths for seed')
        deps=self.con.execute("SELECT dependency_ref FROM semantic_access_seed_dependencies_v13 WHERE generation_id=? AND seed_id=? ORDER BY dependency_ref",(generation_id,seed_id)).fetchall()
        if dependency_capture=='COMPLETE' and not deps: raise IncrementalAccessInvariant('COMPLETE head has no declared dependencies')
        pulse_id=self._latest_pulse_id()
        head_hash=_h({'seed_id':seed_id,'generation_id':generation_id,'source_epoch':source_epoch,'graph_epoch':graph_epoch,
                      'derivation_hash':g[2],'dependency_capture':dependency_capture,'dependencies':[r[0] for r in deps]})
        with self.con:
            self.con.execute("""INSERT INTO semantic_access_seed_heads_v13 VALUES(?,?,?,'CURRENT',?,?,?,?,?,?,?)
                ON CONFLICT(seed_id) DO UPDATE SET generation_id=excluded.generation_id,dependency_capture=excluded.dependency_capture,
                status='CURRENT',installed_source_epoch=excluded.installed_source_epoch,installed_graph_epoch=excluded.installed_graph_epoch,
                installed_by_pulse_id=excluded.installed_by_pulse_id,invalidated_by_pulse_id=NULL,invalidated_delta_id=NULL,
                head_hash=excluded.head_hash,updated_at=excluded.updated_at""",
                (seed_id,generation_id,dependency_capture,source_epoch,graph_epoch,pulse_id,None,None,head_hash,now))
            promotion_id=f"u13-promote:{seed_id}:{generation_id}"
            self.con.execute("INSERT OR REPLACE INTO semantic_access_seed_promotions_v13 VALUES(?,?,?,?,?,?,?,?,?,?)",
                (promotion_id,seed_id,generation_id,pulse_id,source_epoch,graph_epoch,dependency_capture,head_hash,
                 _j({'authority':'NON_AUTHORITATIVE_PROJECTION','pulse_count':pulse_count,'path_count':n}),now))
        return {'seed_id':seed_id,'generation_id':generation_id,'pulse_id':pulse_id,'source_epoch':source_epoch,'graph_epoch':graph_epoch,'head_hash':head_hash}

    def bootstrap_from_u11_current_partial(self,*,now:str='t')->dict:
        """Safe migration bridge: reuse the current U11 generation but mark every head PARTIAL.
        The first applied Pulse delta will therefore invalidate all until COMPLETE dependencies are compiled.
        """
        pulse=self._pulse(); source_epoch,graph_epoch=int(pulse[1]),int(pulse[2])
        h=self.con.execute("SELECT generation_id,source_epoch,graph_epoch FROM semantic_access_head WHERE head_key='CURRENT'").fetchone()
        if not h or int(h[1])!=source_epoch or int(h[2])!=graph_epoch: raise IncrementalAccessInvariant('U11 head is not coherent with Pulse')
        seeds=[r[0] for r in self.con.execute("SELECT DISTINCT seed_id FROM semantic_access_projection_v11 WHERE generation_id=? ORDER BY seed_id",(h[0],))]
        for seed in seeds: self.install_seed_head(seed_id=seed,generation_id=h[0],dependency_capture='PARTIAL',now=now)
        return {'generation_id':h[0],'seed_count':len(seeds),'dependency_capture':'PARTIAL'}

    def query(self,key:str='',*,typed_seed_id:str|None=None,source_epoch:int,graph_epoch:int,limit:int=8,
              lexical_ranking:Sequence[str]|None=None,graph_fallback_ranking:Sequence[str]|None=None)->RetrievalResult:
        started=time.perf_counter_ns(); selector='s.seed_id=?' if typed_seed_id else 's.normalized_key=?'; value=typed_seed_id if typed_seed_id else normalize_key(key)
        rows=self.con.execute(f"""SELECT p.target_record_id,s.seed_id,h.generation_id,r.pulse_id
          FROM frank_database_pulse_state ps
          JOIN semantic_query_seeds s ON {selector} AND s.status='CURRENT'
          JOIN semantic_access_seed_heads_v13 h ON h.seed_id=s.seed_id AND h.status='CURRENT'
          JOIN semantic_access_generations g ON g.generation_id=h.generation_id AND g.status IN ('VERIFIED','CURRENT','SUPERSEDED')
          JOIN semantic_access_projection_v11 p ON p.generation_id=h.generation_id AND p.seed_id=h.seed_id
          LEFT JOIN frank_database_pulse_receipts r ON r.pulse_index=ps.pulse_count
          WHERE ps.singleton_id=1 AND ps.source_epoch=? AND ps.graph_epoch=?
          ORDER BY s.confidence DESC,p.path_rank,p.path_weight DESC,p.authority_rank DESC,p.target_record_id LIMIT ?""",
          (value,source_epoch,graph_epoch,limit)).fetchall()
        if rows: return RetrievalResult(tuple(r[0] for r in rows),'PULSE_INCREMENTAL_FASTPATH',rows[0][1],rows[0][2],rows[0][3],source_epoch,graph_epoch,time.perf_counter_ns()-started)
        rankings=[r for r in (lexical_ranking,graph_fallback_ranking) if r]
        if len(rankings)>=2: refs=_rrf(rankings)[:limit]; mode='HYBRID_RRF_FALLBACK'
        elif rankings: refs=tuple(rankings[0][:limit]); mode='LEXICAL_FALLBACK'
        else: refs=(); mode='MISS'
        pulse_id=self._latest_pulse_id()
        return RetrievalResult(tuple(refs),mode,typed_seed_id,None,pulse_id,source_epoch,graph_epoch,time.perf_counter_ns()-started)
