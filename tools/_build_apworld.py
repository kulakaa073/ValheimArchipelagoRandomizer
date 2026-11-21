"""Package valheimapworld/ into valheimapworld.apworld with a valid AP manifest.

Source archipelago.json must not include container version fields; this script
adds compatible_version/version required by Archipelago 0.6.8+ loaders.

Python files are parsed before the archive is opened. A syntax error aborts
without creating or replacing the output archive.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "valheimapworld"
OUT = WORLD / "valheimapworld.apworld"

# APWorldContainer packaging scheme (worlds/Files.py container_version).
CONTAINER_VERSION = 7

REQUIRED_MEMBERS = (
    "archipelago.json",
    "__init__.py",
    "Items.py",
    "Locations.py",
    "Drops.py",
    "Regions.py",
    "Options.py",
    "Parents.py",
    "Ids.py",
    "id_registry.json",
)


def iter_files():
    for path in WORLD.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".apworld" or path.name == "valheimapworld.apworld":
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        yield path


def parse_python(path: Path, source: str | None = None) -> None:
    text = path.read_text(encoding="utf-8") if source is None else source
    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        line = exc.lineno if exc.lineno is not None else "?"
        raise SystemExit(f"Python syntax error: {path}:{line}: {exc.msg}") from exc


def validate_python_sources(paths) -> None:
    for path in paths:
        if path.suffix != ".py":
            continue
        parse_python(path)


def validate_source_manifest(source_manifest: dict) -> None:
    if "version" in source_manifest or "compatible_version" in source_manifest:
        raise SystemExit("source archipelago.json must not define version/compatible_version")
    if source_manifest.get("game") != "Valheim":
        raise SystemExit("archipelago.json game must be Valheim")
    if not source_manifest.get("world_version"):
        raise SystemExit("archipelago.json is missing world_version")


def _ensure_world_imports() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        import BaseClasses  # noqa: F401
    except ImportError:
        fake = ROOT / "tests" / "ap_fakes.py"
        if not fake.is_file():
            raise SystemExit(
                "Archipelago BaseClasses is not importable and tests/ap_fakes.py is missing. "
                "Install Archipelago or keep the test fakes so id validation can import the world."
            )
        import importlib.util

        spec = importlib.util.spec_from_file_location("ap_fakes", fake)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.install()


def validate_stable_ids() -> None:
    _ensure_world_imports()
    from valheimapworld.Ids import assert_unique_spaces, registry

    assert_unique_spaces()
    data = registry()
    baseline_path = ROOT / "tests" / "fixtures" / "id_baseline.json"
    if not baseline_path.is_file():
        raise SystemExit(f"missing id baseline: {baseline_path}")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    for section, saved in baseline.items():
        live = data.get(section)
        if not isinstance(live, dict):
            raise SystemExit(f"id registry is missing section {section}")
        for name, raw in saved.items():
            if name not in live or int(live[name]) != int(raw):
                raise SystemExit(
                    f"stable id changed for {section} '{name}': "
                    f"baseline {raw}, registry {live.get(name)}"
                )
    # Importing the world modules checks that every data row resolves to the registry.
    import valheimapworld.Items as items
    import valheimapworld.Locations as locations
    import valheimapworld.Drops as drops
    import valheimapworld

    if items.item_table != data["research_items"]:
        raise SystemExit("research item ids do not match id_registry.json")
    if {name: int(value) for name, value in locations.location_table.items()} != {
        name: int(value) for name, value in data["research_locations"].items()
    }:
        raise SystemExit("research location ids do not match id_registry.json")
    if drops.drop_item_table != {name: int(value) for name, value in data["drop_items"].items()}:
        raise SystemExit("gather item ids do not match id_registry.json")
    if drops.drop_location_table != {name: int(value) for name, value in data["drop_locations"].items()}:
        raise SystemExit("gather location ids do not match id_registry.json")
    if drops.boss_item_table != {name: int(value) for name, value in data["boss_items"].items()}:
        raise SystemExit("boss item ids do not match id_registry.json")
    goal_ids = {goal.location: goal.location_id for goal in valheimapworld.GOALS}
    if goal_ids != {name: int(value) for name, value in data["goal_locations"].items()}:
        raise SystemExit("goal location ids do not match id_registry.json")


def validate_archive(zf: zipfile.ZipFile, source_paths) -> None:
    names = set(zf.namelist())
    for member in REQUIRED_MEMBERS:
        archived = f"valheimapworld/{member}"
        if archived not in names:
            raise SystemExit(f"archive is missing {archived}")
    raw = json.loads(zf.read("valheimapworld/archipelago.json"))
    if raw.get("game") != "Valheim":
        raise SystemExit("packaged manifest game must be Valheim")
    if raw.get("version") != CONTAINER_VERSION or raw.get("compatible_version") != CONTAINER_VERSION:
        raise SystemExit("packaged manifest is missing container version fields")
    for path in source_paths:
        rel = path.relative_to(WORLD).as_posix()
        if rel == "archipelago.json":
            continue
        archived = f"valheimapworld/{rel}"
        if archived not in names:
            raise SystemExit(f"archive is missing {archived}")
        payload = zf.read(archived)
        if path.suffix == ".py":
            parse_python(path, payload.decode("utf-8"))
        if payload != path.read_bytes():
            raise SystemExit(f"archive member {archived} does not match {path}")


_IMPORT_CHECK = """
import os, sys
root, archive = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
try:
    import BaseClasses
except ImportError:
    from tests.ap_fakes import install
    install()
sys.path.remove(root)
sys.path.insert(0, archive)
import valheimapworld
from valheimapworld.Ids import registry
home = os.path.normcase(os.path.abspath(str(valheimapworld.__file__)))
if os.path.normcase(os.path.abspath(archive)) not in home:
    raise SystemExit("imported the source folder, not the archive: " + home)
if not registry():
    raise SystemExit("id registry is empty")
"""


def validate_zip_import(archive: Path) -> None:
    """Import the world straight from the zip, the way Archipelago loads an .apworld."""
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_CHECK, str(ROOT), str(archive)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SystemExit(f"world does not import from inside the archive:\n{detail}")


def main() -> None:
    source_paths = sorted(iter_files())
    # Validate before opening the destination so a bad tree cannot replace a good archive.
    validate_python_sources(source_paths)
    source_manifest = json.loads((WORLD / "archipelago.json").read_text(encoding="utf-8"))
    validate_source_manifest(source_manifest)
    validate_stable_ids()

    packaged = dict(source_manifest)
    packaged["compatible_version"] = CONTAINER_VERSION
    packaged["version"] = CONTAINER_VERSION

    temporary = OUT.with_suffix(".apworld.tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("valheimapworld/archipelago.json", json.dumps(packaged, indent=2) + "\n")
            for path in source_paths:
                rel = path.relative_to(WORLD).as_posix()
                if rel == "archipelago.json":
                    continue
                zf.write(path, f"valheimapworld/{rel}")
        with zipfile.ZipFile(temporary, "r") as zf:
            names = zf.namelist()
            validate_archive(zf, source_paths)
            raw = json.loads(zf.read("valheimapworld/archipelago.json"))
        validate_zip_import(temporary)
        temporary.replace(OUT)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    print(f"wrote {OUT} ({len(names)} files)")
    print("manifest", raw)


if __name__ == "__main__":
    main()
 