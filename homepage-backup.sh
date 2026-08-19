#!/bin/bash
# Homepage-Backup: alle Live-Homepages von frank-api -> SeiMensch-VPS (72.61.19.188).
#
# Gabriel 19.08.: "alle homepages sollen immer auf den 2. vps gebackupt liegen."
# Alle Sites werden auf frank-api serviert; der SeiMensch-VPS (srv1563149,
# 162 GB frei) ist das Backup-Ziel.
#
# ⭐ BEWUSST ZERSTOERUNGSFREI: nur rsync + `ln -sfn`, KEIN rm, KEIN --delete auf
# dem Ziel. Datierte Schnappschuesse per --link-dest (unveraenderte Dateien
# werden hart verlinkt -> ein Schnappschuss kostet nur den Zuwachs). `latest`
# zeigt via `ln -sfn` (atomar, ohne rm) auf den neuesten. Alte Schnappschuesse
# werden NICHT automatisch geloescht -- Loeschen ist eine Freigabe-Sache
# (Gabriels Schranke). Bei den kleinen Homepages + Hardlinks passt das lange.
set -euo pipefail

TARGET="root@72.61.19.188"
DEST="/srv/homepage-backups"
STAMP="$(date +%Y-%m-%d_%H%M)"
LOG="/var/log/homepage-backup.log"
SSH="ssh -o BatchMode=yes -o ConnectTimeout=10"

# name -> Quellpfad auf frank-api (Trailing-Slash = Inhalt spiegeln)
SITES=(
  "seimensch:/var/lib/agentforge/projects/12/seimensch/site/"
  "frank-ink:/var/www/frank-ink/"
)

log(){ echo "$(date +%Y-%m-%dT%H:%M:%S) $*" | tee -a "$LOG" ; }

$SSH "$TARGET" "mkdir -p $DEST"

fehler=0
for eintrag in "${SITES[@]}"; do
  name="${eintrag%%:*}"
  src="${eintrag#*:}"
  if [ ! -d "$src" ]; then
    log "UEBERSPRUNGEN $name: Quelle fehlt ($src)"
    continue
  fi
  $SSH "$TARGET" "mkdir -p $DEST/$name"
  # --link-dest ist relativ zum Zielverzeichnis auf dem Remote: ../latest.
  # KEIN --delete: nichts auf dem Ziel wird geloescht.
  if rsync -az --link-dest="../latest" -e "$SSH" "$src" "$TARGET:$DEST/$name/$STAMP/"; then
    # latest atomar umhaengen -- `ln -sfn` ersetzt den Symlink OHNE rm.
    $SSH "$TARGET" "ln -sfn '$STAMP' $DEST/$name/latest"
    groesse=$($SSH "$TARGET" "du -sh $DEST/$name/$STAMP 2>/dev/null | cut -f1")
    log "OK $name -> $DEST/$name/$STAMP ($groesse)"
  else
    log "FEHLER $name: rsync fehlgeschlagen"
    fehler=1
  fi
done

exit $fehler
