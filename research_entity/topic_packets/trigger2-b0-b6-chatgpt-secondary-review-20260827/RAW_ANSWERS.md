# Trigger2 B0-B6 curriculum review -- chatgpt-secondary, 2026-08-27

5 real messages sent via `stern.py chatgpt-senden --prompts [...] --num-workers 1`
into the ChatGPT project "clay science pipeline", one at a time (single-line
text -- see LESSON below). Answers harvested by navigating each conversation
URL directly with `$B goto/text` (targeted harvest of just these 5 URLs, not
a full `chatgpt-ernten` pass over the whole historical `sent_urls_v2.txt`).

Conversation URLs (2026-08-27T03:48-03:50 +07:00):
1. B0/B1: https://chatgpt.com/g/g-p-6a7644f542508191b324659134fb593b-clay-science-pipeline/c/6a8f5114-1244-83ec-b0e1-89a4480c8fc9
2. B2/B3: https://chatgpt.com/g/g-p-6a7644f542508191b324659134fb593b-clay-science-pipeline/c/6a8f515a-d4dc-83ec-b03e-6572b4d2a6b9
3. B4/B5: https://chatgpt.com/g/g-p-6a7644f542508191b324659134fb593b-clay-science-pipeline/c/6a8f516c-12e4-83ec-9e82-a5d16956f41f
4. B6: https://chatgpt.com/g/g-p-6a7644f542508191b324659134fb593b-clay-science-pipeline/c/6a8f517d-79ec-83ec-9a46-7cd938beca20
5. Cross-cutting ranking: https://chatgpt.com/g/g-p-6a7644f542508191b324659134fb593b-clay-science-pipeline/c/6a8f518f-8ec0-83ec-8dad-7c4b7770215f

## LESSON found while sending (real, live)

Multi-paragraph message text with literal newlines gets typed via
Playwright `page.keyboard.type()` in `chatgpt_burst_worker_v2.sh`. A
literal `\n` (0x0A) is typed as a real Enter keypress, and ChatGPT's
compose box submits-on-Enter -- so a multi-line message gets SENT PARTWAY
THROUGH TYPING, comes back empty, and the script's retry logic marks it
FAILED_TYPE even though a truncated message actually went out (first live
attempt today: msg1 sent as-drafted with real newlines -> FAILED_TYPE,
landed a garbage half-typed message in a throwaway conversation). Fix:
single-line messages only (join paragraphs with spaces). Documented as a
code comment in `chatgpt_burst_worker_v2.sh` above `INPUT_SEL`.

## Q1 -- B0/B1 (codebook-order leak, flag consistency)

ChatGPT (hedged, correctly): codebook-order leak would be real IF the
class->ordinal mapping were fixed across examples (e.g. ALLOW always
`:00`), but said it could not tell from the 2 samples alone whether
production data already randomizes it. Also flagged
`positive_jspace_label` as a possible label side-channel if visible
upstream of split/sampling, and cross-family (B0 vs B1) semantic-duplicate
leakage across train/holdout splits as a bigger structural risk than the
flag combination itself.

**Self-verification (claude-code-lead, done):** checked
`TRIGGER2_B1_TRAIN_BALANCED_2ORDER_V1.jsonl` (n=4464) directly --
extracted the ALLOW/DENY ordinal from all 2000 sampled prompts. Ordinal
assignment is NOT fixed: ALLOW appears bound to `:00`-`:09`+ in
roughly even distribution (192/192/192/192/192/176/144/144/144/144 for
the top 10 values), same for DENY. **The flagged risk does NOT
materialize in this file -- REFUTED for B1_TRAIN_BALANCED_2ORDER.** Did
not check B0 (no codebook indirection there, word labels only, risk
doesn't apply) or `B1_BINDING_MATERIALIZED` (larger file, not checked in
this pass).

## Q2 -- B2/B3 (field-name split, prior-override shortcut)

