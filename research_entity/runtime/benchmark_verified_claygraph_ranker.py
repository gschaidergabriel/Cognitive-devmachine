from __future__ import annotations

import json
import math
import platform
import random
import sqlite3
import statistics
import time
from dataclasses import dataclass

from verified_claygraph_ranker import VerifiedClayGraphRanker


@dataclass(frozen=True)
class Case:
    name: str
    anchor: str
    target: str
    distractor: str
    relation: str
    query: str
    target_text: str
    distractor_text: str


CASES = (
    Case('needle_effect','organ:needle','authority:effect_gateway','memory:tool_trace','routes_to',
         'Needle route downstream component commit verified external effects',
         'Effect gateway commit verified external effects with authority receipt',
         'Tool trace stores routing observations and tool history'),
    Case('gwt_receiver','gwt:broadcast','gwt:receiver_use','gwt:candidate_pool','delivers_to',
         'broadcast downstream receiver reconstruct use local effect',
         'Receiver reconstruct broadcast use signal and produce local effect receipt',
         'Candidate pool competes before ignition and broadcast'),
    Case('reentry_receipt','memory:episode','memory:reentry_receipt','memory:retrieval_cache','reenters_via',
         'episode downstream provenance bound reentry receipt causal identity',
         'Reentry receipt binds episode signal causal identity and provenance',
         'Retrieval cache holds recently activated memory candidates'),
    Case('graph_projection','graph:versioned_edge','graph:projection_receipt','graph:adjacency_cache','projects_via',
         'versioned edge downstream verified equal projection receipt current head',
         'Projection receipt verifies current head equal to versioned authoritative edge state',
         'Adjacency cache accelerates neighboring edge lookup'),
    Case('udb_epoch','udb:event','udb:state_epoch','udb:query_cache','advances',
         'event downstream semantic state epoch transaction replay boundary',
         'State epoch binds semantic transaction replay boundary and state hash',
         'Query cache stores repeated materialized reads'),
    Case('work_receipt','work:lease','work:completion_receipt','work:queue_hint','closes_with',
         'lease downstream completion receipt evidence worker result',
         'Completion receipt records worker result evidence and closes leased revision',
         'Queue hint suggests possibly useful future work'),
    Case('visual_candidate','visual:percept','gwt:visual_candidate','visual:feature_cache','feeds',
         'percept downstream workspace candidate attention ignition visual evidence',
         'Visual candidate carries percept evidence into attention and workspace ignition',
         'Feature cache stores visual backbone features'),
    Case('recovery_lkg','recovery:failure','recovery:last_known_good','recovery:retry_counter','recovers_via',
         'failure downstream last known good rollback verified recovery',
         'Last known good checkpoint supports rollback and verified recovery',
         'Retry counter limits bounded transient retries'),
    Case('stagnation_guard','loop:residual_pressure','loop:stagnation_guard','loop:cadence_timer','controls',
         'residual pressure downstream stagnation guard false halt unresolved error',
         'Stagnation guard detects low delta with unresolved error and prevents false halt',
         'Cadence timer schedules ordinary recurrent loop timing'),
    Case('hyper_selection','hyperposition:alternative','hyperposition:selection_receipt','hyperposition:layout','resolves_via',
         'alternative downstream selection receipt competing route resolved evidence',
         'Selection receipt records evidence resolving competing route alternatives',
         'Layout projection displays unresolved alternatives'),
    Case('provenance_record','provenance:source','provenance:evidence_record','provenance:index','materializes_as',
         'source downstream evidence record retrieval time evidence class confidence',
         'Evidence record stores retrieval time evidence class confidence and source lineage',
         'Provenance index accelerates source identifier lookup'),
    Case('worker_claim','capability:worker','work:best_fit_claim','work:presence_ping','claims',
         'worker downstream best fit claim lease capability impact collision avoidance',
         'Best fit claim binds capability impact lease and collision avoidance decision',
         'Presence ping says worker is currently active'),
)


