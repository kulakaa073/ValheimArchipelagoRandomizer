# Build, package and install
 
Commands assume a bash shell (Git Bash on Windows, or Linux/macOS) run from the repository root. The mod DLL can only be built on a machine that has Valheim and BepInEx installed, because the project references their assemblies.
 
## Requirements
 
* .NET SDK (any version that can build `net472` and run the `net8.0` logic tests)
* Python 3.10 or newer
* Valheim (Steam), plus a Gale / BepInEx profile that has Jotunn and Newtonsoft.Json installed
* `unzip` is not needed. Packaging uses `python3 -m zipfile`, which works the same everywhere.
## Reference paths
 
`ValheimRandomizer.csproj` finds the game and BepInEx assemblies through these properties. The defaults match the maintainer's machine. Override any of them on the command line.
 
| Property | Points to |
|---|---|
| `ValheimDir` | Valheim install folder |
| `ValheimManaged` | `valheim_Data/Managed` (derived from `ValheimDir`) |
| `BepInExCore` | the profile's `BepInEx/core` folder |
| `JotunnDll` | full path to `Jotunn.dll` |
| `NewtonsoftJsonDll` | full path to `Newtonsoft.Json.dll` |
| `ArchipelagoDll` | `lib/Archipelago.MultiClient.Net.dll` (default) |
 
A missing file fails the build before compile and names the property to set.
 
Git Bash rewrites paths that look like Unix paths. If a Windows path arrives with a slash missing, prefix the command with `MSYS_NO_PATHCONV=1` and quote the value:
 
```bash
MSYS_NO_PATHCONV=1 dotnet build ValheimRandomizer.csproj -c Release \
  -p:ValheimDir='D:\SteamLibrary\steamapps\common\Valheim'
```
 
## 1. Run the tests
 
```bash
python3 -m unittest discover -s tests -v
dotnet run --project tests/LogicTests/LogicTests.csproj -c Release
```
 
The Python tests cover world generation, ids and the apworld packager. The C# tests cover grant, queue, key and table-parsing logic. They do not load Valheim. A passing run prints `logic tests passed`.
 
## 2. Build the mod DLL
 
```bash
dotnet build ValheimRandomizer.csproj -c Release
```
 
Output: `bin/Release/ValheimRandomizer.dll`.
 
## 3. Build the apworld
 
```bash
python3 tools/_build_apworld.py
```
 
Output: `valheimapworld/valheimapworld.apworld`.
 
The packager parses every `.py` file first and checks the id baseline. It writes a temporary archive, checks its manifest and contents, and only then replaces the old `.apworld`. A syntax error names the file and line and leaves the previous archive untouched.
 
## 4. Build the Thunderstore package
 
Build the DLL first (step 2), then run the script:
 
```bash
bash tools/package-thunderstore.sh
```
 
The script stops with a clear message if any of these is wrong:
 
* `dist/manifest.json` `version_number` does not match `ModVersion` in `src/ValehimRandomizer.cs`
* `dist/CHANGELOG.md` has no `## <version>` section
* a required file is missing
* a source file is newer than `bin/Release/ValheimRandomizer.dll`, meaning the DLL is stale (set `SKIP_STALE_CHECK=1` to bypass)
It stages the files, writes `dist/ValheimArchipelagoRandomizer-<version>.zip`, and checks that the zip has exactly 9 files and no `Newtonsoft.Json.dll`.
 
Also keep the apworld version in `tools/_build_apworld.py` in step with the others.
 
Thunderstore rejects a version number that is already published. Bump the version everywhere before rebuilding a version that was uploaded.
 
The three `.tsv` files must sit next to the DLL. The mod loads them from its own folder and refuses to grant items if one is missing or malformed. Do not include `Newtonsoft.Json.dll`; it comes from the Thunderstore dependency.
 
## 5. Verify the package
 
```bash
python3 -m zipfile -l dist/ValheimArchipelagoRandomizer-0.3.2.zip
```
 
Expected: exactly 9 files, all at the zip root, with no folders:
 
```
manifest.json
README.md
CHANGELOG.md
icon.png
ValheimRandomizer.dll
Archipelago.MultiClient.Net.dll
research.tsv
trophies.tsv
drops.tsv
```
 
`dist/*.zip` is git-ignored. Attach the zip and `valheimapworld/valheimapworld.apworld` to the GitHub release. Upload the same zip to Thunderstore. The `.apworld` is not part of the Thunderstore package.
 
## Install
 
### Players: the mod
 
1. Install Gale (or another Thunderstore-compatible manager) and create a Valheim profile.
2. Install **ValheimArchipelagoRandomizer**. BepInEx and Jotunn install as dependencies.
3. Use the same profile on every player PC and on the host or dedicated server.
To test a local build without Thunderstore, install the dependencies through Gale, then unpack the zip into the profile:
 
```bash
dest="<profile>/BepInEx/plugins/ShadeNoob-ValheimArchipelagoRandomizer"
mkdir -p "$dest"
python3 -m zipfile -e dist/ValheimArchipelagoRandomizer-0.3.2.zip "$dest"
```
 
Use your version in the zip name, and replace `<profile>` with the Gale profile folder (Gale's profile menu has an "open folder" action). Close the game before copying over the DLL.
 
### Archipelago: the apworld
 
1. Open the Archipelago Launcher and choose **Install APWorld**, then select `valheimapworld.apworld`. Alternatively copy it into Archipelago's `custom_worlds` folder.
2. Confirm Valheim appears under Generate Template Options.
3. Generate with the new apworld. Seeds generated with an older apworld keep their old research rows and ids.
## Release checklist
 
1. Tests pass (step 1).
2. DLL and apworld rebuilt (steps 2 and 3).
3. Versions and changelog agree (step 4).
4. Package contents verified (step 5).
5. Generate one real seed for each Boss Checks and goal combination (on, with Valhalla; on, with a boss; off).
6. In a world, confirm a boss reward lands in the inventory, a full inventory keeps the reward queued, and a reconnect does not grant it twice.
7. Tag the release, attach the zip and apworld, then upload the zip to Thunderstore.
 
