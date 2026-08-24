#!/usr/bin/env python3
from __future__ import annotations
import base64, datetime as dt, hashlib, json, os, pathlib, shlex, signal, sqlite3, subprocess, time, traceback

VERSION='CLAY_LOCAL_BRIDGE/v1'
HOME=pathlib.Path.home()
BASE=HOME/'.local/share/clay-local-bridge'
CONTROL=BASE/'control-mirror'
RESULTS=BASE/'results-mirror'
STATE=BASE/'state'
JOBS=BASE/'jobs'
DB=STATE/'bridge.sqlite3'
CONTROL_BRANCH='chatgpt-local-control'
RESULTS_BRANCH='chatgpt-local-results'
QUEUE=pathlib.Path('local_bridge/commands')
MAX_TIMEOUT=14400
MAX_LOG=512*1024
for p in (STATE,JOBS): p.mkdir(parents=True,exist_ok=True)

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def text(b): return (b or b'').decode('utf-8','replace')
def sha(b): return hashlib.sha256(b).hexdigest()
def run(argv,timeout=120,cwd=None,env=None): return subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,cwd=cwd,env=env)
def git(repo,*args,timeout=180,check=True):
    p=run(['git','-C',str(repo),*args],timeout=timeout)
    if check and p.returncode: raise RuntimeError('GIT_FAILED: '+text(p.stderr)[-6000:])
    return p

def conn():
    c=sqlite3.connect(DB)
    c.execute('CREATE TABLE IF NOT EXISTS done(id TEXT PRIMARY KEY, command_sha TEXT NOT NULL, finished TEXT NOT NULL, code INTEGER NOT NULL)')
    c.commit(); return c

def relpath(value):
    p=pathlib.Path(os.path.expanduser(str(value)))
    return p if p.is_absolute() else HOME/p

def sync_control():
    git(CONTROL,'fetch','origin',CONTROL_BRANCH,'--prune')
    git(CONTROL,'checkout','-B',CONTROL_BRANCH,f'origin/{CONTROL_BRANCH}')
    git(CONTROL,'reset','--hard',f'origin/{CONTROL_BRANCH}')

def sync_results():
    git(RESULTS,'fetch','origin',RESULTS_BRANCH,'--prune')
    git(RESULTS,'checkout','-B',RESULTS_BRANCH,f'origin/{RESULTS_BRANCH}')
    git(RESULTS,'reset','--hard',f'origin/{RESULTS_BRANCH}')

def push_results(message,live=False):
    git(RESULTS,'add','local_bridge/results',check=False)
    if git(RESULTS,'diff','--cached','--quiet',check=False).returncode==0: return
    if live:
        subj=text(git(RESULTS,'log','-1','--pretty=%s',check=False).stdout).strip()
        if subj.startswith('local live telemetry'):
            git(RESULTS,'commit','--amend','--no-edit')
            git(RESULTS,'push','--force-with-lease','origin',f'HEAD:{RESULTS_BRANCH}',timeout=300)
            return
    git(RESULTS,'commit','-m',message)
    git(RESULTS,'push','origin',f'HEAD:{RESULTS_BRANCH}',timeout=300)

def job_meta(job_id): return JOBS/job_id/'meta.json'
def load_job(job_id):
    p=job_meta(job_id)
    if not p.exists(): raise FileNotFoundError('JOB_NOT_FOUND')
    return json.loads(p.read_text())
def save_job(meta):
    d=JOBS/meta['job_id']; d.mkdir(parents=True,exist_ok=True)
    job_meta(meta['job_id']).write_text(json.dumps(meta,indent=2)+'\n')
def pid_alive(pid):
    try: os.kill(int(pid),0); return True
    except Exception: return False

def op_exec(s):
    cwd=relpath(s.get('cwd',str(HOME)))
    timeout=min(max(int(s.get('timeout_seconds',3600)),1),MAX_TIMEOUT)
    return run(['bash','-lc',str(s['command'])],cwd=str(cwd),timeout=timeout),{'cwd':str(cwd)}

def op_exec_async(s):
    job_id=str(s.get('job_id') or s['command_id'])
    d=JOBS/job_id; d.mkdir(parents=True,exist_ok=True)
    cwd=relpath(s.get('cwd',str(HOME)))
    out=(d/'stdout.log').open('ab',buffering=0); err=(d/'stderr.log').open('ab',buffering=0)
    p=subprocess.Popen(['bash','-lc',str(s['command'])],cwd=str(cwd),stdout=out,stderr=err,stdin=subprocess.DEVNULL,start_new_session=True)
    meta={'job_id':job_id,'pid':p.pid,'pgid':os.getpgid(p.pid),'cwd':str(cwd),'command':str(s['command']),'started_at':now(),'status':'RUNNING'}
    save_job(meta)
    return subprocess.CompletedProcess(['exec_async'],0,json.dumps(meta,indent=2).encode(),b''),meta

