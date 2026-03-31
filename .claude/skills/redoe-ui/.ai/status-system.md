# Redoe OS — Status System

> Status MUST always use color + icon + text. NEVER color alone.
> Use `StatusBadge` component when available. Otherwise follow this pattern exactly.

---

## Status Mapping

| Status | CSS Token | Background | Text/Icon Color | Icon (Lucide) | Used For |
|--------|-----------|------------|-----------------|---------------|----------|
| Active / On Track | `--color-status-healthy` | `bg-status-healthy/10` | `text-status-healthy` | `CircleCheck` | Running jobs, healthy machines, on-schedule tools |
| Warning / At Risk | `--color-status-warning` | `bg-status-warning/10` | `text-status-warning` | `AlertTriangle` | Late tools, approaching deadline, nearing threshold |
| Critical / Blocked | `--color-status-critical` | `bg-status-critical/10` | `text-status-critical` | `XCircle` | Over budget, blocked, machine down, alarm |
| Complete / Shipped | `--color-status-complete` | `bg-status-complete/10` | `text-status-complete` | `CheckCircle2` | Shipped tools, closed jobs, finished operations |
| Pending / Queued | `--color-status-neutral` | `bg-status-neutral/10` | `text-status-neutral` | `Clock` | Queued jobs, pending approval, on hold |
| Info | `--color-status-info` | `bg-status-info/10` | `text-status-info` | `Info` | Informational, neutral updates, notes |

---

## Badge Pattern (when StatusBadge component not available)

```tsx
<span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium bg-status-healthy/10 text-status-healthy border border-status-healthy/30">
  <CircleCheck className="size-3.5" />
  Active
</span>
```

### Sizes

| Size | Classes | Icon Size | Usage |
|------|---------|-----------|-------|
| `sm` | `px-2 py-0.5 text-[11px]` | `size-3` | Table cells, compact lists |
| `md` | `px-2.5 py-0.5 text-xs` | `size-3.5` | Default — cards, headers |
| `lg` | `px-3 py-1 text-sm` | `size-4` | Page headers, hero areas |

---

## Priority Mapping (for job/tool priority)

| Priority | Color | Icon (Lucide) |
|----------|-------|---------------|
| Urgent | `text-status-critical` | `AlertOctagon` |
| High | `text-orange-500` | `ArrowUp` |
| Medium | `text-status-warning` | `Minus` |
| Low | `text-status-info` | `ArrowDown` |
| None | `text-muted-foreground` | `Minus` (dimmed) |

---

## Entity Badge Pattern

| Entity | Token | Usage |
|--------|-------|-------|
| Redoe Windsor | `bg-entity-redoe-windsor/10 text-entity-redoe-windsor` | Entity filter pills, badges |
| Redoe Hunan | `bg-entity-redoe-hunan/10 text-entity-redoe-hunan` | |
| PES | `bg-entity-pes/10 text-entity-pes` | |
| Pangeo Corp | `bg-entity-pangeo/10 text-entity-pangeo` | |
| GTA | `bg-entity-gta/10 text-entity-gta` | |
| IPO | `bg-entity-ipo/10 text-entity-ipo` | |

---

## Rules

1. Background opacity is always `/10` (10%). Border opacity is `/30` (30%). Never higher.
2. Icon is same color as text (inherits via `currentColor`).
3. Icon size matches the badge size tier (see Sizes table above).
4. Status text is the human-readable label, not the enum value. "On Track" not "ON_TRACK".
5. In tables, use `sm` size. In page headers, use `lg`. Default everywhere else is `md`.
6. For inline status (not a badge), just use icon + text without the pill background.
