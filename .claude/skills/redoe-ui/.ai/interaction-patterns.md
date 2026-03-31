# Interaction Patterns — Redoe OS

> Every interactive state for every component type. No guessing.
> Tokens reference `globals.css`. Component base: shadcn/ui + `components/redoe/`.

---

## 1. Universal States

All interactive elements must handle every state in this table.

| State | Visual Treatment | Classes |
|-------|-----------------|---------|
| Default | Base styling per component | (component default) |
| Hover | Subtle background shift, instant transition | `hover:bg-[var(--layer-hover)] transition-colors duration-[var(--duration-instant)]` |
| Focus | Ring on keyboard focus only, never on click | `focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:outline-none` |
| Active/Pressed | Micro-scale on buttons, bg shift on list items | Buttons: `active:scale-[0.97]` / List items: `active:bg-[var(--layer-active)]` |
| Disabled | Dimmed, no pointer events | `disabled:opacity-50 disabled:pointer-events-none` |
| Loading | Content replaced with skeleton shimmer, never spinners | `.skeleton` class on placeholder div matching content shape |
| Error | Destructive border + inline error text below | `border-destructive` + `<p role="alert" className="text-[11px] text-destructive">` |
| Success | Toast notification (5s auto-dismiss), no persistent green border | `toast.success("message")` via Sonner |

### Rules
- **NEVER** use `:focus` — always `focus-visible` (keyboard-only ring)
- **NEVER** show spinners — use `.skeleton` shimmer (see `globals.css`)
- Disabled elements must also have `aria-disabled="true"`
- Loading states must preserve layout dimensions (no content shift)

---

## 2. Animation Timing

| Category | Duration | Token | Use For |
|----------|----------|-------|---------|
| Instant | 100-150ms | `var(--duration-instant)` / `var(--duration-fast)` | Hover, toggle, button press, checkbox, switch |
| State | 200ms | `var(--duration-normal)` | Tab switch, menu open, panel expand, filter change |
| Layout | 300-500ms | `var(--duration-slow)` / `var(--duration-layout)` | Modal enter, drawer slide, accordion open, page transition |

### Duration Rules
- Exit animation = 75% of enter duration
- Keyboard-initiated transitions = instant, skip animation entirely
- `@media (prefers-reduced-motion: reduce)` handled globally — do not override
- Only animate `transform` and `opacity`. Never animate `width`, `height`, `top`, `left`.
- For height animations use `grid-template-rows: 0fr` / `1fr` pattern

---

## 3. Easing Curves

| Context | Token | Value | Use For |
|---------|-------|-------|---------|
| Elements entering view | `var(--ease-out)` | `cubic-bezier(0.25, 1, 0.5, 1)` | Modals, cards, page content |
| Dropdowns / Popovers | `var(--ease-out-expo)` | `cubic-bezier(0.16, 1, 0.3, 1)` | Menus, tooltips, command palette |
| State toggles | `var(--ease-in-out)` | `cubic-bezier(0.65, 0, 0.35, 1)` | Tabs, switches, accordion |

### Forbidden
- `ease` (generic) — always use a named token
- `ease-in` alone — elements should never decelerate into view
- `spring`, `bounce`, `elastic` — none of these exist in the system

---

## 4. Component-Specific Animations

| Component | Enter | Exit | Transform Origin |
|-----------|-------|------|-----------------|
| Dialog | `scaleIn` 200ms `ease-out` + backdrop `fadeIn` 150ms | Scale to 0.95 + fade, 150ms | `center` |
| Sheet / Drawer | `slideInFromRight` 300ms `ease-out-expo` | Slide out, 225ms | `right` (or `bottom` for mobile) |
| Dropdown / Popover | `fadeSlideIn` 150ms `ease-out-expo` | Fade + slide up 4px, 112ms | `top` (or computed by Radix) |
| Tooltip | `fadeIn` 100ms `ease-out`, 500ms delay | Instant (no exit animation) | Computed by Radix |
| Button press | Scale to 0.97, `duration-instant` | Scale to 1, `duration-instant` | `center` |
| Toast | `slideInFromBottom` 300ms `ease-out` | Fade + slide down, 225ms | `bottom-right` |

### Keyframes Reference (defined in `globals.css`)
```
fadeSlideIn:      translateY(8px) → translateY(0) + opacity
fadeIn:           opacity 0 → 1
scaleIn:          scale(0.95) → scale(1) + opacity
slideInFromRight: translateX(100%) → translateX(0)
slideInFromBottom:translateY(100%) → translateY(0) + opacity
```

---

## 5. Z-Index Layers

| Layer | z-index | Components |
|-------|---------|------------|
| Sticky headers | `z-10` | Table header, filter toolbar |
| Floating actions | `z-20` | FAB, bulk action bar |
| Dropdowns / Menus | `z-30` | Select, DropdownMenu, Popover |
| Tooltips / Context menus | `z-50` | Tooltip, ContextMenu, Command palette |
| Dialog backdrop | `z-90` | `DialogOverlay` |
| Dialog content | `z-100` | `DialogContent`, `SheetContent` |
| Toasts | `z-[999]` | Sonner toaster |

### Rules
- Never use arbitrary z-index values outside this table
- Nested portals inherit parent stacking — Radix handles this automatically
- Sidebar is `z-0` (in-flow, not elevated)

---

## 6. Selection States

| Element | Selected State | Classes |
|---------|---------------|---------|
| Table row | Subtle blue tint background | `bg-[var(--layer-selected)]` |
| Table row (hover while selected) | Slightly darker tint | `bg-[var(--layer-selected)] hover:bg-[var(--layer-active)]` |
| Checkbox (checked) | Primary color fill, white check icon | shadcn default — `data-[state=checked]:bg-primary` |
| Radio (selected) | Primary color dot | shadcn default — `data-[state=checked]:bg-primary` |
| Switch (on) | Primary color track | shadcn default |
| Tab (active, line variant) | Underline via pseudo-element | `after:absolute after:bottom-0 after:h-[2px] after:bg-primary after:opacity-100` |
| Tab (active, pill variant) | Filled background | `bg-[var(--layer-active)] text-foreground font-medium` |
| Sidebar nav item (active) | Layer background + font-medium | `bg-[var(--layer-hover)] text-foreground font-medium` |
| Command item (highlighted) | Accent background | `bg-accent text-accent-foreground` |

---

## 7. Touch Targets

| Tier | Min Target Size | Applies To | Detection |
|------|----------------|------------|-----------|
| Compact (Tier 2, mouse) | 28px | Icon buttons, table row actions, dense controls | Default |
| Standard (Tier 2) | 44px | Buttons, inputs, nav items, checkboxes | Default |
| Shop Floor (Tier 1) | 56px | Primary actions, time clock, status buttons | `@media (pointer: coarse)` |

### Implementation
```tsx
/* Tier detection via CSS */
@media (pointer: coarse) {
  .touch-target { min-height: 56px; min-width: 56px; }
}
@media (pointer: fine) {
  .touch-target { min-height: 44px; min-width: 44px; }
}

/* Invisible hit area expansion (for icons < 44px) */
.hit-area-expand::before {
  content: '';
  position: absolute;
  inset: -8px;
}
```

### Rules
- Every clickable element must meet its tier's minimum
- Icon-only buttons (`size="icon"`): visible 28-32px, hit area 44px via padding or pseudo-element
- Adjacent targets must have 8px gap minimum (prevent mis-taps)
- Shop floor: full-width buttons on mobile (`w-full` below `sm` breakpoint)
