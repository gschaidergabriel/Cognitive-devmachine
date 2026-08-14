# Frank `bug` -> Clay research feedback channel

Date: 2026-08-09
Origin: project-owner directive
Human trigger source: Dr. Andreas Unterweger using Frank

## Owner requirement

When Andreas sends exact `bug`, the immediately preceding Andreas question and immediately preceding Frank answer must be captured for research and preferably returned automatically to the separate Research Entity.

## Implemented architecture

The design preserves the hard Frank/Clay authority firewall:

`Andreas exact bug`
`-> Frank last-complete-pair capture`
`-> Frank UnifiedDB research_bug_reports`
`-> Frank exports/clay_pull/bugs/<bug_id>.json`
`-> Clay-owned pull ingest`
`-> Clay UnifiedDB clay_frank_bug_reports`
`-> READY dynamic work item origin=FRANK_EXPLICIT_BUG_FEEDBACK`

Frank never writes Clay and never receives Harness self-modification authority from the report.

## Frank-side artifacts

Repository: canonical `gschaidergabriel/frankv0.1` (connector alias `gschaidergabriel/Dr.-Unterweger`)

- `global/BUG_RESEARCH_FEEDBACK_PROTOCOL.md`
- `runtime/state/UNIFIEDDB_V13_BUG_RESEARCH_FEEDBACK.sql`
- `runtime/bridge/frank_bug_feedback.py`
- `.claude/hooks/frank_bug_prompt.py`
- `.claude/settings.json` hook wiring
- `.claude/hooks/frank_stop_guard.py` completed-output capture
- `tests/test_bug_research_feedback.py`
- `runtime/state/apply_current_schema.py` includes V13

Frank stores only a pending current input plus the last completed pair per session for this mechanism, not a duplicate full conversation database. Exact `bug` is excluded from pending-pair overwrite. Duplicate reports for the same pair are idempotent. Credential-like secrets are redacted before DB/export persistence.

## Clay-side artifacts

- `research_entity/global/FRANK_BUG_FEEDBACK_INGEST_PROTOCOL.md`
- `research_entity/runtime/RAE_UNIFIEDDB_V10_FRANK_BUG_FEEDBACK.sql`
- `research_entity/runtime/ingest_frank_bug_feedback.py`
- `tests/test_frank_bug_feedback_ingest.py`
- `research_entity/runtime/systemd/clay-frank-bug-ingest.service`
- `research_entity/runtime/systemd/frank-bug-ingest.env.example`

Valid new bugs become READY Research Entity work items after payload-hash verification. The ingest is idempotent. `--watch` supports a one-second Ubuntu-local pull loop.

## Executed development tests

Local deterministic prototypes executed before durable writes:

1. Frank capture sequence: non-bug input -> completed Frank output -> exact `bug` -> previous pair exported; repeated `bug` produced one stable report. PASS.
2. Clay ingest: valid export -> one Clay bug record + one READY work item; second ingest -> DUPLICATE. PASS.
3. Initial Clay ingest implementation failed with SQLite `22 values for 21 columns`; the INSERT was corrected and the test passed. Negative result preserved here.

These are development-sandbox tests, not proof that the migration/service is already deployed on Andreas' Ubuntu host.

## Deployment boundary

Repository implementation is committed. Actual live behavior on Andreas' Ubuntu developer system additionally requires:

- local Frank checkout updated to these commits;
- V13 applied by Research-Entity/installer authority, not Frank self-migration;
- Clay checkout updated;
- Clay bug ingest service configured/enabled (or equivalent Clay runtime integration).

Do not claim live automatic handoff until those host-side receipts exist.
