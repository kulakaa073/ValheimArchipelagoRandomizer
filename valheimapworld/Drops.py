"""Optional gather checks. Off unless the Drop Checks world option is enabled."""
from typing import Dict, List, NamedTuple, TYPE_CHECKING

from BaseClasses import Item, ItemClassification, Location, LocationProgressType

if TYPE_CHECKING:
    from . import ValheimWorld

# Prefab id, player-facing name, logic tier, bundle size granted by the item.
DROP_ROWS = [
    ('Raspberry', 'Raspberries', 0, 15),
    ('Mushroom', 'Mushroom', 0, 10),
    ('Honey', 'Honey', 0, 5),
    ('Dandelion', 'Dandelion', 0, 10),
    ('LeatherScraps', 'Leather Scraps', 0, 10),
    ('RawMeat', 'Raw Meat', 0, 5),
    ('DeerMeat', 'Deer Meat', 0, 5),
    ('DeerHide', 'Deer Hide', 0, 5),
    ('Feathers', 'Feathers', 0, 10),
    ('Resin', 'Resin', 0, 10),
    ('NeckTail', 'Neck Tail', 0, 5),
    ('Blueberries', 'Blueberries', 1, 15),
    ('Thistle', 'Thistle', 1, 8),
    ('MushroomYellow', 'Yellow Mushroom', 1, 8),
    ('GreydwarfEye', 'Greydwarf Eye', 1, 10),
    ('BoneFragments', 'Bone Fragments', 1, 8),
    ('TrollHide', 'Troll Hide', 1, 3),
    ('BjornHide', 'Bear Hide', 1, 3),
    ('BjornMeat', 'Bear Meat', 1, 3),
    ('Bloodbag', 'Bloodbag', 4, 6),
    ('Entrails', 'Entrails', 4, 6),
    ('Guck', 'Guck', 4, 10),
    ('Ooze', 'Ooze', 4, 6),
    ('SerpentMeat', 'Serpent Meat', 4, 3),
    ('SerpentScale', 'Serpent Scale', 4, 5),
    ('Chitin', 'Chitin', 4, 5),
    ('WolfMeat', 'Wolf Meat', 7, 4),
    ('WolfPelt', 'Wolf Pelt', 7, 4),
    ('WolfFang', 'Wolf Fang', 7, 5),
    ('WolfClaw', 'Wolf Claw', 7, 6),
    ('WolfHairBundle', 'Wolf Hair', 7, 10),
    ('FreezeGland', 'Freeze Gland', 7, 4),
    ('Cloudberry', 'Cloudberries', 8, 10),
    ('LoxMeat', 'Lox Meat', 8, 4),
    ('LoxPelt', 'Lox Pelt', 8, 4),
    ('Needle', 'Needle', 8, 8),
    ('RoyalJelly', 'Royal Jelly', 9, 6),
    ('Sap', 'Sap', 9, 6),
    ('ScaleHide', 'Scale Hide', 9, 9),
    ('GiantBloodSack', 'Giant Blood Sack', 9, 4),
    ('Bilebag', 'Bilebag', 9, 9),
    ('BugMeat', 'Seeker Meat', 9, 4),
    ('HareMeat', 'Hare Meat', 9, 4),
    ('MushroomJotunPuffs', 'Jotun Puffs', 9, 6),
    ('MushroomMagecap', 'Magecap', 9, 8),
    ('AsksvinMeat', 'Asksvin Meat', 11, 4),
    ('AskHide', 'Ask Hide', 11, 4),
    ('Vineberry', 'Vineberries', 11, 8),
    ('MushroomSmokePuff', 'Smoke Puff', 11, 6),
    ('Fiddleheadfern', 'Fiddlehead', 11, 10),
    ('BoneMawSerpentMeat', 'Bonemaw Meat', 11, 3),
    ('BonemawSerpentTooth', 'Bonemaw Tooth', 11, 4),
    ('CharredBone', 'Charred Bone', 11, 6),
    ('CelestialFeather', 'Celestial Feather', 11, 3),
    ('MorgenSinew', 'Morgen Sinew', 11, 2),
    ('Lingonberry', 'Lingonberries', 12, 10),
    ('MooseMeat', 'Moose Meat', 12, 4),
    ('MooseHide', 'Moose Hide', 12, 4),
    ('MooseSinew', 'Moose Sinew', 12, 2),
    ('SealBlubber', 'Seal Blubber', 12, 4),
    ('SealHide', 'Seal Hide', 12, 4),
    ('ElakingHairBundle', 'Elaking Hair', 12, 8),
    ('MoleClaws', 'Mole Claws', 12, 2),
    ('Acorn', 'Acorns', 0, 20),
    ('Amber', 'Amber', 1, 5),
    ('AmberPearl', 'Amber Pearl', 1, 10),
    ('AncientCoin', 'Ancient Coin', 1, 20),
    ('AncientGemstoneBlack', 'Draumyx', 12, 5),
    ('AncientGemstoneGreen', 'Grimvarn', 12, 5),
    ('AncientGemstoneOrange', 'Solryth', 12, 5),
    ('AncientGemstonePurple', 'Veydris', 12, 5),
    ('AskBladder', 'Asksvin Bladder', 11, 10),
    ('AsksvinCarrionNeck', 'Asksvin Neck', 11, 10),
    ('AsksvinCarrionPelvic', 'Asksvin Pelvis', 11, 10),
    ('AsksvinCarrionRibcage', 'Asksvin Ribcage', 11, 10),
    ('AsksvinCarrionSkull', 'Asksvin Skull', 11, 10),
    ('AxeHead1', 'Curious Axe Head', 7, 3),
    ('AxeHead2', 'Mysterious Axe Head', 7, 3),
    ('BarkaBranch', 'Frozen Branch', 12, 10),
    ('Barley', 'Barley', 8, 20),
    ('BeechSeeds', 'Beech Seeds', 0, 20),
    ('BellFragment', 'Bell Fragment', 11, 3),
    ('BirchSeeds', 'Birch Seeds', 0, 20),
    ('BjornPaw', 'Bear Paw', 1, 10),
    ('BlackCore', 'Black Core', 9, 7),
    ('BlackMarble', 'Black Marble', 10, 10),
    ('BlackMetal', 'Black Metal', 8, 5),
    ('BlackMetalScrap', 'Black Metal Scrap', 8, 5),
    ('Blackwood', 'Ashwood', 11, 10),
    ('BlobVial', 'Corked Vial', 4, 3),
    ('Bronze', 'Bronze', 3, 5),
    ('BronzeNails', 'Bronze Nails', 3, 20),
    ('BronzeScrap', 'Scrap Bronze', 3, 5),
    ('CandleWick', 'Candle Wick', 4, 10),
    ('Carapace', 'Carapace', 9, 10),
    ('CarrotSeeds', 'Carrot Seeds', 4, 20),
    ('CeramicPlate', 'Ceramic Plate', 11, 5),
    ('Chain', 'Chain', 4, 10),
    ('CharcoalResin', 'Charcoal Resin', 11, 10),
    ('CharredCogwheel', 'Charred Cogwheel', 11, 3),
    ('Charredskull', 'Charred Skull', 11, 10),
    ('Coal', 'Coal', 1, 10),
    ('Coins', 'Coins', 1, 25),
    ('Copper', 'Copper', 3, 5),
    ('CopperOre', 'Copper Ore', 3, 5),
    ('CopperScrap', 'Copper Scrap', 3, 5),
    ('CrownJewel', 'Crown Jewel', 12, 1),
    ('Crystal', 'Crystal', 7, 10),
    ('CuredSquirrelHamstring', 'Cured Squirrel Hamstring', 4, 10),
    ('DvergrKeyFragment', 'Sealbreaker Fragment', 9, 9),
    ('DvergrNeedle', 'Dvergr Extractor', 9, 5),
    ('DyrnwynBladeFragment', 'Dyrnwyn Blade Fragment', 11, 1),
    ('DyrnwynHiltFragment', 'Dyrnwyn Hilt Fragment', 11, 1),
    ('DyrnwynTipFragment', 'Dyrnwyn Tip Fragment', 11, 1),
    ('Ectoplasm', 'Ectoplasm', 1, 10),
    ('Eitr', 'Refined Eitr', 10, 5),
    ('ElderBark', 'Ancient Bark', 5, 10),
    ('FaderEmber', 'Embers', 11, 10),
    ('FineWood', 'Finewood', 12, 10),
    ('FirCone', 'Fir Cone', 0, 20),
    ('FirConeFrost', 'Timberwood Cone', 12, 20),
    ('FlametalNew', 'Flametal', 11, 5),
    ('FlametalOreNew', 'Flametal Ore', 11, 5),
    ('Flax', 'Flax', 8, 20),
    ('Flint', 'Flint', 1, 6),
    ('FragrantBundle', 'Fragrant Bundle', 8, 10),
    ('FreshSeaweed', 'Fresh Seaweed', 4, 10),
    ('FrostCore', 'Frostcore', 12, 10),
    ('Frostwood', 'Timberwood', 12, 10),
    ('FrozenFuel', 'Liquid Frost', 12, 10),
    ('GemstoneBlue', 'Iolite', 11, 10),
    ('GemstoneGreen', 'Jade', 11, 10),
    ('GemstoneRed', 'Bloodstone', 11, 10),
    ('Gold', 'Bloodgold', 12, 20),
    ('GoldOre', 'Petrified Tissue', 12, 5),
    ('Grausten', 'Grausten', 12, 10),
    ('Hook', 'Hook', 12, 10),
    ('Ice', 'Ice', 12, 10),
    ('Iron', 'Iron', 6, 15),
    ('IronNails', 'Iron Nails', 6, 20),
    ('IronOre', 'Iron Ore', 5, 5),
    ('Ironpit', 'Iron Pit', 6, 3),
    ('IronScrap', 'Scrap Iron', 6, 5),
    ('JuteBlue', 'Blue Jute', 9, 10),
    ('JuteRed', 'Red Jute', 7, 10),
    ('KaleSeeds', 'Kale Seeds', 12, 20),
    ('Leatherstraps', 'Leather Straps', 12, 10),
    ('LinenThread', 'Linen Thread', 8, 10),
    ('Mandible', 'Mandible', 9, 10),
    ('MechanicalSpring', 'Mechanical Spring', 9, 3),
    ('MemorialCoal', 'Memorial Coal', 12, 3),
    ('MoldArmorGoldChest', 'Mould: Breastplate of the Protector', 12, 1),
    ('MoldArmorGoldHelmet', 'Mould: Helmet of the Protector', 12, 1),
    ('MoldArmorGoldLegs', 'Mould: Trousers of the Protector', 12, 1),
    ('MoldArmorMageChest', 'Mould: Robes of the Caller', 12, 1),
    ('MoldArmorMageHelmet', 'Mould: Headdress of the Caller', 12, 1),
    ('MoldArmorMageLegs', 'Mould: Trousers of the Caller', 12, 1),
    ('MoldArmormediumChest', 'Mould: Chestpiece of the Vanguard', 12, 1),
    ('MoldArmorMediumHelmet', 'Mould: Hood of the Vanguard', 12, 1),
    ('MoldArmorMediumLegs', 'Mould: Trousers of the Vanguard', 12, 1),
    ('MoldAtgeir', 'Mould: Nord Atgeir', 12, 1),
    ('MoldAxe', 'Mould: Nord Axe', 12, 1),
    ('MoldAxe2H', 'Mould: Nord Greataxe', 12, 1),
    ('MoldBow', 'Mould: Nord Bow', 12, 1),
    ('MoldCrossbow', 'Mould: Nord Crossbow', 12, 1),
    ('MoldFistweapon', 'Mould: Nord Knucklechains', 12, 1),
    ('MoldKeys', 'Mould: Intricate Key', 12, 1),
    ('MoldKnife', 'Mould: Nord Dagger', 12, 1),
    ('MoldMace', 'Mould: Nord Mace', 12, 1),
    ('MoldMace2H', 'Mould: Nord Sledge', 12, 1),
    ('MoldShieldBuckler', 'Mould: Nord Buckler', 12, 1),
    ('MoldShieldRound', 'Mould: Nord Shield', 12, 1),
    ('MoldShieldTower', 'Mould: Nord Greatshield', 12, 1),
    ('MoldSpear', 'Mould: Nord Spear', 12, 1),
    ('MoldStafffrostorbs', 'Mould: Northern Vengeance', 12, 1),
    ('MoldStaffOrbofAhri', 'Mould: Echo Spike', 12, 1),
    ('MoldStaffspiritcaller', 'Mould: Spirit Caller', 12, 1),
    ('MoldStaffthunderblood', 'Mould: Lightning Strike', 12, 1),
    ('MoldSword', 'Mould: Nord Sword', 12, 1),
    ('MoldSword2H', 'Mould: Nord Greatsword', 12, 1),
    ('MoltenCore', 'Molten Core', 11, 8),
    ('MorgenHeart', 'Morgen Heart', 11, 10),
    ('NornThread', 'Nornathread', 12, 10),
    ('OatSeeds', 'Oat Seeds', 12, 20),
    ('Obsidian', 'Obsidian', 7, 10),
    ('OnionSeeds', 'Onion Seeds', 7, 20),
    ('OozeMork', 'Dead Pulp', 11, 10),
    ('OrbFrostFire', 'Frostfire Essence', 12, 10),
    ('OrbThunderBlood', 'Thunderblood Essence', 12, 10),
    ('PineCone', 'Pine Cone', 1, 20),
    ('Pot_Shard_Green', 'Pot Shard', 11, 10),
    ('PoteitrSeeds', 'Seed Poteitr', 12, 20),
    ('PowderedDragonEgg', 'Powdered Dragon Eggshells', 4, 10),
    ('ProustitePowder', 'Proustite Powder', 11, 10),
    ('PungentPebbles', 'Pungent Pebbles', 4, 10),
    ('QueenBee', 'Queen Bee', 1, 5),
    ('Root', 'Root', 4, 10),
    ('RoundLog', 'Corewood', 1, 10),
    ('Ruby', 'Ruby', 1, 5),
    ('SharpeningStone', 'Sharpening Stone', 7, 5),
    ('ShieldCore', 'Shield Core', 8, 5),
    ('Silver', 'Silver', 7, 5),
    ('SilverNecklace', 'Silver Necklace', 6, 5),
    ('SilverOre', 'Silver Ore', 7, 5),
    ('Softtissue', 'Soft Tissue', 10, 5),
    ('SpiceAshlands', 'Fiery Spice Powder', 11, 20),
    ('SpiceDeepNorth', 'Seasoning of the Gourd', 12, 20),
    ('SpiceForests', 'Woodland Herb Blend', 4, 20),
    ('SpiceMistlands', 'Herbs of the Hidden Hills', 10, 20),
    ('SpiceMountains', 'Mountain Peak Pepper Powder', 8, 20),
    ('SpiceOceans', "Seafarer's Herbs", 4, 20),
    ('SpicePlains', 'Grasslands Herbalist Harvest', 9, 20),
    ('Stone', 'Stone', 0, 20),
    ('SulfurStone', 'Sulfur', 11, 10),
    ('SurtlingCore', 'Surtling Core', 1, 5),
    ('Tar', 'Tar', 8, 10),
    ('Thunderstone', 'Thunder Stone', 4, 5),
    ('Tin', 'Tin', 3, 5),
    ('TinOre', 'Tin Ore', 8, 5),
    ('Turnip', 'Turnip', 4, 10),
    ('TurnipSeeds', 'Turnip Seeds', 11, 20),
    ('UndeadBjornRibcage', 'Vile Ribcage', 8, 10),
    ('Upgrader0Armor', 'Wooden Protection Idol', 0, 1),
    ('Upgrader0Weapon', 'Wooden Battle Idol', 0, 1),
    ('Upgrader1Armor', 'Bronze Protection Idol', 3, 1),
    ('Upgrader1Weapon', 'Bronze Battle Idol', 3, 1),
    ('Upgrader2Armor', 'Iron Protection Idol', 6, 1),
    ('Upgrader2Weapon', 'Iron Battle Idol', 6, 1),
    ('Upgrader3Armor', 'Silver Protection Idol', 7, 1),
    ('Upgrader3Weapon', 'Silver Battle Idol', 7, 1),
    ('Upgrader4Armor', 'Black Metal Protection Idol', 8, 1),
    ('Upgrader4Weapon', 'Black Metal Battle Idol', 8, 1),
    ('Upgrader5Armor', 'Black Marble Protection Idol', 10, 1),
    ('Upgrader5Weapon', 'Black Marble Battle Idol', 10, 1),
    ('Upgrader6Armor', 'Flametal Protection Idol', 11, 1),
    ('Upgrader6Weapon', 'Flametal Battle Idol', 11, 1),
    ('Upgrader7Armor', 'Bloodgold Protection Idol', 12, 1),
    ('Upgrader7Weapon', 'Bloodgold Battle Idol', 12, 1),
    ('VineberrySeeds', 'Vineberry Seeds', 11, 20),
    ('VineGreenSeeds', 'Ivy Seeds', 4, 20),
    ('Wisp', 'Wisp', 10, 10),
    ('WitheredBone', 'Withered Bone', 6, 5),
    ('Wood', 'Wood', 0, 20),
    ('WrithanRoots', 'Writhan Roots', 12, 10),
    ('YggdrasilWood', 'Yggdrasil Wood', 9, 10),
    ('YmirRemains', 'Ymir Flesh', 4, 10),
    ('ChickenMeat', 'Chicken Meat', 8, 5),
    ('VoltureMeat', 'Volture Meat', 11, 4),
    ('GlowWorm', 'Luminous Larva', 9, 6),
    ('VoltureEgg', 'Volture Egg', 11, 3),
    ('ChickenEgg', 'Egg', 8, 3),
    ('Carrot', 'Carrot', 4, 10),
    ('Onion', 'Onion', 7, 10),
    ('Kale', 'Kale', 12, 10),
    ('Poteitr', 'Poteitr', 12, 10),
    ('DragonEgg', 'Dragon Egg', 7, 3),
    ('MushroomBzerker', 'Toadstool', 8, 3),
    ('Pukeberries', 'Bukeperries', 1, 8),
    ('RottenMeat', 'Rotten Meat', 1, 5),
    ('ScytheHandle', 'Scythe Handle', 8, 1),
]


