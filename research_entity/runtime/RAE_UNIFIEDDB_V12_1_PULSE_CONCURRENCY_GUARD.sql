-- CLAY U12.1 · SEGMENTED PULSE CONCURRENCY GUARD
-- Candidate additive migration over U12. UnifiedDB remains truth authority.
-- Prevents a stale publisher from creating a second CURRENT access generation when the
-- access_head moved after its initial read but before BEGIN IMMEDIATE.
PRAGMA foreign_keys=ON;

CREATE UNIQUE INDEX IF NOT EXISTS uq_access_generation_single_current
ON access_generation(status)
WHERE status='CURRENT';

-- Safety law:
-- * At most one access_generation may be CURRENT.
-- * A stale U12 publisher that attempts VERIFIED->CURRENT after another publisher won
--   must fail inside the transaction; rollback preserves the newer last-known-good head.
-- * This is an integrity backstop, not permission to skip explicit CAS/head verification.
