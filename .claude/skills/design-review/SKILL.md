---
name: design-review
description: "Post-build design audit for Redoe OS. Rates 7 dimensions 0-10 against the design system, detects AI slop, and makes atomic commits per finding. Use after /qa passes and before /ship — catches 'it works but looks wrong.' Invoked via /design-review or /design-review [url]. Also runs as part of /qa fix when frontend files change."
---

# /design-review — Audit the Built Output

Post-implementation visual audit. /review-plan Phase 3 checks the MOCKUP. /qa Stage 6 checks if it WORKS. This skill checks if it LOOKS RIGHT after building — the gap between "mockup was approved" and "built code drifted."

Same principle as inspecting the cut steel after approving the mold design.

**Team:** Steve (VP), Andy (backend), Kevin (frontend), Ben Wang.

## Usage

```
/design-review                     — Audit current branch (auto-detect changed pages)
/design-review http://localhost:3000/jobs  — Audit a specific page
/design-review --fix               — Audit + auto-fix with atomic commits per finding
```

**When to run:**
- After `/qa` passes (feature works) but before `/ship`
- When Kevin submits frontend PRs
- When any dashboard or Shop Floor page changes

---

## Before Starting

1. Read `_Projects/Redoe-OS/_reference/design-system.md` (canonical — ALL design decisions)
2. Read `_System/design-language.md` (cross-product brand reference)
3. Get changed frontend files: `git diff --name-only main...HEAD -- 'apps/web/src/'`
4. Identify which pages/routes are affected by the changes
5. Start the dev server: `cd apps/web && pnpm dev`
6. Wait for server ready (poll `http://localhost:3000` until 200)
7. If a wireframe exists at `_Projects/Redoe-OS/_specs/wireframes/SPEC-NNN-wireframe.html`, open it side-by-side. Compare built output against wireframe layout intent. Deviation from wireframe = finding (unless justified by implementation constraints).
8. Run Tufte Test checks from `_System/design-language.md` — text overflow, touch targets, contrast, orphaned words. These are deterministic Playwright checks, not subjective.

---

## The 7-Dimension Audit

Rate each dimension 0-10. For any score below 8: describe what a 10 looks like, then fix it (if `--fix` mode) or flag it.

### Dimension 1: Design System Alignment (weight: highest)
Does the output match the Redoe design system?

| Check | What to look for |
|-------|-----------------|
| Color tokens | Only `--redoe-navy`, `--redoe-blue`, `--redoe-light`, status colors, entity colors. No hardcoded hex. |
| Typography | DM Sans for headings/body, JetBrains Mono for data/numbers/KPIs, Outfit for display. NOT Inter, Arial, system default. |
| Spacing | 8px grid. 4px only for icon-text gaps. `gap-6` between sections. |
| Components | shadcn/ui components. No custom HTML elements replacing shadcn equivalents. |
| Status indicators | Color + icon + text. NEVER color alone. Correct Lucide icons per design system. |
| Shadows | Layered shadows (`--shadow-sm/md/lg`), not single box-shadow. |
| Border radius | Design system tokens only. No hardcoded `rounded-[Xpx]`. |

### Dimension 2: Tier Compliance
Does the output match the declared user tier?

| Tier | Requirements |
|------|-------------|
| Shop Floor (Tier 1) | Touch targets 56px+, no sidebar, single-column, no financial data, escape/enter/tab only, no hover-only interactions |
| Management (Tier 2) | Sidebar, Cmd+K accessible, searchable dropdowns, keyboard shortcut hints on buttons, three-column detail |
| Admin (Tier 3) | Settings two-column, API access visible, audit logs, full keyboard |

Flag: "Declared as Shop Floor but uses a data table with 12px row height" = FAIL.

### Dimension 3: Information Architecture
Is the information hierarchy correct?

- KPI cards: 3-4 max across top. Large primary number + small comparison line. No borders — background separation only.
- Filter bar: horizontal pills, one line, below KPIs, above charts.
- Data density: appropriate for tier (dense for Management, sparse for Shop Floor).
- Whitespace: generous. `gap-6` minimum between sections. Cards don't touch.
- Stripe aesthetic: when in doubt, choose whitespace over more information.

### Dimension 4: Interaction State Coverage
Are all states handled?

| State | Must exist |
|-------|-----------|
| Empty state | Centered message + CTA button (not blank page) |
| Loading state | Skeleton shimmer or Redoe logo pulse (not spinner) |
| Error state | Clear message + retry action + contact info |
| Hover state | Only on Management/Admin tiers (Shop Floor = no hover) |
| Focus state | `focus-visible` ring on all interactive elements |
| Disabled state | Muted appearance + tooltip explaining why |
| Offline/degraded | "Saved offline. Will sync when connected." if applicable |

### Dimension 5: Responsive & Accessibility
Does it work on all target devices?

