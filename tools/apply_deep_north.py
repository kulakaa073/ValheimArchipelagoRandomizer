"""Add Valheim 1.0 / Deep North rows to the randomizer tables and rebuild the apworld lists."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "mod" / "research.tsv"
TROPHIES = ROOT / "mod" / "trophies.tsv"
RECIPES = Path(r"D:/tmp/valheim_recipes.json")
PIECES = Path(r"D:/tmp/piece_tables.json")

APPEND_GATED = {
    "researchWallsWood": [
        "wood_wall_roof_67_a",
        "wood_wall_roof_67_upsidedown",
        "wood_wall_roof_top_67",
    ],
    "researchRoofsWood": [
        "wood_roof_67",
        "wood_roof_top_67",
        "wood_roof_ocorner_67",
        "wood_roof_icorner_67",
    ],
    "researchBeamsWood": ["wood_beam_67"],
    "researchBeamsCorewood": ["wood_log_67"],
    "researchRoofsDarkwood": [
        "darkwood_roof_67",
        "darkwood_roof_top_67",
        "darkwood_roof_ocorner_67",
        "darkwood_roof_icorner_67",
    ],
    "researchBeamsDarkwood": ["darkwood_beam_67"],
    "researchAshwoodWalls": [
        "ashwood_wall_roof_67_a",
        "ashwood_wall_roof_67_upsidedown",
        "ashwood_wall_cross_67",
    ],
    "researchAshwoodBeams": ["ashwood_wall_beam_67"],
    "researchDoorsWood": ["wood_fence", "wood_fence_gate"],
}

# icon, id, name, desc, prereqs, costs, gated, tier, category, comment
NEW_ROWS = [
    ("Shovel", "researchSnowShovel", "Snow Shovel", "", "researchBoatTier4", "FlametalNew:4|FaderEmber:2",
     "Shovel", "11", "Progression", "1.0 tool, gates entry to Tier12 with Siege"),
    ("Iron", "researchIronwoodBeam67", "Ironwood Beam 67", "", "researchPickaxeTier3", "Iron:5",
     "woodiron_beam_67", "6", "Filler", "1.0 angle piece"),
    ("Stone", "researchStoneFence", "Stone Fence", "", "researchStonecutter", "Stone:20",
     "stone_fence", "6", "Filler", "1.0"),
    ("Wood", "researchRoundpole", "Roundpole Fence", "", "researchWorkbench", "Wood:20|RoundLog:5",
     "stake_wall|piece_sharpstakes", "1", "Filler", "1.0 roundpole fence and stakes"),
    ("Wood", "researchDrawbridge", "Drawbridge", "", "researchForgeUpgrade1", "Iron:8|Wood:20",
     "piece_drawbridge|piece_drawbridge_log", "6", "Useful", "1.0"),
    ("Ice", "researchFrostKiln", "Frigid Kiln", "Makes Liquid Frost", "researchSnowShovel|researchSiege", "Ice:10|Stone:10",
     "piece_FrostKiln", "12", "Progression", "Deep North fuel station"),
    ("Gold", "researchFrostFoundry", "Frost Foundry", "Hardens casts into Nord gear", "researchFrostKiln", "Iron:15|Stone:20|FrostCore:10",
     "piece_FrostFoundry", "12", "Progression", "Deep North forge"),
    ("BlackCore", "researchBlackForgeUpgrade5", "Black Forge Upgrade 5", "Smith's Aprons", "researchBlackForgeUpgrade4|researchFrostFoundry", "Gold:5|Leatherstraps:4",
     "blackforge_ext5_apron", "12", "Useful", "1.0"),
    ("Honey", "researchCauldronUpgrade6", "Cauldron Upgrade 6", "Smoker", "researchCauldronUpgrade5|researchFrostKiln", "Iron:5|Ice:4",
     "cauldron_ext7_smoker", "12", "Useful", "1.0"),
    ("StaffIceShards", "researchGaldrTableUpgrade4", "Galdr Table Upgrade 4", "Standing Loom", "researchGaldrTableUpgrade3|researchFrostFoundry", "NornThread:5|Gold:4",
     "piece_magetable_ext4", "12", "Useful", "1.0"),
    ("MooseHide", "researchProtectorArmor", "Protector Armor", "Nord heavy set", "researchFrostFoundry", "Gold:20|MooseHide:8",
     "ArmorGoldHeavyChestUncooked|ArmorGoldHeavyLegsUncooked|ArmorGoldHeavyHelmetUncooked|ArmorDeepNorthHeavyChest|ArmorDeepNorthHeavylegs|HelmetDNHeavy",
     "12", "Useful", "Casts and finished pieces"),
    ("SealHide", "researchVanguardArmor", "Vanguard Armor", "Nord medium set", "researchFrostFoundry", "Gold:12|ElakingHairBundle:8",
     "ArmorGoldMediumChestUncooked|ArmorGoldMediumLegsUncooked|ArmorGoldMediumHelmetUncooked|ArmorDeepNorthMediumChest|ArmorDeepNorthMediumlegs|HelmetDNMediumHood",
     "12", "Useful", ""),
    ("NornThread", "researchCallerArmor", "Caller Armor", "Nord mage set", "researchGaldrTableUpgrade4", "Gold:6|MooseHide:6|NornThread:5",
     "ArmorGoldMageChestUncooked|ArmorGoldMageLegsUncooked|ArmorGoldMageHelmetUncooked|ArmorDeepNorthMageChest|ArmorDeepNorthMagelegs|HelmetDNMage",
     "12", "Useful", ""),
    ("LoxPelt", "researchLoxFurArmor", "Lox Fur Armor", "", "researchFrostKiln", "LoxPelt:5|WrithanRoots:2",
     "ArmorLoxChest|ArmorLoxLegs|HelmetLox", "12", "Useful", "1.0 set"),
    ("Gold", "researchCrownOfValheim", "Crown of Valheim", "", "researchFrostFoundry", "Gold:5|CrownJewel:1",
     "HelmetCrownofValheim", "12", "Useful", ""),
    ("MooseHide", "researchCapeTier9", "Cape Tier 9", "Moose hide cape", "researchCapeTier8|researchFrostFoundry", "MooseHide:6|MooseSinew:2",
     "CapeDeepNorth", "12", "Useful", ""),
    ("SealHide", "researchCapeTier10", "Cape Tier 10", "Cape of the Caller", "researchCapeTier9|researchGaldrTableUpgrade4", "SealHide:6|NornThread:2|Eitr:15",
     "CapeDeepNorthMage", "12", "Useful", ""),
    ("SwordGold", "researchBladesTier9", "Blades Tier 9", "Nord, Frostfire, Thunderblood", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "SwordGoldUncooked|SwordGold|SwordGold_FrostFire|SwordGold_BloodLightning", "12", "Useful", ""),
    ("THSwordGold", "researchLongBladesTier4", "Long Blades Tier 4", "Nord greatsword line", "researchFrostFoundry", "Gold:20|BarkaBranch:2",
     "THSwordGoldUncooked|THSwordGold|THSwordGold_FrostFire|THSwordGold_BloodLightning", "12", "Useful", ""),
    ("AtgeirGold", "researchPolearmsTier5", "Polearms Tier 5", "Nord atgeir line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "AtgeirGoldUncooked|AtgeirGold|AtgeirGold_FrostFire|AtgeirGold_BloodLightning", "12", "Useful", ""),
    ("MaceGold", "researchClubTier8", "Clubs Tier 8", "Nord mace line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "MaceGoldUncooked|MaceGold|MaceGold_FrostFire|MaceGold_BloodLightning", "12", "Useful", ""),
    ("SledgeGold", "researchSledgehammerTier4", "Sledgehammers Tier 4", "Nord sledge line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "SledgeGoldUncooked|SledgeGold|SledgeGold_FrostFire|SledgeGold_BloodLightning", "12", "Useful", ""),
    ("AxeGold", "researchAxeTier6", "Axes Tier 6", "Nord axe line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "AxeGoldUncooked|AxeGold|AxeGold_FrostFire|AxeGold_BloodLightning", "12", "Useful", ""),
    ("BattleaxeGold", "researchBattleaxeTier7", "Battleaxes Tier 7", "Nord greataxe line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "BattleaxeGoldUncooked|BattleaxeGold|BattleaxeGold_FrostFire|BattleaxeGold_BloodLightning", "12", "Useful", ""),
    ("SpearGold", "researchSpearTier8", "Spears Tier 8", "Nord spear line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "SpearGoldUncooked|SpearGold|SpearGold_FrostFire|SpearGold_BloodLightning", "12", "Useful", ""),
    ("KnifeGold", "researchShortBladesTier7", "Short Blades Tier 7", "Nord dagger line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "KnifeGoldUncooked|KnifeGold|KnifeGold_FrostFire|KnifeGold_BloodLightning", "12", "Useful", ""),
    ("FistGold", "researchKnucklesTier4", "Knuckles Tier 4", "Nord knucklechains", "researchFrostFoundry", "Gold:20|MoleClaws:2",
     "FistGoldUncooked|FistGold|FistGold_FrostFire|FistGold_BloodLightning", "12", "Useful", ""),
    ("BowGold", "researchBowsTier8", "Bows Tier 8", "Nord bow line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "BowGoldUncooked|BowGold|BowGold_FrostFire|BowGold_BloodLightning", "12", "Useful", ""),
    ("CrossbowGold", "researchCrossbowsTier4", "Crossbows Tier 4", "Nord crossbow line", "researchFrostFoundry", "Gold:20|Frostwood:10",
     "CrossbowGoldUncooked|CrossbowGold|CrossbowGold_FrostFire|CrossbowGold_BloodLightning", "12", "Useful", ""),
    ("ShieldGold", "researchShieldTier7", "Shields Tier 7", "Nord shield", "researchFrostFoundry", "Gold:15|Frostwood:10",
     "ShieldRoundGoldUncooked|ShieldGold", "12", "Useful", ""),
    ("ShieldGoldBuckler", "researchBucklerTier4", "Bucklers Tier 4", "Nord buckler", "researchFrostFoundry", "Gold:10|Frostwood:10",
     "ShieldBucklerGoldUncooked|ShieldGoldBuckler", "12", "Useful", ""),
    ("ShieldGoldTower", "researchTowerShieldTier5", "Tower Shields Tier 5", "Nord greatshield", "researchFrostFoundry", "Gold:20|Frostwood:20",
     "ShieldTowerGoldUncooked|ShieldGoldTower", "12", "Useful", ""),
    ("WrithanRoots", "researchShieldOfRoots", "Shield of Roots", "", "researchFrostKiln", "FineWood:10|WrithanRoots:1",
     "ShieldRoots", "12", "Useful", "1.0"),
    ("ArrowBloodGold", "researchArrowsTier12", "Arrows Tier 12", "Bloodgold arrows", "researchBowsTier8", "Gold:1|Frostwood:8|Feathers:2",
     "ArrowBloodGold", "12", "Useful", ""),
    ("BoltBloodGold", "researchBoltsTier5", "Bolts Tier 5", "Bloodgold bolts", "researchCrossbowsTier4", "Gold:1|Frostwood:8|Feathers:2",
     "BoltBloodGold", "12", "Useful", ""),
    ("TurretBoltBloodgold", "researchBloodgoldAmmo", "Bloodgold Ammunition", "Missile and catapult payload", "researchFrostFoundry", "Gold:2|Frostwood:10",
     "TurretBoltBloodgold|Catapult_Ammo_BloodGold", "12", "Useful", ""),
    ("StaffFrostOrbs", "researchElementalMagicTier4", "Elemental Magic Tier 4", "Northern Vengeance, Lightning Strike, Echo Spike", "researchGaldrTableUpgrade4", "Ice:10|NornThread:5|Gold:10",
     "StaffFrostOrbsUncooked|StaffFrostOrbs|StaffThunderbloodUncooked|StaffThunderBlood|StaffOrbofAhriUncooked|StaffOrbofAhri",
     "12", "Useful", ""),
    ("StaffSpiritCaller", "researchBloodMagicTier3", "Blood Magic Tier 3", "Spirit Caller", "researchGaldrTableUpgrade4", "BarkaBranch:8|NornThread:5",
     "StaffSpiritCallerUncooked|StaffSpiritCaller", "12", "Useful", ""),
    ("TrinketBloodGoldHealth", "researchTrinketTier7", "Trinkets Tier 7", "Neckstabber and Witch Crown", "researchFrostFoundry", "Gold:5",
     "TrinketBloodGoldHealth|TrinketBloodGoldStamina", "12", "Useful", ""),
    ("GrapplingHook", "researchGrapplingHook", "Grappling Hook", "", "researchFrostFoundry", "YggdrasilWood:10|Eitr:10|Hook:1",
     "GrapplingHook", "12", "Useful", "1.0"),
    ("SaddleMoose", "researchSaddleMoose", "Moose Saddle", "", "researchFrostFoundry", "Gold:4|SealHide:5|Frostwood:5",
     "SaddleMoose", "12", "Useful", ""),
    ("KeysGoldUncooked", "researchIntricateKey", "Intricate Key", "", "researchFrostFoundry", "Gold:5",
     "KeysGoldUncooked", "12", "Useful", "Cast; Frost Foundry finishes it"),
    ("Ice", "researchSnowball", "Snowball", "", "researchFrostKiln", "Ice:5",
     "Snowball", "12", "Filler", ""),
    ("BombDynamite", "researchEmberCharge", "Ember Charge", "", "researchFrostKiln", "SealHide:2|FaderEmber:1",
     "BombDynamite", "12", "Useful", "1.0 bomb"),
    ("Frostwood", "researchTimberWalls", "Timber Walls", "", "researchFrostKiln", "Frostwood:20",
     "stave_wall_2x2|stave_gate", "12", "Filler", ""),
    ("Frostwood", "researchTimberBeams", "Timber Beams", "", "researchFrostKiln", "Frostwood:20",
     "stave_pole_2m|stave_pole_4m|stave_beam_2m|stave_beam_4m|stave_beam_26|stave_beam_45|stave_beam_67|stave_wall_cross_26|stave_wall_cross_45|stave_wall_cross_67",
     "12", "Filler", ""),
    ("Frostwood", "researchTimberDecor", "Timber Decor", "", "researchTimberBeams", "Frostwood:10",
     "stave_deco_wall_2x2|stave_deco_pole_2m|stave_deco_beam_2m|stave_deco_beam_26|stave_deco_beam_45|stave_deco_beam_67",
     "12", "Filler", ""),
    ("ScaleHide", "researchScalewoodWalls", "Scalewood Walls", "", "researchFrostKiln", "ScaleHide:10|Frostwood:10",
     "scale_quarterwall_1x1|scale_halfwall_1x2|scale_wall_2x2|scale_wall_roof_26|scale_wall_roof_26_flipped|scale_wall_roof_45|scale_wall_roof_45_flipped|scale_wall_roof_67|scale_wall_roof_67_flipped|scale_wall_roof_26_upsidedown|scale_wall_roof_26_upsidedown_flipped|scale_wall_roof_45_upsidedown|scale_wall_roof_45_upsidedown_flipped|scale_wall_roof_67_upsidedown|scale_wall_roof_67_upsidedown_flipped",
     "12", "Filler", ""),
    ("MooseHide", "researchDeepNorthFurniture", "Deep North Furniture", "", "researchFrostKiln", "MooseHide:4|SealHide:4|Gold:2",
     "piece_moose_throne|rug_moose|rug_seal|piece_chest_grausten|piece_chest_warderobe|piece_bench_runed|piece_chair_runed|piece_table_runed|piece_table_runed_small|piece_birdnest|piece_EternalPyre|piece_hoodedlantern|piece_snowlantern|piece_icecube",
     "12", "Filler", "1.0 furniture and ice block"),
    ("Gold", "researchStorageTier5", "Storage Tier 5", "Metal, flint, timber and bloodgold stacks", "researchStorageTier4|researchFrostFoundry", "Gold:5|Frostwood:10",
     "bar_tin_stack|bar_copper_stack|bar_bronze_stack|bar_iron_stack|bar_silver_stack|bar_blackmetal_stack|bar_flametal_stack|bar_gold_stack|flint_pile|wood_frost_stack",
     "12", "Useful", "1.0 stacks"),
    ("Kale", "researchDeepNorthCrops", "Deep North Crops", "Kale, oats, poteitr, timberwood sapling", "researchCultivator|researchFrostKiln", "KaleSeeds:3|OatSeeds:3|PoteitrSeeds:3",
     "sapling_Kale|sapling_seedkale|sapling_oat|sapling_poteitr|FirTree_big_Sapling", "12", "Useful", ""),
    ("CookedMooseMeat", "researchDeepNorthCooking", "Deep North Cooking", "", "researchCauldronUpgrade6", "Kale:4|Oat:4|Lingonberry:4|MooseMeat:2",
     "BakedPoteitrUncooked|KaleChipsUncooked|Lingondricka|MeatballsMashedPoteitr|MooseKebab|OatmealLingonberryJam|Pancakes|OvenPancakeUncooked|SealSoup|SmokedFish|SmokedMooseMeat|FishSoup|OatMilk",
     "12", "Useful", ""),
    ("FeastDeepNorth_Material", "researchNorthernFeast", "Northern Feast", "", "researchDeepNorthCooking", "CookedMooseMeat:3|Poteitr:5|SpiceDeepNorth:1",
     "FeastDeepNorth_Material|FeastDeepNorth", "12", "Useful", ""),
    ("CookedBjornMeat", "researchPulledBear", "Pulled Bear", "", "researchCookingStation", "CookedBjornMeat:1|Carrot:2",
     "PulledBear", "1", "Useful", "1.0 black forest food"),
    ("Bread", "researchMeatInBread", "Meat In Bread", "", "researchCauldronUpgrade2", "BreadDough:2",
     "FishAndBreadUncooked", "7", "Useful", "1.0"),
]

NEW_TROPHIES = [
    ("TrophyBarka", "researchTrophyBarka", "Attack", "12"),
    ("TrophyMole", "researchTrophyMole", "Attack", "12"),
    ("TrophyFrostTroll", "researchTrophyFrostTroll", "Defense", "1"),
    ("TrophyWrithan", "researchTrophyWrithan", "Defense", "12"),
    ("TrophyBlob_Frost", "researchTrophyFrostBlob", "HP", "7"),
    ("TrophyBlob_Lava", "researchTrophyLavaBlob", "HP", "11"),
    ("TrophyBlob_Morkhalla", "researchTrophyMorkhallaBlob", "HPRegen", "12"),
    ("TrophyMoose", "researchTrophyMoose", "Load", "12"),
    ("TrophySeal", "researchTrophySeal", "Stamina", "12"),
    ("TrophyJotunWarrior", "researchTrophyKrigen", "StaminaRegen", "12"),
    ("TrophyJotunWitch", "researchTrophyHexen", "Eitr", "12"),
    ("TrophyElaking", "researchTrophyElaking", "HP", "12"),
]


def load_known() -> set[str]:
    known = set()
    if RECIPES.exists():
        for row in json.loads(RECIPES.read_text(encoding="utf-8")):
            if row.get("item"):
                known.add(row["item"])
    if PIECES.exists():
        tables = json.loads(PIECES.read_text(encoding="utf-8"))
        for pieces in tables.values():
            known.update(p for p in pieces if p)
    trophy_list = Path(r"D:/tmp/interesting_paths.txt")
    if trophy_list.exists():
        for line in trophy_list.read_text(encoding="utf-8").splitlines():
            base = line.strip().split("/")[-1]
            if base.startswith("Trophy") and base.endswith(".prefab"):
                known.add(base[:-7])
    return known


def patch_research(text: str) -> str:
    text = text.replace("BjronPaw", "BjornPaw").replace("researchWarhmth1", "researchWarmthTier1")
    lines = text.splitlines()
    out = []
    for line in lines:
        if not line or line.startswith("#"):
            out.append(line)
            continue
        cols = line.split("\t")
        if len(cols) >= 9 and cols[1] == "researchSiege":
            cols[8] = "Progression"
        if len(cols) >= 7 and cols[1] == "researchWallsWood":
            cols[6] = "|".join("wood_wall_roof_a" if g == "wood_wall_roof" else g for g in cols[6].split("|"))
        if len(cols) >= 7 and cols[1] in APPEND_GATED:
            extra = [g for g in APPEND_GATED[cols[1]] if g not in cols[6].split("|")]
            if extra:
                cols[6] = cols[6] + "|" + "|".join(extra)
        out.append("\t".join(cols))
    for row in NEW_ROWS:
        out.append("\t".join(row))
    return "\n".join(out) + "\n"


def patch_trophies(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    have = {ln.split("\t")[0] for ln in lines[1:]}
    for row in NEW_TROPHIES:
        if row[0] not in have:
            lines.append("\t".join(row))
    return "\n".join(lines) + "\n"


def validate(research_text: str, trophy_text: str, known: set[str]) -> None:
    new_ids = {row[1] for row in NEW_ROWS}
    ids = []
    names = []
    missing = []
    for line in research_text.splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 9:
            raise SystemExit(f"short research row: {line}")
        ids.append(cols[1])
        names.append(cols[2])
        if cols[1] in new_ids:
            for gated in cols[6].split("|"):
                if gated and gated not in known:
                    missing.append((cols[1], gated))
    dup_ids = sorted({i for i in ids if ids.count(i) > 1})
    dup_names = sorted({n for n in names if names.count(n) > 1})
    idset = set(ids)
    bad_pre = []
    for line in research_text.splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        for pre in filter(None, cols[4].split("|")):
            if pre not in idset:
                bad_pre.append((cols[1], pre))
    troph_ids = []
    for line in trophy_text.splitlines()[1:]:
        cols = line.split("\t")
        troph_ids.append(cols[1])
        if cols[1] in {row[1] for row in NEW_TROPHIES} and cols[0] not in known:
            missing.append((cols[1], cols[0]))
    problems = []
    if dup_ids:
        problems.append(f"duplicate research ids: {dup_ids}")
    if dup_names:
        problems.append(f"duplicate display names: {dup_names}")
    if bad_pre:
        problems.append(f"missing prereqs: {bad_pre}")
    if missing:
        problems.append("unknown gated prefabs:\n  " + "\n  ".join(f"{a} -> {b}" for a, b in missing))
    overlap = set(ids) & set(troph_ids)
    if overlap:
        problems.append(f"research/trophy id overlap: {overlap}")
    if problems:
        raise SystemExit("\n".join(problems))


def rebuild_apworld(research_text: str, trophy_text: str) -> None:
    max_tier = 12
    research_rows = []
    for line in research_text.splitlines():
        if not line or line.startswith("#"):
            continue
        research_rows.append(line.split("\t"))
    trophy_rows = []
    for i, line in enumerate(trophy_text.splitlines()):
        if i == 0 or not line.strip():
            continue
        trophy_rows.append(line.split("\t"))

    tier_items = {t: [] for t in range(max_tier + 1)}
    for row in research_rows:
        if row[8] == "Progression":
            tier = min(max_tier, int(row[7]))
            tier_items[tier].append(row[2])

    region_lines = ["Menu,Tier0"]
    for tier in range(max_tier):
        parts = [f"Tier{tier}", f"Tier{tier + 1}"]
        for name in tier_items[tier]:
            parts.extend([name, "1"])
        region_lines.append(",".join(parts))

    item_lines = ["// Item User Friendly Name,ID,Count,Type,Classification"]
    loc_lines = ["// Location Type,User Friendly Name,ID,Classification,Region"]
    for row in research_rows:
        item_lines.append(f"{row[2]},item:{row[1]},1,Item,{row[8]}")
        loc_lines.append(f"Research,{row[2]},loc:{row[1]},Not Missable,Tier{row[7]}")
    for row in trophy_rows:
        friendly = f"Trophy: {row[0]}"
        item_lines.append(f"{friendly},item:{row[1]},1,Item,Useful")
        loc_lines.append(f"Trophy,{friendly},loc:{row[1]},Not Missable,Tier{row[3]}")

    world = ROOT / "valheimapworld"
    replace_blob(world / "Items.py", "items_txt = '''", "'''", "\n".join(item_lines))
    replace_blob(world / "Locations.py", "locations_txt = '''", "'''", "\n".join(loc_lines))
    replace_blob(world / "Regions.py", "region_txt = '''", "'''", "\n".join(region_lines))

    parser = (ROOT / "tools" / "Program.cs").read_text(encoding="utf-8")
    parser = parser.replace("const int MaxTier = 11;", "const int MaxTier = 12;")
    (ROOT / "tools" / "Program.cs").write_text(parser, encoding="utf-8")

    apworld = world / "valheimapworld.apworld"
    with zipfile.ZipFile(apworld, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("__init__.py", "Items.py", "Locations.py", "Regions.py"):
            zf.write(world / name, f"valheimapworld/{name}")
    print(f"researches {len(research_rows)} trophies {len(trophy_rows)} regions {len(region_lines)}")
    print("Tier11->12", region_lines[-1])


def replace_blob(path: Path, start: str, end: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    a = text.find(start)
    if a < 0:
        raise SystemExit(f"missing start marker in {path}")
    b = text.find(end, a + len(start))
    if b < 0:
        raise SystemExit(f"missing end marker in {path}")
    path.write_text(text[: a + len(start)] + "\n" + body + "\n" + text[b:], encoding="utf-8")


def main() -> None:
    known = load_known()
    research = patch_research(RESEARCH.read_text(encoding="utf-8"))
    trophies = patch_trophies(TROPHIES.read_text(encoding="utf-8"))
    validate(research, trophies, known)
    RESEARCH.write_text(research, encoding="utf-8")
    TROPHIES.write_text(trophies, encoding="utf-8")
    (ROOT / "mod").joinpath("research.tsv").write_text(research, encoding="utf-8")
    rebuild_apworld(research, trophies)
    # keep the copies that ship with the mod and the apworld folder in sync
    (ROOT / "tools" / "research.tsv").write_text(research, encoding="utf-8")
    (ROOT / "tools" / "trophies.tsv").write_text(trophies, encoding="utf-8")
    print("updated", RESEARCH)


if __name__ == "__main__":
    main()
