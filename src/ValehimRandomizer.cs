using BepInEx;
using UnityEngine;
using Jotunn;
using Jotunn.Configs;
using Jotunn.Entities;
using Jotunn.Managers;
using System;
using System.Collections.Generic;
using HarmonyLib;
using System.IO;
using System.Reflection;
using System.Text;
using Newtonsoft.Json.Linq;
using static ValheimRandomizer;

[BepInPlugin(ModGuid, ModName, ModVersion)]
[BepInDependency(Jotunn.Main.ModGuid)]
public class ValheimRandomizer : BaseUnityPlugin
{
    public const string ModGuid = "com.samupo.randomizer";
    public const string ModName = "Randomizer";
    public const string ModVersion = "0.2.34";

    internal static BepInEx.Configuration.ConfigEntry<bool> randomized;
    internal static BepInEx.Configuration.ConfigEntry<string> archipelagoHostname;
    internal static BepInEx.Configuration.ConfigEntry<int> archipelagoPort;
    internal static BepInEx.Configuration.ConfigEntry<string> archipelagoSlot;
    internal static BepInEx.Configuration.ConfigEntry<string> archipelagoPassword;
    internal static BepInEx.Configuration.ConfigEntry<bool> anyResearchMaterial;
    internal static BepInEx.Configuration.ConfigEntry<bool> showResearchUnlocks;
    internal static BepInEx.Configuration.ConfigEntry<string> researchAccess;

    public enum ResearchAccessMode
    {
        Default = 0,
        Tier = 1,
        Materials = 2,
        Natural = 3,
    }

    public static readonly string[] ResearchAccessLabels =
    {
        "Default: parent chain",
        "Tier doors",
        "Materials only",
        "Natural: craft opens the next",
    };

    // Items required to enter a tier. Keep this in sync with valheimapworld/Regions.py.
    static readonly Dictionary<int, string[]> TierDoorItems = new Dictionary<int, string[]>
    {
        { 1, new[] { "Crafting" } },
        { 2, new[] { "Axes Tier 1", "Troll Armor", "Cooking Station", "Bed Tier 1", "Warmth Tier 1" } },
        { 3, new[] { "Pickaxes Tier 1", "Boat Tier 1", "Smelter", "Forge" } },
        { 4, new[] { "Bronze" } },
        { 5, new[] { "Axes Tier 2" } },
        { 6, new[] { "Pickaxes Tier 2" } },
        { 7, new[] { "Pickaxes Tier 3", "Forge Upgrade 1", "Nails Tier 2" } },
        { 8, new[] { "Artisan Table", "Blast Furnace" } },
        { 9, new[] { "Axes Tier 4", "Wisp Fountain", "Wisplight", "Forge Upgrade 2", "Forge Upgrade 3", "Spinning Wheel" } },
        { 10, new[] { "Pickaxes Tier 4" } },
        { 11, new[] { "Ceramic Plates", "Boat Tier 4", "Artisan Press" } },
        { 12, new[] { "Siege", "Snow Shovel" } },
    };

    public class TrophyResearch
    {
        public enum TrophyBoost { Load, HP, Stamina, Eitr, HPRegen, StaminaRegen, Attack, Defense, Adrenaline, EitrRegen, Speed, SkillXp }

        public const int LoadPerTrophy = 10;
        public const int HpPerFood = 2;
        public const int StaminaPerFood = 2;
        public const int EitrPerFood = 5;
        public const int RegenPercentPerFood = 100;
        public const int AdrenalinePerTrophy = 3;
        public const int AttackPercentPerTrophy = 5;
        public const int DefensePercentPerTrophy = 5;
        public const int SpeedPercentPerTrophy = 5;
        public const int SkillXpPercentPerTrophy = 25;

        public string itemID;
        public string researchID;
        public TrophyBoost boost;

        public TrophyResearch(string itemID, string researchID, TrophyBoost boost)
        {
            this.itemID = itemID;
            this.researchID = researchID;
            this.boost = boost;
        }
    }


    // Name for our custom piece/prefab that has a CraftingStation component
    public const string ResearchBenchPrefabName = "piece_randomizer_researchbench";

    public static CraftingStation ResearchBenchCraftingStation { get; set; }

    private Player currentPlayer = null;

    public static List<string> research = new List<string>();
    public static Dictionary<string, List<string>> recipeRequirements = new Dictionary<string, List<string>>();
    public static Dictionary<string, TrophyResearch> trophyByItemID = new Dictionary<string, TrophyResearch>();
    public static Dictionary<string, TrophyResearch> trophyByResearchID = new Dictionary<string, TrophyResearch>(StringComparer.Ordinal);
    public static Dictionary<string, string> researchToArchipelago = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<string, string> archipelagoToResearch = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<string, int> researchTier = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<string, string> researchBody = new Dictionary<string, string>(StringComparer.Ordinal);
    public static Dictionary<string, string[]> researchUnlockPrefabs = new Dictionary<string, string[]>(StringComparer.Ordinal);
    public static ResearchAccessMode ActiveResearchAccess { get; private set; } = ResearchAccessMode.Default;
    public static bool SeedControlsAccess { get; private set; }
    public static bool SequentialTiers { get; private set; }

    public class DropCheck
    {
        public string itemID;
        public string locationName;
        public int amount;

        public DropCheck(string itemID, string locationName, int amount)
        {
            this.itemID = itemID;
            this.locationName = locationName;
            this.amount = amount;
        }
    }

    public class BossDrop
    {
        public string itemID;
        public string itemName;
        public string locationName;
        public string defeatKey;
        public string creature;
        public int amount;
        public bool onePerPlayer;

        public BossDrop(string itemID, string itemName, string locationName, string defeatKey, string creature, int amount, bool onePerPlayer)
        {
            this.itemID = itemID;
            this.itemName = itemName;
            this.locationName = locationName;
            this.defeatKey = defeatKey;
            this.creature = creature;
            this.amount = amount;
            this.onePerPlayer = onePerPlayer;
        }
    }

