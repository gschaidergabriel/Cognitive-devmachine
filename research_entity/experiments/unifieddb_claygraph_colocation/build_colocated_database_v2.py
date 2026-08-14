#!/usr/bin/env python3
"""Hardened reversible UnifiedDB+ClayGraph co-location migration candidate v2.

V2 pins both source databases to explicit read snapshots, builds and verifies a temporary
combined database from those snapshots, then re-reads fresh source heads before publishing.
If either source advanced or its logical receipt changed during the build, the temporary
output is discarded. Source main-file hashes are retained only as physical metadata; logical
identity is bound by StateLedger roots and ClayGraph projection/epoch receipts.

ClayGraph remains derived/rebuildable and never gains truth/effect authority by co-location.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Callable

from .build_colocated_database_v1 import (
    BASE_GRAPH_TABLES,
    DERIVED_GRAPH_TABLES,
    IGNORED_INTERNAL,
    GRAPH_V3_PATH,
    columns,
    copy_table,
    graph_schema_colocated,
    projection_derivation_hash,
    ro,
    sha256_file,
    table_names,
    verify_projection,
)


def _meta(con: sqlite3.Connection, key: str) -> str:
    row=con.execute('SELECT v FROM meta WHERE k=?',(key,)).fetchone()
    if row is None:
        raise RuntimeError(f'missing StateLedger meta {key}')
    return str(row[0])


def _pin_sources(state_path: Path, graph_path: Path):
    state=ro(state_path); graph=ro(graph_path)
    state.execute('BEGIN'); graph.execute('BEGIN')
    # First reads establish WAL snapshots for the lifetime of these transactions.
    state_epoch=int(_meta(state,'global_epoch'))
    semantic_state_hash=_meta(state,'semantic_state_hash')
    trace_root_hash=_meta(state,'trace_root_hash')
    graph_epoch=int(graph.execute('SELECT COALESCE(MAX(graph_epoch),0) FROM graph_epochs').fetchone()[0])
    if graph_epoch <= 0:
        raise RuntimeError('ClayGraph has no graph epoch to publish')
    graph_source_epoch=int(graph.execute('SELECT source_epoch FROM graph_epochs WHERE graph_epoch=?',(graph_epoch,)).fetchone()[0])
    graph_projection_hash=projection_derivation_hash(graph)
    return state,graph,{
        'state_epoch':state_epoch,
        'semantic_state_hash':semantic_state_hash,
        'trace_root_hash':trace_root_hash,
        'graph_epoch':graph_epoch,
        'graph_source_epoch':graph_source_epoch,
        'graph_projection_hash':graph_projection_hash,
    }


def _fresh_heads(state_path: Path, graph_path: Path) -> dict:
    state=ro(state_path); graph=ro(graph_path)
    try:
        state_epoch=int(_meta(state,'global_epoch'))
        semantic_state_hash=_meta(state,'semantic_state_hash')
        trace_root_hash=_meta(state,'trace_root_hash')
        graph_epoch=int(graph.execute('SELECT COALESCE(MAX(graph_epoch),0) FROM graph_epochs').fetchone()[0])
        graph_source_epoch=int(graph.execute('SELECT source_epoch FROM graph_epochs WHERE graph_epoch=?',(graph_epoch,)).fetchone()[0]) if graph_epoch else 0
        graph_projection_hash=projection_derivation_hash(graph)
        return {
            'state_epoch':state_epoch,
            'semantic_state_hash':semantic_state_hash,
            'trace_root_hash':trace_root_hash,
            'graph_epoch':graph_epoch,
            'graph_source_epoch':graph_source_epoch,
            'graph_projection_hash':graph_projection_hash,
        }
    finally:
        state.close(); graph.close()


def build(state_path: Path, graph_path: Path, output_path: Path,
          *, before_publish_hook: Callable[[],None] | None=None) -> dict:
    state_path=state_path.resolve(); graph_path=graph_path.resolve(); output_path=output_path.resolve()
    if output_path.exists(): raise FileExistsError(output_path)
    for p in (state_path,graph_path):
        if not p.is_file(): raise FileNotFoundError(p)

    state_file_sha_before=sha256_file(state_path)
    graph_file_sha_before=sha256_file(graph_path)
    state,graph,pinned=_pin_sources(state_path,graph_path)
    tmp: Path | None=None
    try:
        if columns(state,'meta')!=('k','v'):
            raise RuntimeError(f'unexpected StateLedger meta schema: {columns(state,"meta")}')
        if columns(graph,'meta')!=('key','value'):
            raise RuntimeError(f'unexpected ClayGraph meta schema: {columns(graph,"meta")}')
        graph_tables=table_names(graph)-IGNORED_INTERNAL
        allowed=set(BASE_GRAPH_TABLES)|DERIVED_GRAPH_TABLES|{'meta'}
        unknown=sorted(graph_tables-allowed)
        if unknown:
            raise RuntimeError('unknown ClayGraph tables require migration review: '+', '.join(unknown))
        missing=sorted(set(BASE_GRAPH_TABLES)-graph_tables)
        if missing:
            raise RuntimeError('missing ClayGraph base tables: '+', '.join(missing))
        collisions=sorted((table_names(state)&(set(BASE_GRAPH_TABLES)|DERIVED_GRAPH_TABLES|{'claygraph_meta'}))-IGNORED_INTERNAL)
        if collisions:
            raise RuntimeError('destination state DB already contains ClayGraph objects: '+', '.join(collisions))
        if pinned['graph_source_epoch']!=pinned['state_epoch']:
            raise RuntimeError(f"graph source epoch {pinned['graph_source_epoch']} != StateLedger epoch {pinned['state_epoch']}")

        output_path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp_name=tempfile.mkstemp(prefix=output_path.name+'.',suffix='.tmp',dir=output_path.parent); os.close(fd); tmp=Path(tmp_name)
        dst=sqlite3.connect(tmp); dst.row_factory=sqlite3.Row
        try:
            # SQLite Online Backup copies the pinned StateLedger snapshot into the destination.
            state.backup(dst)
            dst.execute('PRAGMA foreign_keys=ON'); dst.execute('PRAGMA journal_mode=WAL'); dst.execute('PRAGMA synchronous=FULL')
            dst.executescript(graph_schema_colocated()); dst.executescript(GRAPH_V3_PATH.read_text(encoding='utf-8'))
            dst.execute('BEGIN IMMEDIATE')
            dst.executemany('INSERT INTO claygraph_meta(key,value) VALUES(?,?)',[tuple(r) for r in graph.execute('SELECT key,value FROM meta ORDER BY key')])
            copied={table:copy_table(graph,dst,table) for table in BASE_GRAPH_TABLES}
            projection=verify_projection(dst)
            if not projection['pass']:
                raise RuntimeError('rebuilt ClayGraph V3 projection differs from legacy: '+json.dumps(projection,sort_keys=True))
            rebuilt_projection_hash=projection_derivation_hash(dst)
            if rebuilt_projection_hash!=pinned['graph_projection_hash']:
                raise RuntimeError('rebuilt ClayGraph projection hash differs from pinned source projection')
            source_count=int(dst.execute('SELECT (SELECT COUNT(*) FROM graph_nodes)+(SELECT COUNT(*) FROM graph_edges)').fetchone()[0])
            head_count=int(dst.execute('SELECT (SELECT COUNT(*) FROM graph_head_nodes)+(SELECT COUNT(*) FROM graph_head_edges)').fetchone()[0])
            current_count=int(dst.execute('SELECT (SELECT COUNT(*) FROM v_graph_current_nodes_fast)+(SELECT COUNT(*) FROM v_graph_current_edges_fast)').fetchone()[0])
            projection_id='colocated-v3-'+hashlib.sha256((str(pinned['graph_epoch'])+'|'+str(pinned['state_epoch'])+'|'+rebuilt_projection_hash).encode()).hexdigest()[:24]
            now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
            dst.execute('INSERT INTO graph_current_projection_receipts VALUES(?,?,?,?,?,?,?,?,?,?)',(
                projection_id,pinned['graph_epoch'],pinned['state_epoch'],'COLOCATED_V3_NODE_EDGE_HEADS',rebuilt_projection_hash,
                source_count,head_count,current_count,1,now))
            fk=[tuple(r) for r in dst.execute('PRAGMA foreign_key_check')]
            if fk: raise RuntimeError('foreign_key_check failed: '+repr(fk[:20]))
            dst.execute('''CREATE TABLE IF NOT EXISTS udb_claygraph_colocation_receipts(
              migration_id TEXT PRIMARY KEY,state_semantic_state_hash TEXT NOT NULL,state_trace_root_hash TEXT NOT NULL,
              state_epoch INTEGER NOT NULL,graph_epoch INTEGER NOT NULL,graph_source_epoch INTEGER NOT NULL,
              graph_projection_id TEXT NOT NULL,graph_node_versions INTEGER NOT NULL,graph_edge_versions INTEGER NOT NULL,
              projection_verified_equal INTEGER NOT NULL,authority TEXT NOT NULL,created_at TEXT NOT NULL)''')
            migration_id='udb-cg-v2-'+hashlib.sha256((pinned['semantic_state_hash']+'|'+pinned['trace_root_hash']+'|'+projection_id+'|'+json.dumps(copied,sort_keys=True)).encode()).hexdigest()[:24]
            authority='PHYSICAL_COLOCATION_ONLY_CLAYGRAPH_REMAINS_DERIVED'
            dst.execute('INSERT INTO udb_claygraph_colocation_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
                migration_id,pinned['semantic_state_hash'],pinned['trace_root_hash'],pinned['state_epoch'],pinned['graph_epoch'],pinned['graph_source_epoch'],
                projection_id,copied['graph_nodes'],copied['graph_edges'],1,authority,now))
            if str(dst.execute("SELECT v FROM meta WHERE k='semantic_state_hash'").fetchone()[0])!=pinned['semantic_state_hash']:
                raise RuntimeError('StateLedger semantic root changed during co-location build')
            if str(dst.execute("SELECT v FROM meta WHERE k='trace_root_hash'").fetchone()[0])!=pinned['trace_root_hash']:
                raise RuntimeError('StateLedger trace root changed during co-location build')
            dst.commit()
            integrity=str(dst.execute('PRAGMA integrity_check').fetchone()[0])
            if integrity!='ok': raise RuntimeError('integrity_check failed: '+integrity)
            dst.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        finally:
            dst.close()
    except Exception:
        if tmp is not None:
            for p in (tmp,Path(str(tmp)+'-wal'),Path(str(tmp)+'-shm')):
                try:p.unlink()
                except FileNotFoundError:pass
        raise
    finally:
        try: state.rollback()
        finally: state.close()
        try: graph.rollback()
        finally: graph.close()

    try:
        if before_publish_hook is not None:
            before_publish_hook()
        fresh=_fresh_heads(state_path,graph_path)
        if fresh!=pinned:
            raise RuntimeError('source advanced during migration; refusing stale co-located publication: '+json.dumps({'pinned':pinned,'fresh':fresh},sort_keys=True))
        state_file_sha_after=sha256_file(state_path)
        graph_file_sha_after=sha256_file(graph_path)
        os.replace(tmp,output_path)
        return {
            'migration_id':migration_id,'graph_projection_id':projection_id,'output':str(output_path),
            'state_source_main_file_sha256_before':state_file_sha_before,'state_source_main_file_sha256_after':state_file_sha_after,
            'graph_source_main_file_sha256_before':graph_file_sha_before,'graph_source_main_file_sha256_after':graph_file_sha_after,
            'source_snapshot':pinned,'fresh_source_head':fresh,'copied_rows':copied,'projection':projection,
            'integrity_check':'ok','authority':authority,
            'source_hash_note':'main-file SHA is physical metadata only; logical identity is bound by pinned StateLedger roots and ClayGraph epoch/projection hash',
        }
    except Exception:
        for p in (tmp,Path(str(tmp)+'-wal'),Path(str(tmp)+'-shm')):
            try:p.unlink()
            except FileNotFoundError:pass
        raise


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('state_db'); ap.add_argument('graph_db'); ap.add_argument('output_db'); ap.add_argument('--receipt-json')
    a=ap.parse_args(); result=build(Path(a.state_db),Path(a.graph_db),Path(a.output_db)); text=json.dumps(result,indent=2,sort_keys=True); print(text)
    if a.receipt_json: Path(a.receipt_json).write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
