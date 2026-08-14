from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .state_ledger import StateLedger, StaleEpoch, h

@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    domains: tuple[str, ...] = ()
    keys: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ('CURRENT',)
    epistemic: tuple[str, ...] = ('KNOWN','UNKNOWN','CONFLICT')
    limit: int = 64
    basis_epoch: int | None = None
    purpose: str = 'COGNITIVE_RETRIEVAL'

@dataclass(frozen=True)
class QueryReceipt:
    query_id: str
    basis_epoch: int
    semantic_state_hash: str
    query_hash: str
    row_hashes: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    truncated: bool
    authority: str = 'OBSERVATION_ONLY'

@dataclass(frozen=True)
class SelectionPolicy:
    allow_epistemic: tuple[str, ...] = ('KNOWN',)
    allow_status: tuple[str, ...] = ('CURRENT',)
    max_items: int = 12
    include_conflicts: bool = False

class UnifiedDBQueryPlane:
    """Typed logical read/selection surface over the canonical H1 StateLedger.

    This is deliberately not a second store. Every read is derived from the ledger at
    one semantic epoch and returns a provenance/hash-bearing receipt.

    Bounded reads are pushed into SQLite so Clay does not materialize/decode the entire
    semantic state on every query. A conservative legacy fallback preserves behavior for
    unusually large filter sets or alternate ledger implementations.
    """
    _FAST_PATH_MAX_BOUND_FILTER_VALUES = 800

    def __init__(self, ledger: StateLedger):
        self.ledger = ledger

    @staticmethod
    def _add_sql_filter(column: str, values: tuple[Any, ...], where: list[str], args: list[Any]):
        if not values:
            return
        if len(values) == 1:
            where.append(f'{column}=?')
            args.append(values[0])
            return
        where.append(f"{column} IN ({','.join('?' for _ in values)})")
        args.extend(values)

    @staticmethod
    def _decode_state_row(row) -> dict[str, Any]:
        return {
            'domain': row['domain'],
            'key': row['k'],
            'value': json.loads(row['value_json']) if row['value_json'] is not None else None,
            'epistemic': row['epistemic'],
            'status': row['status'],
            'domain_epoch': int(row['domain_epoch']),
            'semantic_hash': row['semantic_hash'],
        }

    def _query_rows_legacy(self, spec: QuerySpec):
        rows = []
        domains = set(spec.domains)
        keys = set(spec.keys)
        statuses = {x.upper() for x in spec.statuses}
        epistemic = {x.upper() for x in spec.epistemic}
        for row in self.ledger.materialized():
            if domains and row['domain'] not in domains:
                continue
            if keys and row['key'] not in keys:
                continue
            if row['status'].upper() not in statuses:
                continue
            if row['epistemic'].upper() not in epistemic:
                continue
            rows.append(row)
        rows.sort(key=lambda x: (x['domain'], x['key'], x['domain_epoch'], x['semantic_hash']))
        return rows[:spec.limit], len(rows) > spec.limit

    def _query_rows_fast(self, spec: QuerySpec):
        # These two filters are mandatory in the legacy semantics: an empty allowed set
        # means no row is admissible, unlike empty domains/keys which mean unrestricted.
        statuses = tuple(dict.fromkeys(x.upper() for x in spec.statuses))
        epistemic = tuple(dict.fromkeys(x.upper() for x in spec.epistemic))
        if not statuses or not epistemic:
            return [], False

        domains = tuple(dict.fromkeys(spec.domains))
        keys = tuple(dict.fromkeys(spec.keys))
        bound_values = len(domains) + len(keys) + len(statuses) + len(epistemic)
        if bound_values > self._FAST_PATH_MAX_BOUND_FILTER_VALUES or not hasattr(self.ledger, 'conn'):
            return self._query_rows_legacy(spec)

        where: list[str] = []
        args: list[Any] = []
        self._add_sql_filter('domain', domains, where, args)
        self._add_sql_filter('k', keys, where, args)
        self._add_sql_filter('status', statuses, where, args)
        self._add_sql_filter('epistemic', epistemic, where, args)

        sql = (
            'SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash '
            'FROM state'
        )
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        sql += (
            ' ORDER BY domain COLLATE BINARY,k COLLATE BINARY,domain_epoch,'
            'semantic_hash COLLATE BINARY LIMIT ?'
        )
        args.append(spec.limit + 1)
        raw = list(self.ledger.conn.execute(sql, args))
        truncated = len(raw) > spec.limit
        chosen = [self._decode_state_row(r) for r in raw[:spec.limit]]
        return chosen, truncated

    def query(self, spec: QuerySpec) -> QueryReceipt:
        if not spec.query_id.strip():
            raise ValueError('query_id required')
        if spec.limit <= 0 or spec.limit > 4096:
            raise ValueError('invalid query limit')
        basis = self.ledger.epoch
        if spec.basis_epoch is not None and int(spec.basis_epoch) != basis:
            raise StaleEpoch(f'query basis {spec.basis_epoch}!={basis}')
        chosen, truncated = self._query_rows_fast(spec)
        qbody = asdict(spec)
        qbody['basis_epoch'] = basis
        return QueryReceipt(
            query_id=spec.query_id,
            basis_epoch=basis,
            semantic_state_hash=self.ledger.semantic_state_hash,
            query_hash=h(qbody),
            row_hashes=tuple(x['semantic_hash'] for x in chosen),
            rows=tuple(chosen),
            truncated=truncated,
        )

    def select_for_assembly(self, receipt: QueryReceipt, policy: SelectionPolicy = SelectionPolicy()):
        if receipt.basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f'selection basis {receipt.basis_epoch}!={self.ledger.epoch}')
        if receipt.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch('selection semantic state hash changed')
        allowed_e = {x.upper() for x in policy.allow_epistemic}
        allowed_s = {x.upper() for x in policy.allow_status}
        selected = []
        conflicts = []
        for row in receipt.rows:
            if row['status'].upper() not in allowed_s:
                continue
            if row['epistemic'].upper() == 'CONFLICT':
                conflicts.append(row)
                if not policy.include_conflicts:
                    continue
            elif row['epistemic'].upper() not in allowed_e:
                continue
            selected.append({
                'domain': row['domain'],
                'key': row['key'],
                'value': row['value'],
                'epistemic': row['epistemic'],
                'status': row['status'],
                'source_semantic_hash': row['semantic_hash'],
                'domain_epoch': row['domain_epoch'],
                'authority': 'CONTEXT_ONLY',
            })
            if len(selected) >= policy.max_items:
                break
        return {
            'basis_epoch': receipt.basis_epoch,
            'query_hash': receipt.query_hash,
            'selected': selected,
            'conflicts_present': len(conflicts),
            'selection_hash': h({'basis_epoch':receipt.basis_epoch,'query_hash':receipt.query_hash,'selected':selected}),
            'authority': 'ASSEMBLY_CONTEXT_ONLY',
        }

    def transact(self, *, event_id: str, idem: str, base_epoch: int, event_type: str,
                 writer: str, ops: Iterable[dict[str, Any]], provenance=None, source=None, execution=None):
        return self.ledger.append_event(
            event_id=event_id, idem=idem, base_epoch=base_epoch, event_type=event_type,
            writer=writer, ops=list(ops), provenance=provenance, source=source, execution=execution,
        )

    def capability_view(self):
        """Disposable possibility/capability projection; never canonical truth by itself."""
        spec = QuerySpec(
            query_id=f'capability-view-{self.ledger.epoch}',
            domains=('capability','peer'),
            statuses=('CURRENT',),
            epistemic=('KNOWN','UNKNOWN','CONFLICT'),
            limit=128,
            basis_epoch=self.ledger.epoch,
            purpose='DERIVED_CAPABILITY_VIEW',
        )
        r = self.query(spec)
        view = []
        for row in r.rows:
            view.append({
                'identity': f"{row['domain']}:{row['key']}",
                'epistemic': row['epistemic'],
                'semantic_hash': row['semantic_hash'],
                'value': row['value'],
            })
        return {
            'basis_epoch': r.basis_epoch,
            'semantic_state_hash': r.semantic_state_hash,
            'items': view,
            'derived': True,
            'persistent_second_store': False,
            'authority': 'NON_AUTHORITATIVE_PROJECTION',
            'view_hash': h({'basis_epoch':r.basis_epoch,'items':view}),
        }
