# Block Map — Mandatory Component Selection

> AI: Read this file BEFORE building any page. Do NOT browse the component library.
> This file tells you EXACTLY which block to use. No choosing. No browsing.
> If a situation isn't covered here, use the Redoe compound from `components/redoe/`.

---

## Rules

1. **Use what's listed here.** Multiple options per category = pick by data shape, not aesthetics.
2. **No colored icons.** All icons: `currentColor`, monochrome. No colored backgrounds on icons.
3. **Numbers in JetBrains Mono.** Add `font-mono` or `font-data` class to all numeric values.
4. **Sidebar and content: SAME background color.** No color contrast between sidebar and main area.
5. **Copy the block file → rename → replace placeholder data with manufacturing data.**

---

## KPI / Stat Cards

| Situation | Use | File | Notes |
|-----------|-----|------|-------|
| Simple KPI (number + delta) | Redoe KPICard | `redoe/kpi-card.tsx` | Label, hero number, delta %, trend arrow. Borderless. |
| KPI with capacity/limit | stat-card7 | `stat-card7.tsx` | Label, number, progress bar, "X of Y" text. For utilization, quotas. |
| KPI with sparkline trend | stat-card8 | `stat-card8.tsx` | Hero number + delta + mini area chart. For financial/trending metrics. |

**Default: `redoe/kpi-card.tsx`** — use this unless you specifically need a progress bar or sparkline.

**Never use:** stat-card1 (too busy), stat-card2 (grid layout), stat-card3 (pipeline), stat-card4 (colored icons), stat-card5 (colored icons), stat-card6 (radial chart).

---

## Data Tables

| Situation | Use | File |
|-----------|-----|------|
| Any table | data-table3 | `data-table3.tsx` |

**Always data-table3.** Sticky header, TanStack React Table, checkbox selection, sort, filter, pagination. Handles 100+ rows.

Customize: replace column definitions with manufacturing fields (WO Number, Customer, Status, etc.). Add StatusBadge in status column. Add ActionMenu in last column. Set row height to 44px. Numbers get `font-mono`.

**Never use:** data-table1 (no sticky header), data-table2 (expandable rows — too complex), data-table4 (drag-and-drop — not needed).

---

## Command Palette (Cmd+K)

| Situation | Use | File |
|-----------|-----|------|
| Any command palette | command2 | `command2.tsx` |

**Always command2.** Grouped results (Navigation + Actions), visible keyboard shortcuts, search icon. Matches Linear pattern.

Customize: replace groups with Redoe navigation (Dashboard, Work Orders, Jobs, Schedule, etc.) and actions (Create Work Order, Start Timer, Run Report, etc.).

**Never use:** command1 (no shortcuts), command3 (file search — too specific), command4 (user search — too specific).

---

## Empty States

| Situation | Use | File |
|-----------|-----|------|
| Any empty state | empty1 | `empty1.tsx` |

**Always empty1.** Icon + title + description + dual CTA buttons. Centered, clean, professional.

Customize: use manufacturing-relevant Lucide icons (ClipboardList for jobs, Wrench for tools, Package for materials, Clock for time entries). Write specific copy ("No active work orders" not "No items found").

**Never use:** empty2 (avatars — not relevant), empty3 (SVG illustration — too decorative), empty4 (404 pattern — too complex).

---

## Tabs

| Situation | Use | File |
|-----------|-----|------|
| Any tabs | tabs4 | `tabs4.tsx` |

**Always tabs4.** Underline style (variant="line"). Clean, monochrome, professional.

Use for: detail page sections (Overview | Operations | Documents | History), settings sections, any multi-panel view.

**Never use:** tabs1 (pill style), tabs2 (hybrid), tabs3 (filled pills — too heavy).

---

## Confirmation Dialogs

| Situation | Use | File |
|-----------|-----|------|
| Destructive action (delete, cancel, remove) | alert-dialog2 | `alert-dialog2.tsx` |
| Also available: | Redoe ConfirmationDialog | `redoe/confirmation-dialog.tsx` |

**Default: `redoe/confirmation-dialog.tsx`** — it wraps the dialog primitive with variant="danger"/"warning" and handles loading state.

Use alert-dialog2 as reference for the visual pattern: icon (monochrome) + title + description + Cancel/Confirm.

**Never use:** alert-dialog1 (no icon), alert-dialog3/4 (FAQ pattern — not for confirmations).

---

## Breadcrumbs

