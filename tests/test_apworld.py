"""World generation, stable ids, tier doors, and packaged-syntax checks."""
from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.ap_fakes import CollectionState, MultiWorld, install

install()

from valheimapworld import GOALS, ValheimWorld, selected_goal
from valheimapworld.Drops import BOSS_DROPS
from valheimapworld.Ids import resolve_section
from valheimapworld.Items import item_table
from valheimapworld.Locations import location_table


class Opt:
    def __init__(self, value):
        self.value = value

    def __bool__(self):
        return bool(self.value)


def make_world(boss_checks, goal, drop_checks=0, research_access=0, sequential=0):
    world = ValheimWorld.__new__(ValheimWorld)
    world.player = 1
    world.multiworld = MultiWorld()
    world.options = type("Options", (), {})()
    world.options.boss_checks = Opt(boss_checks)
    world.options.goal = Opt(goal)
    world.options.drop_checks = Opt(drop_checks)
    world.options.research_access = Opt(research_access)
    world.options.sequential_tiers = Opt(sequential)
    world.create_regions()
    world.create_items()
    world.set_rules()
    world.pre_fill()
    return world


def snapshot(world):
    locations = world.multiworld.get_locations(world.player)
    locked = [loc for loc in locations if loc.locked]
    pool = [item for item in world.multiworld.itempool if item.player == world.player]
    return locations, locked, pool


def fill(world):
    """Place every pool item on an empty location that accepts it."""
    locations = [loc for loc in world.multiworld.get_locations(world.player) if loc.item is None]
    pool = [item for item in world.multiworld.itempool if item.player == world.player]
    pool.sort(key=lambda item: (0 if item.name in {boss.item_name for boss in BOSS_DROPS} else 1, item.name))
    for item in pool:
        placed = False
        for loc in locations:
            if loc.item is not None:
                continue
            if not loc.item_rule(item):
                continue
            loc.item = item
            placed = True
            break
        if not placed:
            raise AssertionError(f"no location accepted {item.name}")
    empty = [loc.name for loc in world.multiworld.get_locations(world.player) if loc.item is None]
    if empty:
        raise AssertionError(f"unfilled locations: {empty[:8]}")


def assert_balanced(test, world):
    locations, locked, pool = snapshot(world)
    test.assertEqual(len(pool) + len(locked), len(locations))
    test.assertEqual(len({loc.name for loc in locations}), len(locations))
    test.assertEqual(len({loc.address for loc in locations}), len(locations))
    fill(world)
    condition = world.multiworld.completion_condition[world.player]
    goal = selected_goal(world)
    state = CollectionState()
    test.assertFalse(condition(state))
    if world.options.boss_checks:
        state.reached.add((goal.location, world.player))
    else:
        state.items[("Victory", world.player)] = 1
    test.assertTrue(condition(state))
    return locations, locked, pool


class GenerationTests(unittest.TestCase):
    def test_boss_checks_valhalla_locks_victory_on_extra_location(self):
        world = make_world(boss_checks=1, goal=8)
        locations, locked, pool = assert_balanced(self, world)
        valhalla = [loc for loc in locations if loc.name == "Journey to Valhalla"]
        self.assertEqual(len(valhalla), 1)
        self.assertTrue(valhalla[0].locked)
        self.assertEqual(valhalla[0].item.name, "Victory")
        self.assertNotIn("Victory", [item.name for item in pool])
        self.assertEqual(len(locked), 1)
        boss_locations = {boss.location for boss in BOSS_DROPS}
        self.assertTrue(boss_locations.isdisjoint({"Journey to Valhalla"}))
        self.assertTrue(boss_locations.issubset({loc.name for loc in locations}))

    def test_boss_checks_kall_does_not_duplicate_the_boss_location(self):
        world = make_world(boss_checks=1, goal=7)
        locations, locked, pool = assert_balanced(self, world)
        kall = [loc for loc in locations if loc.name == "Defeat Kall"]
        self.assertEqual(len(kall), 1)
        self.assertFalse(kall[0].locked)
        self.assertEqual(locked, [])
        self.assertNotIn("Victory", [item.name for item in pool])

    def test_boss_checks_eikthyr_does_not_duplicate_the_boss_location(self):
        world = make_world(boss_checks=1, goal=0)
        locations, locked, pool = assert_balanced(self, world)
        hits = [loc for loc in locations if loc.name == "Defeat Eikthyr"]
        self.assertEqual(len(hits), 1)
        self.assertFalse(hits[0].locked)
        self.assertEqual(locked, [])
        self.assertNotIn("Journey to Valhalla", [loc.name for loc in locations])

    def test_boss_checks_off_valhalla_keeps_locked_victory(self):
        world = make_world(boss_checks=0, goal=8)
        locations, locked, pool = assert_balanced(self, world)
        valhalla = [loc for loc in locations if loc.name == "Journey to Valhalla"]
        self.assertEqual(len(valhalla), 1)
        self.assertTrue(valhalla[0].locked)
        self.assertEqual(valhalla[0].item.name, "Victory")
        self.assertEqual(len(locked), 1)
        self.assertFalse(any(item.name == "Hard Antler" for item in pool))

    def test_boss_checks_off_kall_keeps_goal_location(self):
        world = make_world(boss_checks=0, goal=7)
        locations, locked, pool = assert_balanced(self, world)
        kall = [loc for loc in locations if loc.name == "Defeat Kall"]
        self.assertEqual(len(kall), 1)
        self.assertTrue(kall[0].locked)
        self.assertEqual(kall[0].item.name, "Victory")
        self.assertEqual(len(locked), 1)
        self.assertNotIn("Hard Antler", [item.name for item in pool])

    def test_goal_constants_cover_the_option_order(self):
        self.assertEqual([goal.location for goal in GOALS][-1], "Journey to Valhalla")
        self.assertEqual(GOALS[7].location, "Defeat Kall")
        self.assertEqual(GOALS[0].location, "Defeat Eikthyr")


