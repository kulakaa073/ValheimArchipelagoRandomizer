"""Minimal stand-ins so the world modules import without an Archipelago checkout.

Generation tests use these to build regions, locations, and the item pool. They are
not the Archipelago filler. When BaseClasses is already installed, install() does nothing.
"""
from __future__ import annotations

import enum
import sys
import types


class ItemClassification(enum.IntFlag):
    filler = 0
    progression = 1
    useful = 2
    trap = 4


class LocationProgressType:
    DEFAULT = 1
    EXCLUDED = 2
    PRIORITY = 3


class Item:
    def __init__(self, name, classification, code, player):
        self.name = name
        self.classification = classification
        self.code = code
        self.player = player

    @property
    def advancement(self):
        return bool(self.classification & ItemClassification.progression)


class Location:
    def __init__(self, player, name, address, parent):
        self.player = player
        self.name = name
        self.address = address
        self.parent_region = parent
        self.progress_type = LocationProgressType.DEFAULT
        self.item = None
        self.locked = False
        self.access_rule = lambda state: True
        self.item_rule = lambda item: True

    def place_locked_item(self, item):
        self.item = item
        self.locked = True


class Entrance:
    def __init__(self, player, name, parent):
        self.player = player
        self.name = name
        self.parent_region = parent
        self.connected_region = None
        self.access_rule = lambda state: True

    def connect(self, region):
        self.connected_region = region


class Region:
    def __init__(self, name, player, multiworld):
        self.name = name
        self.player = player
        self.multiworld = multiworld
        self.locations = []
        self.exits = []


class CollectionState:
    def __init__(self):
        self.items = {}
        self.reached = set()

    def has(self, name, player):
        return self.items.get((name, player), 0) > 0

    def has_all(self, names, player):
        return all(self.has(name, player) for name in names)

    def has_all_counts(self, counts, player):
        return all(self.items.get((name, player), 0) >= count for name, count in counts.items())

    def can_reach_location(self, name, player):
        return (name, player) in self.reached


class MultiWorld:
    def __init__(self):
        self.regions = []
        self.itempool = []
        self.completion_condition = {}

    def get_region(self, name, player):
        for region in self.regions:
            if region.name == name and region.player == player:
                return region
        raise KeyError(name)

    def get_locations(self, player):
        found = []
        for region in self.regions:
            if region.player != player:
                continue
            found.extend(region.locations)
        return found


class World:
    def __init__(self):
        self.player = 1
        self.multiworld = MultiWorld()
        self.options = None


class WebWorld:
    pass


class Tutorial:
    def __init__(self, *args, **kwargs):
        pass


class Toggle:
    def __init__(self, value=0):
        self.value = value

    def __bool__(self):
        return bool(self.value)


class Choice:
    def __init__(self, value=0):
        self.value = value


class PerGameCommonOptions:
    pass


def install() -> None:
    existing = sys.modules.get("BaseClasses")
    if existing is not None and hasattr(existing, "Region") and hasattr(existing, "Item"):
        return

    base = types.ModuleType("BaseClasses")
    base.Item = Item
    base.ItemClassification = ItemClassification
    base.Location = Location
    base.LocationProgressType = LocationProgressType
    base.Region = Region
    base.Entrance = Entrance
    base.CollectionState = CollectionState
    base.Tutorial = Tutorial
    sys.modules["BaseClasses"] = base

    worlds = types.ModuleType("worlds")
    auto = types.ModuleType("worlds.AutoWorld")
    auto.World = World
    auto.WebWorld = WebWorld
    worlds.AutoWorld = auto
    sys.modules["worlds"] = worlds
    sys.modules["worlds.AutoWorld"] = auto

    options = types.ModuleType("Options")
    options.Toggle = Toggle
    options.Choice = Choice
    options.PerGameCommonOptions = PerGameCommonOptions
    sys.modules["Options"] = options
