"""Extract quality-1 craft and build costs from the game bundle."""
import json
from pathlib import Path

import UnityPy

GAME = Path(__file__).resolve().parents[2]
BUNDLE = GAME / "valheim_Data" / "StreamingAssets" / "SoftRef" / "Bundles" / "c4210710"
OUT = Path(__file__).resolve().parent / "recipe_costs.json"


def component_ids(go):
    ids = []
    for pair in go.m_Component:
        pointer = pair.component
        pid = getattr(pointer, "path_id", None)
        if pid:
            ids.append(pid)
    return ids


def costs_of(tree, names):
    costs = []
    for req in tree.get("m_resources") or []:
        if not isinstance(req, dict):
            continue
        amount = int(req.get("m_amount") or 0)
        if amount <= 0:
            continue
        pid = (req.get("m_resItem") or {}).get("m_PathID")
        prefab = names.get(pid)
        if not prefab:
            continue
        costs.append({"prefab": prefab, "amount": amount})
    return costs


def main():
    env = UnityPy.load(str(BUNDLE))
    names = {}
    pieces = []
    prefabs = [
        (path, obj) for path, obj in env.container.items()
        if str(path).endswith(".prefab") and obj.type.name == "GameObject"
    ]
    print("prefabs", len(prefabs), flush=True)
    for index, (path, obj) in enumerate(prefabs):
        stem = Path(path).stem
        names[obj.path_id] = stem
        try:
            go = obj.read()
        except Exception:
            continue
        for pid in component_ids(go):
            names[pid] = stem
        if index % 1000 == 0:
            print("mapped", index, flush=True)

    print("names", len(names), flush=True)
    recipes = []
    for path, obj in env.container.items():
        text = str(path).replace("\\", "/")
        if "/Recipes/" not in text or not text.endswith(".asset"):
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        if "m_resources" not in tree:
            continue
        item_pid = (tree.get("m_item") or {}).get("m_PathID")
        station_pid = (tree.get("m_craftingStation") or {}).get("m_PathID")
        recipes.append({
            "kind": "recipe",
            "name": tree.get("m_Name") or Path(text).stem,
            "item": names.get(item_pid, ""),
            "station": names.get(station_pid, ""),
            "folder": text.split("/Recipes/")[1].split("/")[0],
            "upgradeOnly": bool(tree.get("m_noCraftOnlyUpgrade")),
            "costs": costs_of(tree, names),
        })
    print("recipes", len(recipes), flush=True)

    for index, (path, obj) in enumerate(prefabs):
        try:
            go = obj.read()
        except Exception:
            continue
        for pair in go.m_Component:
            try:
                component = pair.component.deref()
            except Exception:
                continue
            if component.type.name != "MonoBehaviour":
                continue
            try:
                tree = component.read_typetree()
            except Exception:
                continue
            if "m_resources" not in tree or "m_comfort" not in tree:
                continue
            costs = costs_of(tree, names)
            if not costs:
                continue
            pieces.append({
                "kind": "piece",
                "name": Path(path).stem,
                "item": Path(path).stem,
                "station": "",
                "folder": "Piece",
                "upgradeOnly": False,
                "costs": costs,
            })
            break
        if index % 1000 == 0:
            print("pieces", index, len(pieces), flush=True)

    OUT.write_text(json.dumps({"recipes": recipes, "pieces": pieces}, indent=2), encoding="utf-8")
    print("wrote", len(recipes), "recipes", len(pieces), "pieces", flush=True)


if __name__ == "__main__":
    main()