class ValheimDrop(NamedTuple):
    item_id: str
    display_name: str
    tier: int
    amount: int
    location_id: int
    ap_item_id: int

    @property
    def check_name(self) -> str:
        return f"Gather: {self.display_name}"


def _build() -> List[ValheimDrop]:
    drops = []
    for index, (item_id, display_name, tier, amount) in enumerate(DROP_ROWS):
        drops.append(ValheimDrop(item_id, display_name, tier, amount, 6001 + index, 8001 + index))
    names = [d.check_name for d in drops]
    if len(names) != len(set(names)):
        raise RuntimeError("Duplicate gather check names")
    return drops


DROPS: List[ValheimDrop] = _build()
drop_location_table: Dict[str, int] = {drop.check_name: drop.location_id for drop in DROPS}
drop_item_table: Dict[str, int] = {drop.check_name: drop.ap_item_id for drop in DROPS}


def create_drop_locations(world: "ValheimWorld") -> None:
    for drop in DROPS:
        region = world.multiworld.get_region(f"Tier{drop.tier}", world.player)
        region.locations.append(Location(world.player, drop.check_name, drop.location_id, region))


def create_drop_items(world: "ValheimWorld") -> None:
    for drop in DROPS:
        world.multiworld.itempool.append(
            Item(drop.check_name, ItemClassification.useful, drop.ap_item_id, world.player)
        )


