# CC10 Source Ledger

Run: `claycode-20260808T1922p0700-chatgpt-secondary`

## Canonical/internal
- RAE-8.8 r2 canonical state `04234efdb86c...`.
- FRANK C6 CNUCS final report, machine-readable architecture and ClayCode mapping.
- Clay G10 COVE.
- ClayGraph C4/G1d final report + schema + self-use benchmark + DB inventory + migration plan + FRANK feedback.
- GWT R4 CSOC.
- Hyperposition H4 HYP-RC4.
- Emergenz E1 E-CERT2.
- ClayCode CC9 CBCC + CC-RC1.4 executable reference.
- Fusion3 CLAY-L4 + `KMP-FUS3-CLAYCODE-L0-L1`.

These internal sources have substantial shared ancestry and are not counted as independent replication.

## Independent external research used materially
- Armesto & Kolb, 2026, *Toward a Science of Intent: Closure Gaps and Delegation Envelopes for Open-World AI Agents*, arXiv:2604.25000 — independent explicit intent-compilation/closure-gap framing.
- Zhang et al., 2026, *FAVA: Formal Authorization for Verified Agents with Evidence-Backed Permission Graphs*, arXiv:2607.27267 — Permission IR -> deterministic lowering -> SMT authorization -> runtime gateway; reported 90.5% aggregate DCR in its evaluation.
- Tan et al., 2026, *ETAS: An Effect-Typed Language for Agent Systems*, arXiv:2607.17780 — typed effects/action traces, residual dynamic obligations and separate requested/handled/denied/committed events.
- Wang et al., 2026, *COVENANT: Natural-Language Workflow Compilation for Aligned Agent Execution*, arXiv:2607.25400 — NL workflow -> WAST/WCFG and runtime checking; reports 50.00% -> 83.33% success and reduced workflow misalignment on its evaluated cases.
- Dantanarayana et al., 2026, *SIGIL: Compiling Agent Skills into Typed Harnesses*, arXiv:2607.27309 — prose skill -> typed AG-IR/harness; reports higher mandated-step execution and lower token use in its evaluation.
- Wang & Sun, 2026, *KBSpec*, arXiv:2606.21339 — formal spec generation with verifier feedback; reports verification-pass gains over compared approaches.
- Li et al., 2026, *XGrammar-2*, arXiv:2601.04426 — dynamic structured generation; supports efficient grammar enforcement, not semantic truth.
- Current intent-formalization research emphasizes the specification-oracle/intent-gap problem: a formal spec can be checkable and still formalize the wrong user meaning.
- LACUNA / Proof-Carrying Agent Actions / related formal-skill work used as architecture-class support for deterministic permission/effect boundaries.

## Provider records
- OpenAlex: `research_entity/runtime/tool_results/cc10-1922-openalex-intent-contract.json` — success, low precision.
- arXiv: `.../cc10-1922-arxiv-intent-contract.json` — success.
- Semantic Scholar: `.../cc10-1922-semscholar-intent-contract.json` — HTTP 429, fallbacks used.
- Tavily: `.../cc10-1922-tavily-intent-contract.json` — success.
- Exa: `.../cc10-1922-exa-intent-contract.json` — success; strongest new discovery surface.
- Judge0: `.../cc10-1922-judge0-intent-contract.json` — independent runtime replication.
- Groq 8B proxy: raw, verbose-typed and compact intent arms — proxy only, never target Qwen evidence.

## Evidence boundary
No external source proves CC-RC1.5 or FRANK transfer. The independent literature supports mechanism classes; the new candidate remains OPEN pending live/twin and target-Qwen tests.