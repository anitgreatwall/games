# Form Patterns — Redoe OS

> Every form decision pre-made. Label above, error below, validation on blur.
> Uses `react-hook-form` + Zod. Components from shadcn/ui `components/ui/`.

---

## 1. Field Layout

```
┌─ FormField ──────────────────────────┐
│ <Label>               * (if required)│  ← text-body-sm font-medium
│                        gap-1.5 (6px) │
│ ┌─ Input / Select / etc ──────────┐  │
│ └─────────────────────────────────┘  │
│ Helper text or error (one, not both) │  ← text-[11px]
└──────────────────────────────────────┘
         gap-6 (24px) between fields
```

### Rules
| Rule | Value |
|------|-------|
| Label position | Above input — NEVER floating, NEVER inline |
| Label-to-input gap | `gap-1.5` (6px) |
| Field-to-field gap | `gap-6` (24px) |
| Required indicator | Red asterisk after label: `<span className="text-destructive ml-0.5">*</span>` |
| Description / help | Below input, `text-[11px] text-muted-foreground` |
| Error message | Replaces description, `text-[11px] text-destructive`, `role="alert"` |
| Label tag | Always `<Label htmlFor={id}>` — never detached labels |

### Compound Component Pattern
```tsx
<FormField
  control={form.control}
  name="jobNumber"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Job Number <span className="text-destructive ml-0.5">*</span></FormLabel>
      <FormControl>
        <Input placeholder="e.g. G-12345" {...field} />
      </FormControl>
      <FormDescription>Assigned by SAP after WBS creation</FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>
```

---

## 2. Validation Rules

| Trigger | Behavior |
|---------|----------|
| On blur | Validate the field. Show error if invalid. |
| On keystroke | Do NOT validate (exception: password strength meter) |
| On change (after error shown) | Re-validate on each change to clear error as soon as valid |
| On submit | Validate all fields. Scroll to first error. Focus it. |

### Error Message Format
| Condition | Message Pattern | Example |
|-----------|----------------|---------|
| Required field empty | "Please enter [field name]" | "Please enter job number" |
| Invalid format | "[Field] needs to be [format]. Example: [example]" | "Email needs to be a valid address. Example: name@redoe.com" |
| Out of range | "[Field] must be between [min] and [max]" | "Quantity must be between 1 and 9999" |
| Too long | "[Field] must be [max] characters or fewer" | "Notes must be 500 characters or fewer" |
| Custom business rule | Plain sentence describing the constraint | "Cannot assign to a completed work order" |

### Zod Schema Convention
```tsx
const workOrderSchema = z.object({
  jobNumber:   z.string().min(1, "Please enter job number"),
  customer:    z.string().min(1, "Please select a customer"),
  quantity:    z.coerce.number().min(1).max(9999, "Quantity must be between 1 and 9999"),
  dueDate:     z.date({ required_error: "Please enter due date" }),
  notes:       z.string().max(500, "Notes must be 500 characters or fewer").optional(),
});
```

---

## 3. Field Type to Component Map

| Field Type | Component | When to Use | Notes |
|------------|-----------|-------------|-------|
| Short text | `<Input>` | Single-line text, email, phone | `type` attr for semantics |
| Long text | `<Textarea>` | Notes, descriptions, comments | `rows={3}` default, auto-resize optional |
| Single select (<=7 options) | `<Select>` (shadcn) | Status, priority, category | Static option list |
| Single select (>7 options) | `<Combobox>` (Command-based) | Customer, program, job lookup | Searchable, async-loadable |
| Multi select | `<MultiCombobox>` (Command-based) | Tags, assignees, operations | Chips display, searchable |
| Boolean (settings) | `<Switch>` | Feature toggles, preferences | Label left, switch right |
| Boolean (forms) | `<Checkbox>` | Consent, multi-option checklist | Label right of checkbox |
| Date (single) | `<DatePicker>` (popover calendar) | Due date, start date | `format="PPP"` display |
| Date range | `<DateRangePicker>` | Reporting period, schedule | Two-month calendar |
| Number | `<Input type="number">` | Quantity, hours, cost | Add `font-data` class, right-align |
| Currency | `<Input>` + formatter | Quote amount, budget | `font-data`, prefix `$`, 2 decimal places |
| Radio choice | `<RadioGroup>` | Mutually exclusive, 2-5 options | Vertical stack default |
| File upload | `<DropZone>` or `<Input type="file">` | Documents, images | Drag-and-drop zone preferred |