# The boss kill is a location. The unique drop is a progression item that can be
# placed on any check from tier 0 through this boss's tier. one_per_player matches
# the corpse: swamp key and wishbone.
# prefab, name, region, amount, creature, defeat key, location, location id, item id, one per player
class BossDrop(NamedTuple):
    item_id: str
    item_name: str
    region: str
    amount: int
    creature: str
    defeat_key: str
    location: str
    location_id: int
    ap_item_id: int
    one_per_player: bool


BOSS_DROPS: List[BossDrop] = [
    BossDrop("HardAntler", "Hard Antler", "Tier1", 3, "Eikthyr", "defeated_eikthyr", "Defeat Eikthyr", 5001, 7101, False),
    BossDrop("CryptKey", "Swamp Key", "Tier4", 1, "gd_king", "defeated_gdking", "Defeat the Elder", 5002, 7102, True),
    BossDrop("Wishbone", "Wishbone", "Tier6", 1, "Bonemass", "defeated_bonemass", "Defeat Bonemass", 5003, 7103, True),
    BossDrop("DragonTear", "Dragon Tear", "Tier8", 10, "Dragon", "defeated_dragon", "Defeat Moder", 5004, 7104, False),
    BossDrop("YagluthDrop", "Torn Spirit", "Tier9", 3, "GoblinKing", "defeated_goblinking", "Defeat Yagluth", 5005, 7105, False),
    BossDrop("QueenDrop", "Majestic Carapace", "Tier10", 5, "SeekerQueen", "defeated_queen", "Defeat the Queen", 5006, 7106, False),
    BossDrop("FaderDrop", "Kindled Ribs", "Tier11", 5, "Fader", "defeated_fader", "Defeat Fader", 5007, 7107, False),
    BossDrop("FrozenKingDrop", "Sacrificial Blood", "Tier12", 1, "FrozenKing_p3", "defeated_frozenking_p3", "Defeat Kall", 5000, 7108, False),
]