- [ ] WCAG AA contrast (4.5:1 minimum on all text)
- [ ] Touch targets 44px minimum (56px for Shop Floor primary actions)
- [ ] Keyboard navigable (Tab between elements, Enter to submit, Escape to close)
- [ ] No horizontal scroll on any viewport
- [ ] Tablet view (1024px) works for Shop Floor pages
- [ ] Data numbers right-aligned with `font-variant-numeric: tabular-nums`
- [ ] Breadcrumbs are clickable links, not decorative text
- [ ] Animations 150-300ms, ease-out, no bounce. Respects `prefers-reduced-motion`.

### Dimension 6: AI Slop Detection
Does the output look like generic AI-generated content?

| Pattern | What to flag |
|---------|-------------|
| **Generic gradients** | Linear gradients that serve no purpose. Especially purple-to-blue "AI aesthetic." |
| **Default shadcn** | shadcn components with zero customization — stock neutral theme, no Redoe tokens applied. |
| **Placeholder data** | "Lorem ipsum", "John Doe", "Acme Corp", "Sample Project" in committed code. |
| **Stock iconography** | Decorative icons that don't map to actual features. Icons for the sake of icons. |
| **Card soup** | 6+ identical cards in a grid with no hierarchy or differentiation. |
| **Dashboard widgets with no data source** | Charts/gauges that look impressive but aren't connected to real queries. |
| **Generic hero section** | "Welcome to Redoe OS" with a stock gradient and no actual content. |
| **Meaningless animations** | Entrance animations on every element, floating particles, unnecessary transitions. |

Score 8+ = clean, intentional design. Score 5-7 = some AI artifacts, needs cleanup. Score <5 = full rewrite.

### Dimension 7: Manufacturing Context
Does it understand the domain?

- [ ] Terminology correct: "Work Order" not "Ticket", "Job" not "Project", "Operation" not "Step", "Moldmaker" not "Technician"
- [ ] Financial data visibility matches RLS tier (no costs on Shop Floor)
- [ ] Bidirectional: dashboard has action buttons, not just read-only charts
- [ ] Time displays: ET for Windsor, CST+8 for Hunan (if cross-plant view)
- [ ] Job number format matches Redoe convention (G-XXXX, R-XXXX)

---

## Scoring & Output

```
=========================================
DESIGN REVIEW — Redoe OS
=========================================
Page: /jobs (Job List — Management Tier)
Branch: feat/SPEC-012-job-list

Dimension                    Score   Notes
────────────────────────────────────────────
1. Design System Alignment   9/10    Minor: one hardcoded #2E75B6
2. Tier Compliance           10/10   Management tier correct
3. Information Architecture  8/10    KPIs good, filter bar missing
4. Interaction States        7/10    No empty state, no loading skeleton
5. Responsive & A11y         9/10    Touch targets pass, missing focus ring on 2 buttons
6. AI Slop                   9/10    Clean — no generic patterns
7. Manufacturing Context     10/10   Terminology correct, bidirectional

OVERALL: 8.9/10 — PASS with 3 findings
AI SLOP GRADE: A (clean)

Findings:
  #1 [P2] Missing empty state on job list — add centered "No jobs found" + CTA
  #2 [P2] Missing skeleton loader — replace spinner with shimmer
  #3 [P3] Hardcoded #2E75B6 in job-table.tsx:42 — use var(--redoe-blue)
=========================================
```

**Grading:**
- 8.0+ overall = **PASS** (ship-ready)
- 6.0-7.9 = **CONDITIONAL** (fix Priority 1-2 findings before ship)
- <6.0 = **FAIL** (significant rework needed)

---

## Fix Mode (`--fix`)

When `--fix` is specified, for each finding:

1. Locate the source file and line
2. Make the minimal CSS/styling/component change
3. Commit with message: `style(design): DR-NNN description`
4. Wait for hot reload
5. Navigate back and verify the fix
6. Take before/after screenshots if visual

**Rules:**
- One commit per finding (fully bisectable)
- CSS-only changes = free pass (inherently safe, no logic risk)
- JSX/TSX changes count against a risk budget — max 10 JSX changes per review
- If a finding requires >5 lines of JSX change, flag it for human review instead
- Hard cap: 30 fixes per review session. After 30, stop and report remaining.

---

## Integration

- **`/review-plan` Phase 3** — checks design BEFORE code (mockups)
- **`/qa` Stage 6** — checks if it WORKS (runtime + browser)
- **`/design-review`** — checks if it LOOKS RIGHT after building (this skill)
- **`/ship`** — gates on design review score (advisory, not blocking)

Pipeline position: `/qa` PASS → `/design-review` → `/ship`

If design review reveals systemic issues (wrong tier, wrong aesthetic), escalate to Steve before shipping. Don't auto-fix foundational design decisions.

---

## What This Catches

- Mockup was approved but developer drifted during implementation
- shadcn defaults not customized to Redoe tokens
- AI-generated slop in committed code (generic dashboards, placeholder text)
- Missing interaction states (empty, loading, error, offline)
- Tier violations (hover interactions on Shop Floor, missing touch targets)
- Manufacturing terminology errors (generic SaaS language in UI)
- Accessibility regressions (contrast, keyboard nav, focus rings)
