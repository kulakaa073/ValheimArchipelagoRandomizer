from typing import Dict, List, NamedTuple, Callable, TYPE_CHECKING

from .Parents import PARENT_CLOSURE, RESEARCH_PARENTS
from BaseClasses import Region, Entrance, CollectionState, Item, ItemClassification

if TYPE_CHECKING:
    from . import ValheimWorld


class ValheimConnection(NamedTuple):
    destination: str  # Name of the region the connection leads to
    required_items: Dict[str, int]  # Item name → Count required


class ValheimRegion(NamedTuple):
    connections: List[ValheimConnection]  # List of connections from this region


def create_connection_rule(required_items: Dict[str, int], world: "ValheimWorld") -> Callable[[CollectionState], bool]:
    """
    Generate an access rule for a connection based on required items.
    """
    def rule(state: CollectionState) -> bool:
        return state.has_all_counts(required_items, world.player)
    return rule


# Define regions and their connections parsed from a text file
region_data_table: Dict[str, ValheimRegion] = {}

# Example region connections text data
region_txt = '''
Menu,Tier0
Tier0,Tier1,Crafting,1
Tier1,Tier2,Axes Tier 1,1,Troll Armor,1,Cooking Station,1,Bed Tier 1,1,Warmth Tier 1,1
Tier2,Tier3,Pickaxes Tier 1,1,Boat Tier 1,1,Smelter,1,Forge,1
Tier3,Tier4,Bronze,1
Tier4,Tier5,Axes Tier 2,1
Tier5,Tier6,Pickaxes Tier 2,1
Tier6,Tier7,Pickaxes Tier 3,1,Forge Upgrade 1,1,Nails Tier 2,1
Tier7,Tier8,Artisan Table,1,Blast Furnace,1
Tier8,Tier9,Axes Tier 4,1,Wisp Fountain,1,Wisplight,1,Forge Upgrade 2,1,Forge Upgrade 3,1,Spinning Wheel,1
Tier9,Tier10,Pickaxes Tier 4,1
Tier10,Tier11,Ceramic Plates,1,Boat Tier 4,1,Artisan Press,1
Tier11,Tier12,Siege,1,Snow Shovel,1
'''

# Parse region data
for line in region_txt.strip().splitlines():
    if not line or line.startswith("//"):
        continue

    parts = line.split(",")
    if len(parts) < 2:
        print(f"Malformed line: {line}")  # Debugging output
        continue

    source_region = parts[0].strip()
    destination_region = parts[1].strip()
    required_items = {}

    # Parse item requirements if available
    if len(parts) > 2:
        for i in range(2, len(parts), 2):
            item = parts[i].strip()
            count = int(parts[i + 1].strip())
            required_items[item] = count

    # Ensure the source region exists
    if source_region not in region_data_table:
        region_data_table[source_region] = ValheimRegion(connections=[])

    # Add the connection to the source region
    region_data_table[source_region].connections.append(
        ValheimConnection(destination=destination_region, required_items=required_items)
    )

    # Ensure the destination region exists (even if it has no connections initially)
    if destination_region not in region_data_table:
        region_data_table[destination_region] = ValheimRegion(connections=[])


def create_regions(world: "ValheimWorld"):
    """
    Step 1: Create all regions and add them to the multiworld.
    """
    created_regions = {
        region_name: Region(region_name, world.player, world.multiworld)
        for region_name in region_data_table
    }
    world.multiworld.regions.extend(created_regions.values())

    """
    Step 2: Add connections between regions using entrances.
    """
    for region_name, region in region_data_table.items():
        source_region = created_regions[region_name]

        for connection in region.connections:
            destination_region = created_regions[connection.destination]

            # Create an entrance in the source region leading to the destination
            entrance_name = f"{source_region.name} -> {destination_region.name}"
            entrance = Entrance(world.player, entrance_name, source_region)

            # Connect the entrance to the destination region
            entrance.connect(destination_region)

            # The bench mode does not change these arrows. Materials and natural
            # still decide recipe visibility on the client.
            if connection.required_items:
                entrance.access_rule = create_connection_rule(connection.required_items, world)

            # Add the entrance to the source region's exits
            source_region.exits.append(entrance)


def apply_default_parent_rules(world: "ValheimWorld") -> None:
    """Default access can send a research only after its parent items arrive."""
    if int(world.options.research_access.value) != 0:
        return
    player = world.player
    for location in world.multiworld.get_locations(player):
        parents = RESEARCH_PARENTS.get(location.name)
        if not parents:
            continue
        # A one-parent entry written as ('Name') is a string. has_all would
        # then require an item for each letter.
        if isinstance(parents, str):
            parents = (parents,)
        needed = tuple(parents)
        location.access_rule = lambda state, needed=needed, player=player: state.has_all(needed, player)


def promote_parent_items(world: "ValheimWorld") -> None:
    """Default access treats a parent as a key, so the filler must be able to see it.

    Archipelago only records progression items. A Useful parent would make every
    check that needs it unreachable, and generation would fail.
    """
    if int(world.options.research_access.value) != 0:
        return
    needed = {parent for parents in RESEARCH_PARENTS.values() for parent in parents}
    for item in world.multiworld.itempool:
        if item.player == world.player and item.name in needed and not item.advancement:
            item.classification |= ItemClassification.progression


def place_sequential_tier_items(world: "ValheimWorld") -> None:
    """Put each door's items on empty locations in the tier that opens that door."""
    if not world.options.sequential_tiers.value:
        return

    # Door items are locked into the region that opens the next one. A check in
    # that region cannot require a door that is locked here or further on, or
    # the two locks close a loop.
    region_tier = {
        name: int(name[4:]) for name in region_data_table if name.startswith("Tier")
    }
    door_tier: Dict[str, int] = {}
    for region_name, region in region_data_table.items():
        here = region_tier.get(region_name, -1)
        for connection in region.connections:
            for item_name in connection.required_items:
                door_tier[item_name] = here

    respect_parents = int(world.options.research_access.value) == 0
    for region_name, region in region_data_table.items():
        for connection in region.connections:
            if not connection.required_items:
                continue
            source = world.multiworld.get_region(region_name, world.player)
            slots = [loc for loc in source.locations if loc.item is None]
            needed: List[str] = []
            for item_name, count in connection.required_items.items():
                needed.extend([item_name] * count)
            here = region_tier.get(region_name, -1)
            open_slots = list(slots)
            chosen = []
            for item_name in needed:
                slot = None
                for loc in open_slots:
                    if respect_parents and _slot_needs_later_door(loc.name, item_name, door_tier, here):
                        continue
                    slot = loc
                    break
                if slot is None:
                    raise ValueError(
                        f"Sequential tiers: {region_name} cannot place '{item_name}' "
                        f"without putting it behind a research that needs it."
                    )
                open_slots.remove(slot)
                chosen.append((item_name, slot))
            for item_name, slot in chosen:
                slot.place_locked_item(take_pool_item(world, item_name))


def _slot_needs_later_door(location_name: str, item_name: str, door_tier: Dict[str, int], here: int) -> bool:
    blocked = PARENT_CLOSURE.get(location_name, ())
    if item_name in blocked:
        return True
    return any(door_tier.get(ancestor, -1) >= here for ancestor in blocked)


def take_pool_item(world: "ValheimWorld", item_name: str) -> Item:
    for item in world.multiworld.itempool:
        if item.player == world.player and item.name == item_name:
            world.multiworld.itempool.remove(item)
            return item
    raise ValueError(f"Sequential tiers could not find '{item_name}' in this world's item pool.")