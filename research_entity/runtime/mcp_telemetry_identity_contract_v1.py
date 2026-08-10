from __future__ import annotations

"""Read-only contract probe for the VPS Frank telemetry database.

No schema mutation is performed. The probe distinguishes the existing general event substrate
from first-class identity/time columns needed for copy-entity and temporal-Pulse longitudinal
queries. Missing fields are negative evidence that feeds a later migration on a recovery copy.
"""

import sqlite3
from pathlib import Path
from typing import Any

REQUIRED_BASE = {
    "event_id","event_ts","ingest_ts","module","category","payload_json","entity_id"
}
REQUIRED_TEMPORAL_ENTITY_V2 = {
    "entity_version","artifact_digest","state_lineage_hash","lease_epoch","pulse_seq",
    "boot_id","invocation_id","gap_class"
}
RECOMMENDED_INDEX_GROUPS = {
    "entity_version_time": {"entity_id","entity_version","event_ts"},
    "artifact_time": {"artifact_digest","event_ts"},
    "pulse_entity_seq": {"entity_id","pulse_seq"},
    "boot_gap_time": {"boot_id","gap_class","event_ts"},
}


def inspect_connection(con: sqlite3.Connection) -> dict[str,Any]:
    con.row_factory=sqlite3.Row
    row=con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'").fetchone()
    if row is None:
        return {"status":"NO_EVENTS_TABLE","base_contract_pass":False,"temporal_entity_v2_pass":False}
    cols={str(r[1]) for r in con.execute("PRAGMA table_info(events)")}
    indexes=[]
    for idx in con.execute("PRAGMA index_list(events)"):
        name=str(idx[1])
        members=[str(r[2]) for r in con.execute(f"PRAGMA index_info('{name}')")]
        indexes.append({"name":name,"columns":members})
    missing_base=sorted(REQUIRED_BASE-cols)
    missing_v2=sorted(REQUIRED_TEMPORAL_ENTITY_V2-cols)
    index_coverage={}
    for label,needed in RECOMMENDED_INDEX_GROUPS.items():
        index_coverage[label]=any(needed.issubset(set(x["columns"])) for x in indexes)
    return {
        "status":"TEMPORAL_ENTITY_V2_READY" if not missing_v2 else "IDENTITY_TIME_FIELDS_NOT_FIRST_CLASS",
        "columns":sorted(cols),
        "missing_base":missing_base,
        "missing_temporal_entity_v2":missing_v2,
        "base_contract_pass":not missing_base,
        "temporal_entity_v2_pass":not missing_v2,
        "indexes":indexes,
        "recommended_index_coverage":index_coverage,
        "migration_required":bool(missing_v2 or not all(index_coverage.values())),
        "authority":"READ_ONLY_SCHEMA_OBSERVATION_NO_MIGRATION_AUTHORITY",
    }


def inspect_path(path:str) -> dict[str,Any]:
    p=Path(path)
    if not p.exists():
        return {
            "status":"DB_NOT_FOUND",
            "path":str(p),
            "base_contract_pass":False,
            "temporal_entity_v2_pass":False,
            "migration_required":False,
            "authority":"READ_ONLY_SCHEMA_OBSERVATION_NO_MIGRATION_AUTHORITY",
        }
    con=sqlite3.connect(f"file:{p}?mode=ro",uri=True,timeout=5)
    try:
        result=inspect_connection(con)
        result["path"]=str(p)
        result["size_bytes"]=p.stat().st_size
        return result
    finally:
        con.close()
