using HarmonyLib;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System;
using UnityEngine;
using TMPro; // optional, but harmless

public static class Patches
{
    // ---------- Piece (building) gating ----------
    // Patch all Player.HaveRequirements overloads whose first parameter is Piece
    [HarmonyPatch]
    private static class Player_HaveRequirements_Piece_Patch
    {
        static IEnumerable<MethodBase> TargetMethods()
        {
            return typeof(Player)
                .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
                .Where(m => m.Name == "HaveRequirements")
                .Where(m =>
                {
                    var p = m.GetParameters();
                    return p.Length > 0 && p[0].ParameterType == typeof(Piece);
                });
        }

        // We only need the first parameter (Piece) and __result; Harmony will ignore the rest
        static bool Prefix(Piece piece, ref bool __result)
        {
            if (piece == null) return true;

            // Use the prefab/component name (e.g., "piece_workbench")
            string id = piece.name;
            if (!string.IsNullOrEmpty(id) && RandomizerUtils.CanResearchBeCrafted(id))
            {
                ValheimRandomizer.Log?.LogDebug($"Blocked building '{id}' (missing research).");
                __result = false; // pretend requirements not met
                return false;     // skip original method
            }

            return true; // run original
        }
    }

    // ---------- Recipe (crafting) gating ----------
    // Patch all Player.HaveRequirements overloads whose first parameter is Recipe
    [HarmonyPatch]
    private static class Player_HaveRequirements_Recipe_Patch
    {
        static IEnumerable<MethodBase> TargetMethods()
        {
            return typeof(Player)
                .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
                .Where(m => m.Name == "HaveRequirements")
                .Where(m =>
                {
                    var p = m.GetParameters();
                    return p.Length > 0 && p[0].ParameterType == typeof(Recipe);
                });
        }

        // Only grab the recipe; Harmony will pass extra args we don't declare
        static bool Prefix(Recipe recipe, ref bool __result)
        {
            if (recipe == null) return true;

            // Prefer the prefab name of the result item
            string id = null;
            try
            {
                // In Valheim, the prefab name is accessible via ItemDrop.name (component) or gameObject.name.
                // Either is fine; .name typically mirrors the prefab name.
                id = recipe.m_item ? recipe.m_item.name : null;
            }
            catch
            {
                // ignore
            }

            if (!string.IsNullOrEmpty(id) && RandomizerUtils.CanResearchBeCrafted(id))
            {
                ValheimRandomizer.Log?.LogDebug($"Blocked crafting '{id}' (missing research).");
                __result = false; // pretend requirements not met
                return false;     // skip original method
            }

            return true; // run original
        }
    }

    // Research bench: craft tab is unfinished research, sorted craftable-then-tier.
    // The upgrade tab is relabeled Done and lists researches already sent.
    [HarmonyPatch(typeof(InventoryGui), "UpdateRecipeList", new Type[] { typeof(List<Recipe>) })]
    public static class InventoryGui_UpdateRecipeList_Patch
    {
        static bool Prefix(InventoryGui __instance, List<Recipe> recipes)
        {
            try
            {
                ResearchBenchList.ApplySortWeights();
                bool bench = ResearchBenchList.IsOpen();
                ResearchBenchList.SetUpgradeTabLabel(__instance, bench);
                if (!bench) return true;

                if (__instance.InCraftTab())
                {
                    recipes.RemoveAll(ResearchBenchList.IsCompleted);
                    return true;
                }

                return ResearchBenchList.FillDoneTab(__instance) ? false : true;
            }
            catch (Exception e)
            {
                ValheimRandomizer.Log?.LogWarning($"Research list update failed: {e.Message}");
                return true;
            }
        }
    }

    [HarmonyPatch(typeof(InventoryGui), "UpdateRecipe")]
    public static class InventoryGui_UpdateRecipe_Patch
    {
        static void Postfix(InventoryGui __instance)
        {
            try
            {
                bool bench = ResearchBenchList.IsOpen();
                ResearchBenchList.SetUpgradeTabLabel(__instance, bench);
                if (!bench || __instance.InCraftTab()) return;
                ResearchBenchList.LockCompletedButton(__instance);
            }
            catch (Exception e)
            {
                ValheimRandomizer.Log?.LogWarning($"Research bench tab label failed: {e.Message}");
            }
        }
    }

