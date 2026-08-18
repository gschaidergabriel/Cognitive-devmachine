# Menschen hinter Zero

Automatisch erzeugt 2026-08-18T09:48:58Z. Dieses Repo ist OEFFENTLICH -- deshalb gilt hier eine engere Freigabe als die sonstige Schwaerzung (die faengt nur Zugangsdaten). Nur Felder mit `herkunft=iar.frank.ink` (schon oeffentlich auf der Institutsseite) oder einzeln gepruefte, klar unpersoenliche Eigner-Felder stehen unten. Alles andere steht als zurueckgehalten da, nicht stillschweigend weggelassen.

## Herkunftsregeln

| Kuerzel | Bedeutung | frei? |
|---|---|---|
| `eigner` | vom Eigner selbst bestaetigt -- kann Privates enthalten | nur nach Einzelpruefung |
| `iar.frank.ink` | steht schon oeffentlich auf der Institutsseite | ja |
| `abgeleitet` | aus anderen Feldern hergeleitet | nur nach Einzelpruefung |
| `gemessen` | aus dem laufenden System gemessen (z.B. Zugriffszahlen, Rechnername) | nur nach Einzelpruefung |

## Freigegeben

### andreas

| Feld | Wert | Herkunft | Beleg |
|---|---|---|---|
| name | Dr. Andreas Unterweger | iar.frank.ink | Teamseite |
| ort | Graz, Austria | iar.frank.ink | Teamseite |
| rolle_institut | Founder, Obmann (Chair), Senior Researcher | iar.frank.ink | Teamseite |
| taetigkeit | ehrenamtlich | iar.frank.ink | Zwei Gruender. Beide ehrenamtlich. |
| titel | Dipl.-Ing. Dr.nat.techn. | iar.frank.ink | Teamseite |

### gabriel

| Feld | Wert | Herkunft | Beleg |
|---|---|---|---|
| github | Eigentuemer des GitHub-Kontos gschaidergabriel | eigner | Eigner 18.08. |
| name | Gabriel Gschaider | iar.frank.ink | Teamseite |
| ort | Knittelfeld -> Graz -> Siem Reap | iar.frank.ink | Teamseite |
| rolle_institut | Co-founder, Vizeobmann (Deputy Chair), Lead Researcher | iar.frank.ink | Teamseite |
| rolle_technisch | schreibt den Code | eigner | Eigner 18.08.: 'seimensch ist das projekt von andreas aber allen code habe ich gemacht' |
| taetigkeit | ehrenamtlich | iar.frank.ink | Zwei Gruender. Beide ehrenamtlich. |

### gemeinsam

| Feld | Wert | Herkunft | Beleg |
|---|---|---|---|
| herkunft_zero | Zero ist aus diesem Institut hervorgegangen. | eigner | Eigner 18.08. |
| institut | Institut fuer Agentic Research (IAR), ZVR 1741094409, Feldkirchen bei Graz. Unabhaengiger gemeinnuetziger Forschungsverein. Zwei Gruender, beide ehrenamtlich. | iar.frank.ink | Fusszeile und Teamseite |

## Zurueckgehalten

12 Feld(er) -- nur DASS es sie gibt, NICHT der Wert:

| Mensch | Feld | Herkunft | Grund |
|---|---|---|---|
| andreas | gemessen_gedaechtniseintraege | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| andreas | gemessen_gespraeche | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| andreas | gemessen_rechner | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| andreas | gemessen_schwerpunkte | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| andreas | gemessen_wiki_bestand | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| andreas | mail | eigner | herkunft=eigner, keine gepruefte Ausnahme -- koennte privat sein |
| gabriel | gemessen_gedaechtniseintraege | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| gabriel | gemessen_gespraeche | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| gabriel | gemessen_rechner | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| gabriel | gemessen_schwerpunkte | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| gabriel | gemessen_wiki_bestand | gemessen | herkunft=gemessen, nicht in ERLAUBTE_HERKUNFT -- noch nicht einzeln geprueft, konservativ zurueckgehalten |
| gabriel | mail | eigner | herkunft=eigner, keine gepruefte Ausnahme -- koennte privat sein |

## Eigentum vs. Urheberschaft

`entityos_projekte` fuehrt `gehoert` (wem das Projekt gehoert) und `gebaut_von` (wer es gebaut hat) als GETRENNTE Spalten -- ein Projekt kann dem einen gehoeren und vom anderen gebaut sein (Beispiel: SeiMensch.net gehoert Andreas, Code von Gabriel). Siehe `PROJEKTE.md`.

