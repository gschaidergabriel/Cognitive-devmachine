from __future__ import annotations

from .state_ledger import h
from .unifieddb_emergent_incremental import IncrementalEmergentAssemblyPreprocessor
from .unifieddb_emergent_preprocessor import PossibilitySpec
from .unifieddb_emergent_family_factorized import (
    FamilyFactorizedEmergentAssemblyPreprocessor,
)


class SyntheticLedger:
    def __init__(self, rows, epoch=9):
        self._rows = rows
        self.epoch = epoch
        self.semantic_state_hash = h(
            [(r['domain'], r['key'], r['semantic_hash']) for r in rows]
        )

    def materialized(self):
        return self._rows


def row(domain, key, value, *, epoch=9, epistemic='KNOWN', status='CURRENT'):
    semantic_hash = h(
        {
            'domain': domain,
            'key': key,
            'value': value,
            'epistemic': epistemic,
            'status': status,
        }
    )
    return {
        'domain': domain,
        'key': key,
        'value': value,
        'epistemic': epistemic,
        'status': status,
        'domain_epoch': epoch,
        'semantic_hash': semantic_hash,
    }


def fixture_rows(*, typed=True):
    rows = [row('semantic', 'root', {'label': 'root'})]
    values = [
        ('a1', 'family:A', 0.99),
        ('a2', 'family:A', 0.98),
        ('b1', 'family:B', 0.80),
    ]
    for key, family, weight in values:
        value = {'label': key}
        if typed:
            value['possibility_family_id'] = family
        rows.append(row('possibility', key, value))
        rows.append(
            row(
                'dependency',
                f'edge_{key}',
                {
                    'source': 'semantic:root',
                    'target': f'possibility:{key}',
                    'strength': weight,
                    'relation_type': 'POSSIBILITY_BINDING',
                },
            )
        )
    return rows


def spec(**overrides):
    base = dict(
        assembly_id='family-test',
        seed_refs=('semantic:root',),
        allowed_domains=('possibility',),
        max_items=2,
        max_hops=1,
        frontier_budget=32,
        min_edge_weight=0.0,
        basis_epoch=9,
    )
    base.update(overrides)
    return PossibilitySpec(**base)


def test_factorization_recovers_distinct_possibility_family_without_changing_top1():
    ledger = SyntheticLedger(fixture_rows())
    baseline = IncrementalEmergentAssemblyPreprocessor(ledger).compile_active_assembly(spec())
    candidate = FamilyFactorizedEmergentAssemblyPreprocessor(ledger).compile_active_assembly(spec())
    assert [x['ref'] for x in baseline['selected']] == ['possibility:a1', 'possibility:a2']
    assert [x['ref'] for x in candidate['selected']] == ['possibility:a1', 'possibility:b1']
    assert candidate['selected'][0]['ref'] == baseline['selected'][0]['ref']
    assert [x['possibility_family_id'] for x in candidate['selected']] == ['family:A', 'family:B']
    assert candidate['family_factorization_applied'] is True
    assert any(x['ref'] == 'possibility:a2' for x in candidate['family_suppressed'])
    assert candidate['persistent_second_store'] is False
    assert candidate['authority'] == 'ASSEMBLY_CONTEXT_ONLY'


def test_missing_family_metadata_never_heuristically_merges_rows():
    ledger = SyntheticLedger(fixture_rows(typed=False))
    candidate = FamilyFactorizedEmergentAssemblyPreprocessor(ledger).compile_active_assembly(spec())
    assert [x['ref'] for x in candidate['selected']] == ['possibility:a1', 'possibility:a2']
    assert all(x['possibility_family_explicit'] is False for x in candidate['selected'])


def test_lexical_query_path_is_byte_selection_compatible_with_incremental_eap():
    ledger = SyntheticLedger(fixture_rows())
    lexical = spec(query_text='root family possibility')
    baseline = IncrementalEmergentAssemblyPreprocessor(ledger).compile_active_assembly(lexical)
    candidate = FamilyFactorizedEmergentAssemblyPreprocessor(ledger).compile_active_assembly(lexical)
    assert candidate['family_factorization_applied'] is False
    assert candidate['family_factorization_reason'] == 'LEXICAL_QUERY_PATH_UNCHANGED'
    assert candidate['selection_hash'] == baseline['selection_hash']
    assert [x['ref'] for x in candidate['selected']] == [x['ref'] for x in baseline['selected']]


def test_max_per_family_two_preserves_two_bindings_when_policy_requests_it():
    ledger = SyntheticLedger(fixture_rows())
    candidate = FamilyFactorizedEmergentAssemblyPreprocessor(
        ledger, max_per_family=2
    ).compile_active_assembly(spec())
    assert [x['ref'] for x in candidate['selected']] == ['possibility:a1', 'possibility:a2']


if __name__ == '__main__':
    tests = [
        test_factorization_recovers_distinct_possibility_family_without_changing_top1,
        test_missing_family_metadata_never_heuristically_merges_rows,
        test_lexical_query_path_is_byte_selection_compatible_with_incremental_eap,
        test_max_per_family_two_preserves_two_bindings_when_policy_requests_it,
    ]
    for test in tests:
        test()
    print(f'PASS {len(tests)} tests')
