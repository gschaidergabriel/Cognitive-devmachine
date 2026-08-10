#!/usr/bin/env python3
"""Build a reversible UnifiedDB+ClayGraph co-located SQLite candidate.

Sources are opened read-only and never mutated. A new temporary destination is built from a
consistent StateLedger backup plus the versioned ClayGraph source logs. ClayGraph derived V3
head tables are rebuilt by triggers from graph_nodes/graph_edges rather than copied. The
result is atomically renamed into place only after integrity and differential checks pass.

This is a research migration candidate. StateLedger remains semantic truth authority;
ClayGraph remains derived/rebuildable even when both share one physical SQLite file.
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

from .benchmark_colocation_v1 import GRAPH_SCHEMA_PATH, GRAPH_V3_PATH, graph_schema_colocated

BASE_GRAPH_TABLES=(
    'graph_epochs','graph_nodes','graph_edges','assemblies','activation_events','graph_deltas',
)
DERIVED_GRAPH_TABLES={
    'graph_head_nodes','graph_head_edges','graph_current_projection_receipts',
}
IGNORED_INTERNAL={'sqlite_sequence'}


def sha256_file(path:Path)->str:
    d=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): d.update(chunk)
    return d.hexdigest()


def ro(path:Path)->sqlite3.Connection:
    con=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def columns(con:sqlite3.Connection,table:str)->tuple[str,...]:
    return tuple(str(r['name']) for r in con.execute(f'PRAGMA table_info("{table}")'))


def table_names(con:sqlite3.Connection)->set[str]:
    return {str(r[0]) for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def copy_table(src:sqlite3.Connection,dst:sqlite3.Connection,table:str)->int:
    src_cols=columns(src,table); dst_cols=columns(dst,table)
    if src_cols != dst_cols:
        raise RuntimeError(f'column mismatch for {table}: source={src_cols} destination={dst_cols}')
    if not src_cols: return 0
    quoted=','.join('"'+c.replace('"','""')+'"' for c in src_cols)
    marks=','.join('?' for _ in src_cols)
    rows=src.execute(f'SELECT {quoted} FROM "{table}"')
    count=0; batch=[]
    for row in rows:
        batch.append(tuple(row[c] for c in src_cols)); count+=1
        if len(batch)>=1000:
            dst.executemany(f'INSERT INTO "{table}"({quoted}) VALUES({marks})',batch); batch.clear()
    if batch: dst.executemany(f'INSERT INTO "{table}"({quoted}) VALUES({marks})',batch)
    return count


def verify_projection(dst:sqlite3.Connection)->dict:
    amb_nodes=dst.execute('SELECT COUNT(*) FROM v_graph_projection_ambiguous_node_epochs').fetchone()[0]
    amb_edges=dst.execute('SELECT COUNT(*) FROM v_graph_projection_ambiguous_edge_epochs').fetchone()[0]
    legacy_missing_node=dst.execute('SELECT COUNT(*) FROM (SELECT node_version_id FROM v_latest_graph_nodes EXCEPT SELECT node_version_id FROM v_graph_current_nodes_fast)').fetchone()[0]
    fast_extra_node=dst.execute('SELECT COUNT(*) FROM (SELECT node_version_id FROM v_graph_current_nodes_fast EXCEPT SELECT node_version_id FROM v_latest_graph_nodes)').fetchone()[0]
    legacy_missing_edge=dst.execute('SELECT COUNT(*) FROM (SELECT edge_version_id FROM v_latest_graph_edges EXCEPT SELECT edge_version_id FROM v_graph_current_edges_fast)').fetchone()[0]
    fast_extra_edge=dst.execute('SELECT COUNT(*) FROM (SELECT edge_version_id FROM v_graph_current_edges_fast EXCEPT SELECT edge_version_id FROM v_latest_graph_edges)').fetchone()[0]
    result={
        'ambiguous_node_epochs':int(amb_nodes),'ambiguous_edge_epochs':int(amb_edges),
        'node_legacy_minus_fast':int(legacy_missing_node),'node_fast_minus_legacy':int(fast_extra_node),
        'edge_legacy_minus_fast':int(legacy_missing_edge),'edge_fast_minus_legacy':int(fast_extra_edge),
    }
    result['pass']=all(v==0 for k,v in result.items() if k!='pass')
    return result


def build(state_path:Path,graph_path:Path,output_path:Path)->dict:
    state_path=state_path.resolve(); graph_path=graph_path.resolve(); output_path=output_path.resolve()
    if output_path.exists(): raise FileExistsError(output_path)
    for p in (state_path,graph_path):
        if not p.is_file(): raise FileNotFoundError(p)
    state_file_hash_before=sha256_file(state_path); graph_file_hash_before=sha256_file(graph_path)
    state=ro(state_path); graph=ro(graph_path)
    try:
        if columns(state,'meta') != ('k','v'):
            raise RuntimeError(f'unexpected StateLedger meta schema: {columns(state,"meta")}')
        if columns(graph,'meta') != ('key','value'):
            raise RuntimeError(f'unexpected ClayGraph meta schema: {columns(graph,"meta")}')
        graph_tables=table_names(graph)-IGNORED_INTERNAL
        allowed=set(BASE_GRAPH_TABLES)|DERIVED_GRAPH_TABLES|{'meta'}
        unknown=sorted(graph_tables-allowed)
        if unknown:
            raise RuntimeError('unknown ClayGraph tables require migration review: '+', '.join(unknown))
        missing=sorted(set(BASE_GRAPH_TABLES)-graph_tables)
        if missing:
            raise RuntimeError('missing ClayGraph base tables: '+', '.join(missing))
        state_tables=table_names(state)
        collisions=sorted((state_tables & (set(BASE_GRAPH_TABLES)|DERIVED_GRAPH_TABLES|{'claygraph_meta'}))-IGNORED_INTERNAL)
        if collisions:
            raise RuntimeError('destination state DB already contains ClayGraph objects: '+', '.join(collisions))
        semantic_state_hash=state.execute("SELECT v FROM meta WHERE k='semantic_state_hash'").fetchone()
        trace_root_hash=state.execute("SELECT v FROM meta WHERE k='trace_root_hash'").fetchone()
        semantic_state_hash=str(semantic_state_hash[0]) if semantic_state_hash else 'UNKNOWN'
        trace_root_hash=str(trace_root_hash[0]) if trace_root_hash else 'UNKNOWN'

        output_path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp_name=tempfile.mkstemp(prefix=output_path.name+'.',suffix='.tmp',dir=output_path.parent)
        os.close(fd); tmp=Path(tmp_name)
        try:
            dst=sqlite3.connect(tmp)
            dst.row_factory=sqlite3.Row
            state.backup(dst)
            dst.execute('PRAGMA foreign_keys=ON'); dst.execute('PRAGMA journal_mode=WAL'); dst.execute('PRAGMA synchronous=FULL')
            dst.executescript(graph_schema_colocated()); dst.executescript(GRAPH_V3_PATH.read_text(encoding='utf-8'))
            dst.execute('BEGIN IMMEDIATE')
            graph_meta_rows=[tuple(r) for r in graph.execute('SELECT key,value FROM meta ORDER BY key')]
            dst.executemany('INSERT INTO claygraph_meta(key,value) VALUES(?,?)',graph_meta_rows)
            copied={}
            for table in BASE_GRAPH_TABLES:
                copied[table]=copy_table(graph,dst,table)
            projection=verify_projection(dst)
            if not projection['pass']:
                raise RuntimeError('rebuilt ClayGraph V3 projection differs from legacy: '+json.dumps(projection,sort_keys=True))
            fk=[tuple(r) for r in dst.execute('PRAGMA foreign_key_check')]
            if fk: raise RuntimeError('foreign_key_check failed: '+repr(fk[:20]))
            dst.execute('''CREATE TABLE IF NOT EXISTS udb_claygraph_colocation_receipts(
              migration_id TEXT PRIMARY KEY,state_semantic_state_hash TEXT NOT NULL,state_trace_root_hash TEXT NOT NULL,
              graph_epoch INTEGER NOT NULL,graph_node_versions INTEGER NOT NULL,graph_edge_versions INTEGER NOT NULL,
              projection_verified_equal INTEGER NOT NULL,authority TEXT NOT NULL,created_at TEXT NOT NULL)''')
            max_ge=dst.execute('SELECT COALESCE(MAX(graph_epoch),0) FROM graph_epochs').fetchone()[0]
            migration_id='udb-cg-v1-'+hashlib.sha256((semantic_state_hash+'|'+trace_root_hash+'|'+str(max_ge)+'|'+json.dumps(copied,sort_keys=True)).encode()).hexdigest()[:24]
            dst.execute('INSERT INTO udb_claygraph_colocation_receipts VALUES(?,?,?,?,?,?,?,?,?)',(
                migration_id,semantic_state_hash,trace_root_hash,int(max_ge),copied['graph_nodes'],copied['graph_edges'],1,
                'PHYSICAL_COLOCATION_ONLY_CLAYGRAPH_REMAINS_DERIVED',time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
            # Graph objects are physical/derived additions only; StateLedger roots stored in meta must not change.
            if dst.execute("SELECT v FROM meta WHERE k='semantic_state_hash'").fetchone()[0] != semantic_state_hash:
                raise RuntimeError('StateLedger semantic root changed during co-location build')
            if dst.execute("SELECT v FROM meta WHERE k='trace_root_hash'").fetchone()[0] != trace_root_hash:
                raise RuntimeError('StateLedger trace root changed during co-location build')
            dst.commit()
            integrity=dst.execute('PRAGMA integrity_check').fetchone()[0]
            if integrity!='ok': raise RuntimeError('integrity_check failed: '+str(integrity))
            dst.execute('PRAGMA wal_checkpoint(TRUNCATE)'); dst.close()
            os.replace(tmp,output_path)
        except Exception:
            try: dst.close()
            except Exception: pass
            for p in (tmp,Path(str(tmp)+'-wal'),Path(str(tmp)+'-shm')):
                try:p.unlink()
                except FileNotFoundError:pass
            raise
    finally:
        state.close(); graph.close()
    if sha256_file(state_path)!=state_file_hash_before: raise RuntimeError('source StateLedger file changed')
    if sha256_file(graph_path)!=graph_file_hash_before: raise RuntimeError('source ClayGraph file changed')
    return {
        'migration_id':migration_id,'output':str(output_path),'state_source_sha256':state_file_hash_before,
        'graph_source_sha256':graph_file_hash_before,'semantic_state_hash':semantic_state_hash,'trace_root_hash':trace_root_hash,
        'copied_rows':copied,'projection':projection,'integrity_check':'ok','authority':'PHYSICAL_COLOCATION_ONLY_CLAYGRAPH_REMAINS_DERIVED'
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('state_db'); ap.add_argument('graph_db'); ap.add_argument('output_db'); ap.add_argument('--receipt-json')
    a=ap.parse_args(); result=build(Path(a.state_db),Path(a.graph_db),Path(a.output_db)); text=json.dumps(result,indent=2,sort_keys=True); print(text)
    if a.receipt_json: Path(a.receipt_json).write_text(text+'\n',encoding='utf-8')

if __name__=='__main__':main()
