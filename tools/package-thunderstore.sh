#!/usr/bin/env bash
# Build the Thunderstore package: dist/ValheimArchipelagoRandomizer-<version>.zip
# Run from anywhere: bash tools/package-thunderstore.sh
# Build the DLL first: dotnet build ValheimRandomizer.csproj -c Release
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

PY=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sys" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "ERROR: Python was not found. Install Python 3 and try again." >&2
  exit 1
fi

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

VERSION="$("$PY" -c "import json; print(json.load(open('dist/manifest.json', encoding='utf-8'))['version_number'])")"
[ -n "$VERSION" ] || fail "Could not read version_number from dist/manifest.json"
echo "Packaging version $VERSION"

SOURCE_VERSION="$(grep -o 'ModVersion = "[^"]*"' src/ValehimRandomizer.cs | head -n 1 | cut -d '"' -f 2)"
[ "$SOURCE_VERSION" = "$VERSION" ] || fail "manifest is $VERSION but ModVersion in src/ValehimRandomizer.cs is '$SOURCE_VERSION'"

grep -q "^## $VERSION" dist/CHANGELOG.md || fail "dist/CHANGELOG.md has no '## $VERSION' section"

FILES="dist/manifest.json dist/README.md dist/CHANGELOG.md dist/icon.png bin/Release/ValheimRandomizer.dll lib/Archipelago.MultiClient.Net.dll tools/research.tsv tools/trophies.tsv tools/drops.tsv"
for f in $FILES; do
  [ -f "$f" ] || fail "Missing $f (build the DLL first if it is bin/Release/ValheimRandomizer.dll)"
done

if [ "${SKIP_STALE_CHECK:-0}" != "1" ] && [ -n "$(find src -name '*.cs' -newer bin/Release/ValheimRandomizer.dll 2>/dev/null)" ]; then
  fail "Sources are newer than bin/Release/ValheimRandomizer.dll. Rebuild the DLL first (or set SKIP_STALE_CHECK=1)."
fi

STAGE="dist/_stage"
ZIP_NAME="ValheimArchipelagoRandomizer-$VERSION.zip"
ZIP_PATH="dist/$ZIP_NAME"

rm -rf "$STAGE"
mkdir -p "$STAGE"
for f in $FILES; do
  cp "$f" "$STAGE/"
done

rm -f "$ZIP_PATH"
(cd "$STAGE" && "$PY" -m zipfile -c "../$ZIP_NAME" manifest.json README.md CHANGELOG.md icon.png ValheimRandomizer.dll Archipelago.MultiClient.Net.dll research.tsv trophies.tsv drops.tsv)
rm -rf "$STAGE"

LISTING="$("$PY" -m zipfile -l "$ZIP_PATH")"
COUNT="$(printf '%s\n' "$LISTING" | tail -n +2 | grep -c .)"
[ "$COUNT" = "9" ] || fail "Expected 9 files in the zip, found $COUNT"
if printf '%s\n' "$LISTING" | grep -qi "Newtonsoft"; then
  fail "The zip must not contain Newtonsoft.Json.dll"
fi

printf '%s\n' "$LISTING"
echo "Wrote $ZIP_PATH"