    public static void RefreshResearchBench()
    {
        try
        {
            ResearchBenchList.RefreshOpenList();
        }
        catch (Exception e)
        {
            ValheimRandomizer.Log?.LogWarning($"Research bench refresh failed: {e.Message}");
        }
    }

    static class ResearchBenchList
    {
        const string DoneLabel = "Done";

        static readonly FieldInfo AvailableRecipesField =
            AccessTools.Field(typeof(InventoryGui), "m_availableRecipes");
        static readonly FieldInfo SelectedRecipeField =
            AccessTools.Field(typeof(InventoryGui), "m_selectedRecipe");
        static readonly AccessTools.FieldRef<InventoryGui, float> ListBaseSize =
            AccessTools.FieldRefAccess<InventoryGui, float>("m_recipeListBaseSize");
        static readonly MethodInfo AddRecipeToListMethod =
            AccessTools.Method(typeof(InventoryGui), "AddRecipeToList", new[]
            {
                typeof(Player), typeof(Recipe), typeof(ItemDrop.ItemData), typeof(bool)
            });
        static readonly MethodInfo UpdateCraftingPanelMethod =
            AccessTools.Method(typeof(InventoryGui), "UpdateCraftingPanel", new[] { typeof(bool) });

        static string savedUpgradeLabel;
        static bool weightsApplied;
        static Dictionary<string, Recipe> researchRecipes;
        static TMP_Text[] upgradeTabLabels;
        static TMP_Text craftButtonLabel;
        static FieldInfo craftTooltipText;

        public static void RefreshOpenList()
        {
            if (!IsOpen() || UpdateCraftingPanelMethod == null) return;
            var gui = InventoryGui.instance;
            if (!gui) return;
            UpdateCraftingPanelMethod.Invoke(gui, new object[] { false });
        }

        public static bool IsOpen()
        {
            var player = Player.m_localPlayer;
            var station = player ? player.GetCurrentCraftingStation() : null;
            if (!station) return false;
            if (station.m_name == "Research Bench") return true;
            string name = station.gameObject ? station.gameObject.name : null;
            return name == ValheimRandomizer.ResearchBenchPrefabName
                || (name != null && name.StartsWith(ValheimRandomizer.ResearchBenchPrefabName, StringComparison.Ordinal));
        }

        public static bool IsCompleted(Recipe recipe)
        {
            string id = recipe?.m_item ? recipe.m_item.name : null;
            return !string.IsNullOrEmpty(id)
                && ValheimRandomizer.researchTier.ContainsKey(id)
                && ValheimRandomizer.IsResearchCrafted(id);
        }

        public static void ApplySortWeights()
        {
            if (weightsApplied) return;
            var all = ObjectDB.instance != null ? ObjectDB.instance.m_recipes : null;
            if (all == null) return;
            int matched = 0;
            foreach (var recipe in all)
            {
                string id = recipe?.m_item ? recipe.m_item.name : null;
                if (string.IsNullOrEmpty(id)) continue;
                if (!ValheimRandomizer.researchTier.TryGetValue(id, out int tier)) continue;
                matched++;
                if (recipe.m_listSortWeight != tier) recipe.m_listSortWeight = tier;
            }
            if (matched > 0 && matched >= ValheimRandomizer.research.Count)
                weightsApplied = true;
        }

        public static bool FillDoneTab(InventoryGui gui)
        {
            if (AddRecipeToListMethod == null || AvailableRecipesField == null || gui.m_recipeListRoot == null)
                return false;

            var available = AvailableRecipesField.GetValue(gui) as System.Collections.IList;
            if (available == null) return false;

            available.Clear();
            var root = gui.m_recipeListRoot;
            for (int i = root.childCount - 1; i >= 0; i--)
                UnityEngine.Object.Destroy(root.GetChild(i).gameObject);

            EnsureRecipeIndex();
            var done = new List<Recipe>();
            if (researchRecipes != null)
            {
                foreach (var id in ValheimRandomizer.research)
                {
                    if (!ValheimRandomizer.IsResearchCrafted(id)) continue;
                    if (researchRecipes.TryGetValue(id, out var recipe)) done.Add(recipe);
                }
            }
            done.Sort(CompareTierThenName);

            var player = Player.m_localPlayer;
            foreach (var recipe in done)
            {
                // canCraft stays true so the icon and name stay visible. The button is locked.
                AddRecipeToListMethod.Invoke(gui, new object[] { player, recipe, null, true });
            }

            float height = Mathf.Max(ListBaseSize(gui), done.Count * gui.m_recipeListSpace);
            gui.m_recipeListRoot.SetSizeWithCurrentAnchors(RectTransform.Axis.Vertical, height);
            return true;
        }