class StableIdTests(unittest.TestCase):
    def test_live_ids_match_the_baseline(self):
        baseline = json.loads((ROOT / "tests" / "fixtures" / "id_baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(item_table, {name: int(value) for name, value in baseline["research_items"].items()})
        self.assertEqual(location_table, {name: int(value) for name, value in baseline["research_locations"].items()})
        from valheimapworld.Drops import boss_item_table, drop_item_table, drop_location_table

        self.assertEqual(drop_item_table, {name: int(value) for name, value in baseline["drop_items"].items()})
        self.assertEqual(drop_location_table, {name: int(value) for name, value in baseline["drop_locations"].items()})
        self.assertEqual(boss_item_table, {name: int(value) for name, value in baseline["boss_items"].items()})
        goals = {goal.location: goal.location_id for goal in GOALS}
        self.assertEqual(goals, {name: int(value) for name, value in baseline["goal_locations"].items()})
        self.assertEqual(baseline["victory_item"]["Victory"], 4500)

    def test_lookup_is_by_name_not_row_position(self):
        names = list(item_table)
        self.assertEqual(item_table["Crafting"], 2000)
        self.assertEqual(item_table[names[10]], json.loads(
            (ROOT / "tests" / "fixtures" / "id_baseline.json").read_text(encoding="utf-8")
        )["research_items"][names[10]])
        reversed_ids = resolve_section("research_items", list(reversed(names)))
        self.assertEqual(reversed_ids[0], item_table[names[-1]])
        self.assertEqual(reversed_ids[-1], item_table[names[0]])

    def test_duplicate_name_and_missing_name_are_rejected(self):
        with self.assertRaises(RuntimeError):
            resolve_section("research_items", ["Crafting", "Crafting"])
        with self.assertRaises(RuntimeError):
            resolve_section("research_items", ["Crafting"])

    def test_empty_research_prerequisites_are_frozensets(self):
        source = (ROOT / "valheimapworld" / "Parents.py").read_text(encoding="utf-8")
        ast.parse(source, filename="Parents.py")
        for name in ("Axes Tier 1", "Clubs Tier 1", "Crafting", "Warmth Tier 1"):
            self.assertIn(f"'{name}': frozenset()", source)


class TierDoorTests(unittest.TestCase):
    def test_csharp_tier_doors_match_region_arrows(self):
        regions = (ROOT / "valheimapworld" / "Regions.py").read_text(encoding="utf-8")
        block = regions.split("region_txt = '''", 1)[1].split("'''", 1)[0]
        doors = {}
        for line in block.strip().splitlines():
            if not line or line.startswith("//"):
                continue
            parts = [part.strip() for part in line.split(",")]
            destination = parts[1]
            if not destination.startswith("Tier"):
                continue
            tier = int(destination[4:])
            items = []
            for index in range(2, len(parts), 2):
                items.append(parts[index])
            if items:
                doors[tier] = items

        source = (ROOT / "src" / "ValehimRandomizer.cs").read_text(encoding="utf-8")
        body = source.split("TierDoorItems", 1)[1].split(";", 1)[0]
        found = {}
        import re
        for tier, raw in re.findall(r"\{\s*(\d+)\s*,\s*new\[\]\s*\{([^}]*)\}\s*\}", body):
            names = re.findall(r'"([^"]+)"', raw)
            found[int(tier)] = names
        self.assertEqual(found, doors)


if __name__ == "__main__":
    unittest.main()
