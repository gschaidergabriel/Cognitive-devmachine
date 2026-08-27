#!/usr/bin/env python3
"""WP14 strict audit plus independent real-Ubuntu-desktop verification.

The base auditor already rechecks the strict target receipt, all ten real application
receipts, full FRANK and P0/P1 defects.  This wrapper adds an independent APP-05 desktop
check so a mapped-window target claim must agree across:
  * raw APP05_UBUNTU_DESKTOP target receipt,
  * GUI_INTERACTIVE real per-app receipt,
  * strict target adjudication,
  * final WP14 manifest.

Any mismatch rewrites the manifest fail-closed before the workspace promoter can see it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import claycode_base_wp14_strict_audit as base

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json"
DESKTOP = ROOT / "research_entity/claycode/target/APP05_UBUNTU_DESKTOP.json"
GUI_APP = ROOT / "research_entity/claycode/target_receipts/apps/GUI_INTERACTIVE.json"
STRICT = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("NOT_OBJECT:" + str(path))
    return value


def validate_desktop() -> tuple[bool, list[str], dict]:
    reasons: list[str] = []
    detail: dict = {}
    for label, path in (("desktop", DESKTOP), ("gui_app", GUI_APP), ("strict", STRICT)):
        if not path.exists():
            reasons.append("MISSING:" + label)
            continue
        try:
            detail[label] = load(path)
        except Exception as exc:
            reasons.append("INVALID:" + label + ":" + type(exc).__name__)

    desktop = detail.get("desktop") or {}
    observed = desktop.get("observed") if isinstance(desktop.get("observed"), dict) else {}
    if desktop:
        if desktop.get("target_host") != TARGET: reasons.append("DESKTOP_WRONG_TARGET")
        if desktop.get("application") != "GUI_INTERACTIVE": reasons.append("DESKTOP_WRONG_APP")
        if desktop.get("pass") is not True: reasons.append("DESKTOP_NOT_PASS")
        if desktop.get("counts_as_target_acceptance") is not True: reasons.append("DESKTOP_NOT_TARGET_ACCEPTING")
        if desktop.get("authority_boundary_preserved") is not True: reasons.append("DESKTOP_AUTHORITY_BOUNDARY")
        if observed.get("io_mode") != "TK_REAL_DESKTOP_EVENT_LOOP": reasons.append("DESKTOP_WRONG_IO_MODE")
        if observed.get("window_was_mapped") is not True: reasons.append("DESKTOP_WINDOW_NOT_MAPPED")
        if (desktop.get("negative_or_failure_path") or {}).get("forbidden_event_rejected") is not True: reasons.append("DESKTOP_NEGATIVE_PATH_NOT_PASS")

    gui = detail.get("gui_app") or {}
    if gui:
        if gui.get("pass") is not True: reasons.append("GUI_APP_NOT_PASS")
        if gui.get("target_host") != TARGET: reasons.append("GUI_APP_WRONG_TARGET")
        if gui.get("evidence_class") != "ANDREAS_UBUNTU_REAL_APPLICATION": reasons.append("GUI_APP_NOT_REAL_TARGET_EVIDENCE")
        if gui.get("desktop_receipt_sha256") != (sha(DESKTOP) if DESKTOP.exists() else None): reasons.append("GUI_APP_DESKTOP_HASH_MISMATCH")
        if (gui.get("positive_test") or {}).get("real_ubuntu_desktop_pass") is not True: reasons.append("GUI_APP_DESKTOP_FLAG_NOT_PASS")

    strict = detail.get("strict") or {}
    if strict:
        if strict.get("overall_pass") is not True: reasons.append("STRICT_NOT_PASS")
        if strict.get("desktop_gui_target_pass") is not True: reasons.append("STRICT_DESKTOP_FLAG_NOT_PASS")
        if strict.get("desktop_gui_receipt_sha256") != (sha(DESKTOP) if DESKTOP.exists() else None): reasons.append("STRICT_DESKTOP_HASH_MISMATCH")
        apps = strict.get("applications") if isinstance(strict.get("applications"), dict) else {}
        strict_gui = apps.get("GUI_INTERACTIVE") if isinstance(apps.get("GUI_INTERACTIVE"), dict) else {}
        if (strict_gui.get("real_ubuntu_desktop") or {}).get("pass") is not True: reasons.append("STRICT_GUI_DESKTOP_BINDING_MISSING")

    return not reasons, reasons, detail


def fail_manifest(reasons: list[str], detail: dict) -> None:
    if MANIFEST.exists():
        manifest = load(MANIFEST)
    else:
        manifest = {"schema_version": "1.3", "manifest": "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST"}
    failed = list(manifest.get("failed_work_packages") or [])
    if "CC-WP-10-GENERAL-APP-SUITE" not in failed:
        failed.append("CC-WP-10-GENERAL-APP-SUITE")
    if "CC-WP-14-BASE-AUDIT" not in failed:
        failed.append("CC-WP-14-BASE-AUDIT")
    manifest["failed_work_packages"] = failed
    manifest["general_purpose_gate_pass"] = False
    manifest["claycode_release_gate_pass"] = False
    manifest["promotion_allowed"] = False
    manifest["desktop_gui_independent_audit"] = {
        "pass": False,
        "reasons": reasons,
        "desktop_receipt_path": str(DESKTOP.relative_to(ROOT)),
        "desktop_receipt_sha256": sha(DESKTOP) if DESKTOP.exists() else None,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    rc = base.main()
    desktop_ok, reasons, detail = validate_desktop()
    if rc != 0 or not desktop_ok:
        fail_manifest(reasons or ["BASE_WP14_NOT_PASS"], detail)
        print(json.dumps({"pass": False, "base_wp14_returncode": rc, "desktop_reasons": reasons}, ensure_ascii=False))
        return 2

    manifest = load(MANIFEST)
    if manifest.get("general_purpose_gate_pass") is not True or manifest.get("claycode_release_gate_pass") is not True or manifest.get("promotion_allowed") is not True:
        fail_manifest(["BASE_MANIFEST_FLAGS_NOT_PASS"], detail)
        return 2

    manifest["schema_version"] = "1.3"
    manifest["desktop_gui_independent_audit"] = {
        "pass": True,
        "desktop_receipt_path": str(DESKTOP.relative_to(ROOT)),
        "desktop_receipt_sha256": sha(DESKTOP),
        "gui_app_receipt_path": str(GUI_APP.relative_to(ROOT)),
        "gui_app_receipt_sha256": sha(GUI_APP),
        "strict_target_receipt_path": str(STRICT.relative_to(ROOT)),
        "strict_target_receipt_sha256": sha(STRICT),
        "required_io_mode": "TK_REAL_DESKTOP_EVENT_LOOP",
        "window_was_mapped": True,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "desktop_gui_independent_audit": True, "manifest": str(MANIFEST.relative_to(ROOT)), "desktop_sha256": sha(DESKTOP)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