ChatGPT: (a) `queried_class_` vs `queried_class` across two files sharing
schema `CLAY_TRIGGER2_B3_MULTIHOP_DEREFERENCE_CANDIDATE/v1` is a real bug,
not an intentional family-specific field -- noted that `audit_unresolvable()`
itself reads the buggy `queried_class_` name, which is why the self-audit
doesn't catch it. (b) B2_PRIOR_OVERRIDE's "NOTE reference only / CODEBOOK
current, authoritative" framing gives a shallow lexical-marker shortcut
("find the block literally labelled current, authoritative") that could
reach high accuracy without doing real prior-override binding -- flagged
as a scope question (fine if the claim is just "pick the authoritative
block", not fine if the claim is "semantic prior override"). (c) unprompted
extra finding: generator docstring says "half the rows" agree/disagree on
the distractor, but full-permutation enumeration over 6 distractor_perm
values actually yields 1/6 agree, 5/6 disagree, and the existing test only
checks `agree_rows > 0`.

**Self-verification (claude-code-lead, done), both CONFIRMED:**
- `tools/trigger2_b3_multihop_dereference_generator_v1.py` line 111 writes
  `"queried_class": queried_class` (MULTI_HOP_DEREF branch); line 195
  writes `"queried_class_": queried_class` (UNRESOLVABLE_CHAIN_REJECTION
  branch, trailing underscore); `audit_unresolvable()` at line 214 reads
  `r["queried_class_"]`. Same file, same schema id, real typo-shaped
  inconsistency. Affects all 1620 UNRESOLVABLE_CHAIN_REJECTION rows in
  `TRIGGER2_B3_UNRESOLVABLE_CHAIN_REJECTION_CANDIDATE_V1.jsonl`. **BUG,
  CONFIRMED, not yet fixed in this pass** (fix = rename + regenerate +
  update audit + cross-family schema-contract test, left for a follow-up
  build task, not done here).
- `distractor_agrees_with_current` distribution counted directly on
  `TRIGGER2_B2_PRIOR_OVERRIDE_CANDIDATE_V1.jsonl` (n=1080): **180 True /
  900 False = exactly 1/6 vs 5/6**, not 50/50. Docstring in
  `tools/trigger2_b2_prior_override_remap_stale_generator_v1.py` line 19
  ("Half the rows have the distractor AGREE...") does not match actual
  output. **CONFIRMED doc/data mismatch**, low severity (doesn't affect
  training correctness, just misleading comment + weak test).

## Q3 -- B4/B5 (multi-digit ordinal tokenization, position shortcut)

ChatGPT: multi-digit ordinals (B4: 20-99, B5: 200-299) were NOT covered by
the earlier digit-atom ABI fix (commit 8840389), which only tested bare
single digits 0-9 preceded by whitespace, not `:NN`/`:NNN` suffixes after
a colon. Correctly notes both B4/B5 generators already mark these rows
`training_eligible=false` (quarantined, placeholder ABI atoms, no real
tokenizer binding yet) -- so this is an open unknown, not a demonstrated
bug, and doesn't block anything currently. Also confirmed
`queried_position_in_codebook` is computed consistently in both
(`order.index(queried)`) and is NOT rendered into the prompt itself in
either file -- flagged a hypothetical risk only if a trainer accidentally
serializes the full JSON row instead of just prompt/target.

**Self-verification:** not independently re-run in this pass (would need
a real tokenizer sweep matching the 8840389 methodology, out of scope for
this review round). Left as an open item, consistent with ChatGPT's own
"UNKNOWN, not yet a demonstrated bug" framing.

## Q4 -- B6 (round1_/round2_ vs flat scores field-shape divergence)

ChatGPT: NOT the same class of bug as the earlier confirmed B6 issue
(that one omitted the family-convention key entirely and broke generic
grouping; the current GWT generator has a regression test requiring both
`family` and `curriculum_family`). Current divergence
(`scores`/`repeats`/`score_winner`/`repeat_count_winner` in
COMPETITION_BROADCAST vs `round1_scores`/`round1_repeats`/`round1_winner`/
`round1_repeat_count_winner` in CAUSAL_REENTRY) is legitimate in part
(one-round vs two-round task), but is still the same *class* of hazard
(same schema id, same round-1 concept, different key names) --
recommends additive aliasing rather than a full rename. On leakage:
confirmed the generator crosses every score permutation with every
repeat-count permutation independently (288/864 agree, 576/864 disagree,
matches its own audit), so "always pick highest repeat count" only gets
1/3 -- no repeat-count shortcut to the score-based target. Flagged that
`score_winner`/`round1_winner`/`round2_scores`/`distinguishing_row` etc.
must never be serialized into model input (currently they aren't, per its
own reading of the prompt construction).

**Self-verification:** not independently re-run in this pass (would need
to read the actual B6 GWT generator source alongside both output files);
treating as a plausible, appropriately-hedged secondary opinion, not yet
independently confirmed either way.

## Q5 -- cross-cutting ranking

ChatGPT ranks B0/B1 fixed-codebook-order (already REFUTED above, see Q1)
and B4/B5 position-only shortcut as the top 2 shortcut risks BY CATEGORY
(not specific to a confirmed instance), explicitly declines to manufacture
a shortcut-leakage problem out of B2/B3 or B6 ("basically fine as-is with
respect to shortcut leakage"), distinguishing schema-hygiene issues from
actual learnability shortcuts. Consistent, non-alarmist framing across all
5 answers.

## Net result of this review round

- 1 flagged risk independently REFUTED by direct data check (B0/B1
  codebook order -- fine as shipped in `B1_TRAIN_BALANCED_2ORDER`).
- 1 real bug CONFIRMED (B3 `queried_class_` vs `queried_class` field-name
  typo, same source file/schema, 1620 affected rows) -- not fixed in this
  pass, left for follow-up.
- 1 doc/data mismatch CONFIRMED (B2 "half" docstring vs actual 1/6-5/6
  distribution) -- cosmetic/test-coverage issue, not a correctness bug.
- 2 items (B4/B5 tokenization, B6 field-shape) plausible but NOT
  independently re-verified in this pass -- flagged as open, not promoted
  to confirmed.
- 1 real automation bug found and fixed live (multi-line message
  premature-submit via Enter-on-newline in `chatgpt_burst_worker_v2.sh`).
