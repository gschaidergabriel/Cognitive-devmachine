# MCA-001 late-arrival re-entry — atomic prompt admission

Post-PR-open canonical change observed: `efa878cbbb8cf12d3417baf263c8a947d6e23af7` makes `UserPromptSubmit` admission atomic through construction/acceptance of the exact bounded hook context. A rejected context now rolls back the user turn, memory extraction, workspace episode and active-turn record together instead of leaving a prompt that Claude never received.

## Adjudication

This closes an important **begin-admission race** and is compatible with MCA-001. It does not establish that a long-running turn's later nonmonotone durable decision remains valid after concurrent same-generation knowledge changes.

MCA-001 remains scoped strictly to the latter question:

- current atomic prompt admission defines a clean initial observation boundary;
- current global entity generation defines a clean boot/recovery lifetime boundary;
- current global EntityOS lease defines a clean external-effect serialization boundary;
- MCA asks whether ordinary same-generation durable knowledge transitions can be split into provably monotone appends versus operations that require a narrower exact context/lease aperture at commit.

If current/future product code adds exact same-generation context dependency validation for all such durable state transitions, MCA must be re-compared and may collapse to `NO_GAIN`.

No product code is changed by this ATOMIC branch.
