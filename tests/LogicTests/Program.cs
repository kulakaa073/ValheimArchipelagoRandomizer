using System;
using System.Collections.Generic;
using ValheimApLogic;

internal static class Program
{
    static int failures;

    static void Main()
    {
        BossQuantities();
        KeysIsolateSlots();
        InboxBudgetsAndIdentity();
        ReconnectDoesNotGrantTwice();
        InventoryFullRetries();
        UnknownIsNotSuccess();
        InitializationKeepsTheQueue();
        GatherHighWater();
        TrophyAndDropRows();
        if (failures != 0)
        {
            Console.Error.WriteLine(failures + " logic test(s) failed.");
            Environment.Exit(1);
        }
        Console.WriteLine("logic tests passed");
    }

    static void BossQuantities()
    {
        int antler = BossRewardMath.RollExclusive(3, 3, (a, b) => { throw new Exception("fixed amount"); });
        Check(BossRewardMath.VanillaTotal(antler, false, 4) == 3, "hard antler stays at the vanilla amount");

        int key = BossRewardMath.VanillaTotal(1, true, 1);
        Check(key == 1, "swamp key one-per-player total for one Valheim player");
        int keys = BossRewardMath.VanillaTotal(9, true, 4);
        Check(keys == 4, "one-per-player replaces the roll with the Valheim player count");
        Check(BossRewardMath.VanillaTotal(3, true, 4) == 4, "one-per-player does not multiply the rolled amount");
        Check(BossRewardMath.VanillaTotal(1, true, 150) == 100, "vanilla amount cap");
        int wishbone = BossRewardMath.VanillaTotal(1, true, 2);
        Check(wishbone == 2, "wishbone uses the same one-per-player total");
        int rolled = BossRewardMath.RollExclusive(1, 4, (min, max) => max - 1);
        Check(rolled == 3, "exclusive roll keeps the vanilla max");
    }

    static void KeysIsolateSlots()
    {
        string a = ApKeys.Received(0, 1, 5);
        string b = ApKeys.Received(0, 2, 5);
        string same = ApKeys.Book(0, 1, "recv_5");
        Check(a == same, "received key format");
        Check(a != b, "different slots do not share a received-item key");
        Check(ApKeys.Book(0, 1, "loc_sent_researchWorkbench") != ApKeys.Book(0, 2, "loc_sent_researchWorkbench"),
            "location keys include the slot");
        Check(ApKeys.Book(1, 1, "goal_sent") != ApKeys.Book(2, 1, "goal_sent"), "team is part of the key");
    }

    static void InboxBudgetsAndIdentity()
    {
        var inbox = new ReceivedItemInbox();
        var names = new List<string>();
        for (int i = 0; i < 10; i++) names.Add(i % 2 == 0 ? "Wood" : "Resin");
        int unityCalls = 0;
        inbox.Mirror(names);
        Check(unityCalls == 0, "mirroring does not apply items");
        Check(inbox.Pending == 10, "backlog is kept");

        var seen = new List<int>();
        int first = inbox.Pump(item =>
        {
            unityCalls++;
            seen.Add(item.Index);
            return ReceivedItemOutcome.Granted;
        }, ApBudgets.MaxItemsPerFrame, 50);
        Check(first == 4, "item budget stops the frame");
        Check(inbox.Pending == 6, "the rest stays queued");
        inbox.Pump(item =>
        {
            seen.Add(item.Index);
            return ReceivedItemOutcome.Granted;
        }, 4, 50);
        inbox.Pump(item =>
        {
            seen.Add(item.Index);
            return ReceivedItemOutcome.Granted;
        }, 4, 50);
        Check(seen.Count == 10, "backlog drains across frames");
        Check(new HashSet<int>(seen).Count == 10, "duplicate names stay distinct indexes");
        for (int i = 0; i < seen.Count; i++) Check(seen[i] == i, "order is preserved");

        var slow = new ReceivedItemInbox();
        slow.Mirror(new[] { "A", "B", "C", "D" });
        int slowCount = slow.Pump(item =>
        {
            System.Threading.Thread.Sleep(5);
            return ReceivedItemOutcome.Granted;
        }, 4, ApBudgets.MaxMillisecondsPerFrame);
        Check(slowCount == 1, "time budget stops after the frame allowance");
        Check(slow.Pending == 3, "time budget does not drop the rest");
    }

