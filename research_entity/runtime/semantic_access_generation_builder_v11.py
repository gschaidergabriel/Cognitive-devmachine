"""Two-phase coherent projection builder for U11.

Build/verify is separate from publish. Publication preserves last-known-good on empty,
stale or failed generations. When ClayGraph V4 verified-plan tables are present, plan
verification becomes an executable fail-closed gate rather than a caller convention.
"""
from __future__ import annotations
from dataclasses import dataclass
import sqlite3


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


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
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
    present = tuple(_table_exists(con, n) for n in names)
    if any(present) and not all(present):
        raise ValueError('incomplete ClayGraph V4 plan schema; refusing semantic generation')
    return all(present)


def _require_binding_schema(con: sqlite3.Connection) -> None:
    if not _table_exists(con, 'semantic_access_generation_plan_bindings'):
        raise ValueError('ClayGraph V4 present but U11B generation-plan binding schema missing')


def _seed_set_is_current(con: sqlite3.Connection, generation_id: str, source_epoch: int, graph_epoch: int, expected: int) -> bool:
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
) -> list[tuple[str, str, str, int, int, str]]:
    """Validate plans/receipts and path coverage; return durable binding rows sans generation/time."""
    if not plan_ids:
        raise ValueError('verified_plan_ids required when ClayGraph V4 is present')
    unique_plan_ids = tuple(dict.fromkeys(plan_ids))
    allowed_pairs: set[tuple[str, str]] = set()
    bindings: list[tuple[str, str, str, int, int, str]] = []

    for plan_id in unique_plan_ids:
        plan = con.execute(
            """SELECT p.seed_id,p.source_epoch,p.graph_epoch,p.topology_hash,p.selected_path_count
               FROM graph_semantic_access_plans p
               JOIN graph_epochs g ON g.graph_epoch=p.graph_epoch
               WHERE p.plan_id=? AND p.status='VERIFIED'
                 AND p.source_epoch=? AND p.graph_epoch=?
                 AND g.source_epoch=p.source_epoch AND g.status='CURRENT'""",
            (plan_id, source_epoch, graph_epoch),
        ).fetchone()
        if plan is None:
            raise ValueError(f'plan {plan_id} is not VERIFIED/current for requested epochs')
        seed_id, _, _, topology_hash, selected_path_count = plan
        receipt = con.execute(
            """SELECT receipt_id
               FROM graph_access_plan_verification_receipts
               WHERE plan_id=? AND graph_epoch=? AND topology_hash=? AND passed=1
                 AND invalid_path_count=0 AND stale_reference_count=0
                 AND missing_counterevidence_count=0
               ORDER BY created_at DESC,receipt_id DESC LIMIT 1""",
            (plan_id, graph_epoch, topology_hash),
        ).fetchone()
        if receipt is None:
            raise ValueError(f'plan {plan_id} lacks a clean passed verification receipt')
        plan_targets = {
            str(r[0]) for r in con.execute(
                "SELECT target_logical_id FROM graph_semantic_access_plan_paths WHERE plan_id=?",
                (plan_id,),
            )
        }
        actual_path_count = con.execute(
            "SELECT COUNT(*) FROM graph_semantic_access_plan_paths WHERE plan_id=?",
            (plan_id,),
        ).fetchone()[0]
        if int(actual_path_count) != int(selected_path_count):
            raise ValueError(f'plan {plan_id} selected_path_count does not match stored plan paths')
        allowed_pairs.update((str(seed_id), t) for t in plan_targets)
        bindings.append((str(plan_id), str(receipt[0]), str(seed_id), source_epoch, graph_epoch, str(topology_hash)))

    missing = sorted(path_pairs - allowed_pairs)
    if missing:
        raise ValueError(f'generation contains paths not covered by verified ClayGraph plans: {missing[:3]}')
    used_seeds = {seed for seed, _ in path_pairs}
    bound_seeds = {row[2] for row in bindings}
    if used_seeds - bound_seeds:
        raise ValueError('generation has seed without verified ClayGraph plan binding')
    return bindings