def op_job_status(s):
    meta=load_job(str(s['job_id']))
    alive=pid_alive(meta['pid'])
    meta['status']='RUNNING' if alive else 'EXITED_OR_UNKNOWN'
    d=JOBS[meta['job_id']]
    stdout=(d/'stdout.log').read_bytes()[-MAX_LOG:] if (d/'stdout.log').exists() else b''
    stderr=(d/'stderr.log').read_bytes()[-MAX_LOG:] if (d/'stderr.log').exists() else b''
    payload={'meta':meta,'stdout_tail':text(stdout)[-24000:],'stderr_tail':text(stderr)[-24000:]}
    return subprocess.CompletedProcess(['job_status'],0,json.dumps(payload,indent=2).encode(),b''),meta

def op_job_cancel(s):
    meta=load_job(str(s['job_id']))
    try: os.killpg(int(meta['pgid']),signal.SIGTERM); time.sleep(1)
    except ProcessLookupError: pass
    meta['status']='CANCEL_REQUESTED'; meta['cancelled_at']=now(); save_job(meta)
    return subprocess.CompletedProcess(['job_cancel'],0,json.dumps(meta,indent=2).encode(),b''),meta

def op_read_file(s):
    p=relpath(s['path']); data=p.read_bytes(); view=data[:MAX_LOG]
    return subprocess.CompletedProcess(['read_file'],0,view,b''),{'path':str(p),'bytes':len(data),'sha256':sha(data),'truncated':len(data)>MAX_LOG}

def op_write_text(s):
    p=relpath(s['path']); p.parent.mkdir(parents=True,exist_ok=True); data=str(s.get('content','')).encode(); p.write_bytes(data)
    return subprocess.CompletedProcess(['write_text'],0,f'WROTE {p} {len(data)} bytes\n'.encode(),b''),{'path':str(p),'sha256':sha(data),'bytes':len(data)}

def op_write_base64(s):
    p=relpath(s['path']); p.parent.mkdir(parents=True,exist_ok=True); data=base64.b64decode(s['base64'],validate=True); p.write_bytes(data)
    return subprocess.CompletedProcess(['write_base64'],0,f'WROTE {p} {len(data)} bytes\n'.encode(),b''),{'path':str(p),'sha256':sha(data),'bytes':len(data)}

def op_list_dir(s):
    p=relpath(s.get('path',str(HOME))); depth=max(1,min(int(s.get('depth',2)),4))
    cmd=f"find {shlex.quote(str(p))} -maxdepth {depth} -printf '%y %s %TY-%Tm-%TdT%TH:%TM:%TS %p\\n' 2>/dev/null | head -2000"
    return run(['bash','-lc',cmd],timeout=60),{'path':str(p),'depth':depth}

def op_git(s):
    action=str(s.get('action','status')); repo=relpath(s['repo'])
    if action=='status': return run(['git','-C',str(repo),'status','--short','--branch'],timeout=60),{'repo':str(repo)}
    if action=='fetch': return run(['git','-C',str(repo),'fetch','--all','--tags','--prune'],timeout=600),{'repo':str(repo)}
    if action=='pull_ff': return run(['git','-C',str(repo),'pull','--ff-only'],timeout=600),{'repo':str(repo)}
    if action=='clone':
        dest=relpath(s['dest']); return run(['git','clone',str(s['url']),str(dest)],timeout=1800),{'dest':str(dest)}
    raise ValueError('UNSUPPORTED_GIT_ACTION')

def op_tmux_start(s):
    name=str(s.get('session','chatgpt')); cwd=relpath(s.get('cwd',str(HOME))); cmd=str(s.get('command','bash'))
    if run(['which','tmux']).returncode: raise RuntimeError('TMUX_NOT_INSTALLED')
    run(['tmux','kill-session','-t',name],check=False) if False else None
    p=run(['tmux','new-session','-d','-s',name,'-c',str(cwd),cmd],timeout=30)
    return p,{'session':name,'cwd':str(cwd)}

def op_tmux_send(s):
    name=str(s.get('session','chatgpt')); cmd=str(s['command'])
    p=run(['tmux','send-keys','-t',name,'-l',cmd],timeout=30)
    if p.returncode==0: run(['tmux','send-keys','-t',name,'Enter'],timeout=30)
    return p,{'session':name}

def op_tmux_capture(s):
    name=str(s.get('session','chatgpt')); lines=max(50,min(int(s.get('lines',400)),4000))
    p=run(['tmux','capture-pane','-p','-S',f'-{lines}','-t',name],timeout=30)
    return p,{'session':name,'lines':lines}

def op_tmux_kill(s):
    name=str(s.get('session','chatgpt')); return run(['tmux','kill-session','-t',name],timeout=30),{'session':name}

