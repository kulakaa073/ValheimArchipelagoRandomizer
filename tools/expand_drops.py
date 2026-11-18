"""Append material gather checks. Keeps the current rows and their ids."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod" / "drops.tsv"
TOOLS = ROOT / "tools" / "drops.tsv"
DROPS_PY = ROOT / "valheimapworld" / "Drops.py"

# Biome tier for materials that never appear as a research cost.
TIER = {
    "Acorn": 0, "BeechSeeds": 0, "BirchSeeds": 0, "FirCone": 0, "PineCone": 1,
    "StoneRock": 0, "Wood": 0, "Stone": 0, "MemorialCoal": 12, "QueenBee": 1,
    "Coal": 1, "HardAntler": 1, "AncientCoin": 1,
    "AxeHead1": 7, "AxeHead2": 7, "SharpeningStone": 7, "Thunderstone": 7,
    "OnionSeeds": 7, "PowderedDragonEgg": 7, "YmirRemains": 7, "Silver": 7,
    "BlobVial": 4, "CandleWick": 4, "Turnip": 4, "FreshSeaweed": 3,
    "Bronze": 3, "BronzeNails": 3, "BronzeScrap": 3, "CopperScrap": 3,
    "IronOre": 5, "IronNails": 6, "IronScrap": 6, "Ironpit": 6,
    "BlackMetal": 8, "LinenThread": 8, "Tar": 8, "FragrantBundle": 8, "ShieldCore": 8,
    "Carapace": 9, "CuredSquirrelHamstring": 9, "DvergrKeyFragment": 9,
    "MechanicalSpring": 9, "PungentPebbles": 9, "QueenDrop": 9, "VineGreenSeeds": 9,
    "Flametal": 9, "FlametalOre": 9,
    "BellFragment": 11, "Blackwood": 11, "BonemawSerpentScale": 11, "CeramicPlate": 11,
    "CharredCogwheel": 11, "Charredskull": 11, "DyrnwynBladeFragment": 11,
    "DyrnwynHiltFragment": 11, "DyrnwynTipFragment": 11, "FaderDrop": 11,
    "FlametalOreNew": 11, "OozeMork": 11, "VineberrySeeds": 11,
    "GemstoneBlue": 11, "GemstoneGreen": 11, "GemstoneRed": 11, "SpiceAshlands": 11,
    "FirConeFrost": 12, "FrozenFuel": 12, "FrozenKingDrop": 12, "Grausten": 12,
    "GoldOre": 12, "OrbFrostFire": 12, "OrbThunderBlood": 12,
    "AncientGemstoneBlack": 12, "AncientGemstoneGreen": 12,
    "AncientGemstoneOrange": 12, "AncientGemstonePurple": 12,
    "SpiceForests": 1, "SpiceOceans": 4, "SpiceMountains": 7, "SpicePlains": 8,
    "SpiceMistlands": 9,
}
UPGRADER_TIER = {0: 0, 1: 3, 2: 6, 3: 7, 4: 8, 5: 10, 6: 11, 7: 12}
UPGRADER_WORD = {
    0: "Wooden", 1: "Bronze", 2: "Iron", 3: "Silver", 4: "Black Metal",
    5: "Black Marble", 6: "Flametal", 7: "Bloodgold",
}


def bundle(stack: int) -> int:
    if stack >= 100:
        return 20
    if stack >= 50:
        return 10
    if stack >= 20:
        return 5
    if stack >= 10:
        return 3
    return 1


def research_tiers():
    tiers = defaultdict(list)
    for line in (ROOT / "mod" / "research.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("icon"):
            continue
        cols = line.split("\t")
        tier = int((cols[7] if len(cols) > 7 else "") or 0)
        for bit in cols[5].split("|"):
            if bit:
                tiers[bit.split(":")[0]].append(tier)
    return {name: min(values) for name, values in tiers.items()}


def tier_of(prefab: str, research: dict) -> int:
    if prefab.startswith("Mold"):
        return 12
    if prefab.startswith("Upgrader") and len(prefab) > 8 and prefab[8].isdigit():
        return UPGRADER_TIER[int(prefab[8])]
    if prefab in TIER:
        return TIER[prefab]
    if prefab in research:
        return research[prefab]
    raise SystemExit(f"no tier for {prefab}")


def label(prefab: str, raw: str, english: dict) -> str:
    if prefab.startswith("Upgrader") and len(prefab) > 8 and prefab[8].isdigit():
        kind = "Protection" if "Armor" in prefab else "Battle"
        return f"{UPGRADER_WORD[int(prefab[8])]} {kind} Idol"
    name = english.get(prefab) or raw
    if not name or name.startswith("item_"):
        raise SystemExit(f"no english name for {prefab}")
    return name


def excluded(prefab: str, row: dict, have: set) -> bool:
    if prefab in have:
        return True
    if (row["food"] or 0) > 0 or (row["stamina"] or 0) > 0 or (row["eitr"] or 0) > 0:
        return True
    if prefab.startswith(("Mead", "BarleyWine", "Feast", "Fireworks", "Catapult_", "Bomb")):
        return True
    if prefab.endswith("Uncooked"):
        return True
    if prefab in {
        "Voidplasm", "LastBossGate_RuneTile", "MoldSmallParts", "Pot_Shard_Red", "VegvisirShard_Bonemass",
        "StoneRock", "FlametalOre", "Flametal", "BonemawSerpentScale",
        "HardAntler", "QueenDrop", "FaderDrop", "FrozenKingDrop", "CrownJewel", "MushroomBlue",
    }:
        return True
    return False


def existing_rows():
    rows = []
    for line in MOD.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 5 and cols[4] == "boss":
            continue
        prefab, name, tier, amount = cols[:4]
        rows.append((prefab, name, int(tier), int(amount)))
    return rows


def main():
    materials = json.loads((ROOT / "tools" / "materials.json").read_text(encoding="utf-8"))
    english = json.loads((ROOT / "tools" / "english_names.json").read_text(encoding="utf-8"))
    research = research_tiers()
    current = existing_rows()
    have = {row[0] for row in current}
    added = []
    for row in materials:
        prefab = row["prefab"]
        if excluded(prefab, row, have):
            continue
        added.append((prefab, label(prefab, row["name"], english), tier_of(prefab, research), bundle(int(row["stack"] or 1))))
    added.sort(key=lambda row: row[0].lower())
    rows = current + added
    names = [row[1] for row in rows]
    dupes = sorted({name for name in names if names.count(name) > 1})
    if dupes:
        raise SystemExit("duplicate gather names: " + ", ".join(dupes))
    header = (
        "# itemPrefab\tdisplayName\ttier\tbundleAmount\n"
        "# Used only when the Archipelago seed enables Drop Checks.\n"
        "# First pickup of a material is a location. The received item grants bundleAmount of that material.\n"
        "# Gear, arrows, food, and mead are not checks. Processed materials such as nails and refined eitr are.\n"
    )
    body = "".join(f"{prefab}\t{name}\t{tier}\t{amount}\n" for prefab, name, tier, amount in rows)
    text = header + body
    MOD.write_text(text, encoding="utf-8")
    TOOLS.write_text(text, encoding="utf-8")
    py = DROPS_PY.read_text(encoding="utf-8")
    start = py.find("DROP_ROWS = [")
    end = py.find("]\n", start)
    if start < 0 or end < 0:
        raise SystemExit("DROP_ROWS block missing")
    lines = ["DROP_ROWS = ["]
    for prefab, name, tier, amount in rows:
        lines.append(f"    ({prefab!r}, {name!r}, {tier}, {amount}),")
    lines.append("]")
    DROPS_PY.write_text(py[:start] + "\n".join(lines) + py[end + 1:], encoding="utf-8")
    print(f"kept {len(current)} added {len(added)} total {len(rows)}")


if __name__ == "__main__":
    main()
