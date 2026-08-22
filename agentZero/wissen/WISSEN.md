# Wissensartikel

Automatisch erzeugt 2026-08-22T04:06:42Z. 12 Artikel -- Betriebswissen (wie deployt wird, Domains, Testpflicht) und Personenwissen (Rollen, wer entscheidet, wo Geheimnisse liegen) aus der gitignorierten Eigner-CLAUDE.md, geheimnisfrei uebertragen durch `clayverse/wissen.py`.

> ⚠️ 8 Zeile(n) ohne `geheimnisfrei=true` -- zurueckgehalten, nicht exportiert.

## Andreas: Rolle und Zustaendigkeit

`wissen-mensch-andreas-rolle` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Dr. Andreas Unterweger, Dipl.-Ing. Dr.nat.techn. Gruender, Obmann und Senior Researcher des Instituts fuer Agentic Research (IAR), ehrenamtlich, Graz. SeiMensch.net ist SEIN Projekt, ebenso das Naturareal. Den Code dazu hat Gabriel geschrieben -- Zugehoerigkeit und Urheberschaft sind hier getrennt und duerfen nicht vermengt werden. Sein Rechner ist <GESCHWAERZT: Rechnername>.

## Gabriels Arbeitsweise: kurz fragen statt lang erklaeren

`wissen-mensch-arbeitsweise-gabriel` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Dauerhafte Anweisung: Antworten kurz und praegnant. Frage statt Lage, Optionen anbieten statt offen fragen, und immer sagen, dass es mehr gibt und wo. ⭐ Der Grund ist kein Hoeflichkeitswunsch, sondern ein Pruefmechanismus: eine kurze Frage ist billig zu pruefen, ein langer kohaerenter Text ist es nicht. Ein ueberforderter Empfaenger hoert nicht auf zu lesen, sondern auf zu PRUEFEN. Zu wenig ist reparierbar, zu viel ist irreversibel. Ausnahme: Architektur, Systemlogik und Grundsatzfragen gesammelt vorlegen, nicht troepfeln -- er entscheidet, er soll nicht recherchieren muessen.

## Wer entscheidet was

`wissen-mensch-entscheidungsrecht` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Gabriel entscheidet fuer beide -- Andreas' Zustimmung liegt dauerhaft vor und ist nie als offener Punkt zu fuehren, sondern nur zu informieren. Betriebliche Freigaben (Schluessel, Dienst, Loeschen) duerfen einzeln und sofort kommen; das sind keine Entwurfsfragen.

## Gabriel: Rolle und Zustaendigkeit

`wissen-mensch-gabriel-rolle` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Gabriel Gschaider, Co-Gruender, Vizeobmann und Lead Researcher des IAR, ehrenamtlich. Schreibt den Code -- auch fuer Projekte, die Andreas gehoeren. Eigentuemer des GitHub-Kontos gschaidergabriel. Sein Rechner ist <GESCHWAERZT: Rechnername>, Project Frankenstein ist sein Projekt.

## Wo die Geheimnisse liegen -- und warum nicht hier

`wissen-mensch-geheimnisse` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Passwoerter, Registrar-Logins, Kundennummern und API-Schluessel stehen NICHT im Wiki. Sie liegen in zwei Tresoren: `zugaenge` (Anmeldungen) und `api` (Maschinenschluessel mit Faehigkeitsliste). Zero sieht davon nur den KATALOG -- was es gibt und was es kann, nie den Wert. Ein Geheimnis, das durch ein Sprachmodell laeuft, ist keines mehr. Wer einen Wert braucht, ist ein Serverteil und holt ihn direkt.

## SeiMensch.net: wie deployt wird

`wissen-seimensch-deploy` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Das zentrale Repo auf dem VPS ist die einzige Wahrheit. Gearbeitet wird ueber Git, nicht ueber manuelles Kopieren. Ablauf: git pull, Dateien aendern, commit, git push origin main -- ein Server-Hook macht daraus Voll-Backup, Integritaetscheck, Spiegelung auf die Live-Site und chown. Es gibt KEINEN manuellen Deploy-Schritt. Ein Push auf main ist damit sofort oeffentlich; halbfertiges gehoert auf einen Branch, denn nur main deployt.

## SeiMensch: drei Domains, eigene Wurzeln

`wissen-seimensch-domains` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

