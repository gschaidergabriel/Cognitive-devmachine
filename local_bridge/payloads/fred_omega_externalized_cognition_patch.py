from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one anchor, got {text.count(old)}")
    p.write_text(text.replace(old, new, 1))


replace_once(
    "scripts/omega_world_turn.py",
    "import omega_grf_brain as grf\n",
    "import omega_grf_brain as grf\nimport omega_externalized_cognition as externalized\n",
)

replace_once(
    "scripts/omega_world_turn.py",
    '''    return {
        "schema": SCHEMA,
        "grf_input": fusion["grf_input"],
        "world_state_digest": fusion["world_state_digest"],
        "world_manifold_digest": fusion["world_manifold_digest"],
        "grf_field_digest": fusion["grf_field_digest"],
        "predecessor_capsule_digest": fusion["hybrid_fusion"]["predecessor_capsule_digest"],
        "subject": subject,
        "authority": False,
        "canonical_truth_credit": False,
        "effect_authority": False,
    }
''',
    '''    try:
        predecessor_cognition = externalized.extract_cycle_from_capsule(predecessor)
        cognition = externalized.build_cycle(
            turn_event_id=entry.turn_event_id,
            entity_generation=generation,
            user_text=user_text,
            retrieval_text=retrieval_text,
            world_state=fusion["world_state"],
            world_manifold=fusion["world_manifold"],
            grf_field=fusion["grf_field"],
            predecessor_cycle=predecessor_cognition,
        )
    except externalized.ExternalizedCognitionError as exc:
        raise WorldTurnError(f"externalized cognition rejected: {exc}") from exc

    # This state is persisted inside the already-canonical GRF capsule.
    # GRID10 remains the only persistence/reentry/effect lifecycle owner.
    grf_input = json.loads(wm.canonical_json(fusion["grf_input"]))
    context = grf_input.setdefault("context", {})
    if not isinstance(context, dict):
        raise WorldTurnError("GRF context must be an object")
    if "omega_externalized_cognition" in context:
        raise WorldTurnError("GRF context already contains omega_externalized_cognition")
    context["omega_externalized_cognition"] = cognition

    primitives = grf_input.setdefault("primitives", [])
    if not isinstance(primitives, list):
        raise WorldTurnError("GRF primitives must be a list")
    existing_ids = {str(p.get("id")) for p in primitives if isinstance(p, Mapping)}
    for primitive in externalized.grf_primitives(cognition):
        if str(primitive["id"]) in existing_ids:
            raise WorldTurnError(f"externalized GRF primitive id collision: {primitive['id']}")
        primitives.append(primitive)
        existing_ids.add(str(primitive["id"]))

    return {
        "schema": SCHEMA,
        "grf_input": grf_input,
        "world_state_digest": fusion["world_state_digest"],
        "world_manifold_digest": fusion["world_manifold_digest"],
        "grf_field_digest": fusion["grf_field_digest"],
        "externalized_cycle_digest": cognition["cycle_digest"],
        "externalized_state_hash": cognition["snapshot"]["state_hash"],
        "context_compilation_hash": cognition["context_compilation"]["serialized_context_hash"],
        "predecessor_capsule_digest": fusion["hybrid_fusion"]["predecessor_capsule_digest"],
        "subject": subject,
        "authority": False,
        "canonical_truth_credit": False,
        "effect_authority": False,
    }
''',
)

replace_once(
    "scripts/omega_voice_world_patch.py",
    "import contextlib\nimport os\nfrom typing import Any\n",
    "import contextlib\nimport json\nimport os\nfrom typing import Any, Mapping\n",
)
replace_once(
    "scripts/omega_voice_world_patch.py",
    "import f2wp1207_grid10_turn_loop as turn_loop\nimport omega_world_turn as world_turn\n",
    "import f2wp1207_grid10_turn_loop as turn_loop\nimport omega_externalized_cognition as externalized\nimport omega_world_turn as world_turn\n",
)
replace_once(
    "scripts/omega_voice_world_patch.py",
    '''        return world_turn.run_atomic_canonical_world_turn(
            conn,
            entry,
            user_text=user_text or "",
            retrieval_text=retrieval_text,
            owner=receipt["owner"],
            machine_id=receipt["machine_id"],
            effect_policy=effect_policy,
            include_self_observation=False,
            evidence_path=stern.F2WP1207_TURN_LOOP_EVIDENCE,
            env=os.environ,
            tune=tune_p7 or None,
        )
''',
    '''        result = world_turn.run_atomic_canonical_world_turn(
            conn,
            entry,
            user_text=user_text or "",
            retrieval_text=retrieval_text,
            owner=receipt["owner"],
            machine_id=receipt["machine_id"],
            effect_policy=effect_policy,
            include_self_observation=False,
            evidence_path=stern.F2WP1207_TURN_LOOP_EVIDENCE,
            env=os.environ,
            tune=tune_p7 or None,
        )
        if result is None:
            return None
        row = conn.execute(
            "SELECT capsule_json FROM f2_grid10_grf_projection WHERE frame_id=?",
            (result.frame_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("atomic world turn committed without GRF capsule readback")
        capsule = json.loads(str(row[0]))
        cognition = externalized.extract_cycle_from_capsule(capsule)
        if cognition is None:
            raise RuntimeError("committed GRF capsule lacks externalized cognition")
        return {
            "turn_result": result,
            "compiled_context": externalized.context_text(cognition),
            "cycle_digest": cognition["cycle_digest"],
            "state_hash": cognition["snapshot"]["state_hash"],
        }
''',
)
replace_once(
    "scripts/omega_voice_world_patch.py",
    '''                _run_atomic_voice_world_turn(
                    full,
                    session_id=sid,
                    user_text=text or "",
                    retrieval_text=treffer or None,
                    receipt=receipt,
                )
''',
    '''                world_result = _run_atomic_voice_world_turn(
                    full,
                    session_id=sid,
                    user_text=text or "",
                    retrieval_text=treffer or None,
                    receipt=receipt,
                )
                if isinstance(world_result, Mapping):
                    compiled = str(world_result.get("compiled_context") or "").strip()
                    if compiled:
                        self._voice_emergent_context = compiled[:12000]
                        self._voice_emergent_chars = len(self._voice_emergent_context)
                        self._voice_externalized_state_hash = str(world_result.get("state_hash") or "")
                        self._voice_externalized_cycle_digest = str(world_result.get("cycle_digest") or "")
                        full._emergent_cache_put(sid, text or "", self._voice_emergent_context)
''',
)

