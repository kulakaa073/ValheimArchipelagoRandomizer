using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;

namespace ValheimApLogic
{
    public enum ReceivedItemOutcome
    {
        Granted = 0,
        AlreadyGranted = 1,
        Retry = 2,
        Unrecognized = 3,
    }

    public readonly struct QueuedApItem
    {
        public readonly int Index;
        public readonly string Name;

        public QueuedApItem(int index, string name)
        {
            Index = index;
            Name = name ?? "";
        }
    }

    public static class ApBudgets
    {
        public const int MaxItemsPerFrame = 4;
        public const int MaxMillisecondsPerFrame = 2;
    }

    public static class ApKeys
    {
        public static string Book(int team, int slot, string suffix)
        {
            return "ap_" + team.ToString(CultureInfo.InvariantCulture)
                + "_" + slot.ToString(CultureInfo.InvariantCulture)
                + "_" + suffix;
        }

        public static string Received(int team, int slot, int index)
        {
            return Book(team, slot, "recv_" + index.ToString(CultureInfo.InvariantCulture));
        }
    }

    public static class BossRewardMath
    {
        public const int VanillaCap = 100;

        // UnityEngine.Random.Range(int, int) is exclusive of max and returns min when min == max.
        public static int RollExclusive(int amountMin, int amountMax, Func<int, int, int> rangeExclusive)
        {
            if (amountMax < amountMin) amountMax = amountMin;
            if (amountMin == amountMax) return amountMin;
            return rangeExclusive(amountMin, amountMax);
        }

        // CharacterDrop replaces the rolled amount when m_onePerPlayer is set.
        // playerCount is the Valheim peer count from that drop, not an Archipelago slot count.
        // The result is one bundle. It is not amount * playerCount.
        public static int VanillaTotal(int exclusiveRoll, bool onePerPlayer, int playerCount)
        {
            int amount = onePerPlayer ? playerCount : exclusiveRoll;
            if (amount > VanillaCap) amount = VanillaCap;
            return amount;
        }
    }

    public static class GatherChecks
    {
        // High-water mark. A later smaller count (a move or a spend) does not send a check.
        public static bool NoteIncrease(Dictionary<string, int> seen, string itemId, int count, bool alreadySent)
        {
            if (seen == null || string.IsNullOrEmpty(itemId) || count < 0) return false;
            int prior;
            seen.TryGetValue(itemId, out prior);
            if (count <= prior) return false;
            seen[itemId] = count;
            return !alreadySent;
        }
    }

    public static class TsvValidation
    {
        public static bool IsCommentOrBlank(string line)
        {
            if (string.IsNullOrWhiteSpace(line)) return true;
            return line.TrimStart().StartsWith("#", StringComparison.Ordinal);
        }

        public static bool IsTrophyHeader(string[] cols)
        {
            return cols != null
                && cols.Length >= 3
                && cols[0] == "researchItemID"
                && cols[1] == "researchID"
                && cols[2] == "boostType";
        }

        public static bool KnownBoost(string name)
        {
            switch (name)
            {
                case "Load":
                case "HP":
                case "Stamina":
                case "Eitr":
                case "HPRegen":
                case "StaminaRegen":
                case "Attack":
                case "Defense":
                case "Adrenaline":
                case "EitrRegen":
                case "Speed":
                case "SkillXp":
                    return true;
                default:
                    return false;
            }
        }

        public static string TrophyError(string[] cols)
        {
            if (cols == null || cols.Length < 4) return "needs 4 columns";
            if (string.IsNullOrWhiteSpace(cols[0]) || string.IsNullOrWhiteSpace(cols[1]))
                return "missing item id or research id";
            if (!KnownBoost(cols[2])) return "unknown boost type '" + cols[2] + "'";
            return null;
        }

        public static string ResearchError(string[] cols)
        {
            if (cols == null || cols.Length < 7) return "needs 7 columns";
            if (string.IsNullOrWhiteSpace(cols[1]) || string.IsNullOrWhiteSpace(cols[2]))
                return "missing id or name";
            return null;
        }

