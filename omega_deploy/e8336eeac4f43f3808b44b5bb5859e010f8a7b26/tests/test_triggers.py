from omega.triggers import TRIGGERS, convergence_requires_reentry, resolve_trigger


def test_999_is_canonical_reentry_not_maximal_convergence():
    inv = resolve_trigger("999")
    assert inv is not None
    assert inv.spec.name == "REENTRY"
    assert inv.spec.maximal_convergence is False
    assert inv.spec.requires_reentry is False


def test_777_is_distinct_convergence_trigger_and_requires_999_semantics_first():
    inv = resolve_trigger("777")
    assert inv is not None
    assert inv.spec.name == "CONVERGENCE"
    assert inv.spec.maximal_convergence is True
    assert inv.spec.requires_reentry is True
    assert inv.spec.reentry_trigger == "999"
    assert convergence_requires_reentry(inv) is True


def test_trigger_can_carry_free_text_instruction_without_changing_identity():
    inv = resolve_trigger("777 NEUES TRIGGERWORT BITTE SUCHEN UND MAXIMAL EFFEKTIV DURCHLAUFEN")
    assert inv is not None
    assert inv.spec.token == "777"
    assert inv.instruction.startswith("NEUES TRIGGERWORT")


def test_embedded_or_prefixed_numbers_do_not_trigger():
    assert resolve_trigger("1777") is None
    assert resolve_trigger("foo 777") is None
    assert resolve_trigger("7777") is None
    assert resolve_trigger("") is None


def test_registry_keeps_777_and_999_semantically_distinct():
    assert set(TRIGGERS) == {"777", "999"}
    assert TRIGGERS["777"].meaning != TRIGGERS["999"].meaning
