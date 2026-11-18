"""Apply DN enchanted split to research.tsv, then sync Items/Locations/Parents.

Does not rebuild DLL, Gale zip, or .apworld archive. Leaves Regions.py alone
(v5.1 door list already applied).
"""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_RESEARCH = ROOT / "mod" / "research.tsv"
TOOLS_RESEARCH = ROOT / "tools" / "research.tsv"
MOD_TROPHIES = ROOT / "mod" / "trophies.tsv"
ITEMS_PY = ROOT / "valheimapworld" / "Items.py"
LOCATIONS_PY = ROOT / "valheimapworld" / "Locations.py"
PARENTS_PY = ROOT / "valheimapworld" / "Parents.py"

COLS = [
    "iconFromItemPrefab",
    "researchItemID",
    "displayName",
    "description",
    "requiredResearchIDs",
    "researchRecipeRequirements",
    "gatedItemPrefabIDs",
    "tier",
    "category",
    "devComment",
]

# Base keeps Uncooked + plain finished. Enchanted gets FrostFire + BloodLightning.
DN_SPLITS = {
    "researchBladesTier9": (
        "Blades Tier 9",
        "researchBladesTier9Enchanted",
        "Blades Tier 9 Enchanted",
        "SwordGold",
    ),
    "researchLongBladesTier4": (
        "Long Blades Tier 4",
        "researchLongBladesTier4Enchanted",
        "Long Blades Tier 4 Enchanted",
        "THSwordGold",
    ),
    "researchPolearmsTier5": (
        "Polearms Tier 5",
        "researchPolearmsTier5Enchanted",
        "Polearms Tier 5 Enchanted",
        "AtgeirGold",
    ),
    "researchClubTier8": (
        "Clubs Tier 8",
        "researchClubTier8Enchanted",
        "Clubs Tier 8 Enchanted",
        "MaceGold",
    ),
    "researchSledgehammerTier4": (
        "Sledgehammers Tier 4",
        "researchSledgehammerTier4Enchanted",
        "Sledgehammers Tier 4 Enchanted",
        "SledgeGold",
    ),
    "researchAxeTier6": (
        "Axes Tier 6",
        "researchAxeTier6Enchanted",
        "Axes Tier 6 Enchanted",
        "AxeGold",
    ),
    "researchBattleaxeTier7": (
        "Battleaxes Tier 7",
        "researchBattleaxeTier7Enchanted",
        "Battleaxes Tier 7 Enchanted",
        "BattleaxeGold",
    ),
    "researchSpearTier8": (
        "Spears Tier 8",
        "researchSpearTier8Enchanted",
        "Spears Tier 8 Enchanted",
        "SpearGold",
    ),
    "researchShortBladesTier7": (
        "Short Blades Tier 7",
        "researchShortBladesTier7Enchanted",
        "Short Blades Tier 7 Enchanted",
        "KnifeGold",
    ),
    "researchKnucklesTier4": (
        "Knuckles Tier 4",
        "researchKnucklesTier4Enchanted",
        "Knuckles Tier 4 Enchanted",
        "FistGold",
    ),
    "researchBowsTier8": (
        "Bows Tier 8",
        "researchBowsTier8Enchanted",
        "Bows Tier 8 Enchanted",
        "BowGold",
    ),
    "researchCrossbowsTier4": (
        "Crossbows Tier 4",
        "researchCrossbowsTier4Enchanted",
        "Crossbows Tier 4 Enchanted",
        "CrossbowGold",
    ),
}


