"""Build proposed research overhaul list for review (v5 — audit fixes)."""
import csv
import json
from collections import Counter
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSV = ROOT / "mod" / "research.tsv"
OUT_JSON = Path(__file__).with_name("_proposed_research.json")

header = (
    "iconFromItemPrefab\tresearchItemID\tdisplayName\tdescription\trequiredResearchIDs\t"
    "researchRecipeRequirements\tgatedItemPrefabIDs\ttier\tcategory\tdevComment"
)

content = TSV.read_text(encoding="utf-8-sig")
rows = list(
    csv.DictReader(
        StringIO(
            header
            + "\n"
            + "\n".join(
                l for l in content.splitlines() if l.strip() and not l.lstrip().startswith("#")
            )
        ),
        delimiter="\t",
    )
)

TIER_LABELS = {
    0: "Bootstrap",
    1: "Meadows",
    2: "Eikthyr / BF prep",
    3: "Black Forest (smelting + BF gear)",
    4: "Bronze (clean copper/tin)",
    5: "Finewood / pre-Swamp",
    6: "Swamp / Iron (Bonemass)",
    7: "Mountains (Moder)",
    8: "Plains (Yagluth)",
    9: "Mistlands entry",
    10: "Mistlands deep (Queen)",
    11: "Ashlands base",
    12: "Ashlands upgraded (Fader)",
    13: "Deep North entry",
    14: "Deep North Nord base (pre-Mörkhalla)",
    15: "Deep North Mörkhalla / enchanted (Kall)",
}

# Door INTO tier -> items living in previous tier
DOORS_INTO = {
    1: ["Crafting"],
    2: ["Axes Tier 1", "Warmth Tier 1", "Bed Tier 1", "Cooking Station"],
    3: ["Pickaxes Tier 1", "Smelter", "Charcoal Kiln", "Forge"],
    4: ["Bronze"],
    5: ["Axes Tier 2"],  # cost must drop swamp mats (Chitin/Guck)
    6: ["Pickaxes Tier 2", "Boat Tier 2"],
    7: ["Pickaxes Tier 3"],  # Cooler is SoftProg, not mountain door
    8: ["Artisan Table", "Blast Furnace"],
    9: ["Axes Tier 4", "Wisp Fountain", "Wisplight"],
    10: ["Pickaxes Tier 4", "Sap Extractor", "Eitr Refinery", "Galdr Table"],
    11: ["Boat Tier 4", "Ceramic Plates", "Artisan Press", "Black Forge"],
    12: ["Black Forge Upgrade 3", "Siege"],
    13: ["Snow Shovel"],
    14: ["Frigid Kiln", "Frost Foundry", "Ember Charge"],
    15: ["Intricate Key"],
}

DOOR_ITEMS = {n for names in DOORS_INTO.values() for n in names}

SOFT = {
    "Boat Tier 1",
    "Nails Tier 1",  # bronze nails — same BF tier as cart
    "Nails Tier 2",
    "Transportation Tier 1",  # cart
    "Transportation Tier 2",  # wood portal — pre-swamp T5
    "Transportation Tier 3",
    "Cauldron",
    "Grappling Hook",
    "Black Forge Upgrade 1",
    "Black Forge Upgrade 2",
    "Black Forge Upgrade 4",
    "Black Forge Upgrade 5",
    "Galdr Table Upgrade 1",
    "Galdr Table Upgrade 2",
    "Galdr Table Upgrade 3",  # role consistency with other Galdr ups
    "Galdr Table Upgrade 4",
    "Spinning Wheel",
    "Boat Tier 3",
    "Forge Upgrade 1",  # Cooler — SoftProg, not tier door
}

