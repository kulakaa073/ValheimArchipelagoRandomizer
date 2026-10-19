import re
from pathlib import Path

src = Path(__file__).resolve().parents[1] / "mod" / "research.tsv"
out = Path(__file__).resolve().parents[1] / "research-unlocks.md"

rows = []
for ln in src.read_text(encoding="utf-8").splitlines():
    if not ln.strip() or ln.startswith("#") or ln.startswith("icon"):
        continue
    cols = ln.split("\t")
    while len(cols) < 9:
        cols.append("")
    rows.append(cols)

by_id = {cols[1]: cols[2] for cols in rows}

NAMES = {
    "Amber": "Amber",
    "AmberPearl": "Amber pearl",
    "AncientSeed": "Ancient seed",
    "AskBladder": "Asksvin bladder",
    "AskHide": "Ask hide",
    "AsksvinCarrionNeck": "Asksvin neck",
    "AsksvinCarrionPelvic": "Asksvin pelvis",
    "AsksvinCarrionRibcage": "Asksvin ribcage",
    "AsksvinCarrionSkull": "Asksvin skull",
    "BarkaBranch": "Barka branch",
    "Barley": "Barley",
    "Bilebag": "Bilebag",
    "BjornHide": "Bear hide",
    "BjornPaw": "Bear paw",
    "BlackCore": "Black core",
    "BlackMarble": "Black marble",
    "BlackMetalScrap": "Black metal scrap",
    "Bloodbag": "Bloodbag",
    "Blueberries": "Blueberries",
    "BoneFragments": "Bone fragments",
    "BonemawSerpentTooth": "Bonemaw tooth",
    "BreadDough": "Bread dough",
    "Carrot": "Carrot",
    "CarrotSeeds": "Carrot seeds",
    "Chain": "Chain",
    "CharcoalResin": "Charcoal resin",
    "CharredBone": "Charred bone",
    "Chitin": "Chitin",
    "Cloudberry": "Cloudberries",
    "Coins": "Coins",
    "CookedBjornMeat": "Cooked bear meat",
    "CookedMooseMeat": "Cooked moose meat",
    "Copper": "Copper",
    "CopperOre": "Copper ore",
    "CrownJewel": "Crown jewel",
    "Crystal": "Crystal",
    "Dandelion": "Dandelion",
    "DeerHide": "Deer hide",
    "DvergrNeedle": "Dvergr extractor",
    "Ectoplasm": "Ectoplasm",
    "Eitr": "Eitr",
    "ElakingHairBundle": "Elaking hair",
    "ElderBark": "Ancient bark",
    "Entrails": "Entrails",
    "FaderEmber": "Fader ember",
    "Feathers": "Feathers",
    "Fiddleheadfern": "Fiddlehead",
    "FineWood": "Fine wood",
    "Finewood": "Fine wood",
    "FlametalNew": "Flametal",
    "Flax": "Flax",
    "Flint": "Flint",
    "FreezeGland": "Freeze gland",
    "FrostCore": "Frost core",
    "Frostwood": "Frostwood",
    "GiantBloodSack": "Giant blood sack",
    "Gold": "Gold",
    "GreydwarfEye": "Greydwarf eye",
    "Guck": "Guck",
    "Honey": "Honey",
    "Hook": "Hook",
    "Ice": "Ice",
    "Iron": "Iron",
    "JuteBlue": "Blue jute",
    "JuteRed": "Red jute",
    "Kale": "Kale",
    "KaleSeeds": "Kale seeds",
    "LeatherScraps": "Leather scraps",
    "Leatherstraps": "Leather straps",
    "Lingonberry": "Lingonberries",
    "LoxPelt": "Lox pelt",
    "Mandible": "Mandible",
    "MoleClaws": "Mole claws",
    "MoltenCore": "Molten core",
    "MooseHide": "Moose hide",
    "MooseMeat": "Moose meat",
    "MooseSinew": "Moose sinew",
    "MorgenHeart": "Morgen heart",
    "Mushroom": "Mushroom",
    "MushroomJotunPuffs": "Jotun puffs",
    "MushroomMagecap": "Magecap",
    "MushroomSmokePuff": "Smoke puff",
    "MushroomYellow": "Yellow mushroom",
    "MusroomYellow": "Yellow mushroom",
    "Needle": "Needle",
    "NornThread": "Norn thread",
    "Oat": "Oats",
    "OatSeeds": "Oat seeds",
    "Obsidian": "Obsidian",
    "Ooze": "Ooze",
    "Pot_Shard_Green": "Green pot shard",
    "Poteitr": "Poteitr",
    "PoteitrSeeds": "Poteitr seeds",
    "ProustitePowder": "Proustite powder",
    "Raspberry": "Raspberries",
    "Resin": "Resin",
    "Root": "Root",
    "RoundLog": "Core wood",
    "RoyalJelly": "Royal jelly",
    "Ruby": "Ruby",
    "Sap": "Sap",
    "ScaleHide": "Scale hide",
    "SealHide": "Seal hide",
    "SilverNecklace": "Silver necklace",
    "SilverOre": "Silver ore",
    "Softtissue": "Soft tissue",
    "SpiceDeepNorth": "Deep North spice",
    "Stone": "Stone",
    "SulfurStone": "Sulfur",
    "SurtlingCore": "Surtling core",
    "Thistle": "Thistle",
    "Tin": "Tin",
    "TinOre": "Tin ore",
    "TrollHide": "Troll hide",
    "TurnipSeeds": "Turnip seeds",
    "UndeadBjornRibcage": "Undead bear ribcage",
    "Vineberry": "Vineberry",
    "Wisp": "Wisp",
    "WitheredBone": "Withered bone",
    "WolfClaw": "Wolf claw",
    "WolfFang": "Wolf fang",
    "WolfHairBundle": "Wolf hair",
    "WolfPelt": "Wolf pelt",
    "Wood": "Wood",
    "WrithanRoots": "Writhing roots",
    "YggdrasilWood": "Yggdrasil wood",
    "piece_workbench": "Workbench",
    "piece_workbench_ext1": "Chopping block",
    "piece_workbench_ext2": "Tanning rack",
    "piece_workbench_ext3": "Adze",
    "piece_workbench_ext4": "Tool shelf",
    "forge": "Forge",
    "smelter": "Smelter",
    "charcoal_kiln": "Charcoal kiln",
    "blastfurnace": "Blast furnace",
    "windmill": "Windmill",
    "piece_spinningwheel": "Spinning wheel",
    "piece_artisanstation": "Artisan table",
    "piece_stonecutter": "Stonecutter",
    "piece_cauldron": "Cauldron",
    "fermenter": "Fermenter",
    "piece_oven": "Stone oven",
    "piece_cookingstation": "Cooking station",
    "Piece_ironcookingstation": "Iron cooking station",
    "piece_preptable": "Food preparation table",
    "blackforge": "Black forge",
    "blackforge_ext2_vise": "Black forge vise",
    "blackforge_ext3_metalcutter": "Black forge metal cutter",
    "blackforge_ext4_gemcutter": "Black forge gem cutter",
    "blackforge_ext5_apron": "Black forge apron",
    "eitrrefinery": "Eitr refinery",
    "piece_magetable": "Galdr table",
    "piece_FrostFoundry": "Frost foundry",
    "piece_FrostKiln": "Frigid kiln",
    "piece_MeadCauldron": "Mead cauldron",
    "piece_EternalPyre": "Eternal pyre",
    "piece_beehive": "Beehive",
    "piece_sapcollector": "Sap extractor",
    "piece_wisplure": "Wisp fountain",
    "portal_wood": "Portal",
    "portal_stone": "Stone portal",
    "bed": "Bed",
    "piece_bed02": "Dragon bed",
    "piece_chest": "Reinforced chest",
    "piece_chest_wood": "Chest",
    "piece_chest_barrel": "Barrel",
    "piece_chest_blackmetal": "Black metal chest",
    "piece_chest_grausten": "Grausten chest",
    "piece_chest_warderobe": "Wardrobe",
    "bonfire": "Bonfire",
    "fire_pit": "Campfire",
    "hearth": "Hearth",
    "piece_hoodedlantern": "Hooded lantern",
    "piece_snowlantern": "Snow lantern",
    "piece_icecube": "Ice cube",
    "piece_bench_runed": "Runed bench",
    "piece_chair_runed": "Runed chair",
    "piece_table_runed": "Runed table",
    "piece_table_runed_small": "Small runed table",
    "piece_moose_throne": "Moose throne",
    "piece_birdnest": "Bird nest",
    "Cart": "Cart",
    "Raft": "Raft",
    "Karve": "Karve",
    "VikingShip": "Longship",
    "VikingShip_Ashlands": "Drakkar",
    "SaddleMoose": "Moose saddle",
    "Hoe": "Hoe",
    "Cultivator": "Cultivator",
    "Shovel": "Shovel",
    "Scythe": "Scythe",
    "GrapplingHook": "Grappling hook",
    "Demister": "Dvergr lantern",
    "BatteringRam": "Battering ram",
    "Catapult": "Catapult",
    "stake_wall": "Stakewall",
    "piece_sharpstakes": "Sharp stakes",
    "piece_dvergr_stake_wall": "Dvergr stakewall",
    "piece_dvergr_sharpstakes": "Dvergr sharp stakes",
    "stone_fence": "Stone wall",
    "piece_drawbridge": "Drawbridge",
    "piece_drawbridge_log": "Log drawbridge",
    "piece_hexagonal_door": "Hexagonal door",
    "piece_dvergr_spiralstair": "Spiral stair",
    "piece_dvergr_spiralstair_right": "Spiral stair (right)",
    "cauldron_ext1_spice": "Spice rack",
    "cauldron_ext3_butchertable": "Butcher table",
    "cauldron_ext4_pots": "Pots and pans",
    "cauldron_ext5_mortarandpestle": "Mortar and pestle",
    "cauldron_ext6_rollingpins": "Rolling pins",
    "cauldron_ext7_smoker": "Smoker",
    "sapling_Kale": "Kale sapling",
    "sapling_oat": "Oat sapling",
    "sapling_poteitr": "Poteitr sapling",
    "sapling_seedkale": "Kale seed sapling",
    "FirTree_big_Sapling": "Fir sapling",
    "rug_moose": "Moose rug",
    "rug_seal": "Seal rug",
    "wood_stack": "Wood stack",
    "wood_fine_stack": "Fine wood stack",
    "wood_core_stack": "Core wood stack",
    "wood_yggdrasil_stack": "Yggdrasil wood stack",
    "wood_frost_stack": "Frostwood stack",
    "blackwood_stack": "Ashwood stack",
    "stone_pile": "Stone pile",
    "coal_pile": "Coal pile",
    "flint_pile": "Flint pile",
    "grausten_pile": "Grausten pile",
    "blackmarble_pile": "Black marble pile",
    "bone_stack": "Bone stack",
    "skull_pile": "Skull pile",
    "treasure_pile": "Treasure pile",
    "treasure_stack": "Treasure stack",
    "bar_copper_stack": "Copper stack",
    "bar_tin_stack": "Tin stack",
    "bar_bronze_stack": "Bronze stack",
    "bar_iron_stack": "Iron stack",
    "bar_silver_stack": "Silver stack",
    "bar_blackmetal_stack": "Black metal stack",
    "bar_flametal_stack": "Flametal stack",
    "bar_gold_stack": "Gold stack",
    "Club": "Club",
    "Torch": "Torch",
    "AxeStone": "Stone axe",
    "AxeFlint": "Flint axe",
    "SwordWood": "Wooden sword",
    "Bow": "Crude bow",
    "ArrowWood": "Wood arrow",
    "ShieldWood": "Wood shield",
    "ShieldWoodTower": "Wood tower shield",
    "ShieldBoneTower": "Bone tower shield",
    "PickaxeAntler": "Antler pickaxe",
    "Bronze": "Bronze",
    "BronzeNails": "Bronze nails",
    "IronNails": "Iron nails",
    "ArmorRagsChest": "Rag tunic",
    "ArmorRagsLegs": "Rag pants",
    "CapeDeerHide": "Deer hide cape",
    "CapeTrollHide": "Troll hide cape",
    "CapeWolf": "Wolf fur cape",
    "CapeLox": "Lox cape",
    "CapeLinen": "Linen cape",
    "CapeFeather": "Feather cape",
    "CapeAsh": "Ask cape",
    "CapeAsksvin": "Asksvin cape",
}


