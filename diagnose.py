#!/usr/bin/env python3
"""seite_diagnose -- warum eine Seite NICHT erreichbar ist, geschichtet.

⭐⭐ ANLASS (Gabriel 19.08.): "sowas muss zero auch checken."
Gabriel meldete: seimensch.net und leihmich.org nicht erreichbar. Der Server
war KERNGESUND -- HTTP 200 in 0,07s. Die Ursache lag auf SEINER Kiste: eine
Zeile in /etc/hosts leitete die Domains auf 127.0.0.2 (localhost) um, Rest
eines toten SSH-Tunnels. Die Seite war vom Server aus oben und von seinem
Rechner aus tot.

⭐ DIE LEHRE, die dieses Werkzeug fest verdrahtet: "erreichbar" ist kein
Ja/Nein, sondern ein VON WO. Eine Seite kann von einem Standpunkt leben und
vom anderen sterben. `seite_pruefen` blickte nur von einem Standpunkt. Diese
Diagnose prueft geschichtet und TRENNT server-seitig von client-seitig -- denn
die Antwort auf "meine Seite ist weg" ist meistens nicht "starte den Server
neu", sondern "dein Server ist gesund, das Problem sitzt zwischen dir und ihm".

DIE SCHICHTEN, von unten nach oben:
  1. Oeffentliches DNS: worauf loest die Domain auf?
  2. Stimmt das mit dem erwarteten Server ueberein?
  3. Ist Port 443 auf dem erwarteten Server offen?
  4. Antwortet HTTPS -- und mit welchem Status?
  5. Ist der Inhalt echt (Titel, Groesse) oder eine 200-Fehlerseite?

Und dann das Urteil: leuchtet alles server-seitig gruen, aber der Mensch kommt
nicht durch, liegt es lokal -- und genau DIE Ursachen, die diesen Menschen
schon zweimal getroffen haben (hosts-Umleitung, Provider-DNS mit NXDOMAIN),
werden namentlich genannt. Ein Werkzeug, das nur "Server ok" sagt, laesst den
Menschen mit dem Rest allein.
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import time

# Erwartete Auslieferungs-IP je Domain. Nur eigene Seiten -- das ist eine
# Diagnose der eigenen Auslieferung, kein Netzwerkscanner.
ERWARTET = {
    "seimensch.net": "72.61.19.188", "www.seimensch.net": "72.61.19.188",
    "leihmich.org": "72.61.19.188", "www.leihmich.org": "72.61.19.188",
    "herzrad.at": "72.61.19.188", "www.herzrad.at": "72.61.19.188",
    "seimensch.frank.ink": "72.61.19.188",
    "frank.ink": "31.97.117.141", "entityos.frank.ink": "31.97.117.141",
    "iar.frank.ink": "31.97.117.141", "retina.frank.ink": "31.97.117.141",
    "oar.frank.ink": "31.97.117.141", "kosal.frank.ink": "31.97.117.141",
}


def _dns(host: str) -> list[str]:
    try:
        return sorted({ai[4][0] for ai in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)})
    except Exception:
        return []


def _port_offen(ip: str, port: int = 443, timeout: float = 6.0) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


def _https(host: str, ip: str | None) -> dict:
    """HTTPS-Abruf. Mit ip: gezielt an den erwarteten Server (SNI bleibt host)."""
    cmd = ["curl", "-sS", "-m", "20", "-o", "/dev/null",
           "-w", "%{http_code} %{time_total} %{size_download}"]
    if ip:
        cmd += ["--resolve", f"{host}:443:{ip}"]
    cmd += ["-H", "Cache-Control: no-cache", f"https://{host}/"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        m = re.match(r"\s*(\d+)\s+([\d.]+)\s+(\d+)", r.stdout or "")
        if not m:
            return {"ok": False, "fehler": (r.stderr or r.stdout or "keine Antwort")[:180]}
        return {"ok": r.returncode == 0 and m.group(1) != "000",
                "status": int(m.group(1)), "ms": round(float(m.group(2)) * 1000),
                "bytes": int(m.group(3))}
    except subprocess.TimeoutExpired:
        return {"ok": False, "fehler": "keine Antwort in 30s"}


def _titel(host: str, ip: str | None) -> str | None:
    cmd = ["curl", "-sS", "-m", "20"]
    if ip:
        cmd += ["--resolve", f"{host}:443:{ip}"]
    cmd += [f"https://{host}/"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        t = re.search(r"<title[^>]*>(.*?)</title>", r.stdout or "", re.S | re.I)
        return t.group(1).strip()[:120] if t else None
    except Exception:
        return None


def diagnose(url: str) -> dict:
    host = re.sub(r"^https?://", "", str(url or "")).split("/")[0].split(":")[0].lower()
    if not host:
        return {"fehler": "keine Domain angegeben"}
    if host not in ERWARTET:
        return {"abgewiesen": f"{host!r} ist keine eigene Seite. Diagnose gibt es fuer: "
                              + ", ".join(sorted(ERWARTET))}

    erwartet_ip = ERWARTET[host]
    schichten = []

    # 1+2: DNS und ob es stimmt
    aufgeloest = _dns(host)
    dns_stimmt = erwartet_ip in aufgeloest
    schichten.append({"schicht": "DNS", "aufgeloest_auf": aufgeloest or "NICHTS",
                      "erwartet": erwartet_ip, "stimmt": dns_stimmt})

    # 3: Port auf dem ERWARTETEN Server (nicht auf dem, worauf DNS zeigt --
    #    so trennt sich "Server unten" von "DNS zeigt woanders hin")
    port = _port_offen(erwartet_ip)
    schichten.append({"schicht": "Port 443 am erwarteten Server",
                      "server": erwartet_ip, "offen": port})

    # 4+5: HTTPS + Inhalt, gezielt am erwarteten Server
    https = _https(host, erwartet_ip)
    titel = _titel(host, erwartet_ip) if https.get("ok") else None
    inhalt_echt = bool(titel) and (https.get("bytes", 0) > 500)
    schichten.append({"schicht": "HTTPS am erwarteten Server", **https,
                      "titel": titel, "inhalt_echt": inhalt_echt})

    server_gesund = port and https.get("ok") and https.get("status") == 200 and inhalt_echt

    # Urteil -- und das ist der Kern: server-seitig von client-seitig trennen.
    if server_gesund and dns_stimmt:
        urteil = (
            f"SERVER GESUND, DNS RICHTIG. {host} liefert HTTP 200 mit echtem Inhalt "
            f"(\"{titel}\", {https.get('bytes')} Bytes) vom erwarteten Server {erwartet_ip}, "
            f"und das oeffentliche DNS zeigt korrekt dorthin. "
            "⭐ Wenn ein MENSCH die Seite trotzdem nicht erreicht, liegt es NICHT am Server, "
            "sondern zwischen ihm und dem Server -- auf SEINER Seite. Die zwei Ursachen, die "
            "hier schon vorkamen: (1) eine Umleitung in /etc/hosts auf 127.0.0.x (Rest eines "
            "toten Tunnels) -- pruefen mit `getent hosts " + host + "`, es MUSS " + erwartet_ip +
            " zeigen; (2) Provider-DNS, das NXDOMAIN liefert -- DNS testweise auf 1.1.1.1 "
            "stellen. Weiter: VPN, Proxy, lokaler DNS-Cache.")
    elif server_gesund and not dns_stimmt:
        urteil = (
            f"SERVER GESUND, aber DNS ZEIGT FALSCH. {host} laeuft auf {erwartet_ip} und "
            f"antwortet dort mit 200 -- aber das DNS loest auf {aufgeloest or 'NICHTS'} auf. "
            "Wer der normalen Aufloesung folgt, landet woanders. Ursache: ein /etc/hosts-"
            f"Eintrag oder ein DNS-Satz, der nicht auf {erwartet_ip} zeigt.")
    elif not port:
        urteil = (
            f"SERVER NICHT ERREICHBAR. Port 443 auf {erwartet_ip} ist zu -- der Webserver "
            "ist unten, oder eine Firewall blockt. DAS ist ein echtes Server-Problem, kein "
            "lokales. (nginx-Status und Erreichbarkeit des VPS pruefen.)")
    else:
        urteil = (
            f"SERVER ANTWORTET NICHT SAUBER. Port {('offen' if port else 'zu')}, "
            f"HTTPS-Status {https.get('status', https.get('fehler'))}, Inhalt "
            f"{'echt' if inhalt_echt else 'fehlt/Fehlerseite'}. Kein glatter 200 mit Inhalt "
            f"-- am Server nachsehen, nicht beim Nutzer.")

    return {"domain": host, "erwarteter_server": erwartet_ip,
            "server_gesund": bool(server_gesund), "dns_stimmt": dns_stimmt,
            "schichten": schichten, "urteil": urteil, "geprueft": time.time()}


if __name__ == "__main__":
    import sys
    print(json.dumps(diagnose(sys.argv[1] if len(sys.argv) > 1 else "seimensch.net"),
                     ensure_ascii=False, indent=2))