def _revalidate_generation_bindings(con: sqlite3.Connection, generation_id: str, source_epoch: int, graph_epoch: int) -> None:
    if not _graph_v4_present(con):
        return
    _require_binding_schema(con)
    bindings = list(con.execute(
        """SELECT plan_id,verification_receipt_id,seed_id,source_epoch,graph_epoch,topology_hash
           FROM semantic_access_generation_plan_bindings WHERE generation_id=? ORDER BY plan_id""",
        (generation_id,),
    ))
    if not bindings:
        raise ValueError('generation has no durable ClayGraph verification bindings')

    allowed_pairs: set[tuple[str, str]] = set()
    for plan_id, receipt_id, seed_id, bound_source, bound_graph, topology_hash in bindings:
        if int(bound_source) != int(source_epoch) or int(bound_graph) != int(graph_epoch):
            raise ValueError('generation-plan binding epoch drift')
        plan = con.execute(
            """SELECT 1 FROM graph_semantic_access_plans p
               JOIN graph_epochs g ON g.graph_epoch=p.graph_epoch
               WHERE p.plan_id=? AND p.seed_id=? AND p.status='VERIFIED'
                 AND p.source_epoch=? AND p.graph_epoch=? AND p.topology_hash=?
                 AND g.source_epoch=p.source_epoch AND g.status='CURRENT'""",
            (plan_id, seed_id, source_epoch, graph_epoch, topology_hash),
        ).fetchone()
        if plan is None:
            raise ValueError(f'bound plan {plan_id} is stale or no longer VERIFIED/current')
        receipt = con.execute(
            """SELECT 1 FROM graph_access_plan_verification_receipts
               WHERE receipt_id=? AND plan_id=? AND graph_epoch=? AND topology_hash=?
                 AND passed=1 AND invalid_path_count=0 AND stale_reference_count=0
                 AND missing_counterevidence_count=0""",
            (receipt_id, plan_id, graph_epoch, topology_hash),
        ).fetchone()
        if receipt is None:
            raise ValueError(f'bound plan receipt {receipt_id} is not clean/currently valid')
        allowed_pairs.update(
            (str(seed_id), str(r[0]))
            for r in con.execute(
                "SELECT target_logical_id FROM graph_semantic_access_plan_paths WHERE plan_id=?",
                (plan_id,),
            )
        )

    actual_pairs = {
        (str(r[0]), str(r[1])) for r in con.execute(
            "SELECT seed_id,target_logical_id FROM semantic_access_projection_v11 WHERE generation_id=?",
            (generation_id,),
        )
    }
    missing = sorted(actual_pairs - allowed_pairs)
    if missing:
        raise ValueError(f'generation path coverage drifted outside bound ClayGraph plans: {missing[:3]}')


def _quarantine(con: sqlite3.Connection, generation_id: str) -> None:
    try:
        with con:
            con.execute(
                "UPDATE semantic_access_generations SET status='QUARANTINED' WHERE generation_id=? AND status IN ('STAGING','VERIFIED')",
                (generation_id,),
            )
    except sqlite3.Error:
        pass


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
    seed_ids = sorted({p.seed_id for p in paths})
    valid = {
        r[0] for r in con.execute(
            f"SELECT seed_id FROM semantic_query_seeds WHERE status='CURRENT' AND source_epoch=? AND (graph_epoch IS NULL OR graph_epoch=?) AND seed_id IN ({','.join('?' for _ in seed_ids)})",
            (source_epoch, graph_epoch, *seed_ids),
        ).fetchall()
    }
    if valid != set(seed_ids):
        raise ValueError('stale/missing seed; refusing generation')

    graph_bindings: list[tuple[str, str, str, int, int, str]] = []
    graph_enforced = _graph_v4_present(con)
    if graph_enforced:
        _require_binding_schema(con)
        graph_bindings = _validate_plan_ids(
            con,
            source_epoch=source_epoch,
            graph_epoch=graph_epoch,
            path_pairs={(p.seed_id, p.target_logical_id) for p in paths},
            plan_ids=tuple(verified_plan_ids or ()),
        )

    with con:
        con.execute(
            "INSERT INTO semantic_access_generations VALUES(?,?,?,?,?,?,?,'{}','STAGING',?,NULL,NULL)",
            (generation_id, source_epoch, graph_epoch, derivation_id, derivation_hash, len(seed_ids), len(paths), created_at),
        )
        con.executemany(
            "INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",
            [
                (generation_id, p.seed_id, p.target_record_id, p.target_logical_id, p.path_rank, p.hop_count, p.path_weight, p.authority_rank, p.path_clay)
                for p in paths
            ],
        )
        if graph_bindings:
            con.executemany(
                "INSERT INTO semantic_access_generation_plan_bindings VALUES(?,?,?,?,?,?,?,?)",
                [
                    (generation_id, plan_id, receipt_id, seed_id, bound_source, bound_graph, topology_hash, created_at)
                    for plan_id, receipt_id, seed_id, bound_source, bound_graph, topology_hash in graph_bindings
                ],
            )
    return {
        'generation_id': generation_id,
        'seed_count': len(seed_ids),
        'path_count': len(paths),
        'graph_plan_gate_enforced': graph_enforced,
        'bound_plan_count': len(graph_bindings),
    }