    public static Dictionary<string, DropCheck> dropByItemID = new Dictionary<string, DropCheck>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<string, DropCheck> dropByLocationName = new Dictionary<string, DropCheck>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<string, BossDrop> bossByItemName = new Dictionary<string, BossDrop>(StringComparer.Ordinal);
    public static Dictionary<string, BossDrop> bossByDefeatKey = new Dictionary<string, BossDrop>(StringComparer.Ordinal);
    public static readonly List<BossDrop> BossDrops = new List<BossDrop>();
    static readonly HashSet<string> bossPrefabs = new HashSet<string>(StringComparer.Ordinal);
    public static bool SuppressDropChecks;
    static Dictionary<string, int> dropSeen = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
    static readonly Dictionary<string, int> dropCounts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
    static readonly List<string> dropMissing = new List<string>();
    static readonly HashSet<string> sentDrops = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    static readonly HashSet<string> craftedResearch = new HashSet<string>(StringComparer.Ordinal);
    static readonly List<ItemDrop.ItemData> researchConsume = new List<ItemDrop.ItemData>();
    static HashSet<string> researchIds;
    static int researchIdCount = -1;
    static int knownMaterialCount = -1;
    static int revealSuppressed;
    static bool revealQueued;
    static bool inventoryDirty;
    static bool scanningInventory;
    static bool revealedForPlayer;
    static bool dropCatchUpDone;
    static bool pityDirty = true;
    static bool pityWasConnected;
    static bool pityChancesFrozen;
    static float pityWait;
    static string pitySent;
    static Dictionary<string, TrophyPityInfo> pityChances;

    class TrophyPityInfo
    {
        public float baseChance;
        public readonly List<PityChance> chances = new List<PityChance>();
    }

    class PityChance
    {
        public float chance;
        public int key;
        public bool starred;
    }
    static readonly AccessTools.FieldRef<Player, HashSet<string>> KnownRecipesRef =
        AccessTools.FieldRefAccess<Player, HashSet<string>>("m_knownRecipes");
    static readonly MethodInfo AddKnownRecipeMethod = AccessTools.Method(typeof(Player), "AddKnownRecipe");
    static readonly MethodInfo AddKnownPieceMethod = AccessTools.Method(typeof(Player), "AddKnownPiece");
    static readonly MethodInfo UpdatePiecesMethod = AccessTools.Method(typeof(Player), "UpdateAvailablePiecesList");
    static readonly AccessTools.FieldRef<Player, HashSet<string>> KnownMaterialsRef =
        AccessTools.FieldRefAccess<Player, HashSet<string>>("m_knownMaterial");

    public static BepInEx.Logging.ManualLogSource Log { get; private set; }

    float time = 0f;

    private void Awake()
    {
        randomized = Config.Bind("Archipelago", "Randomized", false, "Uses Archipelago?");
        archipelagoHostname = Config.Bind("Archipelago", "Host", "localhost", "Archipelago server host");
        archipelagoPort = Config.Bind("Archipelago", "Port", 38281, "Archipelago server port");
        archipelagoSlot = Config.Bind("Archipelago", "Slot", "Player", "Your Archipelago slot name");
        archipelagoPassword = Config.Bind("Archipelago", "Password", "", "Archipelago password (if any)");
        anyResearchMaterial = Config.Bind("Archipelago", "AnyResearchMaterial", false,
            "Off: a research recipe appears after every cost item has been found. On: finding any one cost item reveals the recipe. Crafting always spends the full cost.");
        showResearchUnlocks = Config.Bind("Archipelago", "ShowResearchUnlocks", false,
            "Off: a randomized research says Unlocks: Something?. On: the description lists what that research unlocks.");
        researchAccess = Config.Bind("Archipelago", "ResearchAccess", "default",
            "Used until a seed connects. default, tier, materials, or natural.");
        ActiveResearchAccess = ParseResearchAccess(researchAccess.Value);

        ValheimRandomizer.Log = this.Logger;
        PrefabManager.OnVanillaPrefabsAvailable += DoOnPrefabsAvailable;
        new Harmony(ValheimRandomizer.ModGuid).PatchAll();

        var go = new GameObject("ValheimRandomizer.AP_UI");
        DontDestroyOnLoad(go);
        go.AddComponent<ArchipelagoUI>().Init();
    }

    static string DataFolder => Path.GetDirectoryName(typeof(ValheimRandomizer).Assembly.Location);

    void DoOnPrefabsAvailable()
    {
        PrefabManager.OnVanillaPrefabsAvailable -= DoOnPrefabsAvailable;
        RandomizerUtils.RegisterResearchBench();
        AddDropChecks();
        Invoke(nameof(AddResearchRecipes), 5.0f);
        Invoke(nameof(AddTrophyResearches), 5.5f);
        Invoke(nameof(CheckRecipesAndPiecesWithoutResearch), 10.0f);
    }

    private void Update()
    {
        ArchipelagoConnection.Pump();

        if (currentPlayer != Player.m_localPlayer)
        {
            if (currentPlayer != null && currentPlayer.GetInventory() != null)
            {
                currentPlayer.GetInventory().m_onChanged -= OnInventoryChanged;
            }

            currentPlayer = Player.m_localPlayer;
            revealedForPlayer = false;
            dropCatchUpDone = false;
            inventoryDirty = false;
            knownMaterialCount = MaterialCount(currentPlayer);
            sentDrops.Clear();
            craftedResearch.Clear();

            if (currentPlayer != null && currentPlayer.GetInventory() != null)
            {
                currentPlayer.GetInventory().m_onChanged += OnInventoryChanged;
                SnapshotDropCounts();
            }
        }

        CatchUpHeldDrops();

        if (!revealedForPlayer && currentPlayer != null && research.Count > 0)
        {
            RevealEligibleRecipes();
            revealedForPlayer = true;
        }

        if (inventoryDirty)
            FlushInventoryChecks();

        time += Time.unscaledDeltaTime;
        if (time > 2.0f)
        {
            time = 0.0f;
            ArchipelagoConnection.TryFlushPendingLocations();
        }

        FlushTrophyPity();
    }

    public static void MarkTrophyPityDirty()
    {
        pityDirty = true;
    }

    // The countdown lives on this client. A stored 0 still drops on the next kill, so the published number is at least 1.
    void FlushTrophyPity()
    {
        bool connected = ArchipelagoConnection.IsConnected;
        if (!connected)
        {
            pityWasConnected = false;
            pityWait = 0f;
            return;
        }
        if (!pityWasConnected)
        {
            pityWasConnected = true;
            pityDirty = true;
            pitySent = null;
        }
        if (!pityDirty) return;
        pityWait += Time.unscaledDeltaTime;
        if (pityWait < 0.4f) return;
        pityWait = 0f;
        pityDirty = false;
        try
        {
            var payload = SnapshotTrophyPity();
            string text = payload.ToString(Newtonsoft.Json.Formatting.None);
            if (text == pitySent) return;
            ArchipelagoConnection.PublishPity(payload);
            pitySent = text;
        }
        catch (Exception ex)
        {
            pityDirty = true;
            Log?.LogWarning("Trophy pity publish failed: " + ex.Message);
        }
    }

