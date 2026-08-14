# Original Digital Retina baseline recovery delta

Run: `go-20260811T2029p0700-chatgpt-secondary-q23-temporal-feature-epoch`
Work package: `F-V01-06-DIGITAL-RETINA-MVC`
This is a normal recursive continuation of the same GO macrocycle. It does **not** add a second out-of-box experiment.

## Result

The earlier `BASELINE_PARTIAL_ARCHAEOLOGY` assessment is now materially narrowed. The exact historical source lineage is recoverable; the remaining blocker is primarily the historical model/weight bundle plus re-execution, not source archaeology.

Do **not** promote this to a replacement claim. `NO_ORIGINAL_BASELINE -> NO_REPLACEMENT_CLAIM` still holds until executable baseline measurements exist.

## Recovery evidence

The Google Drive `digital-retina` snapshot contains:

- a repository root with `retina/`, `api/`, `deploy/`, `eval/`, `tests/`, `tools/`, `requirements.txt`, README and `.git`;
- `.git/objects`, `.git/refs`, `.git/index`, `.git/HEAD` and `.git/config`;
- `eval/` subtrees for generic images, photos, art and AI images;
- a separate `digital-retina-e2e` snapshot containing `vlm_coverage_hard.py`, `vlm_coverage_freshset.py`, `tier3_e2e.py`, hard/fresh coverage artifacts and iterative JSON result history.

The recovered `.git/config` identifies the origin as the private repository `gschaidergabriel/digital-retina` with `main` as the tracked branch.

That private GitHub repository is currently reachable by the connected project GitHub identity. Current recovered end-of-lineage source anchor:

`gschaidergabriel/digital-retina@819dcac12253b7de45795239b44482627ade624f` (2026-05-27)

Exact source files recovered at that commit include:

- `retina/core.py` blob `537aa58066ae8184875152c26c887361a58897f4`;
- `retina/vision/frank_eye.py` blob `180a64ed47d0b9ec9f7ce168b11f907b321b5cea`;
- the remaining repository history/commits needed to select earlier comparison points.

`requirements.txt` from the snapshot pins at least the observed ML/vision substrate including torch 2.5.1, torchvision 0.20.1, onnxruntime 1.20.1, open_clip_torch 2.30.0, ultralytics 8.3.50, opencv-python-headless 4.10.0.84, Pillow 11.0.0, pytesseract 0.3.13 and numpy 1.26.4.

## Exact physical weight boundary recovered from source

`frank_eye.py` identifies the historical custom/local model files under `RETINA_VISION_MODELS` / `/var/lib/digital-retina/models/vision`:

- `retina_v8.pt`;
- `library_L3.npz`;
- `dinov2_small_int8.onnx`;
- `dinov2_config.json`.

The same repository `.gitignore` explicitly excludes `models/`, `*.pt`, `*.onnx` and `*.npz`, so absence from Git is expected and must not be interpreted as evidence that they never existed.

Targeted Drive searches in this cycle did not locate the exact three custom/binary filenames `retina_v8.pt`, `library_L3.npz` or `dinov2_small_int8.onnx`. Therefore exact historical execution remains blocked on weight recovery/reconstruction even though exact source and eval logic are now recoverable.

## Recovered benchmark lineage

The private repository history and Drive E2E corpus preserve more measurement structure than the old archaeology receipt captured. Examples:

- Tier-1 commit history records vocab expansion, OCR filtering, DINOv2 re-export and warm/cold behavior;
- CLIP-L/14 was retained disabled after a six-image target probe reported about +5.3 s mean latency over B/32 without measurable top-1 quality improvement;
- the May-27 two-metric remeasurement records a 12-image hard set plus 32-image fresh set and reports 93.1% CLIP-lenient versus 75.1% strict coverage on 44 images / 960 baseline phrases;
- the hard-set driver explicitly distinguishes strict text-visible coverage from CLIP-lenient latent recognition and exercises the live production Retina endpoint;
- the Drive `coverage/` tree retains baseline JSON, iterative coverage passes and final/honest reports rather than only prose summaries.

These are historical measurements and protocols. They are not current accepted-target re-execution receipts.

## Security sanitation finding

The recovered Drive copy of the historical hard-set evaluation driver contains embedded credential fallbacks. No credential values were copied into this receipt, used for testing, or transferred to GitHub/Clay.

Required handling before any reuse:

1. treat those historical credentials as potentially compromised and rotate/revoke them outside this research receipt;
2. create a sanitized benchmark copy that requires credentials from scoped runtime secret injection only;
3. preserve the original file only as restricted historical evidence;
4. exclude credentials from any training corpus, UnifiedDB semantic content, receipts or generated artifacts.

A search of the private `digital-retina` GitHub repository did not find the observed Retina-key prefix or the generic Groq key variable from that Drive-only E2E copy, so this finding is currently bounded to the historical Drive benchmark surface rather than promoted to a repository-wide secret-leak claim.

## Baseline classification after this cycle

Source lineage: **RECOVERED_EXACT**

Evaluation driver/result lineage: **RECOVERED_SUBSTANTIALLY**

Historical dependency manifest: **RECOVERED**

Historical custom/local weights: **NOT YET RECOVERED**

Accepted-target cold/warm re-execution: **NOT RUN**

Matched original-vs-q23/Qwen comparison: **NOT RUN**

Replacement claim allowed: **NO**

## Next smallest falsifiers

1. Search project storage/VPS archives/backups for the exact custom weight filenames and `RETINA_VISION_MODELS` directory lineage.
2. If custom weights remain absent, inspect source/history for deterministic regeneration paths and classify each recovered/rebuilt artifact separately; never silently substitute a different model.
3. Freeze a sanitized compact fixture corpus from the recovered hard/fresh eval assets and preserve exact hashes/ground truth/protocol.
4. Recreate the historical dependency environment in an isolated non-production sandbox and measure import/weight compatibility before any full pipeline run.
5. Only after weights are exact or explicitly reconstructed, execute cold/warm original Retina on the accepted Linux target and capture latency/accuracy/reliability/resource metadata.
6. Compare q23/shared-feature candidates against the exact original baseline on matched fixtures/seeds and preserve negative results.
