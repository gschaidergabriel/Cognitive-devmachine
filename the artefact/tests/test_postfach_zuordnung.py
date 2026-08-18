"""Wer welches Postfach bekommt -- und wer keines.

Der Grund fuer diesen Test steht im Auftrag: Andreas' Clerk-Konto laeuft auf
einer Gmail-Adresse, sein Postfach auf frank.ink. Ein Abgleich ueber die
E-Mail-Adresse haette ihm still KEIN Postfach gegeben, und "still kein" merkt
man erst, wenn eine Mail fehlt. Die Zuordnung laeuft deshalb ueber die
Clerk-Karte, und das wird hier festgenagelt.
"""
import pytest

from clayverse.postfach import (
    PostfachNichtEingerichtet,
    Zugaenge,
    Zugang,
    postfach_fuer_menschen,
    postfach_fuer_subjekt,
    zugaenge_laden,
)

# Absichtlich unverwechselbare Zeichenketten: taucht eine davon irgendwo auf,
# wo sie nicht hingehoert, ist es kein Zufallstreffer.
GEHEIM_G = "GEHEIM-GABRIEL-6f2a"
GEHEIM_A = "GEHEIM-ANDREAS-9c41"

# Die Karte, wie sie CLAYVERSE_CLERK_MAP_JSON liefert. Andreas' Subjekt gehoert
# zu herzradgraz@gmail.com -- die Adresse taucht hier bewusst NICHT auf, weil
# sie fuer die Zuordnung keine Rolle spielen darf.
KARTE = {"clerk_subject_gabriel": "gabriel", "clerk_subject_andreas": "andreas"}


def _zugaenge() -> Zugaenge:
    return Zugaenge(
        postfaecher={
            "gabriel": Zugang("gabriel@frank.ink", GEHEIM_G),
            "andreas": Zugang("andreas@frank.ink", GEHEIM_A),
        },
        imap_host="mail.frank.ink", imap_port=993,
        smtp_host="mail.frank.ink", smtp_port=587,
    )


def test_clerk_subjekt_findet_sein_postfach_ueber_die_karte():
    zugaenge = _zugaenge()
    assert postfach_fuer_subjekt(zugaenge, KARTE, "clerk_subject_gabriel").adresse == "gabriel@frank.ink"
    assert postfach_fuer_subjekt(zugaenge, KARTE, "clerk_subject_andreas").adresse == "andreas@frank.ink"


def test_drittes_subjekt_bekommt_kein_postfach():
    """Wie der IdentityRouter: unbekannt heisst abgewiesen, nicht "irgendeines"."""
    with pytest.raises(PermissionError, match="unmapped Clerk subject"):
        postfach_fuer_subjekt(_zugaenge(), KARTE, "clerk_subject_fremd")


def test_bekanntes_subjekt_ohne_eingetragenes_postfach_wird_abgewiesen():
    unvollstaendig = Zugaenge(
        postfaecher={"gabriel": Zugang("gabriel@frank.ink", GEHEIM_G)},
        imap_host="mail.frank.ink", imap_port=993,
        smtp_host="mail.frank.ink", smtp_port=587,
    )
    with pytest.raises(PermissionError, match="kein Postfach fuer andreas"):
        postfach_fuer_subjekt(unvollstaendig, KARTE, "clerk_subject_andreas")


def test_kein_mensch_ausserhalb_der_zwei():
    with pytest.raises(PermissionError):
        postfach_fuer_menschen(_zugaenge(), "zero")


def test_passwort_steht_in_keiner_textdarstellung():
    """Ein Fehlerbericht formatiert gern ganze Objekte. Genau da faellt es raus."""
    zugaenge = _zugaenge()
    for text in (repr(zugaenge), str(zugaenge), repr(zugaenge.postfaecher["gabriel"]),
                 str(zugaenge.postfaecher["gabriel"]), f"{zugaenge}", f"{zugaenge.postfaecher['andreas']}"):
        assert GEHEIM_G not in text
        assert GEHEIM_A not in text
    assert "<verborgen>" in repr(zugaenge.postfaecher["gabriel"])


def test_zugangsdatei_wird_gelesen_wie_sie_auf_dem_wirt_liegt(tmp_path):
    datei = tmp_path / "postfach.env"
    datei.write_text(
        "# Zugaenge, 640 root:clay\n"
        f"ENTITYOS_POSTFACH_GABRIEL_ADRESSE=gabriel@frank.ink\n"
        f"ENTITYOS_POSTFACH_GABRIEL_PASSWORT={GEHEIM_G}\n"
        f"ENTITYOS_POSTFACH_ANDREAS_ADRESSE=andreas@frank.ink\n"
        f"ENTITYOS_POSTFACH_ANDREAS_PASSWORT={GEHEIM_A}\n"
        "ENTITYOS_IMAP_HOST=mail.frank.ink\n"
        "ENTITYOS_IMAP_PORT=993\n"
        "ENTITYOS_SMTP_HOST=mail.frank.ink\n"
        "ENTITYOS_SMTP_PORT=587\n",
        encoding="utf-8",
    )
    zugaenge = zugaenge_laden(datei)
    assert zugaenge.imap_port == 993 and zugaenge.smtp_port == 587
    assert zugaenge.postfaecher["andreas"].adresse == "andreas@frank.ink"
    assert zugaenge.postfaecher["andreas"].passwort == GEHEIM_A
    # Ohne eingetragene System-Postfaecher gibt es keine. Leer heisst leer.
    assert zugaenge.system == {}


def test_fehlende_zugangsdatei_ist_ein_betriebsfehler_kein_leeres_postfach(tmp_path):
    with pytest.raises(PostfachNichtEingerichtet):
        zugaenge_laden(tmp_path / "gibtsnicht.env")


def test_halb_eingetragenes_systempostfach_wird_nicht_angeboten(tmp_path):
    """Ein Reiter, der beim Anklicken immer scheitert, ist schlechter als keiner."""
    datei = tmp_path / "postfach.env"
    datei.write_text(
        f"ENTITYOS_POSTFACH_GABRIEL_ADRESSE=gabriel@frank.ink\n"
        f"ENTITYOS_POSTFACH_GABRIEL_PASSWORT={GEHEIM_G}\n"
        f"ENTITYOS_POSTFACH_ANDREAS_ADRESSE=andreas@frank.ink\n"
        f"ENTITYOS_POSTFACH_ANDREAS_PASSWORT={GEHEIM_A}\n"
        "ENTITYOS_IMAP_HOST=mail.frank.ink\nENTITYOS_IMAP_PORT=993\n"
        "ENTITYOS_SMTP_HOST=mail.frank.ink\nENTITYOS_SMTP_PORT=587\n"
        "ENTITYOS_POSTFACH_SYSTEM_ABUSE_ADRESSE=abuse@frank.ink\n"
        "ENTITYOS_POSTFACH_SYSTEM_WELCOME_ADRESSE=welcome@seimensch.net\n"
        "ENTITYOS_POSTFACH_SYSTEM_WELCOME_PASSWORT=GEHEIM-WELCOME-1a2b\n",
        encoding="utf-8",
    )
    zugaenge = zugaenge_laden(datei)
    assert set(zugaenge.system) == {"welcome"}
    assert zugaenge.system["welcome"].adresse == "welcome@seimensch.net"