---

## 4. Form Actions (Footer)

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  [Cancel]                    [Create Work Order] │
│  variant="outline"           variant="default"   │
│  left-aligned                right-aligned        │
│                                                 │
└─────────────────────────────────────────────────┘
  ↑ Sticky footer via FormPage layout component
```

### Rules
| Rule | Value |
|------|-------|
| Layout | Sticky footer, `border-t border-subtle`, `py-4 px-6`, `flex justify-between` |
| Cancel button | Left side, `variant="outline"`. Text: "Cancel" or "Keep editing" |
| Submit button | Right side, `variant="default"`. Text: verb + object |
| Submit text examples | "Create Work Order", "Save Changes", "Assign Operator", "Send Quote" |
| Forbidden button text | "OK", "Submit", "Yes", "No", "Confirm", "Done" |
| Loading state | Both buttons disabled. Submit shows: `"Creating..."` (verb + "...") |
| Keyboard shortcut | `Cmd+Enter` / `Ctrl+Enter` submits. Show hint on Tier 2+: `Save (Cmd+Enter)` |

### Delete / Destructive Actions
- Never in the form footer — use `DropdownMenu` in page header
- Always require confirmation via `AlertDialog`
- Destructive button: `variant="destructive"`, text = "Delete [object]"

---

## 5. Success and Error Patterns

| Outcome | Behavior |
|---------|----------|
| Success | `toast.success("Work order created")` + redirect to list or detail page |
| Validation error | Inline field errors (see Section 2) + scroll to first error |
| Server error | `toast.error("Failed to create work order")` + keep form open, preserve all input |
| Network error | `toast.error("Connection lost. Your changes are saved locally.")` (if offline-capable) |
| Conflict (409) | Toast with explanation + "Reload" action button in toast |

### Toast Configuration
```tsx
toast.success("Work order created", {
  duration: 5000,        // 5s auto-dismiss
  description: "G-12345 assigned to Line 3",  // optional detail
});

toast.error("Failed to create work order", {
  duration: 8000,        // longer for errors — user needs to read
  description: "Server returned 500. Try again or contact IT.",
});
```

---

## 6. Field Groups and Multi-Section Forms

### Grouping
| Rule | Implementation |
|------|---------------|
| Related fields | Wrap in `<fieldset>` with `<legend className="text-body font-medium mb-4">` |
| Section dividers | `<Separator className="my-6" />` between groups |
| Two-column layout | `grid grid-cols-1 lg:grid-cols-2 gap-6` within a group |
| Max fields before scroll | 6-8 visible. Beyond that, break into tabs. |

### Multi-Step / Tabbed Forms
```
TabsList (top of form area)
├── Tab: General          ← basic fields (name, customer, dates)
├── Tab: Specifications   ← technical fields (material, dimensions)
├── Tab: Operations       ← operation sequence table
└── Tab: Documents        ← file uploads

Footer (sticky, always visible regardless of active tab)
├── [Cancel]
└── [Create Work Order]   ← submits ALL tabs at once
```

### Rules
- Tab switch does NOT submit — only the footer button submits
- Validation errors on inactive tabs: show red dot indicator on tab label
- Tab with errors: `<TabsTrigger>` gets `<span className="size-2 rounded-full bg-destructive ml-1.5" />`
- Pre-fill what you can from context (e.g., customer from URL param, date = today)
- Read-only fields: render as plain text (`text-foreground`), not disabled inputs
