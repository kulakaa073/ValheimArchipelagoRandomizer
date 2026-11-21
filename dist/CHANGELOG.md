# Changelog

## 0.3.3

- Valhalla with Boss Checks on keeps Victory locked on the extra goal location.
- Research, gather, and boss ids are stored by name so inserting a row does not renumber older seeds.
- Tier door items match the region arrows through Tier 15.
- Missing or malformed research, trophy, and drop tables stop item grants instead of loading a sample file. The log names the file and line.
- Boss Checks on grants one vanilla bundle to the inventory. Boss Checks off leaves the corpse drop alone.
- One-per-player boss rewards use the vanilla player-count total once, instead of multiplying the rolled amount.
- Boss and gather rewards are only granted when the inventory has room for the whole amount (empty slots plus space in matching stacks). A reward that does not fit stays queued and is delivered once space is free, instead of arriving partly and losing the rest.
- Received items are queued off the Unity thread and applied a few per frame, by received-item index.
- Rewards waiting on a full inventory no longer block new items. Only one waiting item is retried per frame, so research unlocks and other new items still arrive.
- The "inventory full" warning is logged at most once every 30 seconds per item instead of every frame.
- Saves from older versions no longer get a second boss or gather reward on connect. Old unscoped reward keys are now recognized immediately, before the key migration runs.
- The key migration for older saves runs once per connection or world instead of on every check flush.
- Items from a closed or replaced Archipelago session can no longer enter the queue of the new session.
- The received-item backlog is synced right after login, so connecting while already in a world does not depend on a live item event arriving.
- The received-item sync is protected against a read error while the server is adding items. It also no longer risks an index-out-of-range error when an item arrives mid-read.
- Errors thrown while granting an item are logged once per item and the item stays queued, instead of failing silently.
- Fixed a possible null reference when the connection drops during a check flush.
- Archipelago check and reward keys include team and slot. Research unlock keys stay shared in a co-op world.


## 0.3.2

- Fixed randomized boss rewards being spawned at boss corpses when Boss Checks are enabled.
- Boss rewards are now granted directly to player inventory when Boss Checks are enabled.


## 0.3.1

- Fixed malformed empty research prerequisite sets.
- Regenerated the Archipelago world package.
- Fix Journey to Valhalla location issue.



## 0.3.0

- Research overhaul (v5.1): tiers, costs, and prereqs retuned across Meadows through Deep North; SoftProg station/upgrade lines; WrithanRoots swamp and JuteRed mountains placement
- Trophy and gather checks retiered to the T0–T15 map; Regions doors through Tier15
- Items, Locations, and Parents regenerated from research/trophies tables
- Deep North gold weapons split: base research keeps Uncooked + finished (T14); Enchanted researches (T15) gate Frostfire + Thunderblood behind the base line + Intricate Key
- Boss overhaul: Kall's Archipelago item is Crown Jewel; Sacrificial Blood always drops from the corpse for the ending and is not an AP item
- Boss progression rewards spawn on the boss corpse at vanilla amounts (no world resource-rate multiply). Swamp Key and Wishbone still scale with player count
- New goal `valhalla` — Journey to Valhalla: place Sacrificial Blood on the Meadows chiselled platform, talk to the Valkyrie, and clear the end credits
- Boss kill regions aligned to the T0–T15 map (Eikthyr T2 … Kall T15)
- Archipelago WebHost docs (`WebWorld`, game info, setup guide) and `archipelago.json` manifest for 0.6.8+ / 0.7.0 compatibility



## 0.2.35

- Trophy drops can stay as they are, double with pity capped at 10, or guarantee the first trophy from each creature
- Research costs can be halved. Half a cost rounds up, and a cost of 1 stays 1
- Health, stamina, and eitr regen from trophies is 50% per food



## 0.2.34

- Natural access opens the next research only after its parents are crafted. Receiving a parent still grants its gear



## 0.2.33

- The game sends each trophy's pity count to the tracker. The Trophy view has a Pity toggle that shows how many kills guarantee that drop



## 0.2.32

- Corewood Beams and Battleaxes Tier 3 had a blank parent, so those recipes never appeared. A blank parent is ignored



## 0.2.31

- A boss drop can be placed on any check from tier 0 through that boss's tier. The kill is no longer reserved for it



## 0.2.30

