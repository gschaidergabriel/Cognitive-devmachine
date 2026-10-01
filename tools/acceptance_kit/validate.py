#!/usr/bin/env python3
"""Draft 2020-12 validator CLI for NEEDLE_ENTITY_PACKET/v1 and needle-entity-result/v1."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parent
SCHEMAS={
 "packet": ROOT/"schemas"/"needle_entity_packet.schema.json",
 "result": ROOT/"schemas"/"needle_entity_result.schema.json",
}
def validate_obj(kind: str, obj: object) -> list[str]:
    schema=json.loads(SCHEMAS[kind].read_text(encoding="utf-8"))
    validator=Draft202012Validator(schema)
    return [e.message for e in sorted(validator.iter_errors(obj),key=lambda e:list(e.path))]
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("kind",choices=sorted(SCHEMAS)); ap.add_argument("path",type=Path); a=ap.parse_args()
    obj=json.loads(a.path.read_text(encoding="utf-8")); errs=validate_obj(a.kind,obj)
    print(json.dumps({"schema":"ACCEPTANCE_KIT_SCHEMA_VALIDATION/v1","pass":not errs,"errors":errs},sort_keys=True)); return 0 if not errs else 2
if __name__=="__main__": raise SystemExit(main())