# Explicit placements (v5 — audit pass)
EXPLICIT_TIER = {
    # T0
    "Crafting": 0,
    "Clubs Tier 1": 0,
    "Lighting Tier 1": 0,
    # T1 Meadows — no troll/bear
    "Axes Tier 1": 1,
    "Warmth Tier 1": 1,
    "Bed Tier 1": 1,
    "Cooking Station": 1,
    "Boat Tier 1": 1,
    "Rag Armor": 1,
    "Cape Tier 1": 1,
    "Leather Armor": 1,
    "Blades Tier 1": 1,
    "Spears Tier 1": 1,
    "Short Blades Tier 1": 1,
    "Bows Tier 1": 1,
    "Arrows Tier 1": 1,
    "Shields Tier 1": 1,
    "Tower Shields Tier 1": 1,
    "Beekeping": 1,
    "Wooden Floors": 1,
    "Wooden Stairs": 1,
    "Wooden Walls": 1,
    "Wooden Roofs": 1,
    "Wooden Beams": 1,
    "Wooden Doors": 1,
    "Storage Tier 1": 1,
    "Storage Tier 2": 1,
    "Workbench Upgrade 1": 1,
    "Workbench Upgrade 2": 1,
    "Roundpole Fence": 1,
    # T2 Eikthyr / BF prep
    "Pickaxes Tier 1": 2,
    "Smelter": 2,
    "Charcoal Kiln": 2,
    "Forge": 2,
    "Sledgehammers Tier 1": 2,
    "Corewood Beams": 2,
    # T3 Black Forest — troll/bear + cart/nails/bronze armor/cultivator
    "Bronze": 3,
    "Troll Armor": 3,
    "Cape Tier 2": 3,
    "Bear Armor": 3,
    "Knuckles Tier 1": 3,
    "Pulled Bear": 3,
    "Cauldron": 3,
    "Bronze Armor": 3,
    "Cultivator": 3,
    "Nails Tier 1": 3,  # with cart (was T4 — cart-before-nails fix)
    "Transportation Tier 1": 3,  # cart
    "Darkwood Beams": 3,
    "Darkwood Decorations": 3,
    "Darkwood Roofs": 3,
    "Hoe": 3,
    "Arrows Tier 2": 3,
    # T4 Bronze — full bronze weapon/tool set + Anvils
    "Axes Tier 2": 4,  # DOOR
    "Short Blades Tier 2": 4,
    "Clubs Tier 2": 4,  # was wrongly T6
    "Blades Tier 2": 4,
    "Spears Tier 2": 4,
    "Polearms Tier 1": 4,
    "Bucklers Tier 1": 4,
    "Trinkets Tier 1": 4,
    "Arrows Tier 3": 4,  # bronze arrows
    "Mead ketill": 4,
    "Knife Butcher": 4,
    "Harpoon": 4,
    "Celebratory Cap": 4,
    "Pointy Hat": 4,
    "Forge Upgrade 3": 4,  # Anvils (forge_ext2) — Wood+Bronze; prereq rewired
    # T5 Finewood — portal soft + finewood station ups
    "Pickaxes Tier 2": 5,
    "Boat Tier 2": 5,
    "Transportation Tier 2": 5,
    "Bonfire": 5,
    "Bows Tier 2": 5,
    "Fermenter": 5,
    "Shields Tier 2": 5,
    "Short Blades Tier 3": 5,
    "Workbench Upgrade 3": 5,  # Adze — Finewood+Bronze
    "Forge Upgrade 1": 5,  # Cooler (forge_ext5) — Finewood+Copper; SoftProg
    # T6 Swamp / Iron — iron forge ups, WrithanRoots gear, spice rack
    "Pickaxes Tier 3": 6,
    "Nails Tier 2": 6,
    "Boat Tier 3": 6,
    "Root Armor": 6,
    "Shield of Roots": 6,  # WrithanRoots = swamp drop
    "Cauldron Upgrade 1": 6,  # Spice Rack — Turnip
    "Forge Upgrade 2": 6,  # Bellows — Chain
    "Forge Upgrade 4": 6,  # Smith's Anvil — Iron
    "Forge Upgrade 5": 6,  # Toolrack — Iron
    "Forge Upgrade 6": 6,  # Grinding Wheel — Sharpening Stone
    "Stonecutter": 6,
    "Iron Cooking Station": 6,
    "Food Preparation Table": 6,
    "Hearth": 6,
    # T7 Mountains — silver / obsidian / red jute
    "Artisan Table": 7,
    "Blast Furnace": 7,
    "Workbench Upgrade 4": 7,  # Tool Shelf — Obsidian
    "Cauldron Upgrade 2": 7,  # Butcher's Table — Silver
    "Bows Tier 4": 7,  # Draugr Fang; JuteRed = mountains mat
    # T8 Plains — black metal / artisan stations
    "Axes Tier 4": 8,
    "Wisp Fountain": 8,
    "Wisplight": 8,
    "Spinning Wheel": 8,
    "Lox Fur Armor": 8,  # WrithanRoots swamp + Lox plains OK
    "Lox Saddle": 8,
    "Windmill": 8,
    "Stone Oven": 8,
    "Cauldron Upgrade 3": 8,  # Pots and Pans — Black Metal
    "Scythe": 8,
    # T9 Mistlands entry — NO Black-Forge-gated gear
    "Pickaxes Tier 4": 9,
    "Sap Extractor": 9,
    "Eitr Refinery": 9,
    "Galdr Table": 9,
    "Grappling Hook": 9,  # SoftProg; prereq → Eitr Refinery (not Frost Foundry)
    # T10 Mistlands deep — Black Forge + all BF-gated pack
    "Black Forge": 10,  # door into Ashlands
    "Black Forge Upgrade 1": 10,  # SoftProg (was T9 before BF)
    "Black Forge Upgrade 2": 10,
    "Boat Tier 4": 10,
    "Ceramic Plates": 10,
    "Artisan Press": 10,
    "Galdr Table Upgrade 1": 10,
    "Galdr Table Upgrade 2": 10,
    "Cauldron Upgrade 4": 10,  # Mortar — Black Marble
    "Carapace Armor": 10,
    "Crossbows Tier 1": 10,
    "Long Blades Tier 1": 10,
    "Spears Tier 5": 10,
    "Arrows Tier 10": 10,
    "Bolts Tier 1": 10,
    "Bolts Tier 2": 10,
    "Bolts Tier 3": 10,
    "Lantern": 10,
    "Short Blades Tier 6": 10,  # Skoll/Hati — was T8 plains with BF prereq
    # T11 Ashlands base (no gem variants)
    "Black Forge Upgrade 3": 11,
    "Siege": 11,
    "Transportation Tier 3": 11,
    "Ask Armor": 11,
    "Embla Armor": 11,
    "Flametal Armor": 11,
    "Asksvin Saddle": 11,
    "Cape Tier 7": 11,
    "Cape Tier 8": 11,
    "Battleaxes Tier 5": 11,
    "Clubs Tier 6": 11,
    "Blades Tier 7": 11,
    "Long Blades Tier 2": 11,
    "Spears Tier 6": 11,
    "Bows Tier 6": 11,
    "Crossbows Tier 2": 11,
    "Shields Tier 6": 11,
    "Tower Shields Tier 4": 11,
    "Bed Tier 3": 11,
    "Cauldron Upgrade 5": 11,
    "Galdr Table Upgrade 3": 11,
    "Elemental Magic Tier 2": 11,
    "Arrows Tier 11": 11,
    "Bolts Tier 4": 11,
    "Trinkets Tier 6": 11,
    "Ashwood Floors": 11,
    "Ashwood Walls": 11,
    "Ashwood Decorations": 11,
    "Ashwood Beams": 11,
    "Ashwood Stairs": 11,
    "Ashwood Doors": 11,
    # T12 Ashlands upgraded / Fader
    "Snow Shovel": 12,
    "Black Forge Upgrade 4": 12,
    "Battleaxes Tier 6": 12,
    "Clubs Tier 7": 12,
    "Blades Tier 8": 12,
    "Long Blades Tier 3": 12,
    "Spears Tier 7": 12,
    "Bows Tier 7": 12,
    "Crossbows Tier 3": 12,
    "Elemental Magic Tier 3": 12,
    "Blood Magic Tier 2": 12,
    # T13 DN entry
    "Frigid Kiln": 13,
    "Frost Foundry": 13,
    "Ember Charge": 13,
    "Deep North Crops": 13,
    "Deep North Cooking": 13,
    "Deep North Furniture": 13,
    "Cauldron Upgrade 6": 13,
    "Timber Walls": 13,
    "Timber Beams": 13,
    "Timber Decor": 13,
    "Scalewood Walls": 13,
    "Snowball": 13,
    "Cape Tier 9": 13,
    "Fishing Hat": 13,
    # T14 DN Nord base
    "Intricate Key": 14,
    "Black Forge Upgrade 5": 14,
    "Galdr Table Upgrade 4": 14,
    "Blades Tier 9": 14,
    "Long Blades Tier 4": 14,
    "Polearms Tier 5": 14,
    "Clubs Tier 8": 14,
    "Sledgehammers Tier 4": 14,
    "Axes Tier 6": 14,
    "Battleaxes Tier 7": 14,
    "Spears Tier 8": 14,
    "Short Blades Tier 7": 14,
    "Knuckles Tier 4": 14,
    "Bows Tier 8": 14,
    "Crossbows Tier 4": 14,
    "Shields Tier 7": 14,
    "Bucklers Tier 4": 14,
    "Tower Shields Tier 5": 14,
    "Arrows Tier 12": 14,
    "Bolts Tier 5": 14,
    "Bloodgold Ammunition": 14,
    "Trinkets Tier 7": 14,
    "Storage Tier 5": 14,
    "Moose Saddle": 14,
    "Crown of Valheim": 14,
    "Northern Feast": 14,
    # T15 post-Key
    "Protector Armor": 15,
    "Vanguard Armor": 15,
    "Caller Armor": 15,
    "Cape Tier 10": 15,
    "Elemental Magic Tier 4": 15,
    "Blood Magic Tier 3": 15,
}

