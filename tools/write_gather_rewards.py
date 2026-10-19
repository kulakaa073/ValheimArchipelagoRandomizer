"""Write gather-rewards.md from drops.tsv and recipe_costs.json. Does not change rewards."""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "gather-rewards.md"
ENGLISH = json.loads((ROOT / "tools" / "english_names.json").read_text(encoding="utf-8"))
COSTS = json.loads((ROOT / "tools" / "recipe_costs.json").read_text(encoding="utf-8"))

STATIONS = {
    "piece_workbench", "piece_workbench_ext1", "piece_workbench_ext2", "piece_workbench_ext3", "piece_workbench_ext4",
    "forge", "forge_ext1", "forge_ext2", "forge_ext3", "forge_ext4", "forge_ext5", "forge_ext6",
    "smelter", "charcoal_kiln", "piece_stonecutter", "piece_artisanstation", "artisan_ext1",
    "piece_magetable", "piece_magetable_ext", "piece_magetable_ext2", "piece_magetable_ext3", "piece_magetable_ext4",
    "blackforge", "blackforge_ext1", "blackforge_ext2_vise", "blackforge_ext3_metalcutter",
    "blackforge_ext4_gemcutter", "blackforge_ext5_apron",
    "eitrrefinery", "blastfurnace", "windmill", "piece_spinningwheel", "piece_oven", "fermenter",
    "piece_MeadCauldron", "piece_cauldron", "cauldron_ext1_spice", "cauldron_ext3_butchertable",
    "cauldron_ext4_pots", "cauldron_ext5_mortarandpestle", "cauldron_ext6_rollingpins", "cauldron_ext7_smoker",
    "piece_cookingstation", "piece_cookingstation_iron", "piece_FrostKiln", "piece_FrostFoundry",
    "piece_sapcollector", "portal_wood",
}
AMMO = re.compile(r"(Arrow|Bolt|Turret|Missile|Bomb|Ammo|Catapult)", re.I)
STACK = re.compile(r"(^bar_|_stack$|_pile$|pile$)", re.I)
FOOD_FOLDERS = {"Consumables", "Fireworks"}
GEAR_FOLDERS = {"Weapons", "Tools", "Armor", "Helmets", "Shields", "Trinkets"}

# Basic craft chosen above the cheapest token use. Amount is the material line on that craft.
OVERRIDES = {
    "Wood": (20, "Research Bench", "Available with the hammer before any other station. The workbench costs 10 and a torch costs 1."),
    "Gold": (20, "Nord weapon cast", "Bloodgold arrows cost 1 and a dagger costs 2. Sword, axe, mace, and bow casts each cost 20."),
    "SurtlingCore": (5, "Smelter and Charcoal Kiln", "A lantern costs 1. The smelter and charcoal kiln each cost 5."),
    "Flint": (6, "Flint Axe", "The flint knife costs 4, so 5 already makes one. The flint axe costs 6. The spear and the chopping block cost 10."),
    "Frostwood": (10, "Nord weapon cast", "The moose saddle costs 5. A nord weapon cast costs 10, which the current reward already covers."),
    "FrostCore": (10, "Frigid Kiln and Frost Foundry", "Both stations cost 10. No build costs less."),
    "Stone": (20, "Smelter, Charcoal Kiln, Frigid Kiln, Frost Foundry", "The research bench costs 10, which the current reward already covers. These stations each cost 20."),
    "Iron": (15, "Frost Foundry and Stone Oven", "The stonecutter costs 2 and the iron cooking station costs 3, so 5 is already a usable craft. The foundry and oven cost 15."),
}


def english(prefab):
    if prefab == "DvergrKey":
        return "Dvergr Key"
    return ENGLISH.get(prefab) or prefab


