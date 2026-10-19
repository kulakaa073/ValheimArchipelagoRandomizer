using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.WebSockets;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine.Events;
using Archipelago.MultiClient.Net;
using Archipelago.MultiClient.Net.Enums;
using Archipelago.MultiClient.Net.Exceptions;
using Archipelago.MultiClient.Net.Models;
using Archipelago.MultiClient.Net.Helpers;
using Newtonsoft.Json.Linq;

internal static class ArchipelagoConnection
{
    public const string DefaultGoalDefeatKey = "defeated_frozenking_p3";
    public const string DefaultGoalLocationName = "Defeat Kall";
    public const string GoalItemName = "Victory";
    static string goalDefeatKey = DefaultGoalDefeatKey;
    static string goalLocationName = DefaultGoalLocationName;

    private static ArchipelagoSession session;
    private static bool connected;
    public static bool IsConnected => connected && session != null;
    public static string DisconnectMessage { get; private set; }
    public static bool DropChecksEnabled { get; private set; }
    public static bool BossDropsEnabled { get; private set; }
    static bool dropChecksResolved;
    static int lost;
    static int sendGeneration;
    static Task inflight;
    static DateTime inflightStartedUtc;
    static Action inflightSuccess;
    static readonly object noticeLock = new object();
    static string pendingNotice;
    static readonly TimeSpan SendTimeout = TimeSpan.FromSeconds(8);

    public static void Connect(string host, int port, string slot, string password)
    {
        Disconnect();

        session = ArchipelagoSessionFactory.CreateSession(host, port);
        try
        {
            var result = session.TryConnectAndLogin("Valheim", slot,
                ItemsHandlingFlags.AllItems, password: password);

            if (!result.Successful)
            {
                var failure = (LoginFailure)result;
                throw new Exception(string.Join("; ", failure.Errors ?? Array.Empty<string>()));
            }

            gottenItems.Clear();
            warnedMissingDrops.Clear();
            ResolveDropChecks(result);
            ResolveBossDrops(result);
            ApplyGoal(result);
            ValheimRandomizer.ApplySeedRules(ReadSlotInt(result, "research_access"), ReadSlotBool(result, "sequential_tiers"));
            session.Items.ItemReceived += OnApItemReceived;
            DisconnectMessage = null;
            session.Socket.SocketClosed += OnSocketClosed;
            session.Socket.ErrorReceived += OnSocketError;
            connected = true;
            PublishResearchCosts();
            if (successSlotData(result, out var slotData))
            {
                ValheimRandomizer.Log?.LogInfo("Slot data keys: " + string.Join(", ", slotData.Keys));
            }
        }
        catch
        {
            Disconnect();
            throw;
        }
    }

    public static void Disconnect()
    {
        ReleaseSession(closeSocket: true);
        DisconnectMessage = null;
        Interlocked.Exchange(ref lost, 0);
    }

    static void LoseConnection(string message)
    {
        if (Interlocked.Exchange(ref lost, 1) != 0) return;
        DisconnectMessage = message;
        lock (noticeLock) pendingNotice = message;
        ValheimRandomizer.Log?.LogError(message);
        ReleaseSession(closeSocket: false);
    }

    static void ReleaseSession(bool closeSocket)
    {
        var old = session;
        session = null;
        connected = false;
        sendGeneration++;
        var abandoned = inflight;
        inflight = null;
        inflightSuccess = null;
        if (abandoned != null && !abandoned.IsCompleted)
        {
            abandoned.ContinueWith(
                t => { var ignored = t.Exception; },
                TaskContinuationOptions.OnlyOnFaulted);
        }
        DropChecksEnabled = false;
        BossDropsEnabled = false;
        dropChecksResolved = false;
        goalDefeatKey = DefaultGoalDefeatKey;
        goalLocationName = DefaultGoalLocationName;
        ValheimRandomizer.ClearSeedRules();
        if (old == null) return;

        try
        {
            old.Items.ItemReceived -= OnApItemReceived;
        }
        catch (Exception ex)
        {
            ValheimRandomizer.Log?.LogWarning("Disconnect unhook failed: " + ex.Message);
        }

        try
        {
            if (old.Socket != null)
            {
                old.Socket.SocketClosed -= OnSocketClosed;
                old.Socket.ErrorReceived -= OnSocketError;
            }
        }
        catch (Exception ex)
        {
            ValheimRandomizer.Log?.LogWarning("Disconnect unhook failed: " + ex.Message);
        }

        if (!closeSocket || old.Socket == null || !old.Socket.Connected) return;
        try
        {
            old.Socket.DisconnectAsync().ContinueWith(
                t => ValheimRandomizer.Log?.LogWarning("Disconnect failed: " + t.Exception.GetBaseException().Message),
                TaskContinuationOptions.OnlyOnFaulted);
        }
        catch (Exception ex)
        {
            ValheimRandomizer.Log?.LogWarning("Disconnect failed: " + ex.Message);
        }
    }

