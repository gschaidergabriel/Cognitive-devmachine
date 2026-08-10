from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import re, sqlite3, unicodedata
from .state_ledger import StaleEpoch, h

class UnverifiedGraphProjection(RuntimeError): pass

@dataclass(frozen=True)
class GraphEdge:
    source_ref: str
    target_ref: str
    relation_type: str
    weight: float = 1.0
    confidence: float | None = None
    provenance_ref: str | None = None

@dataclass(frozen=True)
class CognitiveQueryIntent:
    query_id: str
    text: str
    semantic_hints: tuple[str,...] = ()
    anchor_refs: tuple[str,...] = ()
    target_mode: str = 'DIRECT'
    statuses: tuple[str,...] = ('CURRENT',)
    epistemic: tuple[str,...] = ('KNOWN',)
    limit: int = 12
    basis_epoch: int | None = None
    purpose: str = 'COGNITIVE_RETRIEVAL'

@dataclass(frozen=True)
class CognitiveResult:
    record_ref: str
    domain: str
    key: str
    value: Any
    epistemic: str
    status: str
    source_semantic_hash: str
    score: float
    base_rank: int | None
    graph_path: tuple[str,str,str,str] | None
    score_receipt: dict[str,Any]
    provenance: dict[str,Any]

@dataclass(frozen=True)
class CognitiveRetrievalReceipt:
    query_id: str
    basis_epoch: int
    semantic_state_hash: str
    intent_hash: str
    results: tuple[CognitiveResult,...]
    truncated: bool
    graph_used: bool
    authority: str = 'ASSEMBLY_CONTEXT_ONLY'

def load_verified_claygraph_edges(conn: sqlite3.Connection, *, source_epoch: int) -> tuple[GraphEdge,...]:
    ambiguous=int(conn.execute('SELECT COUNT(*) FROM v_graph_projection_ambiguous_edge_epochs').fetchone()[0])
    if ambiguous: raise UnverifiedGraphProjection(f'ambiguous ClayGraph edge epochs: {ambiguous}')
    row=conn.execute("SELECT MAX(graph_epoch) FROM graph_epochs WHERE status='CURRENT'").fetchone()
    graph_epoch=None if row is None else row[0]
    if graph_epoch is None: raise UnverifiedGraphProjection('no CURRENT ClayGraph epoch')
    receipt=conn.execute(
        'SELECT 1 FROM graph_current_projection_receipts WHERE graph_epoch=? AND source_epoch=? '
        'AND verified_equal=1 ORDER BY created_at DESC LIMIT 1',
        (int(graph_epoch),int(source_epoch))).fetchone()
    if receipt is None:
        raise UnverifiedGraphProjection(f'no verified projection receipt for graph_epoch={graph_epoch} source_epoch={source_epoch}')
    future=int(conn.execute('SELECT COUNT(*) FROM graph_head_edges WHERE graph_epoch>?',(int(graph_epoch),)).fetchone()[0])
    if future: raise UnverifiedGraphProjection('graph head is newer than verified receipt')
    out=[]
    sql=('SELECT logical_edge_id,source_logical_id,target_logical_id,relation_type,weight,confidence,graph_epoch '
         'FROM v_graph_current_edges_fast ORDER BY logical_edge_id')
    for r in conn.execute(sql):
        out.append(GraphEdge(str(r['source_logical_id']),str(r['target_logical_id']),str(r['relation_type']),
            float(r['weight']),None if r['confidence'] is None else float(r['confidence']),
            f"claygraph:{r['logical_edge_id']}@{r['graph_epoch']}"))
    return tuple(out)

_STOP=set(('the a an is are was were be been being of to and or in on at for from by with as it this that what which '
'who how does do where when after before into same actually der die das ein eine einer einem einen ist sind war waren '
'sein wird werden von zu und oder im in am für aus mit als es dies diese dieser was welcher welche welches wer wie wo '
'wann tatsächlich').split())

def _norm(v: Any) -> str:
    s=unicodedata.normalize('NFKC',str(v)).casefold().replace('v0.1','v0_1')
    s=re.sub(r'[_/:\-]+',' ',s); s=re.sub(r'[^\w]+',' ',s,flags=re.UNICODE)
    return ' '.join(s.split())

