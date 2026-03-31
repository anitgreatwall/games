# Redoe OS — Composition Patterns

> Every page MUST match one of these patterns. Do NOT improvise page layouts.
> Components listed here may be from `components/redoe/` (compound) or `components/ui/` (shadcn).

---

## Pattern 1: List Page

Used for: Tool list, Job list, Quote list, Customer list, any tabular data view.

```
PageHeader
├── breadcrumbs: Breadcrumb (shadcn)
├── title: h1, text-heading-lg (Inter 600)
├── description: text-body text-muted-foreground (optional)
└── actions: Button group (primary action right-aligned)

FilterToolbar
├── Search: Input with SearchIcon, w-[280px]
├── Status filter: pill toggle group (All | Active | Warning | Complete)
├── Date range: DatePickerWithRange (optional)
├── View toggle: ToggleGroup (list | board) (optional)
└── Export: Button variant="outline" size="sm" (right-aligned)
    spacing: flex items-center gap-2, single horizontal line
    wrap: at lg breakpoint, stack search above filters

DataTable
├── Header row: bg-surface-2, text-body-sm font-medium text-secondary
│   ├── Sortable columns: cursor-pointer, ChevronUp/Down icon on active
│   └── Numeric headers: text-right
├── Data rows: h-[44px] min, border-b border-subtle, hover:bg-layer-hover
│   ├── ID column: font-data text-muted-foreground (link to detail)
│   ├── Text columns: text-left, truncate with title attr
│   ├── Status column: StatusBadge component
│   ├── Numeric columns: text-right-numeric
│   ├── Date columns: font-data text-muted-foreground
│   └── Actions column: DropdownMenu with MoreHorizontal trigger
├── Selected rows: bg-layer-selected
├── Bulk action bar: appears above table when rows selected
│   └── "N selected" + action buttons (Assign, Delete, Export)
└── Empty state: centered icon + heading + description + CTA button

Pagination
├── "Showing X-Y of Z results" (text-body-sm text-muted-foreground)
├── Rows per page: Select (10 | 25 | 50)
└── Page navigation: prev/next + page numbers (max 5 visible + ellipsis)
    spacing: flex items-center justify-between, mt-4
```

### Layout rules:
- Full width, single column, top to bottom
- FilterToolbar sticky at top on scroll (optional, Tier 2+ only)
- Table fills remaining height: `flex-1 overflow-auto`
- Gap between sections: `space-y-4` (16px)

---

## Pattern 2: Detail Page

Used for: Tool detail, Job detail, Work Order detail, any single-entity view.

```
PageHeader
├── Back button: Button variant="ghost" size="icon" (ArrowLeft)
├── breadcrumbs: Breadcrumb
├── title: h1 + StatusBadge inline
├── description: entity subtitle (customer, program)
└── actions: Button group (Edit, Export, Delete with DropdownMenu)

TabsContainer (shadcn Tabs)
├── TabsList: border-b border-subtle (not boxed)
│   ├── Tab: Overview
│   ├── Tab: Details
│   ├── Tab: Documents
│   └── Tab: History
│
├── TabPanel: Overview
│   ├── KPI card row: grid grid-cols-2 lg:grid-cols-4 gap-4
│   │   └── KPICard × 4 (label, value, delta, trend)
│   ├── Timeline/Activity: recent events, vertical left-border timeline
│   └── Related items: compact list with links
│
├── TabPanel: Details
│   ├── Form sections: grid grid-cols-1 lg:grid-cols-2 gap-6
│   ├── Field groups: Label above, Input/Select below
│   ├── Read-only fields: text-foreground (not input, just text)
│   └── Edit mode: Toggle with "Edit" button in PageHeader actions
│
├── TabPanel: Documents
│   ├── File list: table with name, type, size, uploaded date
│   ├── Upload: drag-and-drop zone or button
│   └── Preview: inline for images/PDFs, download for others
│
└── TabPanel: History
    ├── Activity log: vertical timeline
    ├── Each entry: avatar + name + action + timestamp
    └── Filter: All | Comments | Changes | System
```

