#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, os, platform, random, sqlite3, statistics, tempfile, time
from pathlib import Path

COMMON = r"""
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;
CREATE TABLE executions(execution_id TEXT PRIMARY KEY, admitted INTEGER NOT NULL, valid INTEGER NOT NULL);
CREATE TABLE effects(effect_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL REFERENCES executions(execution_id), attempt_id TEXT NOT NULL, outcome_hash TEXT NOT NULL, outcome_verified INTEGER NOT NULL, state TEXT NOT NULL);
CREATE TABLE gwt(episode_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL, used INTEGER NOT NULL, valid INTEGER NOT NULL);
CREATE TABLE causal(causal_id TEXT PRIMARY KEY, episode_id TEXT NOT NULL, effect_id TEXT NOT NULL, used INTEGER NOT NULL, valid INTEGER NOT NULL);
CREATE TABLE credit(credit_id TEXT PRIMARY KEY, causal_id TEXT NOT NULL, effect_id TEXT NOT NULL, outcome_hash TEXT NOT NULL, admitted INTEGER NOT NULL, valid INTEGER NOT NULL);
CREATE TABLE delta(delta_hash TEXT PRIMARY KEY, credit_id TEXT NOT NULL, effect_id TEXT NOT NULL, admitted INTEGER NOT NULL, valid INTEGER NOT NULL);
CREATE TABLE nolearn(nolearn_id TEXT PRIMARY KEY, credit_id TEXT NOT NULL, effect_id TEXT NOT NULL, admitted INTEGER NOT NULL, valid INTEGER NOT NULL);
CREATE TABLE reentry(reentry_hash TEXT PRIMARY KEY, effect_id TEXT NOT NULL REFERENCES effects(effect_id), execution_id TEXT NOT NULL, episode_id TEXT NOT NULL, causal_id TEXT NOT NULL, credit_id TEXT NOT NULL, delta_hash TEXT, nolearn_id TEXT, CHECK((delta_hash IS NOT NULL AND nolearn_id IS NULL) OR (delta_hash IS NULL AND nolearn_id IS NOT NULL)));
CREATE INDEX ix_effect_exec ON effects(execution_id);
CREATE INDEX ix_gwt_exec ON gwt(execution_id);
CREATE INDEX ix_causal ON causal(episode_id,effect_id);
CREATE INDEX ix_credit ON credit(causal_id,effect_id,outcome_hash);
CREATE INDEX ix_delta ON delta(credit_id,effect_id);
CREATE INDEX ix_nolearn ON nolearn(credit_id,effect_id);
CREATE INDEX ix_reentry ON reentry(effect_id);
CREATE VIEW closure AS
SELECT e.effect_id,r.reentry_hash
FROM effects e
JOIN executions x ON x.execution_id=e.execution_id AND x.admitted=1 AND x.valid=1
JOIN reentry r ON r.effect_id=e.effect_id AND r.execution_id=e.execution_id
JOIN gwt g ON g.episode_id=r.episode_id AND g.execution_id=e.execution_id AND g.used=1 AND g.valid=1
JOIN causal c ON c.causal_id=r.causal_id AND c.episode_id=g.episode_id AND c.effect_id=e.effect_id AND c.used=1 AND c.valid=1
JOIN credit k ON k.credit_id=r.credit_id AND k.causal_id=c.causal_id AND k.effect_id=e.effect_id AND k.outcome_hash=e.outcome_hash AND k.admitted=1 AND k.valid=1
LEFT JOIN delta d ON d.delta_hash=r.delta_hash AND d.credit_id=k.credit_id AND d.effect_id=e.effect_id AND d.admitted=1 AND d.valid=1
LEFT JOIN nolearn n ON n.nolearn_id=r.nolearn_id AND n.credit_id=k.credit_id AND n.effect_id=e.effect_id AND n.admitted=1 AND n.valid=1
WHERE e.outcome_verified=1 AND e.state='REENTERED'
 AND ((r.delta_hash IS NOT NULL AND d.delta_hash IS NOT NULL AND r.nolearn_id IS NULL)
   OR (r.delta_hash IS NULL AND r.nolearn_id IS NOT NULL AND n.nolearn_id IS NOT NULL));
"""
RECEIPT = r"""
CREATE TABLE done(effect_id TEXT PRIMARY KEY REFERENCES effects(effect_id), reentry_hash TEXT NOT NULL, terminal_hash TEXT NOT NULL UNIQUE);
CREATE TRIGGER done_guard BEFORE INSERT ON done FOR EACH ROW BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM closure WHERE effect_id=NEW.effect_id AND reentry_hash=NEW.reentry_hash)
 THEN RAISE(ABORT,'DONE_REQUIRES_CAUSAL_CLOSURE') END;
END;
"""

def ident(p,i): return f"{p}{i:08d}"

def db(path, receipt):
    c=sqlite3.connect(path); c.executescript(COMMON)
    if receipt: c.executescript(RECEIPT)
    return c

