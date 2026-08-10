import os
import tempfile
import unittest

from unifieddb_claygraph_retrieval_candidate import (
    MAX_LIVE_FANOUT,
    ProjectionBasis,
    StaleRetrievalProjection,
    UnifiedDBClayGraphRetrievalCandidate,
)


class RetrievalCandidateTests(unittest.TestCase):
    def make(self, path=":memory:"):
        rows = []

        def row(key, lid, kind, ep, text):
            return {
                "domain": "semantic",
                "key": key,
                "value": {
                    "logical_id": lid,
                    "record_kind": kind,
                    "evidence_class": ep,
                    "search_text": text,
                },
                "epistemic": "KNOWN",
                "status": "CURRENT",
                "domain_epoch": 7,
                "semantic_hash": "h-" + key,
            }

        rows += [
            row("cur", "component_a", "component_state", "VERIFIED", "component_a zxalpha active current owner team_a stable mode mode_7"),
            row("svc", "service_b", "service_fact", "VALIDATED", "service_b provides capability cap_beta through interface iface_beta"),
            row("res", "resource_c", "resource_fact", "VALIDATED", "resource_c supplies resource quota_gamma for downstream chain"),
            row("hyp", "component_a_hyp", "claim", "HYPOTHESIS", "component_a zxalpha allegedly owned by speculative_team; unverified hypothesis"),
            row("de", "prüfung_a", "verification_fact", "VERIFIED", "Größenprüfung Überprüfung zuverlässig österreichische Straße"),
        ]
        edges = [
            {"source_logical_id": "component_a", "target_logical_id": "service_b", "relation_type": "REQUIRES", "weight": 0.97, "confidence": 0.98, "causal_class": "CAUSAL"},
            {"source_logical_id": "service_b", "target_logical_id": "resource_c", "relation_type": "DEPENDS_ON", "weight": 0.95, "confidence": 0.97, "causal_class": "CAUSAL"},
        ]
        basis = ProjectionBasis(7, "statehash", 4, True, True)
        x = UnifiedDBClayGraphRetrievalCandidate(path)
        x.rebuild(state_rows=rows, graph_edges=edges, basis=basis)
        return x, basis

    def top(self, x, b, text, graph=True):
        return x.query(query_id="q", text=text, basis=b, graph_enabled=graph).results[0].record_id

    def test_direct_current(self):
        x, b = self.make()
        self.assertEqual(self.top(x, b, "What is the current stable mode of component_a zxalpha?"), "h-cur")
        x.close()

    def test_provenance_beats_hypothesis(self):
        x, b = self.make()
        self.assertEqual(self.top(x, b, "Which verified owner is confirmed for component_a zxalpha?"), "h-cur")
        x.close()

    def test_one_hop(self):
        x, b = self.make()
        self.assertEqual(self.top(x, b, "Which capability is provided by the service that component_a requires?"), "h-svc")
        x.close()

    def test_two_hop(self):
        x, b = self.make()
        self.assertEqual(self.top(x, b, "Which resource ultimately supports component_a through its required service chain?"), "h-res")
        x.close()

    def test_german_two_hop_intent(self):
        x, b = self.make()
        self.assertEqual(self.top(x, b, "Welche Ressource unterstützt component_a über seine benötigte Servicekette?"), "h-res")
        x.close()

    def test_unicode_lexical_tokens_are_not_ascii_fragments(self):
        x, b = self.make()
        self.assertEqual(x._fts_query("Größenprüfung Überprüfung Straße"), '"größenprüfung" OR "überprüfung" OR "straße"')
        self.assertEqual(self.top(x, b, "Welche Größenprüfung wurde verifiziert?"), "h-de")
        x.close()

    def test_hypothesis_request_preserves_uncertainty(self):
        x, b = self.make()
        self.assertEqual(self.top(x, b, "What speculative ownership hypothesis exists for component_a zxalpha?"), "h-hyp")
        x.close()

    def test_graph_lesion_breaks_graph_retrieval(self):
        x, b = self.make()
        self.assertNotEqual(self.top(x, b, "Which capability is provided by the service that component_a requires?", False), "h-svc")
        x.close()

    def test_unverified_graph_projection_refused(self):
        rows = [{"domain": "semantic", "key": "x", "value": {"logical_id": "x", "search_text": "x"}, "epistemic": "KNOWN", "status": "CURRENT", "domain_epoch": 1, "semantic_hash": "hx"}]
        x = UnifiedDBClayGraphRetrievalCandidate()
        with self.assertRaises(ValueError):
            x.rebuild(state_rows=rows, graph_edges=[], basis=ProjectionBasis(1, "h", 1, True, False))
        x.close()

    def test_stale_basis_rejected(self):
        x, b = self.make()
        with self.assertRaises(StaleRetrievalProjection):
            x.query(query_id="q", text="component_a", basis=ProjectionBasis(8, "other", 4, True, True))
        x.close()

    def test_verified_file_projection_survives_process_reopen(self):
        fd, path = tempfile.mkstemp(prefix="clay-retrieval-", suffix=".db")
        os.close(fd)
        try:
            x, b = self.make(path)
            expected = self.top(x, b, "What is the current stable mode of component_a zxalpha?")
            x.close()
            y = UnifiedDBClayGraphRetrievalCandidate(path)
            self.assertEqual(y.basis, b)
            self.assertEqual(self.top(y, b, "What is the current stable mode of component_a zxalpha?"), expected)
            y.close()
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_incomplete_legacy_metadata_remains_fail_closed_after_reopen(self):
        fd, path = tempfile.mkstemp(prefix="clay-retrieval-old-", suffix=".db")
        os.close(fd)
        try:
            x = UnifiedDBClayGraphRetrievalCandidate(path)
            x.conn.executemany(
                "INSERT OR REPLACE INTO retrieval_projection_meta(key,value) VALUES (?,?)",
                [("source_epoch", "7"), ("semantic_state_hash", "old"), ("graph_epoch", "4")],
            )
            x.conn.commit()
            x.close()
            y = UnifiedDBClayGraphRetrievalCandidate(path)
            self.assertIsNone(y.basis)
            with self.assertRaises(StaleRetrievalProjection):
                y.query(query_id="q", text="anything", basis=ProjectionBasis(7, "old", 4, True, True))
            y.close()
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_high_fanout_is_rank_bounded_and_counterevidence_is_reserved(self):
        rows = []
        edges = []
        for i in range(100):
            lid = f"normal_{i}"
            rows.append({"domain": "semantic", "key": lid, "value": {"logical_id": lid, "search_text": lid}, "epistemic": "KNOWN", "status": "CURRENT", "domain_epoch": 7, "semantic_hash": "h-" + lid})
            edges.append({"source_logical_id": "root", "target_logical_id": lid, "relation_type": "SUPPORTS", "weight": 1.0 - i / 1000.0, "confidence": 1.0})
        rows.append({"domain": "semantic", "key": "counter", "value": {"logical_id": "counter", "search_text": "counter"}, "epistemic": "CONFLICT", "status": "CURRENT", "domain_epoch": 7, "semantic_hash": "h-counter"})
        edges.append({"source_logical_id": "root", "target_logical_id": "counter", "relation_type": "CONTRADICTS", "weight": 0.01, "confidence": 0.2})
        basis = ProjectionBasis(7, "statehash", 4, True, True)
        x = UnifiedDBClayGraphRetrievalCandidate()
        stats = x.rebuild(state_rows=rows, graph_edges=edges, basis=basis)
        admitted = x.conn.execute(
            "SELECT COUNT(*) FROM claygraph_neighbor_cache WHERE source_logical_id='root' AND source_rank<=?",
            (MAX_LIVE_FANOUT,),
        ).fetchone()[0]
        counter_rank = x.conn.execute(
            "SELECT source_rank FROM claygraph_neighbor_cache WHERE source_logical_id='root' AND target_logical_id='counter'"
        ).fetchone()[0]
        self.assertEqual(admitted, MAX_LIVE_FANOUT)
        self.assertLessEqual(counter_rank, MAX_LIVE_FANOUT)
        self.assertEqual(stats["sources_over_cap"], 1)
        self.assertEqual(stats["max_source_degree"], 101)
        x.close()


if __name__ == "__main__":
    unittest.main()
