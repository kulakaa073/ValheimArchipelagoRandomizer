from typing import NamedTuple

from BaseClasses import Item, ItemClassification, Location, LocationProgressType, Tutorial
from worlds.AutoWorld import WebWorld, World
from .Options import ValheimOptions
from .Regions import create_regions, place_sequential_tier_items, apply_default_parent_rules, promote_parent_items
from .Locations import create_locations, location_table
from .Items import create_items, item_table
from .Ids import assert_unique_spaces, require_id
from .Drops import (
    BOSS_DROPS,
    create_drop_items,
    create_drop_locations,
    create_boss_items,
    create_boss_locations,
    allow_boss_drops_through_tier,
    drop_item_table,
    drop_location_table,
    boss_item_table,
)


class ValheimWebWorld(WebWorld):
    theme = "ice"
    bug_report_page = "https://github.com/kulakaa073/ValheimArchipelagoRandomizer/issues"
    rich_text_options_doc = True
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up Valheim for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["ShadeNoob"],
        )
    ]

# OnDeath sets Character.m_defeatSetGlobalKey on the world.
# Kall's chained form sets defeated_frozenking. His last phase sets defeated_frozenking_p3.
GOAL_ITEM_NAME = "Victory"
GOAL_ITEM_ID = 4500


class BossGoal(NamedTuple):
    location: str
    key: str
    region: str
    location_id: int


# Index matches Options.Goal. Defeat Kall keeps id 5000 so older seeds still resolve.
# Boss regions follow the v5.1 map where already remapped; Kall kill stays Defeat Kall.
# Journey to Valhalla is the Sacrificial Blood → Meadows platform → Valkyrie credits ending.
GOALS = (
    BossGoal("Defeat Eikthyr", "defeated_eikthyr", "Tier2", 5001),
    BossGoal("Defeat the Elder", "defeated_gdking", "Tier3", 5002),
    BossGoal("Defeat Bonemass", "defeated_bonemass", "Tier6", 5003),
    BossGoal("Defeat Moder", "defeated_dragon", "Tier7", 5004),
    BossGoal("Defeat Yagluth", "defeated_goblinking", "Tier8", 5005),
    BossGoal("Defeat the Queen", "defeated_queen", "Tier10", 5006),
    BossGoal("Defeat Fader", "defeated_fader", "Tier12", 5007),
    BossGoal("Defeat Kall", "defeated_frozenking_p3", "Tier15", 5000),
    BossGoal("Journey to Valhalla", "ap_ending_valhalla", "Tier15", 5008),
)


class ValheimWorld(World):
    """
    Valheim survival crafting: research, trophies, and optional gather checks through Archipelago.
    Progression uses tier doors. Goals are a boss kill or Journey to Valhalla. Requires the
    Valheim Archipelago Randomizer BepInEx mod.
    """
    game = "Valheim"
    web = ValheimWebWorld()
    options_dataclass = ValheimOptions
    options: ValheimOptions
    location_name_to_id = {**location_table, **drop_location_table, **{goal.location: goal.location_id for goal in GOALS}}
    item_name_to_id = {**item_table, **drop_item_table, **boss_item_table, GOAL_ITEM_NAME: GOAL_ITEM_ID}
    topology_present = True

    def create_regions(self):
        """
        Creates regions and locations for the world.
        `create_regions` internally calls `create_locations`.
        """
        create_regions(self)
        create_locations(self)
        if self.options.boss_checks:
            create_boss_locations(self)
            # Ending goal is not a boss kill location — add it when selected.
            goal = selected_goal(self)
            if goal.location not in {boss.location for boss in BOSS_DROPS}:
                create_goal_location(self, goal, lock_victory=True)
        else:
            create_goal(self)
        if self.options.drop_checks:
            create_drop_locations(self)

    def set_rules(self):
        apply_default_parent_rules(self)
        promote_parent_items(self)
        goal = selected_goal(self)
        player = self.player
        if self.options.boss_checks:
            location = goal.location
            self.multiworld.completion_condition[player] = (
                lambda state, loc=location, p=player: state.can_reach_location(loc, p)
            )
        else:
            self.multiworld.completion_condition[player] = (
                lambda state, p=player: state.has(GOAL_ITEM_NAME, p)
            )

    def completion_condition(self, state) -> bool:
        if self.options.boss_checks:
            goal = selected_goal(self)
            return state.can_reach_location(goal.location, self.player)
        return state.has(GOAL_ITEM_NAME, self.player)

    def create_items(self):
        """
        Populates the item pool with items for the world.
        """
        create_items(self)
        if self.options.boss_checks:
            create_boss_items(self)
        if self.options.drop_checks:
            create_drop_items(self)

    def pre_fill(self):
        if self.options.boss_checks:
            allow_boss_drops_through_tier(self)
        place_sequential_tier_items(self)

    def fill_slot_data(self):
        # Archipelago 0.6 leaves this empty unless the world fills it.
        # The client uses these values. Gather locations are the fallback for older seeds.
        goal = selected_goal(self)
        return {
            "drop_checks": int(bool(self.options.drop_checks.value)),
            "research_access": int(self.options.research_access.value),
            "sequential_tiers": int(bool(self.options.sequential_tiers.value)),
            "goal": int(self.options.goal.value),
            "goal_key": goal.key,
            "goal_location": goal.location,
            "boss_drops": int(bool(self.options.boss_checks.value)),
        }


def create_goal(world: "ValheimWorld") -> None:
    create_goal_location(world, selected_goal(world), lock_victory=True)


def create_goal_location(world: "ValheimWorld", goal: BossGoal, lock_victory: bool) -> None:
    region = world.multiworld.get_region(goal.region, world.player)
    location = Location(world.player, goal.location, goal.location_id, region)
    location.progress_type = LocationProgressType.PRIORITY
    region.locations.append(location)
    if lock_victory:
        victory = Item(GOAL_ITEM_NAME, ItemClassification.progression, GOAL_ITEM_ID, world.player)
        location.place_locked_item(victory)


def selected_goal(world: "ValheimWorld") -> BossGoal:
    index = int(world.options.goal.value)
    if index < 0 or index >= len(GOALS):
        return GOALS[-1]
    return GOALS[index]


for _goal in GOALS:
    require_id("goal_locations", _goal.location, _goal.location_id)
require_id("victory_item", GOAL_ITEM_NAME, GOAL_ITEM_ID)
assert_unique_spaces()