    static void OnSocketClosed(string reason)
    {
        LoseConnection(string.IsNullOrWhiteSpace(reason)
            ? "Archipelago server closed the connection. Reconnect to send checks."
            : "Archipelago server closed the connection: " + reason.Trim() + ". Reconnect to send checks.");
    }

    static void OnSocketError(Exception exception, string message)
    {
        if (!IsDeadSocket(exception) && SocketIsUsable(session?.Socket))
        {
            ValheimRandomizer.Log?.LogWarning("Archipelago error: " + (string.IsNullOrEmpty(message) ? exception?.Message : message));
            return;
        }
        LoseConnection("Archipelago connection lost. Reconnect to send checks.");
    }

    static bool IsDeadSocket(Exception exception)
    {
        for (var current = exception; current != null; current = current.InnerException)
        {
            if (current is ArchipelagoSocketClosedException || current is WebSocketException) return true;
        }
        return false;
    }

    static FieldInfo socketField;

    static bool SocketIsUsable(IArchipelagoSocketHelper socket)
    {
        if (socket == null) return false;
        try
        {
            if (socketField == null) socketField = FindSocketField(socket.GetType());
            if (socketField?.GetValue(socket) is WebSocket webSocket)
                return webSocket.State == WebSocketState.Open;
        }
        catch (Exception ex)
        {
            ValheimRandomizer.Log?.LogWarning("Socket state check failed: " + ex.Message);
        }
        return socket.Connected;
    }

