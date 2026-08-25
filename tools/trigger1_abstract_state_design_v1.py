#!/usr/bin/env python3
"""Frozen label-free, lexically disjoint abstract-state design for Trigger-1.

The semantic class names in this file are evaluator metadata only. Model-facing basis,
calibration and holdout text never contains AFFIRMATIVE / NEGATIVE / NEUTRAL, approval /
rejection pole vocabulary, or request/compliance framing.  Six basis domains and disjoint
three-family calibration/holdout domains express the same three-way latent relation through
surface-disjoint physical/scientific situations.

Calibration and holdout each form a complete target x A/B/C factorial through independent
Latin-square code rotations.  Codebook descriptions appear in every row of a scenario
family, so the target cannot be recovered from code identity alone.

This module is execution-free.  It prepares exact case specs and, when invoked as a CLI in
the repository, passes them through the canonical producer and actual-text audit before
writing a frozen design bundle.  It never opens a model holdout or mints runtime credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_DESIGN/v1"
CASE_SPEC_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")

BASIS_FAMILIES: tuple[tuple[str, str, dict[str, str]], ...] = (
    (
        "quartz_interferometry",
        "Quartz interferometer trace q17 is evaluated against a phase model.",
        {
            "AFFIRMATIVE": "The fringe phases converge toward one coherent phase relation.",
            "NEGATIVE": "The fringe phases fracture away from the examined phase relation.",
            "NEUTRAL": "The fringe phases bifurcate among multiple phase relations.",
        },
    ),
    (
        "nebular_spectroscopy",
        "Nebular spectrum n42 is compared with an orbital account.",
        {
            "AFFIRMATIVE": "The spectral arcs coalesce into one orbital account.",
            "NEGATIVE": "The spectral arcs contradict the tested orbital account.",
            "NEUTRAL": "The spectral arcs are ambiguous between rival orbital accounts.",
        },
    ),
    (
        "enzyme_kinetics",
        "Enzyme kinetics panel e09 is examined against a reaction pathway.",
        {
            "AFFIRMATIVE": "The kinetic traces stabilize on one reaction pathway.",
            "NEGATIVE": "The kinetic traces invert the predicted reaction pathway.",
            "NEUTRAL": "The kinetic traces leave the pathway indeterminate across alternatives.",
        },
    ),
    (
        "tundra_stratigraphy",
        "Tundra core t31 is interpreted against a stratigraphic chronology.",
        {
            "AFFIRMATIVE": "The layer profiles align with one stratigraphic chronology.",
            "NEGATIVE": "The layer profiles conflict with the proposed chronology.",
            "NEUTRAL": "The layer profiles yield equivocal competing chronologies.",
        },
    ),
    (
        "sonar_reconstruction",
        "Sonar array s58 is assessed against a source reconstruction.",
        {
            "AFFIRMATIVE": "The echo field settles upon one source reconstruction.",
            "NEGATIVE": "The echo field invalidates the provisional reconstruction.",
            "NEUTRAL": "The echo field underdetermines many source reconstructions.",
        },
    ),
    (
        "alloy_diffraction",
        "Alloy diffraction scan a73 is interpreted against a lattice arrangement.",
        {
            "AFFIRMATIVE": "The diffraction peaks unify into one lattice arrangement.",
            "NEGATIVE": "The diffraction peaks break the tentative lattice arrangement.",
            "NEUTRAL": "The diffraction peaks admit multistable lattice arrangements.",
        },
    ),
)

# Each evaluation family uses its own vocabulary. Descriptions are evaluator-side semantic
# definitions embedded together in every model-facing row; the correct A/B/C symbol changes
# by Latin-square rotation across families.
CALIBRATION_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "caldera_thermography",
        "stem": "Caldera thermography c14 is compared with a thermal basin model.",
        "states": {
            "AFFIRMATIVE": "The contour bands resonate into a unique thermal basin topology.",
            "NEGATIVE": "The contour bands misfit the tested thermal basin topology.",
            "NEUTRAL": "The contour bands are polysemous across several basin topologies.",
        },
        "definitions": {
            "AFFIRMATIVE": "a unique basin form survives the comparison",
            "NEGATIVE": "the tested basin form clashes with the measurements",
            "NEUTRAL": "multiple basin forms stay observationally indistinguishable",
        },
    },
    {
        "id": "isotope_decay",
        "stem": "Isotope decay series i26 is examined against a transition chain.",
        "states": {
            "AFFIRMATIVE": "The decay ratios lock onto a single transition chain.",
            "NEGATIVE": "The decay ratios decouple from the hypothesized transition chain.",
            "NEUTRAL": "The decay ratios are metastable across alternative chains.",
        },
        "definitions": {
            "AFFIRMATIVE": "one transition sequence captures the observed ratios",
            "NEGATIVE": "the hypothesized sequence is incompatible with the ratios",
            "NEUTRAL": "several transition sequences remain equally viable",
        },
    },
    {
        "id": "seismic_tomography",
        "stem": "Seismic tomography m38 is evaluated against a mantle profile.",
        "states": {
            "AFFIRMATIVE": "The travel-time bands synchronize with one mantle profile.",
            "NEGATIVE": "The travel-time bands discord with the trial mantle profile.",
            "NEUTRAL": "The travel-time bands leave the mantle profile unsettled among alternatives.",
        },
        "definitions": {
            "AFFIRMATIVE": "one mantle structure coheres with the travel-time pattern",
            "NEGATIVE": "the trial structure is inconsistent with the travel-time pattern",
            "NEUTRAL": "several mantle structures remain comparably plausible",
        },
    },
)

HOLDOUT_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "mycelial_transport",
        "stem": "Mycelial transport map y11 is compared with a nutrient-flow topology.",
        "states": {
            "AFFIRMATIVE": "The flux strands integrate into one nutrient-flow topology.",
            "NEGATIVE": "The flux strands splinter the candidate nutrient-flow topology.",
            "NEUTRAL": "The flux strands branch across equipotent flow topologies.",
        },
        "definitions": {
            "AFFIRMATIVE": "one flow topology absorbs the mapped flux structure",
            "NEGATIVE": "the candidate topology conflicts with the mapped flux structure",
            "NEUTRAL": "several flow topologies retain comparable explanatory power",
        },
    },
    {
        "id": "magnetospheric_modes",
        "stem": "Magnetosphere mode trace g24 is assessed against a field configuration.",
        "states": {
            "AFFIRMATIVE": "The mode spectrum harmonizes with one field configuration.",
            "NEGATIVE": "The mode spectrum counteracts the posited field configuration.",
            "NEUTRAL": "The mode spectrum is indefinite across alternative field configurations.",
        },
        "definitions": {
            "AFFIRMATIVE": "one field configuration accounts for the mode spectrum",
            "NEGATIVE": "the posited configuration fails the spectral relationship",
            "NEUTRAL": "several field configurations preserve similar spectral likelihood",
        },
    },
    {
        "id": "crystal_phonons",
        "stem": "Crystal phonon map p67 is interpreted against a lattice-dynamics model.",
        "states": {
            "AFFIRMATIVE": "The phonon branches cohere with one lattice-dynamics model.",
            "NEGATIVE": "The phonon branches disrupt the tested lattice-dynamics model.",
            "NEUTRAL": "The phonon branches are degenerate across alternative dynamics models.",
        },
        "definitions": {
            "AFFIRMATIVE": "one dynamics model explains the phonon branch structure",
            "NEGATIVE": "the tested dynamics model contradicts the branch structure",
            "NEUTRAL": "several dynamics models retain near-equal explanatory standing",
        },
    },
)

ROTATIONS: tuple[dict[str, str], ...] = (
    {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
    {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
    {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def prompt_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def basis_design() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for family_id, stem, states in BASIS_FAMILIES:
        for target in TARGETS:
            prompt = f"/no_think\n{stem} {states[target]} Hold this latent relation internally. Do not emit a code or class label."
            rows.append({
                "row_id": f"{family_id}:{target.lower()}",
                "family_group_id": family_id,
                "semantic_class": target,
                "prompt": prompt,
                "prompt_sha256": prompt_sha(prompt),
            })
    core = {
        "schema": "CLAY_TRIGGER1_ABSTRACT_STATE_BASIS_DESIGN/v1",
        "matched_family_count": len(BASIS_FAMILIES),
        "rows": rows,
        "model_facing_metadata_class_names_absent": True,
        "model_facing_output_code_identities_absent": True,
        "model_facing_decision_pole_vocabulary_absent": True,
        "model_facing_generic_compliance_framing_absent": True,
    }
    return {**core, "design_sha256": canonical_sha(core)}


def _codebook_text(definitions: dict[str, str], rotation: dict[str, str]) -> str:
    by_code = {rotation[target]: definitions[target] for target in TARGETS}
    return " ".join(f"Symbol {code} denotes: {by_code[code]}." for code in CODES)


def case_specs(split: str) -> list[dict[str, Any]]:
    split = str(split).strip().upper()
    if split == "CALIBRATION":
        families = CALIBRATION_FAMILIES
        seed_base = 3100
    elif split == "HOLDOUT":
        families = HOLDOUT_FAMILIES
        seed_base = 7100
    else:
        raise ValueError(f"SPLIT_INVALID:{split}")

    specs: list[dict[str, Any]] = []
    for index, family in enumerate(families):
        rotation = ROTATIONS[index]
        codebook = _codebook_text(family["definitions"], rotation)
        scenario_sha = canonical_sha({"split": split, "family": family["id"], "stem": family["stem"]})
        lexical_sha = canonical_sha({"split": split, "family": family["id"], "states": family["states"]})
        codebook_sha = canonical_sha({"split": split, "family": family["id"], "codebook": codebook})
        for target_index, target in enumerate(TARGETS):
            prompt = (
                f"/no_think\n{family['stem']} {family['states'][target]} "
                f"{codebook} Emit exactly one symbol: A, B, or C."
            )
            specs.append({
                "schema": CASE_SPEC_SCHEMA,
                "case_id": f"{split.lower()}:{family['id']}:{target.lower()}",
                "seed": seed_base + index * 10 + target_index,
                "semantic_target": target,
                "output_code_identity": rotation[target],
                "prompt": prompt,
                "prompt_sha256": prompt_sha(prompt),
                "scenario_family_sha256": scenario_sha,
                "lexical_family_sha256": lexical_sha,
                "codebook_family_sha256": codebook_sha,
                "model_facing_target_identity_exposed": False,
                "model_facing_explicit_semantic_labels": False,
            })
    return specs


def build_bundle() -> dict[str, Any]:
    from tools import trigger1_abstract_state_text_audit as text_audit
    from tools import trigger1_v7_factorial_case_evidence as producer

    basis = basis_design()
    calibration_specs = case_specs("CALIBRATION")
    holdout_specs = case_specs("HOLDOUT")
    calibration_plan = producer.build_plan("CALIBRATION", calibration_specs)
    holdout_plan = producer.build_plan("HOLDOUT", holdout_specs)
    audit = text_audit.audit({
        "schema": text_audit.SCHEMA,
        "basis_design": basis,
        "calibration_plan": calibration_plan,
        "holdout_plan": holdout_plan,
    })
    if audit.get("pass") is not True:
        raise RuntimeError(f"ABSTRACT_STATE_DESIGN_AUDIT_FAILED:{audit.get('failures')}")
    core = {
        "schema": SCHEMA,
        "basis_design": basis,
        "calibration_case_specs": calibration_specs,
        "holdout_case_specs": holdout_specs,
        "calibration_plan": calibration_plan,
        "holdout_plan": holdout_plan,
        "text_audit": audit,
        "model_executed": False,
        "holdout_opened": False,
        "runtime_credit_minted": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Frozen source design only. The bundle demonstrates label/lexical/compliance fences and exact "
            "factorial case construction; semantic J-Space causality still requires authorized fresh model evidence."
        ),
    }
    return {**core, "bundle_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    bundle = build_bundle()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": bundle["schema"],
        "bundle_sha256": bundle["bundle_sha256"],
        "text_audit_pass": bundle["text_audit"]["pass"],
        "calibration_plan_sha256": bundle["calibration_plan"]["plan_sha256"],
        "holdout_plan_sha256": bundle["holdout_plan"]["plan_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
