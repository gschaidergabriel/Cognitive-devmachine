"""Two-phase coherent projection builder for U11.

Build/verify is separate from publish. Publication is one SQLite transaction and preserves
last-known-good on empty, stale or failed generations.
"""
from __future__ import annotations
from dataclasses import dataclass
import sqlite3

@dataclass(frozen=True)
class Path:
    seed_id:str; target_record_id:str; target_logical_id:str; path_rank:int; hop_count:int
    path_weight:float; authority_rank:float; path_clay:str

def stage_generation(con:sqlite3.Connection,*,generation_id:str,source_epoch:int,graph_epoch:int,
                     derivation_id:str,derivation_hash:str,paths:list[Path],created_at:str)->dict:
    if not paths: raise ValueError('empty generation; preserve last-known-good')
    seed_ids=sorted({p.seed_id for p in paths})
    valid={r[0] for r in con.execute(
        f"SELECT seed_id FROM semantic_query_seeds WHERE status='CURRENT' AND source_epoch=? AND (graph_epoch IS NULL OR graph_epoch=?) AND seed_id IN ({','.join('?' for _ in seed_ids)})",
        (source_epoch,graph_epoch,*seed_ids)).fetchall()}
    if valid != set(seed_ids): raise ValueError('stale/missing seed; refusing generation')
    with con:
        con.execute("INSERT INTO semantic_access_generations VALUES(?,?,?,?,?,?,?,'{}','STAGING',?,NULL,NULL)",
                    (generation_id,source_epoch,graph_epoch,derivation_id,derivation_hash,len(seed_ids),len(paths),created_at))
        con.executemany("INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",
            [(generation_id,p.seed_id,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,p.path_weight,p.authority_rank,p.path_clay) for p in paths])
    return {'generation_id':generation_id,'seed_count':len(seed_ids),'path_count':len(paths)}

def verify_generation(con:sqlite3.Connection,generation_id:str,*,verification_clay:str,verified_at:str)->dict:
    g=con.execute("SELECT seed_count,path_count,status FROM semantic_access_generations WHERE generation_id=?",(generation_id,)).fetchone()
    if not g or g[2] != 'STAGING': raise ValueError('generation not STAGING')
    actual=con.execute("SELECT count(DISTINCT seed_id),count(*) FROM semantic_access_projection_v11 WHERE generation_id=?",(generation_id,)).fetchone()
    if tuple(actual)!=(g[0],g[1]) or actual[0]<=0 or actual[1]<=0:
        with con: con.execute("UPDATE semantic_access_generations SET status='QUARANTINED' WHERE generation_id=?",(generation_id,))
        raise ValueError('generation verification failed')
    with con:
        con.execute("UPDATE semantic_access_generations SET verification_clay=?,status='VERIFIED',verified_at=? WHERE generation_id=?",
                    (verification_clay,verified_at,generation_id))
    return {'generation_id':generation_id,'verified':True,'seed_count':actual[0],'path_count':actual[1]}

def publish_generation(con:sqlite3.Connection,generation_id:str,*,published_at:str)->dict:
    g=con.execute("SELECT source_epoch,graph_epoch,derivation_hash,status FROM semantic_access_generations WHERE generation_id=?",(generation_id,)).fetchone()
    if not g or g[3] != 'VERIFIED': raise ValueError('generation not VERIFIED')
    with con:
        old=con.execute("SELECT generation_id FROM semantic_access_head WHERE head_key='CURRENT'").fetchone()
        if old:
            con.execute("UPDATE semantic_access_generations SET status='SUPERSEDED' WHERE generation_id=? AND status='CURRENT'",(old[0],))
        con.execute("UPDATE semantic_access_generations SET status='CURRENT',published_at=? WHERE generation_id=?",(published_at,generation_id))
        con.execute("""INSERT INTO semantic_access_head VALUES('CURRENT',?,?,?,?,?)
                       ON CONFLICT(head_key) DO UPDATE SET generation_id=excluded.generation_id,
                       source_epoch=excluded.source_epoch,graph_epoch=excluded.graph_epoch,
                       derivation_hash=excluded.derivation_hash,published_at=excluded.published_at""",
                    (generation_id,g[0],g[1],g[2],published_at))
    return {'generation_id':generation_id,'previous_generation_id':old[0] if old else None,'published':True}
