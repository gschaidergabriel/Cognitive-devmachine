#!/usr/bin/env python3
"""Deterministic PASS/FAIL receipt constructor for bounded acceptance checks."""
from __future__ import annotations
import re
HEX64=re.compile(r"^[0-9a-f]{64}$")
def make_receipt(*,command:str,exit_code:int,tested_blobs:dict[str,str],unproven_layers:list[str],runtime_credit:int=0)->dict:
    if not isinstance(command,str) or not command.strip(): raise ValueError("command required")
    if not isinstance(exit_code,int): raise ValueError("exit_code must be int")
    if runtime_credit != 0: raise ValueError("unproven runtime_credit must be 0")
    if not tested_blobs or any(not isinstance(p,str) or not HEX64.match(h) for p,h in tested_blobs.items()): raise ValueError("tested_blobs require path -> lowercase sha256")
    if not isinstance(unproven_layers,list): raise ValueError("unproven_layers must be list")
    return {"schema":"ACCEPTANCE_KIT_RECEIPT/v1","verdict":"PASS" if exit_code==0 else "FAIL","command":command,"exit_code":exit_code,"tested_blobs":dict(sorted(tested_blobs.items())),"runtime_credit":0,"unproven_layers":list(unproven_layers)}
