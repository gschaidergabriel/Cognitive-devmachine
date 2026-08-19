"""Die zwei Werkzeuglisten muessen deckungsgleich sein.

⚠️ WARUM DIESER TEST EXISTIERT: `bahn_faehigkeit` und `bahn_lage` standen in
policy/managed-settings.json und fehlten in DEFAULT_ALLOWED_TOOLS. Zwei Listen,
und die ENGERE gewinnt -- Zero hatte die Erlaubnis und konnte sie nicht
benutzen. Gefunden wurde das nicht im Betrieb, sondern beim Nachzaehlen: im
Betrieb faellt so etwas gar nicht auf, weil ein Werkzeug, das nie angeboten
wird, auch nie einen Fehler wirft.

⭐ Das ist die unangenehmste Sorte Luecke, weil BEIDE Seiten fuer sich richtig
aussehen. Wer die Freigabeliste liest, sieht ein gewaehrtes Werkzeug. Wer die
Angebotsliste liest, sieht eine vollstaendige Liste. Erst der Vergleich zeigt
den Fehler -- also muss der Vergleich automatisch laufen.
"""
import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def _freigegeben() -> set[str]:
    d = json.loads((WURZEL / "policy" / "managed-settings.json").read_text(encoding="utf-8"))
    return {x for x in d["permissions"]["allow"] if x.startswith("mcp__")}


def _angeboten() -> set[str]:
    text = (WURZEL / "clayverse" / "mistral_prestage" / "headless_zero.py").read_text(
        encoding="utf-8")
    block = text[text.index("DEFAULT_ALLOWED_TOOLS"):]
    block = block[:block.index("\n)")]
    return set(re.findall(r'"(mcp__[a-z_]+__[a-z_]+)"', block))


def test_freigegeben_wird_auch_angeboten():
    """Was freigegeben ist, muss Zero auch angeboten werden."""
    fehlt = _freigegeben() - _angeboten()
    assert not fehlt, (
        "In policy/managed-settings.json freigegeben, aber nicht in "
        f"DEFAULT_ALLOWED_TOOLS angeboten: {sorted(fehlt)}. "
        "Die engere Liste gewinnt -- diese Freigaben sind wirkungslos.")


def test_angeboten_ist_auch_freigegeben():
    """Und umgekehrt: nichts anbieten, was nicht freigegeben ist.

    Diese Richtung ist die sicherheitsrelevante. Ein Werkzeug anzubieten, das
    die Freigabeliste nicht kennt, heisst, dass die Freigabeliste nicht mehr
    die Wahrheit ueber Zeros Faehigkeiten ist -- und dann ist sie als
    Pruefinstrument wertlos.
    """
    zuviel = _angeboten() - _freigegeben()
    assert not zuviel, (
        f"In DEFAULT_ALLOWED_TOOLS angeboten, aber in policy nicht freigegeben: "
        f"{sorted(zuviel)}. Damit waere die Freigabeliste nicht mehr die Wahrheit "
        "ueber Zeros Faehigkeiten.")


def test_verbote_stehen_nicht_in_der_freigabe():
    """Artifact bleibt verboten. Bash ist jetzt bewusst ERLAUBT (Gabriel 19.08.):
    Zero handelt direkt wie eine Claude-Code-Sitzung. Der Schutz des
    Unersetzlichen liegt jetzt im PreToolUse-Zaun-Hook (clayverse.fence_hook),
    nicht mehr in einem Bash-Verbot."""
    d = json.loads((WURZEL / "policy" / "managed-settings.json").read_text(encoding="utf-8"))
    verboten = set(d["permissions"].get("deny", []))
    erlaubt = set(d["permissions"]["allow"])
    assert "Artifact" in verboten, "Artifact bleibt verboten."
    assert "Bash" not in verboten, "Bash ist jetzt erlaubt -- Zero handelt direkt."
    assert "Bash" in erlaubt, "Bash muss freigegeben sein, damit Zero handeln kann."
    # Der Zaun ersetzt das Verbot: ein PreToolUse-Hook auf fence_hook.
    cmds = [hk["command"] for grp in d.get("hooks", {}).get("PreToolUse", [])
            for hk in grp.get("hooks", [])]
    assert any("clayverse.fence_hook" in c for c in cmds), \
        "Der Zaun-Hook (fence_hook) MUSS als PreToolUse haengen."
    assert not (verboten & _freigegeben()), "etwas ist gleichzeitig verboten und freigegeben"