replace_once(
    "scripts/install_voice_777_omega.sh",
    "  omega_runtime.py\n",
    "  omega_runtime.py\n  omega_externalized_cognition.py\n",
)

workflow = Path(".github/workflows/omega-native-world-model.yml")
y = workflow.read_text()
y = y.replace(
    "      - 'scripts/omega_runtime.py'\n",
    "      - 'scripts/omega_runtime.py'\n      - 'scripts/omega_externalized_cognition.py'\n",
)
y = y.replace(
    "      - 'tests/test_omega_runtime.py'\n",
    "      - 'tests/test_omega_runtime.py'\n      - 'tests/test_omega_externalized_cognition.py'\n",
)
y = y.replace(
    "          scripts/omega_runtime.py\n",
    "          scripts/omega_runtime.py\n          scripts/omega_externalized_cognition.py\n",
)
y = y.replace(
    "          tests/test_omega_runtime.py\n",
    "          tests/test_omega_runtime.py\n          tests/test_omega_externalized_cognition.py\n",
)
workflow.write_text(y)

world_test = Path("tests/test_omega_world_turn.py")
t = world_test.read_text()
anchor = '''    assert prepared["authority"] is False
    assert prepared["effect_authority"] is False
'''
replacement = '''    assert prepared["authority"] is False
    assert prepared["effect_authority"] is False
    cognition = grf_input["context"]["omega_externalized_cognition"]
    assert cognition["snapshot"]["state_hash"] == prepared["externalized_state_hash"]
    assert cognition["context_compilation"]["serialized_context_hash"] == prepared["context_compilation_hash"]
    assert len(cognition["specialist_population"]) >= 20
    assert cognition["snapshot"]["cev_snapshot"]["is_scalar"] is False
    assert cognition["authority"] is False
'''
if t.count(anchor) != 1:
    raise SystemExit("world test anchor 1 drift")
t = t.replace(anchor, replacement, 1)

anchor = '''    assert second["predecessor_capsule_digest"] == first_cap["capsule_digest"]
'''
replacement = '''    assert second["predecessor_capsule_digest"] == first_cap["capsule_digest"]
    first_cognition = first_cap["context"]["omega_externalized_cognition"]
    second_cognition = second["grf_input"]["context"]["omega_externalized_cognition"]
    assert second_cognition["snapshot"]["predecessor_state_hash"] == first_cognition["snapshot"]["state_hash"]
    assert second_cognition["reentry_contract"]["kind"] == "EXACT_EXTERNALIZED_STATE"
    assert second_cognition["reentry_contract"]["proof_gap_explicit"] is False
'''
if t.count(anchor) != 1:
    raise SystemExit("world test anchor 2 drift")
t = t.replace(anchor, replacement, 1)

anchor = '''    assert capsule["world_manifold"]["causal_turn_id"] == result.turn_event_id
    assert projection["canonical_truth_credit"] is False
'''
replacement = '''    assert capsule["world_manifold"]["causal_turn_id"] == result.turn_event_id
    cognition = capsule["context"]["omega_externalized_cognition"]
    assert cognition["turn_event_id"] == result.turn_event_id
    assert cognition["snapshot"]["state_hash"]
    assert cognition["context_compilation"]["source_state_hash"] == cognition["snapshot"]["state_hash"]
    assert cognition["reentry_contract"]["kind"] == "GENESIS"
    assert projection["canonical_truth_credit"] is False
'''
if t.count(anchor) != 1:
    raise SystemExit("world test anchor 3 drift")
t = t.replace(anchor, replacement, 1)
world_test.write_text(t)

voice_test = Path("tests/test_omega_voice_world_patch_semantics.py")
t = voice_test.read_text()
if "test_atomic_success_projects_compiled_state_context_without_second_retrieval" not in t:
    t += '''

def test_atomic_success_projects_compiled_state_context_without_second_retrieval(monkeypatch):
    auto_calls, retrieval_calls = [], []
    full = _full(auto_calls, retrieval_calls)
    monkeypatch.setattr(
        patch,
        "_run_atomic_voice_world_turn",
        lambda *a, **kw: {
            "compiled_context": "OMEGA_STATE_PROJECTION source=state:abc\\n[Semantic Task]\\n- proposal only",
            "state_hash": "state:abc",
            "cycle_digest": "cycle:abc",
        },
    )
    wrapped = _install_fresh(monkeypatch, full)
    voice = _Voice()
    wrapped(voice, "hello")
    assert retrieval_calls == [("room-session", "hello")]
    assert auto_calls == []
    assert voice._voice_emergent_context.startswith("OMEGA_STATE_PROJECTION")
    assert voice._voice_externalized_state_hash == "state:abc"
    assert voice._voice_externalized_cycle_digest == "cycle:abc"
'''
voice_test.write_text(t)
