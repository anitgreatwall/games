# Basejump supabase-test-helpers — API Reference

GitHub: usebasejump/supabase-test-helpers
Install: `CREATE EXTENSION supabase_test_helpers;` in test setup SQL

## Core Functions

### tests.create_supabase_user(email TEXT, metadata JSONB DEFAULT '{}')
Creates a user in `auth.users` with the given email and app_metadata.
Returns the user UUID.

```sql
SELECT tests.create_supabase_user(
  'operator@test.redoe.local',
  '{"role": "cnc_operator", "plant": "windsor"}'::jsonb
);
```

### tests.get_supabase_uid(email TEXT)
Returns the UUID of a previously created test user.

```sql
SELECT tests.get_supabase_uid('operator@test.redoe.local');
```

### tests.authenticate_as(email TEXT)
Sets the current session's JWT claims to match the given user. All subsequent queries in the transaction will be evaluated against that user's RLS policies.

```sql
SELECT tests.authenticate_as('operator@test.redoe.local');
-- Now all queries run as this user
SELECT * FROM jobs;  -- RLS applies based on operator's plant/role
```

### tests.clear_authentication()
Resets the session to unauthenticated (anon). Use this to test that RLS blocks unauthenticated access.

```sql
SELECT tests.clear_authentication();
SELECT COUNT(*) FROM jobs;  -- should be 0 if RLS blocks anon
```

## Usage Pattern for RLS Tests

```sql
BEGIN;
SELECT plan(4);

-- Setup: authenticate as shop floor
SELECT tests.authenticate_as('shopfloor_windsor@test.redoe.local');

-- Positive: can see own plant
SELECT is(
  (SELECT COUNT(*)::int FROM jobs WHERE plant_id = 'windsor'),
  1,  -- expected count
  'Windsor operator sees Windsor jobs'
);

-- Negative: cannot see other plant
SELECT is(
  (SELECT COUNT(*)::int FROM jobs WHERE plant_id = 'hunan'),
  0,
  'Windsor operator cannot see Hunan jobs'
);

-- Switch to management
SELECT tests.authenticate_as('vp@test.redoe.local');

-- Positive: management sees all
SELECT is(
  (SELECT COUNT(*)::int FROM jobs),
  2,  -- both plants
  'VP sees all jobs across plants'
);

-- Unauthenticated
SELECT tests.clear_authentication();
SELECT is(
  (SELECT COUNT(*)::int FROM jobs),
  0,
  'Unauthenticated sees nothing'
);

SELECT * FROM finish();
ROLLBACK;
```

## Redoe OS Test User Convention

| Email | Role | Plant | Tier |
|-------|------|-------|------|
| shopfloor_windsor@test.redoe.local | cnc_operator | windsor | Shop Floor |
| shopfloor_hunan@test.redoe.local | moldmaker | hunan | Shop Floor |
| pm_windsor@test.redoe.local | pm | windsor | PM/Leads |
| finance_windsor@test.redoe.local | finance | windsor | Finance |
| vp@test.redoe.local | vp | windsor | Management |
| gm@test.redoe.local | gm | windsor | Management |

These users are created in `00_helpers.sql` and available to all test files.

## pgTAP Assertion Functions (Most Used)

| Function | Purpose |
|----------|---------|
| `is(got, expected, description)` | Equality check |
| `isnt(got, expected, description)` | Inequality check |
| `ok(boolean, description)` | Boolean assertion |
| `matches(got, regex, description)` | Regex match |
| `lives_ok(sql, description)` | SQL runs without error |
| `throws_ok(sql, errcode, description)` | SQL throws expected error |
| `is_empty(sql, description)` | Query returns zero rows |
| `has_table(schema, table, description)` | Table exists |
| `has_column(schema, table, column, description)` | Column exists |
| `col_type_is(schema, table, column, type)` | Column type check |
| `col_not_null(schema, table, column, description)` | NOT NULL constraint |
| `has_fk(schema, table, description)` | Foreign key exists |
| `has_trigger(table, trigger, description)` | Trigger exists |
| `has_index(schema, table, index, description)` | Index exists |
| `policies_are(table, array, description)` | Assert exact set of policies |