# On implement: replace requiredResearchIDs with these (None = clear extras / keep listed only).
# Values are display names; generator annotates items.
FIX_PREREQS = {
    # Forge ups: break linear chain — each needs Forge (+ biome gate), not previous Up N
    "Forge Upgrade 1": ["Forge"],  # Cooler
    "Forge Upgrade 2": ["Forge"],  # Bellows (Chain mats via cost/region)
    "Forge Upgrade 3": ["Forge", "Bronze"],  # Anvils — NOT Forge Upgrade 2
    "Forge Upgrade 4": ["Forge", "Pickaxes Tier 2"],  # Smith's Anvil — iron era
    "Forge Upgrade 5": ["Forge"],  # Toolrack
    "Forge Upgrade 6": ["Forge", "Stonecutter"],  # Grinding Wheel
    # Cart/nails same BF sphere
    "Transportation Tier 1": ["Nails Tier 1"],
    "Nails Tier 1": ["Bronze"],
    # Bronze should not soft-lock on raft
    "Bronze": ["Forge"],
    # Roots / Lox — WrithanRoots is swamp; drop Frigid Kiln
    "Shield of Roots": ["Root Armor"],  # or Forge; swamp pack
    "Lox Fur Armor": ["Spinning Wheel"],  # plains linen path; was Frigid Kiln
    # Grappling Hook — mist SoftProg, not DN foundry
    "Grappling Hook": ["Eitr Refinery"],
    # Draugr Fang — no linen / spinning wheel (JuteRed is mountains mat in cost OK)
    "Bows Tier 4": ["Bows Tier 3", "Blast Furnace", "Forge Upgrade 1"],
    # Scythe — plains, not mist pick
    "Scythe": ["Cultivator", "Blast Furnace"],
    # Mountain door pick: allow Anvils OR Cooler for forge level (implement either)
    "Pickaxes Tier 3": ["Pickaxes Tier 2", "Forge Upgrade 1"],  # keep Cooler; optional also accept Up3
}