def load_research():
    uses = defaultdict(list)
    for line in (ROOT / "mod" / "research.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("icon"):
            continue
        cols = line.split("\t")
        name = cols[2]
        for bit in cols[5].split("|"):
            if not bit or ":" not in bit:
                continue
            prefab, amount = bit.split(":")
            uses[prefab].append({"amount": int(amount), "label": name})
    return uses


def load_drops():
    rows = []
    for line in (ROOT / "mod" / "drops.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        prefab, display, tier, amount = line.split("\t")
        rows.append((prefab, display, int(tier), int(amount)))
    return rows


def collect_uses():
    uses = defaultdict(list)
    for recipe in COSTS["recipes"]:
        ammo = bool(AMMO.search(recipe["name"]) or AMMO.search(recipe.get("item") or ""))
        food = recipe["folder"] in FOOD_FOLDERS
        for cost in recipe["costs"]:
            uses[cost["prefab"]].append({
                "amount": cost["amount"],
                "label": english(recipe["item"] or recipe["name"]),
                "kind": "food" if food else ("ammo" if ammo else "gear"),
                "folder": recipe["folder"],
            })
    for piece in COSTS["pieces"]:
        name = piece["name"]
        if name in STATIONS:
            kind = "station"
        elif STACK.search(name):
            kind = "stack"
        else:
            kind = "build"
        for cost in piece["costs"]:
            uses[cost["prefab"]].append({
                "amount": cost["amount"],
                "label": english(name),
                "kind": kind,
                "folder": "Piece",
            })
    uses["Wood"].append({"amount": 20, "label": "Research Bench", "kind": "bench", "folder": "Bench"})
    uses["Stone"].append({"amount": 10, "label": "Research Bench", "kind": "bench", "folder": "Bench"})
    return uses


def cheapest(rows):
    if not rows:
        return None
    return min(rows, key=lambda row: (row["amount"], row["label"]))


def basic_craft(prefab, rows):
    if prefab in OVERRIDES:
        amount, label, why = OVERRIDES[prefab]
        return {"amount": amount, "label": label, "kind": "override", "why": why}
    groups = (
        ("gear", lambda row: row["kind"] == "gear" and (row["folder"] in GEAR_FOLDERS or row["folder"] == "Materials")),
        ("station", lambda row: row["kind"] in {"station", "bench"}),
        ("build", lambda row: row["kind"] == "build"),
        ("food", lambda row: row["kind"] == "food"),
        ("ammo", lambda row: row["kind"] == "ammo"),
        ("stack", lambda row: row["kind"] == "stack"),
    )
    for _, match in groups:
        pool = [row for row in rows if match(row)]
        if pool:
            pick = dict(cheapest(pool))
            pick["why"] = ""
            return pick
    pick = cheapest(rows)
    if pick:
        pick = dict(pick)
        pick["why"] = ""
    return pick


def cell(text):
    return str(text).replace("|", "/")


def research_ends(rows):
    if not rows:
        return None, None
    return cheapest(rows), max(rows, key=lambda row: (row["amount"], row["label"]))


def main():
    uses = collect_uses()
    research = load_research()
    drops = load_drops()
    records = []
    for prefab, display, tier, current in drops:
        rows = uses.get(prefab, [])
        low = cheapest(rows)
        basic = basic_craft(prefab, rows)
        required = basic["amount"] if basic else None
        rmin, rmax = research_ends(research.get(prefab, []))
        token = prefab.startswith("Mold") or prefab.startswith("Upgrader")
        stack_only = basic is not None and basic["kind"] in {"stack", "build"} and prefab in {"Flametal", "Coins"}
        if token:
            proposed = 1
            note = "Every recipe uses 1. No research uses it."
        elif required is None and rmin is None:
            proposed = current
            note = "No craft, build, or research uses this."
        elif stack_only and rmin is None:
            proposed = current
            note = "Only a storage or treasure piece uses this. Left at the current reward."
        else:
            floors = [current]
            if required is not None and not (stack_only and basic["kind"] == "stack"):
                if not (prefab == "Coins" and basic and basic["kind"] == "build"):
                    floors.append(required)
            if rmin is not None:
                floors.append(rmin["amount"])
            proposed = max(floors)
            if prefab == "Coins":
                note = "Hearth costs 25. The treasure chest costs 99 and is not the target."
            elif prefab in {"Stone", "Iron"}:
                note = "Review. " + basic["why"]
            elif basic and basic.get("why"):
                note = basic["why"]
            elif rmin is not None and (required is None or rmin["amount"] > required) and proposed > current:
                note = f"Cheapest research, {rmin['label']}, costs {rmin['amount']}."
            elif proposed > current:
                note = "Current reward cannot pay this craft."
            elif proposed < current:
                note = "Current bundle is more than one craft."
            else:
                note = ""
        records.append({
            "prefab": prefab,
            "display": display,
            "tier": tier,
            "current": current,
            "low": low,
            "basic": basic,
            "required": required if required is not None else "",
            "rmin": rmin,
            "rmax": rmax,
            "proposed": proposed,
            "note": note,
            "token": token,
        })

    def research_cell(entry):
        if not entry:
            return "none"
        return f"{entry['amount']} {entry['label']}"

    rises = [row for row in records if row["proposed"] > row["current"]]
    cuts = [row for row in records if row["proposed"] < row["current"] and not row["token"]]
    tokens = [row for row in records if row["token"]]
    short = [
        row for row in records
        if row["rmax"] and row["rmax"]["amount"] > row["proposed"]
    ]
    lines = []
    lines.append("# Gather reward review")
    lines.append("")
    lines.append("No rewards are changed yet. This compares the current gather bundle with one craft, one station build, and the cheapest research recipe that spends that material.")
    lines.append("")
    lines.append("Current amounts for the newer materials come from the item's stack size: 100 or more gives 20, 50 or more gives 10, 20 or more gives 5, 10 or more gives 3, and anything smaller gives 1. The original forage rows were set by hand. That stack rule is why wood is 10 and frostcore is 5.")
    lines.append("")
    lines.append("## Rule used for the proposed column")
    lines.append("")
    lines.append("One received gather reward should pay that material's line on one basic craft and on the cheapest research that uses it. It does not pay the most expensive research.")
    lines.append("")
    lines.append("- A weapon, tool, armor, shield, trinket, or processed material sets the craft amount when one exists. A station sets it when the material is not used for gear. Arrows, bolts, food, mead, decorative pieces, and storage stacks do not.")
    lines.append("- The cheapest research recipe is a second floor. Proposed is the higher of the current reward, the craft, and that research. The largest research is listed and does not raise the reward.")
    lines.append("- Moulds and idols drop to 1. Every recipe uses one, and no research uses them.")
    lines.append("- Wood, bloodgold, flint, surtling cores, and frostcore use a named craft instead of the cheapest token use. Stone and iron are marked Review because the cheap craft is already covered and the useful station costs more.")
    lines.append("")
    lines.append("## Deep North: one weapon from the lucky rewards")
    lines.append("")
    lines.append("A nord weapon cast is made at the black forge. The frost foundry does not craft it. The sword cast is `SwordGoldUncooked`: 20 bloodgold, 1 Mould: Nord Sword (`MoldSword`), and 10 timberwood. The finished sword is `SwordGold`: those same materials plus 1 Bloodgold Battle Idol (`Upgrader7Weapon`). Each weapon has its own mould. Three sword moulds are three copies of that one mould, not three different moulds. The Frigid Kiln and Frost Foundry are hammer builds.")
    lines.append("")
    lines.append("| Piece | Item | Recipe cost | Current reward | Proposed | Covers it |")
    lines.append("| --- | --- | ---: | ---: | ---: | --- |")
    lines.append("| Nord weapon cast | Bloodgold | 20 | 5 | 20 | After the change |")
    lines.append("| Nord weapon cast | Mould: Nord Sword | 1 | 3 | 1 | One is enough |")
    lines.append("| Nord weapon cast | Timberwood | 10 | 10 | 10 | Already |")
    lines.append("| Finished nord sword | Bloodgold Battle Idol | 1 | 5 | 1 | One is enough |")
    lines.append("| Frigid Kiln or Frost Foundry | Frostcore | 10 | 5 | 10 | After the change |")
    lines.append("| Frigid Kiln | Ice | 5 | 10 | 10 | Already |")
    lines.append("| Either station | Stone | 20 | 10 | 20 | After the change, if the stone review is accepted |")
    lines.append("| Frost Foundry | Iron | 15 | 5 | 15 | After the change, if the iron review is accepted |")
    lines.append("| Research bench | Wood | 20 | 10 | 20 | After the change |")
    lines.append("")
    lines.append("The same 1-cost rule covers every mould and every idol: armor moulds, staff moulds, and the wooden through flametal idols. Research recipes do not ask for any of them. With bloodgold at 20, one sword mould, and timberwood at 10, one of each reward casts a nord weapon at a black forge. Placing the frost foundry still needs 15 iron and 20 stone.")
    lines.append("")
    lines.append("## Proposed changes")
    lines.append("")
    lines.append(f"{len(rises)} rewards would rise. {len(tokens)} moulds and idols would drop from 3 or 5 to 1. The other rows already cover the craft and the cheapest research.")
    lines.append("")
    lines.append("| Material | Tier | Current | Craft | Cheapest research | Proposed | Why |")
    lines.append("| --- | ---: | ---: | ---: | --- | ---: | --- |")
    for row in rises:
        craft = row["required"] if row["required"] != "" else ""
        lines.append(
            f"| {cell(row['display'])} | {row['tier']} | {row['current']} | {craft} | {cell(research_cell(row['rmin']))} | {row['proposed']} | {cell(row['note'])} |"
        )
    lines.append("")
    lines.append("## Largest research still above the proposed reward")
    lines.append("")
    lines.append("These research recipes cost more than one proposed reward. The cheapest research is already covered. Raising the reward to the largest research would pay that one recipe and leave most other researches over-supplied.")
    lines.append("")
    lines.append("| Material | Proposed | Largest research | Amount |")
    lines.append("| --- | ---: | --- | ---: |")
    for row in sorted(short, key=lambda item: (-(item["rmax"]["amount"] - item["proposed"]), item["display"])):
        lines.append(
            f"| {cell(row['display'])} | {row['proposed']} | {cell(row['rmax']['label'])} | {row['rmax']['amount']} |"
        )
    lines.append("")
    lines.append("## Review notes")
    lines.append("")
    lines.append("| Material | Current | Proposed | Why it is a choice |")
    lines.append("| --- | ---: | ---: | --- |")
    for prefab in ("Wood", "Stone", "Iron", "Gold", "Flint", "SurtlingCore", "FrostCore"):
        row = next(item for item in records if item["prefab"] == prefab)
        lines.append(
            f"| {cell(row['display'])} | {row['current']} | {row['proposed']} | {cell(row['note'])} |"
        )
    lines.append("")
    lines.append("Rejecting the stone row leaves it at 10. That still builds the research bench and the forge. It does not place a smelter, charcoal kiln, frigid kiln, or frost foundry. Rejecting the iron row leaves it at 5. That still builds the stonecutter and the iron cooking station. It does not place the frost foundry or the stone oven.")
    lines.append("")
    lines.append("## All gather rewards")
    lines.append("")
    lines.append("Craft is the basic item or station. Cheapest research is the smallest research-bench cost. Largest research is the biggest one, and it does not set Proposed unless it is also the cheapest.")
    lines.append("")
    lines.append("| Material | Tier | Current | Craft | Cheapest research | Largest research | Proposed | Note |")
    lines.append("| --- | ---: | ---: | ---: | --- | --- | ---: | --- |")
    for row in records:
        craft = ""
        if row["basic"]:
            amount = row["required"] if row["required"] != "" else ""
            craft = f"{amount} {row['basic']['label']}"
        lines.append(
            "| {display} | {tier} | {current} | {craft} | {rmin} | {rmax} | {proposed} | {note} |".format(
                display=cell(row["display"]),
                tier=row["tier"],
                current=row["current"],
                craft=cell(craft or "none"),
                rmin=cell(research_cell(row["rmin"])),
                rmax=cell(research_cell(row["rmax"])),
                proposed=row["proposed"],
                note=cell(row["note"]),
            )
        )
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} rises {len(rises)} tokens {len(tokens)} short {len(short)} of {len(records)}")


if __name__ == "__main__":
    main()
