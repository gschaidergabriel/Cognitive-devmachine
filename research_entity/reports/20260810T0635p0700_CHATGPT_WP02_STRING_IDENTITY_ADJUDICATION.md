# WP02 JSON string identity — primary-source adjudication

Created: 2026-08-10 06:35 +07
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Role: temporary Clay Research Entity worker; NOT Frank
Trigger context: exact `go`
Canonical parent: RAE-8.8 / revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Current implementation observed: commit `72fb8d3b2dff2c85a982035211b01d54bbe88c6e`

## Decision

Primary-source review SUPPORTS the direction of `72fb8d3...` for the project-local WP02 semantic identity contract:

1. JSON escape spelling is representation, not a distinct decoded string value. RFC 8259 permits a character to be represented directly or by an escape and states that interoperable parsers agree on the contents of Unicode strings regardless of escaping.
2. Therefore a semantic canonical surface that is intended to agree with the production frontend should compare/canonicalize the decoded string value rather than retain the raw JSON STRING token spelling as semantic identity.
3. Do NOT apply Unicode normalization such as NFC/NFD as part of this fix. RFC 8785/JCS explicitly preserves parsed Unicode string data as-is and does not perform Unicode normalization. Thus `é` (U+00E9) and `e` + U+0301 remain different scalar sequences unless ClayCode separately changes its semantic contract.
4. Reject lone/unpaired UTF-16 surrogate values. RFC 8259 marks such values non-interoperable/unpredictable; RFC 8785 requires canonicalization to terminate on invalid Unicode such as lone surrogates.

The current implementation exactly follows that separation: `json.loads(raw)` decodes escape spelling, `_validate_scalar_string()` rejects surrogate code points, escape-equivalent pairs are required equal, and composed-vs-decomposed scalar sequences are required distinct.

## Evidence

Internal falsifier:
- `research_entity/trigger_runs/go/go-20260810T0632p0700-wp02-cross-canonical-string/OOB_RESULT.json`
- 4/5 bounded comparisons refuted cross-surface partition agreement under the pre-fix canonicalizer.

Internal fix:
- `tools/claycode_base_canonicalizer.py` at commit `72fb8d3b2dff2c85a982035211b01d54bbe88c6e`

External primary sources retrieved live:
- RFC 8259, Sections 7, 8.2, 8.3: https://www.rfc-editor.org/rfc/rfc8259.html
- RFC 8785, Sections 3.1, 3.2.2.2: https://www.rfc-editor.org/rfc/rfc8785.html

## Strongest counterhypothesis

Counterhypothesis: raw escape spelling is intentionally semantic source identity in the strict canonicalizer and must therefore remain distinct.

Disposition: REFUTED for the currently declared WP02 semantic-identity role because:
- production BASE frontend already decodes STRING escapes;
- current canonicalizer's own admitted regression requires literal/escaped spellings of the same scalar sequence to share identity;
- preserving raw escape form would make two canonical surfaces disagree on semantic equivalence.

This does NOT prohibit a separate lexical/source-provenance hash if future debugging requires exact spelling preservation. Such a lexical identity must be explicitly separate from semantic identity rather than overloaded into the WP02 semantic hash.

## Test obligations

Before any WP02 promotion:
- literal `é` == `\u00e9` semantic identity;
- literal ASCII == corresponding `\uXXXX` semantic identity;
- `/` == `\/` semantic identity where grammar admits it;
- literal supplementary character == valid surrogate-pair escape semantic identity;
- U+00E9 != `e` + U+0301 unless a separate ClayCode normalization contract is explicitly adopted;
- lone surrogates rejected;
- V17 strict construction/full current G9+dialect/canonical mutation/trivia tests remain green;
- exact-SHA Hostinger Ubuntu receipt still required.

## Architecture consequence

`NO_CORE_LANGUAGE_CHANGE`.

This is a canonicalizer semantic-value repair and regression obligation, not evidence for a new ClayCode primitive, new GWT mechanism, Needle authority change, or Frank Harness mutation.

## Promotion boundary

The primary-source adjudication supports the fix direction but is NOT executable acceptance. `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` was still absent during this go cycle. WP02 remains fail-closed until exact target-class receipts exist.
