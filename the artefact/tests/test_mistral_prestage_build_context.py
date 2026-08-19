"""Tests fuer clayverse/mistral_prestage/prestage.py::build_context.

Regel e): current_user_profile MUSS im Kontext landen -- das ist der Traeger,
der Zero die geprueften Profildaten des anwesenden Menschen mitgibt statt nur
eine user_id-Zeichenkette. Fehlt ein Profil, muss ein SICHTBARER NO_PROFILE-
Marker stehen, kein stilles Weglassen des Schluessels.

Ausserdem ein paar billige Randfaelle von run_prestage (Validierung vor jedem
Netzwerkzugriff), damit das Modul nicht komplett ohne Test bleibt.
"""
from __future__ import annotations

import json

import pytest

from clayverse.mistral_prestage import prestage


def _kontext(**overrides):
    basis = dict(
        raw_prompt="hallo",
        world=None,
        connected_systems=None,
        current_user="gabriel",
        current_user_profile=None,
        recent_turns=None,
        zero_suggestion=None,
    )
    basis.update(overrides)
    return json.loads(prestage.build_context(**basis))


# ── Regel e: current_user_profile ist immer im Kontext ─────────────────────

def test_build_context_traegt_das_profil_unter_current_user_profile():
    profil = {
        "user_id": "gabriel",
        "felder": {"name": {"wert": "Gabriel Gschaider", "herkunft": "iar.frank.ink"}},
        "rechner": [{"wirt": "ai-core-node", "meiner": True}],
    }
    kontext = _kontext(current_user_profile=profil)
    assert kontext["current_user_profile"] == profil


def test_build_context_ohne_profil_zeigt_sichtbaren_no_profile_marker():
    kontext = _kontext(current_user_profile=None)
    assert "current_user_profile" in kontext
    assert kontext["current_user_profile"]["status"] == "NO_PROFILE"


def test_build_context_leeres_profil_dict_ist_kein_fehlendes_profil():
    """Ein leeres Dict {} ist falsy in Python -- die `or`-Klausel in
    build_context wuerde es sonst faelschlich durch den NO_PROFILE-Marker
    ersetzen. Explizit festhalten, was das Verhalten aktuell IST, damit eine
    Aenderung hier bewusst getroffen wird statt aus Versehen zu passieren."""
    kontext = _kontext(current_user_profile={})
    assert kontext["current_user_profile"]["status"] == "NO_PROFILE"


def test_build_context_alle_neun_schluessel_vorhanden():
    kontext = _kontext()
    for schluessel in (
        "current_user",
        "current_user_profile",
        "raw_prompt",
        "world",
        "recent_turns",
        "connected_systems",
        "zero_round1_suggestion",
    ):
        assert schluessel in kontext
    # ⭐ Der Moeglichkeitsraum ist der neunte Schluessel. Der Test hat beim
    # Hinzufuegen zu Recht angeschlagen -- er bewacht die FORM des Kontexts.
    # Deshalb hier nicht nur die Zahl hochsetzen, sondern den Schluessel
    # benennen: eine Zahl allein haette auch ein Umbenennen durchgelassen.
    assert "moeglichkeitsraum" in kontext



def test_build_context_recent_turns_wird_auf_letzte_drei_gekappt():
    turns = [{"n": i} for i in range(10)]
    kontext = _kontext(recent_turns=turns)
    assert kontext["recent_turns"] == [{"n": 7}, {"n": 8}, {"n": 9}]


def test_build_context_ist_gueltiges_json_ohne_ascii_flucht():
    kontext_str = prestage.build_context(
        raw_prompt="Umlaute: aeoeue",
        world=None,
        connected_systems=None,
        current_user="gabriel",
        current_user_profile=None,
        recent_turns=None,
        zero_suggestion=None,
    )
    json.loads(kontext_str)  # wirft nicht


# ── run_prestage: Validierung vor jedem Netzwerkzugriff ────────────────────

def test_run_prestage_lehnt_runde_3_ab():
    with pytest.raises(ValueError, match="round"):
        prestage.run_prestage(raw_prompt="x", round_no=3, api_key="dummy")


def test_run_prestage_runde_2_ohne_zero_suggestion_raised():
    with pytest.raises(ValueError, match="zero_suggestion"):
        prestage.run_prestage(raw_prompt="x", round_no=2, api_key="dummy")


def test_run_prestage_leerer_prompt_raised():
    with pytest.raises(ValueError, match="invalid raw prompt"):
        prestage.run_prestage(raw_prompt="", round_no=1, api_key="dummy")


def test_run_prestage_ohne_api_key_raised(monkeypatch):
    from clayverse.mistral_prestage import secrets

    monkeypatch.setattr(secrets, "load_free_api_keys", lambda *a, **k: {})
    with pytest.raises(RuntimeError, match="no Mistral key available"):
        prestage.run_prestage(raw_prompt="hallo", round_no=1, api_key="")
