#!/usr/bin/env python3
"""Authoritative BASE14 closure entrypoint.

Patch the v3 phase graph so the strict application adjudicator may return its explicit,
non-promoting 9/10 intermediate state; the immediately following H2 phase must then
supply FULL_FRANK_HANDOFF before v3's final apps_pass/work-package/promotion checks can
succeed.  No release condition is weakened.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import claycode_andreas_base14_closure_v3 as base

for index,(name,argv) in enumerate(base.PHASES):
    if name=='strict_apps':
        base.PHASES[index]=(name,[sys.executable,'tools/claycode_andreas_strict_application_adjudicator.py','--allow-pending-full-frank'])

if __name__=='__main__':
    raise SystemExit(base.main())
