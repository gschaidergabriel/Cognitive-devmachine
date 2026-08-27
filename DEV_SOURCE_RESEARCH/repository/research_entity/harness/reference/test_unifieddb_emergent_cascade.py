import unittest
from dataclasses import dataclass

from .state_ledger import StateLedger, StaleEpoch
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import UnifiedDBEmergentPlane
from .unifieddb_emergent_cascade import FailClosedEmergentRetrievalCascade, EmergentCascadeSpec


@dataclass(frozen=True)
class Resolution:
    logical_id: str | None
    resolution_class: str
    confidence: float
    candidates: tuple[str, ...] = ()
    latency_ns: int = 10


class Resolver:
    def __init__(self, resolution):
        self.resolution = resolution
    def resolve(self, text, *, source_epoch):
        return self.resolution


class EmergentCascadeTests(unittest.TestCase):
    def make(self, resolution):
        ledger = StateLedger()
        plane = UnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger))
        plane.transact(
            event_id='cascade-seed', idem='cascade-seed', base_epoch=0,
            event_type='CASCADE_SEED', writer='test', ops=[
                {'op':'SET','domain':'semantic','key':'anchor','value':{'label':'anchor'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'target','value':{'label':'target'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'edge','value':{'source':'semantic:anchor','target':'semantic:target','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        cascade = FailClosedEmergentRetrievalCascade(
            resolver=Resolver(resolution),
            preprocessor=plane.preprocessor,
            logical_to_ref=lambda logical_id: {'component_anchor':'semantic:anchor'}.get(logical_id),
        )
        return ledger, cascade

    def test_evidence_alias_opens_bounded_assembly(self):
        ledger, cascade = self.make(Resolution('component_anchor','EVIDENCE_ALIAS',0.96,('component_anchor',)))
        out = cascade.retrieve(EmergentCascadeSpec('q','please inspect the amber relay',ledger.epoch,max_items=2))
        self.assertFalse(out['blocked'])
        self.assertEqual(out['seed_ref'],'semantic:anchor')
        self.assertEqual([x['ref'] for x in out['assembly']['selected']],['semantic:anchor','semantic:target'])
        self.assertFalse(out['persistent_second_store'])
        ledger.close()

    def test_exact_logical_id_is_admitted(self):
        ledger, cascade = self.make(Resolution('component_anchor','EXACT_LOGICAL_ID',1.0,('component_anchor',)))
        out = cascade.retrieve(EmergentCascadeSpec('q','component_anchor',ledger.epoch,max_items=2))
        self.assertFalse(out['blocked'])
        ledger.close()

    def test_ambiguous_resolution_never_starts_graph(self):
        ledger, cascade = self.make(Resolution(None,'AMBIGUOUS',0.91,('component_anchor','component_other')))
        out = cascade.retrieve(EmergentCascadeSpec('q','amber',ledger.epoch,max_items=2))
        self.assertTrue(out['blocked'])
        self.assertEqual(out['block_reason'],'RESOLUTION_NOT_ADMITTED')
        self.assertIsNone(out['assembly'])
        ledger.close()

    def test_low_confidence_resolution_never_starts_graph(self):
        ledger, cascade = self.make(Resolution(None,'LOW_CONFIDENCE',0.41,('component_anchor',)))
        out = cascade.retrieve(EmergentCascadeSpec('q','maybe amber thing',ledger.epoch,max_items=2))
        self.assertTrue(out['blocked'])
        self.assertIsNone(out['assembly'])
        ledger.close()

    def test_misclassified_low_confidence_alias_is_still_blocked(self):
        ledger, cascade = self.make(Resolution('component_anchor','EVIDENCE_ALIAS',0.52,('component_anchor',)))
        out = cascade.retrieve(EmergentCascadeSpec('q','resolver bug',ledger.epoch,max_items=2))
        self.assertTrue(out['blocked'])
        self.assertEqual(out['block_reason'],'RESOLUTION_CONFIDENCE_BELOW_CASCADE_GATE')
        self.assertIsNone(out['assembly'])
        ledger.close()

    def test_selected_id_missing_from_candidates_is_blocked(self):
        ledger, cascade = self.make(Resolution('component_anchor','EVIDENCE_ALIAS',0.96,('component_other',)))
        out = cascade.retrieve(EmergentCascadeSpec('q','inconsistent resolver',ledger.epoch,max_items=2))
        self.assertTrue(out['blocked'])
        self.assertEqual(out['block_reason'],'RESOLUTION_SELECTED_ID_NOT_IN_CANDIDATES')
        self.assertIsNone(out['assembly'])
        ledger.close()

    def test_invalid_cascade_confidence_threshold_rejected(self):
        ledger, cascade = self.make(Resolution('component_anchor','EVIDENCE_ALIAS',0.96,('component_anchor',)))
        with self.assertRaises(ValueError):
            cascade.retrieve(EmergentCascadeSpec('q','amber relay',ledger.epoch,min_resolution_confidence=1.2))
        ledger.close()

    def test_unbound_logical_id_fails_closed(self):
        ledger, cascade = self.make(Resolution('unknown_component','EVIDENCE_ALIAS',0.99,('unknown_component',)))
        out = cascade.retrieve(EmergentCascadeSpec('q','unknown component',ledger.epoch,max_items=2))
        self.assertTrue(out['blocked'])
        self.assertEqual(out['block_reason'],'LOGICAL_ID_NOT_BOUND_TO_CURRENT_UNIFIEDDB_REF')
        ledger.close()

    def test_stale_source_epoch_rejected_before_resolution(self):
        ledger, cascade = self.make(Resolution('component_anchor','EVIDENCE_ALIAS',0.96,('component_anchor',)))
        with self.assertRaises(StaleEpoch):
            cascade.retrieve(EmergentCascadeSpec('q','amber relay',ledger.epoch-1,max_items=2))
        ledger.close()


if __name__ == '__main__':
    unittest.main()
