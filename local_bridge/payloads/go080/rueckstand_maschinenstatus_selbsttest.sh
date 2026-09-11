#!/usr/bin/env bash
# Regression fuer GO080: ein vom Laeufer erkannter RUECKSTAND darf nicht rc=0 sein.
set -u
LC_ALL=C
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGINAL="$HIER/selbsttests.sh"

fehler=0
ok()  { printf '  ok      %s\n' "$1"; }
nok() { printf '  FEHLER  %s\n' "$1"; fehler=$((fehler+1)); }

scratch="$(mktemp -d -t rueckstand-status-XXXXXXXX)" || exit 1
trap 'rm -rf -- "$scratch"' EXIT

welt="$scratch/welt"
basis="$scratch/basis"
mkdir -p "$welt" "$basis"
cp "$ORIGINAL" "$welt/selbsttests.sh"

cat > "$welt/aaa_selbsttest.sh" <<'EOF'
#!/usr/bin/env bash
echo sauber
exit 0
EOF
cat > "$welt/zzz_selbsttest.sh" <<'EOF'
#!/usr/bin/env bash
echo "erzeuge rueckstand"
echo beleg > "$TMPDIR/rueckstand-go080.txt"
exit 0
EOF
chmod +x "$welt"/*_selbsttest.sh

out="$scratch/out.txt"
set +e
TMPDIR="$basis" SELBSTTESTS_BEDARF_MIB=1 bash "$welt/selbsttests.sh" >"$out" 2>&1
rc=$?
set -e

if grep -q '^RUECKSTAND:' "$out"; then
  ok "R1 RUECKSTAND wird erkannt"
else
  nok "R1 RUECKSTAND fehlt"
fi

if [ "$rc" -eq 5 ]; then
  ok "R2 erkannter RUECKSTAND -> rc=5 (nicht gruen)"
else
  nok "R2 erkannter RUECKSTAND -> rc=$rc (erwartet 5)"
fi

if grep -qP '^#SATZ\t2/2$' "$out"; then
  ok "R3 Kindtests bleiben ehrlich 2/2; der Runnerstatus traegt den Cleanup-Befund"
else
  nok "R3 Kindtest-Zaehler wurde verfaelscht: $(grep '^#SATZ' "$out" | tr '\t' ' ')"
fi

# Gegenprobe: ohne liegengebliebene Datei muss exakt derselbe Runner gruen bleiben.
rm -rf -- "$welt" "$basis"
mkdir -p "$welt" "$basis"
cp "$ORIGINAL" "$welt/selbsttests.sh"
cat > "$welt/aaa_selbsttest.sh" <<'EOF'
#!/usr/bin/env bash
echo sauber
exit 0
EOF
chmod +x "$welt/aaa_selbsttest.sh"
set +e
TMPDIR="$basis" SELBSTTESTS_BEDARF_MIB=1 bash "$welt/selbsttests.sh" >"$out" 2>&1
rc2=$?
set -e
if [ "$rc2" -eq 0 ] && ! grep -q '^RUECKSTAND:' "$out"; then
  ok "R4 sauberer Lauf bleibt rc=0 ohne RUECKSTAND"
else
  nok "R4 sauberer Lauf rc=$rc2 / unerwarteter RUECKSTAND"
fi

printf '\n'
if [ "$fehler" -eq 0 ]; then
  echo 'Alle Pruefungen bestanden.'
  exit 0
fi
echo "$fehler Fehler."
exit 1
