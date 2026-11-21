# Valheim Setup Guide

## Required software

* [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) (0.5.0 or newer recommended)
* This world's `valheimapworld.apworld` from the [mod releases](https://github.com/kulakaa073/ValheimArchipelagoRandomizer/releases/latest)
* [Valheim](https://store.steampowered.com/app/892970/Valheim/) on Steam
* The Valheim Archipelago Randomizer mod via [Gale / Thunderstore](https://thunderstore.io/c/valheim/p/ShadeNoob/ValheimArchipelagoRandomizer/) (BepInEx and Jotunn are dependencies)

## Optional software

* [Web tracker](https://valheim-tracker.vercel.app) — paste the room URL after the server is up

## Install the APWorld

1. Open the Archipelago Launcher.
2. Choose **Install APWorld** and select `valheimapworld.apworld`, or drag the file onto the launcher.
3. Confirm Valheim appears under custom worlds / Generate Template Options.

Generation with this custom world must be done locally. You can still upload the generated multiworld to archipelago.gg for hosting.

## Install the game mod

1. Install Gale (or another Thunderstore-compatible manager) for Valheim.
2. Install **ValheimArchipelagoRandomizer** and its dependencies into your profile.
3. Install the same profile on every player PC and on the dedicated server / host. The host must run the mod so randomized boss drops are removed from corpses when they roll. Received boss rewards go to that player's inventory. One shared world is one Archipelago slot; research unlocks are not separated per slot.

The mod zip on the GitHub release matches the Thunderstore package.

## Generate a seed

1. In the Archipelago Launcher, open **Generate Template Options** and create a Valheim YAML (or copy options from the player-options page once docs are loaded).
2. Put the YAML in your `Players` folder.
3. Run **Generate**.
4. Host with **Host** locally, or upload the output to the website.

## Connect in Valheim

1. Launch Valheim with the modded profile.
2. Load or create a world. Open the Archipelago connect window from the mod UI.
3. Enter server address, port, slot name, and password from your room.
4. Connect. Research, trophies, and other checks send when you complete them in-game. Items received unlock research gear and grant drop bundles as configured.

Local connect-window options (trophy drop rate, halved research costs) are client-side and do not change the seed.

## Common issues

* **Checks never send** — confirm the mod is loaded (BepInEx log) and that you are connected before completing the check.
* **Boss still drops the progression item** — the host/server must also run the mod.
* **Wrong or missing researches** — regenerate after updating the apworld; old seeds do not pick up new research rows.
* **Valhalla goal** — Sacrificial Blood always drops from Kall. Place it on the Meadows chiselled platform, speak to the Valkyrie, and finish the credits for the goal check.
