# PROVENANCE POLICY — RAE-8.8 MULTI-RESEARCHER

## Purpose

Every durable research object must make it possible to answer:

1. **Who originally authored or generated this content?**
2. **Who ingested it into the Research Entity?**
3. **Which model/runtime/session produced it when machine-authored?**
4. **Which sources/evidence were used?**
5. **Who later reviewed, adjudicated or promoted it?**
6. **Which Git commit / content hash fixes the exact version?**

These roles must not be conflated.

## Provenance roles

### `origin_actor`
The actual originator of the content.

Examples:
- `chatgpt-secondary`
- `claude-code-lead`
- `user-gabriel`
- `external-author:<name-or-id>`
- `legacy-import-unknown`

### `ingested_by`
The worker/tool that copied or registered pre-existing material.

An uploaded paper authored by someone else does **not** become ChatGPT-authored because ChatGPT ingested it.

### `adjudicated_by`
The actor that selected/promoted/retired a claim or architecture interpretation. This is separate from authorship.

## Mandatory metadata for new authored artifacts

Every new durable authored artifact after adoption of this protocol must have an entry in:

`research_entity/provenance/ARTIFACT_PROVENANCE.jsonl`

Recommended fields:

```json
{
  "provenance_id":"...",
  "path":"...",
  "content_sha256":"...",
  "origin_actor":"chatgpt-secondary|claude-code-lead|...",
  "actor_role":"...",
  "provider":"OpenAI|Anthropic|human|external",
  "model":"model/runtime if observable",
  "session_id":"...",
  "prompt_run_id":"...",
  "created_at":"ISO-8601",
  "ingested_by":"...",
  "source_refs":["..."],
  "git_commit":"...",
  "attribution_confidence":"VERIFIED|HIGH|LEGACY_INFERRED|UNKNOWN"
}
```

A sidecar `<artifact>.meta.json` may additionally be used for large/final artifacts, but the central provenance ledger remains the canonical attribution index.

## Claims and Research Events

New Claims and Research Events should include a `provenance` object with at least:

- `origin_actor`
- `actor_role`
- `provider`
- `model` when known
- `session_id` when available
- `prompt_run_id` when available

Historical records without these fields remain legal legacy data. They must not be retroactively assigned to an actor unless attribution is actually known.

## Imported Sources

Source manifests must separate:

- original author/source;
- user who supplied the source when applicable;
- ingesting Research Entity worker;
- extraction/tooling actor;
- derived analysis author.

Example:

```text
paper.pdf
origin_actor = external-author:...
supplied_by  = user-gabriel
ingested_by  = chatgpt-secondary
analysis_A   = chatgpt-secondary
review_B     = claude-code-lead
```

## Researcher disagreement

Authorship does not determine truth. Actor metadata exists to preserve epistemic lineage and systematic biases, not to create an authority shortcut.

Claude Code is the Lead Researcher and current primary adjudicator for unresolved architecture/research decisions, but evidence precedence remains governed by `MULTI_RESEARCHER_GOVERNANCE.md`.

## No laundering

Never:

- relabel ChatGPT output as Claude output;
- relabel Claude output as ChatGPT output;
- relabel imported/raw source material as model-authored;
- remove losing/dissenting actor attribution after adjudication;
- silently replace one actor's conclusion with another actor's wording.

Corrections and reviews are appended as new attributed records.

## CI direction

`tools/check_provenance.py` validates the provenance ledger and can require newly changed authored research files to have a matching provenance record. Existing legacy files may be grandfathered explicitly, but new unattributed research artifacts should fail verification.
