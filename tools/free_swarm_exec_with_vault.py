#!/usr/bin/env python3
"""Exec a Free-Swarm child with all allow-listed provider credentials found locally.

Secret values are never printed or written. Only counts/fingerprints are persisted.
The parser intentionally does not `source` shell files; only KEY=VALUE assignments
whose names match admitted FREE providers are accepted.
"""
from __future__ import annotations
import hashlib, json, os, re, shlex, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ART=Path(os.getenv('CLAY_SWARM_ARTIFACT_ROOT','/artifacts/clay-entityos-swarm'))
ALLOW_DIRS=[ROOT/'research_entity/private',ROOT/'vault',ROOT/'secrets',Path('/run/secrets'),Path('/artifacts'),Path('/cache')]
PROVIDER_PATTERNS={
 'groq':re.compile(r'^GROQ[A-Z0-9_]*KEY[A-Z0-9_]*$'),
 'mistral':re.compile(r'^MISTRAL[A-Z0-9_]*KEY[A-Z0-9_]*$'),
 'nvidia':re.compile(r'^(?:NVIDIA|NGC)[A-Z0-9_]*KEY[A-Z0-9_]*$'),
 'openrouter':re.compile(r'^OPENROUTER[A-Z0-9_]*KEY[A-Z0-9_]*$'),
}
KNOWN={'GROQ_API_KEY':'groq','MISTRAL_API_KEY':'mistral','NVIDIA_API_KEY':'nvidia','NVIDIA_NIM_API_KEY':'nvidia','NGC_API_KEY':'nvidia','OPENROUTER_API_KEY':'openrouter'}

def provider_for(name:str)->str|None:
 if name in KNOWN:return KNOWN[name]
 for p,rx in PROVIDER_PATTERNS.items():
  if rx.match(name):return p
 return None

def parse_value(raw:str)->str:
 raw=raw.strip()
 if not raw:return ''
 try:
  parts=shlex.split(raw,comments=True,posix=True)
  return parts[0] if parts else ''
 except Exception:
  return raw.strip().strip('"').strip("'")

def collect()->tuple[dict[str,str],dict[str,list[str]]]:
 env=dict(os.environ); vals={p:[] for p in PROVIDER_PATTERNS}
 for k,v in list(env.items()):
  p=provider_for(k)
  if p and v.strip() and v.strip() not in vals[p]:vals[p].append(v.strip())
 seen=set()
 for d in ALLOW_DIRS:
  if not d.exists():continue
  paths=[d] if d.is_file() else []
  if d.is_dir():
   for pat in ('*.env','*.secret','*.secrets','*TOKEN*','*KEY*'):paths.extend(d.rglob(pat))
  for path in paths:
   try:
    rp=path.resolve()
    if rp in seen or not path.is_file() or path.stat().st_size>2_000_000:continue
    seen.add(rp);text=path.read_text(encoding='utf-8',errors='ignore')
   except OSError:continue
   for line in text.splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s:continue
    if s.startswith('export '):s=s[7:].lstrip()
    name,raw=s.split('=',1);name=name.strip();p=provider_for(name)
    if not p:continue
    value=parse_value(raw)
    if value and value not in vals[p]:vals[p].append(value)
 for p,items in vals.items():
  if items:env[f'{p.upper()}_API_KEYS']=','.join(items)
 if vals['groq']:env.setdefault('GROQ_API_KEY',vals['groq'][0])
 if vals['mistral']:env.setdefault('MISTRAL_API_KEY',vals['mistral'][0])
 if vals['nvidia']:env.setdefault('NVIDIA_API_KEY',vals['nvidia'][0])
 if vals['openrouter']:env.setdefault('OPENROUTER_API_KEY',vals['openrouter'][0])
 return env,vals

def fp(v:str)->str:return hashlib.sha256(v.encode()).hexdigest()[:10]

def main()->int:
 if len(sys.argv)<2:
  print('usage: free_swarm_exec_with_vault.py COMMAND [ARGS...]',file=sys.stderr);return 2
 env,vals=collect();ART.mkdir(parents=True,exist_ok=True)
 summary={'schema':'CLAY_FREE_SWARM_CREDENTIAL_POOL/v1','providers':{p:{'keys':len(v),'fingerprints':[fp(x) for x in v]} for p,v in vals.items()},'secret_values_logged':False}
 (ART/'CREDENTIAL_POOL.json').write_text(json.dumps(summary,indent=2)+'\n')
 os.execvpe(sys.argv[1],sys.argv[1:],env)
 return 127
if __name__=='__main__':raise SystemExit(main())