    // The live counter is keyed by prefab hash plus the chance in thousandths, so each star level has its own count.
    static JObject SnapshotTrophyPity()
    {
        var root = new JObject();
        EnsurePityChances();
        var table = CharacterDrop.s_pseudoCounter;
        if (table == null || pityChances == null) return root;
        var names = new List<string>(pityChances.Keys);
        names.Sort(StringComparer.Ordinal);
        for (int i = 0; i < names.Count; i++)
        {
            var info = pityChances[names[i]];
            int baseLeft = 0;
            float baseShown = info.baseChance;
            bool hasBase = false;
            var stars = new JArray();
            for (int c = 0; c < info.chances.Count; c++)
            {
                var chance = info.chances[c];
                if (!table.TryGetValue(chance.key, out int count)) continue;
                int left = Math.Max(1, count);
                if (!chance.starred)
                {
                    hasBase = true;
                    baseLeft = left;
                    baseShown = chance.chance;
                    continue;
                }
                stars.Add(new JObject
                {
                    ["left"] = left,
                    ["chance"] = Math.Round(chance.chance, 4),
                });
            }
            if (!hasBase && stars.Count == 0)
            {
                if (info.baseChance <= 0.3f) continue;
                root[names[i]] = new JObject
                {
                    ["pity"] = false,
                    ["chance"] = Math.Round(info.baseChance, 4),
                };
                continue;
            }
            var entry = new JObject();
            if (hasBase)
            {
                entry["left"] = baseLeft;
                entry["chance"] = Math.Round(baseShown, 4);
            }
            if (stars.Count > 0) entry["stars"] = stars;
            root[names[i]] = entry;
        }
        return root;
    }

    static void EnsurePityChances()
    {
        if (pityChancesFrozen || trophyByItemID.Count == 0) return;
        var found = Resources.FindObjectsOfTypeAll<CharacterDrop>();
        if (found == null || found.Length == 0) return;
        var map = new Dictionary<string, TrophyPityInfo>(StringComparer.Ordinal);
        for (int i = 0; i < found.Length; i++)
        {
            var dropper = found[i];
            if (dropper == null || dropper.m_drops == null) continue;
            for (int d = 0; d < dropper.m_drops.Count; d++)
            {
                var drop = dropper.m_drops[d];
                if (drop == null || drop.m_prefab == null) continue;
                string name = drop.m_prefab.name;
                if (string.IsNullOrEmpty(name) || !trophyByItemID.ContainsKey(name)) continue;
                if (!map.TryGetValue(name, out var info))
                {
                    info = new TrophyPityInfo();
                    map[name] = info;
                }
                info.baseChance = drop.m_chance;
                AddPityChance(info, name, drop.m_chance, starred: false);
                if (!drop.m_levelMultiplier) continue;
                AddPityChance(info, name, drop.m_chance * 2f, starred: true);
                AddPityChance(info, name, drop.m_chance * 4f, starred: true);
            }
        }
        if (map.Count == 0) return;
        pityChances = map;
        if (ZNetScene.instance != null) pityChancesFrozen = true;
    }

    static void AddPityChance(TrophyPityInfo info, string name, float chance, bool starred)
    {
        if (chance <= 0f || chance > 0.3f) return;
        int key = name.GetStableHashCode() + (int)(chance * 1000f);
        for (int i = 0; i < info.chances.Count; i++)
        {
            if (info.chances[i].key == key) return;
        }
        info.chances.Add(new PityChance { chance = chance, key = key, starred = starred });
    }

    private void OnInventoryChanged()
    {
        if (scanningInventory) return;
        inventoryDirty = true;
    }

    void FlushInventoryChecks()
    {
        if (scanningInventory) return;
        var player = currentPlayer;
        var inventory = player != null ? player.GetInventory() : null;
        if (inventory == null)
        {
            inventoryDirty = false;
            return;
        }

        scanningInventory = true;
        inventoryDirty = false;
        revealSuppressed++;
        bool reveal = false;
        bool refreshBench = false;
        try
        {
            var items = inventory.GetAllItems();
            var ids = ResearchIdSet();
            researchConsume.Clear();
            bool trackDrops = ArchipelagoConnection.DropChecksEnabled && !SuppressDropChecks && dropByItemID.Count > 0;
            if (trackDrops) dropCounts.Clear();

            if (items != null)
            {
                for (int i = 0; i < items.Count; i++)
                {
                    var it = items[i];
                    var prefab = it?.m_dropPrefab;
                    if (prefab == null) continue;
                    string name = prefab.name;
                    if (string.IsNullOrEmpty(name)) continue;

                    if (ids.Contains(name))
                        researchConsume.Add(it);

                    if (trophyByItemID.TryGetValue(name, out var tr) && !AlreadyCrafted(tr.researchID))
                    {
                        craftedResearch.Add(tr.researchID);
                        UnlockResearch(tr.researchID);
                        reveal = true;
                        Log?.LogInfo($"Unlocked trophy research '{tr.researchID}' from '{name}'.");
                    }

                    if (trackDrops && dropByItemID.ContainsKey(name) && !DropAlreadySent(name))
                    {
                        dropCounts.TryGetValue(name, out int have);
                        dropCounts[name] = have + it.m_stack;
                    }
                }
            }

            for (int i = 0; i < researchConsume.Count; i++)
            {
                var it = researchConsume[i];
                if (it?.m_dropPrefab == null) continue;
                string name = it.m_dropPrefab.name;
                bool first = !AlreadyCrafted(name);
                craftedResearch.Add(name);
                if (first)
                {
                    UnlockResearch(name);
                    reveal = true;
                }
                inventory.RemoveItem(it, 1);
                refreshBench = true;
            }
            researchConsume.Clear();

            if (trackDrops)
                ApplyDropCounts();

            if (MaterialsGrew(player))
                reveal = true;
        }
        finally
        {
            revealSuppressed--;
            scanningInventory = false;
        }

        if (reveal || revealQueued)
        {
            revealQueued = false;
            RevealEligibleRecipes();
        }

        // The craft list rebuilds inside the craft action, before this scan
        // records the research. Refresh once the local crafted set is updated.
        if (refreshBench)
            Patches.RefreshResearchBench();
    }

    static HashSet<string> ResearchIdSet()
    {
        if (researchIds == null || researchIdCount != research.Count)
        {
            researchIds = new HashSet<string>(research, StringComparer.Ordinal);
            researchIdCount = research.Count;
        }
        return researchIds;
    }

    static bool AlreadyCrafted(string researchId)
    {
        if (string.IsNullOrEmpty(researchId)) return true;
        if (craftedResearch.Contains(researchId)) return true;
        if (!IsResearchCrafted(researchId)) return false;
        craftedResearch.Add(researchId);
        return true;
    }

    static bool DropAlreadySent(string itemID)
    {
        if (sentDrops.Contains(itemID)) return true;
        if (ZoneSystem.instance == null) return false;
        if (!ZoneSystem.instance.GetGlobalKey("ap_drop_sent_" + itemID)
            && !ZoneSystem.instance.GetGlobalKey("ap_drop_pending_" + itemID))
            return false;
        sentDrops.Add(itemID);
        return true;
    }

