#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "usage: $0 /path/to/EntityOS <sha256>" >&2
  exit 64
fi

src=$1
expected=$(printf '%s' "$2" | tr 'A-F' 'a-f')
case "$expected" in
  *[!0-9a-f]*|'') echo "invalid EntityOS sha256" >&2; exit 64 ;;
esac
[ "${#expected}" -eq 64 ] || { echo "invalid EntityOS sha256 length" >&2; exit 64; }
[ -f "$src" ] || { echo "EntityOS source is not a regular file" >&2; exit 66; }
[ ! -L "$src" ] || { echo "EntityOS source symlink rejected" >&2; exit 66; }

actual=$(sha256sum "$src" | awk '{print $1}')
[ "$actual" = "$expected" ] || {
  echo "EntityOS source digest mismatch: expected=$expected actual=$actual" >&2
  exit 65
}

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
stage_dir="$root/build-assets/entityos"
mkdir -p "$stage_dir"
tmp="$stage_dir/.EntityOS.stage.$$"
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cp -- "$src" "$tmp"
chmod 0555 "$tmp"
postcopy=$(sha256sum "$tmp" | awk '{print $1}')
[ "$postcopy" = "$expected" ] || {
  echo "EntityOS staged digest mismatch: expected=$expected actual=$postcopy" >&2
  exit 65
}
mv -f -- "$tmp" "$stage_dir/EntityOS"
trap - EXIT HUP INT TERM
printf 'staged EntityOS sha256=%s\n' "$expected"