    static FieldInfo FindSocketField(Type type)
    {
        while (type != null)
        {
            var field = type.GetField("Socket", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            if (field != null) return field;
            type = type.BaseType;
        }
        return null;
    }

    public static void PublishResearchCosts()
    {
        if (!IsConnected || session == null) return;
        var info = session.ConnectionInfo;
        string key = "valheim_costs_" + info.Team.ToString(CultureInfo.InvariantCulture)
            + "_" + info.Slot.ToString(CultureInfo.InvariantCulture);
        session.DataStorage[key] = ValheimRandomizer.ActiveResearchCosts == ValheimRandomizer.ResearchCostMode.Halved
            ? "halved"
            : "default";
    }

    public static void PublishPity(JObject payload)
    {
        if (!IsConnected || session == null || payload == null) return;
        var info = session.ConnectionInfo;
        string key = "valheim_pity_" + info.Team.ToString(CultureInfo.InvariantCulture)
            + "_" + info.Slot.ToString(CultureInfo.InvariantCulture);
        session.DataStorage[key] = payload.ToString(Newtonsoft.Json.Formatting.None);
    }

    public static void Pump()
    {
        string notice;
        lock (noticeLock)
        {
            if (pendingNotice == null || MessageHud.instance == null) return;
            notice = pendingNotice;
            pendingNotice = null;
        }
        MessageHud.instance.ShowMessage(MessageHud.MessageType.Center, notice);
        ValheimRandomizer.RevealEligibleRecipes();
    }

    static void ResolveDropChecks(LoginResult result)
    {
        bool slotOn = ReadSlotBool(result, "drop_checks");
        bool gatherLocations = SeedHasGatherLocations();
        if (slotOn || gatherLocations)
        {
            DropChecksEnabled = true;
            dropChecksResolved = true;
            ValheimRandomizer.Log?.LogInfo(slotOn
                ? "Drop checks on from slot data."
                : "Drop checks on because this seed has Gather locations.");
            return;
        }

        if (session?.Locations?.AllLocations != null && session.Locations.AllLocations.Count > 0)
        {
            DropChecksEnabled = false;
            dropChecksResolved = true;
            ValheimRandomizer.Log?.LogInfo("Drop checks off.");
        }
    }

    static void ResolveBossDrops(LoginResult result)
    {
        bool slotOn = ReadSlotBool(result, "boss_drops");
        if (slotOn || SeedHasBossLocations())
        {
            BossDropsEnabled = true;
            ValheimRandomizer.Log?.LogInfo(slotOn
                ? "Boss drops on from slot data."
                : "Boss drops on because this seed has more than one boss location.");
            return;
        }
        BossDropsEnabled = false;
        ValheimRandomizer.Log?.LogInfo("Boss drops off. This seed still drops them from the boss.");
    }

    static bool SeedHasBossLocations()
    {
        int found = 0;
        foreach (var boss in ValheimRandomizer.BossDrops)
        {
            try
            {
                if (session.Locations.GetLocationIdFromName("Valheim", boss.locationName) > 0)
                    found++;
            }
            catch
            {
                return false;
            }
            if (found >= 2) return true;
        }
        return false;
    }

    public static void EnsureDropChecksResolved()
    {
        if (dropChecksResolved || session == null) return;
        if (SeedHasGatherLocations())
        {
            DropChecksEnabled = true;
            dropChecksResolved = true;
            ValheimRandomizer.Log?.LogInfo("Drop checks on because this seed has Gather locations.");
            return;
        }
        if (session.Locations?.AllLocations != null && session.Locations.AllLocations.Count > 0)
        {
            DropChecksEnabled = false;
            dropChecksResolved = true;
            ValheimRandomizer.Log?.LogInfo("Drop checks off.");
        }
    }

    static bool SeedHasGatherLocations()
    {
        var locations = session?.Locations?.AllLocations;
        if (locations == null) return false;
        foreach (long id in locations)
        {
            string name = session.Locations.GetLocationNameFromId(id, "Valheim");
            if (!string.IsNullOrEmpty(name) && name.StartsWith("Gather: ", StringComparison.Ordinal))
                return true;
        }
        return false;
    }

    static bool successSlotData(LoginResult result, out Dictionary<string, object> slotData)
    {
        slotData = null;
        if (!(result is LoginSuccessful success) || success.SlotData == null) return false;
        slotData = success.SlotData;
        return true;
    }

    static bool ReadSlotBool(LoginResult result, string key)
    {
        if (!TrySlotValue(result, key, out var raw)) return false;
        if (TryCoerceBool(raw, out var flag)) return flag;
        ValheimRandomizer.Log?.LogWarning($"Slot data '{key}' was {raw.GetType().Name} '{raw}' and was not read as on.");
        return false;
    }

    static bool TryCoerceBool(object raw, out bool flag)
    {
        flag = false;
        if (raw == null) return false;
        if (raw is bool boxed)
        {
            flag = boxed;
            return true;
        }
        if (raw is string text)
        {
            if (bool.TryParse(text, out flag)) return true;
            if (int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out var number))
            {
                flag = number != 0;
                return true;
            }
            if (text.Equals("yes", StringComparison.OrdinalIgnoreCase))
            {
                flag = true;
                return true;
            }
            return false;
        }
        var valueProperty = raw.GetType().GetProperty("Value");
        if (valueProperty != null && valueProperty.PropertyType == typeof(object))
        {
            var inner = valueProperty.GetValue(raw);
            if (inner != null && !ReferenceEquals(inner, raw))
                return TryCoerceBool(inner, out flag);
        }
        try
        {
            flag = Convert.ToInt64(raw, CultureInfo.InvariantCulture) != 0;
            return true;
        }
        catch
        {
            return false;
        }
    }

