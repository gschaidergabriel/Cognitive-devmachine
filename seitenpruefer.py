#!/usr/bin/env python3
"""Der Seitenpruefer -- Zero soll nachsehen koennen, statt zu hoffen.

⭐⭐ GEMESSEN IM ANDREAS-TEST: Zero berichtete, die ZVR-Korrektur sei "still
local, still not live". Sie WAR live. Sein Schluss war trotzdem richtig
gezogen -- er sah nur den Spiegel auf diesem Wirt und hatte kein Mittel, die
oeffentliche Seite anzusehen.

⚠️ UND DAS WAR MEIN FEHLER, nicht seiner. In seinem Handbuch steht seit heute:
"Pruefe danach die Seite, statt den Erfolg zu behaupten." Ich habe ihm eine
Pflicht gegeben und kein Werkzeug dazu. Eine Anweisung, die sich nicht
befolgen laesst, erzieht nicht zur Sorgfalt, sondern zum Erfinden -- entweder
behauptet er den Erfolg doch, oder er sagt jedes Mal "kann ich nicht pruefen",
und beides ist schlechter als nachsehen.

⚠️⚠️ UND DER ZWEITE, GROESSERE BEFUND DAHINTER: `/srv/git/seimensch.git` auf
DIESEM Wirt ist ein SPIEGEL. Die Seite wird von 72.61.19.188 ausgeliefert.
Ein Push hierher durchlaeuft den vollstaendigen Deploy-Haken -- Sicherung,
Integritaetspruefung, Spiegelung, chown -- und meldet Erfolg. Nur sieht die
oeffentliche Seite davon nichts. Das ist die gefaehrlichste Sorte Erfolg:
einer mit vollstaendigem Beleg.

Deshalb faehrt dieses Werkzeug ueber HTTP an die ECHTE Adresse. Nur lesend,
nur die eigenen Domains, kein Umweg.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from urllib.parse import urlparse

# Erlaubnisliste. Nur eigene Seiten -- dies ist kein Netzzugang, sondern ein
# Blick auf die eigene Auslieferung.
EIGENE = (
    "seimensch.net", "www.seimensch.net",
    "leihmich.org", "www.leihmich.org",
    "herzrad.at", "www.herzrad.at",
    "frank.ink", "entityos.frank.ink", "iar.frank.ink", "retina.frank.ink",
    "oar.frank.ink", "kosal.frank.ink", "seimensch.frank.ink",
)
MAX_BYTES = 400_000


def _erlaubt(url: str) -> tuple[bool, str]:
    u = urlparse(url if "://" in url else "https://" + url)
    if u.scheme not in ("http", "https"):
        return False, f"nur http/https, nicht {u.scheme!r}"
    wirt = (u.hostname or "").lower()
    if wirt not in EIGENE:
        return False, (f"{wirt!r} ist keine eigene Seite. Erlaubt: {', '.join(EIGENE)}. "
                       "Dieses Werkzeug ist ein Blick auf die eigene Auslieferung, "
                       "kein Netzzugang.")
    return True, ""


def pruefen(url: str, suche: str = "") -> dict:
    """Eine eigene Seite abrufen und sagen, was WIRKLICH dort steht.

    `suche` ist ein regulaerer Ausdruck. Steht er drin, ist die Aenderung
    angekommen; steht er nicht drin, ist sie es nicht -- und das ist ein
    Befund, keine Vermutung.
    """
    ok, grund = _erlaubt(url)
    if not ok:
        return {"abgewiesen": grund}
    voll = url if "://" in url else "https://" + url
    # Zwischenspeicher umgehen: nach einem Deploy ist die alte Fassung genau
    # das, was man faelschlich fuer den neuen Zustand haelt.
    trenner = "&" if "?" in voll else "?"
    voll = f"{voll}{trenner}_pruef={int(time.time())}"
    try:
        r = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "25", "--max-filesize", str(MAX_BYTES),
             "-H", "Cache-Control: no-cache", "-H", "Pragma: no-cache",
             "-w", "\n__STATUS__%{http_code} __ZEIT__%{time_total} __GROESSE__%{size_download}",
             voll],
            capture_output=True, text=True, timeout=40)
    except subprocess.TimeoutExpired:
        return {"url": voll, "fehler": "keine Antwort in 40s -- das ist ein Befund, "
                                       "kein leeres Ergebnis"}
    aus = r.stdout or ""
    m = re.search(r"__STATUS__(\d+) __ZEIT__([\d.]+) __GROESSE__(\d+)\s*$", aus)
    text = aus[:m.start()] if m else aus
    erg = {"url": voll,
           "status": int(m.group(1)) if m else None,
           "ms": round(float(m.group(2)) * 1000) if m else None,
           "bytes": int(m.group(3)) if m else len(text),
           "titel": (re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I) or [None, None])[1]}
    if erg["titel"]:
        erg["titel"] = erg["titel"].strip()[:120]
    if r.returncode != 0:
        erg["fehler"] = (r.stderr or "")[:220]
        return erg
    if suche:
        try:
            treffer = [x.group(0)[:160] for x in re.finditer(suche, text, re.I)][:8]
        except re.error as e:
            return {**erg, "fehler": f"ungueltiges Muster: {e}"}
        erg["gesucht"] = suche
        erg["treffer"] = treffer
        erg["gefunden"] = bool(treffer)
        erg["urteil"] = (
            f"GEFUNDEN ({len(treffer)}x) -- die Aenderung ist oeffentlich sichtbar."
            if treffer else
            "NICHT GEFUNDEN -- was du erwartet hast, steht dort NICHT. Entweder ist der "
            "Deploy nicht durchgelaufen, oder er lief auf einen Spiegel statt auf die "
            "ausliefernde Maschine. ⚠️ /srv/git/seimensch.git auf diesem Wirt ist ein "
            "SPIEGEL: ein Push dorthin durchlaeuft den ganzen Deploy-Haken und meldet "
            "Erfolg, waehrend seimensch.net von 72.61.19.188 ausgeliefert wird.")
    return erg


if __name__ == "__main__":
    import sys
    print(json.dumps(pruefen(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""),
                     ensure_ascii=False, indent=2))
