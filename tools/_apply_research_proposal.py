"""Apply _proposed_research.json tiers/costs/prereqs/categories into research.tsv.

Does not touch Items.py / Parents.py / Regions.py / DLL / apworld.
Skips NEW Enchanted rows and DN weapon prefab splits (later overhaul).
"""
from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROP = Path(__file__).with_name("_proposed_research.json")
TSV_PATHS = [ROOT / "mod" / "research.tsv", ROOT / "tools" / "research.tsv"]

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

HEADER_LINE = "# " + "\t".join(COLS)


def role_to_category(role: str, old_cat: str) -> str:
    if role == "Door":
        return "Progression"
    if role == "SoftProg":
        # Soft progression stays Progression for AP classification until Regions overhaul.
        return "Progression"
    if role == "Filler":
        return "Filler"
    return "Useful"


def main() -> None:
    prop = json.loads(PROP.read_text(encoding="utf-8"))
    by_name = {
        i["name"]: i
        for i in prop["items"]
        if not i["name"].endswith(" Enchanted")
    }
    fix_prereqs: dict[str, list[str]] = prop["fix_prereqs"]
    proposed_costs: dict[str, str] = prop["proposed_costs"]

    raw = (ROOT / "mod" / "research.tsv").read_text(encoding="utf-8-sig")
    lines = raw.splitlines()
    comment_prefix = []
    data_lines = []
    for line in lines:
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            # keep only non-header comments before first data? We rebuild header.
            if line.startswith("# iconFromItemPrefab") or line.startswith("#iconFromItemPrefab"):
                continue
            comment_prefix.append(line)
            continue
        data_lines.append(line)

    reader = csv.DictReader(StringIO("\t".join(COLS) + "\n" + "\n".join(data_lines)), delimiter="\t")
    rows = list(reader)
    id_by_name = {r["displayName"]: r["researchItemID"] for r in rows}

    missing = [n for n in by_name if n not in id_by_name]
    if missing:
        raise SystemExit(f"Proposal names missing from TSV: {missing}")

    changes = []
    for r in rows:
        name = r["displayName"]
        p = by_name[name]
        old = {
            "tier": r["tier"],
            "category": r["category"],
            "cost": r["researchRecipeRequirements"],
            "reqs": r["requiredResearchIDs"],
        }

        r["tier"] = str(p["tier"])
        r["category"] = role_to_category(p["role"], p["oldCat"])

        if name in proposed_costs:
            # accept "A:1, B:2" or "A:1|B:2"
            cost = proposed_costs[name].replace(", ", "|").replace(",", "|")
            r["researchRecipeRequirements"] = cost

        if name in fix_prereqs:
            ids = []
            for parent in fix_prereqs[name]:
                pid = id_by_name.get(parent)
                if not pid:
                    raise SystemExit(f"{name}: unknown prereq parent {parent}")
                ids.append(pid)
            r["requiredResearchIDs"] = "|".join(ids)

        new = {
            "tier": r["tier"],
            "category": r["category"],
            "cost": r["researchRecipeRequirements"],
            "reqs": r["requiredResearchIDs"],
        }
        if old != new:
            changes.append((name, old, new))

    out_lines = [HEADER_LINE]
    # Preserve stray comments that were between rows? Current file only has header comment.
    for r in rows:
        out_lines.append("\t".join(r.get(c, "") or "" for c in COLS))
    text = "\n".join(out_lines) + "\n"

    for path in TSV_PATHS:
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path} ({len(rows)} rows, {len(changes)} changed)")

    # Summary by field
    tier_c = sum(1 for _, o, n in changes if o["tier"] != n["tier"])
    cat_c = sum(1 for _, o, n in changes if o["category"] != n["category"])
    cost_c = sum(1 for _, o, n in changes if o["cost"] != n["cost"])
    req_c = sum(1 for _, o, n in changes if o["reqs"] != n["reqs"])
    print(f"tier={tier_c} category={cat_c} cost={cost_c} prereq={req_c}")


if __name__ == "__main__":
    main()