    static void ApplyGoal(LoginResult result)
    {
        goalDefeatKey = DefaultGoalDefeatKey;
        goalLocationName = DefaultGoalLocationName;

        string key = ReadSlotString(result, "goal_key");
        string location = ReadSlotString(result, "goal_location");
        if (IsGoalKey(key) && IsGoalLocation(location))
        {
            goalDefeatKey = key;
            goalLocationName = location;
        }

        ValheimRandomizer.Log?.LogInfo("Goal is " + goalLocationName + " (" + goalDefeatKey + ").");
    }

    static string ReadSlotString(LoginResult result, string key)
    {
        if (!TrySlotValue(result, key, out var raw)) return null;
        if (raw is string text) return text.Trim();
        try
        {
            return Convert.ToString(raw, CultureInfo.InvariantCulture)?.Trim();
        }
        catch
        {
            return null;
        }
    }

    static bool IsGoalKey(string key)
    {
        if (string.IsNullOrEmpty(key) || key.Length > 64) return false;
        foreach (char c in key)
        {
            if (c >= 'a' && c <= 'z') continue;
            if (c >= '0' && c <= '9') continue;
            if (c == '_') continue;
            return false;
        }
        return true;
    }

    static bool IsGoalLocation(string name)
    {
        if (string.IsNullOrWhiteSpace(name) || name.Length > 80) return false;
        return name.IndexOf('\n') < 0 && name.IndexOf('\r') < 0;
    }

