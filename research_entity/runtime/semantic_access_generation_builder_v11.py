"""Two-phase coherent projection builder for U11.

Legacy U11-only deployments retain the original transaction behavior. When ClayGraph V4 is
installed, generation construction becomes fail-closed and provenance-bound: stage/verify/
publish own an immediate write transaction, every projected path is covered by VERIFIED graph
plans, the newest plan-verification receipt must be clean, and the exact plan-path content is
fingerprinted and rechecked before publication.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import sqlite3


class SemanticAccessBusyError(RuntimeError):
    """Integrated semantic-access mutation did not start because another writer owns SQLite."""


@dataclass(frozen=True)
class Path:
    seed_id: str
    target_record_id: str
    target_logical_id: str
    path_rank: int
    hop_count: int
    path_weight: float
    authority_rank: float
    path_clay: str


def _object_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=? LIMIT 1",
        (name,),
    ).fetchone() is not None


def _graph_v4_present(con: sqlite3.Connection) -> bool:
    names = (
        'graph_semantic_access_plans',
        'graph_semantic_access_plan_paths',
        'graph_access_plan_verification_receipts',
    )
    present = tuple(_object_exists(con, n) for n in names)
    if any(present) and not all(present):
        raise ValueError('incomplete ClayGraph V4 plan schema; refusing semantic generation')
    return all(present)


def _binding_schema_present(con: sqlite3.Connection) -> bool:
    return _object_exists(con, 'semantic_access_generation_plan_bindings')


def _generation_has_bindings(con: sqlite3.Connection, generation_id: str) -> bool:
    if not _binding_schema_present(con):
        return False
    return con.execute(
        "SELECT 1 FROM semantic_access_generation_plan_bindings WHERE generation_id=? LIMIT 1",
        (generation_id,),
    ).fetchone() is not None


def _begin_owned_write(con: sqlite3.Connection, operation: str) -> None:
    if con.in_transaction:
        raise ValueError(f'{operation} requires a clean transaction boundary when ClayGraph V4 is integrated')
    try:
        con.execute('BEGIN IMMEDIATE')
    except sqlite3.OperationalError as exc:
        code = getattr(exc, 'sqlite_errorcode', None)
        if code is not None and (int(code) & 0xFF) == sqlite3.SQLITE_BUSY:
            raise SemanticAccessBusyError(
                f'{operation} busy before mutation; safe to retry from fresh state'
            ) from exc
        raise


def _plan_rows(con: sqlite3.Connection, plan_id: str) -> list[tuple]:
    return [
        tuple(r)
        for r in con.execute(
            """SELECT path_id,target_logical_id,path_rank,hop_count,relation_signature,path_weight,
                      admissibility_clay,provenance_clay,counterevidence
               FROM graph_semantic_access_plan_paths
               WHERE plan_id=? ORDER BY path_id""",
            (plan_id,),
        )
    ]


def _plan_paths_hash(rows: list[tuple]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _latest_receipt(con: sqlite3.Connection, plan_id: str):
    return con.execute(
        """SELECT receipt_id,graph_epoch,topology_hash,passed,invalid_path_count,
                  stale_reference_count,missing_counterevidence_count
           FROM graph_access_plan_verification_receipts
           WHERE plan_id=?
           ORDER BY created_at DESC,receipt_id DESC LIMIT 1""",
        (plan_id,),
    ).fetchone()


def _receipt_is_clean(receipt, graph_epoch: int, topology_hash: str) -> bool:
    return bool(
        receipt
        and int(receipt[1]) == int(graph_epoch)
        and str(receipt[2]) == str(topology_hash)
        and int(receipt[3]) == 1
        and int(receipt[4]) == 0
        and int(receipt[5]) == 0
        and int(receipt[6]) == 0
    )


def _seed_set_is_current(
    con: sqlite3.Connection,
    generation_id: str,
    source_epoch: int,
    graph_epoch: int,
    expected: int,
) -> bool:
    actual = con.execute(
        """SELECT COUNT(DISTINCT p.seed_id)
           FROM semantic_access_projection_v11 p
           JOIN semantic_query_seeds s ON s.seed_id=p.seed_id
           WHERE p.generation_id=? AND s.status='CURRENT'
             AND s.source_epoch=? AND (s.graph_epoch IS NULL OR s.graph_epoch=?)""",
        (generation_id, source_epoch, graph_epoch),
    ).fetchone()[0]
    return int(actual) == int(expected)


def _validate_plan_ids(
    con: sqlite3.Connection,
    *,
    source_epoch: int,
    graph_epoch: int,
    path_pairs: set[tuple[str, str]],
    plan_ids: tuple[str, ...],
) -> list[tuple[str, str, str, str, int, int, str]]:
    if not plan_ids:
        raise ValueError('verified_plan_ids required when ClayGraph V4 is present')
    allowed_pairs: set[tuple[str, str]] = set()
    bindings: list[tuple[str, str, str, str, int, int, str]] = []
    for plan_id in tuple(dict.fromkeys(plan_ids)):
        plan = con.execute(
            """SELECT p.seed_id,p.topology_hash,p.selected_path_count
               FROM graph_semantic_access_plans p
               JOIN graph_epochs g ON g.graph_epoch=p.graph_epoch
               WHERE p.plan_id=? AND p.status='VERIFIED'
                 AND p.source_epoch=? AND p.graph_epoch=?
                 AND g.source_epoch=p.source_epoch AND g.status='CURRENT'""",
            (plan_id, source_epoch, graph_epoch),
        ).fetchone()
        if plan is None:
            raise ValueError(f'plan {plan_id} is not VERIFIED/current for requested epochs')
        seed_id, topology_hash, selected_path_count = plan
        rows = _plan_rows(con, str(plan_id))
        if len(rows) != int(selected_path_count):
            raise ValueError(f'plan {plan_id} selected_path_count does not match stored plan paths')
        receipt = _latest_receipt(con, str(plan_id))
        if not _receipt_is_clean(receipt, graph_epoch, str(topology_hash)):
            raise ValueError(f'latest receipt for plan {plan_id} is not clean/current')
        fingerprint = _plan_paths_hash(rows)
        allowed_pairs.update((str(seed_id), str(r[1])) for r in rows)
        bindings.append(
            (
                str(plan_id),
                str(receipt[0]),
                fingerprint,
                str(seed_id),
                int(source_epoch),
                int(graph_epoch),
                str(topology_hash),
            )
        )
    missing = sorted(path_pairs - allowed_pairs)
    if missing:
        raise ValueError(f'generation contains paths not covered by verified ClayGraph plans: {missing[:3]}')
    if {seed for seed, _ in path_pairs} - {row[3] for row in bindings}:
        raise ValueError('generation has seed without verified ClayGraph plan binding')
    return bindings


def _revalidate_generation_bindings(
    con: sqlite3.Connection,
    generation_id: str,
    source_epoch: int,
    graph_epoch: int,
) -> None:
    if not _graph_v4_present(con):
        raise ValueError('bound generation lost ClayGraph V4 verification schema')
    if not _binding_schema_present(con):
        raise ValueError('U11B generation-plan binding schema missing')
    bindings = list(
        con.execute(
            """SELECT plan_id,verification_receipt_id,plan_paths_hash,seed_id,
                      source_epoch,graph_epoch,topology_hash
               FROM semantic_access_generation_plan_bindings
               WHERE generation_id=? ORDER BY plan_id""",
            (generation_id,),
        )
    )
    if not bindings:
        raise ValueError('generation has no durable ClayGraph verification bindings')

    allowed_pairs: set[tuple[str, str]] = set()
    for plan_id, receipt_id, expected_hash, seed_id, bound_source, bound_graph, topology_hash in bindings:
        if int(bound_source) != int(source_epoch) or int(bound_graph) != int(graph_epoch):
            raise ValueError('generation-plan binding epoch drift')
        plan = con.execute(
            """SELECT p.selected_path_count
               FROM graph_semantic_access_plans p
               JOIN graph_epochs g ON g.graph_epoch=p.graph_epoch
               WHERE p.plan_id=? AND p.seed_id=? AND p.status='VERIFIED'
                 AND p.source_epoch=? AND p.graph_epoch=? AND p.topology_hash=?
                 AND g.source_epoch=p.source_epoch AND g.status='CURRENT'""",
            (plan_id, seed_id, source_epoch, graph_epoch, topology_hash),
        ).fetchone()
        if plan is None:
            raise ValueError(f'bound plan {plan_id} is stale or no longer VERIFIED/current')
        rows = _plan_rows(con, str(plan_id))
        if len(rows) != int(plan[0]) or _plan_paths_hash(rows) != str(expected_hash):
            raise ValueError(f'bound plan {plan_id} path content changed after stage verification')
        receipt = _latest_receipt(con, str(plan_id))
        if not _receipt_is_clean(receipt, graph_epoch, str(topology_hash)):
            raise ValueError(f'latest receipt for bound plan {plan_id} is not clean/current')
        if str(receipt[0]) != str(receipt_id):
            raise ValueError(f'bound plan {plan_id} has a newer verification receipt; restage required')
        allowed_pairs.update((str(seed_id), str(r[1])) for r in rows)

    actual_pairs = {
        (str(r[0]), str(r[1]))
        for r in con.execute(
            "SELECT seed_id,target_logical_id FROM semantic_access_projection_v11 WHERE generation_id=?",
            (generation_id,),
        )
    }
    missing = sorted(actual_pairs - allowed_pairs)
    if missing:
        raise ValueError(f'generation path coverage drifted outside bound ClayGraph plans: {missing[:3]}')


def _legacy_stage_generation(
    con: sqlite3.Connection,
    *,
    generation_id: str,
    source_epoch: int,
    graph_epoch: int,
    derivation_id: str,
    derivation_hash: str,
    paths: list[Path],
    created_at: str,
) -> dict:
    seed_ids = sorted({p.seed_id for p in paths})
    valid = {
        r[0]
        for r in con.execute(
            f"SELECT seed_id FROM semantic_query_seeds WHERE status='CURRENT' AND source_epoch=? AND "
            f"(graph_epoch IS NULL OR graph_epoch=?) AND seed_id IN ({','.join('?' for _ in seed_ids)})",
            (source_epoch, graph_epoch, *seed_ids),
        ).fetchall()
    }
    if valid != set(seed_ids):
        raise ValueError('stale/missing seed; refusing generation')
    with con:
        con.execute(
            "INSERT INTO semantic_access_generations VALUES(?,?,?,?,?,?,?,'{}','STAGING',?,NULL,NULL)",
            (generation_id, source_epoch, graph_epoch, derivation_id, derivation_hash, len(seed_ids), len(paths), created_at),
        )
        con.executemany(
            "INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",
            [(generation_id,p.seed_id,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,p.path_weight,p.authority_rank,p.path_clay) for p in paths],
        )
    return {'generation_id': generation_id, 'seed_count': len(seed_ids), 'path_count': len(paths)}


def stage_generation(
    con: sqlite3.Connection,
    *,
    generation_id: str,
    source_epoch: int,
    graph_epoch: int,
    derivation_id: str,
    derivation_hash: str,
    paths: list[Path],
    created_at: str,
    verified_plan_ids: tuple[str, ...] | list[str] | None = None,
) -> dict:
    if not paths:
        raise ValueError('empty generation; preserve last-known-good')
    if not _graph_v4_present(con):
        return _legacy_stage_generation(
            con,
            generation_id=generation_id,
            source_epoch=source_epoch,
            graph_epoch=graph_epoch,
            derivation_id=derivation_id,
            derivation_hash=derivation_hash,
            paths=paths,
            created_at=created_at,
        )
    if not _binding_schema_present(con):
        raise ValueError('ClayGraph V4 present but U11B generation-plan binding schema missing')

    _begin_owned_write(con, 'stage_generation')
    try:
        if not _graph_v4_present(con):
            raise ValueError('ClayGraph V4 disappeared before integrated stage')
        seed_ids = sorted({p.seed_id for p in paths})
        valid = {
            r[0]
            for r in con.execute(
                f"SELECT seed_id FROM semantic_query_seeds WHERE status='CURRENT' AND source_epoch=? AND "
                f"(graph_epoch IS NULL OR graph_epoch=?) AND seed_id IN ({','.join('?' for _ in seed_ids)})",
                (source_epoch, graph_epoch, *seed_ids),
            ).fetchall()
        }
        if valid != set(seed_ids):
            raise ValueError('stale/missing seed; refusing generation')
        bindings = _validate_plan_ids(
            con,
            source_epoch=source_epoch,
            graph_epoch=graph_epoch,
            path_pairs={(p.seed_id, p.target_logical_id) for p in paths},
            plan_ids=tuple(verified_plan_ids or ()),
        )
        con.execute(
            "INSERT INTO semantic_access_generations VALUES(?,?,?,?,?,?,?,'{}','STAGING',?,NULL,NULL)",
            (generation_id, source_epoch, graph_epoch, derivation_id, derivation_hash, len(seed_ids), len(paths), created_at),
        )
        con.executemany(
            "INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",
            [(generation_id,p.seed_id,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,p.path_weight,p.authority_rank,p.path_clay) for p in paths],
        )
        con.executemany(
            "INSERT INTO semantic_access_generation_plan_bindings VALUES(?,?,?,?,?,?,?,?,?)",
            [(generation_id,plan_id,receipt_id,path_hash,seed_id,bound_source,bound_graph,topology_hash,created_at)
             for plan_id,receipt_id,path_hash,seed_id,bound_source,bound_graph,topology_hash in bindings],
        )
        con.commit()
        return {
            'generation_id': generation_id,
            'seed_count': len(seed_ids),
            'path_count': len(paths),
            'graph_plan_gate_enforced': True,
            'bound_plan_count': len(bindings),
        }
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise


def _strict_generation(con: sqlite3.Connection, generation_id: str) -> bool:
    graph_present = _graph_v4_present(con)
    bound = _generation_has_bindings(con, generation_id)
    if bound and not graph_present:
        return True
    return graph_present or bound


def verify_generation(con: sqlite3.Connection, generation_id: str, *, verification_clay: str, verified_at: str) -> dict:
    if not _strict_generation(con, generation_id):
        g = con.execute(
            "SELECT seed_count,path_count,status FROM semantic_access_generations WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if not g or g[2] != 'STAGING':
            raise ValueError('generation not STAGING')
        actual = con.execute(
            "SELECT count(DISTINCT seed_id),count(*) FROM semantic_access_projection_v11 WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if tuple(actual) != (g[0], g[1]) or actual[0] <= 0 or actual[1] <= 0:
            with con:
                con.execute("UPDATE semantic_access_generations SET status='QUARANTINED' WHERE generation_id=?", (generation_id,))
            raise ValueError('generation verification failed')
        with con:
            con.execute(
                "UPDATE semantic_access_generations SET verification_clay=?,status='VERIFIED',verified_at=? WHERE generation_id=?",
                (verification_clay, verified_at, generation_id),
            )
        return {'generation_id': generation_id, 'verified': True, 'seed_count': actual[0], 'path_count': actual[1]}

    _begin_owned_write(con, 'verify_generation')
    try:
        g = con.execute(
            "SELECT source_epoch,graph_epoch,seed_count,path_count,status FROM semantic_access_generations WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if not g or g[4] != 'STAGING':
            raise ValueError('generation not STAGING')
        actual = con.execute(
            "SELECT count(DISTINCT seed_id),count(*) FROM semantic_access_projection_v11 WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if tuple(actual) != (g[2], g[3]) or actual[0] <= 0 or actual[1] <= 0:
            raise ValueError('generation count verification failed')
        if not _seed_set_is_current(con, generation_id, g[0], g[1], g[2]):
            raise ValueError('generation seed set became stale before verification')
        _revalidate_generation_bindings(con, generation_id, g[0], g[1])
        con.execute(
            "UPDATE semantic_access_generations SET verification_clay=?,status='VERIFIED',verified_at=? "
            "WHERE generation_id=? AND status='STAGING'",
            (verification_clay, verified_at, generation_id),
        )
        if con.execute('SELECT changes()').fetchone()[0] != 1:
            raise ValueError('generation changed during verification')
        con.commit()
        return {
            'generation_id': generation_id,
            'verified': True,
            'seed_count': actual[0],
            'path_count': actual[1],
            'graph_plan_gate_enforced': True,
        }
    except ValueError:
        if con.in_transaction:
            con.execute(
                "UPDATE semantic_access_generations SET status='QUARANTINED' "
                "WHERE generation_id=? AND status IN ('STAGING','VERIFIED')",
                (generation_id,),
            )
            con.commit()
        raise
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise


def publish_generation(con: sqlite3.Connection, generation_id: str, *, published_at: str) -> dict:
    if not _strict_generation(con, generation_id):
        g = con.execute(
            "SELECT source_epoch,graph_epoch,derivation_hash,status FROM semantic_access_generations WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if not g or g[3] != 'VERIFIED':
            raise ValueError('generation not VERIFIED')
        with con:
            old = con.execute("SELECT generation_id FROM semantic_access_head WHERE head_key='CURRENT'").fetchone()
            if old:
                con.execute("UPDATE semantic_access_generations SET status='SUPERSEDED' WHERE generation_id=? AND status='CURRENT'", (old[0],))
            con.execute("UPDATE semantic_access_generations SET status='CURRENT',published_at=? WHERE generation_id=?", (published_at, generation_id))
            con.execute(
                """INSERT INTO semantic_access_head VALUES('CURRENT',?,?,?,?,?)
                   ON CONFLICT(head_key) DO UPDATE SET generation_id=excluded.generation_id,
                   source_epoch=excluded.source_epoch,graph_epoch=excluded.graph_epoch,
                   derivation_hash=excluded.derivation_hash,published_at=excluded.published_at""",
                (generation_id, g[0], g[1], g[2], published_at),
            )
        return {'generation_id': generation_id, 'previous_generation_id': old[0] if old else None, 'published': True}

    _begin_owned_write(con, 'publish_generation')
    try:
        g = con.execute(
            "SELECT source_epoch,graph_epoch,derivation_hash,seed_count,status FROM semantic_access_generations WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if not g or g[4] != 'VERIFIED':
            raise ValueError('generation not VERIFIED')
        if not _seed_set_is_current(con, generation_id, g[0], g[1], g[3]):
            raise ValueError('generation seed set became stale before publication')
        current_graph = con.execute(
            "SELECT 1 FROM graph_epochs WHERE graph_epoch=? AND source_epoch=? AND status='CURRENT'",
            (g[1], g[0]),
        ).fetchone()
        if current_graph is None:
            raise ValueError('generation graph epoch became stale before publication')
        _revalidate_generation_bindings(con, generation_id, g[0], g[1])
        old = con.execute("SELECT generation_id FROM semantic_access_head WHERE head_key='CURRENT'").fetchone()
        if old:
            con.execute(
                "UPDATE semantic_access_generations SET status='SUPERSEDED' WHERE generation_id=? AND status='CURRENT'",
                (old[0],),
            )
        con.execute(
            "UPDATE semantic_access_generations SET status='CURRENT',published_at=? "
            "WHERE generation_id=? AND status='VERIFIED'",
            (published_at, generation_id),
        )
        if con.execute('SELECT changes()').fetchone()[0] != 1:
            raise ValueError('generation changed during publication; refusing head swap')
        con.execute(
            """INSERT INTO semantic_access_head VALUES('CURRENT',?,?,?,?,?)
               ON CONFLICT(head_key) DO UPDATE SET generation_id=excluded.generation_id,
               source_epoch=excluded.source_epoch,graph_epoch=excluded.graph_epoch,
               derivation_hash=excluded.derivation_hash,published_at=excluded.published_at""",
            (generation_id, g[0], g[1], g[2], published_at),
        )
        previous_generation_id = old[0] if old else None
        con.commit()
        return {
            'generation_id': generation_id,
            'previous_generation_id': previous_generation_id,
            'published': True,
            'graph_plan_gate_enforced': True,
        }
    except ValueError:
        if con.in_transaction:
            con.execute(
                "UPDATE semantic_access_generations SET status='QUARANTINED' "
                "WHERE generation_id=? AND status='VERIFIED'",
                (generation_id,),
            )
            con.commit()
        raise
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
