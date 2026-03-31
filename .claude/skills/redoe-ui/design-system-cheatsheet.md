# Redoe OS — Design System Cheatsheet

> Zero prose. Copy-paste ready. Full spec: `design-system.md`.

---

## Tokens (CSS variables in globals.css)

### Brand
```
--color-redoe-navy    #1F4E79   Primary brand, headers, CTAs
--color-redoe-blue    #2E75B6   Secondary actions, links
--color-redoe-light   #D6E4F0   Light backgrounds, hovers
```

### Status (always: color + icon + text)
```
--color-status-healthy   #22C55E   CircleCheck       Active, on track
--color-status-warning   #F59E0B   AlertTriangle     At risk, approaching deadline
--color-status-critical  #EF4444   XCircle           Blocked, over budget
--color-status-complete  #10B981   CheckCircle2      Shipped, done
--color-status-neutral   #94A3B8   Clock             Pending, on hold
--color-status-info      #38BDF8   Info              Informational
```

### Entity (canonical — never deviate)
```
Redoe Windsor   #2563EB   --color-entity-redoe-windsor
Redoe Hunan     #7C3AED   --color-entity-redoe-hunan
PES             #EA580C   --color-entity-pes
Pangeo Corp     #6B7280   --color-entity-pangeo
GTA             #0891B2   --color-entity-gta
IPO             #DB2777   --color-entity-ipo
```

### Depth (Canvas > Surface > Layer)
```
--canvas          off-white    Root page background
--surface-1       white        Cards, sidebar, content areas
--surface-2       slight gray  Secondary panels
--layer-1         light gray   Depth within surfaces
--layer-hover     hover bg     Single consistent hover state
--layer-active    pressed bg   Active/pressed state
--layer-selected  blue tint    Selected row/item
```

### Borders (near-invisible — Linear pattern)
```
--border          default      Standard dividers
--border-subtle   barely there Sidebar edge, row separators
--border-strong   visible      Section breaks, focused inputs
```

### Text
```
--text-primary      near-black   Body text
--text-secondary    dark gray    Descriptions
--text-tertiary     medium gray  Captions
--text-placeholder  light gray   Input placeholders
--text-disabled     lighter      Disabled elements
--text-on-color     white        Text on colored backgrounds
```

### Shadows (depth via bg color — shadows only for elevated layers)
```
--shadow-xs     cards at rest (barely visible)
--shadow-sm     inputs, subtle cards
--shadow-md     dropdowns, popovers
--shadow-lg     sheets, drawers
--shadow-xl     modals
--shadow-modal  heavy modal overlay
```

### Motion
```
--duration-instant  100ms   Hover, toggle, button press
--duration-fast     150ms   Tooltips, color changes
--duration-normal   200ms   Tab switch, menu open
--duration-slow     300ms   Panel expand, accordion
--duration-layout   500ms   Modal, drawer, page transition
--ease-out          cubic-bezier(0.25, 1, 0.5, 1)     Entering elements
--ease-out-expo     cubic-bezier(0.16, 1, 0.3, 1)     Dropdowns, popovers
--ease-in-out       cubic-bezier(0.65, 0, 0.35, 1)    State toggles
```

---

## Typography

```
Font          Role                    Weights
Inter         Headings, labels, body  400, 500, 600, 700
JetBrains M.  Job IDs, KPIs, data     400, 500, 600
```

```
Name          Size    Font           Usage
display-lg    36px    Inter 700      Page titles
heading-lg    24px    Inter 600      Section headers
heading-md    20px    Inter 600      Card titles
body          13px    Inter 400      Default body (base)
body-sm       12px    Inter 400      Captions, labels
data-lg       32px    JBMono 500     KPI hero numbers
data          13px    JBMono 400     Table cells, job IDs
data-sm       12px    JBMono 400     Timestamps
caption       11px    Inter 400      Minimal labels
```

**Rules:** Max 4 sizes + 3 weights per view. Hierarchy via weight, not size.

---

## Spacing (8px grid)

```
4px    Icon-text gaps ONLY
8px    Tight padding, inline spacing
12px   Compact card padding
16px   Standard card padding, form gaps
24px   Card-to-card gaps
32px   Section separators
48px   Major section breaks
```

**Radius:** Buttons `0.5rem` | Cards `0.75rem` | Badges `9999px` (pill)