def seed(c,n,receipt):
    q=c.cursor(); q.execute("BEGIN IMMEDIATE")
    for i in range(n):
        x,e,g,ca,k=[ident(p,i) for p in ("x","e","g","c","k")]
        out,r=ident("o",i),ident("r",i)
        q.execute("INSERT INTO executions VALUES(?,1,1)",(x,))
        q.execute("INSERT INTO effects VALUES(?,?,?,?,1,'REENTERED')",(e,x,ident("a",i),out))
        q.execute("INSERT INTO gwt VALUES(?,?,1,1)",(g,x))
        q.execute("INSERT INTO causal VALUES(?,?,?,1,1)",(ca,g,e))
        q.execute("INSERT INTO credit VALUES(?,?,?,?,1,1)",(k,ca,e,out))
        if i%2==0:
            d,nl=ident("d",i),None; q.execute("INSERT INTO delta VALUES(?,?,?,1,1)",(d,k,e))
        else:
            d,nl=None,ident("n",i); q.execute("INSERT INTO nolearn VALUES(?,?,?,1,1)",(nl,k,e))
        q.execute("INSERT INTO reentry VALUES(?,?,?,?,?,?,?,?)",(r,e,x,g,ca,k,d,nl))
        if receipt: q.execute("INSERT INTO done VALUES(?,?,?)",(e,r,ident("t",i)))
    c.commit()

def point(c,receipt,n,samples,seedv):
    rng=random.Random(seedv); ids=[ident("e",rng.randrange(n)) for _ in range(samples)]
    sql="SELECT terminal_hash FROM done WHERE effect_id=?" if receipt else "SELECT reentry_hash FROM closure WHERE effect_id=?"
    q=c.cursor()
    for e in ids[:100]: q.execute(sql,(e,)).fetchone()
    xs=[]
    for e in ids:
        t=time.perf_counter_ns(); row=q.execute(sql,(e,)).fetchone(); xs.append(time.perf_counter_ns()-t)
        assert row is not None
    xs.sort(); pct=lambda p: xs[min(len(xs)-1,math.ceil(p*len(xs))-1)]
    return {"median_ns":statistics.median(xs),"p95_ns":pct(.95),"p99_ns":pct(.99)}

def run_one(root,n,receipt,rep):
    p=root/f"{'receipt' if receipt else 'ccw'}-{rep}.sqlite"
    c=db(p,receipt); t=time.perf_counter(); seed(c,n,receipt); build=time.perf_counter()-t
    q=point(c,receipt,n,min(3000,n),1000+rep)
    result={"build_s":build,"db_bytes":os.path.getsize(p),**q}; c.close(); return result

def mutation_corpus(root):
    cases={
      "VALID":None,"FABRICATED_EPISODE":"UPDATE reentry SET episode_id='fabricated' WHERE effect_id='e00000000'",
      "WRONG_EXECUTION":"UPDATE reentry SET execution_id='x00000001' WHERE effect_id='e00000000'",
      "WRONG_CAUSAL":"UPDATE reentry SET causal_id='c00000001' WHERE effect_id='e00000000'",
      "EXECUTION_INVALID":"UPDATE executions SET valid=0 WHERE execution_id='x00000000'",
      "GWT_UNUSED":"UPDATE gwt SET used=0 WHERE episode_id='g00000000'",
      "CREDIT_INVALID":"UPDATE credit SET valid=0 WHERE credit_id='k00000000'",
      "DELTA_INVALID":"UPDATE delta SET valid=0 WHERE delta_hash='d00000000'",
      "OUTCOME_UNVERIFIED":"UPDATE effects SET outcome_verified=0 WHERE effect_id='e00000000'",
      "NOT_REENTERED":"UPDATE effects SET state='VERIFIED' WHERE effect_id='e00000000'"
    }
    out={}
    for name,sql in cases.items():
        cv=db(root/f"mv-{name}.sqlite",False); seed(cv,2,False)
        if sql: cv.execute(sql); cv.commit()
        view=bool(cv.execute("SELECT 1 FROM closure WHERE effect_id='e00000000'").fetchone()); cv.close()
        cr=db(root/f"mr-{name}.sqlite",True); seed(cr,2,False)
        if sql: cr.execute(sql); cr.commit()
        try:
            cr.execute("INSERT INTO done VALUES('e00000000','r00000000','terminal-x')"); cr.commit(); rec=True
        except sqlite3.IntegrityError:
            cr.rollback(); rec=False
        cr.close(); out[name]={"ccw":view,"receipt":rec}
    return out

def main():
    a=argparse.ArgumentParser(); a.add_argument("--n",type=int,default=10000); a.add_argument("--reps",type=int,default=6); a.add_argument("--output")
    z=a.parse_args(); root=Path(tempfile.mkdtemp(prefix="ccw-")); reps=[]
    for r in range(z.reps):
        order=[True,False] if r%2==0 else [False,True]; row={}
        for receipt in order: row["receipt" if receipt else "ccw"]=run_one(root,z.n,receipt,r)
        reps.append(row)
    ratios={
      "build_ccw_over_receipt":[r["ccw"]["build_s"]/r["receipt"]["build_s"] for r in reps],
      "storage_ccw_over_receipt":[r["ccw"]["db_bytes"]/r["receipt"]["db_bytes"] for r in reps],
      "point_median_ccw_over_receipt":[r["ccw"]["median_ns"]/r["receipt"]["median_ns"] for r in reps],
      "point_p95_ccw_over_receipt":[r["ccw"]["p95_ns"]/r["receipt"]["p95_ns"] for r in reps]}
    result={"environment":{"python":platform.python_version(),"platform":platform.platform(),"sqlite":sqlite3.sqlite_version},"n":z.n,"reps":reps,"ratio_medians":{k:statistics.median(v) for k,v in ratios.items()},"mutation_corpus":mutation_corpus(root)}
    text=json.dumps(result,indent=2); print(text)
    if z.output: Path(z.output).write_text(text,encoding="utf-8")
if __name__=="__main__": main()
