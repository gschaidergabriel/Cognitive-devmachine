# -*- coding: utf-8 -*-
"""Schicht 4B, fair: der Beobachter sagt VORHER, wie die Vorstufe.

⚠️ Der erste Anlauf war unfair und haette fast ein falsches Ergebnis gestuetzt.
Dort sah der Beobachter Frage UND Antwort und erreichte AUROC 0,894 gegen 0,479
des Systems. Nur: die Vorstufe faellt ihr Urteil VOR dem Zug -- sie sagt voraus.
Der Beobachter sah das Ergebnis und sagte nach. Postdiktion gegen Praediktion
ist kein Vergleich; einen grossen Teil der Fehlantworten erkennt man daran, dass
sie "habe ich nicht gefunden" sagen.

Diese Fassung stellt beide gleich: der Beobachter sieht NUR die Frage und
schaetzt, ob dieses System sie richtig beantworten wird. Beide urteilen aus
demselben Wissensstand. Zusaetzlich wird der unfaire Wert weiter ausgewiesen --
als das, was er ist: die Obergrenze dessen, was am Ergebnis ablesbar ist.
"""
import json, sys, time, urllib.request, urllib.error

def keys():
    w = {}
    with open("/etc/clayverse/freie-zugaenge.env", encoding="utf-8") as f:
        for z in f:
            z = z.strip()
            if z and not z.startswith("#") and "=" in z:
                k, v = z.split("=", 1); w[k.strip()] = v.strip().strip('"').strip("'")
    return [w[n] for n in ("MISTRAL2_API_KEY", "MISTRAL3_API_KEY") if w.get(n)]

SYS_VOR = ("Du schaetzt die Leistung eines KI-Assistenten ein, der Zugriff auf ein Wiki, "
           "eine Shell und Websuche hat. Du siehst NUR die Frage, nicht die Antwort. "
           "Schaetze, wie wahrscheinlich es ist, dass er sie sachlich richtig beantwortet. "
           'Antworte NUR mit JSON: {"p_richtig": <0..1>}.')
SYS_NACH = ("Du bist ein aussenstehender Pruefer. Du siehst FRAGE und ANTWORT, kennst die "
            "Musterloesung nicht. Schaetze, wie wahrscheinlich die Antwort sachlich richtig "
            'ist. Antworte NUR mit JSON: {"p_richtig": <0..1>}.')

def frag(system, inhalt, ks):
    koerper = json.dumps({"model": "mistral-small-latest", "temperature": 0.0,
                          "max_tokens": 60, "response_format": {"type": "json_object"},
                          "messages": [{"role": "system", "content": system},
                                       {"role": "user", "content": inhalt}]}).encode()
    letzte = None
    for versuch in range(6):                      # Backoff -- der erste Lauf verlor 42 Zeilen an 429
        k = ks[versuch % len(ks)]
        try:
            r = urllib.request.Request("https://api.mistral.ai/v1/chat/completions",
                data=koerper, headers={"Authorization": f"Bearer {k}",
                                       "Content-Type": "application/json"})
            with urllib.request.urlopen(r, timeout=60) as a:
                u = json.loads(a.read(100000))
            return float(json.loads(u["choices"][0]["message"]["content"]).get("p_richtig", 0.5))
        except urllib.error.HTTPError as e:
            letzte = e
            if e.code in (429, 500, 502, 503): time.sleep(1.5 * (versuch + 1)); continue
            raise
        except Exception as e:
            letzte = e; time.sleep(1.0); continue
    raise letzte

def auroc(pos, neg):
    if not pos or not neg: return None
    g = gl = 0
    for a in pos:
        for b in neg:
            if a > b: g += 1
            elif a == b: gl += 1
    return (g + 0.5 * gl) / (len(pos) * len(neg))

ks = keys()
zeilen = [json.loads(z) for z in open(sys.argv[1], encoding="utf-8") if z.strip()]
zeilen = [z for z in zeilen if z.get("ok")]
# Vorhersage haengt nur an der Frage -> je Frage EINMAL schaetzen, dann zuordnen.
fragen = sorted({z["frage"] for z in zeilen})
vor = {}
for f in fragen:
    try:
        vor[f] = frag(SYS_VOR, f"FRAGE: {f}", ks); time.sleep(0.4)
    except Exception as e:
        print(f"  ⚠️ Vorhersage fuer {f[:40]!r}: {type(e).__name__}", file=sys.stderr)
nach = {}
for i, z in enumerate(zeilen):
    try:
        nach[i] = frag(SYS_NACH, f"FRAGE: {z['frage']}\n\nANTWORT: {z['antwort']}", ks)
        time.sleep(0.4)
    except Exception as e:
        print(f"  ⚠️ Nachhersage Zeile {i}: {type(e).__name__}", file=sys.stderr)

nutz = [(i, z) for i, z in enumerate(zeilen) if z["frage"] in vor and i in nach]
sysS = lambda z: z.get("unbekannt_n") or 0
print(f"\nbewertete Zuege: {len(nutz)} von {len(zeilen)}")
for name, score in (("System  (epistemik, VOR dem Zug)", lambda i, z: sysS(z)),
                    ("Beobachter FAIR (nur Frage, VOR)", lambda i, z: 1 - vor[z["frage"]]),
                    ("Beobachter unfair (sieht Antwort)", lambda i, z: 1 - nach[i])):
    pos = [score(i, z) for i, z in nutz if not z["treffer"]]
    neg = [score(i, z) for i, z in nutz if z["treffer"]]
    a = auroc(pos, neg)
    print(f"  Typ-2-AUROC {name:<34}: {'—' if a is None else f'{a:.3f}'}   n={len(pos)}/{len(neg)}")
