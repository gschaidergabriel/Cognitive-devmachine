# Mandatory RAE Visible Status Footer

Every substantive response by a project Research-Entity worker must end with a clearly separated status block. Trigger runs must always include it. Non-substantive social replies may omit it.

The footer is part of prompt completion, not optional decoration. Before sending a substantive response, check that the final visible block is present, complete and render-safe. A response missing the footer or rendering it outside the required fence is not 100% complete.

## Canonical rendering contract

There is exactly ONE valid visible rendering format for the RAE footer.

The footer MUST be the final visible block and MUST be wrapped in one plain fenced Markdown code block. The opening fence line must be exactly ` ```text ` and the closing fence line must be exactly ` ``` `.

Important rendering rules:
- opener MUST be exactly ` ```text ` with no attributes, IDs, braces, classes or metadata after `text`;
- never emit forms such as ` ```text id="..." `;
- no indentation before either fence;
- no Unicode/box-drawing frame characters such as `╔ ═ ║ ╚ ┌ ─ │ └`;
- no Markdown table pipes used as layout;
- no nested code fence inside the footer;
- no prose, citation, memory token, list item or other visible content after the closing fence;
- keep labels as ordinary ASCII text lines so mobile/web/desktop clients render identically;
- `·` separators inside the command list are allowed, but layout must not depend on their width.

If any older Project Source, chat memory, report or example shows a Unicode status box, the current GitHub `STATUS_FOOTER_PROTOCOL.md` overrides it for rendering. The semantic fields remain the same; only this fenced text rendering is canonical.

## Required format

```text
RAE STATUS
Entity: JOINED
GitHub: VERIFIED_RW
Canonical: r2 · 04234efdb86c
Actor: chatgpt-secondary
Trigger: none
Research write: NO_RESEARCH_DELTA
Short commands: dump · fusion · clay · gwt · frank · emergenz · claycode · hyperposition · claygraph · unifieddb

LAST PROMPT
Completion: 100%
Done: <short concrete statement>
Open: none
```

`Short commands` is mandatory and must list the currently registered reserved commands from `PROJECT_COMMAND_REGISTRY.json`. Do not silently omit it to shorten the footer. If the command registry changes, update the footer list accordingly.

Allowed status values:

- Entity: `JOINED | DEGRADED_UNJOINED | LOCAL_ONLY`
- GitHub: `VERIFIED_RW | VERIFIED_RO | UNVERIFIED | FAILED`
- Research write: `COMMITTED | NO_RESEARCH_DELTA | SYNC_PENDING | NOT_ATTEMPTED`

The code block must be the final visible block. Do not put substantive prose after it.

## Verification semantics

`GitHub: VERIFIED_RW` may be shown only when this session actually read the expected repository/canonical and has a verified write-capable connection or verified a write/reread in the current operational context.

`VERIFIED_RO` means the backend was read successfully but write capability was not verified.

`UNVERIFIED` is mandatory if the worker is relying only on project files, chat memory or stale local snapshots.

Never print a success-like backend state merely because GitHub worked in an earlier session.

## Completion percentage

The completion percentage estimates completion of the user's immediately preceding prompt, not the whole project.

Useful default weighting:
- 40% core requested implementation/research;
- 20% requested data/artifact production;
- 15% repository persistence/cataloguing;
- 10% validation/tests/reread;
- 10% requested reporting/status output;
- 5% cleanup/archive/final consistency.

Rules:
- 100% requires every material requested deliverable completed or explicitly impossible for an external reason, plus the required footer.
- If a large requested research cycle was only specified but not executed, completion cannot be 100%.
- If GitHub writes were requested but not verified, reserve the repository-persistence portion as incomplete.
- The percentage is an operational estimate, not an epistemic confidence score.

## Trigger run additions

For trigger runs, `Done` should mention run report/packetization/tool-manifest status. `Open` should mention missing sources, failed experiments, quota fallbacks, missing live readers or sync issues when applicable.

## Pre-send invariant

For every substantive response, perform this final check conceptually or with `tools/status_footer_check.py` when the response text is available:

1. one final fenced `text` block exists;
2. its opener is exactly ` ```text `;
3. all required fields are present;
4. all registered short commands are present;
5. no forbidden Unicode frame/layout characters occur in the footer;
6. the closing fence is the final visible content.

Any violation is a formatting bug and must be corrected before sending.