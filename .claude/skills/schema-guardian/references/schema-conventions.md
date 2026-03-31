# Redoe OS Schema Conventions

Extracted from schema-v1.sql (v1.1, 2026-03-07). These are the naming and structural rules that all migrations must follow.

## Naming Rules

### Tables
- snake_case, plural: `jobs`, `labour_entries`, `machine_events`
- Lookup/config tables: `shifts`, `indirect_codes`, `break_types`, `downtime_reasons`, `scrap_reasons`
- Join tables: `design_review_attendance`, `approval_checklist_items`

### Columns
- snake_case, singular: `job_id`, `plant_id`, `created_at`
- Foreign keys: `<referenced_table_singular>_id` (e.g., `job_id`, `vendor_id`, `department_id`)
- Boolean: `is_` prefix (e.g., `is_outsourced`, `is_complete`, `is_paid`)
- Timestamps: `_at` suffix (e.g., `created_at`, `approved_at`, `actual_start`)
- Dates: `_date` suffix or descriptive (e.g., `entry_date`, `order_date`, `expected_delivery`)

### Enums
- Type name: snake_case (e.g., `job_type`, `approval_status`, `machine_type`)
- Values: lowercase, underscores allowed (e.g., `'cnc_operator'`, `'po_received'`, `'wire_edm'`)
- Never: camelCase values, uppercase values, spaces in values

### Functions
- Prefix: `fn_` (e.g., `fn_audit_trigger`, `fn_job_cost_alert`)
- snake_case after prefix
- Trigger functions return `TRIGGER`

### Triggers
- Audit: `audit_<table>` (e.g., `audit_jobs`, `audit_labour`)
- Workflow: `trg_<descriptive_name>` (e.g., `trg_finishing_approved`, `trg_eco_all_checked`)

### Policies
- Format: `<table>_<operation>` (e.g., `jobs_read`, `labour_insert`, `po_read`)
- Operations: `read` (SELECT), `insert` (INSERT), `update` (UPDATE), `delete` (DELETE)

### Indexes
- Format: `idx_<table>_<column(s)>` (e.g., `idx_jobs_plant_status`, `idx_labour_person_date`)

## Structural Rules

### Required Columns (all tables)
- `id` — SERIAL, BIGSERIAL, or UUID as PRIMARY KEY
- `created_at TIMESTAMPTZ DEFAULT NOW()`

### Required for Mutable Tables
- `updated_at TIMESTAMPTZ` (optional for append-only tables like `audit_log`, `machine_events`)

### RLS
- Every table accessible via Supabase client MUST have `ENABLE ROW LEVEL SECURITY`
- Every RLS-enabled table MUST have at least one policy (RLS + zero policies = deny-all)
- Lookup tables (shifts, departments, indirect_codes, etc.) may be exempt — document in `rls-exceptions.md`

### Audit Triggers
Business data tables need `fn_audit_trigger()`. Required on:
- `jobs`, `labour_entries`, `job_costs`, `purchase_orders`, `purchase_requisitions`
- `requirement_forms`, `eco_headers`, `quality_incidents`, `design_status_tasks`, `machine_events`

NOT required on lookup/config tables: `departments`, `shifts`, `indirect_codes`, `break_types`, `scrap_reasons`, `downtime_reasons`, `machine_monitoring_config`

### Data Types
- Money: `DECIMAL(14,2)` for amounts, `DECIMAL(10,4)` for exchange rates, `DECIMAL(5,2)` for percentages
- Hours: `DECIMAL(8,2)`
- IDs: `SERIAL` for most, `BIGSERIAL` for high-volume (machine_events)
- Timestamps: Always `TIMESTAMPTZ` (never `TIMESTAMP`)
- Plant: Use `plant_type` enum, not free text
- Currency: Use `currency_type` enum

### Foreign Keys
- Always specify `ON DELETE` behavior:
  - `CASCADE` for child records (po_line_items → purchase_orders)
  - `SET NULL` for optional references
  - Default (RESTRICT) for critical references (job_costs → jobs)

## Existing Enum Values (for reference)

### job_type
R, G, C, P, S

### job_status
quoted, po_received, design, engineering, manufacturing, tryout, tuning, shipped, invoiced, closed, on_hold, cancelled

### person_role
pm, designer, moldmaker, cnc_operator, edm_operator, inspector, finance, management, sales, engineering_mgr, plant_mgr, gm, vp, buyer, scheduler, it

### approval_status
draft, submitted, approved, rejected, cancelled

### machine_type
cnc, edm, wire_edm, gundrill, cmm, boring_mill, press, grinder, polish, lathe, other
