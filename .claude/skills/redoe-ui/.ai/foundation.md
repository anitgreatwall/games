# Redoe OS — AI Foundation Rules

> Read this file before generating ANY UI code. These rules are non-negotiable.
> For deep reference: `../../DESIGN.md`. For token values: `../src/app/globals.css`.

---

## Stack

React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui + Lucide icons + Next.js 16 (App Router)

---

## MUST (non-negotiable)

### Tokens
- Use CSS variables from `globals.css` — NEVER hardcode hex values in components
- Use `cn()` from `@/lib/utils` for conditional class merging
- Use `font-data` class for all numeric displays (activates JetBrains Mono + tabular-nums)
- Right-align all currency/numeric columns with `text-right-numeric` class

### Components
- Use shadcn/ui components from `components/ui/` as base primitives (24 available: avatar, badge, button, checkbox, collapsible, command, context-menu, dialog, dropdown-menu, input, input-group, popover, progress, radio-group, scroll-area, select, separator, sheet, sidebar, skeleton, switch, table, tabs, textarea, tooltip)
- Use Redoe compound components from `components/redoe/` when available — they eliminate decisions:
  - StatusBadge, KPICard, PageHeader, EmptyState, EntityBadge, FilterBar, DataTable, ChartSection
  - ConfirmationDialog (destructive actions), RedoeToaster/toast (feedback), ActionMenu (⋯ buttons)
  - SearchCommand (Cmd+K palette), FormField (label+input+error), Breadcrumbs, DateRangePicker
  - StatRow (inline stats), LoadingSkeleton (page-level loading by variant)
- Use layout templates from `components/layouts/` — pick one, fill slots:
  - ManagementLayout (sidebar+main), DashboardPage, ListPage, DetailPage, ShopFloorLayout
  - FormPage (create/edit), SettingsPage (two-column), SplitView (list+detail)
- Use Lucide React icons — no other icon library
- All icons: `size={16}` (size-4), monochrome (`currentColor`). NO colored icons in nav/sidebar.
- Magic UI: only `NumberTicker` for KPI hero numbers. Nothing else.

### Component Sourcing (MANDATORY workflow)
1. Check `components/redoe/` compounds FIRST — they encode all visual decisions
2. If no compound exists, use `components/ui/` shadcn primitives
3. Before building new primitives: `npx shadcn add <name>` or `npx shadcn add @shadcnuikit/<name>`
4. Build from scratch ONLY if nothing in any registry matches

### Status Indicators
- Status MUST use color + icon + text — NEVER color alone
- Use `StatusBadge` component when available, or follow pattern: `bg-{status}/10 text-{status} border-{status}/30`
- Reference `.ai/status-system.md` for complete mapping

### Typography
- Inter for all UI text (headings, labels, body)
- JetBrains Mono for data: job IDs, KPI numbers, timestamps, table numeric columns
- 13px base (set on `html`). Hierarchy via weight (400/500/600), not size.
- Max 4 font sizes + 3 weights per view

### Depth (Surface > Layer)
- **Sidebar and content area MUST be the SAME background color.** No split-tone. Both use `--surface-1` (white).
- `--surface-1` (white) = everything: page background, sidebar, content area, cards
- `--surface-2` = secondary panels, alternate table row stripes (subtle)
- `--layer-1` = depth within surfaces. `--layer-hover` for hover. `--layer-active` for pressed.
- `--layer-selected` = selected row/item (subtle blue tint)
- Depth via background color, NOT shadows. Shadows only for modals/popovers/dropdowns.
- Do NOT use `--canvas` for page backgrounds — use `--surface-1` everywhere.

### Icons
- **ALL icons MUST be monochrome.** Use `currentColor` only. No colored icon backgrounds.
- No colored icons in sidebar, navigation, headers, or anywhere.
- Color only appears on: status badge text/bg, CTAs, trend arrows. Icons themselves = monochrome always.

### Borders
- `--border` = default (near-invisible, Linear pattern)
- `--border-subtle` = barely visible separator (sidebar edge, row dividers)
- `--border-strong` = emphasis when needed (section breaks, focused inputs)
- Borders should be nearly invisible. If you can see them at a glance, they're too heavy.

