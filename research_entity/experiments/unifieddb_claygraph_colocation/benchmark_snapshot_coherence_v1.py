#!/usr/bin/env python3
"""Orchestrated WAL snapshot-coherence falsifier for one-file vs ATTACH layouts.

The reader deliberately acquires its state snapshot first, then a writer commits a coupled
state+graph update, then the same reader touches graph state. With two attached WAL databases
this can bind two different per-database snapshots inside one SQL transaction. With one
physical database file both reads share the same database snapshot.

This measures a physical storage property only; marker tables do not represent semantic truth.
"""
from __future__ import annotations
import argparse, json, os, platform, sqlite3, tempfile, threading, time
from pathlib import Path


def wal(con):
    con.execute('PRAGMA journal_mode=WAL'); con.execute('PRAGMA synchronous=FULL')


def setup_one(td):
    p=Path(td)/'unified.sqlite'; c=sqlite3.connect(p); wal(c)
    c.executescript('CREATE TABLE state_marker(v INTEGER NOT NULL); INSERT INTO state_marker VALUES(0); CREATE TABLE graph_marker(v INTEGER NOT NULL); INSERT INTO graph_marker VALUES(0);'); c.commit(); c.close(); return p


def setup_two(td):
    s=Path(td)/'state.sqlite'; g=Path(td)/'graph.sqlite'
    c=sqlite3.connect(s); wal(c); c.execute('CREATE TABLE state_marker(v INTEGER NOT NULL)'); c.execute('INSERT INTO state_marker VALUES(0)'); c.commit(); c.close()
    c=sqlite3.connect(g); wal(c); c.execute('CREATE TABLE graph_marker(v INTEGER NOT NULL)'); c.execute('INSERT INTO graph_marker VALUES(0)'); c.commit(); c.close(); return s,g


def one_trial():
    with tempfile.TemporaryDirectory() as td:
        path=setup_one(td); first=threading.Event(); committed=threading.Event(); out={}
        def reader():
            c=sqlite3.connect(path,timeout=5); c.execute('BEGIN')
            out['state']=c.execute('SELECT v FROM state_marker').fetchone()[0]; first.set()
            if not committed.wait(5): raise RuntimeError('writer timeout')
            out['graph']=c.execute('SELECT v FROM graph_marker').fetchone()[0]; c.rollback(); c.close()
        def writer():
            if not first.wait(5): raise RuntimeError('reader timeout')
            c=sqlite3.connect(path,timeout=5); c.execute('BEGIN IMMEDIATE'); c.execute('UPDATE state_marker SET v=1'); c.execute('UPDATE graph_marker SET v=1'); c.commit(); c.close(); committed.set()
        r=threading.Thread(target=reader); w=threading.Thread(target=writer); r.start(); w.start(); r.join(); w.join(); return out


def two_trial():
    with tempfile.TemporaryDirectory() as td:
        state,graph=setup_two(td); first=threading.Event(); committed=threading.Event(); out={}
        def connect():
            c=sqlite3.connect(state,timeout=5); c.execute('ATTACH DATABASE ? AS g',(str(graph),)); return c
        def reader():
            c=connect(); c.execute('BEGIN')
            out['state']=c.execute('SELECT v FROM state_marker').fetchone()[0]; first.set()
            if not committed.wait(5): raise RuntimeError('writer timeout')
            out['graph']=c.execute('SELECT v FROM g.graph_marker').fetchone()[0]; c.rollback(); c.close()
        def writer():
            if not first.wait(5): raise RuntimeError('reader timeout')
            c=connect(); c.execute('BEGIN IMMEDIATE'); c.execute('UPDATE state_marker SET v=1'); c.execute('UPDATE g.graph_marker SET v=1'); c.commit(); c.close(); committed.set()
        r=threading.Thread(target=reader); w=threading.Thread(target=writer); r.start(); w.start(); r.join(); w.join(); return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--trials',type=int,default=100); ap.add_argument('--output'); a=ap.parse_args()
    one=[]; two=[]
    for _ in range(a.trials): one.append(one_trial()); two.append(two_trial())
    one_bad=sum(x['state']!=x['graph'] for x in one); two_bad=sum(x['state']!=x['graph'] for x in two)
    out={
      'schema':'clay.udb_claygraph_snapshot_coherence.v1',
      'scope':'orchestrated local SQLite WAL snapshot acquisition across one physical file vs two ATTACHed files',
      'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform()},
      'trials':a.trials,
      'single_file':{'incoherent_reads':one_bad,'incoherent_rate':one_bad/a.trials,'observed_pairs':sorted({(x['state'],x['graph']) for x in one})},
      'two_file_attach':{'incoherent_reads':two_bad,'incoherent_rate':two_bad/a.trials,'observed_pairs':sorted({(x['state'],x['graph']) for x in two})},
      'interpretation':'A one-file layout supplies one SQLite database snapshot to both marker reads. In the attached-WAL layout the two schemas can acquire snapshots at different moments when first touched. This is a physical coherence hazard, not proof that every two-store architecture is invalid.',
      'promotion':'MECHANISM_EVIDENCE_ONLY'
    }
    text=json.dumps(out,indent=2,sort_keys=True); print(text)
    if a.output: Path(a.output).write_text(text+'\n')
    if one_bad: raise SystemExit('single-file snapshot incoherence observed')

if __name__=='__main__':main()