### Layout rules:
- PageHeader + Tabs in a single column
- No sidebar in detail view (unlike Linear's 3-column — our data isn't dense enough yet)
- Content max-width: `max-w-4xl mx-auto` for readability
- Tab content: `pt-6` below tab bar
- Back button always visible (don't rely on browser back)

---

## Pattern 3: Dashboard

Used for: Plant overview, PM dashboard, Finance summary, any KPI-first view.

```
PageHeader
├── title: h1, text-heading-lg
├── description: context line (entity, date range)
└── actions: DateRangePicker + Export button

KPICardGrid
├── grid: grid-cols-2 lg:grid-cols-4 gap-4
└── KPICard × 3-4 (never more than 4)
    ├── label: text-body-sm text-muted-foreground font-medium
    ├── value: text-data-lg font-data font-semibold
    ├── delta: text-body-sm + TrendingUp/Down icon + green/red color
    └── sparkline: optional mini chart (Recharts, 48px tall)
    style: bg-surface-1, no border (borderless Stripe pattern), p-4 rounded-xl

FilterBar (optional)
├── Time pills: ToggleGroup (7d | 30d | MTD | YTD | Custom)
├── Scope: entity/program selector
└── spacing: flex items-center gap-2, py-3

ChartSection
├── grid: grid-cols-1 lg:grid-cols-2 gap-6
├── Chart card: bg-surface-1 rounded-xl p-6
│   ├── header: title (text-body font-medium) + subtitle (text-body-sm text-muted-foreground)
│   ├── chart: Recharts via shadcn wrappers, 280px height
│   └── legend: below chart, text-body-sm
└── Chart types: Area (trends), Bar (comparison), Donut (breakdown)

RecentActivityTable (compact)
├── header: "Recent Activity" + "View all" link
├── table: compact rows (h-[36px]), max 10 rows
├── columns: timestamp (font-data), description, status (StatusBadge sm)
└── empty state: "No recent activity"
```

### Layout rules:
- Full width, single column, top to bottom
- KPIs always at top, never buried
- Charts side-by-side on desktop, stacked on mobile
- Activity table at bottom
- Gap between major sections: `space-y-6` (24px)
- All cards: `bg-surface-1 rounded-xl`. KPI cards are borderless.

---

## Pattern 4: Form Page

Used for: Create Work Order, Edit Employee, New Quote, any create/edit flow.

```
FormPage layout (components/layouts/form-page.tsx)
├── header slot: PageHeader
│   ├── Breadcrumbs (Work Orders > Create)
│   └── title: "Create Work Order"
│
├── children: centered form (max-w-2xl mx-auto)
│   ├── Section heading (optional): text-heading-md font-semibold
│   ├── FormField × N (components/redoe/form-field.tsx)
│   │   ├── label: text-[13px] font-medium, required asterisk
│   │   ├── input slot: Input, Select, Textarea, RadioGroup, DateRangePicker
│   │   ├── description: text-[11px] text-muted-foreground
│   │   └── error: text-[11px] text-destructive (replaces description)
│   ├── gap between fields: gap-6 (24px)
│   └── Separator between sections
│
└── footer slot: sticky bottom bar
    ├── Cancel: Button variant="outline" (left)
    └── Submit: Button (right), verb + object ("Create Work Order")
```

### Layout rules:
- ALWAYS use FormPage layout for create/edit pages
- ALWAYS use FormField compound for every input
- Validate on blur. Required = red asterisk.
- Success: `toast.success()` + redirect. Error: `toast.error()` + keep form.
- See `.ai/form-patterns.md` for complete field type → component mapping
- See `.ai/examples/form-page-example.tsx` for gold-standard reference

---

## Pattern 5: Settings Page

Used for: Settings, Admin config, Notification preferences, Profile.

```
SettingsPage layout (components/layouts/settings-page.tsx)
├── nav sidebar (220px, left)
│   ├── title: "Settings" text-[14px] font-semibold
│   └── nav items: icon + label, active state via pathname
│       active: bg-layer-active text-foreground font-medium
│       inactive: text-muted-foreground hover:bg-layer-hover
│
└── content area (flex-1, right, max-w-3xl centered)
    ├── Section heading: text-heading-md font-semibold + description
    ├── Setting rows: FormField with Switch/Select/Input
    ├── Separator between sections
    └── Save button per section (not global)
```

### Layout rules:
- One save button per section, not a global submit
- Use Switch for boolean settings, Select for choice settings
- `toast.success("Settings saved")` on save
- See `.ai/examples/settings-page-example.tsx` for gold-standard reference

---

## Pattern 6: Split View

Used for: Inbox, Messages, Job detail with sidebar list. Linear pattern.

```
SplitView layout (components/layouts/split-view.tsx)
├── list panel (320px, left, bg-canvas)
│   ├── Search/filter at top
│   ├── Scrollable item list
│   ├── Selected item: bg-layer-selected
│   └── Each item: title + subtitle + timestamp + status
│
└── detail panel (flex-1, right, bg-surface-1)
    ├── Full detail content for selected item
    ├── Actions in header
    └── EmptyState when nothing selected
```

### Layout rules:
- List panel: fixed width, scrollable independently
- Detail panel: scrollable independently
- Selected item highlighted in list
- Empty state in detail when no selection
- Border between panels: `border-r border-[var(--border-subtle)]`

---

## Responsive Rules (all patterns)

| Breakpoint | Width | Behavior |
|------------|-------|----------|
| `sm` | 640px | Single column, stacked filters |
| `md` | 768px | 2-column KPI grid |
| `lg` | 1024px | Full layout, side-by-side charts |
| `xl` | 1280px | Comfortable spacing |
| `2xl` | 1536px | Max content width with margins |

- FilterToolbar: wraps below `lg`, search gets full width
- Tables: horizontal scroll below `lg`
- KPI grid: 2 cols on `md`, 4 cols on `lg`+
- Charts: stack on mobile, side-by-side on `lg`+
