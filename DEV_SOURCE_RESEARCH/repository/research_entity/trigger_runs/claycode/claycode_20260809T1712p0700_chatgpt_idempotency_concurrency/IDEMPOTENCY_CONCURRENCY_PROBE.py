import sqlite3, tempfile, threading, os, time, json, hashlib

ROUNDS=80

def init_db(path):
    c=sqlite3.connect(path)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE effects (idempotency_key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, result TEXT NOT NULL)')
    c.commit(); c.close()

def h(payload): return hashlib.sha256(payload.encode()).hexdigest()

def prelock_round(diff_payload=False):
    fd,path=tempfile.mkstemp(); os.close(fd); os.unlink(path); init_db(path)
    barrier=threading.Barrier(2); out=[]; lock=threading.Lock()
    def worker(name,payload):
        con=sqlite3.connect(path, timeout=3, isolation_level=None)
        try:
            row=con.execute('SELECT payload_hash,result FROM effects WHERE idempotency_key=?',('K',)).fetchone()
            if row:
                res=('replay' if row[0]==h(payload) else 'conflict')
            else:
                barrier.wait()
                con.execute('BEGIN IMMEDIATE')
                try:
                    con.execute('INSERT INTO effects VALUES (?,?,?)',('K',h(payload),'APPLIED'))
                    con.execute('COMMIT'); res='applied'
                except Exception as e:
                    try: con.execute('ROLLBACK')
                    except: pass
                    res=type(e).__name__
        finally:
            con.close()
        with lock: out.append((name,res))
    t1=threading.Thread(target=worker,args=('A','p1')); t2=threading.Thread(target=worker,args=('B','p2' if diff_payload else 'p1'))
    t1.start(); t2.start(); t1.join(); t2.join()
    con=sqlite3.connect(path); n=con.execute('SELECT count(*) FROM effects').fetchone()[0]; con.close(); os.unlink(path)
    return sorted(x[1] for x in out),n

def postlock_round(diff_payload=False):
    fd,path=tempfile.mkstemp(); os.close(fd); os.unlink(path); init_db(path)
    barrier=threading.Barrier(2); out=[]; lock=threading.Lock()
    def worker(name,payload):
        con=sqlite3.connect(path, timeout=3, isolation_level=None)
        try:
            barrier.wait()
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT payload_hash,result FROM effects WHERE idempotency_key=?',('K',)).fetchone()
            if row:
                res=('replay' if row[0]==h(payload) else 'conflict')
                con.execute('COMMIT')
            else:
                con.execute('INSERT INTO effects VALUES (?,?,?)',('K',h(payload),'APPLIED'))
                con.execute('COMMIT'); res='applied'
        except Exception as e:
            try: con.execute('ROLLBACK')
            except: pass
            res=type(e).__name__
        finally:
            con.close()
        with lock: out.append((name,res))
    t1=threading.Thread(target=worker,args=('A','p1')); t2=threading.Thread(target=worker,args=('B','p2' if diff_payload else 'p1'))
    t1.start(); t2.start(); t1.join(); t2.join()
    con=sqlite3.connect(path); n=con.execute('SELECT count(*) FROM effects').fetchone()[0]; con.close(); os.unlink(path)
    return sorted(x[1] for x in out),n

def uniqueness_only_payload_mismatch():
    fd,path=tempfile.mkstemp(); os.close(fd); os.unlink(path); init_db(path)
    con=sqlite3.connect(path)
    con.execute('INSERT INTO effects VALUES (?,?,?)',('K',h('p1'),'APPLIED')); con.commit()
    cur=con.execute('INSERT OR IGNORE INTO effects VALUES (?,?,?)',('K',h('DIFFERENT'),'APPLIED')); con.commit()
    row=con.execute('SELECT payload_hash,result FROM effects WHERE idempotency_key=?',('K',)).fetchone()
    out={'insert_or_ignore_rowcount':cur.rowcount,'stored_payload_is_original':row[0]==h('p1'),'payload_mismatch_explicitly_classified':False}
    con.close(); os.unlink(path)
    return out

def run(fn,diff=False):
    results=[]; t=time.perf_counter()
    for _ in range(ROUNDS): results.append(fn(diff))
    elapsed=time.perf_counter()-t
    kinds={}
    for r,n in results: kinds[(tuple(r),n)]=kinds.get((tuple(r),n),0)+1
    return {'rounds':ROUNDS,'patterns':[{'results':list(k[0]),'rows':k[1],'count':v} for k,v in kinds.items()],'elapsed_s':elapsed}

report={
 'probe':'ClayCode runtime-lowering idempotency transaction probe',
 'prelock_same_payload':run(prelock_round,False),
 'postlock_same_payload':run(postlock_round,False),
 'postlock_different_payload':run(postlock_round,True),
 'uniqueness_only_different_payload':uniqueness_only_payload_mismatch(),
}
print(json.dumps(report,indent=2))