        public static string DropError(string[] cols)
        {
            if (cols == null || cols.Length < 4) return "needs 4 columns";
            if (string.IsNullOrWhiteSpace(cols[0]) || string.IsNullOrWhiteSpace(cols[1]))
                return "missing item id or name";
            int amount;
            if (!int.TryParse(cols[3], NumberStyles.Integer, CultureInfo.InvariantCulture, out amount) || amount < 1)
                return "amount must be a positive integer";
            if (cols.Length >= 5 && cols[4] == "boss" && cols.Length < 9)
                return "boss row needs 9 columns";
            return null;
        }
    }

    public sealed class ReceivedItemInbox
    {
        readonly object gate = new object();
        readonly ConcurrentQueue<QueuedApItem> inbound = new ConcurrentQueue<QueuedApItem>();
        readonly List<QueuedApItem> retry = new List<QueuedApItem>();
        readonly HashSet<int> finished = new HashSet<int>();
        int mirrored;
        int generation;

        public int Pending
        {
            get
            {
                lock (gate) return inbound.Count + retry.Count;
            }
        }

        public void ResetSession()
        {
            lock (gate)
            {
                generation++;
                while (inbound.TryDequeue(out _)) { }
                retry.Clear();
                finished.Clear();
                mirrored = 0;
            }
        }

        // Network thread. Copies new received-item indexes. Does not call gameplay code.
        public void Mirror(IReadOnlyList<string> names)
        {
            if (names == null) return;
            lock (gate)
            {
                int count = names.Count;
                if (count < mirrored) mirrored = 0;
                for (int i = mirrored; i < count; i++)
                    inbound.Enqueue(new QueuedApItem(i, names[i]));
                mirrored = count;
            }
        }

        public int Pump(Func<QueuedApItem, ReceivedItemOutcome> apply, int itemBudget, int millisecondBudget)
        {
            if (apply == null) return 0;
            if (itemBudget < 1) itemBudget = 1;
            if (millisecondBudget < 1) millisecondBudget = 1;

            int generationAtStart;
            var batch = new List<QueuedApItem>(itemBudget);
            lock (gate)
            {
                generationAtStart = generation;
                int retries = retry.Count;
                int retryCap = 1; // at most one stuck item competes with new items each frame
                while (batch.Count < itemBudget)
                {
                    QueuedApItem next;
                    if (retries > 0 && retryCap > 0)
                    {
                        next = retry[0];
                        retry.RemoveAt(0);
                        retries--;
                        retryCap--;
                    }
                    else if (!inbound.TryDequeue(out next))
                    {
                        if (retries == 0) break;
                        next = retry[0];
                        retry.RemoveAt(0);
                        retries--;
                    }
                    batch.Add(next);
                }
            }

            int processed = 0;
            var elapsed = Stopwatch.StartNew();
            for (int n = 0; n < batch.Count; n++)
            {
                if (processed >= itemBudget || elapsed.ElapsedMilliseconds >= millisecondBudget)
                {
                    lock (gate)
                    {
                        if (generation != generationAtStart) return processed;
                        for (int i = batch.Count - 1; i >= n; i--)
                            retry.Insert(0, batch[i]);
                    }
                    return processed;
                }

                var item = batch[n];
                bool skip;
                lock (gate)
                {
                    if (generation != generationAtStart) return processed;
                    skip = finished.Contains(item.Index);
                }
                if (skip)
                {
                    processed++;
                    continue;
                }

                ReceivedItemOutcome outcome;
                try
                {
                    outcome = apply(item);
                }
                catch (Exception)
                {
                    outcome = ReceivedItemOutcome.Retry;
                }

                lock (gate)
                {
                    if (generation != generationAtStart) return processed;
                    if (outcome == ReceivedItemOutcome.Retry)
                        retry.Add(item);
                    else
                        finished.Add(item.Index);
                }
                processed++;
            }
            return processed;
        }
    }
}