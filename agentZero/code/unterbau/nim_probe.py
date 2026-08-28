#!/usr/bin/env python3
"""nim_probe.py — kleiner Nachweis, dass die NVIDIA-NIM-Bahn steht.

Macht genau zwei Aufrufe und druckt die gemessenen Zahlen:
  1. ein Embedding-Aufruf  (integrate.api.nvidia.com/v1/embeddings)
  2. ein Rerank-Aufruf     (ai.api.nvidia.com/v1/retrieval/nvidia/reranking)

Bewusst NICHT verdrahtet: kein Import in bahn.py, keine Wiki-Datenbank,
kein Schreiben. Reines Messwerkzeug.

Aufruf:  python3 /opt/clayverse/werkzeug/nim_probe.py
"""
import json
import math
import os
import time
import urllib.error
import urllib.request

ZUGAENGE = '/etc/clayverse/freie-zugaenge.env'
EMB_URL = 'https://integrate.api.nvidia.com/v1/embeddings'
RER_URL = 'https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking'

# Gemessen am 2026-08-15 als erreichbar (siehe Bestandsaufnahme):
EMB_MODELL = 'nvidia/llama-nemotron-embed-1b-v2'   # 2048 Dim, 8192 Token
RER_MODELL = 'nvidia/rerank-qa-mistral-4b'         # max 512 Stellen

# Manche Kanten blocken den Standard-User-Agent von urllib.
UA = 'Mozilla/5.0 (X11; Linux x86_64) clayverse-nim-probe/1.0'


def schluessel(name='NVIDIA_NIM_API_KEY'):
    """Liest den Schluessel aus der Zugangsdatei. Gibt ihn NIE aus."""
    wert = os.environ.get(name)
    if wert:
        return wert.strip()
    try:
        with open(ZUGAENGE, encoding='utf-8') as f:
            for zeile in f:
                zeile = zeile.strip()
                if zeile.startswith(name + '='):
                    return zeile.split('=', 1)[1].strip().strip('"').strip("'")
    except OSError as e:
        raise SystemExit(f'Zugangsdatei nicht lesbar: {e}')
    raise SystemExit(f'{name} steht nicht in {ZUGAENGE}')


def ruf(url, nutzlast, key, zeitgrenze=120):
    """Ein POST. Liefert (ok, ms, code, objekt_oder_fehlertext)."""
    daten = json.dumps(nutzlast).encode('utf-8')
    anfrage = urllib.request.Request(url, data=daten, method='POST')
    anfrage.add_header('Authorization', 'Bearer ' + key)
    anfrage.add_header('Content-Type', 'application/json')
    anfrage.add_header('Accept', 'application/json')
    anfrage.add_header('User-Agent', UA)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(anfrage, timeout=zeitgrenze) as antwort:
            roh = antwort.read()
            ms = (time.perf_counter() - t0) * 1000.0
            return True, ms, antwort.status, json.loads(roh)
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000.0
        return False, ms, e.code, e.read().decode('utf-8', 'replace')[:400]
    except Exception as e:                      # Netz, DNS, Zeitgrenze
        ms = (time.perf_counter() - t0) * 1000.0
        return False, ms, 0, repr(e)[:300]


def kosinus(a, b):
    punkt = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return punkt / (na * nb) if na and nb else 0.0


# --------------------------------------------------------------- Embedding
def probe_embedding(key):
    texte = [
        'Der Grubenbrand ist ein Brennverfahren ganz ohne elektrischen Ofen.',
        'Beim Raku wird die Ware glueheend aus dem Feuer genommen.',
        'Fahrraeder kann man beim Verein LeihMich ausborgen.',
    ]
    ok, ms, code, erg = ruf(EMB_URL, {
        'model': EMB_MODELL,
        'input': texte,
        'input_type': 'passage',
        'encoding_format': 'float',
    }, key)

    print('--- Embedding ---')
    print(f'  Modell     : {EMB_MODELL}')
    print(f'  Endpunkt   : {EMB_URL}')
    if not ok:
        print(f'  FEHLER     : HTTP {code} {erg}')
        return False

    vektoren = [e['embedding'] for e in sorted(erg['data'],
                                               key=lambda e: e['index'])]
    print(f'  HTTP       : {code}')
    print(f'  Latenz     : {ms:.0f} ms fuer {len(texte)} Texte '
          f'({ms / len(texte):.1f} ms/Text)')
    print(f'  Dimension  : {len(vektoren[0])}')
    print(f'  Verbrauch  : {erg.get("usage", {})}')
    print(f'  cos(Brand, Raku)     = {kosinus(vektoren[0], vektoren[1]):.4f}')
    print(f'  cos(Brand, Fahrrad)  = {kosinus(vektoren[0], vektoren[2]):.4f}')
    return True


# ---------------------------------------------------------------- Reranker
def probe_rerank(key):
    frage = 'Wie brennt man Ton ohne elektrischen Ofen?'
    stellen = [
        'Der elektrische Toepferofen erreicht 1200 Grad in acht Stunden.',
        'Die Gemeinde Feldkirchen bei Graz hat rund 6000 Einwohner.',
        'Ein Tonnenofen aus einem Oelfass brennt mit Holz auf 900 Grad.',
        'Schamotte macht den Ton temperaturwechselbestaendig.',
        'Ohne Strom laesst sich Ton auch im Lagerfeuer schruppbrennen.',
    ]
    ok, ms, code, erg = ruf(RER_URL, {
        'model': RER_MODELL,
        'query': {'text': frage},
        'passages': [{'text': t} for t in stellen],
        'truncate': 'END',
    }, key)

    print()
    print('--- Reranker ---')
    print(f'  Modell     : {RER_MODELL}')
    print(f'  Endpunkt   : {RER_URL}')
    if not ok:
        print(f'  FEHLER     : HTTP {code} {erg}')
        return False

    print(f'  HTTP       : {code}')
    print(f'  Latenz     : {ms:.0f} ms fuer {len(stellen)} Stellen '
          f'({ms / len(stellen):.1f} ms/Stelle)')
    print(f'  Frage      : {frage}')
    print('  Rangliste  :')
    for platz, eintrag in enumerate(erg.get('rankings', []), 1):
        i = eintrag['index']
        print(f'    {platz}. logit={eintrag["logit"]:8.3f}  {stellen[i][:64]}')
    return True


def main():
    key = schluessel()
    a = probe_embedding(key)
    b = probe_rerank(key)
    print()
    print(f'Ergebnis: Embedding={"OK" if a else "FEHLER"}  '
          f'Rerank={"OK" if b else "FEHLER"}')
    return 0 if (a and b) else 1


if __name__ == '__main__':
    raise SystemExit(main())
