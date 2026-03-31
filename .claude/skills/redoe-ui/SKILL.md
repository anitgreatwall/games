---
name: redoe-ui
description: Build Redoe OS UI components using the Redoe design system. Use this skill when building any UI for Redoe OS — dashboards, forms, tables, visualizations, shop floor interfaces. Ensures all generated code matches Redoe brand, uses correct tokens, and follows manufacturing UX rules. Trigger when user mentions Redoe OS UI, dashboard, component, or references design system.
---

This skill ensures all Redoe OS UI work is on-brand, consistent, and production-ready. Before generating any UI code, load and follow the design system.

## Design Quality Stack (priority order when conflicts arise)

1. **`.ai/foundation.md`** + **`design-system-cheatsheet.md`** — AUTHORITATIVE for tokens, rules, patterns
2. **`DESIGN.md`** (scaffold root) — full spec when cheatsheet doesn't cover your need
3. **Impeccable skill** (`.claude/skills/impeccable/`) — general design principles, `/audit`, `/polish`, `/delight`
4. **Emil Kowalski skill** (`.claude/skills/emil-design-eng/`) — animation polish, micro-interactions
5. **`.impeccable.md`** (project root) — Redoe-specific context for Impeccable commands

When Impeccable or Emil suggest different fonts, colors, or spacing → Redoe design system wins. When they add depth our system doesn't cover (motion easing, UX writing, interaction states) → follow their guidance.

## Step 1: Load Design Context

Read these files before generating any UI code:

1. **Block Map** (REQUIRED — read FIRST): `apps/web/.ai/block-map.md`
   - Tells you EXACTLY which component/block to use for every situation
   - Pick by data shape, not aesthetics. Follow the map.

2. **AI Foundation Rules** (REQUIRED): `apps/web/.ai/foundation.md`
   - MUST/SHOULD/WON'T rules, tokens, depth model, spacing, motion, accessibility
   - Component inventory: 44 primitives, 17 compounds, 8 layouts, 100+ pulled blocks

3. **Composition Patterns** (REQUIRED for any page): `apps/web/.ai/composition-patterns.md`
   - 6 canonical page layouts: List, Detail, Dashboard, Form, Settings, Split View

4. **Interaction Patterns**: `apps/web/.ai/interaction-patterns.md`
   - Every state (hover, focus, active, disabled, loading, error, success), animation timing, z-index

5. **Form Patterns**: `apps/web/.ai/form-patterns.md`
   - Field layout, validation, field type → component mapping, form actions

6. **Status System**: `apps/web/.ai/status-system.md`
   - Status → token → background → icon → usage. Badge sizes, entity badges.

7. **Design System Cheatsheet**: `_reference/design-system-cheatsheet.md`
   - All tokens, typography, spacing, component quick-ref, hard rejects

8. **Few-Shot Examples**: `apps/web/.ai/examples/`
   - Gold-standard pages: list, dashboard, detail, form, settings. Match these patterns.

9. **Full Design Spec** (on demand only): `DESIGN.md`
   - Only when the above files don't cover your need

## Step 2: Identify the Context

Before coding, determine:

- **Target user:** Shop floor operator? PM? Finance? Management?
- **Target device:** Tablet kiosk (lg)? Desktop (xl/2xl)? Phone (sm)?
- **Data source:** Which Supabase tables/views? Real-time subscription needed?
- **Actions available:** What can the user DO from this view? (Approve, reject, flag, reassign, escalate)
- **Composition pattern:** Which of the 3 canonical patterns matches? (List, Detail, Dashboard)

## Step 3: Generate Code

Follow these rules strictly:

### Colors & Depth
- Use CSS variables (`bg-primary`, `text-foreground`) — NEVER hardcoded hex
- Depth model: Canvas (off-white bg) > Surface (white cards) > Layer (hover/selected states)
- Depth via background color, NOT shadows. Shadows only for modals/popovers/dropdowns.
- Status: use `--color-status-*` tokens. Always color + icon + text.
- Borders: near-invisible (`--border-subtle`). If visible at a glance, too heavy.
- Light mode is DEFAULT. Color only for status and CTAs — everything else is monochrome.

### Typography
- Body/headings/labels: `font-sans` (Inter) — 13px base set on `<html>`
- Numbers/codes/job IDs: `font-data` class (JetBrains Mono + tabular-nums)
- KPI hero numbers: `text-[32px] font-data font-semibold tracking-tight`
- Hierarchy via weight (400/500/600), not size. Max 4 sizes + 3 weights per view.

### Components
- Use Redoe compound components from `components/redoe/` FIRST (StatusBadge, KPICard, etc.)
- Fall back to shadcn/ui from `components/ui/` for base primitives
- **Registry-first:** Search `@shadcn` then `@magicui` before building from scratch
- Tables: 44px row height, `font-data` + right-align on numbers, empty state required
- Buttons: 44px min height (56px shop floor). Use verb + object labels ("Save changes" not "OK")
- Forms: react-hook-form + zod. Labels above inputs. Validate on blur. Searchable Command dropdowns.
- Loading: `.skeleton` class shimmer, never spinners. Specific messages ("Loading job data...")
- Empty states: centered icon + heading + description + CTA button (Linear pattern)

### Visualizations
- Charts: Recharts via shadcn chart wrappers (Tier 1)
- Graphs/flows: React Flow (Tier 2, Sprint 2+)
- Accents: Magic UI sparingly (number ticker, marquee, shimmer border)

### Bidirectional Pattern (CRITICAL)
Every dashboard view MUST include action buttons. Not just data display.
```
Chart shows over-budget jobs  →  "Escalate" button
Table row shows anomaly       →  "Approve/Reject" inline
KPI card shows low metric     →  "Drill Down" → detail view → "Flag for Review"
```