---

## Component Quick-Ref

### Status Badge
```tsx
<span className="inline-flex items-center gap-1.5 rounded-full
  px-2.5 py-0.5 text-xs font-medium
  bg-status-healthy/10 text-status-healthy border border-status-healthy/30">
  <CircleCheck className="size-3.5" />
  Active
</span>
```
Sizes: `sm` (11px, tables) | `md` (xs, default) | `lg` (sm, headers)

### KPI Card (Stripe pattern — borderless)
```tsx
<div className="bg-surface-1 rounded-xl p-4">
  <p className="text-[13px] text-muted-foreground font-medium">Revenue</p>
  <p className="text-[32px] font-mono font-semibold tracking-tight">$1.2M</p>
  <p className="text-[13px] text-muted-foreground">
    <span className="text-status-healthy">↑ 12%</span> vs last month
  </p>
</div>
```
Max 4 per row. No borders. Hero number + delta.

### Data Table Row
```tsx
<tr className="h-[44px] border-b border-subtle hover:bg-layer-hover">
  <td className="font-mono text-muted-foreground">G-8232</td>
  <td>CNC Housing</td>
  <td><StatusBadge status="active" size="sm" /></td>
  <td className="text-right font-mono tabular-nums">$45,200</td>
</tr>
```
44px rows. Mono + right-align numbers. Empty state required.

### Empty State (Linear pattern)
```tsx
<div className="flex flex-col items-center justify-center py-16 text-center">
  <Wrench className="size-12 text-muted-foreground/40 mb-4" />
  <h3 className="text-[15px] font-medium mb-1">No active jobs</h3>
  <p className="text-[13px] text-muted-foreground mb-4">
    Jobs assigned to your station will appear here.
  </p>
  <Button>+ Create Work Order</Button>
</div>
```

---

## Component Inventory (v2)

### Primitives (ui/) — 24 total
avatar, badge, button, checkbox, collapsible, command, context-menu, dialog, dropdown-menu, input, input-group, number-ticker (Magic UI), popover, progress, radio-group, scroll-area, select, separator, sheet, sidebar, skeleton, switch, table, tabs, textarea, tooltip

### Compounds (redoe/) — 17 total
```
StatusBadge, KPICard, PageHeader, EmptyState, EntityBadge, FilterBar, DataTable, ChartSection,
ConfirmationDialog, RedoeToaster/toast, ActionMenu, SearchCommand, FormField, Breadcrumbs,
DateRangePicker, StatRow, LoadingSkeleton
```

### Layouts (layouts/) — 8 total
```
ManagementLayout, DashboardPage, ListPage, DetailPage, ShopFloorLayout,
FormPage, SettingsPage, SplitView
```

### New Compound Snippets

```tsx
// Confirmation Dialog (destructive actions)
<ConfirmationDialog open={open} onOpenChange={setOpen} variant="danger"
  title="Delete Work Order?" description="This cannot be undone."
  onConfirm={handleDelete} confirmLabel="Delete" />

// Toast (feedback)
import { toast } from "@/components/redoe"
toast.success("Work order created")
toast.error("Failed to save changes")

// Action Menu (⋯ button)
<ActionMenu items={[
  { label: "Edit", icon: Pencil, onClick: edit },
  { label: "Delete", icon: Trash2, onClick: del, variant: "danger" },
]} />

// Form Field (label + input + error)
<FormField label="Job Number" required error={errors.job}>
  <Input placeholder="G-XXXX" />
</FormField>

// Search Command (Cmd+K)
<SearchCommand open={open} onOpenChange={setOpen} groups={[
  { heading: "Navigation", items: [
    { label: "Dashboard", icon: Home, onSelect: () => router.push("/") },
  ]},
]} />

// Date Range Picker
<DateRangePicker value={range} onChange={setRange} />

// Stat Row (inline stats)
<StatRow items={[
  { label: "Hours", value: "142.5h", trend: "up" },
  { label: "Budget", value: "$23,400", trend: "down" },
]} />

// Loading Skeleton
<LoadingSkeleton variant="dashboard" />
<LoadingSkeleton variant="list" />
```

---

## Layout Patterns

### Dashboard (Tier 2) — `<DashboardPage>`
KPI cards (3-4 max) → filter bar (7d/30d/MTD/YTD) → chart → table

