# GateFlow semantic branch freshness gate

Status: CANDIDATE / coordination-only.

This gate operationalizes the existing GateFlow law that freshness is semantic, not merely branch age.

## Inputs

Each candidate snapshot binds:

- candidate/PR identity;
- branch and base branch;
- `ahead_by` / `behind_by` as diagnostics only;
- exact candidate changed-file set;
- exact `main`-since-merge-base changed-file set;
- optional declared dependency-cone patterns;
- explicit supersession/stacking metadata when known.

## Invariants

1. `behind_by` alone MUST NEVER classify a candidate RED.
2. Direct changed-file overlap with current main is RED.
3. A current-main change inside the candidate's declared dependency cone is RED.
4. Executable/runtime/schema/authority/tool/test surfaces with main movement but without a proven overlap are AMBER and must rerun cheap gates before scarce target scheduling.
5. Pure append-only research/receipt branches are GREEN when no declared dependency-cone hit exists, even when hundreds of commits behind.
6. Stacked PRs are evaluated against their parent before main.
7. Explicitly superseded candidates may be recommended for closure only after supersession confirmation. The classifier itself performs no destructive action.
8. RED candidates cannot be treated as promotion-ready.
9. Missing/invalid snapshot fields fail closed at the classifier boundary.

## Recommendations

- `REBASE_AND_RERUN`
- `RERUN_CHEAP_GATES`
- `FOLLOW_STACKED_PARENT`
- `KEEP_ACTIVE_NO_REBASE_REQUIRED`
- `SAFE_TO_CLOSE_AFTER_SUPERSESSION_CONFIRMATION`

## Non-authority

The tool is read-only classification. It does not merge, rebase, close, delete, promote, credit workspace progress, mutate Frank, authorize training, or grant runtime/effect authority.