def verify_generation(con: sqlite3.Connection, generation_id: str, *, verification_clay: str, verified_at: str) -> dict:
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
    try:
        if tuple(actual) != (g[2], g[3]) or actual[0] <= 0 or actual[1] <= 0:
            raise ValueError('generation count verification failed')
        if not _seed_set_is_current(con, generation_id, g[0], g[1], g[2]):
            raise ValueError('generation seed set became stale before verification')
        _revalidate_generation_bindings(con, generation_id, g[0], g[1])
    except ValueError:
        _quarantine(con, generation_id)
        raise
    with con:
        con.execute(
            "UPDATE semantic_access_generations SET verification_clay=?,status='VERIFIED',verified_at=? WHERE generation_id=?",
            (verification_clay, verified_at, generation_id),
        )
    return {
        'generation_id': generation_id,
        'verified': True,
        'seed_count': actual[0],
        'path_count': actual[1],
        'graph_plan_gate_enforced': _graph_v4_present(con),
    }


def publish_generation(con: sqlite3.Connection, generation_id: str, *, published_at: str) -> dict:
    g = con.execute(
        "SELECT source_epoch,graph_epoch,derivation_hash,seed_count,status FROM semantic_access_generations WHERE generation_id=?",
        (generation_id,),
    ).fetchone()
    if not g or g[4] != 'VERIFIED':
        raise ValueError('generation not VERIFIED')
    try:
        if not _seed_set_is_current(con, generation_id, g[0], g[1], g[3]):
            raise ValueError('generation seed set became stale before publication')
        if _table_exists(con, 'graph_epochs'):
            current_graph = con.execute(
                "SELECT 1 FROM graph_epochs WHERE graph_epoch=? AND source_epoch=? AND status='CURRENT'",
                (g[1], g[0]),
            ).fetchone()
            if current_graph is None:
                raise ValueError('generation graph epoch became stale before publication')
        _revalidate_generation_bindings(con, generation_id, g[0], g[1])
    except ValueError:
        _quarantine(con, generation_id)
        raise

    with con:
        old = con.execute("SELECT generation_id FROM semantic_access_head WHERE head_key='CURRENT'").fetchone()
        if old:
            con.execute(
                "UPDATE semantic_access_generations SET status='SUPERSEDED' WHERE generation_id=? AND status='CURRENT'",
                (old[0],),
            )
        con.execute(
            "UPDATE semantic_access_generations SET status='CURRENT',published_at=? WHERE generation_id=? AND status='VERIFIED'",
            (published_at, generation_id),
        )
        if con.execute("SELECT changes()").fetchone()[0] != 1:
            raise ValueError('generation changed during publication; refusing head swap')
        con.execute(
            """INSERT INTO semantic_access_head VALUES('CURRENT',?,?,?,?,?)
               ON CONFLICT(head_key) DO UPDATE SET generation_id=excluded.generation_id,
               source_epoch=excluded.source_epoch,graph_epoch=excluded.graph_epoch,
               derivation_hash=excluded.derivation_hash,published_at=excluded.published_at""",
            (generation_id, g[0], g[1], g[2], published_at),
        )
    return {
        'generation_id': generation_id,
        'previous_generation_id': old[0] if old else None,
        'published': True,
        'graph_plan_gate_enforced': _graph_v4_present(con),
    }