        public static void LockCompletedButton(InventoryGui gui)
        {
            if (gui.m_craftButton == null || SelectedRecipeField == null) return;
            object pair = SelectedRecipeField.GetValue(gui);
            var recipe = pair?.GetType().GetProperty("Recipe")?.GetValue(pair) as Recipe;
            if (!IsCompleted(recipe)) return;

            gui.m_craftButton.interactable = false;
            if (craftButtonLabel == null)
                craftButtonLabel = gui.m_craftButton.GetComponentInChildren<TMP_Text>();
            if (craftButtonLabel != null && craftButtonLabel.text != DoneLabel)
                craftButtonLabel.text = DoneLabel;
            ClearCraftTooltip(gui.m_craftButton);
        }

        public static void SetUpgradeTabLabel(InventoryGui gui, bool doneTab)
        {
            if (gui?.m_tabUpgrade == null) return;
            if (upgradeTabLabels == null || upgradeTabLabels.Length == 0)
            {
                var found = gui.m_tabUpgrade.GetComponentsInChildren<TMP_Text>(true);
                if (found != null && found.Length > 0) upgradeTabLabels = found;
            }
            var labels = upgradeTabLabels;
            if (labels == null || labels.Length == 0) return;

            if (savedUpgradeLabel == null)
            {
                foreach (var label in labels)
                {
                    if (label == null || string.IsNullOrEmpty(label.text) || label.text == DoneLabel) continue;
                    savedUpgradeLabel = label.text;
                    break;
                }
            }

            string text = doneTab ? DoneLabel : (savedUpgradeLabel ?? "Upgrade");
            foreach (var label in labels)
            {
                if (label == null || label.text == text) continue;
                if (savedUpgradeLabel != null && label.text != savedUpgradeLabel && label.text != DoneLabel) continue;
                label.text = text;
            }
        }

        static void EnsureRecipeIndex()
        {
            if (researchRecipes != null && researchRecipes.Count > 0) return;
            var all = ObjectDB.instance != null ? ObjectDB.instance.m_recipes : null;
            if (all == null) return;
            researchRecipes = new Dictionary<string, Recipe>(StringComparer.Ordinal);
            foreach (var recipe in all)
            {
                string id = recipe?.m_item ? recipe.m_item.name : null;
                if (string.IsNullOrEmpty(id) || researchRecipes.ContainsKey(id)) continue;
                if (!ValheimRandomizer.researchTier.ContainsKey(id)) continue;
                researchRecipes.Add(id, recipe);
            }
            if (researchRecipes.Count == 0) researchRecipes = null;
        }

        static void ClearCraftTooltip(Component button)
        {
            if (button == null) return;
            if (craftTooltipText == null)
            {
                foreach (var behaviour in button.GetComponents<MonoBehaviour>())
                {
                    if (behaviour == null || behaviour.GetType().Name != "UITooltip") continue;
                    var field = behaviour.GetType().GetField("m_text");
                    if (field != null && field.FieldType == typeof(string))
                    {
                        craftTooltipText = field;
                        craftTooltipTarget = behaviour;
                        break;
                    }
                }
            }
            if (craftTooltipText != null && craftTooltipTarget != null)
                craftTooltipText.SetValue(craftTooltipTarget, "");
        }

        static MonoBehaviour craftTooltipTarget;

        static int CompareTierThenName(Recipe a, Recipe b)
        {
            int tier = TierOf(a).CompareTo(TierOf(b));
            if (tier != 0) return tier;
            return string.Compare(DisplayName(a), DisplayName(b), StringComparison.OrdinalIgnoreCase);
        }

        static int TierOf(Recipe recipe)
        {
            string id = recipe?.m_item ? recipe.m_item.name : null;
            if (!string.IsNullOrEmpty(id) && ValheimRandomizer.researchTier.TryGetValue(id, out int tier)) return tier;
            return recipe != null ? recipe.m_listSortWeight : 0;
        }