# Concrete research costs for pre-swamp / bronze rows that still used swamp or plains mats.
# Shown as the proposed cost; old cost kept in annotation.
PROPOSED_COST = {
    # T3 Black Forest
    "Cauldron": "Tin:8",
    "Nails Tier 1": "CarrotSeeds:5, Tin:2, Bronze:1",
    "Transportation Tier 1": "Bronze:2, Wood:10",
    "Bronze Armor": "Flint:4, SurtlingCore:5, Bronze:2",
    "Cultivator": "RoundLog:1, CopperOre:4, Tin:2",
    "Darkwood Beams": "Wood:10, Resin:5",
    "Darkwood Decorations": "Wood:10, Resin:5",
    "Darkwood Roofs": "Wood:10, Resin:5",
    # T4 Bronze
    "Axes Tier 2": "Bronze:5, Copper:3, RoundLog:5",
    "Arrows Tier 3": "MushroomYellow:1, RoundLog:5, Bronze:3",
    "Blades Tier 2": "RoundLog:7, Bronze:3",
    "Bucklers Tier 1": "Bronze:5, Wood:10",
    "Clubs Tier 2": "Tin:6, Bronze:2",
    "Forge Upgrade 3": "Wood:10, Bronze:5",  # Anvils
    "Polearms Tier 1": "Feathers:2, Bronze:5",
    "Spears Tier 2": "Bronze:4, Wood:5",
    "Trinkets Tier 1": "Tin:3, Copper:3",
    # T5 Finewood / pre-swamp
    "Boat Tier 2": "Flint:5, FineWood:10",
    "Pickaxes Tier 2": "Bronze:5, FineWood:5",
    "Forge Upgrade 1": "FineWood:10, Copper:5",  # Cooler
    "Transportation Tier 2": "Ectoplasm:2, GreydwarfEye:10",
    "Bows Tier 2": "Raspberry:7, FineWood:10",
    "Workbench Upgrade 3": "FineWood:10, Bronze:2",  # Adze
    # T6 swamp station (plains mat was wrong)
    "Forge Upgrade 2": "Chain:5",  # Bellows
}