- Bog Witch and Haldor gather checks sit in the tier where that item can actually be gotten
- Toadstool and the scythe handle wait for Moder. The spices wait for the boss that unlocks them. Eggs and chicken meat are plains checks
- Ungated witch goods, Ymir flesh, and thunder stones are swamp checks



## 0.2.29

- Boss kills are a world option, on by default. Off, the corpse still drops its item and only the goal kill is a location



## 0.2.28

- Blue Mushroom is not placed in the world, so it is no longer a gather check



## 0.2.27

- Rock, Glowing Metal Ore, Ancient Metal, and Bonemaw Scale are no longer checks
- Chicken meat, volture meat, blue mushroom, luminous larva, eggs, crops, dragon eggs, toadstool, bukeperries, rotten meat, and the scythe handle are gather checks
- A boss kill is a check in that boss's tier. The unique drop no longer falls from the corpse, and the check grants it
- That grant follows the world resource rate. The swamp key and the wishbone also follow the player count



## 0.2.26

- A dropped Archipelago connection disconnects and asks for a reconnect, and a dead socket cannot freeze the game



## 0.2.25

- The Queen grants eitr regen, the Hare grants movement speed, and the Fuling Shaman grants skill experience



## 0.2.24

- Forge requires Yellow Mushroom, and finewood researches require Finewood, so those checks can be crafted



## 0.2.23

- Default access generates. A research with one parent was read letter by letter, so that check could never open
- Sequential tiers no longer locks a door onto a check that needs a later door



## 0.2.22

- Default access no longer places a research item on a check that needs that item first



## 0.2.21

- Memorial Coal is a Deep North gather, tier 12, and one reward is enough for the altar
- Gather rewards that could not pay their cheapest craft now can
- The unused alpha troll trophy is no longer a check
- Upgrade idols use their item names on the tracker



## 0.2.20

- Materials and natural seeds keep the tier doors. The bench still follows the selected access mode
- Celebratory Cap, Pointy Hat, Fishing Hat, Iron Shield, Lox Saddle, Asksvin Saddle, and Lantern are researches



## 0.2.19

- The troll trophy that drops is a Black Forest check, so it is tier 1



## 0.2.18

- A finished research leaves the craft tab as soon as it completes



## 0.2.17

- Frost Blob is a mountain trophy, so its check is tier 7
- Lava Blob is an ashlands trophy, so its check is tier 11



## 0.2.16

- Picking up many items scans the inventory once, and skips checks that are already done
- Recipes refresh when a pickup teaches a new material or finishes a research



## 0.2.15

- Artisan Press unlocks the artisan press, not a second copy of the artisan table



## 0.2.14

- A trophy reward shows a notice with the stat it grants
- The compendium Active effects page lists the trophy bonuses you have



## 0.2.13

- A menu switch lists what a randomized research unlocks. It is off by default



## 0.2.12

- The Done tab no longer searches every loaded type while it is open



## 0.2.11

- The world option Goal chooses which boss kill finishes the seed
- Kall still means his last phase



## 0.2.10

- The research bench lists unfinished researches by tier, and still puts ones you can craft first
- Completed researches move to the Done tab



## 0.2.9

- A gather reward is granted once per world. Reconnecting no longer pays it again



## 0.2.8

- Gather rewards cover one basic craft or station build, including the research bench, smelter, and a nord weapon cast
- Moulds and idols grant 1, matching the recipe
- Research recipe costs do not change the gather amount



## 0.2.7

- Finding one research cost reveals the recipe when that option is on
- Crafting a research still spends every material in the recipe



## 0.2.6

- Gather checks cover crafting materials, including processed materials such as nails and refined eitr
- Gear, arrows, food, and mead stay ordinary items, except the forage and creature drops that were already checks



## 0.2.5

- Gather checks turn on when the seed contains them, including seeds whose slot data was empty
- Items already in inventory send their gather check on the next connect



## 0.2.4

- Research access can follow the parent chain, tier doors, materials, or natural crafting
- Sequential tiers places each tier door's items in the previous tier



## 0.2.2

- Goal is defeating Kall's last phase



## 0.2.1

- Status stays on Connecting until login succeeds
- Disconnect closes the session



## 0.2.0

- Deep North researches and trophies
- Optional drop checks
- Location checks no longer collide when names contain spaces
- Goal location Defeat Kall

