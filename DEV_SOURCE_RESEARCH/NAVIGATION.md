# Developer / Research Navigation

Use this page when you need a specific evidence layer without scanning the repository.

| Need | Read |
|---|---|
| Technical architecture synthesis | [`README.md`](README.md) |
| Git-supported Frankenstein chronology | [`FRANKENSTEIN_GIT_CHRONOLOGY.md`](FRANKENSTEIN_GIT_CHRONOLOGY.md) |
| External primary literature and transfer boundaries | [`EXTERNAL_PRIMARY_CONTEXT.md`](EXTERNAL_PRIMARY_CONTEXT.md) |
| Unsupported labels, conflicts, and unresolved claims | [`GAPS_CONTRADICTIONS_AND_UNSUPPORTED_LABELS.md`](GAPS_CONTRADICTIONS_AND_UNSUPPORTED_LABELS.md) |
| Machine-readable historical/current failure constraints | [`../research_entity/architecture_archaeology/FAILURE_ATLAS.json`](../research_entity/architecture_archaeology/FAILURE_ATLAS.json) |
| Machine-readable surviving/reusable success patterns | [`../research_entity/architecture_archaeology/SUCCESS_PATTERN_ATLAS.json`](../research_entity/architecture_archaeology/SUCCESS_PATTERN_ATLAS.json) |
| Machine-readable Triggerword 3 evidence ledger | [`repository/TRIGGERWORD3_EVIDENCE_LEDGER_20260827.json`](repository/TRIGGERWORD3_EVIDENCE_LEDGER_20260827.json) |
| Root cleanup/migration protocol | [`repository/ROOT_MIGRATION_PLAN.md`](repository/ROOT_MIGRATION_PLAN.md) |
| Canonical read-only root inventory tool | [`repository/root_migration_inventory.py`](repository/root_migration_inventory.py) |
| AI installer contract | [`../AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json`](../AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json) |

## Authority re-entry

Before making a current-state claim, re-read:

1. `CLAY_EXECUTION_AUTHORITY.md`;
2. the owner authority it points to;
3. `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`;
4. current `main` source/receipts relevant to the claim.

The curation documents are indexes and syntheses. They are not a replacement authority.

## Evidence labels

```text
CURRENT_SOURCE
HISTORICAL_SOURCE
PROJECT_MEASUREMENT
EXTERNAL_PRIMARY
INFERENCE
OPEN_HYPOTHESIS
NEGATIVE_RESULT
```

Lifecycle values in the machine ledger additionally include:

```text
attempted
source-ready
measured
reproduced
contradicted
blocked
prepared-not-run
adopted
retired
```

## Minimal principle

Follow the deepest link that answers the question. Do not read thousands of archive files merely because they exist.
