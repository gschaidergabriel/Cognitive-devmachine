from __future__ import annotations

from .state_ledger import h
from .unifieddb_emergent_incremental import IncrementalEmergentAssemblyPreprocessor
from .unifieddb_emergent_preprocessor import PossibilitySpec
from .unifieddb_emergent_family_factorized_v2 import (
    OnePassFamilyFactorizedEmergentAssemblyPreprocessor,
)


class SyntheticLedger:
    def __init__(self, rows, epoch=19):
        self._rows = rows
        self.epoch = epoch
        self.semantic_state_hash = h(
            [(r['domain'], r['key'], r['semantic_hash']) for r in rows]
        )

    def materialized(self):
        return self._rows


def row(domain, key, value, *, epoch=19):
    semantic_hash = h((domain, key, value))
    return {
        'domain': domain,
        'key': key,
        'value': value,
        'epistemic': 'KNOWN',
        'status': 'CURRENT',
        'domain_epoch': epoch,
        'semantic_hash': semantic_hash,
    }


def fixture(bindings_per_family=8, families=20, *, typed=True):
    rows = [row('semantic', 'root', {'label': 'root'})]
    for family_index in range(families):
        family_id = f'family:{family_index:03d}'
        family_score = 0.999 - family_index * 0.02
        for binding_index in range(bindings_per_family):
            score = family_score - binding_index * 0.00001
            key = f'f{family_index:03d}_b{binding_index:02d}'
            value = {'binding_id': key}
            if typed:
                value['possibility_family_id'] = family_id
            rows.append(row('possibility', key, value))
            rows.append(
                row(
                    'dependency',
                    f'edge_{key}',
                    {
                        'source': 'semantic:root',
                        'target': f'possibility:{key}',
                        'strength': score,
                        'relation_type': 'POSSIBILITY_BINDING',
                    },
                )
            )
    return rows


def spec(**overrides):
    base = dict(
        assembly_id='f2-test',
        seed_refs=('semantic:root',),
        allowed_domains=('possibility',),
        max_items=12,
        max_hops=1,
        frontier_budget=10000,
        min_edge_weight=0.0,
        basis_epoch=19,
    )
    base.update(overrides)
    return PossibilitySpec(**base)


def families(assembly):
    out=[]
    for item in assembly['selected']:
        value=item.get('value')
        family=value.get('possibility_family_id') if isinstance(value,dict) else None
        if family is not None and family not in out:
            out.append(family)
    return out


def test_f2_recovers_twelve_families_at_eight_bindings_each_and_preserves_top1():
    ledger=SyntheticLedger(fixture(bindings_per_family=8,families=20))
    baseline=IncrementalEmergentAssemblyPreprocessor(ledger).compile_active_assembly(spec())
    candidate=OnePassFamilyFactorizedEmergentAssemblyPreprocessor(ledger,pool_cap=4096).compile_active_assembly(spec())
    assert len(families(baseline))==2
    assert len(families(candidate))==12
    assert candidate['selected'][0]['ref']==baseline['selected'][0]['ref']
    assert candidate['pool_exhausted_before_requested_family_budget'] is False
    assert candidate['authority']=='ASSEMBLY_CONTEXT_ONLY'
    assert candidate['persistent_second_store'] is False


def test_f2_cap_exhaustion_is_observable_not_silently_complete():
    ledger=SyntheticLedger(fixture(bindings_per_family=8,families=20))
    candidate=OnePassFamilyFactorizedEmergentAssemblyPreprocessor(ledger,pool_cap=48).compile_active_assembly(spec())
    assert len(families(candidate))==6
    assert candidate['pool_exhausted_before_requested_family_budget'] is True
    assert candidate['candidate_pool_items']==48


def test_missing_family_metadata_never_heuristically_merges():
    ledger=SyntheticLedger(fixture(bindings_per_family=2,families=10,typed=False))
    baseline=IncrementalEmergentAssemblyPreprocessor(ledger).compile_active_assembly(spec(max_items=8))
    candidate=OnePassFamilyFactorizedEmergentAssemblyPreprocessor(ledger,pool_cap=64).compile_active_assembly(spec(max_items=8))
    assert [x['ref'] for x in candidate['selected']]==[x['ref'] for x in baseline['selected']]
    assert all(x['possibility_family_explicit'] is False for x in candidate['selected'])


def test_lexical_path_remains_unmodified():
    ledger=SyntheticLedger(fixture(bindings_per_family=2,families=10))
    lexical=spec(max_items=8,query_text='family binding possibility')
    baseline=IncrementalEmergentAssemblyPreprocessor(ledger).compile_active_assembly(lexical)
    candidate=OnePassFamilyFactorizedEmergentAssemblyPreprocessor(ledger,pool_cap=64).compile_active_assembly(lexical)
    assert candidate['family_factorization_applied'] is False
    assert candidate['selection_hash']==baseline['selection_hash']
    assert [x['ref'] for x in candidate['selected']]==[x['ref'] for x in baseline['selected']]


def test_policy_can_allow_two_bindings_per_family():
    ledger=SyntheticLedger(fixture(bindings_per_family=3,families=10))
    candidate=OnePassFamilyFactorizedEmergentAssemblyPreprocessor(ledger,max_per_family=2,pool_cap=64).compile_active_assembly(spec(max_items=4))
    got=[x['value']['possibility_family_id'] for x in candidate['selected']]
    assert got[:4]==['family:000','family:000','family:001','family:001']


if __name__=='__main__':
    tests=[test_f2_recovers_twelve_families_at_eight_bindings_each_and_preserves_top1,
           test_f2_cap_exhaustion_is_observable_not_silently_complete,
           test_missing_family_metadata_never_heuristically_merges,
           test_lexical_path_remains_unmodified,
           test_policy_can_allow_two_bindings_per_family]
    for test in tests: test()
    print(f'PASS {len(tests)} tests')
