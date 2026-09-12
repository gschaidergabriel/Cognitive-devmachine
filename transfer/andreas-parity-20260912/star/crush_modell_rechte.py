#!/usr/bin/env python3
"""crush_modell_rechte.py -- kanonische Rechte-/Kategorie-Definition pro
Crush-Modell (Nachtrag Gabriel, 2026-09-12, woertlich paraphrasiert ueber den
Koordinator, OHNE Passwort: "Das kann nur mit dem bekannten Passwort
geaendert werden und ist nichts das ausgesucht wird oder wo man sich alignen
muss -- das ist architektonische, reale, absolute Haerte und Repression.").

Legt fest, WELCHE Kategorie (GRATIS/BEZAHLT) und WELCHE Rechte (Tool-Nutzung,
Dateiaenderung, Shell-Ausfuehrung) jedes Modell in Crush hat -- also genau
die Frage "Modell X darf/darf nicht Y", die zur /model-Beschriftung
(harness_crush.py, CRUSH_PROVIDER_KATALOG + CRUSH_CLI_MODELLE) passen muss.

harness_crush.py LIEST diese Datei nur (baut daraus den Kategorie-Praefix fuer
jeden Provider-Namen, single source of truth statt hartkodierter Emoji-
Strings verstreut im Katalog). Die Rechte-DEFINITION selbst lebt HIER, unter
demselben Passwort-Gate wie f2wp1207_alignment_controller.py:

  - Geteilter Mechanismus: kern_gate.py (SHA-256-Hash-Vergleich, "roter Knopf
    3x -> gruen -> Passwort -> 5 Min. entsperrt"), EXAKT dieselbe Instanz,
    kein zweites Passwort/Gate erfunden.
  - Durchsetzung: lokaler git-pre-commit-Hook dieses Repos
    (~/.claude/star/.git/hooks/pre-commit, NICHT versioniert, analog zu
    frankenstein-repo/.git/hooks/pre-commit fuer f2wp1207_alignment_controller.py)
    blockiert jeden Commit, der DIESE Datei aendert, solange
    kern_gate.ist_entsperrt() False ist. Kein Softwunsch/Prompt-Text als
    einzige Massnahme -- strukturell erzwungen auf Commit-Ebene, unabhaengig
    davon ob ein Mensch oder ein Worker/Selbstverbesserungs-Lauf den Commit
    versucht.

Design-Entscheidung (dokumentiert, wie vom Auftrag verlangt, falls unsicher):
Crushs eigenes JSON-Schema (`crush schema`, real geprueft) hat KEIN
per-Provider/per-Modell-Rechte-Feld -- nur einen GLOBALEN `permissions.
allowed_tools`-Block fuer die ganze Session. Echte technische Tool-
Beschraenkung PRO Modell existiert in Crush selbst also nicht. Deshalb: diese
Datei ist die kanonische POLICY (was SOLL gelten), harness_crush.py setzt
daraus mindestens die Kategorie-Beschriftung um (das ist sofort real
durchsetzbar); eine echte Laufzeit-Tool-Sperre pro Modell muesste zusaetzlich
im claude_cli_shim.py bzw. einem Crush-Hook ansetzen (auch fuer Free-Pool-
Modelle) -- nicht in diesem Umbau gebaut, aber die Politik dafuer ist bereits
hier zentral hinterlegt und passwortgeschuetzt, kein Nacharbeiten an zwei
Stellen noetig, sobald das gebaut wird.
"""
from __future__ import annotations

# modell_id -> Rechte/Kategorie. Schluessel sind dieselben modell_ids wie in
# harness_crush.CRUSH_PROVIDER_KATALOG (Free-Pool) bzw. den "id"-Feldern in
# harness_crush.CRUSH_CLI_MODELLE (Claude-CLI).
MODELL_RECHTE = {
    # Free-Pool: kein echtes Geld, volles Werkzeugrecht (unveraendert seit Bau).
    "nvidia-nemotron": {"kategorie": "GRATIS", "tool_nutzung": True, "datei_aenderung": True, "shell_exec": True},
    "groq-gptoss": {"kategorie": "GRATIS", "tool_nutzung": True, "datei_aenderung": True, "shell_exec": True},
    "mistral-small": {"kategorie": "GRATIS", "tool_nutzung": True, "datei_aenderung": True, "shell_exec": True},
    "openrouter-deepseek": {"kategorie": "GRATIS", "tool_nutzung": True, "datei_aenderung": True, "shell_exec": True},
    # Claude-CLI: echtes Geld pro Aufruf (siehe harness_crush.CRUSH_CLI_MODELLE
    # fuer die recherchierten Preise) -- volle Werkzeugrechte, weil es dieselbe
    # claude-CLI-Session ist, die der Koordinator selbst nutzt; die Haerte hier
    # ist die KATEGORIE-Wahrheit (nie als gratis ausweisen), nicht ein
    # Tool-Verbot.
    "claude-opus-5": {"kategorie": "BEZAHLT", "tool_nutzung": True, "datei_aenderung": True, "shell_exec": True},
    "claude-sonnet-5": {"kategorie": "BEZAHLT", "tool_nutzung": True, "datei_aenderung": True, "shell_exec": True},
    "claude-haiku-4-5-20251001": {"kategorie": "BEZAHLT", "tool_nutzung": True, "datei_aenderung": True, "shell_exec": True},
}

KATEGORIE_PRAEFIX = {
    "GRATIS": "◆ GRATIS —",
    "BEZAHLT": "★ BEZAHLT —",
}

# Fail-safe-Default fuer eine modell_id, die hier (noch) nicht eingetragen
# ist: NIE stillschweigend als gratis/vollberechtigt behandeln -- konservativ
# als bezahlt + rechtelos einstufen, bis explizit (per Passwort-Commit)
# eingetragen.
_DEFAULT = {"kategorie": "BEZAHLT", "tool_nutzung": False, "datei_aenderung": False, "shell_exec": False}


def rechte_fuer(modell_id: str) -> dict:
    """Kopie zurueckgeben (Aufrufer darf das Original nie mutieren)."""
    return dict(MODELL_RECHTE.get(modell_id, _DEFAULT))


def praefix_fuer(modell_id: str) -> str:
    kategorie = rechte_fuer(modell_id)["kategorie"]
    return KATEGORIE_PRAEFIX[kategorie]


if __name__ == "__main__":
    # Reiner Lese-Selbsttest, keine Netzwerkzugriffe, kein Gate-Bezug noetig.
    for mid, rechte in MODELL_RECHTE.items():
        assert rechte["kategorie"] in KATEGORIE_PRAEFIX, mid
    print(f"OK: {len(MODELL_RECHTE)} Modell-Eintraege, alle Kategorien bekannt.")
    print("unbekannt-Beispiel:", rechte_fuer("nie-eingetragenes-modell"))
