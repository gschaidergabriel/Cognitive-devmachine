#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED_MODULES = {
    "token_api",
    "de_to_clay_translator",
    "clay_to_de_translator",
    "proactive_agency",
    "web_ingress_guard",
    "research_entity_bridge",
}

REQUIRED_INVARIANT_TOKENS = {
    "self.root",
    "CLAYCODE_ONLY",
    "TARGET_VPS",
    "token",
    "proactive",
    "UNTRUSTED_EXTERNAL_DATA",
}


def audit_freeze(doc: dict) -> dict:
    module_ids = {m.get("id", "") for m in doc.get("modules", []) if isinstance(m, dict)}
    invariant_text = "\n".join(map(str, doc.get("invariants", [])))
    missing_modules = sorted(REQUIRED_MODULES - module_ids)
    missing_invariants = sorted(t for t in REQUIRED_INVARIANT_TOKENS if t not in invariant_text)
    failures = []
    if doc.get("target_host") != "TARGET_VPS":
        failures.append({"code": "TARGET_HOST_STALE", "observed": doc.get("target_host"), "expected": "TARGET_VPS"})
    if missing_modules:
        failures.append({"code": "OWNER_FIXED_MODULES_MISSING", "missing": missing_modules})
    if missing_invariants:
        failures.append({"code": "OWNER_FIXED_INVARIANTS_MISSING", "missing": missing_invariants})
    return {
        "pass": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "rule": "A reference freeze may not be release-audited as current when newer owner-fixed target semantics are absent.",
    }


def main(argv):
    if len(argv) != 2:
        print("usage: harness_target_contract_gate.py <freeze.json>", file=sys.stderr)
        return 2
    doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    result = audit_freeze(doc)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