def pretty(pid: str) -> str:
    if pid in NAMES:
        return NAMES[pid]
    text = pid
    text = text.replace("Uncooked", " (uncooked)")
    text = text.replace("_BloodLightning", " (blood lightning)")
    text = text.replace("_FrostFire", " (frost fire)")
    text = text.replace("BloodLightning", " (blood lightning)")
    text = text.replace("FrostFire", " (frost fire)")
    if text.startswith("THSword"):
        text = "Two-handed sword " + text[len("THSword") :]
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    text = text.replace("_", " ")
    text = text.replace("upsidedown", "upside down")
    text = text.replace("icorner", "inner corner")
    text = text.replace("ocorner", "outer corner")
    text = text.replace("woodwall", "wood wall")
    text = re.sub(r"\s+", " ", text).strip()
    words = []
    for word in text.split(" "):
        if not word:
            continue
        if word.startswith("(") or word.endswith(")") or word[0].isdigit():
            words.append(word)
        else:
            words.append(word[0].upper() + word[1:])
    return " ".join(words)


def mats(raw: str) -> str:
    if not raw.strip():
        return "None"
    parts = []
    for bit in raw.split("|"):
        if not bit:
            continue
        name, amount = bit.split(":") if ":" in bit else (bit, "1")
        parts.append(f"{amount} {pretty(name)}")
    return ", ".join(parts)


