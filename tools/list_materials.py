"""List ItemType.Material prefabs from the game for gather-check expansion."""
import csv
import json
from io import StringIO
from pathlib import Path

import UnityPy

GAME = Path(__file__).resolve().parents[2]
BUNDLE = GAME / "valheim_Data" / "StreamingAssets" / "SoftRef" / "Bundles" / "c4210710"
RESOURCES = GAME / "valheim_Data" / "resources.assets"
OUT = Path(__file__).resolve().parent / "materials.json"


def load_english():
    env = UnityPy.load(str(RESOURCES))
    table = {}
    for obj in env.objects:
        if obj.type.name != "TextAsset" or obj.read().m_Name != "localization":
            continue
        text = obj.read().m_Script
        if isinstance(text, bytes):
            text = text.decode("utf-8", "replace")
        rows = csv.reader(StringIO(text.lstrip("\ufeff")))
        header = next(rows)
        english = header.index("English")
        for row in rows:
            if len(row) > english and row[0].strip() and row[english].strip():
                table[row[0].strip()] = row[english].strip()
        break
    deep = GAME / "valheim_Data" / "resources.assets"
    env = UnityPy.load(str(deep))
    for obj in env.objects:
        if obj.type.name != "TextAsset" or obj.read().m_Name != "localization_deepnorth":
            continue
        text = obj.read().m_Script
        if isinstance(text, bytes):
            text = text.decode("utf-8", "replace")
        rows = csv.reader(StringIO(text.lstrip("\ufeff")))
        header = next(rows)
        try:
            english = header.index("English")
        except ValueError:
            english = 1
        for row in rows:
            if len(row) > english and row[0].strip() and row[english].strip():
                table[row[0].strip()] = row[english].strip()
    return table


def clean(token, table):
    if not token:
        return ""
    key = token[1:] if token.startswith("$") else token
    return table.get(key, key).replace("\\n", " ").strip()


def main():
    table = load_english()
    env = UnityPy.load(str(BUNDLE))
    rows = []
    for path, obj in env.container.items():
        if not path.endswith(".prefab") or obj.type.name != "GameObject":
            continue
        stem = Path(path).stem
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
            shared = tree.get("m_itemData", {}).get("m_shared") if isinstance(tree.get("m_itemData"), dict) else None
            if not isinstance(shared, dict) or shared.get("m_itemType") != 1:
                continue
            rows.append({
                "prefab": stem,
                "name": clean(shared.get("m_name"), table),
                "stack": shared.get("m_maxStackSize") or 1,
                "food": shared.get("m_food") or 0,
                "stamina": shared.get("m_foodStamina") or 0,
                "eitr": shared.get("m_foodEitr") or 0,
                "consume": bool(shared.get("m_consumeStatusEffect")),
            })
            break
    rows.sort(key=lambda row: row["prefab"].lower())
    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print("materials", len(rows))


if __name__ == "__main__":
    main()