def percentile(values, p):
    values = sorted(values)
    pos = (len(values)-1)*p
    lo = int(pos)
    hi = min(lo+1,len(values)-1)
    frac = pos-lo
    return values[lo]*(1-frac)+values[hi]*frac


def setup():
    db=sqlite3.connect(':memory:')
    db.row_factory=sqlite3.Row
    db.executescript('''
      CREATE VIRTUAL TABLE docs USING fts5(ref UNINDEXED, body, tokenize='unicode61 remove_diacritics 2');
      CREATE TABLE graph_epochs(graph_epoch INTEGER,source_epoch INTEGER,status TEXT);
      CREATE TABLE graph_head_edges(logical_edge_id TEXT,graph_epoch INTEGER);
      CREATE TABLE graph_current_projection_receipts(graph_epoch INTEGER,source_epoch INTEGER,verified_equal INTEGER,created_at TEXT);
      CREATE TABLE amb(logical_edge_id TEXT,graph_epoch INTEGER,version_count INTEGER);
      CREATE VIEW v_graph_projection_ambiguous_edge_epochs AS SELECT * FROM amb;
      CREATE TABLE heads(logical_edge_id TEXT,source_logical_id TEXT,target_logical_id TEXT,relation_type TEXT,weight REAL,confidence REAL,graph_epoch INTEGER);
      CREATE VIEW v_graph_current_edges_fast AS SELECT * FROM heads;
    ''')
    db.execute("INSERT INTO graph_epochs VALUES(16,16,'CURRENT')")
    db.execute("INSERT INTO graph_current_projection_receipts VALUES(16,16,1,'fixture')")
    text={}
    for i,c in enumerate(CASES):
        anchor_text=f'{c.anchor} anchor current Clay semantic node'
        text[c.anchor]=anchor_text
        text[c.target]=c.target_text
        text[c.distractor]=c.distractor_text
        for ref,body in ((c.anchor,anchor_text),(c.target,c.target_text),(c.distractor,c.distractor_text)):
            db.execute('INSERT INTO docs VALUES(?,?)',(ref,body))
        # 3 of 12 cases deliberately omit a lexical decoy; the others contain an unstructured
        # current note that is lexically stronger but is not the graph target of the anchor.
        if i not in (0,4,8):
            decoy=f'doc:lexical_decoy_{i:02d}'
            text[decoy]=f'{c.query} {c.query} descriptive note only, not the target relation'
            db.execute('INSERT INTO docs VALUES(?,?)',(decoy,text[decoy]))
        # Four cases give plain weight ordering the correct edge; eight make a generic high-weight
        # neighbor win unless the query semantics are used.
        correct_weight=0.99 if i%3==0 else 0.80
        distractor_weight=0.82 if i%3==0 else 0.98
        for suffix,target,weight in (('t',c.target,correct_weight),('d',c.distractor,distractor_weight)):
            edge=f'e{i:02d}{suffix}'
            db.execute('INSERT INTO graph_head_edges VALUES(?,16)',(edge,))
            db.execute('INSERT INTO heads VALUES(?,?,?,?,?,?,16)',
                       (edge,c.anchor,target,c.relation,weight,1.0))
    db.commit()
    ranker=VerifiedClayGraphRanker(
        db,
        text_for_ref=lambda ref,epoch:text.get(ref,''),
        admissible_ref=lambda ref,epoch: ref in text,
    )
    return db,ranker,text


def fts_rank(db,query,limit=5):
    terms=' '.join('"'+term.replace('"','')+'"' for term in query.split() if len(term)>1)
    # OR is a conventional broad candidate baseline; BM25 determines order.
    expression=' OR '.join(terms.split())
    return [r['ref'] for r in db.execute(
        'SELECT ref FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?', (expression,limit))]


def sql_graph_rank(db,anchor,limit=5):
    rows=db.execute('''
      SELECT CASE WHEN source_logical_id=? THEN target_logical_id ELSE source_logical_id END AS ref,
             weight*COALESCE(confidence,1.0) AS score
      FROM v_graph_current_edges_fast
      WHERE source_logical_id=? OR target_logical_id=?
      ORDER BY score DESC, ref LIMIT ?
    ''',(anchor,anchor,anchor,limit))
    return [r['ref'] for r in rows]