### Accessibility
- Body text: 4.5:1 contrast (WCAG AA). Shop floor: 7:1 (WCAG AAA).
- `focus-visible` ring on all interactive elements
- ARIA: `navigation` on sidebar, `aria-sort` on table headers, `aria-modal` on dialogs, `role="status"` on badges
- Status = color + Lucide icon + text. NEVER color alone.
- Keyboard: Cmd+K (search), Cmd+B (sidebar), Escape (close). Show hints on Tier 2+.

### Layout
- Match page to composition pattern from `.ai/composition-patterns.md`
- Sidebar: 232px expanded, 48px collapsed, Cmd+B toggle. Icons monochrome.
- Detail views: tabs (Overview | Details | Documents | History). Max-w-4xl for readability.
- Settings: two-column (section nav + content)
- Command palette (Cmd+K): global search + actions with shortcut hints

### Shop Floor Rules (if target = operator)
- No sidebar. Full-screen content only.
- Three-screen max: Select → Act → Confirm
- 44px minimum touch targets (56px primary actions, full-width)
- No financial data visible (costs, margins, revenue)
- WCAG AAA (7:1 contrast). Readable from 3 feet.
- Offline tolerance: queue actions locally

### Motion
- 100-150ms instant feedback (hover, toggle). 200-300ms state changes. Exit = 75% of enter.
- Use `--ease-out` for entering, `--ease-out-expo` for dropdowns
- Only animate `transform` and `opacity`. No bounce/wobble/elastic.
- Keyboard-initiated actions: no animation (Cmd+K, shortcuts)
- `prefers-reduced-motion` handled globally in CSS

## AI Slop Rejection Criteria (v9)

### HARD REJECT (regenerate if present)
- Purple/violet gradients as primary scheme
- Glassmorphism on everything (management accent only, never shop floor)
- Generic dashboard with 4 equal stat cards (use composition patterns)
- Circular progress as main viz (use Recharts bar/line)
- Stock illustrations or emoji placeholders
- >12px radius on containers
- Rainbow status colors (lime/amber/red/sky ONLY)
- Centered single-column for data-dense views
- Hardcoded hex values in components
- Spinners instead of skeleton loaders
- Colored icons in navigation/sidebar
- Improvised page layout that doesn't match a composition pattern

### SOFT REJECT (fix before accepting)
- Generic card shadows (use `--shadow-*` tokens)
- Placeholder "Lorem ipsum" (use real Redoe data: job numbers, operation names)
- "Welcome back, User" greeting (manufacturing apps show status, not greetings)
- Hamburger menu on desktop (sidebar always visible at Tier 2+)
- Hover tooltips as primary info display (no hover on touchscreens)

### What Redoe OS SHOULD Look Like
Reference aesthetic: **Linear density + Plane depth + Stripe dashboards**
- Dense, information-rich, monochrome with surgical color accents
- Off-white canvas background, white surface cards, near-invisible borders
- Weight hierarchy (400/500/600) over size hierarchy
- Data tables with `font-data`, right-aligned numbers, `tabular-nums`
- Command palette (Cmd+K) as primary navigation for power users
- KPI cards: borderless, hero numbers, Stripe pattern
- Restrained animation (100-200ms ease-out, no bounce)

## HTML Mockup Template (for feature previews)

When building **HTML mockups** to preview a feature before coding React, use the mockup template instead of hand-coding the app shell:

**Template file:** `_reference/mockup-template.html` (also in this skill folder as `mockup-template.html`)

**What it provides:**
- Exact mirror of `app-sidebar.tsx` — 6 nav groups, Lucide icons, blue badges, SP user footer
- Design tokens from `globals.css` (Inter + JetBrains Mono, surfaces, borders, status colors)
- Presentation bar with screen-switching tabs
- Common components: buttons, KPI cards, filter bar, view switcher, data table, status badges
- Modal overlay, save bar, full-page header patterns

**How to use:**
1. Copy the template as your starting point
2. Fill `<div class="cb">` with feature content
3. Add screen tabs to `.pbar` for navigation
4. Set `data-sb="<key>"` on each sidebar to highlight active nav item

**Sidebar active keys:** `dashboard`, `inbox`, `alljobs`, `pipeline`, `schedule`, `employees`, `timeclock`, `timeanalytics`, `timeapproval`, `machines`, `quality`, `jobcosting`, `reports`, `settings`

**Sync rule:** When `app-sidebar.tsx` changes (new nav items, icon updates), update the template in the same PR.

## Step 4: Verify

Before presenting code to user, check:
- [ ] All colors use CSS variables (no hardcoded hex)
- [ ] `font-data` on all numbers, codes, job IDs
- [ ] Page matches a composition pattern from `.ai/composition-patterns.md`
- [ ] All interactive elements have action buttons (bidirectional)
- [ ] Touch targets >= 44px (shop floor >= 56px primary)
- [ ] No financial data exposed to shop floor role
- [ ] Redoe compounds used where available, shadcn for everything else
- [ ] Status indicators use color + icon + text (never color alone)
- [ ] Skeleton loaders for all data-dependent views
- [ ] Empty states for all lists/tables/feeds
- [ ] Depth model: canvas bg, surface cards, layer hover states
- [ ] Borders near-invisible (--border-subtle)
- [ ] 8px grid spacing (4px only for icon-text gaps)

## Quick Reference: shadcn CLI

```bash
npx shadcn@latest add <component>            # Add component
npx shadcn@latest add <component> --dry-run   # Preview without installing
npx shadcn@latest add <component> --diff      # See changes
npx shadcn docs <component>                   # Get docs in terminal
npx shadcn info                               # Show project config
```