def _tokens(v: Any) -> list[str]:
    return [x for x in _norm(v).split() if len(x)>1 and x not in _STOP and not x.isdigit()]

def _flatten(v: Any) -> str:
    if v is None: return ''
    if isinstance(v,dict): return ' '.join(f'{k} {_flatten(v[k])}' for k in sorted(v,key=str))
    if isinstance(v,(list,tuple,set)): return ' '.join(_flatten(x) for x in v)
    return str(v)

class CognitiveRetrievalIndex:
    def __init__(self,query_plane,*,graph_edges=(),alias_groups=()):
        self.query_plane=query_plane; self.ledger=query_plane.ledger; self.graph_edges=tuple(graph_edges)
        self._alias={}
        for group in alias_groups:
            terms={_norm(x) for x in group if _norm(x)}
            for term in terms: self._alias.setdefault(term,set()).update(terms-{term})
        self._epoch=self._state_hash=None; self._rows={}; self._doc_tokens={}; self._provenance={}; self._adj={}
        self._fts=None; self._fts_available=False

    def close(self):
        if self._fts is not None: self._fts.close()
        self._fts=None

    @staticmethod
    def _variants(term):
        out={term}
        for suffix in ('ing','ed','es','s','en','ern','ungen','ung','ieren','ier','ly'):
            if len(term)>len(suffix)+3 and term.endswith(suffix): out.add(term[:-len(suffix)])
        return out

    def _expand(self,text):
        base=_tokens(text); out=set(base)
        for term in base:
            for variant in self._variants(term):
                out.add(variant); out.update(self._alias.get(variant,()))
        return sorted(out)

    def _reconstruct_provenance(self):
        latest={}
        try: events=self.ledger.export_events()
        except Exception: return latest
        for e in events:
            for op in e.get('ops') or ():
                d=str(op.get('domain','')).strip(); k=str(op.get('key','')).strip()
                if d and k:
                    latest[f'{d}:{k}']={'event_id':e.get('event_id'),'writer':e.get('writer'),
                        'committed_at':e.get('committed_at'),'provenance':e.get('provenance') or {},
                        'source':e.get('source') or {}}
        return latest

    def _refresh(self):
        epoch=self.ledger.epoch; state_hash=self.ledger.semantic_state_hash
        if self._epoch==epoch and self._state_hash==state_hash: return
        rows={}; dt={}
        for row in self.ledger.materialized():
            ref=f"{row['domain']}:{row['key']}"; rows[ref]=dict(row)
            dt[ref]=set(_tokens(f"{row['domain']} {row['key']} {_flatten(row['value'])}"))
        adj={}
        for e in self.graph_edges:
            w=max(0.0,min(1.0,float(e.weight)))
            if e.confidence is not None: w*=max(0.0,min(1.0,float(e.confidence)))
            adj.setdefault(e.source_ref,[]).append((e.target_ref,e.relation_type,w,'FORWARD',e.provenance_ref))
            adj.setdefault(e.target_ref,[]).append((e.source_ref,e.relation_type,w*.9,'REVERSE',e.provenance_ref))
        if self._fts is not None: self._fts.close()
        db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row; ok=True
        try:
            db.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(record_ref UNINDEXED,key_text,body_text,tokenize='unicode61 remove_diacritics 2')")
            db.execute("INSERT INTO docs_fts(docs_fts,rank) VALUES('rank','bm25(0.0,3.0,1.0)')")
            for ref,row in rows.items():
                db.execute('INSERT INTO docs_fts(record_ref,key_text,body_text) VALUES(?,?,?)',
                    (ref,f"{row['domain']} {row['key']}",_flatten(row['value'])))
            db.commit()
        except sqlite3.OperationalError: ok=False
        self._rows=rows; self._doc_tokens=dt; self._provenance=self._reconstruct_provenance(); self._adj=adj
        self._fts=db; self._fts_available=ok; self._epoch=epoch; self._state_hash=state_hash

    @staticmethod
    def _validate(i):
        if not i.query_id.strip(): raise ValueError('query_id required')
        if i.target_mode not in {'DIRECT','CONNECTED_TARGET'}: raise ValueError('invalid target_mode')
        if not 0<i.limit<=4096: raise ValueError('invalid limit')
        if i.target_mode=='CONNECTED_TARGET' and not i.anchor_refs: raise ValueError('CONNECTED_TARGET requires anchor_refs')

    def _candidate_ranks(self,terms,max_rows):
        if not terms: return []
        if self._fts_available and self._fts is not None:
            q=' OR '.join('"' + t.replace('"','') + '"' for t in terms)
            try:
                return [r['record_ref'] for r in self._fts.execute(
                    'SELECT record_ref FROM docs_fts WHERE docs_fts MATCH ? ORDER BY rank LIMIT ?',(q,max_rows))]
            except sqlite3.OperationalError: pass
        q=set(terms); scored=[]
        for ref,doc in self._doc_tokens.items():
            n=len(q&doc)
            if n: scored.append((n/max(1,len(q)),n,ref))
        scored.sort(key=lambda x:(-x[0],-x[1],x[2])); return [x[2] for x in scored[:max_rows]]

    def query(self,intent):
        self._validate(intent); self._refresh(); basis=self.ledger.epoch; state_hash=self.ledger.semantic_state_hash
        if intent.basis_epoch is not None and int(intent.basis_epoch)!=basis:
            raise StaleEpoch(f'cognitive retrieval basis {intent.basis_epoch}!={basis}')
        if self._epoch!=basis or self._state_hash!=state_hash: raise StaleEpoch('retrieval projection is stale')
        terms=self._expand(' '.join((intent.text,*intent.semantic_hints)))
        allow_s={x.upper() for x in intent.statuses}; allow_e={x.upper() for x in intent.epistemic}
        ranked=self._candidate_ranks(terms,max(intent.limit*8,64)); scores={}; receipts={}
        for n,ref in enumerate(ranked,1):
            row=self._rows.get(ref)
            if row is None or row['status'].upper() not in allow_s or row['epistemic'].upper() not in allow_e: continue
            score=1.0/n; scores[ref]=score; receipts[ref]={'base_rank':n,'base_score':score,
                'candidate_generator':'SQLITE_FTS5_RANK' if self._fts_available else 'TOKEN_OVERLAP_FALLBACK'}
        graph_used=intent.target_mode=='CONNECTED_TARGET'
        if graph_used:
            qterms=set(terms)
            for anchor in intent.anchor_refs:
                if anchor not in self._rows: continue
                if anchor in scores: scores[anchor]*=.35; receipts.setdefault(anchor,{})['anchor_factor']=.35
                residual=qterms-self._doc_tokens.get(anchor,set())
                for target,relation,weight,direction,edge_prov in self._adj.get(anchor,()):
                    row=self._rows.get(target)
                    if row is None or row['status'].upper() not in allow_s or row['epistemic'].upper() not in allow_e: continue
                    th=len(residual&self._doc_tokens.get(target,set())); rh=len(qterms&set(_tokens(relation)))
                    boost=.52*weight+.07*min(th,5)+.06*min(rh,3); scores[target]=scores.get(target,0)+boost
                    r=receipts.setdefault(target,{}); r['graph_boost']=r.get('graph_boost',0)+boost
                    r['graph_path']=(anchor,relation,target,direction); r['graph_edge_provenance_ref']=edge_prov
                    r['residual_hits']=th; r['relation_hits']=rh
        ordered=sorted(scores.items(),key=lambda x:(-x[1],x[0])); out=[]
        for ref,score in ordered[:intent.limit]:
            row=self._rows[ref]; rec=receipts.get(ref,{}); path=rec.get('graph_path')
            out.append(CognitiveResult(ref,row['domain'],row['key'],row['value'],row['epistemic'],row['status'],
                row['semantic_hash'],score,rec.get('base_rank'),tuple(path) if path else None,rec,self._provenance.get(ref,{})))
        if self.ledger.epoch!=basis or self.ledger.semantic_state_hash!=state_hash:
            raise StaleEpoch('semantic state changed during cognitive retrieval')
        body=asdict(intent); body['basis_epoch']=basis
        return CognitiveRetrievalReceipt(intent.query_id,basis,state_hash,h(body),tuple(out),len(ordered)>intent.limit,graph_used)