    static int MaterialCount(Player player)
    {
        var materials = player != null ? KnownMaterialsRef(player) : null;
        return materials != null ? materials.Count : 0;
    }

    static bool MaterialsGrew(Player player)
    {
        int count = MaterialCount(player);
        if (count <= knownMaterialCount)
        {
            knownMaterialCount = count;
            return false;
        }
        knownMaterialCount = count;
        return true;
    }

    static void TallyUnsentDrops(List<ItemDrop.ItemData> items)
    {
        dropCounts.Clear();
        if (items == null) return;
        for (int i = 0; i < items.Count; i++)
        {
            var it = items[i];
            var prefab = it?.m_dropPrefab;
            if (prefab == null) continue;
            string name = prefab.name;
            if (string.IsNullOrEmpty(name) || !dropByItemID.ContainsKey(name) || DropAlreadySent(name)) continue;
            dropCounts.TryGetValue(name, out int have);
            dropCounts[name] = have + it.m_stack;
        }
    }

    static void ApplyDropCounts()
    {
        foreach (var pair in dropCounts)
        {
            dropSeen.TryGetValue(pair.Key, out int seen);
            if (pair.Value > seen && dropByItemID.TryGetValue(pair.Key, out var drop))
                ArchipelagoConnection.SendDropLocation(drop.itemID, drop.locationName);
            dropSeen[pair.Key] = pair.Value;
        }

        dropMissing.Clear();
        foreach (var pair in dropSeen)
        {
            if (dropCounts.ContainsKey(pair.Key) || DropAlreadySent(pair.Key)) continue;
            dropMissing.Add(pair.Key);
        }
        for (int i = 0; i < dropMissing.Count; i++)
            dropSeen[dropMissing[i]] = 0;
        dropMissing.Clear();
    }

    public static void SnapshotDropCounts()
    {
        dropSeen.Clear();
        var player = Player.m_localPlayer;
        if (player?.GetInventory() == null || dropByItemID.Count == 0) return;
        TallyUnsentDrops(player.GetInventory().GetAllItems());
        foreach (var pair in dropCounts)
            dropSeen[pair.Key] = pair.Value;
    }

    void CatchUpHeldDrops()
    {
        if (dropCatchUpDone) return;
        if (currentPlayer == null || ZoneSystem.instance == null || dropByItemID.Count == 0) return;
        if (!ArchipelagoConnection.DropChecksEnabled || randomized == null || !randomized.Value) return;

        dropCatchUpDone = true;
        TallyUnsentDrops(currentPlayer.GetInventory().GetAllItems());
        int held = 0;
        foreach (var pair in dropCounts)
        {
            dropSeen[pair.Key] = pair.Value;
            if (pair.Value <= 0) continue;
            held++;
            if (dropByItemID.TryGetValue(pair.Key, out var drop))
                ArchipelagoConnection.SendDropLocation(drop.itemID, drop.locationName);
        }
        Log?.LogInfo($"Drop catch-up: {held} listed stacks already held.");
    }

    public static bool IsBossDropPrefab(string prefabName)
    {
        return !string.IsNullOrEmpty(prefabName) && bossPrefabs.Contains(prefabName);
    }

    // Vanilla marks these drops dontScale. The check still follows the world resource rate,
    // and a one-per-player drop (swamp key, wishbone) is multiplied by the player count.
    public static int BossGrantAmount(BossDrop boss)
    {
        int min = boss.amount;
        int max = boss.amount;
        bool onePerPlayer = boss.onePerPlayer;
        var creature = ZNetScene.instance != null ? ZNetScene.instance.GetPrefab(boss.creature) : null;
        var table = creature != null ? creature.GetComponent<CharacterDrop>() : null;
        if (table != null && table.m_drops != null)
        {
            for (int i = 0; i < table.m_drops.Count; i++)
            {
                var drop = table.m_drops[i];
                if (drop == null || drop.m_prefab == null) continue;
                if (!string.Equals(drop.m_prefab.name, boss.itemID, StringComparison.Ordinal)) continue;
                min = drop.m_amountMin;
                max = drop.m_amountMax;
                onePerPlayer = drop.m_onePerPlayer;
                break;
            }
        }
        if (max < min) max = min;
        int rolled = min == max ? min : UnityEngine.Random.Range(min, max + 1);
        float rate = Game.m_resourceRate > 0f ? Game.m_resourceRate : 1f;
        int amount = Mathf.Max(1, Mathf.RoundToInt(rolled * rate));
        if (onePerPlayer)
        {
            int players = 1;
            if (ZNet.instance != null)
                players = Mathf.Max(1, ZNet.instance.GetNrOfPlayers());
            amount *= players;
        }
        if (amount > 100) amount = 100;
        return amount;
    }

    public static bool GrantDropBundle(string itemID, int amount)
    {
        var player = Player.m_localPlayer;
        var prefab = ObjectDB.instance != null ? ObjectDB.instance.GetItemPrefab(itemID) : null;
        if (player == null || prefab == null || player.GetInventory() == null)
        {
            Log?.LogWarning($"Could not grant drop bundle '{itemID}' yet.");
            return false;
        }

        SuppressDropChecks = true;
        try
        {
            bool added = player.GetInventory().AddItem(prefab, amount);
            if (!added)
            {
                Log?.LogWarning($"Inventory refused drop bundle {amount}x {itemID}.");
                return false;
            }
            Log?.LogInfo($"Granted drop bundle {amount}x {itemID}.");
            return true;
        }
        finally
        {
            SuppressDropChecks = false;
            SnapshotDropCounts();
        }
    }

    public static void DoUnlockResearch(string research)
    {
        bool first = ZoneSystem.instance != null && !ZoneSystem.instance.GetGlobalKey(research);
        Log.LogInfo("Research unlocked: " + research);
        ZoneSystem.instance.SetGlobalKey(research);
        RevealEligibleRecipes();
        if (first)
            AnnounceTrophy(research);
    }

    static void AnnounceTrophy(string research)
    {
        if (string.IsNullOrEmpty(research) || !trophyByResearchID.TryGetValue(research, out var tr)) return;
        if (MessageHud.instance == null) return;

        string name = TrophyNameToken(tr.itemID);
        string bonus = TrophyBonusPhrase(tr.boost);
        MessageHud.instance.ShowMessage(
            MessageHud.MessageType.TopLeft,
            name + ": " + bonus,
            0,
            TrophyIcon(tr.itemID));
    }

    static string TrophyNameToken(string itemID)
    {
        string token = UnlockLabel(itemID);
        return string.IsNullOrEmpty(token) ? itemID : token;
    }

