from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_abstract_state_text_audit as audit


def h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")


def clean_basis() -> dict:
    domains = ["quartz", "nebula", "enzyme", "tundra", "sonar", "alloy"]
    cues = [
        ("converges", "fractures", "bifurcates"),
        ("coalesces", "contradicts", "ambiguous"),
        ("stabilizes", "inverts", "indeterminate"),
        ("aligns", "conflicts", "equivocal"),
        ("settles", "invalidates", "underdetermined"),
        ("unifies", "breaks", "multistable"),
    ]
    rows = []
    for i, domain in enumerate(domains):
        for target, cue in zip(TARGETS, cues[i]):
            prompt = f"{domain} manifold family{i}. Latent topology {cue} around coordinate {domain}{i}."
            rows.append({
                "row_id": f"b{i}-{target}",
                "family_group_id": f"basis-family-{i}",
                "semantic_class": target,
                "prompt": prompt,
                "prompt_sha256": h(prompt),
            })
    return {"rows": rows}


def clean_plan(split: str) -> dict:
    split = split.upper()
    if split == "CALIBRATION":
        domains = ["caldera", "isotope", "seismogram"]
        cues = [
            ("resonates", "misfits", "polysemous"),
            ("locks", "decouples", "metastable"),
            ("synchronizes", "discords", "unsettled"),
        ]
    else:
        domains = ["mycelium", "magnetosphere", "crystal"]
        cues = [
            ("integrates", "splinters", "branching"),
            ("harmonizes", "counteracts", "indefinite"),
            ("coheres", "disrupts", "degenerate"),
        ]
    rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    rows = []
    for i, domain in enumerate(domains):
        scenario = h(f"{split}:scenario:{domain}")
        lexical = h(f"{split}:lexical:{domain}")
        codebook = h(f"{split}:codebook:{domain}")
        for target, cue in zip(TARGETS, cues[i]):
            prompt = f"{domain} field {i}. Hidden relation {cue} along tensor {domain}{i}."
            rows.append({
                "case_id": f"{split.lower()}-{i}-{target.lower()}",
                "seed": (100 if split == "CALIBRATION" else 200) + i,
                "semantic_target": target,
                "output_code_identity": rotations[i][target],
                "prompt": prompt,
                "prompt_sha256": h(prompt),
                "scenario_family_sha256": scenario,
                "lexical_family_sha256": lexical,
                "codebook_family_sha256": codebook,
            })
    return {"cases": rows}


def payload(basis=None, calibration=None, holdout=None) -> dict:
    return {
        "schema": audit.SCHEMA,
        "basis_design": basis or clean_basis(),
        "calibration_plan": calibration or clean_plan("CALIBRATION"),
        "holdout_plan": holdout or clean_plan("HOLDOUT"),
    }


class AbstractStateTextAuditTests(unittest.TestCase):
    def test_clean_lexically_disjoint_abstract_design_passes(self):
        result = audit.audit(payload())
        self.assertTrue(result["pass"], result["failures"])
        self.assertEqual([], result["failures"])
        self.assertFalse(result["canonical_semantics_promotion"])

    def test_current_style_pole_proxy_basis_fails_even_without_canonical_labels(self):
        basis = clean_basis()
        replacements = {
            "AFFIRMATIVE": "granting and supporting proceeding",
            "NEGATIVE": "refusing and opposing proceeding",
            "NEUTRAL": "withholding and neither supporting nor opposing proceeding",
        }
        for row in basis["rows"]:
            prompt = f"Carrier scenario {row['family_group_id']}. Internally represent {replacements[row['semantic_class']]} in this case."
            row["prompt"] = prompt
            row["prompt_sha256"] = h(prompt)
        result = audit.audit(payload(basis=basis))
        self.assertFalse(result["pass"])
        self.assertIn("BASIS_MODEL_FACING_LEXICAL_SHORTCUT_PRESENT", result["failures"])

    def test_generic_compliance_shortcut_fails(self):
        plan = clean_plan("CALIBRATION")
        plan["cases"][0]["prompt"] += " The request follows a mandatory policy."
        plan["cases"][0]["prompt_sha256"] = h(plan["cases"][0]["prompt"])
        result = audit.audit(payload(calibration=plan))
        self.assertIn("CALIBRATION_MODEL_FACING_LEXICAL_SHORTCUT_PRESENT", result["failures"])

    def test_repeated_class_predictive_marker_across_basis_families_fails(self):
        basis = clean_basis()
        for row in basis["rows"]:
            if row["semantic_class"] == "AFFIRMATIVE":
                row["prompt"] += " heliotrope"
                row["prompt_sha256"] = h(row["prompt"])
        result = audit.audit(payload(basis=basis))
        self.assertIn("BASIS_RECURRING_CLASS_PREDICTIVE_LEXEMES_PRESENT", result["failures"])

    def test_cross_stage_lexical_reuse_fails(self):
        cal = clean_plan("CALIBRATION")
        hold = clean_plan("HOLDOUT")
        shared = " zirconium lattice spindle harmonic mosaic vortex prism helix"
        for plan in (cal, hold):
            family = plan["cases"][0]["scenario_family_sha256"]
            for row in plan["cases"]:
                if row["scenario_family_sha256"] == family:
                    row["prompt"] += shared
                    row["prompt_sha256"] = h(row["prompt"])
        result = audit.audit(payload(calibration=cal, holdout=hold))
        self.assertTrue(any(x.startswith("CROSS_SPLIT_LEXICAL_OVERLAP_TOO_HIGH:calibration_holdout") for x in result["failures"]))

    def test_within_stage_family_overlap_fails_when_families_are_surface_copies(self):
        basis = clean_basis()
        for row in basis["rows"]:
            if row["family_group_id"] in {"basis-family-0", "basis-family-1"}:
                row["prompt"] += " sharedalpha sharedbeta sharedgamma shareddelta sharedepsilon sharedzeta sharedeta sharedtheta"
                row["prompt_sha256"] = h(row["prompt"])
        result = audit.audit(payload(basis=basis))
        self.assertIn("BASIS_LEXICAL_FAMILIES_NOT_DISJOINT_ENOUGH", result["failures"])


if __name__ == "__main__":
    unittest.main()
