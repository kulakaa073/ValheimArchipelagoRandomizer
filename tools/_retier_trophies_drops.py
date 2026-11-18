"""Retier trophies.tsv + drops.tsv to research v5.1 T0–T15 biomes.

Also syncs Locations.py trophy tiers, Drops.py DROP_ROWS, and extends Regions.py
through Tier15 so T13–T15 locations resolve. Does not touch boss kill rows/BOSS_DROPS.
Does not rebuild mod/apworld.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- Trophy prefab → new tier (biome where the creature lives) ---
TROPHY_TIER = {
    # T0 meadows early
    "TrophyNeck": 0,
    "TrophyBoar": 0,
    "TrophyDeer": 0,
    # T2 Eikthyr beat
    "TrophyEikthyr": 2,
    # T3 Black Forest
    "TrophyGreydwarf": 3,
    "TrophyGreydwarfBrute": 3,
    "TrophyGreydwarfShaman": 3,
    "TrophyBjorn": 3,
    "TrophySkeleton": 3,
    "TrophySkeletonPoison": 3,
    "TrophyGhost": 3,
    "TrophyFrostTroll": 3,
    "TrophyTheElder": 3,
    # T6 Swamp / ocean
    "TrophySkeletonHildir": 6,  # Brenna
    "TrophyDraugr": 6,
    "TrophyDraugrElite": 6,
    "TrophyAbomination": 6,
    "TrophyBonemass": 6,
    "TrophyKvastur": 6,
    "TrophyBlob": 6,
    "TrophyLeech": 6,
    "TrophyWraith": 6,
    "TrophySurtling": 6,
    "TrophySerpent": 6,
    # T7 Mountains
    "TrophyCultist_Hildir": 7,  # Geirrhafa
    "TrophyFenring": 7,
    "TrophyWolf": 7,
    "TrophySGolem": 7,
    "TrophyDragonQueen": 7,  # Moder
    "TrophyCultist": 7,
    "TrophyHatchling": 7,
    "TrophyUlv": 7,
    "TrophyBlob_Frost": 7,
    # T8 Plains
    "TrophyGoblinBruteBrosBrute": 8,
    "TrophyDeathsquito": 8,
    "TrophyGoblinBrute": 8,
    "TrophyLox": 8,
    "TrophyBjornUndead": 8,
    "TrophyGoblinBruteBrosShaman": 8,
    "TrophyGoblinKing": 8,
    "TrophyGoblin": 8,
    "TrophyGrowth": 8,
    "TrophyGoblinShaman": 8,
    # T9 Mistlands entry
    "TrophySeekerBrute": 9,
    "TrophyGjall": 9,
    "TrophySeeker": 9,
    "TrophyTick": 9,
    "TrophyDvergr": 9,
    "TrophyHare": 9,
    # T10 Queen
    "TrophySeekerQueen": 10,
    # T11 Ashlands base
    "TrophyBonemawSerpent": 11,
    "TrophyCharredArcher": 11,
    "TrophyMorgen": 11,
    "TrophyCharredMage": 11,
    "TrophyFallenValkyrie": 11,
    "TrophyCharredMelee": 11,
    "TrophyAsksvin": 11,
    "TrophyVolture": 11,
    # T12 Fader
    "TrophyFader": 12,
    # T13 DN entry / shore
    "TrophyMoose": 13,
    "TrophySeal": 13,
    # T14 DN Nord / tunnels
    "TrophyBarka": 14,
    "TrophyMole": 14,
    "TrophyWrithan": 14,
    "TrophyBlob_Lava": 14,
    "TrophyElaking": 14,
    # T15 Mörkhalla
    "TrophyBlob_Morkhalla": 15,
    "TrophyJotunWarrior": 15,
    "TrophyJotunWitch": 15,
}

# Prefab → tier for gather drops. Boss-annotated rows are skipped.
# Explicit overrides; anything unlisted keeps its current tier (then we assert coverage).
DROP_TIER = {
    # T0 meadows
    "Raspberry": 0,
    "Mushroom": 0,
    "Honey": 0,
    "Dandelion": 0,
    "LeatherScraps": 0,
    "RawMeat": 0,
    "DeerMeat": 0,
    "DeerHide": 0,
    "Feathers": 0,
    "Resin": 0,
    "NeckTail": 0,
    "Acorn": 0,
    "BeechSeeds": 0,
    "BirchSeeds": 0,
    "FirCone": 0,
    "Stone": 0,
    "Wood": 0,
    "Upgrader0Armor": 0,
    "Upgrader0Weapon": 0,
    # T1 meadows / early trader fluff still findable early
    "Amber": 1,
    "AmberPearl": 1,
    "AncientCoin": 1,
    "Coins": 1,
    "Flint": 1,
    "QueenBee": 1,
    "Pukeberries": 1,
    "RottenMeat": 1,
    # T3 Black Forest
    "Blueberries": 3,
    "Thistle": 3,
    "MushroomYellow": 3,
    "GreydwarfEye": 3,
    "BoneFragments": 3,
    "TrollHide": 3,
    "BjornHide": 3,
    "BjornMeat": 3,
    "BjornPaw": 3,
    "Coal": 3,
    "Copper": 3,
    "CopperOre": 3,
    "CopperScrap": 3,
    "Tin": 3,
    "TinOre": 3,
    "Bronze": 3,
    "BronzeNails": 3,
    "BronzeScrap": 3,
    "SurtlingCore": 3,
    "Ectoplasm": 3,
    "RoundLog": 3,
    "PineCone": 3,
    "Ruby": 3,
    "CarrotSeeds": 3,
    "Carrot": 3,
    "SpiceForests": 3,
    "Upgrader1Armor": 3,
    "Upgrader1Weapon": 3,
    # T5 finewood / pre-swamp
    "FineWood": 5,
    "ElderBark": 5,
    "IronOre": 5,
    # T6 swamp / iron / ocean
    "Bloodbag": 6,
    "Entrails": 6,
    "Guck": 6,
    "Ooze": 6,
    "SerpentMeat": 6,
    "SerpentScale": 6,
    "Chitin": 6,
    "Chain": 6,
    "Root": 6,
    "Turnip": 6,
    "TurnipSeeds": 6,
    "Iron": 6,
    "IronNails": 6,
    "Ironpit": 6,
    "IronScrap": 6,
    "WitheredBone": 6,
    "BlobVial": 6,
    "CandleWick": 6,
    "CuredSquirrelHamstring": 6,
    "FreshSeaweed": 6,
    "PowderedDragonEgg": 6,  # moved from swamp-tier placeholder; actually mountain — see T7
    "PungentPebbles": 6,
    "SpiceOceans": 6,
    "Thunderstone": 6,
    "YmirRemains": 6,
    "VineGreenSeeds": 6,  # overridden below to mist if needed
    "WrithanRoots": 6,  # swamp drop
    "SilverNecklace": 6,  # often swamp crypt loot; mountain silver is separate
    "Upgrader2Armor": 6,
    "Upgrader2Weapon": 6,
    # fix PowderedDragonEgg + VineGreen + Thunderstone properly:
}

# Fix the few I double-assigned above
DROP_TIER.update(
    {
        "PowderedDragonEgg": 7,
        "Thunderstone": 7,
        "YmirRemains": 7,
        "VineGreenSeeds": 9,  # mistlands ivy
        "SilverNecklace": 7,
        # T7 mountains
        "WolfMeat": 7,
        "WolfPelt": 7,
        "WolfFang": 7,
        "WolfClaw": 7,
        "WolfHairBundle": 7,
        "FreezeGland": 7,
        "Crystal": 7,
        "Obsidian": 7,
        "Silver": 7,
        "SilverOre": 7,
        "Onion": 7,
        "OnionSeeds": 7,
        "DragonEgg": 7,
        "JuteRed": 7,
        "AxeHead1": 7,
        "AxeHead2": 7,
        "SharpeningStone": 7,
        "SpiceMountains": 7,
        "Upgrader3Armor": 7,
        "Upgrader3Weapon": 7,
        # T8 plains
        "Cloudberry": 8,
        "LoxMeat": 8,
        "LoxPelt": 8,
        "Needle": 8,
        "Barley": 8,
        "Flax": 8,
        "BlackMetal": 8,
        "BlackMetalScrap": 8,
        "Tar": 8,
        "LinenThread": 8,
        "FragrantBundle": 8,
        "ShieldCore": 8,
        "UndeadBjornRibcage": 8,
        "ChickenMeat": 8,
        "ChickenEgg": 8,
        "MushroomBzerker": 8,
        "ScytheHandle": 8,
        "SpicePlains": 8,
        "Upgrader4Armor": 8,
        "Upgrader4Weapon": 8,
        # T9 mist entry
        "RoyalJelly": 9,
        "Sap": 9,
        "ScaleHide": 9,
        "GiantBloodSack": 9,
        "Bilebag": 9,
        "BugMeat": 9,
        "HareMeat": 9,
        "MushroomJotunPuffs": 9,
        "MushroomMagecap": 9,
        "BlackCore": 9,
        "Carapace": 9,
        "YggdrasilWood": 9,
        "JuteBlue": 9,
        "Mandible": 9,
        "MechanicalSpring": 9,
        "DvergrKeyFragment": 9,
        "DvergrNeedle": 9,
        "GlowWorm": 9,
        # T10 mist deep / Queen
        "BlackMarble": 10,
        "Eitr": 10,
        "Softtissue": 10,
        "Wisp": 10,
        "SpiceMistlands": 10,
        "Upgrader5Armor": 10,
        "Upgrader5Weapon": 10,
        # T11 ash base
        "AsksvinMeat": 11,
        "AskHide": 11,
        "AskBladder": 11,
        "AsksvinCarrionNeck": 11,
        "AsksvinCarrionPelvic": 11,
        "AsksvinCarrionRibcage": 11,
        "AsksvinCarrionSkull": 11,
        "Vineberry": 11,
        "VineberrySeeds": 11,
        "MushroomSmokePuff": 11,
        "Fiddleheadfern": 11,
        "BoneMawSerpentMeat": 11,
        "BonemawSerpentTooth": 11,
        "CharredBone": 11,
        "CelestialFeather": 11,
        "MorgenSinew": 11,
        "MorgenHeart": 11,
        "Blackwood": 11,
        "BellFragment": 11,
        "CeramicPlate": 11,
        "CharcoalResin": 11,
        "CharredCogwheel": 11,
        "Charredskull": 11,
        "FlametalNew": 11,
        "FlametalOreNew": 11,
        "GemstoneBlue": 11,
        "GemstoneGreen": 11,
        "GemstoneRed": 11,
        "MoltenCore": 11,
        "OozeMork": 11,
        "Pot_Shard_Green": 11,
        "ProustitePowder": 11,
        "SulfurStone": 11,
        "SpiceAshlands": 11,
        "VoltureMeat": 11,
        "VoltureEgg": 11,
        "DyrnwynBladeFragment": 11,
        "DyrnwynHiltFragment": 11,
        "DyrnwynTipFragment": 11,
        "Upgrader6Armor": 11,
        "Upgrader6Weapon": 11,
        # T12 Fader / ash upgraded
        "FaderEmber": 12,
        # T13 DN entry
        "Lingonberry": 13,
        "MooseMeat": 13,
        "MooseHide": 13,
        "MooseSinew": 13,
        "SealBlubber": 13,
        "SealHide": 13,
        "Ice": 13,
        "FrostCore": 13,
        "Frostwood": 13,
        "FirConeFrost": 13,
        "FrozenFuel": 13,
        "Grausten": 13,
        "Kale": 13,
        "KaleSeeds": 13,
        "OatSeeds": 13,
        "Poteitr": 13,
        "PoteitrSeeds": 13,
        "SpiceDeepNorth": 13,
        # T14 Nord base
        "ElakingHairBundle": 14,
        "MoleClaws": 14,
        "BarkaBranch": 14,
        "Gold": 14,
        "GoldOre": 14,
        "Leatherstraps": 14,
        "NornThread": 14,
        "Hook": 14,
        "Upgrader7Armor": 14,
        "Upgrader7Weapon": 14,
        # weapon / key moulds → T14
        "MoldAtgeir": 14,
        "MoldAxe": 14,
        "MoldAxe2H": 14,
        "MoldBow": 14,
        "MoldCrossbow": 14,
        "MoldFistweapon": 14,
        "MoldKeys": 14,
        "MoldKnife": 14,
        "MoldMace": 14,
        "MoldMace2H": 14,
        "MoldShieldBuckler": 14,
        "MoldShieldRound": 14,
        "MoldShieldTower": 14,
        "MoldSpear": 14,
        "MoldStafffrostorbs": 14,
        "MoldStaffOrbofAhri": 14,
        "MoldStaffspiritcaller": 14,
        "MoldStaffthunderblood": 14,
        "MoldSword": 14,
        "MoldSword2H": 14,
        # T15 Mörkhalla / enchanted
        "MemorialCoal": 15,
        "OrbFrostFire": 15,
        "OrbThunderBlood": 15,
        "AncientGemstoneBlack": 15,
        "AncientGemstoneGreen": 15,
        "AncientGemstoneOrange": 15,
        "AncientGemstonePurple": 15,
        "MoldArmorGoldChest": 15,
        "MoldArmorGoldHelmet": 15,
        "MoldArmorGoldLegs": 15,
        "MoldArmorMageChest": 15,
        "MoldArmorMageHelmet": 15,
        "MoldArmorMageLegs": 15,
        "MoldArmormediumChest": 15,
        "MoldArmorMediumHelmet": 15,
        "MoldArmorMediumLegs": 15,
    }
)

REGION_TXT = """
Menu,Tier0
Tier0,Tier1,Crafting,1
Tier1,Tier2,Axes Tier 1,1,Warmth Tier 1,1,Bed Tier 1,1,Cooking Station,1
Tier2,Tier3,Pickaxes Tier 1,1,Smelter,1,Charcoal Kiln,1,Forge,1
Tier3,Tier4,Bronze,1
Tier4,Tier5,Axes Tier 2,1
Tier5,Tier6,Pickaxes Tier 2,1,Boat Tier 2,1
Tier6,Tier7,Pickaxes Tier 3,1
Tier7,Tier8,Artisan Table,1,Blast Furnace,1
Tier8,Tier9,Axes Tier 4,1,Wisp Fountain,1,Wisplight,1
Tier9,Tier10,Pickaxes Tier 4,1,Sap Extractor,1,Eitr Refinery,1,Galdr Table,1
Tier10,Tier11,Boat Tier 4,1,Ceramic Plates,1,Artisan Press,1,Black Forge,1
Tier11,Tier12,Black Forge Upgrade 3,1,Siege,1
Tier12,Tier13,Snow Shovel,1
Tier13,Tier14,Frigid Kiln,1,Frost Foundry,1,Ember Charge,1
Tier14,Tier15,Intricate Key,1
"""


def write_trophies() -> None:
    path = ROOT / "mod" / "trophies.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    out = [lines[0]]
    missing = []
    changed = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        prefab = cols[0]
        if prefab not in TROPHY_TIER:
            missing.append(prefab)
            out.append(line)
            continue
        new_tier = str(TROPHY_TIER[prefab])
        if cols[3] != new_tier:
            changed += 1
        cols[3] = new_tier
        out.append("\t".join(cols))
    if missing:
        raise SystemExit(f"Trophy missing mapping: {missing}")
    text = "\n".join(out) + "\n"
    path.write_text(text, encoding="utf-8")
    (ROOT / "tools" / "trophies.tsv").write_text(text, encoding="utf-8")
    print(f"trophies: {changed} tier changes")


def write_drops() -> list[tuple[str, str, int, int]]:
    path = ROOT / "mod" / "drops.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = []
    body = []
    boss = []
    gather_rows: list[tuple[str, str, int, int]] = []
    missing = []
    changed = 0
    for line in lines:
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            header.append(line)
            continue
        cols = line.split("\t")
        prefab, name, tier, amount = cols[0], cols[1], cols[2], cols[3]
        if len(cols) >= 5 and cols[4] == "boss":
            boss.append(line)  # leave boss rows untouched
            continue
        if prefab not in DROP_TIER:
            missing.append(prefab)
            new_tier = int(tier)
        else:
            new_tier = DROP_TIER[prefab]
            if int(tier) != new_tier:
                changed += 1
        gather_rows.append((prefab, name, new_tier, int(amount)))
        body.append(f"{prefab}\t{name}\t{new_tier}\t{amount}")
    if missing:
        raise SystemExit(f"Drop missing mapping ({len(missing)}): {missing}")
    # Keep original comment header; ensure boss note stays
    text = "\n".join(header + body + boss) + "\n"
    path.write_text(text, encoding="utf-8")
    (ROOT / "tools" / "drops.tsv").write_text(text, encoding="utf-8")
    print(f"drops gather: {changed} tier changes; boss rows left as-is ({len(boss)})")
    return gather_rows


def sync_drops_py(rows: list[tuple[str, str, int, int]]) -> None:
    path = ROOT / "valheimapworld" / "Drops.py"
    py = path.read_text(encoding="utf-8")
    start = py.find("DROP_ROWS = [")
    end = py.find("]\n", start)
    if start < 0 or end < 0:
        raise SystemExit("DROP_ROWS block missing")
    lines = ["DROP_ROWS = ["]
    for prefab, name, tier, amount in rows:
        lines.append(f"    ({prefab!r}, {name!r}, {tier}, {amount}),")
    lines.append("]")
    path.write_text(py[:start] + "\n".join(lines) + py[end + 1 :], encoding="utf-8")
    print(f"Drops.py DROP_ROWS synced ({len(rows)})")


def sync_locations_trophies() -> None:
    path = ROOT / "valheimapworld" / "Locations.py"
    text = path.read_text(encoding="utf-8")
    # Map researchID → tier via trophies file
    id_tier = {}
    for line in (ROOT / "mod" / "trophies.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        if not line.strip():
            continue
        prefab, rid, _boost, tier = line.split("\t")[:4]
        id_tier[rid] = tier

    def repl(m: re.Match) -> str:
        rid = m.group(1)
        tier = id_tier.get(rid)
        if tier is None:
            return m.group(0)
        return f"loc:{rid},Not Missable,Tier{tier}"

    new, n = re.subn(
        r"loc:(researchTrophy\w+),Not Missable,Tier\d+",
        repl,
        text,
    )
    path.write_text(new, encoding="utf-8")
    print(f"Locations.py trophy tiers updated ({n} lines)")


def sync_regions() -> None:
    path = ROOT / "valheimapworld" / "Regions.py"
    text = path.read_text(encoding="utf-8")
    new = re.sub(
        r"region_txt = '''.*?'''",
        "region_txt = '''" + REGION_TXT + "'''",
        text,
        count=1,
        flags=re.S,
    )
    if new == text:
        raise SystemExit("Regions.py region_txt not replaced")
    path.write_text(new, encoding="utf-8")
    print("Regions.py extended to Tier15 (v5.1 doors)")


def main() -> None:
    write_trophies()
    rows = write_drops()
    sync_drops_py(rows)
    sync_locations_trophies()
    sync_regions()


if __name__ == "__main__":
    main()