### List Page (Tier 2) — `<ListPage>`
Page header → filter toolbar → data table → pagination

### Detail Page (Tier 2) — `<DetailPage>`
Page header + status → tabs (Overview | Details | Documents | History)

### Form Page (Tier 2) — `<FormPage>`
Page header → centered form (max-w-2xl) → sticky footer (Cancel + Submit)

### Settings Page (Tier 3) — `<SettingsPage>`
220px nav sidebar → content area (max-w-3xl) → save per section

### Split View (Tier 2) — `<SplitView>`
List panel (320px) + detail panel (flex-1). Inbox/message pattern.

### Shop Floor (Tier 1) — `<ShopFloorLayout>`
No sidebar. 56px buttons. 3 screens: Select → Act → Confirm

---

## Hard Rejects

1. Hardcoded hex in components
2. Color-only status (must: color + icon + text)
3. Bounce/wobble/elastic animations
4. Purple gradients, glassmorphism on light mode
5. Lorem ipsum or placeholder text
6. Spinners (use `.skeleton` shimmer)
7. Colored icons in nav/sidebar
8. `<select>` elements (use Command search)
9. >4 font sizes or >3 weights per view
10. >12px radius on containers
11. >7 table columns without scroll
12. >4 KPI cards per row
13. KPIs that change meaning when filters change (anchor to mental model)
14. Blue badges for "pending action" items (use amber — blue = informational)
15. Filter transitions without fade (--duration-fast minimum)
16. Nested data crammed into table cells (use Sheet detail panel)
17. Custom components that duplicate existing compounds (check Component Inventory above FIRST)
18. Writing UI without reading this cheatsheet (enforced by PostCompact hook)
19. Toggle/pill groups where inactive options are invisible (use bordered container + white active + muted inactive)

---

## Interaction Principles

### KPIs Anchor to Mental Model, Not Filters
KPI strips show the user's "right now" snapshot. When a table filter changes
the visible rows, KPIs must NOT recalculate to match the filter — they answer
"how much needs my attention?" which is always a global/current question.
Exception: dashboard-level KPIs that explicitly label their scope ("This Week").

### Filters Must Not Break the Page
When toggling filters (date range, status, department):
- Use --duration-fast (150ms) fade transition on the table body
- Keep sort order consistent (date desc → name asc) so rows don't shuffle randomly
- Show the active filter range explicitly ("Mar 24 – Mar 29") not just the pill label
- Disable forward navigation when at current period

### Sub-Data → Detail Panel, Not Inline Expansion
When a table row contains nested data (multiple tasks per shift, line items per order,
attachments per record), open a Sheet (right slide-out) on row click. Don't try to
expand inline or cram sub-tables into cells.
- Sheet width: 480px for detail views, 640px for edit-capable views
- Content: summary header → breakdown table → actions at bottom
- Row click = read-only detail. Edit button = edit mode.

### Status Indicators: Pending = Amber, Not Blue
"Pending" / "needs attention" items must use amber (--color-status-warning) not blue.
Blue reads as "informational" or "selected" — amber reads as "act on this."
Reserved: green = done/approved, red = rejected/error, amber = pending/needs action,
gray = neutral/inactive.

### Prevent Layout Shift on Filter Toggle
When a filter changes the number of visible rows, the content area height changes and
everything below it "jumps." This makes KPIs feel like they moved even when their values
are stable. Fix: set `min-h-[400px]` (or similar) on the table/list container so the
page skeleton stays the same height regardless of row count. Combine with the
--duration-fast fade transition on content swap.

### Toggle Groups: All Options Always Visible
Toggle/pill groups (status tabs, date range, department filters) must show ALL options
at ALL times. Inactive options are muted text, not invisible borders.
Pattern: bordered container `border border-[var(--border)] p-0.5 bg-muted/30`,
active = `bg-white shadow-sm text-foreground`, inactive = `text-muted-foreground`.
NEVER use individual bordered pills where inactive = transparent border on white bg.

### Approval Sub-Workflows Need Their Own Surface
When a record has approvable sub-items (break requests on a shift, line items on a PO),
don't hide approval actions as decorative badges. Give them a dedicated section in the
detail panel with explicit approve/reject buttons per item.
