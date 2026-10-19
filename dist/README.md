# Valheim Archipelago Randomizer

Gates Valheim research and trophies through Archipelago. Optional gather checks. The goal is a boss kill chosen for the seed. The default is Defeat Kall.

Gale installs this package. BepInEx and Jotunn are dependencies.

The Archipelago world is separate. Install `valheimapworld.apworld` from the [repository](https://github.com/kulakaa073/ValheimArchipelagoRandomizer). The [tracker](https://valheim-tracker.vercel.app) shows the room.

Code added after Samupo's original mod was written with AI assistance in Cursor, using Grok (xAI).

## World options

`boss_checks` is on by default. Each boss kill is a check in that boss's tier. The unique drop is removed from the corpse and can be placed on any check from tier 0 through that boss's tier. The granted amount follows the world resource rate. The swamp key and the wishbone also follow how many players are in the world. Off, the corpse still drops the item, and only the goal kill is a location.

`goal` chooses which boss kill finishes the seed. The game sets a world key when that boss dies, and the client sends that check when the key is present.

* `eikthyr`
* `elder`
* `bonemass`
* `moder`
* `yagluth`
* `queen`
* `fader`
* `kall` — Kall's last phase. This is the default.

`research_access` chooses when a research recipe shows on the bench. The received item still grants that research's gear.

* `default` — the recipe shows after every parent research is received.
* `tier` — the recipe shows after the items that open its tier are received.
* `materials` — the recipe shows once its materials have been found. Tier doors are removed.
* `natural` — crafting a research opens the next recipes. Receiving a parent leaves those recipes closed. The received item grants the gear. Tier doors are removed.

`sequential_tiers` places the items that open the next tier into the previous tier, in your own world. Tier 0 checks unlock Tier 1, Tier 1 checks unlock Tier 2, and so on. It has no effect for `materials` or `natural`, because those modes do not use tier doors.

`drop_checks` turns the first pickup of a crafting material into a check. That includes processed materials such as bronze nails and refined eitr. Gear, arrows, food, and mead are not checks. Berries, mushrooms, honey, and raw meat stay checks because they were already on the list.

Receiving a trophy reward shows a notice with the stat it grants. The compendium Active effects page lists the bonuses you currently have. Opening that page again refreshes the totals. Reconnecting does not show the notice again.