def clay_rank(ranker,c,limit=5):
    return [x.ref for x in ranker.rank(c.anchor,c.query,16,16,limit)]


def evaluate(method):
    ranks=[]
    rows=[]
    for c in CASES:
        got=method(c)
        rank=next((i+1 for i,x in enumerate(got) if x==c.target),None)
        ranks.append(rank)
        rows.append({'case':c.name,'target':c.target,'rank':rank,'top5':got})
    return {
        'n':len(CASES),
        'hit_at_1':sum(r==1 for r in ranks)/len(ranks),
        'mrr':sum(0 if r is None else 1/r for r in ranks)/len(ranks),
        'recall_at_3':sum(r is not None and r<=3 for r in ranks)/len(ranks),
        'failures':[row for row in rows if row['rank']!=1],
        'rows':rows,
    }


def timing(method,repetitions=500):
    jobs=list(CASES)*repetitions
    random.Random(20260810).shuffle(jobs)
    samples=[]
    for c in jobs:
        start=time.perf_counter_ns(); method(c); samples.append((time.perf_counter_ns()-start)/1000.0)
    return {
        'n':len(samples),
        'p50_us':percentile(samples,.50),
        'p95_us':percentile(samples,.95),
        'p99_us':percentile(samples,.99),
        'mean_us':statistics.mean(samples),
        'max_us':max(samples),
    }


def main():
    db,ranker,_=setup()
    methods={
        'sqlite_fts5_bm25':lambda c:fts_rank(db,c.query),
        'plain_sql_graph_weight':lambda c:sql_graph_rank(db,c.anchor),
        'verified_claygraph_query_ranker':lambda c:clay_rank(ranker,c),
    }
    result={
        'schema_version':'1.0',
        'benchmark':'U16_VERIFIED_CLAYGRAPH_RELATION_TARGET_V1',
        'evidence_class':'SYNTHETIC_RELATION_TARGET_ENGINEERING_BENCHMARK',
        'scope':'12 frozen Clay-shaped one-hop relation-target questions; this is not universal database superiority.',
        'environment':{
            'platform':platform.platform(),
            'python':platform.python_version(),
            'sqlite':sqlite3.sqlite_version,
        },
        'fixture':{
            'cases':len(CASES),
            'graph_epoch':16,
            'source_epoch':16,
            'lexical_decoy_cases':9,
            'plain_graph_weight_distractor_cases':8,
        },
        'quality':{name:evaluate(fn) for name,fn in methods.items()},
        'latency':{name:timing(fn) for name,fn in methods.items()},
        'claim_guard':[
            'A conventional database can implement the same typed score and then match the ranker; the measured gain belongs to Clay semantic query composition, not magical storage.',
            'Resolved anchors are supplied by the fixture; automatic entity resolution is not credited here.',
            'Synthetic benchmark evidence does not replace real UnifiedDB/ClayGraph held-out data or Andreas target acceptance.',
        ],
    }
    q=result['quality']
    result['delta']={
        'hit1_vs_fts_pp':100*(q['verified_claygraph_query_ranker']['hit_at_1']-q['sqlite_fts5_bm25']['hit_at_1']),
        'hit1_vs_plain_graph_pp':100*(q['verified_claygraph_query_ranker']['hit_at_1']-q['plain_sql_graph_weight']['hit_at_1']),
    }
    print(json.dumps(result,indent=2,sort_keys=True))
    assert q['verified_claygraph_query_ranker']['hit_at_1'] >= q['sqlite_fts5_bm25']['hit_at_1']
    assert q['verified_claygraph_query_ranker']['hit_at_1'] >= q['plain_sql_graph_weight']['hit_at_1']
    assert q['verified_claygraph_query_ranker']['hit_at_1'] == 1.0
    db.close()


if __name__=='__main__':
    main()
