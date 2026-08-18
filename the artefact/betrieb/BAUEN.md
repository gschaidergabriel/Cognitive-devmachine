# Container bauen -- und die eine Zeile, die den Dienst umlegt

## So geht es

    cd "/opt/entityos/the artefact"
    docker compose --env-file /etc/clayverse/entityos-deploy.env up -d --build

## ⛔ So NICHT

    set -a; . /etc/clayverse/entityos-deploy.env; . /etc/clayverse/entityos-clerk.env; set +a
    docker compose up -d --build

Diese Fassung steht im Auftragsdokument und hat am 18.08. den Dienst lahmgelegt.
Zwei getrennte Gruende, beide still:

**1. Die Anfuehrungszeichen verschwinden.** `CLAYVERSE_CLERK_MAP_JSON` enthaelt
JSON. Beim Einlesen mit `.` interpretiert bash die Zeile und entfernt dabei die
doppelten Anfuehrungszeichen. Im Container kam an:

    {user_3C1pnXkHAaStEcoPgYln5QC7O3V:gabriel,...}

statt

    {"user_3C1pnXkHAaStEcoPgYln5QC7O3V":"gabriel",...}

Ergebnis: `RuntimeError: CLAYVERSE_CLERK_MAP_JSON is invalid JSON`, Container in
einer Neustartschleife, alle Seiten tot. `--env-file` reicht den Wert
unveraendert durch und hat dieses Problem nicht.

**2. Die zweite Datei ueberschreibt die erste.** `entityos-clerk.env` enthaelt
EBENFALLS ein `CLAYVERSE_CLERK_MAP_JSON` -- mit einer ANDEREN Clerk-Kennung fuer
Andreas:

    entityos-deploy.env   ...,"user_3C5R4TCSv9yow0b8GhBlQTRlHFm":"andreas"}   <- live, funktioniert
    entityos-clerk.env    ...,"user_3C6kpF9WdVfp5uL1NbUD3uDVsf7":"andreas"}   <- veraltet

Wer clerk.env zuletzt einliest, faehrt mit der veralteten Kennung. Andreas kann
sich dann anmelden und bekommt "unmapped Clerk subject" -- oder schlimmer, er
bekommt es NICHT und arbeitet unter einer Kennung, die nirgends sonst gilt.

⚠️ Die veraltete Datei wurde NICHT geloescht: sie ist Konfiguration, und ob sie
anderswo gelesen wird, ist ungeprueft. Das gehoert aufgeraeumt, aber bewusst und
nicht nebenbei beim Debuggen.

## Warum das hier steht und nicht nur im Kopf

Beide Fehler sind still. Der erste wirft zwar eine Ausnahme -- aber erst im
Container, nach dem Bau, im Log; der Bau selbst meldet Erfolg. Der zweite wirft
gar nichts und aendert nur, wer Andreas ist.
