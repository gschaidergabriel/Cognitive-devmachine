from __future__ import annotations

import unittest

from .adaptive_semantic_backend_router_v1 import (
    AdaptiveSemanticBackendRouterV1, BackendEvidence, QueryClass, QueryEnvelope,
    RoutePolicy, RouteStatus,
)


def ev(name,*classes,epoch=7,p50=10.0,hit=1.0,recall=1.0,all5=1.0,ndcg=1.0,
       verified=True,prov=True,ann=None,prod_embed=False,authority='CONTEXT_ONLY_NO_EFFECT_AUTHORITY'):
    return BackendEvidence(
        backend_id=name,query_classes=frozenset(classes),measured_epoch=epoch,
        verified=verified,provenance_valid=prov,evidence_class='TEST',p50_us=p50,
        hit_at_1=hit,recall_at_5=recall,all_evidence_at_5=all5,ndcg_at_5=ndcg,
        ann_recall_at_5_vs_exact=ann,production_embedding_validated=prod_embed,
        authority=authority,
    )


def q(qclass,**kw):
    return QueryEnvelope('q',qclass,basis_epoch=kw.pop('basis_epoch',7),current_epoch=kw.pop('current_epoch',7),**kw)


class AdaptiveBackendRouterTests(unittest.TestCase):
    def setUp(self): self.r=AdaptiveSemanticBackendRouterV1()

    def test_direct_keyed_chooses_faster_equal_quality_sql_not_graph(self):
        d=self.r.route(q(QueryClass.DIRECT_KEYED),[
            ev('SQL_KEYED',QueryClass.DIRECT_KEYED,p50=4),
            ev('GRAPH_POINT',QueryClass.DIRECT_KEYED,p50=18),
        ])
        self.assertEqual((d.status,d.selected_backend),(RouteStatus.SELECTED,'SQL_KEYED'))

    def test_multihop_prefers_complete_graph_even_when_slower(self):
        d=self.r.route(q(QueryClass.RELATIONAL_MULTIHOP),[
            ev('FTS_FAST',QueryClass.RELATIONAL_MULTIHOP,p50=5,recall=.95,all5=.95,ndcg=.92),
            ev('CLAY_GRAPH',QueryClass.RELATIONAL_MULTIHOP,p50=40,recall=1,all5=1,ndcg=1),
        ])
        self.assertEqual(d.selected_backend,'CLAY_GRAPH')

    def test_equal_multihop_quality_chooses_lower_latency_backend(self):
        d=self.r.route(q(QueryClass.RELATIONAL_MULTIHOP),[
            ev('SQL_RECURSIVE',QueryClass.RELATIONAL_MULTIHOP,p50=30),
            ev('GRAPH_NATIVE',QueryClass.RELATIONAL_MULTIHOP,p50=12),
        ])
        self.assertEqual(d.selected_backend,'GRAPH_NATIVE')

    def test_production_vector_query_rejects_proxy_embedding(self):
        d=self.r.route(q(QueryClass.VECTOR_SEMANTIC,requires_production_embedding=True),[
            ev('PGVECTOR_PROXY',QueryClass.VECTOR_SEMANTIC,p50=8,recall=1,ann=1,prod_embed=False)
        ])
        self.assertEqual(d.status,RouteStatus.ABSTAIN)
        self.assertIn(('PGVECTOR_PROXY','PROXY_OR_UNVALIDATED_EMBEDDING'),d.rejected)

    def test_ann_below_exact_recall_floor_is_rejected(self):
        d=self.r.route(q(QueryClass.VECTOR_SEMANTIC),[
            ev('HNSW_BAD',QueryClass.VECTOR_SEMANTIC,p50=2,recall=.99,ann=.80,prod_embed=True),
            ev('EXACT',QueryClass.VECTOR_SEMANTIC,p50=20,recall=.99,ann=None,prod_embed=True),
        ])
        self.assertEqual(d.selected_backend,'EXACT')
        self.assertIn(('HNSW_BAD','ANN_RECALL_BELOW_EXACT_ORACLE_FLOOR'),d.rejected)

    def test_stale_measurement_cannot_win_by_speed(self):
        d=self.r.route(q(QueryClass.LEXICAL),[
            ev('STALE_FAST',QueryClass.LEXICAL,epoch=6,p50=1),
            ev('CURRENT_SLOW',QueryClass.LEXICAL,epoch=7,p50=9),
        ])
        self.assertEqual(d.selected_backend,'CURRENT_SLOW')
        self.assertIn(('STALE_FAST','STALE_MEASUREMENT_EPOCH'),d.rejected)

    def test_invalid_provenance_and_unverified_evidence_rejected(self):
        d=self.r.route(q(QueryClass.LEXICAL),[
            ev('SHUFFLED',QueryClass.LEXICAL,prov=False,p50=1),
            ev('UNVERIFIED',QueryClass.LEXICAL,verified=False,p50=1),
            ev('TRUTHFUL',QueryClass.LEXICAL,p50=10),
        ])
        self.assertEqual(d.selected_backend,'TRUTHFUL')
        self.assertEqual(dict(d.rejected)['SHUFFLED'],'INVALID_PROVENANCE')
        self.assertEqual(dict(d.rejected)['UNVERIFIED'],'UNVERIFIED_EVIDENCE')

    def test_backend_cannot_smuggle_effect_authority(self):
        d=self.r.route(q(QueryClass.DIRECT_KEYED),[
            ev('BAD_AUTH',QueryClass.DIRECT_KEYED,p50=.1,authority='MAY_EXECUTE_EFFECTS'),
            ev('SAFE',QueryClass.DIRECT_KEYED,p50=5),
        ])
        self.assertEqual(d.selected_backend,'SAFE')
        self.assertIn(('BAD_AUTH','BACKEND_AUTHORITY_ESCALATION_FORBIDDEN'),d.rejected)

    def test_query_conflict_blocks_all_backend_selection(self):
        d=self.r.route(q(QueryClass.COUNTEREVIDENCE_CLOSURE,conflict=True),[
            ev('GRAPH',QueryClass.COUNTEREVIDENCE_CLOSURE,p50=1)
        ])
        self.assertEqual((d.status,d.selected_backend),(RouteStatus.BLOCKED_CONFLICT,None))

    def test_stale_query_basis_blocks_even_current_backend(self):
        d=self.r.route(q(QueryClass.DIRECT_KEYED,basis_epoch=6,current_epoch=7),[
            ev('SQL',QueryClass.DIRECT_KEYED,p50=1)
        ])
        self.assertEqual(d.status,RouteStatus.BLOCKED_STALE_BASIS)

    def test_no_global_engine_rank_exists_across_query_classes(self):
        sql=ev('SQL',QueryClass.DIRECT_KEYED,QueryClass.LEXICAL,p50=2)
        graph=ev('GRAPH',QueryClass.RELATIONAL_MULTIHOP,p50=20)
        self.assertEqual(self.r.route(q(QueryClass.DIRECT_KEYED),[sql,graph]).selected_backend,'SQL')
        self.assertEqual(self.r.route(q(QueryClass.RELATIONAL_MULTIHOP),[sql,graph]).selected_backend,'GRAPH')


if __name__=='__main__': unittest.main(verbosity=2)
