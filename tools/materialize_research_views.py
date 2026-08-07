#!/usr/bin/env python3
"""Rebuild CURRENT/OPEN/SUPERSEDED/REFUTED views from append-only ledgers."""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "research_entity" / "ledgers" / "CLAIMS.jsonl"
EVENTS = ROOT / "research_entity" / "ledgers" / "CLAIM_STATUS_EVENTS.jsonl"
OUT = ROOT / "research_sources" / "status"


def read_jsonl(path: Path):
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    claims = {x["claim_id"]: x for x in read_jsonl(CLAIMS)}
    states = {cid: c.get("first_status", "OPEN") for cid, c in claims.items()}
    for ev in read_jsonl(EVENTS):
        states[ev["claim_id"]] = ev["to"]
    buckets = defaultdict(list)
    for cid, claim in claims.items():
        c = dict(claim); c["status"] = states[cid]; buckets[states[cid]].append(c)
    mapping = {"CURRENT":"current/CURRENT_CLAIMS.jsonl","OPEN":"open/OPEN_CLAIMS.jsonl","SUPERSEDED":"superseded/SUPERSEDED_CLAIMS.jsonl","REFUTED":"refuted/REFUTED_CLAIMS.jsonl","NEGATIVE_RESULT":"refuted/NEGATIVE_RESULTS_VIEW.jsonl"}
    for status, rel in mapping.items():
        p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True)+"\n" for x in buckets.get(status, [])), encoding="utf-8")
    print(json.dumps({k: len(v) for k,v in buckets.items()}, indent=2))

if __name__ == "__main__": main()
