#!/usr/bin/env python3
"""Thin corpus-v2 adapter. Paid-create semantics stay owned by launch_together_v1."""
import subprocess, sys
from pathlib import Path
import launch_together_v1 as canonical

HERE=Path(__file__).resolve().parent
canonical.TRAIN=HERE/"train_v2.jsonl"
canonical.VALID=HERE/"validation_v2.jsonl"

def run_v2_checks():
    subprocess.run([sys.executable,str(HERE/"generate_sft_v2.py")],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(canonical.TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/"validate_sft_v1.py"),str(canonical.VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/"corpus_split_gate_v2.py"),str(canonical.TRAIN),str(canonical.VALID)],check=True)

canonical.run_local_checks=run_v2_checks

if __name__=="__main__": canonical.main()