    static int? ReadSlotInt(LoginResult result, string key)
    {
        if (!TrySlotValue(result, key, out var raw)) return null;
        if (raw is string text)
        {
            text = text.Trim();
            if (int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out var parsed)) return parsed;
            if (text.Equals("default", StringComparison.OrdinalIgnoreCase)) return 0;
            if (text.Equals("tier", StringComparison.OrdinalIgnoreCase)) return 1;
            if (text.Equals("materials", StringComparison.OrdinalIgnoreCase) || text.Equals("mats", StringComparison.OrdinalIgnoreCase)) return 2;
            if (text.Equals("natural", StringComparison.OrdinalIgnoreCase)) return 3;
            return null;
        }
        try
        {
            return Convert.ToInt32(raw, CultureInfo.InvariantCulture);
        }
        catch
        {
            return null;
        }
    }

    static bool TrySlotValue(LoginResult result, string key, out object raw)
    {
        raw = null;
        if (!(result is LoginSuccessful success) || success.SlotData == null) return false;
        return success.SlotData.TryGetValue(key, out raw) && raw != null;
    }

    public static void SendLocation(string researchId)
    {
        if (!ValheimRandomizer.randomized.Value) return;
        if (!WorldLoaded()) return;
        if (string.IsNullOrWhiteSpace(researchId)) return;
        if (researchId.IndexOf(' ') >= 0)
        {
            ValheimRandomizer.Log.LogWarning("Refusing location key with a space: " + researchId);
            return;
        }

        if (!ValheimRandomizer.researchToArchipelago.TryGetValue(researchId, out var locationName))
        {
            ValheimRandomizer.Log.LogWarning("No Archipelago name for research " + researchId);
            return;
        }

        ValheimRandomizer.Log.LogInfo("Queue location " + locationName);
        if (HasGlobal("ap_loc_sent_" + researchId)) return;
        if (HasGlobal("ap_loc_pending_" + researchId)) return;

        SetGlobal("ap_loc_pending_" + researchId);
        TryFlushPendingLocations();
    }

    public static void SendGoal()
    {
        if (!connected || session == null) return;
        if (!ValheimRandomizer.randomized.Value) return;
        if (!WorldLoaded()) return;
        if (HasGlobal("ap_goal_sent") || HasGlobal("ap_goal_pending")) return;

        ValheimRandomizer.Log.LogInfo("Queue goal " + goalLocationName);
        SetGlobal("ap_goal_pending");
        TryFlushPendingLocations();
    }

    public static void SendDropLocation(string itemID, string locationName)
    {
        if (!DropChecksEnabled || !ValheimRandomizer.randomized.Value) return;
        if (!WorldLoaded()) return;
        if (string.IsNullOrWhiteSpace(itemID)) return;
        if (HasGlobal($"ap_drop_sent_{itemID}")) return;
        if (HasGlobal($"ap_drop_pending_{itemID}")) return;

        ValheimRandomizer.Log.LogInfo("Queue drop location " + locationName);
        SetGlobal($"ap_drop_pending_{itemID}");
        TryFlushPendingLocations();
    }

    private static void OnApItemReceived(ReceivedItemsHelper helper)
    {
        if (!WorldLoaded()) return;
        while (true)
        {
            var item = helper.DequeueItem();
            if (item == null) break;

            ApplyReceivedItem(item.ItemName);
        }
    }

    static List<string> gottenItems = new List<string>();
    static readonly HashSet<string> warnedMissingDrops = new HashSet<string>();
    static void TryGetAllItems()
    {
        if (!WorldLoaded()) return;

        foreach (var item in session.Items.AllItemsReceived)
        {
            ApplyReceivedItem(item.ItemName);
        }
    }

    static void ApplyReceivedItem(string name)
    {
        if (string.IsNullOrEmpty(name)) return;
        if (gottenItems.Contains(name)) return;

        if (ValheimRandomizer.archipelagoToResearch.TryGetValue(name, out var researchId))
        {
            gottenItems.Add(name);
            ValheimRandomizer.DoUnlockResearch(researchId);
            return;
        }

        if (name == GoalItemName)
        {
            gottenItems.Add(name);
            return;
        }

        if (name.StartsWith("Gather: ", StringComparison.Ordinal))
        {
            if (!ValheimRandomizer.dropByLocationName.TryGetValue(name, out var drop)) return;
            string grantedKey = "ap_gather_got_" + drop.itemID;
            if (HasGlobal(grantedKey))
            {
                gottenItems.Add(name);
                return;
            }
            if (ValheimRandomizer.GrantDropBundle(drop.itemID, drop.amount))
            {
                gottenItems.Add(name);
                SetGlobal(grantedKey);
            }
            return;
        }

        if (ValheimRandomizer.bossByItemName.TryGetValue(name, out var bossDrop))
        {
            string grantedKey = "ap_boss_got_" + bossDrop.itemID;
            if (HasGlobal(grantedKey))
            {
                gottenItems.Add(name);
                return;
            }
            int amount = ValheimRandomizer.BossGrantAmount(bossDrop);
            if (ValheimRandomizer.GrantDropBundle(bossDrop.itemID, amount))
            {
                gottenItems.Add(name);
                SetGlobal(grantedKey);
            }
            return;
        }

        gottenItems.Add(name);
        ValheimRandomizer.Log.LogWarning(
            $"Received AP item '{name}' but no research mapping was found.");
    }

    public static void TryFlushPendingLocations()
    {
        if (!ReadyToSend()) return;
        if (!SocketIsUsable(session.Socket))
        {
            LoseConnection("Archipelago connection lost. Reconnect to send checks.");
            return;
        }
        if (!WorldLoaded()) return;
        EnsureDropChecksResolved();
        TryGetAllItems();
        QueueBossKills();
        QueueGoalIfBossDown();

        var researchIds = new List<long>();
        var researchKeys = new List<string>();
        var dropIds = new List<long>();
        var dropKeys = new List<string>();
        var bossIds = new List<long>();
        var bossKeys = new List<string>();
        string[] keys;
        try
        {
            keys = ZoneSystem.instance.GetGlobalKeys().ToArray();
        }
        catch (Exception ex)
        {
            ValheimRandomizer.Log?.LogWarning("Pending location scan failed: " + ex.Message);
            return;
        }

        foreach (var key in keys)
        {
            if (key.StartsWith("ap_pending:", StringComparison.Ordinal) || key.StartsWith("ap_sent:", StringComparison.Ordinal))
            {
                RemoveGlobal(key);
                if (warnedMissingDrops.Add("legacy-spaced-keys"))
                {
                    ValheimRandomizer.Log.LogWarning("Cleared old spaced Archipelago keys. Those checks were not reliable and will not be resent.");
                }
                continue;
            }

            const string prefix = "ap_loc_pending_";
            if (!key.StartsWith(prefix, StringComparison.Ordinal)) continue;

            var researchId = key.Substring(prefix.Length);
            if (string.IsNullOrWhiteSpace(researchId)) continue;
            if (HasGlobal("ap_loc_sent_" + researchId)) continue;
            if (!ValheimRandomizer.researchToArchipelago.TryGetValue(researchId, out var locationName)) continue;

            long id = LookupLocationId(locationName);
            if (id <= 0) continue;
            researchIds.Add(id);
            researchKeys.Add(researchId);
        }

        bool sendGoal = HasGlobal("ap_goal_pending") && !HasGlobal("ap_goal_sent");
        long goalId = 0;
        if (sendGoal)
        {
            goalId = LookupLocationId(goalLocationName,
                $"Goal location '{goalLocationName}' is not in this seed. Sending goal status anyway.");
        }

        foreach (var key in keys)
        {
            const string prefix = "ap_drop_pending_";
            if (!key.StartsWith(prefix, StringComparison.Ordinal)) continue;

            var itemID = key.Substring(prefix.Length);
            if (!ValheimRandomizer.dropByItemID.TryGetValue(itemID, out var drop)) continue;
            if (HasGlobal($"ap_drop_sent_{itemID}")) continue;

            long id = LookupLocationId(drop.locationName);
            if (id <= 0) continue;
            dropIds.Add(id);
            dropKeys.Add(itemID);
        }

        if (BossDropsEnabled)
        {
            foreach (var key in keys)
            {
                const string prefix = "ap_boss_pending_";
                if (!key.StartsWith(prefix, StringComparison.Ordinal)) continue;
                var defeatKey = key.Substring(prefix.Length);
                if (!ValheimRandomizer.bossByDefeatKey.TryGetValue(defeatKey, out var boss)) continue;
                if (HasGlobal("ap_boss_sent_" + defeatKey)) continue;
                long id = LookupLocationId(boss.locationName);
                if (id <= 0) continue;
                bossIds.Add(id);
                bossKeys.Add(defeatKey);
            }
        }

        if (researchIds.Count == 0 && dropIds.Count == 0 && bossIds.Count == 0 && !sendGoal) return;

        var captured = session;
        var researchToMark = researchKeys.ToArray();
        var dropsToMark = dropKeys.ToArray();
        var bossesToMark = bossKeys.ToArray();
        var researchNames = researchIds.Count;
        var dropNames = dropIds.Count;
        var bossNames = bossIds.Count;
        var goalName = goalLocationName;
        var locationIds = researchIds.Concat(dropIds).Concat(bossIds).ToArray();
        int generation = sendGeneration;
        inflightStartedUtc = DateTime.UtcNow;
        inflightSuccess = () =>
        {
            if (generation != sendGeneration) return;
            for (int i = 0; i < researchToMark.Length; i++)
            {
                SetGlobal("ap_loc_sent_" + researchToMark[i]);
                RemoveGlobal("ap_loc_pending_" + researchToMark[i]);
            }
            if (researchNames > 0)
                ValheimRandomizer.Log?.LogInfo("Unlocked " + researchNames + " location(s).");
            for (int i = 0; i < dropsToMark.Length; i++)
            {
                SetGlobal("ap_drop_sent_" + dropsToMark[i]);
                RemoveGlobal("ap_drop_pending_" + dropsToMark[i]);
            }
            if (dropNames > 0)
                ValheimRandomizer.Log?.LogInfo("Unlocked " + dropNames + " drop location(s).");
            for (int i = 0; i < bossesToMark.Length; i++)
            {
                SetGlobal("ap_boss_sent_" + bossesToMark[i]);
                RemoveGlobal("ap_boss_pending_" + bossesToMark[i]);
            }
            if (bossNames > 0)
                ValheimRandomizer.Log?.LogInfo("Unlocked " + bossNames + " boss location(s).");
            if (sendGoal)
            {
                SetGlobal("ap_goal_sent");
                RemoveGlobal("ap_goal_pending");
                ValheimRandomizer.Log?.LogInfo("Goal sent: " + goalName);
            }
        };
        inflight = Task.Run(() => SendPending(captured, locationIds, sendGoal, goalId));
    }

    static long LookupLocationId(string locationName, string missingWarning = null)
    {
        try
        {
            var id = session.Locations.GetLocationIdFromName("Valheim", locationName);
            if (id > 0) return id;
            if (warnedMissingDrops.Add(locationName))
            {
                ValheimRandomizer.Log.LogWarning(missingWarning
                    ?? $"Location '{locationName}' is not in this seed.");
            }
        }
        catch (Exception ex)
        {
            ValheimRandomizer.Log.LogWarning($"AP location lookup failed for '{locationName}'. Error: {ex.Message}");
        }
        return 0;
    }

    static void SendPending(ArchipelagoSession target, long[] locationIds, bool sendGoal, long goalId)
    {
        if (locationIds.Length > 0)
            target.Locations.CompleteLocationChecks(locationIds);
        if (!sendGoal) return;
        if (goalId > 0)
            target.Locations.CompleteLocationChecks(goalId);
        target.SetGoalAchieved();
    }

    static bool ReadyToSend()
    {
        var task = inflight;
        if (task == null) return connected && session != null;
        if (!task.IsCompleted)
        {
            if (DateTime.UtcNow - inflightStartedUtc > SendTimeout)
                LoseConnection("Archipelago stopped answering. Reconnect to send checks.");
            return false;
        }

        if (!ReferenceEquals(inflight, task)) return connected && session != null;
        var success = inflightSuccess;
        inflight = null;
        inflightSuccess = null;
        if (task.IsFaulted || task.IsCanceled)
        {
            string detail = task.Exception?.GetBaseException()?.Message;
            LoseConnection(string.IsNullOrEmpty(detail)
                ? "Archipelago connection lost. Reconnect to send checks."
                : "Archipelago connection lost. Reconnect to send checks. " + detail);
            return false;
        }

        try
        {
            success?.Invoke();
        }
        catch (Exception ex)
        {
            ValheimRandomizer.Log?.LogWarning("Saving sent checks failed: " + ex.Message);
        }
        return connected && session != null;
    }

    private static bool WorldLoaded()
        => ZoneSystem.instance != null && Player.m_localPlayer != null; // simple & reliable

    private static bool HasGlobal(string k)
        => ZoneSystem.instance != null && ZoneSystem.instance.GetGlobalKey(k);

    private static void SetGlobal(string k)
    {
        if (ZoneSystem.instance == null) return;
        ZoneSystem.instance.SetGlobalKey(k);
    }

    private static void RemoveGlobal(string k)
    {
        if (ZoneSystem.instance == null) return;
        ZoneSystem.instance.RemoveGlobalKey(k);
    }

    static void QueueBossKills()
    {
        if (!BossDropsEnabled || !ValheimRandomizer.randomized.Value) return;
        foreach (var boss in ValheimRandomizer.BossDrops)
        {
            if (!HasGlobal(boss.defeatKey)) continue;
            if (HasGlobal("ap_boss_sent_" + boss.defeatKey) || HasGlobal("ap_boss_pending_" + boss.defeatKey)) continue;
            ValheimRandomizer.Log?.LogInfo("Queue boss location " + boss.locationName);
            SetGlobal("ap_boss_pending_" + boss.defeatKey);
        }
    }

    static void QueueGoalIfBossDown()
    {
        if (!ValheimRandomizer.randomized.Value) return;
        if (HasGlobal("ap_goal_sent") || HasGlobal("ap_goal_pending")) return;
        if (!HasGlobal(goalDefeatKey)) return;

        SetGlobal("ap_goal_pending");
    }

    public static void CompleteGame()
    {
        if (!connected || session == null) return;
        if (!HasGlobal("ap_goal_sent") && !HasGlobal("ap_goal_pending"))
            SetGlobal("ap_goal_pending");
        TryFlushPendingLocations();
    }
}
