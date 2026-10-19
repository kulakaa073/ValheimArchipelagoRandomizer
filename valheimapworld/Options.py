from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Toggle


class DropChecks(Toggle):
    """First time you pick up a raw drop (meat, hide, berries, and other forage or creature drops), that pickup is a location.
    You keep the drop. The matching item is a bundle of that same material."""
    display_name = "Drop Checks"


class ResearchAccess(Choice):
    """How a research recipe appears on the bench.
    default: the recipe appears after you receive every parent research.
    tier: the recipe appears after you receive the items that open its tier.
    materials: the recipe appears once you have found its materials. Tier doors are removed.
    natural: crafting a research opens the next recipes. Receiving a parent leaves those recipes closed. The received item grants the gear. Tier doors are removed."""
    display_name = "Research Access"
    option_default = 0
    option_tier = 1
    option_materials = 2
    option_natural = 3
    default = 0


class SequentialTiers(Toggle):
    """Place the items that open the next tier into the previous tier, in this world.
    Tier 0 checks unlock Tier 1, Tier 1 checks unlock Tier 2, and so on.
    This still runs when Research Access is materials or natural. Those modes only change when the bench shows a recipe."""
    display_name = "Sequential Tiers"


class BossChecks(Toggle):
    """Each boss kill is a check. The unique drop is removed from the corpse.
    That drop can be placed on any check from tier 0 through the boss's own tier.
    The amount follows the world resource rate. The swamp key and the wishbone also follow the player count.
    Off: the corpse still drops the item, and only the goal kill is a location."""
    display_name = "Boss Checks"
    default = 1


class Goal(Choice):
    """Which boss kill finishes the seed.
    eikthyr, elder, bonemass, moder, yagluth, queen, fader, or kall.
    Kall is his last phase only.
    With Boss Checks on, every boss kill is a location and that drop is its reward."""
    display_name = "Goal"
    option_eikthyr = 0
    option_elder = 1
    option_bonemass = 2
    option_moder = 3
    option_yagluth = 4
    option_queen = 5
    option_fader = 6
    option_kall = 7
    default = 7


@dataclass
class ValheimOptions(PerGameCommonOptions):
    drop_checks: DropChecks
    boss_checks: BossChecks
    research_access: ResearchAccess
    sequential_tiers: SequentialTiers
    goal: Goal
