#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("doomsday_forecast", ROOT / "tools" / "doomsday_forecast.py")
DF = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DF)


def writej(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture() -> Path:
    base = Path(tempfile.mkdtemp()) / "repo"
    for d in [
        "research_entity/rooms", "research_entity/forecast", "research_entity/global",
        "research_entity/archive_assimilation", "research_entity/claycode",
        "research_entity/harness", "research_entity/unifieddb", "research_entity/training_data",
    ]:
        (base / d).mkdir(parents=True, exist_ok=True)

    writej(base / "research_entity/rooms/PROGRAM_STATE.json", {"stage_gates": {
        "L0_ARCHIVE_ASSIMILATION": {"status": "IN_PROGRESS", "progress_source": {"kind": "archive_assimilation", "path": "research_entity/archive_assimilation/666_WORKSPACE.json", "percent_field": "combined_progress.exact_coverage_percent"}},
        "BASE_CLAYCODE_RELEASE": {"status": "BLOCKED", "progress_source": {"kind": "work_packages", "path": "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json", "field": "work_packages"}},
        "H1_REFERENCE_HARNESS": {"status": "BLOCKED", "progress_source": {"kind": "work_packages", "path": "research_entity/harness/HARNESS_WORKSPACE.json", "field": "work_packages", "include_prefixes": ["H1-"]}},
        "H2_CLAYCODE_HARNESS": {"status": "BLOCKED", "progress_source": {"kind": "work_packages", "path": "research_entity/harness/HARNESS_WORKSPACE.json", "field": "work_packages", "include_prefixes": ["H2-"]}},
        "H3_ONE_MODULE_FRANK": {"status": "BLOCKED", "progress_source": {"kind": "stage_workspace", "path": "research_entity/harness/HARNESS3_WORKSPACE.json", "field": "work_packages", "missing_means": 0}},
        "UDB_UNIFIED_DATABASE": {"status": "BLOCKED", "progress_source": {"kind": "stage_workspace", "path": "research_entity/unifieddb/UNIFIEDDB_RELEASE_WORKSPACE.json", "field": "work_packages", "missing_means": 0}},
        "DATA_LORA_TRAINING_DATA": {"status": "BLOCKED", "progress_source": {"kind": "stage_workspace", "path": "research_entity/training_data/LORA1_DATA_WORKSPACE.json", "field": "work_packages", "missing_means": 0}}
    }})
    writej(base / "research_entity/rooms/PROGRAM_THROUGHPUT.json", {"user_active_hours_per_day": 10, "observations": []})
    writej(base / "research_entity/rooms/CAPACITY_STATE.json", {"next_expected_change": "2026-08-11", "compute": {"available_now": ["Minisforum 790 Pro"], "expected_not_yet_available": ["VPS expected around 2026-08-16 with RTX 3090, 24 GB VRAM"]}})
    writej(base / "research_entity/archive_assimilation/666_WORKSPACE.json", {"combined_progress": {"exact_coverage_percent": 0}})
    writej(base / "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json", {"work_packages": {"a": {"status": "OPEN"}, "b": {"status": "OPEN"}}})
    writej(base / "research_entity/harness/HARNESS_WORKSPACE.json", {"work_packages": {"H1-a": {"status": "OPEN"}, "H1-b": {"status": "OPEN"}, "H2-a": {"status": "OPEN"}}})
    shutil.copy(ROOT / "research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json", base / "research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json")
    shutil.copy(ROOT / "research_entity/forecast/DOOMSDAY_CAPABILITY_RULES.json", base / "research_entity/forecast/DOOMSDAY_CAPABILITY_RULES.json")
    writej(base / "research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json", {"tools": [{"tool_name": "e2b", "provider": "E2B", "class": "remote_code_sandbox", "preferred_for": ["compiler runtime"], "status": "RUNTIME_VERIFIED"}]})
    (base / "research_entity/forecast/DOOMSDAY_EVENTS.jsonl").write_text("", encoding="utf-8")
    return base


def run(root: Path):
    return DF.resolve(root, DF.date(2026, 8, 9))


def row(result, row_id):
    return next(x for x in result["rows"] if x["row_id"] == row_id)


def main():
    tests = 0
    r0 = run(fixture())
    assert r0["conditional_on_immediate_training_authorization"] is True; tests += 1
    assert any(c["tool"] == "e2b" and c["state"] == "ACTIVE_UNCALIBRATED" for c in r0["capabilities"]); tests += 1

    rt = fixture(); w = json.loads((rt / "research_entity/archive_assimilation/666_WORKSPACE.json").read_text()); w["combined_progress"]["exact_coverage_percent"] = 50; writej(rt / "research_entity/archive_assimilation/666_WORKSPACE.json", w); r = run(rt)
    assert r["progress_percent"] > r0["progress_percent"] and r["forecast_high"] < r0["forecast_high"]; tests += 1

    rt = fixture(); (rt / "research_entity/forecast/DOOMSDAY_EVENTS.jsonl").write_text(json.dumps({"event_id":"a","type":"ACCELERATOR","status":"VERIFIED","affected_rows":["H3_ONE_MODULE_BINARY_FRANK"],"multiplier":0.5,"evidence_refs":["receipt:x"]})+"\n"); r=run(rt)
    assert row(r,"H3_ONE_MODULE_BINARY_FRANK")["event_factor"] == 0.5 and r["forecast_high"] < r0["forecast_high"]; tests += 1

    rt = fixture(); (rt / "research_entity/forecast/DOOMSDAY_EVENTS.jsonl").write_text(json.dumps({"event_id":"a","type":"ACCELERATOR","status":"HYPOTHESIS","affected_rows":["H3_ONE_MODULE_BINARY_FRANK"],"multiplier":0.2,"evidence_refs":["x"]})+"\n"); r=run(rt)
    assert r["forecast_high"] == r0["forecast_high"] and r["rejected_events"]; tests += 1

    rt=fixture(); writej(rt/"research_entity/global/NEW_RESEARCH_CAPABILITY.json", {"tool_name":"magic_trainer","provider":"New","class":"model_training","preferred_for":["fine-tuning trainer"],"status":"RUNTIME_VERIFIED"}); r=run(rt); c=next(x for x in r["capabilities"] if x["tool"]=="magic_trainer")
    assert c["state"]=="ACTIVE_UNCALIBRATED" and "FINAL_MODEL_FINE_TUNE" in c["relevant_rows"] and r["forecast_high"]==r0["forecast_high"]; tests += 1

    rt=fixture(); writej(rt/"research_entity/global/NEW_RESEARCH_CAPABILITY.json", {"tool_name":"magic_trainer","provider":"New","class":"model_training","status":"RUNTIME_VERIFIED","doomsday_forecast":{"impacts":[{"status":"VERIFIED","rows":["FINAL_MODEL_FINE_TUNE"],"multiplier":0.4,"evidence_refs":["bench:1"]}]}}); r=run(rt)
    assert row(r,"FINAL_MODEL_FINE_TUNE")["capability_factor"]==0.4 and r["forecast_high"]<r0["forecast_high"]; tests += 1

    rt=fixture(); writej(rt/"research_entity/global/FAKE_RESEARCH_CAPABILITY.json", {"tool_name":"fake","class":"model_training","status":"NOT_RUNTIME_VERIFIED","doomsday_forecast":{"impacts":[{"status":"VERIFIED","rows":["FINAL_MODEL_FINE_TUNE"],"multiplier":0.01,"evidence_refs":["fake"]}]}}); r=run(rt)
    assert row(r,"FINAL_MODEL_FINE_TUNE")["capability_factor"]==1.0 and r["forecast_high"]==r0["forecast_high"]; tests += 1

    rt=fixture()
    for name,m in [("a_trainer",0.7),("b_trainer",0.5)]: writej(rt/f"research_entity/global/{name.upper()}_RESEARCH_CAPABILITY.json", {"tool_name":name,"class":"model_training","status":"RUNTIME_VERIFIED","doomsday_forecast":{"impacts":[{"status":"VERIFIED","rows":["FINAL_MODEL_FINE_TUNE"],"multiplier":m,"evidence_refs":[f"bench:{name}"]}]}})
    r=run(rt); assert row(r,"FINAL_MODEL_FINE_TUNE")["capability_factor"]==0.5; tests += 1

    rt=fixture(); (rt/"research_entity/forecast/DOOMSDAY_EVENTS.jsonl").write_text(json.dumps({"event_id":"b","type":"BLOCKER","status":"VERIFIED","affected_rows":["UDB_UNIFIED_DATABASE"],"multiplier":2,"evidence_refs":["bug:1"]})+"\n"); r=run(rt)
    assert r["forecast_high"]>r0["forecast_high"]; tests += 1

    assert row(r0,"PROJECT_HARDWARE_DEPLOYMENT")["start_high"].date().isoformat() >= "2026-08-16"; tests += 1

    rt=fixture(); (rt/"research_entity/forecast/DOOMSDAY_EVENTS.jsonl").write_text(json.dumps({"event_id":"o","type":"OWNER_AUTHORIZATION","status":"VERIFIED","affected_rows":["OWNER_TRAINING_RELEASE_GATE"]})+"\n"); r=run(rt)
    assert r["conditional_on_immediate_training_authorization"] is False; tests += 1

    rt=fixture(); m=json.loads((rt/"research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json").read_text()); m["rows"]["CLAY_0_1_FULL_INTEGRATION"]["future_workspace"]="research_entity/release/CLAY_0_1_INTEGRATION_WORKSPACE.json"; writej(rt/"research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json",m); writej(rt/"research_entity/release/CLAY_0_1_INTEGRATION_WORKSPACE.json",{"status":"PASS"}); r=run(rt)
    assert row(r,"CLAY_0_1_FULL_INTEGRATION")["progress_percent"]==100 and r["progress_percent"]>r0["progress_percent"]; tests += 1

    rt=fixture(); (rt/"research_entity/forecast/DOOMSDAY_EVENTS.jsonl").write_text(json.dumps({"event_id":"elim","type":"ELIMINATION","status":"VERIFIED","affected_rows":["MODEL_EXPORT_RUNTIME_PACKAGE"],"evidence_refs":["compiler:bundle"]})+"\n"); r=run(rt)
    assert row(r,"MODEL_EXPORT_RUNTIME_PACKAGE")["remaining_days_high"]==0 and r["forecast_high"]<r0["forecast_high"]; tests += 1

    rt=fixture(); tp={"user_active_hours_per_day":10,"observations":[{"stage_id":"BASE_CLAYCODE_RELEASE","completed_fraction":0.5,"owner_active_hours":1}]}; writej(rt/"research_entity/rooms/PROGRAM_THROUGHPUT.json",tp); r=run(rt)
    assert row(r,"BASE_CLAYCODE_RELEASE")["effort_basis"]=="measured_stage_velocity" and row(r,"BASE_CLAYCODE_RELEASE")["remaining_days_high"] < row(r0,"BASE_CLAYCODE_RELEASE")["remaining_days_high"]; tests += 1

    rt=fixture(); reg=json.loads((rt/"research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json").read_text()); reg["tools"].append({"tool_name":"newapi","class":"model_training","status":"NOT_RUNTIME_VERIFIED"}); writej(rt/"research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json",reg); writej(rt/"research_entity/global/NEWAPI_RESEARCH_CAPABILITY.json",{"tool_name":"newapi","class":"model_training","status":"RUNTIME_VERIFIED"}); r=run(rt)
    assert next(x for x in r["capabilities"] if x["tool"]=="newapi")["state"]=="ACTIVE_UNCALIBRATED"; tests += 1

    rt=fixture(); writej(rt/"research_entity/global/CALENDAR_RESEARCH_CAPABILITY.json",{"tool_name":"calendar_api","class":"calendar","status":"RUNTIME_VERIFIED"}); r=run(rt)
    assert next(x for x in r["capabilities"] if x["tool"]=="calendar_api")["state"]=="NO_DIRECT_PATH_IMPACT" and r["forecast_high"]==r0["forecast_high"]; tests += 1

    rt=fixture(); m=json.loads((rt/"research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json").read_text()); m["rows"]["L0_ARCHIVE_ASSIMILATION"]["dependencies"]=["CLAY_0_1_ACCEPTANCE_RUN"]; writej(rt/"research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json",m)
    try: run(rt); raise AssertionError("cycle not detected")
    except ValueError as exc: assert "dependency_cycle" in str(exc); tests += 1

    print(f"DOOMSDAY_FORECAST_TESTS_PASS:{tests}")


if __name__ == "__main__":
    main()
