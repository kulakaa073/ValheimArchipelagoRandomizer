"""Stable Archipelago ids.

Numeric ids are looked up by name from id_registry.json. Row order is not an id.
Adding a name means adding a new unused id to the registry. Existing names keep
the ids they already shipped with.
"""
from __future__ import annotations

import json
import pkgutil
from pathlib import Path

REGISTRY_NAME = "id_registry.json"
REGISTRY_PATH = Path(__file__).with_name(REGISTRY_NAME)

ITEM_SECTIONS = ("research_items", "drop_items", "boss_items", "victory_item")
LOCATION_SECTIONS = ("research_locations", "drop_locations", "goal_locations")

_REGISTRY = None


def _read_registry_text() -> str:
    """Read the registry from a folder or from inside a zipped .apworld.

    Path.read_text() cannot open a file inside a zip, so go through the module
    loader first. The plain path is only a fallback for odd import setups.
    """
    package = __name__.rpartition(".")[0]
    if package:
        data = pkgutil.get_data(package, REGISTRY_NAME)
        if data is not None:
            return data.decode("utf-8")
    return REGISTRY_PATH.read_text(encoding="utf-8")


def registry() -> dict:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = json.loads(_read_registry_text())
    return _REGISTRY


def resolve_section(section: str, names: list) -> list:
    """Return one id per name, in the same order. Reject duplicate names and ids."""
    table = registry().get(section)
    if not isinstance(table, dict):
        raise RuntimeError(f"id_registry.json is missing the '{section}' object")

    seen_names = set()
    seen_ids = {}
    out = []
    for name in names:
        if name in seen_names:
            raise RuntimeError(f"Duplicate {section} name '{name}'")
        seen_names.add(name)
        if name not in table:
            raise RuntimeError(
                f"{section} '{name}' has no stable id. "
                "Add a new unused id to valheimapworld/id_registry.json. "
                "Do not renumber existing names."
            )
        try:
            value = int(table[name])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"{section} id for '{name}' is not an integer") from exc
        if value in seen_ids:
            raise RuntimeError(
                f"Duplicate {section} id {value} for '{name}' and '{seen_ids[value]}'"
            )
        seen_ids[value] = name
        out.append(value)

    unused = sorted(set(table) - seen_names)
    if unused:
        raise RuntimeError(
            f"{section} registry lists names that are not in the data: {unused[:8]}"
        )
    return out


def require_id(section: str, name: str, expected: int) -> None:
    """Fail if a hardcoded id drifted from the registry."""
    table = registry().get(section)
    if not isinstance(table, dict) or name not in table:
        raise RuntimeError(f"{section} '{name}' has no stable id in id_registry.json")
    found = int(table[name])
    if found != int(expected):
        raise RuntimeError(
            f"{section} '{name}' is {expected} in code and {found} in id_registry.json"
        )


def assert_unique_spaces() -> None:
    data = registry()

    def check(sections, label):
        seen = {}
        for section in sections:
            table = data.get(section) or {}
            for name, raw in table.items():
                value = int(raw)
                if value in seen:
                    other_section, other_name = seen[value]
                    raise RuntimeError(
                        f"Duplicate {label} id {value}: "
                        f"{section}:{name} and {other_section}:{other_name}"
                    )
                seen[value] = (section, name)

    check(ITEM_SECTIONS, "item")
    check(LOCATION_SECTIONS, "location")
 