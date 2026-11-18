# Valheim

## What is this game?

Valheim is an open-world survival crafting game. In Archipelago, research recipes, trophies, and (optionally) gather drops are checks. Receiving a research item unlocks that research's gear. Progression is organized into tiers (Tier0–Tier15) with door items that open the next tier.

This world is a custom APWorld. Generation must be local. Hosting the resulting multiworld on the website works as usual.

The community's officially maintained Valheim Archipelago Randomizer is [xyzzy44/ValheimArchipelagoRandomizer](https://github.com/xyzzy44/ValheimArchipelagoRandomizer). This apworld belongs to the ShadeNoob / kulakaa073 fork.

## What does randomization do?

* **Research** — Crafting a research at the research bench is a location. The matching research item unlocks that line's gated recipes.
* **Trophies** — Turning in a trophy is a location. Trophy rewards grant passive bonuses.
* **Boss checks** (default on) — Each boss kill is a location in that boss's tier. The unique progression drop is removed from the corpse and can land on any check from tier 0 through that boss's tier. Receiving it spawns the item on that corpse. Sacrificial Blood is never randomized; Kall always drops it for the ending.
* **Gather / drop checks** (optional) — First pickup of listed materials can be a location.
* **Deep North enchanted weapons** — Gold weapon bases unlock at Frost Foundry (T14). Frostfire and Thunderblood variants need a separate Enchanted research (T15), gated by the base line and the Intricate Key.

## Goals

`goal` chooses what finishes the seed:

* Boss goals send when that boss's defeat world key is set (Kall uses the last phase).
* `valhalla` — Journey to Valhalla: place Sacrificial Blood on the Meadows chiselled platform, talk to the Valkyrie, and clear the end credits.

Default is Defeat Kall.

## Research access

`research_access` controls when a research recipe appears on the bench. The Archipelago item still grants the gear when received.

* `default` — after every parent research is received
* `tier` — after the items that open its tier are received
* `materials` — once its materials have been found (tier doors removed)
* `natural` — crafting opens the next recipes; receiving a parent leaves them closed (tier doors removed)

`sequential_tiers` can force door items into the previous tier in your own world. It has no effect for `materials` or `natural`.

## Where is the options page?

The [player options page for this game](../player-options) lists every YAML option.

## Client and tracker

Play with the Valheim Archipelago Randomizer BepInEx mod (Gale / Thunderstore). Install the same mod on every client and on the host or dedicated server so boss corpses strip randomized drops correctly.

A web tracker is available for the room: [valheim-tracker.vercel.app](https://valheim-tracker.vercel.app).
