#!/usr/bin/env python3
import unicodedata, hashlib, json, sys

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def assert_scalar_string(s: str) -> None:
    for ch in s:
        cp = ord(ch)
        if 0xD800 <= cp <= 0xDFFF:
            raise ValueError("lone surrogate / non-scalar Unicode value")

def semantic_hash(kind: str, s: str) -> str:
    assert_scalar_string(s)
    if kind == "ExactText":
        value = s
        policy = "EXACT_SCALAR_SEQUENCE"
    elif kind == "CanonText":
        value = unicodedata.normalize("NFC", s)
        policy = "NFC"
    else:
        raise ValueError(kind)
    preimage = json.dumps(
        {"type": kind, "normalization": policy, "text": value},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha(preimage)

def main():
    canon_pairs = []
    compat_pairs = []
    for cp in range(0x10000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        nfd = unicodedata.normalize("NFD", ch)
        if nfd != ch and unicodedata.normalize("NFC", nfd) == unicodedata.normalize("NFC", ch):
            canon_pairs.append((ch, nfd))
        nfc = unicodedata.normalize("NFC", ch)
        nfkc = unicodedata.normalize("NFKC", ch)
        if nfkc != nfc:
            compat_pairs.append((ch, nfkc))

    canon_tested = 0
    canon_failures = 0
    for a, b in canon_pairs:
        if a == b:
            continue
        canon_tested += 1
        ok = (
            a != b
            and unicodedata.normalize("NFC", a) == unicodedata.normalize("NFC", b)
            and semantic_hash("ExactText", a) != semantic_hash("ExactText", b)
            and semantic_hash("CanonText", a) == semantic_hash("CanonText", b)
        )
        canon_failures += int(not ok)

    compat_tested = 0
    compat_failures = 0
    for a, b in compat_pairs:
        if a == b or unicodedata.normalize("NFC", a) == unicodedata.normalize("NFC", b):
            continue
        compat_tested += 1
        ok = (
            unicodedata.normalize("NFKC", a) == unicodedata.normalize("NFKC", b)
            and semantic_hash("ExactText", a) != semantic_hash("ExactText", b)
            and semantic_hash("CanonText", a) != semantic_hash("CanonText", b)
        )
        compat_failures += int(not ok)

    length_counterexample = {
        "a": "é",
        "b": "e\u0301",
        "raw_codepoint_lengths": [len("é"), len("e\u0301")],
        "nfc_equal": unicodedata.normalize("NFC", "é") == unicodedata.normalize("NFC", "e\u0301"),
    }

    concat_inputs = [
        ("a", "\u0302"),
        ("A", "\u030A"),
        ("e", "\u0301"),
        ("\u1100", "\u1161"),
    ]
    concat_counterexamples = []
    for x, y in concat_inputs:
        joined = x + y
        concat_counterexamples.append({
            "left_is_nfc": unicodedata.is_normalized("NFC", x),
            "right_is_nfc": unicodedata.is_normalized("NFC", y),
            "joined_is_nfc": unicodedata.is_normalized("NFC", joined),
            "joined_changed_by_nfc": joined != unicodedata.normalize("NFC", joined),
            "joined_codepoints": [f"U+{ord(c):04X}" for c in joined],
            "normalized_codepoints": [f"U+{ord(c):04X}" for c in unicodedata.normalize("NFC", joined)],
        })

    sample_strings = ["", "ascii", "é", "e\u0301", "ﬃ", "①", "가", "\u1100\u1161"]
    cross_kind_collisions = sum(
        semantic_hash("ExactText", s) == semantic_hash("CanonText", s)
        for s in sample_strings
    )

    surrogate_rejections = 0
    for cp in [0xD800, 0xDBFF, 0xDC00, 0xDFFF]:
        try:
            semantic_hash("ExactText", chr(cp))
        except ValueError:
            surrogate_rejections += 1

    result = {
        "schema_version": "1.0",
        "experiment": "ClayCode Unicode canonical boundary proxy",
        "python": sys.version.split()[0],
        "unicode_database_version": unicodedata.unidata_version,
        "hash": "sha256",
        "policy_candidate": {
            "generic_string": "EXACT_SCALAR_SEQUENCE",
            "explicit_normalized_text": "NFC",
            "compatibility_normalization": "NO_IMPLICIT_NFKC",
            "semantic_preimage_domain_separated_by_type": True,
            "normalization_at_final_typed_value_boundary": True,
        },
        "results": {
            "canonical_equivalence_pairs_tested": canon_tested,
            "canonical_equivalence_failures": canon_failures,
            "compatibility_only_pairs_tested": compat_tested,
            "compatibility_only_failures": compat_failures,
            "cross_kind_hash_collisions": cross_kind_collisions,
            "invalid_surrogate_cases_tested": 4,
            "invalid_surrogate_cases_rejected": surrogate_rejections,
            "concat_counterexamples": concat_counterexamples,
            "global_nfc_length_counterexample": length_counterexample,
        },
        "verdict": "PASS_TYPED_POLICY_PROXY" if (
            canon_failures == 0
            and compat_failures == 0
            and cross_kind_collisions == 0
            and surrogate_rejections == 4
            and all(
                c["left_is_nfc"] and c["right_is_nfc"]
                and not c["joined_is_nfc"]
                and c["joined_changed_by_nfc"]
                for c in concat_counterexamples
            )
        ) else "FAIL",
        "scope": "HOSTED_PYTHON_PROXY_NOT_NORMATIVE_CLAYCODE_OR_UBUNTU_TARGET_EVIDENCE",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