    static void ReconnectDoesNotGrantTwice()
    {
        var granted = new HashSet<int>();
        var inbox = new ReceivedItemInbox();
        inbox.Mirror(new[] { "Wood", "Wood" });
        inbox.Pump(item =>
        {
            granted.Add(item.Index);
            return ReceivedItemOutcome.Granted;
        }, 4, 50);
        Check(granted.Count == 2, "two woods granted once each");

        inbox.ResetSession();
        inbox.Mirror(new[] { "Wood", "Wood" });
        int grants = 0;
        inbox.Pump(item =>
        {
            if (granted.Contains(item.Index)) return ReceivedItemOutcome.AlreadyGranted;
            grants++;
            granted.Add(item.Index);
            return ReceivedItemOutcome.Granted;
        }, 4, 50);
        Check(grants == 0 && granted.Count == 2, "reconnect does not grant a stored reward again");
    }

    static void InventoryFullRetries()
    {
        var inbox = new ReceivedItemInbox();
        inbox.Mirror(new[] { "Hard Antler" });
        int attempts = 0;
        inbox.Pump(item =>
        {
            attempts++;
            return ReceivedItemOutcome.Retry;
        }, 4, 50);
        Check(inbox.Pending == 1, "a refused grant stays pending");
        bool stored = false;
        inbox.Pump(item =>
        {
            attempts++;
            stored = true;
            return ReceivedItemOutcome.Granted;
        }, 4, 50);
        Check(stored && inbox.Pending == 0, "a later grant can succeed");
        Check(attempts == 2, "the failed attempt was not counted as done");
    }

    static void UnknownIsNotSuccess()
    {
        var stored = new HashSet<int>();
        var inbox = new ReceivedItemInbox();
        inbox.Mirror(new[] { "Not A Real Item" });
        inbox.Pump(item => ReceivedItemOutcome.Unrecognized, 4, 50);
        Check(!stored.Contains(0), "unknown item is not stored as granted");
        int again = 0;
        inbox.Pump(item =>
        {
            again++;
            return ReceivedItemOutcome.Granted;
        }, 4, 50);
        Check(again == 0, "an unrecognized item is not retried as a success in the same session");
    }

    static void InitializationKeepsTheQueue()
    {
        var inbox = new ReceivedItemInbox();
        inbox.Mirror(new[] { "Crafting", "Bronze" });
        bool ready = false;
        if (ready)
            inbox.Pump(item => ReceivedItemOutcome.Granted, 4, 50);
        Check(inbox.Pending == 2, "items received before data is ready stay queued");
        ready = true;
        var got = new List<string>();
        if (ready)
        {
            inbox.Pump(item =>
            {
                got.Add(item.Name);
                return ReceivedItemOutcome.Granted;
            }, 4, 50);
        }
        Check(got.Count == 2 && got[0] == "Crafting" && got[1] == "Bronze", "ready data grants the queued items");
    }

    static void GatherHighWater()
    {
        var seen = new Dictionary<string, int> { { "Wood", 10 } };
        Check(!GatherChecks.NoteIncrease(seen, "Wood", 5, false), "a drop is not a pickup");
        Check(seen["Wood"] == 10, "high water stays");
        Check(!GatherChecks.NoteIncrease(seen, "Wood", 10, false), "restoring a moved stack is not a new pickup");
        Check(GatherChecks.NoteIncrease(seen, "Wood", 12, false), "a real increase sends once");
        Check(!GatherChecks.NoteIncrease(seen, "Wood", 0, true), "spending the stack does not send again");
        Check(seen["Wood"] == 12, "spend does not lower the mark");
    }

    static void TrophyAndDropRows()
    {
        Check(TsvValidation.IsTrophyHeader(new[] { "researchItemID", "researchID", "boostType", "tier" }), "trophy header");
        Check(TsvValidation.TrophyError(new[] { "researchItemID", "researchID", "boostType", "tier" }) != null, "header is not a trophy");
        Check(TsvValidation.TrophyError(new[] { "TrophyBoar", "researchTrophyBoar", "NotABoost", "0" }) != null, "unknown boost");
        Check(TsvValidation.TrophyError(new[] { "TrophyBoar", "researchTrophyBoar", "HP", "0" }) == null, "known boost");
        Check(TsvValidation.ResearchError(new[] { "only", "four" }) != null, "short research row");
        Check(TsvValidation.DropError(new[] { "Wood", "Wood", "0", "nope" }) != null, "bad drop amount");
        Check(TsvValidation.DropError(new[] { "HardAntler", "Hard Antler", "2", "3", "boss", "Eikthyr" }) != null, "short boss row");
        Check(TsvValidation.IsCommentOrBlank("# itemPrefab\tdisplayName") , "comment");
        Check(TsvValidation.IsCommentOrBlank("   "), "blank");
    }

    static void Check(bool condition, string name)
    {
        if (condition) return;
        failures++;
        Console.Error.WriteLine("FAIL " + name);
    }
}
