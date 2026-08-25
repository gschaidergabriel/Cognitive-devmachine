#!/usr/bin/env python3
"""Fail-closed supersession marker for the Trigger-2 swarm binding V2 pilot.

The previously committed V2 generator is preserved in Git history for donor/reproduction
purposes, but MUST NOT be used to generate training candidates after the later swarm
review found a scientific nuisance shortcut:

    I(target_symbol ; train_template) = 2.0 bits

Cause: each train template owned a disjoint three-symbol placeholder pool. The generic
candidate schema gate did not test this nuisance relation, so 144/144 schema-gate PASS
was not scientific shortcut acceptance.

Reproduce the prior gate-aligned donor only from its exact historical identity:
    commit: bf87ddd67c41021e39c86b941af8740bd3853698
    blob:   5cc190fcffa749485a03964a801aeb9ffa6e23ff

Retained current path:
    tools/trigger2_dynamic_binding_blueprint_v2.py
    tools/trigger2_dynamic_binding_materializer_v1.py

The retained materializer keeps real ABI rendering fail-closed, reserves an unseen
symbol partition and holdout permutation/template, and remains PRE-HOLDOUT until the
exact accepted 46-atom ABI inventory + pinned tokenizer evidence are available.

This file intentionally performs no dataset generation and mints no dataset/training,
J-Space, HCU, EntityOS or runtime credit.
"""
from __future__ import annotations
import json

STATUS = {
    "schema": "TRIGGER2_SWARM_BINDING_GENERATOR_SUPERSESSION/v1",
    "status": "SUPERSEDED_FAIL_CLOSED",
    "reason": "TARGET_SYMBOL_TEMPLATE_NUISANCE_MI_2_BITS",
    "prior_donor_commit": "bf87ddd67c41021e39c86b941af8740bd3853698",
    "prior_donor_blob": "5cc190fcffa749485a03964a801aeb9ffa6e23ff",
    "retained_blueprint": "tools/trigger2_dynamic_binding_blueprint_v2.py",
    "retained_materializer": "tools/trigger2_dynamic_binding_materializer_v1.py",
    "training_ready": False,
    "accepted_dataset_tokens": 0,
    "training_credit": 0
}

if __name__ == "__main__":
    print(json.dumps(STATUS, sort_keys=True))
    raise SystemExit(2)
