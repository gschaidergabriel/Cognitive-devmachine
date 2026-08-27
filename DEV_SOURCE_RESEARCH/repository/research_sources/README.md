# Research Source Archive

This tree is the project-wide source/evidence archive used by the Global Research Entity.

## Fundamental rule

Raw source bytes are immutable evidence. **Status belongs primarily to claims, not files.**

A historical document may contain simultaneously:
- still-current measurements;
- superseded architecture;
- explicitly refuted interpretations;
- open hypotheses.

Therefore the archive has two planes:

1. `raw_snapshot/` — immutable exact source snapshot (base64-split archive + hashes).
2. `status/` — continuously maintained claim/source views:
   - `current/`
   - `open/`
   - `superseded/`
   - `refuted/`

Never delete a source because its claim was refuted. Refutation increases its scientific value as negative lineage.

## Continuous operation

At every substantive project session, the Research Entity should:
1. detect new/changed source artifacts;
2. hash and register them;
3. extract claims/evidence relevant to the active task;
4. compare against current canonical state and later evidence;
5. update claim status with provenance;
6. preserve previous status events append-only;
7. update current status views;
8. write only justified research-state promotions to Canonical.

This is autonomous **during active research runs/sessions**. GitHub itself does not create new ChatGPT research work in the background unless an explicit scheduled automation/runner is separately configured.
