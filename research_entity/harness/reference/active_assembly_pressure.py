"""Non-authoritative diagnostics for FRANK ActiveAssembly selection pressure.

This module observes an already-compiled ActiveAssembly. It does not change selection,
truth state, ranking, re-expansion, or execution authority. The purpose is to make
conflict-slot pressure explicit so policy experiments can be replayed and compared
without silently changing current H1 reference semantics.
"""
from __future__ import annotations

import hashlib
import json


class ActiveAssemblyPressureError(ValueError):
    pass


def diagnose_active_assembly_pressure(assembly: dict) -> dict:
    if not isinstance(assembly, dict):
        raise ActiveAssemblyPressureError("BAD_ASSEMBLY")
    max_items = assembly.get("max_items")
    items = assembly.get("items")
    reexpand_refs = assembly.get("reexpand_refs", [])
    if not isinstance(max_items, int) or max_items <= 0:
        raise ActiveAssemblyPressureError("BAD_MAX_ITEMS")
    if not isinstance(items, list):
        raise ActiveAssemblyPressureError("BAD_ITEMS")
    if not isinstance(reexpand_refs, list):
        raise ActiveAssemblyPressureError("BAD_REEXPAND_REFS")

    conflict_selected = 0
    ordinary_selected = 0
    unknown_roles = 0
    for item in items:
        if not isinstance(item, dict):
            raise ActiveAssemblyPressureError("BAD_ITEM")
        role = item.get("selection_role")
        if role == "CONFLICT_VISIBILITY":
            conflict_selected += 1
        elif role == "ORDINARY":
            ordinary_selected += 1
        else:
            unknown_roles += 1

    selected_count = len(items)
    if selected_count > max_items:
        raise ActiveAssemblyPressureError("BUDGET_VIOLATION")

    conflict_slot_fraction = conflict_selected / max_items
    budget_utilization = selected_count / max_items
    ordinary_capacity_remaining = max(0, max_items - conflict_selected)

    if selected_count == max_items and conflict_selected == max_items:
        pressure_band = "SATURATED"
    elif conflict_slot_fraction >= 0.75:
        pressure_band = "HIGH"
    elif conflict_slot_fraction >= 0.50:
        pressure_band = "MEDIUM"
    elif conflict_selected > 0:
        pressure_band = "LOW"
    else:
        pressure_band = "NONE"

    result = {
        "schema": "frank.active-assembly-pressure.v0.1",
        "assembly_sha256": assembly.get("assembly_sha256"),
        "max_items": max_items,
        "selected_count": selected_count,
        "conflict_selected_count": conflict_selected,
        "ordinary_selected_count": ordinary_selected,
        "unknown_selection_role_count": unknown_roles,
        "conflict_slot_fraction": round(conflict_slot_fraction, 12),
        "budget_utilization": round(budget_utilization, 12),
        "ordinary_capacity_remaining": ordinary_capacity_remaining,
        "reexpand_ref_count": len(reexpand_refs),
        "pressure_band": pressure_band,
        "selection_policy_changed": False,
        "execution_authority": False,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    result["diagnostic_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result