    static Sprite TrophyIcon(string itemID)
    {
        var go = PrefabManager.Instance != null ? PrefabManager.Instance.GetPrefab(itemID) : null;
        var drop = go ? go.GetComponent<ItemDrop>() : null;
        var shared = drop != null && drop.m_itemData != null ? drop.m_itemData.m_shared : null;
        if (shared == null || shared.m_icons == null || shared.m_icons.Length == 0) return null;
        int variant = drop.m_itemData.m_variant;
        if (variant < 0 || variant >= shared.m_icons.Length) variant = 0;
        return shared.m_icons[variant];
    }

    public static string TrophyBonusPhrase(TrophyResearch.TrophyBoost boost)
    {
        switch (boost)
        {
            case TrophyResearch.TrophyBoost.Load:
                return "+" + TrophyResearch.LoadPerTrophy + " carry weight";
            case TrophyResearch.TrophyBoost.HP:
                return "+" + TrophyResearch.HpPerFood + " health per food";
            case TrophyResearch.TrophyBoost.Stamina:
                return "+" + TrophyResearch.StaminaPerFood + " stamina per food";
            case TrophyResearch.TrophyBoost.Eitr:
                return "+" + TrophyResearch.EitrPerFood + " eitr per food";
            case TrophyResearch.TrophyBoost.HPRegen:
                return "+" + TrophyResearch.RegenPercentPerFood + "% health regen per food";
            case TrophyResearch.TrophyBoost.StaminaRegen:
                return "+" + TrophyResearch.RegenPercentPerFood + "% stamina regen per food";
            case TrophyResearch.TrophyBoost.EitrRegen:
                return "+" + TrophyResearch.RegenPercentPerFood + "% eitr regen per food";
            case TrophyResearch.TrophyBoost.Speed:
                return "+" + TrophyResearch.SpeedPercentPerTrophy + "% movement speed";
            case TrophyResearch.TrophyBoost.SkillXp:
                return "+" + TrophyResearch.SkillXpPercentPerTrophy + "% skill experience";
            case TrophyResearch.TrophyBoost.Attack:
                return "+" + TrophyResearch.AttackPercentPerTrophy + "% damage";
            case TrophyResearch.TrophyBoost.Defense:
                return "+" + TrophyResearch.DefensePercentPerTrophy + "% armor";
            case TrophyResearch.TrophyBoost.Adrenaline:
                return "+" + TrophyResearch.AdrenalinePerTrophy + " adrenaline";
            default:
                return "";
        }
    }

