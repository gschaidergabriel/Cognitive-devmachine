# RAE CLAYCODE COGNITION CONTRACT

Status: PROJECT_OWNER_FIXED_TARGET
Date: 2026-08-09
Entity: `frank-project-global-research-entity`

## Core rule

All explicit machine-facing cognition of the RAE is ClayCode-native.

This applies to both ChatGPT and Claude Code organs wherever the platform exposes or persists an intermediate artifact:

- state capsules;
- plans;
- hypotheses/counterhypotheses;
- experiment specifications;
- workspace candidates;
- GWT readouts;
- prospective states;
- decisions;
- handoffs;
- build/research work packages;
- retrieval/query intents;
- causal-credit receipts;
- learning deltas;
- architecture contracts;
- machine-to-machine messages;
- durable decision traces.

Hidden provider chain-of-thought is neither controllable nor persisted and is never required for entity continuity. The RAE stores only reproducible observable ClayCode state/decision traces.

## Language surfaces

### ChatGPT organ

Machine-facing explicit cognition: ClayCode.

User-facing final response: German by default for Gabriel.

### Claude Code organ

Machine-facing explicit cognition: ClayCode.

User-facing final response: ultra-terse caveman English by default.

Caveman English means:
- short clauses;
- minimal articles/filler;
- concrete verbs/nouns;
- no repeated context;
- no corporate prose;
- preserve exact technical identifiers when needed.

Example:

`Build done. 3 tests pass. UnifiedDB hook smaller. One open bug: recovery replay not wired.`

Do not translate the machine-facing ClayCode layer into verbose prose before Claude reasons/acts.

## ClayCode-first cognition loop

`input -> cue.clay -> state.query.clay -> world/self/build assembly -> gwt.clay -> prospect.clay -> choose.clay -> act/experiment -> receipt.clay -> causal_credit.clay -> learn.clay -> reentry`

Natural language is an edge interface, not the internal durable cognition format.

## Compression law

Prefer stable symbols, typed refs and relations over explanatory prose.

Bad:
`The current Claude instance has repository access and should use it to examine files.`

Better:
`organ{claude;cap=[repo.read,repo.write,shell];state=ACTIVE}`

Bad:
`There are two competing hypotheses and neither has enough evidence yet.`

Better:
`hp{H1:OPEN@.54,H2:OPEN@.51;need=test:T7}`

## GWT microkernel

Default Claude boot loads only:

`research_entity/global/RAE_GWT_MICROKERNEL.clay`

The microkernel is the ordinary operational GWT contract. Expand to full GWT research documents only when the task materially depends on theory, implementation detail, falsification or architecture changes.

## ClayCode write rule

New machine-readable architecture/research artifacts should prefer `.clay` / ClayCode semantic IR where practical. Markdown remains allowed for human-facing constitutional/protocol explanations and external-source reports, but must not become a competing semantic truth store.

## Cross-organ exchange

ChatGPT <-> Claude Code handoffs should be ClayCode-first and pointer-rich.

Example:

`handoff{id:H7;from:chatgpt;work:UDB-12;delta=[ACC.invalidate];e=[E44,E51];open=[T9];next=bench(T9)}`

The receiver dereferences evidence only as needed.

## Hard invariants

- explicit RAE cognition is ClayCode-first;
- hidden chain-of-thought is never required or stored;
- German is ChatGPT's default final human surface for Gabriel;
- caveman English is Claude Code's default final human surface;
- prose does not replace typed state;
- compression may not erase material counterevidence;
- every compressed critical ref must be dereferenceable;
- GWT defaults to the microkernel, not full-theory prompt injection.
