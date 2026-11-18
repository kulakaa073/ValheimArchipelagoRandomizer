import json
from pathlib import Path

data = json.loads(Path(__file__).with_name("_proposed_research.json").read_text(encoding="utf-8"))


def dump(o):
    return json.dumps(o, ensure_ascii=False)


items = [{k: i[k] for k in ("name", "tier", "oldTier", "role", "cost", "oldCat")} for i in data["items"]]

template = r'''import { Callout, H1, H2, H3, Row, Select, Stack, Stat, Table, Text, TextInput, useCanvasState } from "cursor/canvas";

type Item = {
  name: string;
  tier: number;
  oldTier: number;
  role: string;
  cost: string;
  oldCat: string;
};

const ITEMS: Item[] = __ITEMS__;
const DOORS = __DOORS__;
const LABELS = __LABELS__;
const SOFT = __SOFT__;
const NOTES = __NOTES__;
const COUNTS = __COUNTS__;
const ROLES = __ROLES__;

const ROLE_ORDER: Record<string, number> = { Door: 0, SoftProg: 1, Useful: 2, Filler: 3 };

function isChanged(row: Item): boolean {
  if (row.tier !== row.oldTier) return true;
  if ((row.role === "Door" || row.role === "SoftProg") && row.oldCat !== "Progression") return true;
  if (row.oldCat === "Progression" && row.role === "Useful") return true;
  return false;
}

export default function ResearchOverhaulProposal() {
  const [query, setQuery] = useCanvasState("query", "");
  const [tier, setTier] = useCanvasState("tier", "all");
  const [role, setRole] = useCanvasState("role", "all");
  const [changedOnly, setChangedOnly] = useCanvasState("changedOnly", "all");
  const needle = query.trim().toLowerCase();

  const filtered = ITEMS.filter((row) => {
    if (tier !== "all" && String(row.tier) !== tier) return false;
    if (role !== "all" && row.role !== role) return false;
    if (changedOnly === "changed" && !isChanged(row)) return false;
    if (!needle) return true;
    return [row.name, row.role, row.cost, row.oldCat].join(" ").toLowerCase().includes(needle);
  }).sort((a, b) => a.tier - b.tier || ROLE_ORDER[a.role] - ROLE_ORDER[b.role] || a.name.localeCompare(b.name));

  const tiers = Object.keys(LABELS).map(Number).sort((a, b) => a - b);
  const activeTiers = tier === "all" ? tiers : tiers.filter((t) => String(t) === tier);

  return (
    <Stack gap={20}>
      <Stack gap={6}>
        <H1>Research overhaul v5.1 — cost retunes</H1>
        <Text tone="secondary">
          Pre-swamp/bronze costs cleared of swamp/plains mats (rows show was:). Nails+cart T3, bronze set T4, BF mist pack T10, forge prereqs rewired.
        </Text>
      </Stack>

      <Row gap={12} wrap>
        <Stat value={String(ITEMS.length)} label="Researches" />
        <Stat value={String(ROLES.Door || 0)} label="Doors" tone="info" />
        <Stat value={String(ROLES.SoftProg || 0)} label="Soft Progression" tone="warning" />
        <Stat value={String(ROLES.Useful || 0)} label="Useful" />
        <Stat value={String(ROLES.Filler || 0)} label="Filler" />
      </Row>

      <H2>Rules in this revision</H2>
      <Stack gap={6}>
        {NOTES.map((n) => (
          <Callout key={n} tone="info" title={n.slice(0, 56) + (n.length > 56 ? "…" : "")}>
            {n}
          </Callout>
        ))}
      </Stack>

      <H2>Door map</H2>
      <Table
        headers={["Into tier", "Biome", "Door items"]}
        columnAlign={["right", "left", "left"]}
        striped
        stickyHeader
        rows={tiers.filter((t) => DOORS[String(t)]).map((t) => [
          String(t),
          LABELS[String(t)],
          (DOORS[String(t)] || []).join(", "),
        ])}
      />

      <H2>Soft Progression</H2>
      <Text>{SOFT.join(" · ")}</Text>

      <H2>Full research list</H2>
      <Row gap={8} wrap align="center">
        <TextInput value={query} onChange={setQuery} placeholder="Search name / cost / role" style={{ minWidth: 240 }} />
        <Select
          value={tier}
          onChange={setTier}
          options={[{ value: "all", label: "All tiers" }, ...tiers.map((t) => ({ value: String(t), label: `T${t} · ${LABELS[String(t)]} (${COUNTS[String(t)] || 0})` }))]}
        />
        <Select
          value={role}
          onChange={setRole}
          options={[
            { value: "all", label: "All roles" },
            { value: "Door", label: "Door" },
            { value: "SoftProg", label: "Soft Progression" },
            { value: "Useful", label: "Useful" },
            { value: "Filler", label: "Filler" },
          ]}
        />
        <Select
          value={changedOnly}
          onChange={setChangedOnly}
          options={[
            { value: "all", label: "All rows" },
            { value: "changed", label: "Changed vs current only" },
          ]}
        />
      </Row>

      {activeTiers.map((t) => {
        const rows = filtered.filter((i) => i.tier === t);
        const into = DOORS[String(t)] || [];
        const emptyNote = "No researches in this tier under the current filter.";
        return (
          <Stack key={t} gap={8}>
            <H3>{`Tier ${t} — ${LABELS[String(t)]}`}</H3>
            <Text size="small" tone="secondary">
              {into.length ? `Door into this tier: ${into.join(", ")}` : "No door (bootstrap)."}
              {` · ${rows.length} researches shown`}
            </Text>
            {rows.length ? (
              <Table
                headers={["Role", "Research", "Cost", "Old tier", "Old class"]}
                columnAlign={["left", "left", "left", "right", "left"]}
                striped
                stickyHeader
                rows={rows.map((r) => [r.role, r.name, r.cost || "—", String(r.oldTier), r.oldCat])}
                rowTone={rows.map((r) =>
                  r.role === "Door" ? "info" : r.role === "SoftProg" ? "warning" : undefined
                )}
              />
            ) : (
              <Callout tone="neutral" title="Empty tier">
                {emptyNote}
              </Callout>
            )}
          </Stack>
        );
      })}
    </Stack>
  );
}
'''

tsx = (
    template.replace("__ITEMS__", dump(items))
    .replace("__DOORS__", dump(data["doors_into"]))
    .replace("__LABELS__", dump(data["tier_labels"]))
    .replace("__SOFT__", dump(data["soft"]))
    .replace("__NOTES__", dump(data["notes"]))
    .replace("__COUNTS__", dump({str(k): v for k, v in data["counts_by_tier"].items()}))
    .replace("__ROLES__", dump(data["counts_by_role"]))
)

out = Path(
    r"C:/Users/Shade/.cursor/projects/d-SteamLibrary-steamapps-common-Valheim/canvases/research-overhaul-proposal.canvas.tsx"
)
out.write_text(tsx, encoding="utf-8")
print("wrote", out, out.stat().st_size)
