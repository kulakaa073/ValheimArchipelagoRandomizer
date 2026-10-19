"""Export English item names and inventory icons for the tracker."""
import csv
import json
import re
from io import StringIO
from pathlib import Path

import UnityPy
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT.parent
BUNDLE = GAME / "valheim_Data" / "StreamingAssets" / "SoftRef" / "Bundles" / "c4210710"
RESOURCES = GAME / "valheim_Data" / "resources.assets"
ICONS = GAME / "valheim-tracker" / "icons"
NAMES = Path(__file__).resolve().parent / "english_names.json"
LOCALIZATION_ASSETS = ("localization", "localization_deepnorth", "localization_extra", "localization_witch")


def prefabs():
    names = set()
    research = (ROOT / "mod" / "research.tsv").read_text(encoding="utf-8").splitlines()
    for line in research:
        if not line.strip() or line.startswith("#") or line.startswith("icon"):
            continue
        cols = line.split("\t")
        while len(cols) < 9:
            cols.append("")
        if cols[0]:
            names.add(cols[0])
        for bit in cols[5].split("|"):
            if bit:
                names.add(bit.split(":")[0])
        for bit in cols[6].split("|"):
            if bit:
                names.add(bit)
    for line in (ROOT / "mod" / "trophies.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("research"):
            continue
        names.add(line.split("\t")[0])
    for line in (ROOT / "mod" / "drops.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        names.add(line.split("\t")[0])
    names.add("TrophyElaking")
    return names


def load_localization():
    env = UnityPy.load(str(RESOURCES))
    blobs = {}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.read()
        if data.m_Name in LOCALIZATION_ASSETS:
            text = data.m_Script
            if isinstance(text, bytes):
                text = text.decode("utf-8", "replace")
            blobs[data.m_Name] = text
    table = {}
    for name in LOCALIZATION_ASSETS:
        text = blobs.get(name)
        if not text:
            continue
        rows = csv.reader(StringIO(text.lstrip("\ufeff")))
        header = next(rows)
        try:
            english = header.index("English")
        except ValueError:
            english = 1
        for row in rows:
            if len(row) <= english or not row[0].strip():
                continue
            value = row[english].strip()
            if value:
                table[row[0].strip()] = value
    return table


def clean_name(token, table):
    if not token:
        return ""
    text = token[1:] if token.startswith("$") else token
    if text in table:
        text = table[text]
    for _ in range(4):
        updated = re.sub(r"\$([A-Za-z0-9_]+)", lambda match: table.get(match.group(1), match.group(0)), text)
        if updated == text:
            break
        text = updated
    text = re.sub(r"</?color(?:=[^>]*)?>", "", text)
    text = text.replace("\\n", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


ALIASES = {
    "Finewood": "FineWood",
    "MusroomYellow": "MushroomYellow",
    "Piece_ironcookingstation": "piece_cookingstation_iron",
}


def cab_index(folder: Path):
    index = {}
    for path in folder.iterdir():
        if not path.is_file():
            continue
        blob = path.read_bytes()[:120000]
        for match in re.finditer(rb"CAB-[0-9a-fA-F]+", blob):
            index.setdefault(match.group(0).decode("ascii").lower(), path)
    return index


def objects_in(file_obj):
    found = {}
    if getattr(file_obj, "objects", None):
        found.update(file_obj.objects)
    for child in getattr(file_obj, "files", {}).values():
        if getattr(child, "objects", None):
            found.update(child.objects)
    return found


def fit_icon(image):
    if image is None or image.width > 512 or image.height > 512:
        return None
    image = image.convert("RGBA")
    image.thumbnail((64, 64), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.paste(image, ((64 - image.width) // 2, (64 - image.height) // 2), image)
    return canvas


def component_trees(game_object):
    trees = []
    for pair in game_object.read().m_Component:
        try:
            component = pair.component.deref()
        except Exception:
            continue
        if component.type.name != "MonoBehaviour":
            continue
        try:
            trees.append((component, component.read_typetree()))
        except Exception:
            continue
    return trees


def describe(trees):
    for component, tree in trees:
        shared = tree.get("m_itemData", {}).get("m_shared") if isinstance(tree.get("m_itemData"), dict) else None
        if isinstance(shared, dict) and shared.get("m_name"):
            icons = shared.get("m_icons") or []
            return shared.get("m_name"), component, icons[0] if icons else None
    for component, tree in trees:
        icon = tree.get("m_icon")
        if tree.get("m_name") and isinstance(icon, dict) and icon.get("m_PathID"):
            return tree.get("m_name"), component, icon
    return None, None, None


def main():
    needed = prefabs()
    print("prefabs", len(needed))
    table = load_localization()
    print("localization keys", len(table))
    print("indexing bundle cabs")
    cabs = cab_index(BUNDLE.parent)
    print("cabs", len(cabs))
    print("loading item bundle")
    env = UnityPy.load(str(BUNDLE))
    found = {}
    cooking = []
    for path, obj in env.container.items():
        if not path.endswith(".prefab"):
            continue
        stem = Path(path).stem
        found.setdefault(stem, obj)
        if "cooking" in stem.lower() or "ironcook" in stem.lower():
            cooking.append(stem)
    print("cooking prefabs", ", ".join(cooking[:20]))
    rows = []
    extra_names = set()
    for name in sorted(needed):
        source_name = ALIASES.get(name, name)
        obj = found.get(source_name)
        if obj is None:
            continue
        token, component, icon = describe(component_trees(obj))
        rows.append((name, token, component, icon))
        if isinstance(icon, dict) and icon.get("m_FileID"):
            external = component.assets_file.externals[icon["m_FileID"] - 1]
            extra_names.add(external.name.lower())
    print("icon files", sorted(extra_names))
    for cab_name in sorted(extra_names):
        path = cabs.get(cab_name)
        if path is None:
            print("unmapped", cab_name)
            continue
        print("loading", cab_name, path.name, path.stat().st_size)
        env.load_file(str(path), name=path.name)
    object_cache = {}

    def sprite_for(component, pointer):
        if not isinstance(pointer, dict):
            return None
        path_id = pointer.get("m_PathID") or 0
        file_id = pointer.get("m_FileID") or 0
        if not path_id:
            return None
        if file_id == 0:
            source = component.assets_file.objects
        else:
            external = component.assets_file.externals[file_id - 1]
            key = external.name.lower()
            source = object_cache.get(key)
            if source is None:
                cab = env.get_cab(key)
                source = objects_in(cab) if cab is not None else {}
                object_cache[key] = source
        obj = source.get(path_id)
        if obj is None or obj.type.name not in ("Sprite", "Texture2D"):
            return None
        return fit_icon(obj.read().image)

    ICONS.mkdir(parents=True, exist_ok=True)
    names = {}
    saved = 0
    no_icon = []
    for name, token, component, icon in rows:
        english = clean_name(token, table)
        if english:
            names[name] = english
        image = sprite_for(component, icon)
        if image is None:
            no_icon.append(name)
            continue
        image.save(ICONS / f"{name}.png")
        saved += 1
    NAMES.write_text(json.dumps(names, indent=2, ensure_ascii=False), encoding="utf-8")
    missing = sorted(needed - {name for name, *_rest in rows})
    print(f"names={len(names)} icons={saved} no_icon={len(no_icon)} missing_prefab={len(missing)}")
    if missing:
        print("missing", ", ".join(missing[:40]))
    if no_icon:
        print("no icon", ", ".join(no_icon[:40]))


if __name__ == "__main__":
    main()
