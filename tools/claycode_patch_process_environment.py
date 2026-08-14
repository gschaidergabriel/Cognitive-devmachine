#!/usr/bin/env python3
"""One-shot repair: process.exec must not inherit ambient host credentials."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/'tools/claycode_base_runtime.py'
OLD='child_env={k:v for k,v in os.environ.items() if not k.startswith("CLAYCODE_CAPABILITY_") and k not in {"CLAYCODE_AUTHORITY_CONTEXT","CLAYCODE_RUNTIME_SECRET"}}'
NEW='child_env={"LANG":os.environ.get("LANG","C.UTF-8"),"LC_ALL":os.environ.get("LC_ALL","C.UTF-8")}'
def main():
 text=PATH.read_text(encoding='utf-8')
 if NEW in text: print({'changed':False});return 0
 if OLD not in text: raise SystemExit('PROCESS_CHILD_ENV_SITE_NOT_FOUND')
 PATH.write_text(text.replace(OLD,NEW,1),encoding='utf-8');print({'changed':True});return 0
if __name__=='__main__':raise SystemExit(main())
