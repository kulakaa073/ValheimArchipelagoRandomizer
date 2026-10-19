"""Build the static tracker catalog from the research, trophy, and drop tables."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from write_research_md import pretty  # noqa: E402

TIER_DOORS = {
    1: ["Crafting"],
    2: ["Axes Tier 1", "Troll Armor", "Cooking Station", "Bed Tier 1", "Warmth Tier 1"],
    3: ["Pickaxes Tier 1", "Boat Tier 1", "Smelter", "Forge"],
    4: ["Bronze"],
    5: ["Axes Tier 2"],
    6: ["Pickaxes Tier 2"],
    7: ["Pickaxes Tier 3", "Forge Upgrade 1", "Nails Tier 2"],
    8: ["Artisan Table", "Blast Furnace"],
    9: ["Axes Tier 4", "Wisp Fountain", "Wisplight", "Forge Upgrade 2", "Forge Upgrade 3", "Spinning Wheel"],
    10: ["Pickaxes Tier 4"],
    11: ["Ceramic Plates", "Boat Tier 4", "Artisan Press"],
    12: ["Siege", "Snow Shovel"],
}

RESOURCES = {
    "Bronze", "BronzeNails", "IronNails", "CeramicPlate",
    "FishSoup", "Pancakes", "Lingondricka", "OatMilk", "OatmealLingonberryJam",
    "MeatballsMashedPoteitr", "MooseKebab", "SealSoup", "SmokedFish", "SmokedMooseMeat",
    "FeastDeepNorth", "FeastDeepNorth_Material", "PulledBear", "KaleChipsUncooked",
    "FishAndBreadUncooked", "BakedPoteitrUncooked", "OvenPancakeUncooked",
    "FirTree_big_Sapling", "sapling_Kale", "sapling_oat", "sapling_poteitr", "sapling_seedkale",
}


def blob(marker: str, path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f"missing {marker} in {path}")
    return text[start:].split("'''", 2)[1]


def reward_kind(prefab: str) -> str:
    low = prefab.lower()
    if prefab in RESOURCES or low.endswith("_stack") or low.endswith("_pile"):
        return "resource"
    if "uncooked" in low and not any(word in prefab for word in ("Sword", "Axe", "Bow", "Mace", "Spear", "Shield", "Armor", "Helmet", "Knife", "Staff", "Sledge", "Atgeir")):
        return "resource"
    if low.startswith("piece_") or low.startswith(("wood_", "darkwood_", "ashwood_", "stave_", "scale_", "woodiron_")):
        return "building"
    if low in {
        "forge", "smelter", "charcoal_kiln", "blastfurnace", "windmill", "blackforge", "eitrrefinery",
        "fermenter", "bonfire", "fire_pit", "hearth", "bed", "portal_wood", "portal_stone", "stake_wall",
        "stone_fence", "cart",
    } or low.startswith(("forge_", "blackforge_", "cauldron_", "artisan_")):
        return "building"
    return "gear"


ENGLISH = {}
_english_path = Path(__file__).resolve().parent / "english_names.json"
if _english_path.exists():
    ENGLISH = json.loads(_english_path.read_text(encoding="utf-8"))


NAME_OVERRIDES = {
    "artisan_ext1": "Artisan Press",
    "Upgrader0Armor": "Wooden Protection Idol",
    "Upgrader0Weapon": "Wooden Battle Idol",
    "Upgrader1Armor": "Bronze Protection Idol",
    "Upgrader1Weapon": "Bronze Battle Idol",
    "Upgrader2Armor": "Iron Protection Idol",
    "Upgrader2Weapon": "Iron Battle Idol",
    "Upgrader3Armor": "Silver Protection Idol",
    "Upgrader3Weapon": "Silver Battle Idol",
    "Upgrader4Armor": "Black Metal Protection Idol",
    "Upgrader4Weapon": "Black Metal Battle Idol",
    "Upgrader5Armor": "Black Marble Protection Idol",
    "Upgrader5Weapon": "Black Marble Battle Idol",
    "Upgrader6Armor": "Flametal Protection Idol",
    "Upgrader6Weapon": "Flametal Battle Idol",
    "Upgrader7Armor": "Bloodgold Protection Idol",
    "Upgrader7Weapon": "Bloodgold Battle Idol",
    "FeastDeepNorth_Material": "Northern Morning Fare platter",
    "HelmetCelebration": "Celebratory Cap",
    "HelmetPointyHat": "Pointy Hat",
    "HelmetFishingHat": "Fishing Hat",
    "ShieldIronSquare": "Iron Shield",
    "SaddleLox": "Lox Saddle",
    "SaddleAsksvin": "Asksvin Saddle",
}


def english_name(prefab: str, fallback: str | None = None) -> str:
    override = NAME_OVERRIDES.get(prefab)
    if override:
        return override
    english = ENGLISH.get(prefab)
    if english:
        return english
    return fallback if fallback else pretty(prefab)


def materials(raw: str):
    out = []
    for bit in raw.split("|"):
        if not bit:
            continue
        name, amount = bit.split(":") if ":" in bit else (bit, "1")
        out.append({"prefab": name, "name": english_name(name), "amount": int(amount)})
    return out


def load_ap_rows(path: Path, marker: str, id_start: int):
    rows = []
    number = id_start
    for line in blob(marker, path).splitlines():
        if not line.strip() or line.startswith("//"):
            continue
        parts = [part.strip() for part in line.split(",")]
        rows.append((number, parts))
        number += 1
    return rows


def main() -> None:
    researches = []
    for line in (ROOT / "mod" / "research.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("icon"):
            continue
        cols = line.split("\t")
        while len(cols) < 9:
            cols.append("")
        researches.append(cols)
    by_id = {cols[1]: cols[2] for cols in researches}

    locations = {parts[1]: number for number, parts in load_ap_rows(ROOT / "valheimapworld" / "Locations.py", "locations_txt = '''", 1)}
    items = {parts[0]: number for number, parts in load_ap_rows(ROOT / "valheimapworld" / "Items.py", "items_txt = '''", 2000)}

    checks = []
    unlocks = []
    for cols in researches:
        parents = [part for part in cols[4].split("|") if part]
        gated = [part for part in cols[6].split("|") if part]
        unlock_rows = []
        for prefab in gated:
            kind = reward_kind(prefab)
            unlock_rows.append({"prefab": prefab, "name": english_name(prefab), "rewardKind": kind})
            unlocks.append({
                "id": prefab,
                "name": english_name(prefab),
                "rewardKind": kind,
                "checkId": cols[1],
                "checkName": cols[2],
                "checkKind": "research",
                "tier": int(cols[7] or 0),
                "iconPrefab": prefab,
            })
        checks.append({
            "id": cols[1],
            "name": cols[2],
            "kind": "research",
            "tier": int(cols[7] or 0),
            "category": cols[8],
            "locationId": locations.get(cols[2]),
            "itemId": items.get(cols[2]),
            "iconPrefab": cols[0],
            "requires": [{"id": parent, "name": by_id.get(parent, parent)} for parent in parents],
            "materials": materials(cols[5]),
            "rewardKind": "research",
            "unlocks": unlock_rows,
        })

    for line in (ROOT / "mod" / "trophies.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("research"):
            continue
        prefab, research_id, boost, tier = line.split("\t")[:4]
        name = "Trophy: " + prefab
        checks.append({
            "id": research_id,
            "name": name,
            "kind": "trophy",
            "tier": int(tier),
            "category": "Useful",
            "locationId": locations.get(name),
            "itemId": items.get(name),
            "iconPrefab": prefab,
            "requires": [],
            "materials": [],
            "rewardKind": "stats",
            "boost": boost,
            "unlocks": [{"prefab": prefab, "name": english_name(prefab), "rewardKind": "stats", "boost": boost}],
        })
        unlocks.append({
            "id": prefab,
            "name": english_name(prefab),
            "rewardKind": "stats",
            "boost": boost,
            "checkId": research_id,
            "checkName": name,
            "checkKind": "trophy",
            "tier": int(tier),
            "iconPrefab": prefab,
        })

    # Location and item ids match valheimapworld/Drops.py. Gather ids follow gather rows only.
    boss_location_ids = {
        "Defeat Eikthyr": 5001,
        "Defeat the Elder": 5002,
        "Defeat Bonemass": 5003,
        "Defeat Moder": 5004,
        "Defeat Yagluth": 5005,
        "Defeat the Queen": 5006,
        "Defeat Fader": 5007,
        "Defeat Kall": 5000,
    }
    boss_item_ids = {
        "HardAntler": 7101,
        "CryptKey": 7102,
        "Wishbone": 7103,
        "DragonTear": 7104,
        "YagluthDrop": 7105,
        "QueenDrop": 7106,
        "FaderDrop": 7107,
        "FrozenKingDrop": 7108,
    }
    gather_index = 0
    for line in (ROOT / "mod" / "drops.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        prefab, label, tier, amount = cols[:4]
        amount = int(amount)
        tier = int(tier)
        if len(cols) >= 5 and cols[4] == "boss":
            location_name = cols[7]
            if location_name not in boss_location_ids or prefab not in boss_item_ids:
                raise SystemExit(f"boss row has no tracker id: {prefab} {location_name}")
            checks.append({
                "id": prefab,
                "name": location_name,
                "kind": "boss",
                "tier": tier,
                "category": "Progression",
                "locationId": boss_location_ids[location_name],
                "itemId": boss_item_ids[prefab],
                "iconPrefab": prefab,
                "requires": [],
                "materials": [],
                "rewardKind": "resource",
                "bundle": amount,
                "onePerPlayer": cols[8] == "1",
                "unlocks": [{
                    "prefab": prefab,
                    "name": english_name(prefab, label),
                    "rewardKind": "resource",
                    "amount": amount,
                }],
            })
            unlocks.append({
                "id": prefab,
                "name": english_name(prefab, label),
                "rewardKind": "resource",
                "amount": amount,
                "checkId": prefab,
                "checkName": location_name,
                "checkKind": "boss",
                "tier": tier,
                "iconPrefab": prefab,
            })
            continue
        name = "Gather: " + label
        checks.append({
            "id": prefab,
            "name": name,
            "kind": "gather",
            "tier": tier,
            "category": "Useful",
            "locationId": 6001 + gather_index,
            "itemId": 8001 + gather_index,
            "iconPrefab": prefab,
            "requires": [],
            "materials": [],
            "rewardKind": "resource",
            "bundle": amount,
            "unlocks": [{
                "prefab": prefab,
                "name": english_name(prefab, label),
                "rewardKind": "resource",
                "amount": amount,
            }],
        })
        unlocks.append({
            "id": prefab,
            "name": english_name(prefab, label),
            "rewardKind": "resource",
            "amount": amount,
            "checkId": prefab,
            "checkName": name,
            "checkKind": "gather",
            "tier": tier,
            "iconPrefab": prefab,
        })
        gather_index += 1

    missing_locations = [check["name"] for check in checks if check["kind"] != "gather" and check["kind"] != "goal" and check["locationId"] is None]
    if missing_locations:
        raise SystemExit("checks missing location ids: " + ", ".join(missing_locations[:8]))

    catalog = {
        "states": {
            "locked": "Reward item has not been received. Show the icon gray.",
            "unlocked": "Reward item has been received. Show the icon in color. Gear, the stat, or the resource bundle is yours.",
            "finished": "This slot's location has been checked. Show a checkmark. For a research, that means it was crafted and sent.",
        },
        "modes": {
            "icons": "Uses locked, unlocked, and finished. No placement data.",
            "source": "Uses research_access to choose the rule text: parents, tier doors, materials, or crafted parents. sequential_tiers says the door items are in the previous tier of this world.",
            "cheatSheet": "Needs a scout or a hint for each location. The static catalog does not know that a blueberry check holds a bow.",
        },
        "seedFlags": {
            "drop_checks": "Slot data on seeds generated after 0.2.5. Older seeds: on when any Gather location exists.",
            "boss_checks": "Slot data boss_drops. On by default for seeds generated after 0.2.29. Off when only the goal boss location exists.",
            "research_access": "Slot data int. 0 default, 1 tier, 2 materials, 3 natural. Missing on the current seed. Not inferable.",
            "sequential_tiers": "Slot data 0 or 1. Missing on the current seed. Not inferable.",
        },
        "tierDoors": {str(tier): names for tier, names in TIER_DOORS.items()},
        "checks": checks,
        "unlocks": unlocks,
    }
    text = json.dumps(catalog, indent=2)
    outs = [ROOT / "tracker" / "catalog.json", ROOT.parent / "valheim-tracker" / "catalog.json"]
    for out in outs:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    kinds = {}
    for unlock in unlocks:
        kinds[unlock["rewardKind"]] = kinds.get(unlock["rewardKind"], 0) + 1
    print(f"checks={len(checks)} unlocks={len(unlocks)} rewards={kinds}")


if __name__ == "__main__":
    main()