seimensch.net, leihmich.org und herzrad.at zeigen alle auf dieselbe Produktion. ABER: herzrad.at und leihmich.org haben EIGENE nginx-Wurzeln (site/herzrad bzw. site/leihmich). Diese Ordner sind gleichzeitig Unterordner von seimensch.net UND Domainwurzel. Deshalb brauchen sie relative Asset-Pfade und eigene Kopien der Wurzeldateien -- ein absolutes /favicon.ico zeigt auf der eigenen Domain ins Leere.

## SeiMensch: die Grundregel des Kunden

`wissen-seimensch-grundregel` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

NICHTS ERFINDEN. Keine ausgedachten Preise, Spezifikationen oder Merkmale. Bei Unsicherheit recherchieren oder weglassen. Das ist die aelteste und haerteste Regel dieses Projekts.

## LeihMich: Daten liegen inline, Slugs brauchen Freigabe

`wissen-seimensch-leihmich` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Die Artikeldaten stehen inline in leihmich/index.html (ITEMS-Array, CC-Map, CATS). ⚠️ Ein neuer Item-Slug MUSS zusaetzlich in LEIHMICH_SLUGS im Umfrage-Dienst eingetragen werden, sonst antwortet die Klickzaehlung mit 400. Bau-Lehre: nie json.dumps(CATS) global ersetzen -- das zieht Kommas in Kategorienamen zusammen und zerlegt die Filter. Index-Slicing nutzen und die JS-Datenbloecke vor dem Commit syntaktisch pruefen.

## SeiMensch: wo alles liegt

`wissen-seimensch-pfade` · EntityOS/entityos · 2026-08-18T14:36:11+0000

**Wieso:** Zero fand den Deploy-Weg, aber keinen Pfad -- der Wissensartikel beantwortete die Frage nicht, fuer die er geschrieben wurde

**Gehoert zu:** EntityOS / SeiMensch

Arbeitskopie auf den Arbeitsrechnern: ~/seimensch-redesign -- ein Git-Klon des zentralen Repos, gemeinsame Arbeitskopie beider Menschen. Live-Wurzel auf dem VPS: /var/lib/agentforge/projects/12/seimensch/site/ -- vom Deploy-Hook befuellt und NICHT direkt zu editieren; eine Aenderung dort wird beim naechsten Push ueberschrieben. Darunter die eigenen Domainwurzeln: site/herzrad fuer herzrad.at, site/leihmich fuer leihmich.org. nginx-Konfiguration fuer seimensch.net: /etc/nginx/conf.d/seimensch-net.conf, statisch von der Platte, kein Neustart noetig. Deploy-Protokoll: /var/log/seimensch-deploy.log. Sicherungen vor jedem Deploy: /root/seimensch-backups/site-predeploy-*.tgz, die letzten 15. Rueckbau sauber ueber git revert und einen erneuten Push -- der Hook deployt dann den vorherigen Stand. ⚠️ Die ZUGANGSROUTE zum Repo (Benutzer und Adresse) steht NICHT hier, sondern im Tresor `zugaenge` unter SEIMENSCH_REPO_REMOTE. Wer den Pfad kennt, kann noch nichts; wer die Route kennt, kommt hin.

## SeiMensch: Pflicht vor jedem Push auf main

`wissen-seimensch-testpflicht` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Im echten Browser verifizieren, Desktop UND Mobil: 0 Konsolenfehler, 0 kaputte Bilder, 0 waagerechter Ueberlauf. Grund: main geht sofort oeffentlich, es gibt keine Zwischenstufe. ⚠️ Danach den Browser-Daemon stoppen -- sonst dreht das 360-Grad-Panorama der Startseite endlos WebGL in Software und faehrt die CPU auf Vollast.

## SeiMensch: was der Verein ist

`wissen-seimensch-verein` · EntityOS/entityos · 2026-08-18T14:08:40+0000

**Wieso:** Betriebs- und Personenwissen war nur in einer gitignorierten Datei auf einem Arbeitsrechner -- vermischt mit Geheimnissen, deshalb nirgends teilbar

**Gehoert zu:** EntityOS / SeiMensch

Gemeinnuetziger Verein in Feldkirchen bei Graz. Unterseiten: /leihmich/ (Verleih), /projekte/, /harte-baesse/, /herzrad/, /workshop/, /unterstuetzer/. Altlast: /resilienz/ existiert noch als aeltere Seite, ist von nirgendwo verlinkt und hat keine kanonische URL -- nicht mit /workshop/ verwechseln.

