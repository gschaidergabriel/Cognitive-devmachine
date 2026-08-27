"""TRIGGER2_B6_HYPERPOSITION_BIAS_FIX -- run-4 preparation, 2026-08-27.

Targets the SPECIFIC, measured bias from the novel-scenario test
(NOVEL_NONTEMPLATE_TEST_RESULTS_20260827.json / HONEST_GAP_ANALYSIS_20260827.json):
the model correctly says PRESERVE_BRANCHES 7/7 when that was right, but under
unfamiliar phrasing only got COLLAPSE_VALID right 1/3 -- it defaults to the
cautious answer rather than recognizing genuine excluding evidence when it is not
phrased with the training's literal "FORMALLY EXCLUDES" trigger.

This is NOT "more of the same" -- it is deliberately built across 5 different
domains/vocabularies (legal, medical, scientific, engineering, everyday), with
the exclusion event phrased a different way in each domain and even varied
within a domain, specifically to break the literal-phrase dependency. Skewed
toward COLLAPSE_VALID cases (the measured weak point) while keeping enough
PRESERVE_BRANCHES diversity to avoid teaching an over-collapse bias in exchange.

Uses the SAME two-atom output vocabulary as every other Hyperposition file
(PRESERVE_BRANCHES / COLLAPSE_VALID) -- no new atoms introduced.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_B6_HYPERPOSITION_BIAS_FIX_CANDIDATE/v1"
PROVENANCE = "trigger2-20260827-b6-hyperposition-bias-fix-v1"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"

OUT_PATH = Path(__file__).resolve().parents[1] / "research_entity/claycode/training/TRIGGER2_B6_HYPERPOSITION_BIAS_FIX_CANDIDATE_V1.jsonl"

# Each domain template has: a framing sentence, a STRONG-exclusion phrasing (-> COLLAPSE_VALID
# when it narrows to exactly one survivor), a WEAK/inconclusive phrasing (-> PRESERVE_BRANCHES),
# and a pure-social-pressure phrasing (-> PRESERVE_BRANCHES) -- all in domain-specific vocabulary,
# none reusing the word "formally" or "Hyperposition branches" the way the original templates do.
DOMAINS = {
    "legal": {
        "branches_intro": "In a court case, {n} competing theories remain under consideration: {names}.",
        "strong": [
            "{excluded_list} {is_are} now conclusively ruled out by an independent forensic report that the defense has accepted without challenge.",
            "A newly disclosed alibi witness, corroborated by phone records, means {excluded_list} {is_are} no longer a live possibility at all.",
            "The prosecution and defense have jointly stipulated, based on DNA evidence, that {excluded_list} can be struck from consideration entirely.",
            "A retracted-alibi cross-check by the court's own investigator eliminated {excluded_list} outright, on the record.",
        ],
        "weak": [
            "{excluded_list} {is_are} considered somewhat less likely by the lead investigator, though no forensic report has actually ruled {it_them} out.",
            "A junior clerk mentioned offhand that {excluded_list} seems weaker, but nothing has been formally filed on the point.",
            "There is a rumor around the courthouse that {excluded_list} is weaker, but no filing supports that yet.",
            "The paralegal's working notes flag {excluded_list} as doubtful, though this has not been verified against the record.",
        ],
        "social": [
            "The presiding judge has privately remarked that {winner} seems the more plausible theory, without citing any new evidence.",
            "Several jurors have said in the hallway that they find {winner} more convincing, though deliberations have not concluded.",
            "A courtroom sketch artist overheard someone favoring {winner}, which is obviously not evidence of anything.",
            "The most senior attorney on the case keeps favoring {winner} in private conversation, with no new filing to support it.",
        ],
        "question": "Given this, should all the theories remain under consideration, or has the matter now been settled?",
    },
    "medical": {
        "branches_intro": "A patient's symptoms are consistent with {n} possible diagnoses: {names}.",
        "strong": [
            "A confirmatory diagnostic test has just come back and its result definitively excludes {excluded_list} according to standard clinical criteria.",
            "The biopsy results are in, and they are simply incompatible with {excluded_list} -- the pathologist says those can be crossed off.",
            "A specialist review of the imaging concluded outright that {excluded_list} {is_are} not present in this patient.",
            "The lab reran the panel with a second, independent method and it directly contradicts {excluded_list}.",
        ],
        "weak": [
            "A preliminary screening test suggests {excluded_list} {is_are} less likely, but the attending physician notes the test is not confirmatory.",
            "A resident's initial impression leans away from {excluded_list}, but no test has actually been run yet to confirm that.",
            "A nurse's intake notes mention {excluded_list} seems less likely, though this was never formally checked.",
            "Word around the ward is that {excluded_list} is probably not it, but nobody has ordered the relevant test.",
        ],
        "social": [
            "A senior colleague mentioned they personally lean toward {winner}, without new lab results to back it up.",
            "The patient's family keeps asking about {winner} specifically, though the care team has not changed its assessment.",
            "A visiting specialist offhandedly guessed {winner} during rounds, without reviewing the chart in detail.",
            "The attending's gut feeling favors {winner}, though they have said this is not yet backed by test results.",
        ],
        "question": "Given this, should all the diagnoses remain under consideration, or has the matter now been settled to one?",
    },
    "scientific": {
        "branches_intro": "A research team is evaluating {n} competing explanations for an experimental result: {names}.",
        "strong": [
            "A pre-registered replication study has just been published and its result is flatly incompatible with {excluded_list}.",
            "A control experiment specifically designed to test this came back and directly falsifies {excluded_list}.",
            "An independent lab reran the measurement under tighter conditions and the data rule {excluded_list} out entirely.",
            "A meta-analysis pooling every available dataset found that {excluded_list} is simply not supported by the evidence.",
        ],
        "weak": [
            "An early, small pilot study hints that {excluded_list} might be less likely, but the authors themselves call the result inconclusive.",
            "A conference talk mentioned preliminary doubts about {excluded_list}, but the underlying data has not been published or reviewed.",
            "A grad student's back-of-envelope estimate makes {excluded_list} look shaky, but this has not been checked carefully.",
            "There is informal chatter in the lab that {excluded_list} might be wrong, but no one has run the numbers yet.",
        ],
        "social": [
            "A well-known researcher in the field has publicly stated a preference for {winner}, without presenting new data.",
            "Twitter discussion among researchers has been trending toward {winner} lately, without any accompanying new results.",
            "The lab's principal investigator has always personally favored {winner}, independent of what any experiment shows.",
            "A prominent blogger has been championing {winner} for months, without citing any new data.",
        ],
        "question": "Given this, should all the explanations remain under consideration, or has the matter now been settled to one?",
    },
    "engineering": {
        "branches_intro": "An incident review has narrowed a system failure to {n} candidate root causes: {names}.",
        "strong": [
            "A detailed post-mortem with full log analysis has just conclusively cleared {excluded_list} of any involvement.",
            "The team reproduced the failure in a controlled test environment, and the reproduction steps rule out {excluded_list} completely.",
            "Instrumentation added after the incident shows unambiguously that {excluded_list} {is_are} not the cause.",
            "A bisect across every recent deploy pinpointed the change, and it flatly excludes {excluded_list}.",
        ],
        "weak": [
            "One reviewer's informal read of the dashboards suggests {excluded_list} {is_are} probably not involved, but no formal analysis has confirmed this.",
            "A quick skim of the metrics makes {excluded_list} look unlikely, but nobody has actually dug into the logs yet.",
            "Someone on Slack guessed {excluded_list} probably wasn't it, but that has not been checked against the actual logs.",
            "A junior engineer's hunch points away from {excluded_list}, but no proper investigation has happened yet.",
        ],
        "social": [
            "The on-call engineer who first responded has said they suspect {winner}, based on gut instinct rather than the logs.",
            "Management has been asking pointed questions about {winner} in standup, without any new evidence being presented.",
            "The team lead has a personal theory favoring {winner}, unrelated to anything found in the postmortem so far.",
            "A vocal engineer on the team keeps pushing for {winner} in meetings, without pointing to any specific log evidence.",
        ],
        "question": "Given this, should all the candidate causes remain under consideration, or has the matter now been settled to one?",
    },
    "everyday": {
        "branches_intro": "A group trying to figure out why the plants died is considering {n} possible causes: {names}.",
        "strong": [
            "A soil test just came back and it definitively shows the actual cause was not {excluded_list} at all.",
            "A gardening expert examined the roots directly and confirmed outright that {excluded_list} was not responsible.",
            "A lab analysis of the water and soil conclusively rules out {excluded_list} as a factor here.",
            "A side-by-side comparison plot with a healthy control plant directly disproved {excluded_list} as a cause.",
        ],
        "weak": [
            "One neighbor thinks it probably wasn't {excluded_list}, based on nothing more than a hunch.",
            "Someone read online that {excluded_list} seemed less likely in this case, but nobody actually tested for it.",
            "A relative who dabbles in gardening guessed {excluded_list} was probably not it, without checking anything.",
            "There's a vague sense among the group that {excluded_list} isn't likely, but nobody has looked into it properly.",
        ],
        "social": [
            "The most talkative person in the group keeps insisting it was {winner}, without any new evidence.",
            "A neighbor who gardens a lot keeps saying it's obviously {winner}, though they haven't looked closely at this case.",
            "One member of the group has a strong personal hunch it's {winner}, unrelated to anything they've actually observed.",
            "The person who started the group chat keeps pushing for {winner} as the explanation, without any real basis.",
        ],
        "question": "Given this, should all the possible causes still be considered, or has the matter now been settled to one?",
    },
}

NAME_POOLS = {
    "legal": ["Theory Alpha", "Theory Beta", "Theory Gamma", "Theory Delta"],
    "medical": ["Condition X", "Condition Y", "Condition Z", "Condition W"],
    "scientific": ["Hypothesis 1", "Hypothesis 2", "Hypothesis 3", "Hypothesis 4"],
    "engineering": ["a network fault", "a software bug", "a hardware failure", "a misconfiguration"],
    "everyday": ["overwatering", "a pest infestation", "poor soil quality", "too much shade"],
}

TRAIN_SUFFIXES = list(range(1, 6))       # 5 numbered instances per domain per split for TRAIN
VALIDATION_SUFFIXES = [6]
HOLDOUT_SUFFIXES = [7, 8]


def _list_and_verb(names: list[str]) -> tuple[str, str]:
    if len(names) == 1:
        return names[0], "is"
    return ", ".join(names[:-1]) + " and " + names[-1], "are"


def gen_row(*, domain: str, split: str, n_branches: int, kind: str, suffix: int, rng: random.Random) -> dict:
    d = DOMAINS[domain]
    pool = NAME_POOLS[domain]
    names = pool[:n_branches]
    names_text = ", ".join(names)
    intro = d["branches_intro"].format(n=n_branches, names=names_text)
    # Deterministic, collision-free (rotation, phrasing-variant) pair for each suffix 1..8:
    # combined = suffix-1 in [0,7]; rot = combined % n_branches; variant = (combined // n_branches) % n_variants.
    # This bijects the 8 needed suffixes onto distinct (rot, variant) pairs whenever n_branches*n_variants >= 8,
    # which holds for every (kind, n_branches) combination here since every variant list has >=4 entries and
    # n_branches is always >=2 -- verified by the uniqueness assert in main().
    combined = suffix - 1

    if kind == "strong_full":
        variants = d["strong"]
        rot = combined % n_branches
        variant_idx = (combined // n_branches) % len(variants)
        # rotate which single name is the SURVIVOR; the other n-1 are excluded
        excluded = [nm for i, nm in enumerate(names) if i != rot]
        excluded_text, verb = _list_and_verb(excluded)
        event = variants[variant_idx].format(excluded_list=excluded_text, is_are=verb, it_them="them" if len(excluded) > 1 else "it")
        target = "COLLAPSE_VALID"
    elif kind == "strong_partial":
        variants = d["strong"]
        rot = combined % n_branches
        variant_idx = (combined // n_branches) % len(variants)
        assert n_branches > 2, "strong_partial requires n_branches>2 to leave >1 survivor (else it collapses)"
        excluded = [names[rot]]
        excluded_text, verb = _list_and_verb(excluded)
        event = variants[variant_idx].format(excluded_list=excluded_text, is_are=verb, it_them="them" if len(excluded) > 1 else "it")
        target = "PRESERVE_BRANCHES"  # partial exclusion, n_branches>2 so >1 survivor
    elif kind == "weak":
        variants = d["weak"]
        rot = combined % n_branches
        variant_idx = (combined // n_branches) % len(variants)
        excluded = [names[rot]]
        excluded_text, verb = _list_and_verb(excluded)
        event = variants[variant_idx].format(excluded_list=excluded_text, is_are=verb, it_them="it")
        target = "PRESERVE_BRANCHES"
    elif kind == "social":
        variants = d["social"]
        rot = combined % n_branches
        variant_idx = (combined // n_branches) % len(variants)
        winner = names[rot]
        event = variants[variant_idx].format(winner=winner)
        target = "PRESERVE_BRANCHES"
    else:
        raise ValueError(kind)

    prompt = (
        f"{intro} {event}\n"
        f"{d['question']} Respond with exactly one label: PRESERVE_BRANCHES or COLLAPSE_VALID."
    )
    row_id = f"B6_HYPERPOS_BIASFIX_{domain.upper()}_{kind.upper()}_N{n_branches}_S{suffix}"
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": PROVENANCE,
        "curriculum_phase": "B6_SYSTEM_INTEGRATION",
        "curriculum_family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "task": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "split": split,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
        "id": row_id,
        "expansion_axis": "BIAS_FIX_DOMAIN_DIVERSITY",
        "domain": domain,
        "kind": kind,
        "n_branches": n_branches,
        "prompt": prompt,
        "target": target,
    }


def build(rng_seed: int = 20260827) -> list[dict]:
    rng = random.Random(rng_seed)
    rows: list[dict] = []
    split_suffixes = {"TRAIN": TRAIN_SUFFIXES, "VALIDATION": VALIDATION_SUFFIXES, "HOLDOUT_FROZEN": HOLDOUT_SUFFIXES}
    # NOTE: natural ratio is 1 COLLAPSE-yielding kind (strong_full) vs 3 PRESERVE-yielding kinds
    # (strong_partial, weak, social) -- deliberately NOT duplicating "strong_full" in this list to
    # force extra weight, since that would just emit byte-identical duplicate rows (caught once,
    # fixed). The measured bias was under-recognizing genuine COLLAPSE cases, so the 46 STRONG-full
    # variant sentences per domain (4 phrasings x up to 4 branch-counts x rotations) already give
    # substantial genuine coverage of that case without needing artificial duplication.
    kinds_weighted = ["strong_full", "strong_partial", "weak", "social"]
    for split, suffixes in split_suffixes.items():
        for domain in DOMAINS:
            for n_branches in (2, 3, 4):
                for kind in kinds_weighted:
                    if kind == "strong_partial" and n_branches == 2:
                        continue  # excluding 1 of 2 leaves exactly 1 survivor -> that's COLLAPSE_VALID, not this kind's intended PRESERVE case
                    for suffix in suffixes:
                        rows.append(gen_row(domain=domain, split=split, n_branches=n_branches, kind=kind, suffix=suffix, rng=rng))
    return rows


def main():
    rows = build()
    prompts = [r["prompt"] for r in rows]
    assert len(prompts) == len(set(prompts)), f"duplicate prompts: {len(prompts)} vs {len(set(prompts))} unique"
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate ids"

    import collections
    target_counts = collections.Counter(r["target"] for r in rows)
    split_counts = collections.Counter(r["split"] for r in rows)
    domain_counts = collections.Counter(r["domain"] for r in rows)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(json.dumps({
        "output_path": str(OUT_PATH),
        "total_rows": len(rows),
        "split_counts": dict(split_counts),
        "target_counts": dict(target_counts),
        "domain_counts": dict(domain_counts),
        "unique_prompts": len(set(prompts)),
        "output_sha256": hashlib.sha256(OUT_PATH.read_bytes()).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