| Situation | Use | File |
|-----------|-----|------|
| Any breadcrumbs | Redoe Breadcrumbs | `redoe/breadcrumbs.tsx` |
| Reference pattern | breadcrumb1 | `breadcrumb1.tsx` |

**Default: `redoe/breadcrumbs.tsx`** — pass items array, get consistent breadcrumbs with ChevronRight separator.

**Never use:** breadcrumb3/4/5 with HomeIcon (adds unnecessary visual noise).

---

## Charts

| Data Type | Use | File | Notes |
|-----------|-----|------|-------|
| Comparison (this vs that) | Bar chart | `chart1.tsx` | Grouped bars, clean legend, Recharts |
| Trend over time | Line chart | `chart3.tsx` | CartesianGrid, multi-line, time axis |
| Composition (parts of whole) | Donut chart | `chart4.tsx` | PieChart with center label |

**Choose by DATA TYPE, not by aesthetics.** If unsure, default to bar chart (chart1).

**Never use:** chart2 (too minimal), chart5 (too complex — currency conversion UI).

---

## Sidebar Navigation

| Situation | Use | File |
|-----------|-----|------|
| Main app sidebar | nav-main pattern | `sidebar-layout/nav-main.tsx` |

**Always this pattern.** Collapsible accordion sections with ChevronRight toggle. Icon + label for top-level items, indented sub-items.

Sections for Redoe OS:
- **Operations:** Dashboard, Work Orders, Jobs, Schedule
- **Resources:** Employees, Machines, Materials
- **Quality:** NCRs, Inspections, Audits
- **Finance:** Job Costing, Reports, Invoices
- **Admin:** Settings, Users, Integrations

**Critical: Sidebar and content must be the SAME background color.** No color contrast between panels.

---

## Dashboard Layout

| Situation | Use | File |
|-----------|-----|------|
| Any management page | dashboard-page-layout1 | `dashboard-page-layout1.tsx` |

**Always layout1.** SidebarProvider + SidebarInset + AppHeader + content area.

**Background rule:** Sidebar bg = Content bg. Both use the same surface color. No split-tone.

---

## Forms

| Situation | Use | File |
|-----------|-----|------|
| Full create/edit form | form-layout1 | `form-layout1.tsx` |
| Individual form fields | FormField compound | `redoe/form-field.tsx` |

**form-layout1** for reference: multi-section, label-above-input, react-hook-form + Zod, grid-based responsive.

**FormField** compound for every individual field — label + input + error. No exceptions.

Use `FormPage` layout template for page structure (centered, sticky footer).

---

## Toasts / Notifications

| Situation | Use | File |
|-----------|-----|------|
| Any feedback | Redoe toast | `redoe/toaster.tsx` |

**Always use the Redoe toast utility:**
```tsx
import { toast } from "@/components/redoe"
toast.success("Work order created")
toast.error("Failed to save changes")
```

Position: bottom-right. Duration: 5s. Auto-styled with Redoe tokens.

---

## Loading States

| Situation | Use | File |
|-----------|-----|------|
| Page loading | LoadingSkeleton | `redoe/loading-skeleton.tsx` |

Pass variant: "list", "dashboard", "detail", "form", or "card". Gets correct skeleton layout automatically.

**Never use spinners.** Always skeleton shimmer.

---

## Detail Side Panel (click row → detail slides in from right)

| Situation | Use | File |
|-----------|-----|------|
| Click table row → show detail | sheet1 | `sheet1.tsx` |
| Click table row → show detail (with form) | sheet2 | `sheet2.tsx` |
| Bottom drawer on mobile | drawer1 | `drawer1.tsx` |

The Sheet pattern: user clicks a row in a data table → a panel slides in from the right showing full details. User can view/edit without leaving the list. Close by clicking outside or pressing Escape.

Use Sheet for desktop (slides from right). Use Drawer for mobile (slides from bottom).

---

## Filter Bars

| Situation | Use | File |
|-----------|-----|------|
| Any list/table filter | FilterBar compound | `redoe/filter-bar.tsx` |

Search input + filter slots + time pills + export button. One line.

---

## Status Indicators

| Situation | Use | File |
|-----------|-----|------|
| Any status display | StatusBadge | `redoe/status-badge.tsx` |

Pass status key → get correct icon + color + text. Always color + icon + text. Never color alone.

---

## Action Menus (⋯ button)

| Situation | Use | File |
|-----------|-----|------|
| Row/card actions | ActionMenu | `redoe/action-menu.tsx` |

Pass items array → get correct dropdown. Danger items auto-separated to bottom.