DN_WEAPON_SPLITS = [
    "Blades Tier 9",
    "Long Blades Tier 4",
    "Polearms Tier 5",
    "Clubs Tier 8",
    "Sledgehammers Tier 4",
    "Axes Tier 6",
    "Battleaxes Tier 7",
    "Spears Tier 8",
    "Short Blades Tier 7",
    "Knuckles Tier 4",
    "Bows Tier 8",
    "Crossbows Tier 4",
]


def home_tier(name: str, old: int) -> int:
    if name in EXPLICIT_TIER:
        return EXPLICIT_TIER[name]
    if old <= 10:
        return old
    if old == 11:
        return 11
    if old == 12:
        return 14
    return old


def role_of(name: str, old_cat: str) -> str:
    if name in DOOR_ITEMS:
        return "Door"
    if name in SOFT:
        return "SoftProg"
    if old_cat == "Filler":
        return "Filler"
    return "Useful"


items = []
for r in rows:
    name = r["displayName"]
    old = int(r["tier"])
    tier = home_tier(name, old)
    role = role_of(name, r["category"])
    old_cost = r["researchRecipeRequirements"].replace("|", ", ")
    flags = []
    if name in PROPOSED_COST:
        cost = PROPOSED_COST[name]
        flags.append(f"was: {old_cost}")
    else:
        cost = old_cost
    if name in DN_WEAPON_SPLITS:
        flags.append("SPLIT: keep Uncooked+base only")
    if name in FIX_PREREQS:
        flags.append(f"PREREQ→ {' + '.join(FIX_PREREQS[name])}")
    if flags:
        cost = f"{cost}  [{'; '.join(flags)}]"
    items.append(
        {
            "name": name,
            "oldTier": old,
            "tier": tier,
            "role": role,
            "cost": cost,
            "oldCat": r["category"],
        }
    )

for base_name in DN_WEAPON_SPLITS:
    items.append(
        {
            "name": f"{base_name} Enchanted",
            "oldTier": 12,
            "tier": 15,
            "role": "Useful",
            "cost": "NEW research — Frostfire + Thunderblood variants (needs Memorial Coal path)",
            "oldCat": "Useful",
        }
    )

notes = [
    "v5.1: pre-swamp/bronze research costs retuned — no swamp/plains mats before their biomes (see PROPOSED_COST; rows show was:).",
    "v5 audit: nails+cart SoftProg T3; bronze weapons T4; BF-gated mist pack T10; forge prereqs rewired; Galdr Up3 SoftProg.",
    "WrithanRoots = swamp → Shield of Roots T6 + Lox Fur T8; drop Frigid Kiln prereqs.",
    "JuteRed = mountains → Bows T4 stays T7; drop Spinning Wheel prereq.",
    "Forge ups by vanilla mats: Cooler(Up1)=T5 SoftProg; Anvils(Up3)=T4; Bellows(Up2)+Smith/Toolrack/Grind=T6. Prereqs not linear.",
    "Workbench: Up1-2 Meadows; Adze T5; Tool Shelf T7. Cauldron: Spice T6 → Butcher T7 → Pots T8 → Mortar T10 → Rolling T11 → Smoker T13.",
    "Grappling Hook SoftProg T9 (prereq Eitr Refinery). Scythe → Blast Furnace. Short Blades T6 → T10. Bronze prereq drops Boat T1.",
    "T14 Nord + Key; T15 armor + Enchanted + Kall. Moder=T7, Yagluth=T8, Fader=T12, Kall=T15.",
]

payload = {
    "version": "5.1",
    "doors_into": {str(k): v for k, v in DOORS_INTO.items()},
    "tier_labels": {str(k): v for k, v in TIER_LABELS.items()},
    "soft": sorted(SOFT),
    "fix_prereqs": FIX_PREREQS,
    "proposed_costs": PROPOSED_COST,
    "notes": notes,
    "counts_by_tier": {
        str(t): Counter(i["tier"] for i in items).get(t, 0) for t in sorted(TIER_LABELS)
    },
    "counts_by_role": dict(Counter(i["role"] for i in items)),
    "items": sorted(
        items,
        key=lambda x: (
            x["tier"],
            {"Door": 0, "SoftProg": 1, "Useful": 2, "Filler": 3}[x["role"]],
            x["name"],
        ),
    ),
}

OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("tiers", payload["counts_by_tier"])
print("roles", payload["counts_by_role"])
print("T3:", [i["name"] for i in items if i["tier"] == 3])
print("T4:", [i["name"] for i in items if i["tier"] == 4])
print("T9:", [i["name"] for i in items if i["tier"] == 9])
print("T10:", [i["name"] for i in items if i["tier"] == 10])
