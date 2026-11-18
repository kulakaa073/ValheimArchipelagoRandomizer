"""Package valheimapworld/ into valheimapworld.apworld with a valid AP manifest.

Source archipelago.json must not include container version fields; this script
adds compatible_version/version required by Archipelago 0.6.8+ loaders.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "valheimapworld"
OUT = WORLD / "valheimapworld.apworld"

# APWorldContainer packaging scheme (worlds/Files.py container_version).
CONTAINER_VERSION = 7

SKIP_NAMES = {".apworld", ".pyc", "__pycache__"}


def iter_files():
    for path in WORLD.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".apworld" or path.name == "valheimapworld.apworld":
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        yield path


def main() -> None:
    source_manifest = json.loads((WORLD / "archipelago.json").read_text(encoding="utf-8"))
    if "version" in source_manifest or "compatible_version" in source_manifest:
        raise SystemExit("source archipelago.json must not define version/compatible_version")
    if source_manifest.get("game") != "Valheim":
        raise SystemExit("archipelago.json game must be Valheim")

    packaged = dict(source_manifest)
    packaged["compatible_version"] = CONTAINER_VERSION
    packaged["version"] = CONTAINER_VERSION

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("valheimapworld/archipelago.json", json.dumps(packaged, indent=2) + "\n")
        for path in sorted(iter_files()):
            rel = path.relative_to(WORLD).as_posix()
            if rel == "archipelago.json":
                continue  # already written with container fields
            zf.write(path, f"valheimapworld/{rel}")

    with zipfile.ZipFile(OUT, "r") as zf:
        names = zf.namelist()
        raw = json.loads(zf.read("valheimapworld/archipelago.json"))
    print(f"wrote {OUT} ({len(names)} files)")
    print("manifest", raw)


if __name__ == "__main__":
    main()