def unlocks(raw: str) -> str:
    ids = [gate for gate in raw.split("|") if gate]
    if not ids:
        return "Nothing"
    return ", ".join(pretty(gate) for gate in ids)


def cond(raw: str) -> str:
    ids = [part for part in raw.split("|") if part]
    if not ids:
        return "None. Shows once its materials have been picked up."
    names = [by_id.get(part, part) for part in ids]
    return "Requires " + ", ".join(names)


def main() -> None:
    lines = [
        "# Research recipes",
        "",
        "278 researches from `research.tsv`. This table is the parent chain, used when `research_access` is `default`. Meadow gathering only reveals a recipe whose unlock condition is **None**. The other 273 stay hidden until every research named in the unlock condition has been received from Archipelago. Crafting a research sends its check. It does not open the next recipe by itself.",
        "",
        "The seed can use a different rule. `tier` shows every recipe in a tier once that tier's door items are received. `materials` shows a recipe once its materials have been found. `natural` opens the next recipes when you craft a research. Receiving that research leaves the next recipes closed, and the received item grants the gear. `sequential_tiers` places each tier's door items in the previous tier.",
        "",
        "The five with no earlier research are Crafting, Clubs Tier 1, Lighting Tier 1, Axes Tier 1, and Warmth Tier 1. Receiving **Crafting** is what opens the next 23 bench recipes.",
        "",
        "| Research | Unlock condition | Materials | Unlocks |",
        "|---|---|---|---|",
    ]
    for cols in rows:
        lines.append(
            "| {name} | {condition} | {material} | {opened} |".format(
                name=cols[2].replace("|", "/"),
                condition=cond(cols[4]).replace("|", "/"),
                material=mats(cols[5]).replace("|", "/"),
                opened=unlocks(cols[6]).replace("|", "/"),
            )
        )
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(rows)} rows)")


if __name__ == "__main__":
    main()
