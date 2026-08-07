#!/usr/bin/env python3
"""Compact query interface over the derived RAE SQLite materialization.

Use this to select relevant claims/packets/source chunks before loading files into an
agent context. It is a retrieval aid only; returned rows point back to canonical ledgers
and immutable sources.
"""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/'research_sources'/'sources.db'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('query')
    ap.add_argument('--db',default=str(DEFAULT_DB))
    ap.add_argument('--limit',type=int,default=12)
    ap.add_argument('--status',action='append',choices=['CURRENT','OPEN','SUPERSEDED','REFUTED','NEGATIVE_RESULT','CONTEXT_ONLY'])
    args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
    q=args.query.strip()
    out={'query':q,'claims':[],'packets':[],'chunks':[]}

    # FTS5 is used for claims/chunks. Quote plain user text to avoid accidental operators.
    fts='"'+q.replace('"','""')+'"'
    try:
        rows=con.execute('''SELECT c.claim_id,cs.status,c.scope,c.proposition
                            FROM claim_fts f JOIN claims c USING(claim_id)
                            LEFT JOIN claim_current_status cs USING(claim_id)
                            WHERE claim_fts MATCH ? LIMIT ?''',(fts,args.limit*3)).fetchall()
    except sqlite3.OperationalError:
        rows=[]
    statuses=set(args.status or [])
    for r in rows:
        d=dict(r); d['status']=d.get('status') or ''
        if statuses and d['status'] not in statuses: continue
        out['claims'].append(d)
        if len(out['claims'])>=args.limit: break

    like=f'%{q}%'
    for r in con.execute('''SELECT packet_id,status,title,summary FROM packets
                            WHERE title LIKE ? OR summary LIKE ? LIMIT ?''',(like,like,args.limit)).fetchall():
        out['packets'].append(dict(r))

    try:
        for r in con.execute('''SELECT s.path,f.chunk_id,substr(f.text,1,1200) AS excerpt
                                FROM chunk_fts f JOIN sources s USING(source_id)
                                WHERE chunk_fts MATCH ? LIMIT ?''',(fts,args.limit)).fetchall():
            out['chunks'].append(dict(r))
    except sqlite3.OperationalError:
        pass

    con.close(); print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