def read_research(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    lines = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    return list(csv.DictReader(StringIO("\t".join(COLS) + "\n" + "\n".join(lines)), delimiter="\t"))


def write_research(rows: list[dict]) -> None:
    out = ["# " + "\t".join(COLS)]
    for r in rows:
        out.append("\t".join(r.get(c, "") or "" for c in COLS))
    text = "\n".join(out) + "\n"
    MOD_RESEARCH.write_text(text, encoding="utf-8")
    TOOLS_RESEARCH.write_text(text, encoding="utf-8")


def split_gated(gated: str, stem: str) -> tuple[str, str]:
    parts = [p for p in gated.split("|") if p]
    base, ench = [], []
    for p in parts:
        if p.endswith("_FrostFire") or p.endswith("_BloodLightning"):
            ench.append(p)
        elif p == stem or p == stem + "Uncooked" or p.endswith("Uncooked") and p.startswith(stem):
            base.append(p)
        elif "_FrostFire" in p or "_BloodLightning" in p:
            ench.append(p)
        else:
            base.append(p)
    if not base:
        raise SystemExit(f"no base prefabs for stem {stem} in {gated}")
    if not ench:
        raise SystemExit(f"no enchanted prefabs for stem {stem} in {gated}")
    return "|".join(base), "|".join(ench)


def apply_dn_split(rows: list[dict]) -> list[dict]:
    by_id = {r["researchItemID"]: r for r in rows}
    if any(r["researchItemID"].endswith("Enchanted") for r in rows):
        print("DN Enchanted rows already present — skipping split insert")
        return rows

    new_rows: list[dict] = []
    inserted = 0
    for r in rows:
        rid = r["researchItemID"]
        if rid not in DN_SPLITS:
            new_rows.append(r)
            continue
        _base_name, ench_id, ench_name, stem = DN_SPLITS[rid]
        base_gated, ench_gated = split_gated(r["gatedItemPrefabIDs"], stem)
        r = dict(r)
        r["gatedItemPrefabIDs"] = base_gated
        r["description"] = "Nord base (uncooked + finished)"
        r["devComment"] = (r.get("devComment") or "") + " SPLIT base"
        new_rows.append(r)

        ench = {
            "iconFromItemPrefab": stem + "_FrostFire",
            "researchItemID": ench_id,
            "displayName": ench_name,
            "description": "Frostfire + Thunderblood variants",
            "requiredResearchIDs": f"{rid}|researchIntricateKey",
            "researchRecipeRequirements": "MemorialCoal:1|Gold:10",
            "gatedItemPrefabIDs": ench_gated,
            "tier": "15",
            "category": "Useful",
            "devComment": "SPLIT enchanted — Memorial Coal / Morkhalla path",
        }
        # Prefer FrostFire icon; fall back to BloodLightning if missing naming
        if stem + "_FrostFire" not in ench_gated.split("|"):
            ench["iconFromItemPrefab"] = ench_gated.split("|")[0]
        new_rows.append(ench)
        inserted += 1

    # Sanity: Intricate Key exists
    if "researchIntricateKey" not in by_id:
        raise SystemExit("researchIntricateKey missing")
    print(f"DN split: added {inserted} Enchanted researches")
    return new_rows


def replace_blob(path: Path, start: str, end: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    a = text.find(start)
    if a < 0:
        raise SystemExit(f"missing start in {path}")
    b = text.find(end, a + len(start))
    if b < 0:
        raise SystemExit(f"missing end in {path}")
    path.write_text(text[: a + len(start)] + "\n" + body + "\n" + text[b:], encoding="utf-8")


def sync_items_locations(research: list[dict]) -> None:
    trophy_lines = MOD_TROPHIES.read_text(encoding="utf-8").splitlines()
    trophy_rows = []
    for i, line in enumerate(trophy_lines):
        if i == 0 or not line.strip():
            continue
        trophy_rows.append(line.split("\t"))

    item_lines = ["// Item User Friendly Name,ID,Count,Type,Classification"]
    loc_lines = ["// Location Type,User Friendly Name,ID,Classification,Region"]
    for r in research:
        item_lines.append(f"{r['displayName']},item:{r['researchItemID']},1,Item,{r['category']}")
        loc_lines.append(
            f"Research,{r['displayName']},loc:{r['researchItemID']},Not Missable,Tier{r['tier']}"
        )
    for row in trophy_rows:
        friendly = f"Trophy: {row[0]}"
        item_lines.append(f"{friendly},item:{row[1]},1,Item,Useful")
        loc_lines.append(f"Trophy,{friendly},loc:{row[1]},Not Missable,Tier{row[3]}")

    replace_blob(ITEMS_PY, "items_txt = '''", "'''", "\n".join(item_lines))
    replace_blob(LOCATIONS_PY, "locations_txt = '''", "'''", "\n".join(loc_lines))
    print(f"Items/Locations: {len(research)} research + {len(trophy_rows)} trophies")


def sync_parents(research: list[dict]) -> None:
    id_to_name = {r["researchItemID"]: r["displayName"] for r in research}
    parents: dict[str, tuple[str, ...]] = {}
    for r in research:
        reqs = []
        for rid in filter(None, (r.get("requiredResearchIDs") or "").split("|")):
            name = id_to_name.get(rid)
            if not name:
                raise SystemExit(f"{r['displayName']}: unknown prereq id {rid}")
            reqs.append(name)
        if reqs:
            parents[r["displayName"]] = tuple(reqs)

    # Transitive closure
    memo: dict[str, frozenset[str]] = {}

    def closure(name: str, stack: set[str] | None = None) -> frozenset[str]:
        if name in memo:
            return memo[name]
        if stack is None:
            stack = set()
        if name in stack:
            return frozenset()
        stack.add(name)
        acc: set[str] = set()
        for p in parents.get(name, ()):
            acc.add(p)
            acc |= closure(p, stack)
        stack.remove(name)
        memo[name] = frozenset(acc)
        return memo[name]

    for name in list(parents):
        closure(name)

    lines = [
        '"""Parent research items for default access.',
        "",
        "A research check can be sent only after those items are received.",
        "Generated from research.tsv. Do not edit by hand.",
        '"""',
        "",
        "RESEARCH_PARENTS = {",
    ]
    for name in sorted(parents):
        vals = ", ".join(repr(p) for p in parents[name])
        lines.append(f"    {name!r}: ({vals},),")
    lines.append("}")
    lines.append("")
    lines.append("PARENT_CLOSURE = {")
    for name in sorted(memo):
        vals = ", ".join(repr(p) for p in sorted(memo[name]))
        lines.append(f"    {name!r}: frozenset(({vals},)),")
    lines.append("}")
    lines.append("")
    PARENTS_PY.write_text("\n".join(lines), encoding="utf-8")
    print(f"Parents: {len(parents)} direct, {len(memo)} closures")


def main() -> None:
    rows = read_research(MOD_RESEARCH)
    rows = apply_dn_split(rows)
    write_research(rows)
    sync_items_locations(rows)
    sync_parents(rows)
    print("done")


if __name__ == "__main__":
    main()
