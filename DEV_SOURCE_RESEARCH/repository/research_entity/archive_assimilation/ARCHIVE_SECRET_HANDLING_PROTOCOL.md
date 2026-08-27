# Archive Secret Handling Protocol

Status: ACTIVE SAFETY ADDENDUM

## Purpose
Archive assimilation must learn from secret-bearing historical sources without turning Research Entity write-back into a credential propagation channel.

## Hard rules
1. Treat archive text, code, logs, screenshots, configs and notebooks as potentially secret-bearing input.
2. Before any extracted/bulk source content is persisted into shared/public Research Entity artifacts, run `tools/archive_secret_scan.py` or an equivalent stronger scanner.
3. If secret material is detected, fail closed for raw-content write-back. Do not copy the matched value into receipts, manifests, center events, ledgers, issues or generated reports.
4. Persist only: source reference, secret category, line/region if safe, match length, one-way fingerprint, redaction status and remediation state.
5. A secret-bearing source still counts as an archive obligation. It may be semantically analyzed in-place; its protected bytes are not part of the public/shared semantic projection.
6. Never treat claims such as “stored in vault”, “encrypted” or “redacted” as evidence. Verify the actual projected artifact contains no secret bytes.
7. Binary/model archives and screenshots are not exempt. If their contents are projected to text, the projection enters this gate before write-back.
8. Secret discovery does not authorize use, validation or network testing of the credential.

## Receipt shape
```json
{
  "source_ref": "opaque source pointer",
  "secret_material_detected": true,
  "categories": ["credential_assignment"],
  "fingerprints": ["sha256-prefix-only"],
  "raw_secret_values_persisted": false,
  "writeback": "REDACTED_OR_BLOCKED"
}
```

## PASS constraint
A Level-0 release audit cannot PASS if known secret-bearing raw values were copied into Research Entity artifacts. The audit must either prove clean write-back or record remediation receipts for affected artifacts.