        static string DisplayName(Recipe recipe)
        {
            return recipe?.m_item?.m_itemData?.m_shared?.m_name ?? "";
        }
    }

    // ========================= Carry weight =========================
    [HarmonyPatch(typeof(Player), nameof(Player.GetMaxCarryWeight))]
    private static class Player_GetMaxCarryWeight_Patch
    {
        private static void Postfix(Player __instance, ref float __result)
        {
            if (__instance == null || !__instance.IsPlayer()) return;
            int tiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.Load);
            if (tiers <= 0) return;
            __result += ValheimRandomizer.TrophyResearch.LoadPerTrophy * tiers;
        }
    }

    [HarmonyPatch]
    internal static class Player_GetTotalFoodValue_Patch
    {
        // Cached direct field ref => fastest way to access a private field with Harmony
        private static readonly AccessTools.FieldRef<Player, List<Player.Food>> FoodsRef =
            AccessTools.FieldRefAccess<Player, List<Player.Food>>("m_foods");

        static MethodBase TargetMethod()
        {
            // private void GetTotalFoodValue(out float hp, out float stamina, out float eitr)
            var paramTypes = new[]
            {
            typeof(float).MakeByRefType(),
            typeof(float).MakeByRefType(),
            typeof(float).MakeByRefType()
        };
            return AccessTools.Method(typeof(Player), "GetTotalFoodValue", paramTypes);
        }

        static bool Prepare() => TargetMethod() != null && FoodsRef != null;

        // Postfix so we bump the already-accumulated totals
        static void Postfix(Player __instance, ref float hp, ref float stamina, ref float eitr)
        {
            if (__instance == null) return;

            // Read private m_foods via FieldRef
            var foodsList = FoodsRef(__instance);
            int foods = foodsList != null ? foodsList.Count : 0;
            if (foods <= 0) return;

            // HP
            int hpTiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.HP);
            if (hpTiers > 0) hp += ValheimRandomizer.TrophyResearch.HpPerFood * foods * hpTiers;

            // Stamina
            int stTiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.Stamina);
            if (stTiers > 0) stamina += ValheimRandomizer.TrophyResearch.StaminaPerFood * foods * stTiers;

            // Eitr
            int eiTiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.Eitr);
            if (eiTiers > 0) eitr += ValheimRandomizer.TrophyResearch.EitrPerFood * foods * eiTiers;
        }
    }

    [HarmonyPatch]
    internal static class Player_AddAdrenaline_Patch
    {
        static MethodBase TargetMethod() =>
            AccessTools.Method(typeof(Player), "AddAdrenaline", new[] { typeof(float) });

        static bool Prepare() => TargetMethod() != null;

        // Add +3 per tier to the incoming value before the game processes it.
        static void Prefix(Player __instance, ref float v)
        {
            if (__instance == null || __instance != Player.m_localPlayer) return;

            int tiers = ValheimRandomizer.GetBoost(
                ValheimRandomizer.TrophyResearch.TrophyBoost.Adrenaline);

            if (tiers <= 0) return;

            v += ValheimRandomizer.TrophyResearch.AdrenalinePerTrophy * tiers;
        }
    }

    internal static class SEManPatchHelpers
    {
        // SEMan -> Character owner
        public static readonly AccessTools.FieldRef<SEMan, Character> OwnerRef =
            AccessTools.FieldRefAccess<SEMan, Character>("m_character");

        // Player -> private List<Player.Food> m_foods
        public static readonly AccessTools.FieldRef<Player, List<Player.Food>> FoodsRef =
            AccessTools.FieldRefAccess<Player, List<Player.Food>>("m_foods");

        public static bool IsLocalPlayer(SEMan se)
        {
            var ch = OwnerRef != null ? OwnerRef(se) : null;
            return ch is Player p && p == Player.m_localPlayer;
        }

        public static int GetActiveFoodCount(Player p)
        {
            if (FoodsRef == null || p == null) return 0;
            var foods = FoodsRef(p);
            return foods != null ? foods.Count : 0;
        }
    }

    // ======================= HEALTH REGEN (ref float) =======================
    [HarmonyPatch]
    internal static class SEMan_ModifyHealthRegen_RefOnly_Patch
    {
        static MethodBase TargetMethod()
        {
            // Try: void ModifyHealthRegen(ref float regen)
            var param = new[] { typeof(float).MakeByRefType() };
            return AccessTools.Method(typeof(SEMan), "ModifyHealthRegen", param);
        }

        static bool Prepare() => TargetMethod() != null && SEManPatchHelpers.OwnerRef != null && SEManPatchHelpers.FoodsRef != null;

        static void Postfix(SEMan __instance, ref float regenMultiplier)
        {
            if (!SEManPatchHelpers.IsLocalPlayer(__instance)) return;
            var player = Player.m_localPlayer;
            int foods = SEManPatchHelpers.GetActiveFoodCount(player);
            if (foods <= 0) return;

            int tiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.HPRegen);
            if (tiers <= 0) return;

            regenMultiplier += (ValheimRandomizer.TrophyResearch.RegenPercentPerFood / 100f) * foods * tiers;
        }
    }

    // ======================= STAMINA REGEN (ref float) =======================
    [HarmonyPatch]
    internal static class SEMan_ModifyStaminaRegen_RefOnly_Patch
    {
        static MethodBase TargetMethod()
        {
            // Try: void ModifyStaminaRegen(ref float regen)
            var param = new[] { typeof(float).MakeByRefType() };
            return AccessTools.Method(typeof(SEMan), "ModifyStaminaRegen", param);
        }

        static bool Prepare() => TargetMethod() != null && SEManPatchHelpers.OwnerRef != null && SEManPatchHelpers.FoodsRef != null;

        static void Postfix(SEMan __instance, ref float staminaMultiplier)
        {
            if (!SEManPatchHelpers.IsLocalPlayer(__instance)) return;
            var player = Player.m_localPlayer;
            int foods = SEManPatchHelpers.GetActiveFoodCount(player);
            if (foods <= 0) return;

            int tiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.StaminaRegen);
            if (tiers <= 0) return;

            staminaMultiplier += (ValheimRandomizer.TrophyResearch.RegenPercentPerFood / 100f) * foods * tiers;
        }
    }

    // ======================= EITR REGEN (ref float) =======================
    [HarmonyPatch]
    internal static class SEMan_ModifyEitrRegen_RefOnly_Patch
    {
        static MethodBase TargetMethod()
        {
            var param = new[] { typeof(float).MakeByRefType() };
            return AccessTools.Method(typeof(SEMan), "ModifyEitrRegen", param);
        }

        static bool Prepare() => TargetMethod() != null && SEManPatchHelpers.OwnerRef != null && SEManPatchHelpers.FoodsRef != null;

        static void Postfix(SEMan __instance, ref float eitrMultiplier)
        {
            if (!SEManPatchHelpers.IsLocalPlayer(__instance)) return;
            var player = Player.m_localPlayer;
            int foods = SEManPatchHelpers.GetActiveFoodCount(player);
            if (foods <= 0) return;

            int tiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.EitrRegen);
            if (tiers <= 0) return;

            eitrMultiplier += (ValheimRandomizer.TrophyResearch.RegenPercentPerFood / 100f) * foods * tiers;
        }
    }

    // Walk and sprint share one percent. Armor weight stays on its own factor.
    [HarmonyPatch(typeof(Player), "GetJogSpeedFactor")]
    internal static class Player_GetJogSpeedFactor_Patch
    {
        static bool Prepare() => AccessTools.Method(typeof(Player), "GetJogSpeedFactor") != null;

        static void Postfix(Player __instance, ref float __result)
        {
            ApplyMoveSpeed(__instance, ref __result);
        }
    }

    [HarmonyPatch(typeof(Player), "GetRunSpeedFactor")]
    internal static class Player_GetRunSpeedFactor_Patch
    {
        static bool Prepare() => AccessTools.Method(typeof(Player), "GetRunSpeedFactor") != null;

        static void Postfix(Player __instance, ref float __result)
        {
            ApplyMoveSpeed(__instance, ref __result);
        }
    }

    static void ApplyMoveSpeed(Player player, ref float factor)
    {
        if (player != Player.m_localPlayer) return;
        int tiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.Speed);
        if (tiers <= 0) return;
        factor *= 1f + (ValheimRandomizer.TrophyResearch.SpeedPercentPerTrophy / 100f) * tiers;
    }

    // Adds to the same multiplier rested uses, so the two stack as 1.75x rather than 1.875x.
    [HarmonyPatch]
    internal static class SEMan_ModifyRaiseSkill_Patch
    {
        static MethodBase TargetMethod() =>
            AccessTools.Method(typeof(SEMan), "ModifyRaiseSkill", new[] { typeof(Skills.SkillType), typeof(float).MakeByRefType() });

        static bool Prepare() => TargetMethod() != null && SEManPatchHelpers.OwnerRef != null;

        static void Postfix(SEMan __instance, Skills.SkillType skill, ref float multiplier)
        {
            if (skill == Skills.SkillType.None) return;
            if (!SEManPatchHelpers.IsLocalPlayer(__instance)) return;

            int tiers = ValheimRandomizer.GetBoost(ValheimRandomizer.TrophyResearch.TrophyBoost.SkillXp);
            if (tiers <= 0) return;

            multiplier += (ValheimRandomizer.TrophyResearch.SkillXpPercentPerTrophy / 100f) * tiers;
        }
    }

    [HarmonyPatch(typeof(Player), nameof(Player.GetBodyArmor))]
    internal static class Player_GetBodyArmor_DefenseBoost_Patch
    {
        // Postfix: multiply final armor value
        private static void Postfix(Player __instance, ref float __result)
        {
            if (__instance != Player.m_localPlayer) return;

            int tiers = ValheimRandomizer.GetBoost(
                ValheimRandomizer.TrophyResearch.TrophyBoost.Defense);

            if (tiers <= 0) return;

            float mul = 1f + (ValheimRandomizer.TrophyResearch.DefensePercentPerTrophy / 100f) * tiers;
            __result *= mul;
        }
    }

    [HarmonyPatch(typeof(Character), nameof(Character.Damage))]
    internal static class Character_Damage_AttackBoost_Patch
    {
        // Prefix: scale outgoing damage when the attacker is the local player
        private static void Prefix(Character __instance, HitData hit)
        {
            if (hit == null) return;

            var attacker = hit.GetAttacker();
            if (!(attacker is Player p) || p != Player.m_localPlayer) return;

            int tiers = ValheimRandomizer.GetBoost(
                ValheimRandomizer.TrophyResearch.TrophyBoost.Attack);

            if (tiers <= 0) return;

            float mul = 1f + (ValheimRandomizer.TrophyResearch.AttackPercentPerTrophy / 100f) * tiers;
            ScaleDamageTypes(ref hit.m_damage, mul);
        }

        private static void ScaleDamageTypes(ref HitData.DamageTypes dmg, float mul)
        {
            dmg.m_damage *= mul;
            dmg.m_blunt *= mul;
            dmg.m_slash *= mul;
            dmg.m_pierce *= mul;
            dmg.m_fire *= mul;
            dmg.m_frost *= mul;
            dmg.m_lightning *= mul;
            dmg.m_poison *= mul;
            dmg.m_spirit *= mul;
            // include tool-like damages in case something uses them offensively
            dmg.m_pickaxe *= mul;
            dmg.m_chop *= mul;
        }
    }

    [HarmonyPatch(typeof(TextsDialog), "AddActiveEffects")]
    static class TextsDialog_AddActiveEffects_Patch
    {
        static readonly AccessTools.FieldRef<TextsDialog, List<TextsDialog.TextInfo>> TextsRef =
            AccessTools.FieldRefAccess<TextsDialog, List<TextsDialog.TextInfo>>("m_texts");

        static void Prefix(TextsDialog __instance, out int __state)
        {
            var list = TextsRef(__instance);
            __state = list != null ? list.Count : -1;
        }

        static void Postfix(TextsDialog __instance, int __state)
        {
            if (__state < 0) return;
            var list = TextsRef(__instance);
            if (list == null || list.Count != __state + 1 || list.Count == 0) return;

            string block = ValheimRandomizer.BuildTrophyStatusBlock();
            if (string.IsNullOrEmpty(block)) return;

            var info = list[0];
            if (info == null) return;
            info.m_text = string.IsNullOrEmpty(info.m_text)
                ? block
                : info.m_text.TrimEnd() + "\n\n" + block;
        }
    }

    // Pity counts update inside the drop roll. The tracker reads them from the next publish.
    [HarmonyPatch(typeof(CharacterDrop), nameof(CharacterDrop.GenerateDropList))]
    static class CharacterDrop_Pity_Patch
    {
        static void Postfix()
        {
            ValheimRandomizer.MarkTrophyPityDirty();
        }
    }

    // The unique boss drop is the Archipelago item. The corpse keeps its trophy and the rest of the table.
    [HarmonyPatch(typeof(CharacterDrop), nameof(CharacterDrop.GenerateDropList))]
    static class CharacterDrop_GenerateDropList_Patch
    {
        static void Postfix(List<KeyValuePair<GameObject, int>> __result)
        {
            if (!ArchipelagoConnection.BossDropsEnabled || __result == null || __result.Count == 0) return;
            __result.RemoveAll(pair => pair.Key != null && ValheimRandomizer.IsBossDropPrefab(pair.Key.name));
        }
    }

    // x2 doubles trophy chance and caps pity at 10. Easy forces the first trophy, then leaves the roll alone.
    [HarmonyPatch(typeof(CharacterDrop), nameof(CharacterDrop.GenerateDropList))]
    static class CharacterDrop_TrophyHelp_Patch
    {
        const int PityCap = 10;

        static void Prefix(CharacterDrop __instance, out float[] __state)
        {
            __state = null;
            if (ValheimRandomizer.ActiveTrophyDrops != ValheimRandomizer.TrophyDropMode.Double) return;
            if (__instance == null || __instance.m_drops == null) return;
            var saved = new float[__instance.m_drops.Count];
            bool any = false;
            for (int i = 0; i < __instance.m_drops.Count; i++)
            {
                var drop = __instance.m_drops[i];
                saved[i] = drop != null ? drop.m_chance : 0f;
                if (!IsTrophy(drop)) continue;
                any = true;
                drop.m_chance *= 2f;
                ClampPity(drop);
            }
            if (any) __state = saved;
        }

        static void Postfix(CharacterDrop __instance, List<KeyValuePair<GameObject, int>> __result, float[] __state)
        {
            if (__state != null && __instance != null && __instance.m_drops != null)
            {
                int count = Math.Min(__state.Length, __instance.m_drops.Count);
                for (int i = 0; i < count; i++)
                {
                    var drop = __instance.m_drops[i];
                    if (!IsTrophy(drop)) continue;
                    ClampPity(drop);
                    drop.m_chance = __state[i];
                }
            }
            if (ValheimRandomizer.ActiveTrophyDrops == ValheimRandomizer.TrophyDropMode.Easy)
                ForceFirstTrophy(__instance, __result);
        }

        static bool IsTrophy(CharacterDrop.Drop drop)
        {
            return drop != null && drop.m_prefab != null
                && ValheimRandomizer.trophyByItemID.ContainsKey(drop.m_prefab.name);
        }

        static void ClampPity(CharacterDrop.Drop drop)
        {
            if (drop.m_prefab == null || CharacterDrop.s_pseudoCounter == null) return;
            string name = drop.m_prefab.name;
            ClampOne(name, drop.m_chance);
            if (!drop.m_levelMultiplier) return;
            ClampOne(name, drop.m_chance * 2f);
            ClampOne(name, drop.m_chance * 4f);
        }

        static void ClampOne(string name, float chance)
        {
            if (chance <= 0f || chance > 0.3f) return;
            int key = name.GetStableHashCode() + (int)(chance * 1000f);
            if (CharacterDrop.s_pseudoCounter.TryGetValue(key, out int count) && count > PityCap)
                CharacterDrop.s_pseudoCounter[key] = PityCap;
        }

        static void ForceFirstTrophy(CharacterDrop dropper, List<KeyValuePair<GameObject, int>> result)
        {
            if (dropper == null || dropper.m_drops == null || result == null || ZoneSystem.instance == null) return;
            for (int i = 0; i < dropper.m_drops.Count; i++)
            {
                var drop = dropper.m_drops[i];
                if (!IsTrophy(drop)) continue;
                string key = "ap_trophy_first_" + drop.m_prefab.name;
                if (ZoneSystem.instance.GetGlobalKey(key)) continue;
                ZoneSystem.instance.SetGlobalKey(key);
                bool present = false;
                for (int r = 0; r < result.Count; r++)
                {
                    if (result[r].Key == drop.m_prefab)
                    {
                        present = true;
                        break;
                    }
                }
                if (!present) result.Add(new KeyValuePair<GameObject, int>(drop.m_prefab, 1));
            }
        }
    }
}
