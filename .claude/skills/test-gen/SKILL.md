---
name: test-gen
description: Auto-generate pgTAP tests for Redoe OS RLS policies, PL/pgSQL functions, and triggers. Use when user says "generate tests", "write pgTAP tests", "test this policy", "test this function", invokes /test-gen, or when Schema Guardian detects new RLS policies/functions without corresponding tests. Outputs to supabase/tests/.
---

# Test Generator — pgTAP Test Scaffolding for Redoe OS

Generates database-level unit tests using pgTAP + Basejump supabase-test-helpers. Every RLS policy, function, and trigger gets both positive and negative test cases.

## Step 1: Identify Test Targets

Compare existing coverage against the schema:

1. Read `supabase/migrations/` to find all RLS policies, functions, and triggers
2. Read `supabase/tests/` to find existing test files
3. Identify gaps: policies/functions without corresponding test files

If invoked with a specific target (e.g., `/test-gen jobs_read`), generate tests only for that target.

## Step 2: Load Test Patterns

Read `references/basejump-patterns.md` for the Basejump test helpers API. Key functions:
- `tests.create_supabase_user(email, metadata)` — create auth.users with JWT claims
- `tests.authenticate_as(email)` — set session JWT for RLS evaluation
- `tests.clear_authentication()` — reset to anon (unauthenticated)
- `tests.get_supabase_uid(email)` — get user UUID

Read `references/rls-test-template.sql` for the RLS test pattern.
Read `references/function-test-template.sql` for the function test pattern.

## Step 3: Generate RLS Tests

For each RLS policy, generate both positive AND negative cases across all 4 security tiers:

| Tier | Roles | Plant Access | Cost Access |
|------|-------|-------------|-------------|
| Shop Floor | cnc_operator, moldmaker, edm_operator | Own plant only | BLOCKED |
| PM/Leads | pm, engineering_mgr, scheduler | Own plant only | ALLOWED |
| Finance | finance, buyer | Own plant only | ALLOWED |
| Management | gm, vp | ALL plants | ALLOWED |

**Mandatory test cases per SELECT policy:**
1. Positive: Allowed role sees expected data
2. Positive: Management role sees cross-plant data
3. Negative: Blocked role sees zero rows
4. Negative: Cross-plant access blocked for non-management
5. Negative: Unauthenticated user sees nothing

**Mandatory test cases per INSERT/UPDATE policy:**
1. Positive: Allowed role can write own records
2. Negative: Cannot write records for other users/plants
3. Negative: Blocked role gets rejected

## Step 4: Generate Function Tests

For each PL/pgSQL function, test:
1. **Happy path:** Expected input produces expected output
2. **Edge cases:** Zero values, NULL inputs, boundary conditions
3. **Side effects:** Triggers that create notifications, alerts, audit log entries
4. **Error handling:** Division by zero guards, missing FK references

## Step 5: Generate Trigger Tests

For audit triggers, verify:
1. INSERT creates audit_log row with `operation='INSERT'`, `new_data` populated
2. UPDATE creates audit_log row with `operation='UPDATE'`, both `old_data` and `new_data`
3. DELETE creates audit_log row with `operation='DELETE'`, `old_data` populated
4. `changed_by` matches the authenticated user's ID

For workflow triggers, verify the complete state transition.

## Step 6: Write Test Files

Output to `supabase/tests/` using this naming convention:
- `NN_rls_<table>_test.sql` — RLS policy tests
- `NN_fn_<function_name>_test.sql` — Function tests
- `NN_trigger_<name>_test.sql` — Trigger tests

Every test file must follow this structure:
```sql
BEGIN;
SELECT plan(N);  -- exact count of assertions

-- ... test body ...

SELECT * FROM finish();
ROLLBACK;  -- clean up, don't leak test data
```

Use IDs in the 900+ range for test data to avoid collision with seed data.

## Step 7: Verify

If `supabase` CLI is available locally, run:
```bash
supabase test db
```
Report pass/fail counts. If tests fail, diagnose and fix before presenting to user.

## Test User Fixtures

The `assets/00_setup.sql` file creates 6 test users across 4 tiers and 2 plants. Copy this to `supabase/tests/00_helpers.sql` when initializing the test suite for the first time.

## CI Integration

In `db-qa.yml`, the Test Generator runs after Schema Guardian when new migrations are detected. It uses `anthropics/claude-code-action` with Sonnet to generate test files, then auto-commits them to the PR branch.
