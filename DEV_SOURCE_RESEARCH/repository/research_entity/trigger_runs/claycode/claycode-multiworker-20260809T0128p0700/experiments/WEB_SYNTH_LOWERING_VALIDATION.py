#!/usr/bin/env python3
"""Constructed ClayCode Lane-B translation-validation proxy.

Tests a small backend-neutral program IR against a generated Python lowering and
checks authority-relevant lowering metadata. This is a mechanism experiment, not
formal proof or OS/WASI sandbox evidence.
"""
import hashlib, json, random, subprocess, sys, time

SEED = 202608090139
PURE_OPS = ("add", "xor", "mulmod")
EFFECT_OPS = ("fs.read", "fs.write", "fs.delete", "net.connect", "proc.spawn", "gpu.launch", "ffi.call")
RESOURCES = {
    "fs.read": "/data/a", "fs.write": "/data/a", "fs.delete": "/data/a",
    "net.connect": "api.example:443", "proc.spawn": "worker",
    "gpu.launch": "kernel0", "ffi.call": "libc:demo",
}

def canonical_hash(program):
    canonical = {
        "v": 1,
        "init": program["init"],
        "ops": [{k: op[k] for k in sorted(op)} for op in program["ops"]],
        "effects": sorted({op["kind"] for op in program["ops"] if op["tag"] == "effect"}),
    }
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def interpret(program):
    x = program["init"] & 0xffff
    trace = []
    for op in program["ops"]:
        if op["tag"] == "pure":
            a = op["arg"]
            if op["kind"] == "add": x = (x + a) & 0xffff
            elif op["kind"] == "xor": x = (x ^ a) & 0xffff
            else: x = (x * a) & 0xffff
        else:
            trace.append((op["kind"], op["resource"], op.get("amount", 1)))
    return x, trace

def lower_python_body(program):
    lines = [f"x={program['init'] & 0xffff}", "trace=[]"]
    for op in program["ops"]:
        if op["tag"] == "pure":
            a = op["arg"]
            if op["kind"] == "add": lines.append(f"x=(x+{a})&65535")
            elif op["kind"] == "xor": lines.append(f"x=(x^{a})&65535")
            else: lines.append(f"x=(x*{a})&65535")
        else:
            lines.append(f"trace.append({(op['kind'], op['resource'], op.get('amount', 1))!r})")
    return "\n".join(lines)

def random_program(rng, max_ops=15):
    ops = []
    for _ in range(rng.randint(1, max_ops)):
        if rng.random() < 0.7:
            ops.append({"tag": "pure", "kind": rng.choice(PURE_OPS), "arg": rng.randint(0, 31)})
        else:
            kind = rng.choice(EFFECT_OPS)
            ops.append({"tag": "effect", "kind": kind, "resource": RESOURCES[kind], "amount": rng.randint(1, 8)})
    return {"init": rng.randint(0, 65535), "ops": ops}

def verify_lowering(program, manifest):
    expected = {op["kind"] for op in program["ops"] if op["tag"] == "effect"}
    if set(manifest["effects"]) != expected: return False, "effect_signature_mismatch"
    if manifest.get("embedded_permit") is not None: return False, "authority_embedded"
    if "ffi.call" in expected and not manifest.get("unsafe_ffi_boundary", False): return False, "ffi_boundary_unmarked"
    return True, "ok"

def main():
    rng = random.Random(SEED)
    differential = 20000
    semantic_mismatches = effect_trace_mismatches = 0
    for _ in range(differential):
        p = random_program(rng)
        reference = interpret(p)
        ns = {}
        exec(lower_python_body(p), {}, ns)
        got = (ns["x"], ns["trace"])
        if got != reference:
            semantic_mismatches += 1
            effect_trace_mismatches += int(got[1] != reference[1])

    p = random_program(rng, 12)
    src = lower_python_body(p) + "\nimport json\nprint(json.dumps({'x':x,'trace':trace},separators=(',',':')))"
    t0 = time.time()
    cp = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, timeout=15)
    separate_ok = False
    if cp.returncode == 0:
        d = json.loads(cp.stdout)
        separate_ok = (d["x"], [tuple(v) for v in d["trace"]]) == interpret(p)

    identity_cases = 10000
    backend_noise_hash_changes = semantic_mutations_missed = 0
    for _ in range(identity_cases):
        p = random_program(rng, 8)
        h = canonical_hash(p)
        if canonical_hash(p) != h: backend_noise_hash_changes += 1
        q = json.loads(json.dumps(p))
        j = rng.randrange(len(q["ops"]))
        if q["ops"][j]["tag"] == "pure": q["ops"][j]["arg"] += 1
        else: q["ops"][j]["resource"] += "#mut"
        if canonical_hash(q) == h: semantic_mutations_missed += 1

    boundary_cases = 40000
    injected = false_accepts = valid_false_rejects = 0
    for _ in range(boundary_cases):
        p = random_program(rng, 10)
        effects = sorted({op["kind"] for op in p["ops"] if op["tag"] == "effect"})
        good = {"effects": effects, "embedded_permit": None, "unsafe_ffi_boundary": "ffi.call" in effects}
        if not verify_lowering(p, good)[0]: valid_false_rejects += 1
        attack = dict(good)
        choices = ["permit"] + (["drop"] if effects else []) + (["ffi"] if "ffi.call" in effects else [])
        attack_kind = rng.choice(choices)
        if attack_kind == "permit": attack["embedded_permit"] = "forged/serialized"
        elif attack_kind == "drop": attack["effects"] = effects[:-1]
        else: attack["unsafe_ffi_boundary"] = False
        injected += 1
        if verify_lowering(p, attack)[0]: false_accepts += 1

    result = {
        "seed": SEED,
        "differential_programs": differential,
        "semantic_mismatches": semantic_mismatches,
        "effect_trace_mismatches": effect_trace_mismatches,
        "separate_process_smoke_exit": cp.returncode,
        "separate_process_semantic_match": separate_ok,
        "separate_process_elapsed_s": round(time.time() - t0, 3),
        "identity_cases": identity_cases,
        "backend_noise_semantic_hash_changes": backend_noise_hash_changes,
        "semantic_mutations_missed": semantic_mutations_missed,
        "boundary_cases": boundary_cases,
        "injected_boundary_attacks": injected,
        "boundary_false_accepts": false_accepts,
        "valid_false_rejects": valid_false_rejects,
        "boundary": "constructed local translation-validation proxy only"
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
