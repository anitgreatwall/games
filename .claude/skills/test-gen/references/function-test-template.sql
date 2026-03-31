-- ==========================================================================
-- Function Test Template — Redoe OS
-- Replace: <FUNCTION_NAME>, <TRIGGER_TABLE>, <TRIGGER_NAME>
-- ==========================================================================

BEGIN;
SELECT plan(5);  -- adjust count

-- Authenticate as a user with sufficient access
SELECT tests.authenticate_as('vp@test.redoe.local');

-- ============================================================
-- TEST 1: Happy path — expected behavior
-- ============================================================
-- Setup: Insert test data that will trigger the function
INSERT INTO <TRIGGER_TABLE> (/* columns */)
VALUES (/* values */);

SELECT is(
  (SELECT /* check result */),
  /* expected value */,
  'Function produces expected result on normal input'
);

-- ============================================================
-- TEST 2: Side effect — verify audit/notification created
-- ============================================================
SELECT is(
  (SELECT COUNT(*)::int FROM audit_log
   WHERE table_name = '<TRIGGER_TABLE>'
   AND operation = 'INSERT'),
  1,
  'Audit log entry created after INSERT'
);

-- ============================================================
-- TEST 3: Boundary condition — threshold behavior
-- ============================================================
-- Insert data at exactly the threshold value
UPDATE <TRIGGER_TABLE> SET /* column */ = /* boundary value */
WHERE id = /* test id */;

SELECT is(
  (SELECT /* check threshold response */),
  /* expected at boundary */,
  'Function handles boundary condition correctly'
);

-- ============================================================
-- TEST 4: Edge case — zero/null guard
-- ============================================================
SELECT lives_ok(
  $$INSERT INTO <TRIGGER_TABLE> (/* columns */)
    VALUES (/* zero or null values */)$$,
  'No error on zero/null input (guard clause works)'
);

-- ============================================================
-- TEST 5: Audit trail — changed_by matches authenticated user
-- ============================================================
SELECT is(
  (SELECT changed_by FROM audit_log
   WHERE table_name = '<TRIGGER_TABLE>'
   ORDER BY changed_at DESC LIMIT 1),
  tests.get_supabase_uid('vp@test.redoe.local'),
  'Audit log changed_by matches authenticated user'
);

SELECT * FROM finish();
ROLLBACK;