### Spacing
- 8px grid. 4px only for icon-text gaps.
- `space-2` (8px) tight. `space-4` (16px) standard card padding. `space-6` (24px) card-to-card gaps.
- Buttons: `rounded-lg` (0.5rem). Cards: `rounded-xl` (0.75rem). Badges: `rounded-full` (pill).

### Motion
- 100-150ms instant feedback (hover, toggle, button press)
- 200-300ms state changes (tab switch, menu open, panel expand)
- Exit = 75% of enter duration
- Use `--ease-out` for entering, `--ease-out-expo` for dropdowns/popovers
- Only animate `transform` and `opacity`. Never bounce/wobble/elastic.
- `@media (prefers-reduced-motion: reduce)` handled globally in CSS

### Accessibility
- Body text: 4.5:1 contrast (WCAG AA). Shop floor: 7:1 (WCAG AAA).
- Touch targets: 44px min (standard), 56px (shop floor primary actions)
- Focus ring: handled by shadcn defaults. Don't override.
- Tab order follows visual layout. No positive tabindex.
- Dialogs trap focus. Escape closes.

### Page Structure
- Match page to nearest composition pattern in `.ai/composition-patterns.md`
- Every list/table needs an empty state (icon + heading + description + CTA)
- Loading: content-shaped skeletons using `.skeleton` class, never spinners
- Every data view needs action buttons — no read-only displays

---

## SHOULD (preferred unless good reason not to)

- Prefer Server Components. Use `'use client'` only for interactivity (forms, state, effects).
- Store filter/pagination state in URL search params, not React state
- Use Zod for all form validation schemas
- Use `react-hook-form` for forms
- Use searchable Command dropdowns, never raw `<select>`
- Prefer `gap-*` over margin for spacing between siblings
- Use `grid-template-rows: 0fr/1fr` for height animations instead of animating `height`
- Tables: 44px row height, sortable columns, `font-data` on numeric columns
- Buttons on Tier 2+: include keyboard hint — `Save (Cmd+S)`
- Validate forms on blur, not keystroke
- Error messages answer: What happened? Why? How to fix?

---

## WON'T (forbidden — hard rejects)

- No inline styles
- No hardcoded hex colors (use tokens)
- No custom table implementations (use DataTable compound or shadcn Table)
- No new animation libraries (use CSS transitions with token durations)
- No spinners (use `.skeleton` shimmer)
- No colored icons in navigation or sidebar
- No Calibri or system fonts
- No bounce, wobble, or elastic animations
- No purple gradients or glassmorphism
- No `<select>` elements (use searchable Command)
- No Lorem ipsum or placeholder content
- No rounded corners >12px on containers
- No `scale(0)` animations — start from 0.95+
- No decorative illustrations in data views
- No more than 7 table columns before horizontal scroll

---

## User Tiers

Every screen declares its tier. Tier rules override general rules.

| Tier | Users | Input | Key Overrides |
|------|-------|-------|---------------|
| 1: Shop Floor | Operators, moldmakers | Touch (tablets, gloves) | 56px buttons, no sidebar, no financials, 3-screen max, WCAG AAA |
| 2: Management | PMs, finance, plant mgr | Mouse + keyboard | Dense tables, Cmd+K, three-column detail, searchable dropdowns |
| 3: Admin | IT, Steve | Full keyboard | Settings two-column, audit logs, all shortcuts |

---

## Manufacturing Terminology

| Use This | NOT This |
|----------|----------|
| Work Order | Ticket, Task, Issue |
| Job | Project (shop floor) |
| Operation | Step, Stage |
| Program | Product Line |
| Shop Floor | Factory Floor |
| Moldmaker | Technician |

---

## File Conventions

| What | Convention | Example |
|------|-----------|---------|
| Components | PascalCase | `StatusBadge.tsx` |
| Files | kebab-case | `status-badge.tsx` |
| CSS | Tailwind utilities | `bg-primary text-primary-foreground` |
| Hooks | `use-` prefix | `use-jobs.ts` |
| Types | from `@redoe-os/types` | Never hand-write DB types |