boss_item_table: Dict[str, int] = {boss.item_name: boss.ap_item_id for boss in BOSS_DROPS}
_boss_names = [boss.item_name for boss in BOSS_DROPS]
if len(_boss_names) != len(set(_boss_names)):
    raise RuntimeError("Duplicate boss item names")


def create_boss_locations(world: "ValheimWorld") -> None:
    for boss in BOSS_DROPS:
        region = world.multiworld.get_region(boss.region, world.player)
        location = Location(world.player, boss.location, boss.location_id, region)
        location.progress_type = LocationProgressType.PRIORITY
        region.locations.append(location)


def create_boss_items(world: "ValheimWorld") -> None:
    for boss in BOSS_DROPS:
        world.multiworld.itempool.append(
            Item(boss.item_name, ItemClassification.progression, boss.ap_item_id, world.player)
        )


def allow_boss_drops_through_tier(world: "ValheimWorld") -> None:
    """Let each boss drop land on any check from tier 0 through its own tier."""
    item_tier = {boss.item_name: int(boss.region[4:]) for boss in BOSS_DROPS}
    names = set(item_tier)
    player = world.player
    for location in world.multiworld.get_locations(player):
        region_name = location.parent_region.name
        if not region_name.startswith("Tier"):
            continue
        loc_tier = int(region_name[4:])
        previous = location.item_rule

        def rule(item, previous=previous, loc_tier=loc_tier, item_tier=item_tier, names=names, player=player):
            if item.player == player and item.name in names and item_tier[item.name] < loc_tier:
                return False
            return previous(item)

        location.item_rule = rule