    public static string BuildTrophyStatusBlock()
    {
        int foods = ActiveFoodCount();
        var lines = new List<string>();
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.Load, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.HP, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.Stamina, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.Eitr, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.HPRegen, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.StaminaRegen, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.EitrRegen, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.Speed, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.SkillXp, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.Adrenaline, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.Attack, foods);
        AddTrophyStatusLine(lines, TrophyResearch.TrophyBoost.Defense, foods);
        if (lines.Count == 0) return null;
        var builder = new StringBuilder();
        builder.Append("<color=orange>Trophy bonuses</color>");
        foreach (string line in lines)
        {
            builder.Append('\n');
            builder.Append(line);
        }
        return builder.ToString();
    }

    static void AddTrophyStatusLine(List<string> lines, TrophyResearch.TrophyBoost boost, int foods)
    {
        int tiers = GetBoost(boost);
        if (tiers <= 0) return;
        string value = TrophyStatusValue(boost, tiers, foods);
        if (string.IsNullOrEmpty(value)) return;
        lines.Add(TrophyStatusLabel(boost) + ": <color=orange>" + value + "</color>");
    }

    static string TrophyStatusLabel(TrophyResearch.TrophyBoost boost)
    {
        switch (boost)
        {
            case TrophyResearch.TrophyBoost.Load: return "Carry weight";
            case TrophyResearch.TrophyBoost.HP: return "Health";
            case TrophyResearch.TrophyBoost.Stamina: return "Stamina";
            case TrophyResearch.TrophyBoost.Eitr: return "Eitr";
            case TrophyResearch.TrophyBoost.HPRegen: return "Health regen";
            case TrophyResearch.TrophyBoost.StaminaRegen: return "Stamina regen";
            case TrophyResearch.TrophyBoost.EitrRegen: return "Eitr regen";
            case TrophyResearch.TrophyBoost.Speed: return "Movement speed";
            case TrophyResearch.TrophyBoost.SkillXp: return "Skill experience";
            case TrophyResearch.TrophyBoost.Attack: return "Damage";
            case TrophyResearch.TrophyBoost.Defense: return "Armor";
            case TrophyResearch.TrophyBoost.Adrenaline: return "Adrenaline";
            default: return "";
        }
    }

    static string TrophyStatusValue(TrophyResearch.TrophyBoost boost, int tiers, int foods)
    {
        switch (boost)
        {
            case TrophyResearch.TrophyBoost.Load:
                return "+" + (TrophyResearch.LoadPerTrophy * tiers);
            case TrophyResearch.TrophyBoost.HP:
                return PerFood(TrophyResearch.HpPerFood * tiers, foods, false);
            case TrophyResearch.TrophyBoost.Stamina:
                return PerFood(TrophyResearch.StaminaPerFood * tiers, foods, false);
            case TrophyResearch.TrophyBoost.Eitr:
                return PerFood(TrophyResearch.EitrPerFood * tiers, foods, false);
            case TrophyResearch.TrophyBoost.HPRegen:
            case TrophyResearch.TrophyBoost.StaminaRegen:
            case TrophyResearch.TrophyBoost.EitrRegen:
                return PerFood(TrophyResearch.RegenPercentPerFood * tiers, foods, true);
            case TrophyResearch.TrophyBoost.Speed:
                return "+" + (TrophyResearch.SpeedPercentPerTrophy * tiers) + "%";
            case TrophyResearch.TrophyBoost.SkillXp:
                return "+" + (TrophyResearch.SkillXpPercentPerTrophy * tiers) + "%";
            case TrophyResearch.TrophyBoost.Attack:
                return "+" + (TrophyResearch.AttackPercentPerTrophy * tiers) + "%";
            case TrophyResearch.TrophyBoost.Defense:
                return "+" + (TrophyResearch.DefensePercentPerTrophy * tiers) + "%";
            case TrophyResearch.TrophyBoost.Adrenaline:
                return "+" + (TrophyResearch.AdrenalinePerTrophy * tiers);
            default:
                return "";
        }
    }

    static string PerFood(int perFood, int foods, bool percent)
    {
        string rate = "+" + perFood + (percent ? "% per food" : " per food");
        if (foods <= 0) return rate;
        int now = perFood * foods;
        return rate + " (+" + now + (percent ? "%)" : ")");
    }

    static int ActiveFoodCount()
    {
        var player = Player.m_localPlayer;
        if (player == null) return 0;
        var foods = player.GetFoods();
        return foods != null ? foods.Count : 0;
    }

    public static bool ResearchRequirementsMet(string itemID)
    {
        foreach (string required in GetResearchRequired(itemID))
        {
            if (!IsResearchUnlocked(required)) return false;
        }
        return true;
    }

    public static void RevealEligibleRecipes()
    {
        if (revealSuppressed > 0)
        {
            revealQueued = true;
            return;
        }
        RevealEligibleRecipesNow();
    }

    static void RevealEligibleRecipesNow()
    {
        var player = Player.m_localPlayer;
        if (player == null || ObjectDB.instance == null) return;
        var known = KnownRecipesRef(player);
        if (known == null) return;

        bool anyMaterial = anyResearchMaterial != null && anyResearchMaterial.Value;
        if (ObjectDB.instance.m_recipes != null)
        {
            foreach (var recipe in ObjectDB.instance.m_recipes)
            {
                if (recipe?.m_item == null) continue;
                string id = recipe.m_item.name;
                bool isResearch = ResearchIdSet().Contains(id);
                if (isResearch)
                    recipe.m_requireOnlyOneIngredient = false;
                bool opened = isResearch ? ResearchRecipeVisible(id) : ResearchRequirementsMet(id);
                if (!recipeRequirements.ContainsKey(id) || !opened)
                {
                    if (isResearch)
                    {
                        string hide = recipe.m_item.m_itemData?.m_shared?.m_name;
                        if (!string.IsNullOrEmpty(hide))
                            known.Remove(hide);
                    }
                    continue;
                }
                string shown = recipe.m_item.m_itemData?.m_shared?.m_name;
                if (isResearch && !ResearchMaterialsMatch(player, recipe, anyMaterial))
                {
                    if (!string.IsNullOrEmpty(shown))
                        known.Remove(shown);
                    continue;
                }
                if (string.IsNullOrEmpty(shown) || known.Contains(shown)) continue;
                if (MessageHud.instance != null && AddKnownRecipeMethod != null)
                    AddKnownRecipeMethod.Invoke(player, new object[] { recipe });
                else
                    known.Add(shown);
            }
        }

        bool pieceAdded = false;
        if (ZNetScene.instance != null)
        {
            foreach (var pair in recipeRequirements)
            {
                if (!ResearchRequirementsMet(pair.Key) || known.Contains(pair.Key)) continue;
                var prefab = ZNetScene.instance.GetPrefab(pair.Key);
                var piece = prefab != null ? prefab.GetComponent<Piece>() : null;
                if (piece == null) continue;
                if (MessageHud.instance != null && Hud.instance != null && AddKnownPieceMethod != null)
                    AddKnownPieceMethod.Invoke(player, new object[] { piece });
                else
                    known.Add(piece.m_name);
                pieceAdded = true;
            }
        }

        if (pieceAdded && UpdatePiecesMethod != null)
            UpdatePiecesMethod.Invoke(player, null);
    }

    static bool ResearchMaterialsMatch(Player player, Recipe recipe, bool anyMaterial)
    {
        var materials = KnownMaterialsRef(player);
        var requirements = recipe?.m_resources;
        if (requirements == null || requirements.Length == 0) return true;
        bool sawCost = false;
        foreach (var requirement in requirements)
        {
            if (requirement == null || requirement.m_resItem == null || requirement.m_amount <= 0) continue;
            sawCost = true;
            string name = requirement.m_resItem.m_itemData?.m_shared?.m_name;
            bool knows = materials != null && !string.IsNullOrEmpty(name) && materials.Contains(name);
            if (anyMaterial && knows) return true;
            if (!anyMaterial && !knows) return false;
        }
        return !sawCost || !anyMaterial;
    }

    public static void SetAnyResearchMaterial(bool any)
    {
        if (anyResearchMaterial != null && anyResearchMaterial.Value != any)
            anyResearchMaterial.Value = any;
        RevealEligibleRecipes();
    }

    public static bool ShowResearchUnlocks =>
        showResearchUnlocks != null && showResearchUnlocks.Value;

    public static void SetShowResearchUnlocks(bool show)
    {
        if (showResearchUnlocks != null && showResearchUnlocks.Value != show)
            showResearchUnlocks.Value = show;
        RefreshResearchDescriptions();
    }

    public static string BuildResearchDescription(string researchId)
    {
        researchBody.TryGetValue(researchId, out var body);
        body = body ?? "";
        bool hide = randomized != null && randomized.Value && !ShowResearchUnlocks;
        if (hide)
            return body + "\r\n\r\nUnlocks: Something?";
        if (!researchUnlockPrefabs.TryGetValue(researchId, out var ids) || ids == null || ids.Length == 0)
            return body;
        var labels = new string[ids.Length];
        for (int i = 0; i < ids.Length; i++)
            labels[i] = UnlockLabel(ids[i]);
        return body + "\r\n\r\nUnlocks: " + string.Join(", ", labels);
    }

    static string UnlockLabel(string prefabId)
    {
        var go = PrefabManager.Instance != null ? PrefabManager.Instance.GetPrefab(prefabId) : null;
        if (go)
        {
            var drop = go.GetComponent<ItemDrop>();
            string token = drop != null && drop.m_itemData != null && drop.m_itemData.m_shared != null
                ? drop.m_itemData.m_shared.m_name
                : null;
            if (string.IsNullOrEmpty(token))
            {
                var piece = go.GetComponent<Piece>();
                if (piece != null) token = piece.m_name;
            }
            if (!string.IsNullOrEmpty(token)) return token;
        }
        return prefabId;
    }

    public static void RefreshResearchDescriptions()
    {
        if (PrefabManager.Instance == null) return;
        foreach (var id in research)
        {
            var go = PrefabManager.Instance.GetPrefab(id);
            var drop = go ? go.GetComponent<ItemDrop>() : null;
            if (drop == null || drop.m_itemData == null || drop.m_itemData.m_shared == null) continue;
            drop.m_itemData.m_shared.m_description = BuildResearchDescription(id);
        }
    }

    public static void SetLocalResearchAccess(ResearchAccessMode mode)
    {
        if (researchAccess != null)
            researchAccess.Value = ResearchAccessName(mode);
        if (SeedControlsAccess) return;
        ActiveResearchAccess = mode;
        RevealEligibleRecipes();
    }

    public static void ApplySeedRules(int? access, bool sequential)
    {
        SeedControlsAccess = access.HasValue;
        SequentialTiers = sequential;
        int accessValue = access ?? 0;
        if (accessValue < 0) accessValue = 0;
        if (accessValue > 3) accessValue = 3;
        ActiveResearchAccess = access.HasValue
            ? (ResearchAccessMode)accessValue
            : ParseResearchAccess(researchAccess?.Value);
        Log?.LogInfo("Research access " + ActiveResearchAccess
            + (SeedControlsAccess ? " from seed." : " from local config.")
            + " Sequential tiers " + (SequentialTiers ? "on." : "off."));
    }

    public static void ClearSeedRules()
    {
        SeedControlsAccess = false;
        SequentialTiers = false;
        ActiveResearchAccess = ParseResearchAccess(researchAccess?.Value);
    }

    public static ResearchAccessMode ParseResearchAccess(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return ResearchAccessMode.Default;
        switch (text.Trim().ToLowerInvariant())
        {
            case "tier":
            case "1":
                return ResearchAccessMode.Tier;
            case "materials":
            case "mats":
            case "2":
                return ResearchAccessMode.Materials;
            case "natural":
            case "3":
                return ResearchAccessMode.Natural;
            default:
                return ResearchAccessMode.Default;
        }
    }

    static string ResearchAccessName(ResearchAccessMode mode)
    {
        switch (mode)
        {
            case ResearchAccessMode.Tier: return "tier";
            case ResearchAccessMode.Materials: return "materials";
            case ResearchAccessMode.Natural: return "natural";
            default: return "default";
        }
    }

    public static bool ResearchRecipeVisible(string researchId)
    {
        switch (ActiveResearchAccess)
        {
            case ResearchAccessMode.Materials:
                return true;
            case ResearchAccessMode.Tier:
                return TierIsOpen(TierOf(researchId));
            case ResearchAccessMode.Natural:
                foreach (string parent in GetResearchRequired(researchId))
                {
                    if (!IsResearchCrafted(parent)) return false;
                }
                return true;
            default:
                return ResearchRequirementsMet(researchId);
        }
    }

    static int TierOf(string researchId)
    {
        if (researchId != null && researchTier.TryGetValue(researchId, out int tier)) return tier;
        return 0;
    }

    static bool TierIsOpen(int tier)
    {
        if (tier <= 0) return true;
        if (!TierDoorItems.TryGetValue(tier, out var items)) return false;
        foreach (string itemName in items)
        {
            if (!archipelagoToResearch.TryGetValue(itemName, out var id)) return false;
            if (!IsResearchUnlocked(id)) return false;
        }
        return true;
    }

    public static void UnlockResearch(string research)
    {
        ZoneSystem.instance.SetGlobalKey(research + "_crafted");
        if (randomized.Value)
        {
            ArchipelagoConnection.SendLocation(research);
        }
        else
        {
            DoUnlockResearch(research);
        }
    }

    public static bool IsResearchUnlocked(string research)
    {
        return ZoneSystem.instance.GetGlobalKey(research);
    }

    public static bool IsResearchCrafted(string research)
    {
        // The crafted key is a routed RPC, so it is not visible in the same craft.
        // The local set is filled when the research item is consumed.
        if (!string.IsNullOrEmpty(research) && craftedResearch.Contains(research)) return true;
        return ZoneSystem.instance.GetGlobalKey(research + "_crafted");
    }

    public static void AddResearchRequirement(string itemID, params string[] researches)
    {
        if (!recipeRequirements.ContainsKey(itemID))
        {
            recipeRequirements[itemID] = new List<string>();
        }
        foreach (string research in researches)
        {
            recipeRequirements[itemID].Add(research);
        }
    }

    public static IEnumerable<string> GetResearchRequired(string itemID)
    {
        if (!recipeRequirements.ContainsKey(itemID)) yield break;
        foreach (string research in recipeRequirements[itemID]) yield return research;
    }

    public static int GetBoost(TrophyResearch.TrophyBoost boost)
    {
        int total = 0;
        foreach (var tr in trophyByItemID.Values)
        {
            if (tr.boost != boost) continue;
            if (!IsResearchUnlocked(tr.researchID)) continue;
            total++;
        }
        return total;
    }

    private void AddResearchRecipes()
    {
        Logger.LogInfo("Trying to add recipes");
        if (!ResearchBenchCraftingStation)
        {
            Logger.LogWarning("AddResearchRecipes: Research bench prefab missing; skipping.");
            return;
        }

        try
        {
            string file = Path.Combine(DataFolder, "research.tsv");

            // Seed a tiny example if missing
            if (!File.Exists(file))
            {
                var seed = string.Join("\n", new[]
                {
                "# iconFromItemPrefab\tresearchItemID\tdisplayName\tdescription\trequiredResearchIDs\tresearchRecipeRequirements\tgatedItemPrefabIDs",
                "Hammer\tresearchWorkbench\tCrafting\tAllows basic crafting\t\tWood:5\tpiece_workbench",
                "Bow\tresearchBowTier1\tBows Tier 1\tAllows to craft bows and arrows\tresearchWorkbench\tWood:5|LeatherScraps:2\tBow|ArrowWood"
            });
                File.WriteAllText(file, seed);
                Logger.LogInfo($"Created starter research file at: {file}");
            }
            Logger.LogInfo("File found at " + file);

            int added = 0;
            foreach (var raw in File.ReadAllLines(file))
            {
                var line = raw.Trim();
                if (line.Length == 0 || line.StartsWith("#")) continue;

                // Split on TABs (no escaping needed if you avoid tabs in text)
                var cols = line.Split('\t');
                if (cols.Length < 7)
                {
                    Logger.LogWarning($"Skipping line (needs 7 columns): {line}");
                    continue;
                }

                string iconSrc = cols[0];
                string rid = cols[1];
                string name = cols[2];
                string desc = cols[3];
                string prereqStr = cols[4];
                string costsStr = cols[5];
                string gatedStr = cols[6];

                if (string.IsNullOrWhiteSpace(rid) || string.IsNullOrWhiteSpace(name))
                {
                    Logger.LogWarning($"Skipping line (missing id/name): {line}");
                    continue;
                }

                int tier = 0;
                if (cols.Length > 7)
                    int.TryParse(cols[7], out tier);
                researchTier[rid] = tier;

                string[] prereqs = SplitPipes(prereqStr);
                string[] gated = SplitPipes(gatedStr);

                var reqs = new List<RequirementConfig>();
                foreach (var tok in SplitPipes(costsStr))
                {
                    var p = tok.Split(':');
                    if (p.Length == 2 && int.TryParse(p[1], out int amt) && amt > 0)
                        reqs.Add(new RequirementConfig(p[0], amt));
                }

                RandomizerUtils.CreateResearch(
                    string.IsNullOrWhiteSpace(iconSrc) ? "Amber" : iconSrc,
                    rid,
                    name,
                    desc ?? string.Empty,
                    prereqs,
                    reqs.ToArray(),
                    gated
                );

                added++;
            }

            Logger.LogInfo($"Loaded and registered {added} research definition(s) from {file}.");
            RevealEligibleRecipes();
        }
        catch (Exception ex)
        {
            Logger.LogError($"AddResearchRecipes (from TSV) failed: {ex}");
        }

        // local helpers — tiny & clear
        string[] SplitPipes(string s)
        {
            if (string.IsNullOrWhiteSpace(s)) return Array.Empty<string>();
            var kept = new List<string>();
            foreach (string part in s.Split('|'))
            {
                if (!string.IsNullOrWhiteSpace(part)) kept.Add(part);
            }
            return kept.ToArray();
        }
    }

    private void CheckRecipesAndPiecesWithoutResearch()
    {
        try
        {
            string pluginFolder = DataFolder;
            string recipesFile = System.IO.Path.Combine(pluginFolder, "RecipesWithoutResearch.txt");
            string piecesFile = System.IO.Path.Combine(pluginFolder, "PiecesWithoutResearch.txt");

            var recipesWithoutResearch = new List<string>();
            var piecesWithoutResearch = new List<string>();

            // --- Recipes: scan ObjectDB recipes
            if (ObjectDB.instance != null && ObjectDB.instance.m_recipes != null)
            {
                foreach (var recipe in ObjectDB.instance.m_recipes)
                {
                    if (recipe == null || recipe.m_item == null || !recipe.m_enabled) continue;
                    string id = recipe.m_item.name;
                    if (string.IsNullOrEmpty(id)) continue;

                    if (!ValheimRandomizer.recipeRequirements.ContainsKey(id))
                    {
                        string toAdd = id;
                        if (recipe.m_craftingStation != null)
                        {
                            toAdd += " " + recipe.m_craftingStation.name + " " + recipe.m_minStationLevel;
                        }
                        recipesWithoutResearch.Add(toAdd);
                    }
                }
            }

            // --- Pieces: gather all buildable pieces from every PieceTable
            var buildablePieces = new HashSet<Piece>();
            var allTables = Resources.FindObjectsOfTypeAll<PieceTable>();
            foreach (var table in allTables)
            {
                if (table?.m_pieces == null) continue;
                foreach (var p in table.m_pieces)
                {
                    if (p != null && p.GetComponent<Piece>() != null) buildablePieces.Add(p.GetComponent<Piece>());
                }
            }

            foreach (var piece in buildablePieces)
            {
                string id = piece?.name;
                if (string.IsNullOrEmpty(id)) continue;

                if (!ValheimRandomizer.recipeRequirements.ContainsKey(id))
                {
                    piecesWithoutResearch.Add(id);
                }
            }

            System.IO.File.WriteAllLines(recipesFile, recipesWithoutResearch);
            System.IO.File.WriteAllLines(piecesFile, piecesWithoutResearch);

            Logger.LogInfo($"Exported {recipesWithoutResearch.Count} recipes and {piecesWithoutResearch.Count} pieces without research.");
        }
        catch (Exception ex)
        {
            Logger.LogError($"Error while exporting ungated recipes/pieces: {ex}");
        }
    }

    private void AddTrophyResearches()
    {
        try
        {
            string file = Path.Combine(DataFolder, "trophies.tsv");
            if (!System.IO.File.Exists(file))
            {
                Logger.LogWarning($"Trophy research file not found at {file}. Skipping trophy researches.");
                return;
            }

            int added = 0;

            foreach (var raw in System.IO.File.ReadAllLines(file))
            {
                var line = raw.Trim();
                if (line.Length == 0 || line.StartsWith("#")) continue;

                var cols = line.Split('\t');
                if (cols.Length < 4)
                {
                    Logger.LogWarning($"Skipping trophy line (needs 4 columns): {line}");
                    continue;
                }

                string itemID = cols[0];
                string researchID = cols[1];
                string boostStr = cols[2];

                if (string.IsNullOrWhiteSpace(itemID) || string.IsNullOrWhiteSpace(researchID))
                {
                    Logger.LogWarning($"Skipping trophy line (missing itemID/researchID): {line}");
                    continue;
                }

                if (!TryParseBoost(boostStr, out TrophyResearch.TrophyBoost boost))
                {
                    Logger.LogWarning($"Unknown boost type '{boostStr}' for '{itemID}'. Defaulting to Load.");
                    boost = TrophyResearch.TrophyBoost.Load;
                }

                RandomizerUtils.CreateTrophyResearch(itemID, researchID, boost);
                added++;
            }

            Logger.LogInfo($"Loaded and registered {added} trophy research definition(s) from {file}.");
        }
        catch (Exception ex)
        {
            Logger.LogError($"AddTrophyResearches (from TSV) failed: {ex}");
        }
    }

    private void AddDropChecks()
    {
        try
        {
            string file = Path.Combine(DataFolder, "drops.tsv");
            if (!File.Exists(file))
            {
                Logger.LogWarning($"Drop check file not found at {file}.");
                return;
            }

            dropByItemID.Clear();
            dropByLocationName.Clear();
            bossByItemName.Clear();
            bossByDefeatKey.Clear();
            BossDrops.Clear();
            bossPrefabs.Clear();
            int added = 0;
            int bosses = 0;
            foreach (var raw in File.ReadAllLines(file))
            {
                var line = raw.Trim();
                if (line.Length == 0 || line.StartsWith("#")) continue;
                var cols = line.Split('\t');
                if (cols.Length < 4)
                {
                    Logger.LogWarning($"Skipping drop line (needs 4 columns): {line}");
                    continue;
                }

                string itemID = cols[0];
                string display = cols[1];
                if (!int.TryParse(cols[3], out int amount) || amount < 1) amount = 1;
                if (string.IsNullOrWhiteSpace(itemID) || string.IsNullOrWhiteSpace(display)) continue;

                if (cols.Length >= 9 && cols[4] == "boss")
                {
                    bool onePerPlayer = cols[8] == "1";
                    var boss = new BossDrop(itemID, display, cols[7], cols[6], cols[5], amount, onePerPlayer);
                    BossDrops.Add(boss);
                    bossByItemName[display] = boss;
                    bossByDefeatKey[cols[6]] = boss;
                    bossPrefabs.Add(itemID);
                    bosses++;
                    continue;
                }

                var drop = new DropCheck(itemID, "Gather: " + display, amount);
                dropByItemID[itemID] = drop;
                dropByLocationName[drop.locationName] = drop;
                added++;
            }

            SnapshotDropCounts();
            Logger.LogInfo($"Loaded {added} drop check(s) and {bosses} boss drop(s) from {file}.");
        }
        catch (Exception ex)
        {
            Logger.LogError($"AddDropChecks failed: {ex}");
        }
    }

    static bool TryParseBoost(string s, out TrophyResearch.TrophyBoost boost)
    {
        return Enum.TryParse(s, out boost);
    }
}
