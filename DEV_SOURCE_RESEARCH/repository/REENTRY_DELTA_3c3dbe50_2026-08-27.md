# Triggerword-3 re-entry delta — main moved to 3c3dbe50

**Observed after the initial curation snapshot:** `main` advanced from `854f6bc87780f4a5242489a6c807d186b16a8c3d` to `3c3dbe5020f57065f47bd4d0a2dce3c537128797` while this pass was in progress.

This delta exists so the curation layer does not freeze an already-moving blocker.

## What changed

Commit `3c3dbe5020f57065f47bd4d0a2dce3c537128797`:

- preserves the provider-backed Bauleiter/Bugfix implementations and legacy build plan as quarantined donor provenance;
- changes the canonical Frankenstein orchestration plan to `QUARANTINED_NON_OPERATIVE_UNDER_CURRENT_PROVIDER_HARD_OFF`;
- makes canonical Frankenstein entrypoints resolve `SUPERVISOR_INBOX.json` before provider import, secret lookup, network, Aider or fallback dispatch;
- makes those entrypoints fail closed while current 9.13 HARD_OFF remains active;
- sets Together allowance explicitly to zero;
- reports `10/10 PASS` for focused local validation;
- explicitly scopes that evidence to source/local-unit closure only.

## What did NOT change

The current `SUPERVISOR_INBOX.json` still selects 9.13O and still records:

- provider routes admitted = false;
- Together forbidden;
- no paid fallback;
- runtime quiescence not passed;
- provider path runtime pass = false;
- whole EntityOS runtime pass = false;
- HCU full runtime pass = false;
- canonical semantics promotion = false;
- training credit = 0;
- the broader `stern.py -> harness_aider.py -> last-resort/llm.py` external free-pool caller boundary as a P0 closure target.

Therefore the correct interpretation is:

```text
Frankenstein canonical entrypoint gate: SOURCE/LOCAL-UNIT CLOSED at 3c3dbe50
Global provider/free-pool runtime path: NOT PROMOTED / inbox still P0
Provider execution authority: HARD_OFF
Provider runtime credit: 0
Whole EntityOS/HCU credit: 0
Training credit: 0
```

A later inbox/steering update may admit the new source closure, but this curation pass does not self-promote it.

## Curation impact

Earlier files in this branch remain valid where they say the provider-backed 72h orchestration is non-operative under HARD_OFF. Where they describe the caller gate as open, read that now as the **broader provider/free-pool path**, not as a claim that the newly gated Frankenstein canonical entrypoints still import providers before authority resolution.

## Evidence class

- `CURRENT_SOURCE`: commit `3c3dbe5020f57065f47bd4d0a2dce3c537128797`
- `CURRENT_SOURCE`: current `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
- `PROJECT_MEASUREMENT`: 10/10 local focused validation as reported by the commit, source/local-unit scope only
- `INFERENCE`: global runtime promotion remains unavailable because the selected inbox has not promoted it and explicitly keeps provider-path runtime pass false

## Next exact check

Re-read the selected supervisor inbox after the next authority cycle. Promote only the scope it explicitly admits; do not infer runtime/provider credit from the source gate or its local unit tests.