def op_status(s):
    probes={}
    for name,argv in {'uname':['uname','-a'],'uptime':['uptime'],'memory':['free','-b'],'disk':['df','-B1',str(HOME)],'id':['id']}.items():
        p=run(argv,timeout=20); probes[name]={'rc':p.returncode,'out':text(p.stdout)[-12000:],'err':text(p.stderr)[-2000:]}
    proc=run(['bash','-lc','ps auxww --sort=-%cpu | head -80'],timeout=30)
    jobs=[]
    for m in JOBS.glob('*/meta.json'):
        try:
            x=json.loads(m.read_text()); x['alive']=pid_alive(x.get('pid',-1)); jobs.append(x)
        except Exception: pass
    payload={'schema':'CLAY_LOCAL_LIVE/v1','observed_at':now(),'bridge_version':VERSION,'home':str(HOME),'host':probes,'processes':text(proc.stdout)[-24000:],'jobs':jobs[-100:]}
    return subprocess.CompletedProcess(['status'],0,json.dumps(payload,indent=2).encode(),b''),{}

OPS={'exec':op_exec,'exec_async':op_exec_async,'job_status':op_job_status,'job_cancel':op_job_cancel,'read_file':op_read_file,'write_text':op_write_text,'write_base64':op_write_base64,'list_dir':op_list_dir,'git':op_git,'tmux_start':op_tmux_start,'tmux_send':op_tmux_send,'tmux_capture':op_tmux_capture,'tmux_kill':op_tmux_kill,'status':op_status}

def publish_receipt(receipt,stdout,stderr):
    d=RESULTS/'local_bridge/results'; (d/'receipts').mkdir(parents=True,exist_ok=True); (d/'logs').mkdir(parents=True,exist_ok=True)
    cid=receipt['command_id']; (d/'receipts'/f'{cid}.json').write_text(json.dumps(receipt,indent=2)+'\n'); (d/'logs'/f'{cid}.stdout.txt').write_bytes(stdout[-MAX_LOG:]); (d/'logs'/f'{cid}.stderr.txt').write_bytes(stderr[-MAX_LOG:]); (d/'LATEST.json').write_text(json.dumps(receipt,indent=2)+'\n'); push_results('local receipt: '+cid)

def execute(path):
    raw=path.read_bytes(); s=json.loads(raw)
    if s.get('schema')!='CLAY_LOCAL_COMMAND/v1': raise ValueError('BAD_SCHEMA')
    cid=str(s['command_id']); c=conn()
    if c.execute('SELECT 1 FROM done WHERE id=?',(cid,)).fetchone(): c.close(); return False
    started=now(); stdout=stderr=b''; meta={}
    try:
        op=str(s.get('op','exec'))
        if op not in OPS: raise ValueError('UNSUPPORTED_OP:'+op)
        p,meta=OPS[op](s); code=p.returncode; stdout=p.stdout or b''; stderr=p.stderr or b''; st='PASS' if code==0 else 'FAIL'
    except subprocess.TimeoutExpired as e:
        code=124; st='TIMEOUT'; stdout=e.stdout or b''; stderr=(e.stderr or b'')+repr(e).encode()
    except Exception as e:
        code=125; st='ERROR'; stderr=(repr(e)+'\n'+traceback.format_exc()).encode()
    receipt={'schema':'CLAY_LOCAL_RECEIPT/v1','command_id':cid,'command_sha256':sha(raw),'started_at':started,'finished_at':now(),'status':st,'exit_code':code,'op':s.get('op','exec'),'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'stdout_tail':text(stdout)[-24000:],'stderr_tail':text(stderr)[-24000:],'meta':meta,'execution_boundary':'LOCAL_USER_HOST_SHELL','automatic_root_grant':False}
    sync_results(); publish_receipt(receipt,stdout,stderr); c.execute('INSERT INTO done VALUES(?,?,?,?)',(cid,sha(raw),now(),code)); c.commit(); c.close(); return True

def publish_live():
    p,_=op_status({}); sync_results(); d=RESULTS/'local_bridge/results'; d.mkdir(parents=True,exist_ok=True); (d/'LIVE.json').write_bytes(p.stdout); push_results('local live telemetry',live=True)

def publish_error(e):
    try:
        sync_results(); d=RESULTS/'local_bridge/results'; d.mkdir(parents=True,exist_ok=True); (d/'DAEMON_ERROR.json').write_text(json.dumps({'schema':'CLAY_LOCAL_DAEMON_ERROR/v1','observed_at':now(),'error':repr(e),'traceback':traceback.format_exc()[-20000:]},indent=2)+'\n'); push_results('local daemon error')
    except Exception: pass

def main():
    last=0.0
    while True:
        try:
            sync_control(); q=CONTROL/QUEUE
            if q.exists():
                for p in sorted(q.glob('*.json')):
                    if execute(p): break
            if time.time()-last>=60: publish_live(); last=time.time()
        except Exception as e: publish_error(e)
        time.sleep(4)
if __name__=='__main__': main()
