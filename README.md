# Valheim Archipelago Randomizer

Gates Valheim research and trophies through Archipelago. Optional gather checks. The goal is a chosen boss kill or Journey to Valhalla. The default is Defeat Kall.

This fork continues [Samupo's Valheim Archipelago Randomizer](https://github.com/Samupo/ValheimArchipelagoRandomizer). The community's officially maintained Valheim Archipelago Randomizer is [xyzzy44/ValheimArchipelagoRandomizer](https://github.com/xyzzy44/ValheimArchipelagoRandomizer) — use that build unless you specifically want this fork.

Gale installs this package from [Thunderstore](https://thunderstore.io/c/valheim/p/ShadeNoob/ValheimArchipelagoRandomizer/). The [tracker](https://valheim-tracker.vercel.app) shows a room.

Code added after the original mod was written with AI assistance in Cursor, using Grok (xAI).

The connect window has two local options. Trophy drops: Default, x2, or Easy. x2 doubles trophy chance and caps the pity counter at 10. Easy drops that trophy on the first kill, then uses the normal rate. The host rolls the corpse. Research costs: Default or Halved. Halved spends half, rounded up, and never less than 1. Health, stamina, and eitr regen from trophies is 50% per food.

## Install

The mod and the Archipelago world are separate.

* Install the mod with Gale from [Thunderstore](https://thunderstore.io/c/valheim/p/ShadeNoob/ValheimArchipelagoRandomizer/). It depends on BepInEx and Jotunn. Install it on every player's game, and on the host or dedicated server, so the unique boss item is removed when the corpse rolls its drops. The same zip is on the [latest release](https://github.com/kulakaa073/ValheimArchipelagoRandomizer/releases/latest).
* `valheimapworld.apworld` is on that release. Install it in Archipelago, then generate the seed.
* Source for that version is attached to the release.

## World options

`boss_checks` is on by default. Each boss kill is a check in that boss's tier. The unique progression drop is removed from the corpse and can be placed on any check from tier 0 through that boss's tier. Receiving it grants one vanilla bundle into the player inventory. One-per-player rewards (swamp key, wishbone) use the vanilla Valheim player-count total once. That total is not multiplied again and is not split per Archipelago slot. Sacrificial Blood is never randomized; Kall always drops it for the ending. Off, the corpse still drops the item, and only the goal is a location.

`goal` chooses what finishes the seed. Boss goals use the defeat world key. `valhalla` completes when you finish Journey to Valhalla (Sacrificial Blood on the Meadows chiselled platform, then the Valkyrie end credits).

* `eikthyr`
* `elder`
* `bonemass`
* `moder`
* `yagluth`
* `queen`
* `fader`
* `kall` — Kall's last phase. This is the default.
* `valhalla` — Journey to Valhalla end credits

`research_access` chooses when a research recipe shows on the bench. The received item still grants that research's gear.

* `default` — the recipe shows after every parent research is received.
* `tier` — the recipe shows after the items that open its tier are received.
* `materials` — the recipe shows once its materials have been found. The bench does not wait on tier door items. Region arrows stay in the multiworld.
* `natural` — crafting a research opens the next recipes. Receiving a parent leaves those recipes closed. The received item grants the gear. Region arrows stay in the multiworld.

`sequential_tiers` places the items that open the next tier into the previous tier, in your own world. Tier 0 checks unlock Tier 1, Tier 1 checks unlock Tier 2, and so on. It still places those items when research access is `materials` or `natural`. Those modes only change when the bench shows a recipe.

`drop_checks` turns the first pickup of a crafting material into a check. That includes processed materials such as bronze nails and refined eitr. Gear, arrows, food, and mead are not checks. Berries, mushrooms, honey, and raw meat stay checks because they were already on the list.

Receiving a trophy reward shows a notice with the stat it grants. The compendium Active effects page lists the bonuses you currently have. Opening that page again refreshes the totals. Reconnecting does not show the notice again.

## Multiplayer

The supported co-op setup is several Valheim clients in one world, on one Archipelago team and slot, with the mod on every client and on the host. Research unlocks are world keys, so the group shares that progression. Archipelago check and reward keys include the team and slot, so two slots in one world do not overwrite each other's check flags. They still share research unlock keys. Inventory rewards are granted by the client that processes the item, then stored on a received-item index so a reconnect does not grant them again. Two clients on the same slot can both see the network items before the world key replicates, so a reward can land twice in that short window. Full per-slot progression in one shared Valheim world is not supported.
